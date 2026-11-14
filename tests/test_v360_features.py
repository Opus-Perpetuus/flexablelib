"""3.6.0: signature pad, stopwatch, a vertical stack that shares its height
and follows the focus, focus shown without colour on empty tables and
images drawn as text, forms that collect nested fields and editable
tables, a scanner that keeps its value, catalog cards with pictures,
image downloads with headers and a validation summary built from a list
of errors."""

import datetime as dt
import http.server
import threading

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib import _images as I  # noqa: E402
from flexablelib_tui import App, Key, accessibility as a11y  # noqa: E402
from flexablelib_tui.keys import MouseEvent  # noqa: E402
from flexablelib.text_width import strip_ansi, visible_width  # noqa: E402


def key(name):
    if name == 'space':
        return Key('space', ' ')
    if len(name) == 1:
        return Key(name, name)
    return Key(name)


def press(comp, *names):
    comp.focused = True
    return [comp.handle_key(key(n)) for n in names]


def text(comp, width=50, height=None):
    return strip_ansi(comp.render(width=width, height=height))


ENV = ('FLEXABLELIB_IMAGE', 'FLEXABLELIB_NO_BROWSER', 'BROWSER', 'DISPLAY',
       'WAYLAND_DISPLAY', 'TMUX', 'NO_COLOR', 'SSH_CONNECTION', 'SSH_TTY',
       'WSL_DISTRO_NAME', 'COLORTERM', 'TERM_PROGRAM', 'KITTY_WINDOW_ID')


@pytest.fixture(autouse=True)
def plain_a11y(monkeypatch):
    from flexablelib_tui import graphics as g
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('TERM', 'dumb')        # pictures as alt text
    g.reset_cache()
    with a11y.configure(screen_reader=False, ascii=False, reduced_motion=False,
                        focus_marker=False):
        yield
    g.reset_cache()


def term(monkeypatch, value):
    from flexablelib_tui import graphics as g
    monkeypatch.setenv('TERM', value)
    g.reset_cache()


def picture(w=8, h=6):
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out += bytes([x * 30, y * 40, 120, 255])
    return I.Bitmap(w, h, bytes(out))


# +---------------------------------------------------------------------------+
# 1. SignatureInput and Stopwatch

class TestSignature:
    def test_keyboard_strokes_and_exports(self):
        changes = []
        s = C.SignatureInput('Firma', columns=6, rows=3, required=True,
                             on_change=changes.append, use_colors=False)
        assert s.is_empty() and s.validate() == 'Requerido'
        assert s.a11y_value() == 'sin firma'
        press(s, 'space', 'right', 'right', 'down', 'space', 'right')
        assert s.value == [[(0, 0), (1, 0), (2, 0), (2, 1)]]
        assert not s.pen_down and s.validate() is None and changes
        assert s.to_text() == ['###   ', '  #   ', '      ']
        assert s.to_text(ink='x', blank='.')[1] == '..x...'
        press(s, 'space', 'down')          # a second stroke
        assert len(s.value) == 2 and s.a11y_value() == '2 trazos'
        press(s, 'backspace')
        assert len(s.value) == 1
        s.pen = (1, 0)
        press(s, 'x')                       # erase under the pen
        assert (1, 0) not in s.cells()
        press(s, 'left', 'left', 'up')      # clamped to the pad
        assert s.pen == (0, 0)
        press(s, 'c')
        assert s.value == [] and s.is_empty()
        assert press(s, 'q') == [False]

    def test_image_export(self):
        s = C.SignatureInput(value=[[(0, 0), (1, 1)]], columns=3, rows=2)
        bm = s.to_bitmap(scale=2)
        assert (bm.width, bm.height) == (6, 4)
        assert bm.pixel(0, 0)[:3] == (0, 0, 0)
        assert bm.pixel(5, 0)[:3] == (255, 255, 255)
        png = s.to_png(scale=1)
        assert png[:8] == b'\x89PNG\r\n\x1a\n'
        back = I.decode(png)
        assert (back.width, back.height) == (3, 2)

    def test_mouse_draws_a_line(self):
        s = C.SignatureInput('Firma', columns=10, rows=4, use_colors=False)
        # Row 0 is the label, row 1 the top border: cell (0, 0) is at (1, 2).
        assert s.on_mouse(MouseEvent(0, 1, 2, True))
        assert s.on_mouse(MouseEvent(0, 5, 2, True, action='drag'))
        assert s.on_mouse(MouseEvent(0, 5, 2, False))
        assert s.value == [[(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]]
        assert not s.on_mouse(MouseEvent(0, 30, 2, True))     # outside
        assert not s.on_mouse(MouseEvent(0, 3, 3, False))
        s.on_mouse(MouseEvent(0, 1, 3, True))
        s.on_mouse(MouseEvent(0, 4, 5, True, action='drag'))
        assert s.value[-1][0] == (0, 1) and s.value[-1][-1] == (3, 3)

    def test_render_and_value_setter(self):
        s = C.SignatureInput('Firma', value=[[(0, 0)], []], columns=5,
                             rows=2, use_colors=False)
        assert s.value == [[(0, 0)]]
        lines = [l.rstrip() for l in text(s, 30).split('\n')]
        assert lines[0] == 'Firma' and lines[2].startswith('│█    │')
        s.focused = True
        out = text(s, 60)
        assert '+' in out and 'pluma arriba' in out
        coloured = C.SignatureInput(columns=5, rows=2, use_colors=True)
        coloured.focused = True
        assert '\x1b[' in coloured.render(width=40)
        assert s.natural_width() >= 7
        s.set_value([[(4, 1)]])
        assert s.to_text()[1] == '    #'
        s.extend((2, 1))
        assert s.value[-1] == [(4, 1), (3, 1), (2, 1)]
        fresh = C.SignatureInput(columns=3, rows=3)
        fresh.extend((1, 1))                  # no stroke yet: starts one
        assert fresh.value == [[(1, 1)]]
        press(fresh, 'enter')

    def test_in_a_form(self):
        got = []
        sig = C.SignatureInput('Firma', name='firma', columns=4, rows=2,
                               required=True)
        form = C.Form([sig], on_submit=got.append, use_colors=False)
        form.submit()
        assert form.errors == {'Firma': 'Requerido'}
        sig.set_value([[(0, 0), (1, 0)]])
        form.submit()
        assert got == [{'firma': [[(0, 0), (1, 0)]]}]


class TestStopwatch:
    def test_start_stop_lap_reset(self):
        now = [0.0]
        laps, changes = [], []
        w = C.Stopwatch('Tiempo', clock=lambda: now[0], on_lap=laps.append,
                        on_change=changes.append, use_colors=False)
        assert w.value == dt.timedelta(0) and w.is_empty()
        assert w.lap() is False             # not running
        press(w, 'space')
        assert w.running and not w.is_empty()
        now[0] = 12.34
        press(w, 'l')
        assert laps == [dt.timedelta(seconds=12.34)] and w.laps == laps
        now[0] = 75.5
        assert w.value == dt.timedelta(seconds=75.5)
        assert w.text() == '00:01:15.5'
        press(w, 'enter')                   # stop
        assert not w.running and changes[-1] == dt.timedelta(seconds=75.5)
        now[0] = 100
        assert w.value == dt.timedelta(seconds=75.5)
        assert '1 vueltas' in w.a11y_value() and 'detenido' in w.a11y_value()
        out = text(w, 70)
        assert '00:01:15.5' in out and '1. 00:00:12.3' in out
        press(w, 'r')
        assert w.value == dt.timedelta(0) and w.laps == []
        assert press(w, 'z') == [False]

    def test_value_setter_and_formats(self):
        w = C.Stopwatch(value=dt.timedelta(minutes=2), precision=0,
                        clock=lambda: 0.0, max_laps=2)
        assert w.text() == '00:02:00' and not w.running
        w.value = 3661
        assert w.text() == '01:01:01'
        w.start()
        w.start()                            # already running: no-op
        for _ in range(3):
            w.lap()
        assert len(w.laps) == 2
        w.reset()                            # running: keeps running from 0
        assert w.running
        assert C.Stopwatch.format_duration(1.25, 2) == '00:00:01.25'
        assert C.Stopwatch.format_duration(-5, 0) == '00:00:00'
        assert w.on_mouse(MouseEvent(0, 0, 0, True))
        assert not w.running
        assert not w.on_mouse(MouseEvent(0, 0, 0, False))
        assert w.natural_width() >= 40
        coloured = C.Stopwatch('T', use_colors=True, clock=lambda: 0.0)
        coloured.focused = True
        assert 'espacio: iniciar' in strip_ansi(coloured.render(width=70))

    def test_in_a_form(self):
        got = []
        w = C.Stopwatch('Duración', name='duracion', value=90, required=True)
        C.Form([w], on_submit=got.append).submit()
        assert got == [{'duracion': dt.timedelta(seconds=90)}]
        empty = C.Stopwatch('Duración', required=True)
        assert empty.validate() == 'Requerido'


# +---------------------------------------------------------------------------+
# 2. VStack

class Lines(C.Box.__mro__[1]):            # a _Themed component with n lines
    def __init__(self, n, label='x', focusable=False, **kw):
        super(Lines, self).__init__(**kw)
        self.n = n
        self.label = label
        self.focusable = focusable

    def draw(self, width, height):
        rows = height if (height and self.expand) else self.n
        return ['{0}{1}'.format(self.label, i) for i in range(rows)]


class Filler(Lines):
    expand = True


class TestVStack:
    def test_weights_min_max(self):
        a, b, c = Lines(2, 'a'), Filler(1, 'b'), Filler(1, 'c')
        st = C.VStack([a, b, c], weights=[0, 1, 3], max_heights=[None, None,
                                                                 5])
        out = [l.rstrip() for l in text(st, 10, 12).split('\n')]
        assert st.heights == [2, 5, 5]      # c capped at 5, b takes the rest
        assert out[:3] == ['a0', 'a1', 'b0'] and len(out) == 12
        st2 = C.VStack([Filler(1, 'b'), Filler(1, 'c')], weights=[1, 1],
                       min_heights=[4, 0], gap=1)
        text(st2, 10, 7)
        assert st2.heights == [5, 1]      # weights share what is left
        st3 = C.VStack([Filler(1, 'b'), Filler(1, 'c')], weights=[1, 2])
        text(st3, 10, 10)
        assert st3.heights == [3, 7]
        # No height: every child keeps its own (bounded) height.
        free = C.VStack([Lines(3), Lines(9)], max_heights=[None, 4],
                        scrollbar=False)
        assert len(text(free, 10).split('\n')) == 7 and free.heights == [3, 4]
        with pytest.raises(ValueError):
            C.VStack([Lines(1)], weights=[1, 2])
        assert st.natural_width() >= 1 and st.children() == [a, b, c]

    def test_scrolls_following_the_focus(self):
        fields = [C.TextInput('Campo {0}'.format(i), name='f{0}'.format(i))
                  for i in range(8)]
        st = C.VStack(fields, height=6)
        app = App(body=st)
        app.run(keys=[], size=(40, 8))
        assert st.total > st.view_height and st.offset == 0
        assert '│' in app.last_frame or '█' in app.last_frame
        for _ in range(6):
            app.dispatch(key('tab'))
        app.render(40, 8)
        assert app.focused is fields[6]
        assert 'Campo 6' in app.last_frame or 'Campo 6' in \
            strip_ansi(app.render(40, 8))
        assert st.offset > 0
        before = st.offset
        assert st.handle_key(key('pageup'))
        assert st.offset < before
        st.scroll_to(0)
        assert st.offset == 0
        assert 'líneas 1-' in st.a11y_value()
        # Back to the first field: the stack follows it up again.
        for _ in range(2):
            app.dispatch(key('tab'))
        app.render(40, 8)
        assert app.focused is fields[0] and st.offset == 0
        assert not st.handle_key(key('x'))

    def test_tall_child_and_no_scrollbar(self):
        big = Lines(10, 'b', focusable=True)
        st = C.VStack([Lines(3), big], height=4, scrollbar=False)
        app = App(body=st)
        app.run(keys=[], size=(20, 4))
        app.focus(big)
        out = strip_ansi(app.render(20, 4)).split('\n')
        assert out[0].startswith('b0')       # taller than the view: its top
        fits = C.VStack([Lines(2)], height=5)
        assert [l.rstrip() for l in text(fits, 10, 5).split('\n')][:2] == \
            ['x0', 'x1']
        assert fits.a11y_value() == '' and not fits.handle_key(
            key('pagedown'))

    def test_wheel_and_marked_bar(self):
        st = C.VStack([Lines(20)], height=5, use_colors=True)
        st.render(width=10, height=5)
        assert st.handle_key(key('scrolldown')) and st.offset == 3
        with a11y.configure(focus_marker=True):
            assert '█' in strip_ansi(st.render(width=10, height=5))

    def test_inside_a_form(self):
        got = []
        a = C.TextInput('A', value='1')
        b = C.Checkbox('B', value=True)
        form = C.Form([C.VStack([a, C.Stack([b])])], on_submit=got.append)
        form.submit()
        assert got == [{'a': '1', 'b': True}]


# +---------------------------------------------------------------------------+
# 3. Focus visible without colour

class TestFocusWithoutColour:
    def test_empty_table(self):
        for colors in (False, True):
            t = C.DataTable(['a', 'b'], [], use_colors=colors)
            t.focused = True
            out = t.render(width=30)
            assert ('▸ Sin registros' if colors else '> Sin registros') in \
                strip_ansi(out)
            if colors:
                assert '\x1b[7' in out or ';7m' in out or '7;' in out
            t.focused = False
            assert '>' not in strip_ansi(t.render(width=30)).split('\n')[2]

    def test_image_as_alt_text(self):
        img = C.Image(picture(), alt='Logo', method='alt', focusable=True,
                      use_colors=True)
        assert '▸' not in strip_ansi(img.render(width=30))
        img.focused = True
        out = img.render(width=30)
        assert strip_ansi(out).startswith('▸ Imagen: Logo')
        missing = C.Image('/no/such/file.png', alt='X', method='half',
                          focusable=True, use_colors=False)
        missing.focused = True
        with a11y.configure(ascii=True):
            assert strip_ansi(missing.render(width=60)).startswith(
                '> Imagen: X')

    def test_image_none_and_warning(self, monkeypatch):
        term(monkeypatch, 'xterm-256color')
        none = C.Image(picture(), alt='Logo', method='none', focusable=True,
                       use_colors=False)
        assert strip_ansi(none.render(width=30)).startswith('[Logo]')
        none.focused = True
        assert strip_ansi(none.render(width=30)).startswith('> [Logo]')
        monkeypatch.setenv('FLEXABLELIB_NO_BROWSER', '1')
        broken = C.Image(b'not an image', alt='X', method='half',
                         focusable=True, use_colors=True)
        broken.focused = True
        out = broken.render(width=60)
        assert strip_ansi(out).startswith('▸ ') and '\x1b[' in out

    def test_image_viewer(self):
        v = C.ImageViewer([(picture(), 'uno'), (picture(), 'dos')],
                          method='ascii', use_colors=True)
        last = strip_ansi(v.render(width=40, height=6)).split('\n')[-1]
        assert '▸' not in last
        v.focused = True
        raw = v.render(width=40, height=6).split('\n')[-1]
        assert '▸' in strip_ansi(raw) and '\x1b[' in raw
        plain = C.ImageViewer([(picture(), 'uno')], method='ascii',
                              use_colors=False)
        plain.focused = True
        assert '> ' in strip_ansi(plain.render(width=40, height=6))


# +---------------------------------------------------------------------------+
# 4. Form collects nested fields and editable tables

class TestFormNested:
    def test_values_from_containers_and_tables(self):
        got = []
        name = C.TextInput('Nombre', value='Ana')
        qty = C.NumberInput('Cantidad', value=2)
        table = C.EditableTable([{'key': 'sku', 'title': 'SKU'},
                                 {'key': 'n', 'title': 'N', 'type': 'number'}],
                                [{'sku': 'A1', 'n': 1}], name='lineas')
        tabs = C.Tabs([('Datos', C.Stack([name, qty])), ('Tabla', table)])
        form = C.Form([tabs], on_submit=got.append, use_colors=False)
        assert set(map(id, form.fields())) == {id(name), id(qty)}
        assert table in form.form_nodes()
        form.submit()
        assert got == [{'nombre': 'Ana', 'cantidad': 2,
                        'lineas': [{'sku': 'A1', 'n': 1}]}]
        got[0]['lineas'][0]['n'] = 99        # a copy, not the table's rows
        assert table.rows[0]['n'] == 1
        table.value = [{'sku': 'B', 'n': 3}]
        assert form.values()['lineas'] == [{'sku': 'B', 'n': 3}]

    def test_validation_reaches_nested(self):
        inner = C.TextInput('Correo', required=True)
        form = C.Form([C.VStack([C.Stack([inner])])], use_colors=False)
        app = App(body=form)
        app.run(keys=['ctrl+s'], size=(60, 20))
        assert form.errors == {'Correo': 'Requerido'} and app.focused is inner
        # Enter in a nested one-line input moves on, as at the top level.
        assert inner.on_submit is not None
        unnamed = C.EditableTable(['a'], [[1]])
        assert C.Form([unnamed]).values() == {}

    def test_list_rows_and_strings(self):
        table = C.EditableTable(['a', 'b'], [[1, 2]], name='t')
        form = C.Form(['Sección', table, (C.Checkbox('X'),)])
        assert form.values() == {'t': [[1, 2]], 'x': False}


# +---------------------------------------------------------------------------+
# 5. ScanInput keeps its value

class TestScanKeepsValue:
    def test_default_keeps(self):
        codes = []
        s = C.ScanInput('Código', on_scan=codes.append, use_colors=False)
        for c in 'ABC':
            press(s, c)
        press(s, 'enter')
        assert codes == ['ABC'] and s.text == 'ABC' and s.value == 'ABC'
        assert s.last_code == 'ABC'
        press(s, 'enter')                    # Enter on the shown code
        assert codes == ['ABC']
        for c in 'XYZ':                      # the next read replaces it
            press(s, c)
        assert s.text == 'XYZ'
        press(s, 'enter')
        assert codes == ['ABC', 'XYZ'] and s.value == 'XYZ'
        press(s, 'left', 'Q')                # editing keys keep the text
        assert s.text == 'XYQZ'
        form = C.Form([s], use_colors=False)
        assert form.values() == {'código': 'XYQZ'}

    def test_duplicate_keeps_and_opt_out(self):
        now = [0.0]
        s = C.ScanInput(clock=lambda: now[0])
        s.text = '9'
        s.submit()
        s.text = '9'
        s.submit()                            # dropped duplicate
        assert s.scans == ['9'] and s.text == '9'
        changes = []
        old = C.ScanInput(keep_value=False, on_change=changes.append,
                          clock=lambda: now[0])
        for c in '12':
            press(old, c)
        press(old, 'enter')
        assert old.text == '' and old.scans == ['12']
        for c in '12':
            press(old, c)
        press(old, 'enter')                   # duplicate: cleared too
        assert old.text == '' and old.last_code == '12'
        assert C.ScanInput().last_code is None


# +---------------------------------------------------------------------------+
# 6. CatalogGrid with pictures

class TestCatalogImages:
    def items(self):
        return [{'title': 'Uno', 'subtitle': 'primero', 'image': picture()},
                {'title': 'Dos', 'subtitle': 'segundo', 'image': picture(),
                 'image_alt': 'Foto dos'},
                {'title': 'Tres'}]

    def test_cards_with_pictures(self):
        picked = []
        g = C.CatalogGrid(self.items(), min_width=16, image_height=3,
                          image_method='ascii', on_select=picked.append,
                          use_colors=False)
        out = text(g, 60)
        lines = out.split('\n')
        assert g._card_rows() == 9 and len(lines) == 9
        assert 'Uno' in out and 'primero' in out and 'Tres' in out
        assert any(set(l[2:14]) - set(' ') for l in lines[1:4])
        press(g, 'right')
        g.render(width=60)
        assert '> Dos' in text(g, 60)
        press(g, 'enter')
        assert picked[-1]['title'] == 'Dos' and g.value is g.items[1]
        assert g.selected is g.items[1]
        g._click(2)
        assert g.index == 2 and len(picked) == 1
        g._click(2)
        assert picked[-1]['title'] == 'Tres'
        assert C.CatalogGrid([]).select() is False

    def test_default_height_and_alt(self):
        g = C.CatalogGrid(self.items(), image_method='alt', use_colors=False)
        assert g._picture_rows() == 6
        out = text(g, 80)
        assert 'Imagen: Foto dos' in out and 'Imagen: Uno' in out
        plain = C.CatalogGrid([{'title': 'x'}])
        assert plain._picture_rows() == 0 and plain._card_rows() == 6
        coloured = C.CatalogGrid(self.items(), image_method='half',
                                 image_height=2, use_colors=True)
        coloured.focused = True
        assert '▸ Uno' in strip_ansi(coloured.render(width=80))
        # The Image objects are reused between frames.
        first = dict(coloured._images)
        coloured.render(width=80)
        assert dict(coloured._images) == first


# +---------------------------------------------------------------------------+
# 7. Images by URL with headers

class _Handler(http.server.BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        _Handler.seen.append((self.path, self.headers.get('Authorization'),
                              self.headers.get('X-Tenant')))
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/open.png')
            self.end_headers()
            return
        if self.path == '/secure.png' and \
                self.headers.get('Authorization') != 'Bearer s3cr3t':
            self.send_response(401)
            self.end_headers()
            return
        data = I.encode_png(picture(4, 2))
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def server():
    _Handler.seen = []
    srv = http.server.HTTPServer(('127.0.0.1', 0), _Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:{0}'.format(srv.server_address[1])
    srv.shutdown()
    srv.server_close()


class TestImageHeaders:
    def test_authorized_download(self, server):
        bm = I.load(server + '/secure.png',
                    headers={'Authorization': 'Bearer s3cr3t',
                             'X-Tenant': 't1'})
        assert (bm.width, bm.height) == (4, 2)
        assert _Handler.seen[-1] == ('/secure.png', 'Bearer s3cr3t', 't1')

    def test_unauthorized_error_hides_the_token(self, server):
        with pytest.raises(I.ImageError) as info:
            I.load(server + '/secure.png',
                   headers={'authorization': 'Bearer wrong-token'})
        assert 'HTTP 401' in str(info.value)
        assert 'wrong-token' not in str(info.value)
        img = C.Image(server + '/secure.png', alt='Foto', method='half',
                      headers={'Authorization': 'Bearer nope'},
                      use_colors=False)
        out = text(img, 60)
        assert 'nope' not in out and 'nope' not in (img.error or '')

    def test_token_not_sent_on_to_redirects(self, server):
        I.load(server + '/redirect', headers={'Authorization': 'Bearer t',
                                              'X-Tenant': 't2'})
        assert _Handler.seen[0] == ('/redirect', 'Bearer t', 't2')
        assert _Handler.seen[1] == ('/open.png', None, 't2')

    def test_components_pass_headers(self, server):
        img = C.Image(server + '/secure.png', alt='Foto',
                      headers={'Authorization': 'Bearer s3cr3t'})
        assert img.bitmap() is not None and img.error is None
        assert 's3cr3t' not in repr(vars(img).get('alt'))
        v = C.ImageViewer([server + '/secure.png'],
                          headers={'Authorization': 'Bearer s3cr3t'})
        assert v.current.bitmap() is not None
        g = C.CatalogGrid([{'title': 'x', 'image': server + '/secure.png'}],
                          image_headers={'Authorization': 'Bearer s3cr3t'},
                          image_method='ascii', use_colors=False)
        text(g, 40)
        assert all(auth == 'Bearer s3cr3t' for _, auth, _ in _Handler.seen)
        anim = C.Image(server + '/secure.png', animate=True,
                       headers={'Authorization': 'Bearer s3cr3t'})
        assert anim.bitmap() is not None

    def test_connection_error_reason(self):
        with pytest.raises(I.ImageError) as info:
            I.read_source('http://127.0.0.1:9/x.png', timeout=0.5,
                          headers={'Authorization': 'Bearer zzz'})
        assert 'zzz' not in str(info.value)


# +---------------------------------------------------------------------------+
# 8. ValidationSummary from a list of errors

class TestValidationSummaryList:
    def test_shapes(self):
        e = ValueError('Fecha inválida')
        vs = C.ValidationSummary(['Falta el total', ('sku', 'Requerido'),
                                  {'field': 'qty', 'message': 'Mayor a 0'},
                                  {'name': 'n', 'error': 'X'}, e],
                                 use_colors=False)
        assert vs.messages == ['Falta el total', 'Requerido', 'Mayor a 0',
                               'X', 'Fecha inválida']
        assert vs.errors == {'sku': 'Requerido', 'qty': 'Mayor a 0', 'n': 'X'}
        out = text(vs, 50)
        assert '• Falta el total' in out and '• sku: Requerido' in out
        assert 'Falta el total; sku: Requerido' in vs.a11y_value()
        assert not vs.focusable             # nothing to go to
        assert C.ValidationSummary('Un error').messages == ['Un error']
        assert C.ValidationSummary().render(width=20) == ''
        dict_vs = C.ValidationSummary({'a': 'b'})
        assert dict_vs.errors == {'a': 'b'}
        dict_vs.errors = []
        assert dict_vs.entries == [] and not dict_vs.activate()

    def test_focus_moves_to_the_field(self):
        picked = []
        sku = C.TextInput('SKU', name='sku')
        qty = C.NumberInput('Cantidad', name='qty')
        form = C.Form([sku, qty], use_colors=False)
        vs = C.ValidationSummary([('qty', 'Mayor a 0'), ('Nombre', 'x'),
                                  ('sku', 'Requerido')], fields=form,
                                 on_select=lambda f, i: picked.append((f, i)),
                                 use_colors=False)
        app = App(body=C.Stack([vs, form]))
        app.run(keys=[], size=(60, 24))
        assert vs.focusable
        app.focus(vs)
        out = strip_ansi(app.render(60, 24))
        assert '> qty: Mayor a 0' in out
        app.dispatch(key('enter'))
        assert app.focused is qty and picked == [('qty', qty)]
        app.focus(vs)
        for k in ('down', 'enter'):
            app.dispatch(key(k))
        assert picked[-1] == ('Nombre', None) and app.focused is vs
        app.dispatch(key('end'))
        app.dispatch(key('space'))
        assert app.focused is sku
        app.focus(vs)
        app.dispatch(key('home'))
        assert vs.index == 0 and not vs.handle_key(key('x'))
        # A click on an error line goes there too.
        vs.render(width=60)
        vs.on_mouse(MouseEvent(0, 4, 4, True))
        assert vs.index == 2

    def test_fields_as_list_and_labels(self):
        name = C.TextInput('Nombre completo', name='nombre')
        vs = C.ValidationSummary({'Nombre completo': 'Requerido'},
                                 fields=[name], use_colors=True)
        assert vs.find('Nombre completo') is name and vs.find(None) is None
        vs.focused = True
        raw = vs.render(width=50)
        assert '▸ Nombre completo' in strip_ansi(raw)
        assert vs.activate(0)
        assert C.ValidationSummary(['x'], on_select=print).focusable
        assert not C.ValidationSummary([]).handle_key(key('down'))


class TestCoverageEdges:
    def test_wizard_and_accordion_fields(self):
        a = C.TextInput('A', value='1')
        b = C.TextInput('B', value='2')
        c = C.TextInput('C', value='3')
        wiz = C.Wizard([('Uno', a), ('Dos', C.Stack([b])), ('Fin', 'texto')])
        acc = C.Accordion([('Sección', c), ('Nota', 'solo texto')])
        form = C.Form([wiz, acc])
        assert form.values() == {'a': '1', 'b': '2', 'c': '3'}

    def test_vstack_gap_scroll_and_foreign_focus(self):
        outside = C.TextInput('Fuera')
        inner = [C.TextInput('Campo {0}'.format(i)) for i in range(5)]
        st = C.VStack(inner, gap=1, height=5)
        app = App(body=C.Stack([outside, st]))
        app.run(keys=[], size=(40, 9))
        app.focus(outside)              # focus outside the stack: no jump
        app.render(40, 9)
        assert st.offset == 0 and st._holder() is None
        lone = C.VStack([Lines(9)], height=3)
        assert lone._holder() is None   # no app

    def test_signature_noops(self):
        s = C.SignatureInput(columns=3, rows=2)
        s.undo()
        s.erase((0, 0))
        assert s.strokes == [] and s.value == []
        s.begin((0, 0))
        s.extend((2, 0))
        s.erase((1, 0))                 # a stroke keeps its other cells
        assert s.cells() == {(0, 0), (2, 0)}
        s.erase((0, 0))
        s.erase((2, 0))
        assert s.value == []

    def test_cards_with_pixels(self, monkeypatch):
        term(monkeypatch, 'xterm-256color')
        g = C.CatalogGrid([{'title': 'Uno', 'image': picture()}],
                          image_height=2, image_method='half',
                          use_colors=True)
        out = strip_ansi(g.render(width=30))
        assert '▀' in out or '▄' in out
