"""3.7.1: fixes found testing the 3.6.0 / 3.7.0 components -- narrow forms,
catalog cards with small heights, the signature pad's eraser and value,
stopwatch lap numbers, menus and sidebars drawn shorter than max_visible,
VStack following the focus inside tall children, DataTable pages taller
than their slot, one-line status bars and image download errors that must
not quote a header."""

import http.server
import threading

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib import _images as I  # noqa: E402
from flexablelib_tui import App, Key, ScrollView  # noqa: E402
from flexablelib_tui import accessibility as a11y  # noqa: E402
from flexablelib_tui.keys import MouseEvent  # noqa: E402
from flexablelib.text_width import strip_ansi, visible_width  # noqa: E402


@pytest.fixture(autouse=True)
def plain_a11y():
    with a11y.configure(screen_reader=False, ascii=False, reduced_motion=False,
                        focus_marker=False):
        yield


def key(name):
    if name == 'space':
        return Key('space', ' ')
    if len(name) == 1:
        return Key(name, name)
    return Key(name)


def lines(comp, width=30, height=None):
    return strip_ansi(comp.render(width=width, height=height)).split('\n')


def same_width(out, width):
    return all(visible_width(line) == width for line in out)


# +---------------------------------------------------------------------------+
# Form at narrow widths

class TestNarrowForm:
    def fields(self):
        return [C.TextInput('Nombre', name='a'), C.TextInput('B', name='b'),
                C.TextInput('C', name='c')]

    @pytest.mark.parametrize('columns', [2, 3, 4])
    @pytest.mark.parametrize('width', [1, 2, 3, 4, 5, 7])
    def test_columns_never_fail(self, columns, width):
        form = C.Form(self.fields(), columns=columns, use_colors=False)
        assert same_width(lines(form, width), width)
        row = C.Form([tuple(self.fields())], use_colors=False)
        assert same_width(lines(row, width), width)

    @pytest.mark.parametrize('width', [1, 2, 3, 5, 8])
    def test_grid_layout_never_fails(self, width):
        a, b, c = self.fields()
        form = C.Form([C.FormCell(a, span=2), b, c], columns=4,
                      use_colors=False)
        assert same_width(lines(form, width), width)
        assert 1 <= form.grid_columns(width) <= max(1, (width + 2) // 3)

    def test_fields_that_do_not_fit_stack(self):
        form = C.Form(self.fields(), columns=3, use_colors=False)
        out = lines(form, 7)
        labels = [l for l in out if l.strip()[:1] in ('N', 'B', 'C')]
        assert labels[0].split() == ['N', 'B', 'C']
        wide = lines(form, 60)
        assert 'Nombre' in wide[0] and 'B' in wide[0]
        assert form.grid_columns(60) == 3 and form.grid_columns(1) == 1


# +---------------------------------------------------------------------------+
# CatalogGrid with small cards

class TestCatalogSmallCards:
    ITEMS = [{'title': 'Uno', 'price': 1}, {'title': 'Dos'},
             {'title': 'Tres', 'subtitle': 'x'}]

    @pytest.mark.parametrize('card_height', [-1, 0, 1, 2])
    def test_tiny_card_height(self, card_height):
        g = C.CatalogGrid(self.ITEMS, card_height=card_height, min_width=8,
                          use_colors=False)
        assert g._card_rows() == 3
        for height in (None, 1, 2, 5):
            out = lines(g, 30, height)
            assert same_width(out, 30)
        assert any('Uno' in l for l in lines(g, 30, 3))

    @pytest.mark.parametrize('min_width', [-5, -1, 0])
    def test_non_positive_min_width(self, min_width):
        g = C.CatalogGrid(self.ITEMS, min_width=min_width, use_colors=False)
        assert same_width(lines(g, 20, 6), 20)


# +---------------------------------------------------------------------------+
# SignatureInput

class TestSignature:
    def test_erasing_lifts_the_pen(self):
        s = C.SignatureInput('Firma', columns=10, rows=3)
        s.focused = True
        for k in ['space', 'right', 'right', 'space', 'right', 'right',
                  'right', 'space']:
            s.handle_key(key(k))
        assert s.value == [[(0, 0), (1, 0), (2, 0)], [(5, 0)]]
        assert s.pen_down
        s.handle_key(key('x'))                # erases the dot under the pen
        assert not s.pen_down
        assert s.value == [[(0, 0), (1, 0), (2, 0)]]
        s.handle_key(key('right'))            # pen up: draws nothing
        assert s.value == [[(0, 0), (1, 0), (2, 0)]]
        assert s.to_text()[0] == '###       '
        s.handle_key(key('space'))            # down again: a new stroke
        s.handle_key(key('right'))
        assert s.value == [[(0, 0), (1, 0), (2, 0)], [(6, 0), (7, 0)]]

    def test_erase_in_the_middle_of_a_stroke(self):
        s = C.SignatureInput(columns=6, rows=1)
        s.begin((0, 0))
        s.extend((5, 0))
        s.pen = (2, 0)
        s.pen_down = True
        s.erase((2, 0))
        assert not s.pen_down
        assert s.cells() == {(0, 0), (1, 0), (3, 0), (4, 0), (5, 0)}

    def test_value_is_a_copy(self):
        s = C.SignatureInput('Firma', columns=5, rows=2, name='firma')
        form = C.Form([s])
        s.begin((0, 0))
        collected = form.values()
        s.extend((3, 0))
        s.begin((1, 1))
        assert collected == {'firma': [[(0, 0)]]}
        got = []
        s2 = C.SignatureInput(columns=4, rows=1, on_change=got.append)
        s2.begin((0, 0))
        s2.extend((2, 0))
        assert got == [[[(0, 0)]], [[(0, 0), (1, 0), (2, 0)]]]
        v = s2.value
        v[0].append((3, 0))
        v.append([(9, 9)])
        assert s2.strokes == [[(0, 0), (1, 0), (2, 0)]]
        s2.value = [[(1, 0)]]
        assert s2.value == [[(1, 0)]] and not s2.is_empty()

    def test_submitted_snapshot(self):
        got = []
        s = C.SignatureInput('Firma', columns=5, rows=2, name='firma')
        s.begin((0, 0))
        C.Form([s], on_submit=got.append).submit()
        s.extend((4, 1))
        assert got == [{'firma': [[(0, 0)]]}]


# +---------------------------------------------------------------------------+
# Stopwatch lap numbers

class TestStopwatchLaps:
    def test_numbers_follow_the_laps_dropped(self):
        now = [0.0]
        w = C.Stopwatch('t', clock=lambda: now[0], max_laps=3,
                        use_colors=False)
        w.start()
        for _ in range(10):
            now[0] += 1
            w.lap()
        out = [l.strip() for l in lines(w, 40)]
        assert out[2:] == ['8. 00:00:08.0', '9. 00:00:09.0',
                           '10. 00:00:10.0']
        w.reset()
        now[0] += 1
        w.lap()
        assert [l.strip() for l in lines(w, 40)][2] == '1. 00:00:01.0'

    def test_without_max_laps_shows_the_last_five(self):
        now = [0.0]
        w = C.Stopwatch('t', clock=lambda: now[0], use_colors=False)
        w.start()
        for _ in range(7):
            now[0] += 1
            w.lap()
        out = [l.strip() for l in lines(w, 40)]
        assert out[2].startswith('3. ') and out[-1].startswith('7. ')
        w.laps = []                       # set from code: numbered from 1
        assert len(lines(w, 40)) == 2


# +---------------------------------------------------------------------------+
# Menu and Sidebar shorter than max_visible

class TestMenuWindow:
    @pytest.mark.parametrize('height', [1, 2, 3, 4])
    def test_current_item_stays_in_view(self, height):
        m = C.Menu(['Op{0:02d}'.format(i) for i in range(20)], max_visible=8,
                   use_colors=False)
        m.focused = True
        for _ in range(13):
            m.handle_key(key('down'))
        out = lines(m, 20, height)
        assert len(out) == height
        assert any('Op13' in l for l in out)
        if height >= 3:
            assert out[0].startswith(' ^') and out[-1].startswith(' v')

    def test_counts_add_up(self):
        m = C.Menu(['Op{0:02d}'.format(i) for i in range(20)], max_visible=8,
                   use_colors=False)
        m.focused = True
        for _ in range(10):
            m.handle_key(key('down'))
        out = lines(m, 20, 5)
        shown = [l for l in out if 'Op' in l]
        above = int(out[0].split()[1])
        below = int(out[-1].split()[1])
        assert above + len(shown) + below == 20
        assert m._page == 3                   # a page is the window shown
        m.render(width=20, height=5)
        m.on_mouse(MouseEvent(0, 2, 4, True))  # the ▼ line pages down
        assert m.index > 10

    def test_max_visible_smaller_than_height(self):
        m = C.Menu(['Op{0:02d}'.format(i) for i in range(20)], max_visible=4,
                   use_colors=False)
        assert len(lines(m, 20, 10)) == 4

    @pytest.mark.parametrize('height', [1, 2, 3])
    def test_sidebar_short_with_title(self, height):
        picked = []
        sb = C.Sidebar({'Sec': ['Uno', 'Dos', 'Tres', 'Cuatro', 'Cinco']},
                       title='Menú', use_colors=False,
                       on_select=lambda i, item: picked.append(item['label']))
        sb.focused = True
        sb.handle_key(key('down'))
        sb.handle_key(key('down'))
        out = lines(sb, 12, height)
        assert len(out) == height
        row = [n for n, l in enumerate(out) if 'Tres' in l]
        assert row
        if height >= 2:
            assert 'Menú' in out[0]
        sb.on_mouse(MouseEvent(0, 3, row[0], True))
        assert picked == ['Tres']

    def test_sidebar_max_visible_and_height(self):
        sb = C.Sidebar({'A': ['a{0}'.format(i) for i in range(15)]},
                       max_visible=10, use_colors=False)
        sb.focused = True
        sb.handle_key(key('end'))
        out = lines(sb, 12, 5)
        assert len(out) == 5 and 'a14' in out[-1]


# +---------------------------------------------------------------------------+
# VStack

def run_app(body, size):
    app = App(body=body)
    app.run(keys=[], size=size)
    return app


class TestVStackFocus:
    def test_follows_the_component_inside_a_tall_child(self):
        fields = [C.TextInput('Campo{0}'.format(i)) for i in range(4)]
        vs = C.VStack([C.Stack(fields)])
        app = run_app(vs, (24, 4))
        for i in range(1, 4):
            app.dispatch(key('tab'))
            frame = strip_ansi(app.render(24, 4))
            assert app.focused is fields[i]
            assert 'Campo{0}'.format(i) in frame
        app.dispatch(key('shift+tab'))
        app.dispatch(key('shift+tab'))
        assert 'Campo1' in strip_ansi(app.render(24, 4))

    def test_fixed_height_taller_than_the_slot(self):
        fields = [C.TextInput('Campo{0}'.format(i)) for i in range(3)]
        vs = C.VStack([C.Stack(fields[:1]), C.Stack(fields[1:])], height=6)
        app = run_app(vs, (24, 3))
        assert vs.view_height == 3
        while app.focused is not fields[2]:
            app.dispatch(key('tab'))
        assert 'Campo2' in strip_ansi(app.render(24, 3))
        lines(vs, 24, 10)
        assert vs.view_height == 6               # a taller slot: its own

    def test_growing_child_keeps_a_row(self):
        view = ScrollView('\n'.join('línea {0}'.format(i) for i in range(9)))
        top = C.Stack([C.TextInput('A'), C.TextInput('B')])
        vs = C.VStack([top, view])
        app = run_app(vs, (24, 4))
        assert vs.heights[1] >= 1
        app.focus(view)
        frame = strip_ansi(app.render(24, 4))
        assert 'línea' in frame
        # weights given: a child with weight keeps a row too, unless capped.
        capped = C.VStack([C.Stack([C.TextInput('A'), C.TextInput('B')]),
                           ScrollView('x')], max_heights=[None, 0])
        capped.render(width=20, height=4)
        assert capped.heights[1] == 0

    def test_sharing_unchanged_when_there_is_room(self):
        a = C.DataTable(['n'], [[i] for i in range(30)], fill=True)
        b = C.DataTable(['n'], [[i] for i in range(30)], fill=True)
        vs = C.VStack([a, b])
        vs.render(width=20, height=20)
        assert vs.heights == [10, 10]


# +---------------------------------------------------------------------------+
# DataTable pages taller than the slot

class TestDataTablePages:
    def cursor_line(self, out):
        return [l for l in out if l.startswith('>')]

    @pytest.mark.parametrize('height', [4, 5, 6, 8])
    def test_cursor_row_in_view(self, height):
        t = C.DataTable(['id'], [[i] for i in range(23)], page_size=10,
                        fill=True, use_colors=False)
        t.focused = True
        for steps in (0, 7, 9, 12, 22):
            t.cursor_row = steps
            out = lines(t, 20, height)
            assert len(out) == height
            current = self.cursor_line(out)
            assert current and current[0].split() == ['>', str(steps)] or \
                current and current[0][1:].split() == [str(steps)]
            assert 'pág. {0}/3'.format(steps // 10 + 1) in out[-1]
            shown = [int(l[1:].split()[0]) for l in out[2:-1]
                     if l[1:].split() and l[1:].split()[0].isdigit()]
            # Only rows of the current page.
            assert all(n // 10 == steps // 10 for n in shown)

    def test_page_fits_unchanged(self):
        t = C.DataTable(['id'], [[i] for i in range(23)], page_size=5,
                        use_colors=False)
        t.cursor_row = 7
        out = lines(t, 20, 20)
        assert [l.split()[0] for l in out[2:7]] == ['5', '6', '7', '8', '9']
        assert t.top == 5 and t.visible_rows == 5

    def test_height_attribute_smaller_than_page(self):
        t = C.DataTable(['id'], [[i] for i in range(30)], page_size=10,
                        height=3, use_colors=False)
        t.focused = True
        t.handle_key(key('end'))
        out = lines(t, 20)
        assert any(l.startswith('>') and '29' in l for l in out)
        t.handle_key(key('pageup'))
        assert t.cursor_row == 19
        out = lines(t, 20)
        assert any(l.startswith('>') and '19' in l for l in out)


# +---------------------------------------------------------------------------+
# StatusLine

class TestStatusLineOneLine:
    def test_line_breaks_and_tabs(self):
        s = C.StatusLine('a\nb', 'c\r\nd', 'e\tf', use_colors=False)
        out = s.render(width=20)
        assert '\n' not in out and '\t' not in out
        assert visible_width(out) == 20
        assert s.parts() == ('a b', 'c d', 'e f')
        assert s.a11y_value() == 'a b · c d · e f'
        assert C.StatusLine(lambda: 'x\u2028y').parts()[0] == 'x y'

    def test_right_text_stays_in_view(self):
        s = C.StatusLine('Guardando el archivo de clientes', '', '12/40',
                         kind='info', use_colors=False)
        for width in (10, 12, 20, 30):
            out = strip_ansi(s.render(width=width))
            assert out.endswith('12/40 ') and visible_width(out) == width
            assert '…' in out
        assert strip_ansi(s.render(width=80)).startswith(
            ' ℹ Guardando el archivo de clientes')
        # Too narrow for both: the left text wins, as before.
        assert strip_ansi(s.render(width=6)).startswith(' ℹ')


# +---------------------------------------------------------------------------+
# Image download errors never quote a header

class _Handler(http.server.BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        _Handler.seen.append(self.headers.get('Authorization'))
        data = I.encode_png(I.Bitmap(1, 1, b'\x00\x00\x00\xff'))
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


class TestImageHeaderErrors:
    @pytest.mark.parametrize('value', ['Bearer SECRETO\r\nX-Otro: 1',
                                       'Bearer SE\nCRETO'])
    def test_invalid_value_not_quoted(self, value):
        with pytest.raises(I.ImageError) as info:
            I.read_source('http://127.0.0.1:9/x.png', timeout=0.5,
                          headers={'Authorization': value})
        assert 'SECRETO' not in str(info.value) and \
            'CRETO' not in str(info.value)
        assert 'cabecera no válida' in str(info.value)
        assert info.value.__suppress_context__

    def test_invalid_name_not_quoted(self):
        with pytest.raises(I.ImageError) as info:
            I.read_source('http://127.0.0.1:9/x.png', timeout=0.5,
                          headers={'X-SECRETO\n': 'v'})
        assert 'SECRETO' not in str(info.value)

    def test_value_with_a_trailing_newline_is_trimmed(self, server):
        bm = I.load(server + '/x.png',
                    headers={'Authorization': 'Bearer s3cr3t\n'})
        assert (bm.width, bm.height) == (1, 1)
        assert _Handler.seen == ['Bearer s3cr3t']

    def test_other_errors(self):
        with pytest.raises(I.ImageError) as info:
            I.read_source('http://127.0.0.1:9/x.png', timeout=0.5)
        assert 'no se pudo descargar' in str(info.value)
        with pytest.raises(I.ImageError) as info:
            I.read_source('http://127.0.0.1:9/a b\x01.png', timeout=0.5)
        assert 'no se pudo descargar' in str(info.value)


# +---------------------------------------------------------------------------+
# Public API branches without tests until now

class TestUncoveredBranches:
    def test_form_and_catalog_a11y(self):
        form = C.Form([C.TextInput('Nombre', name='n', required=True)],
                      title='Alta')
        assert form.a11y_value() == '' and form.a11y_name() == 'Alta'
        form.validate()
        assert form.a11y_value() == '1 errores'
        assert C.CatalogGrid([]).a11y_value() == 'Sin elementos'
        g = C.CatalogGrid([{'title': 'Pan', 'price': 12.5}, {'title': 'Sal'}])
        assert g.a11y_value() == 'Pan (1 de 2), precio 12.5'
        g.index = 1
        assert g.a11y_value() == 'Sal (2 de 2)'

    def test_datatable_page_scrolls_back_up(self):
        t = C.DataTable(['id'], [[i] for i in range(30)], page_size=10,
                        use_colors=False)
        t.focused = True
        t.cursor_row = 9
        lines(t, 20, 5)
        assert t.top == 8                 # 2 rows fit: 8 and 9
        t.cursor_row = 3                  # above the window, same page
        out = lines(t, 20, 5)
        assert t.top == 3 and out[2].startswith('>')

    def test_toast_and_help_close_on_click_and_key(self):
        app = App(body=C.Stack([C.TextInput('A')]))
        app.run(keys=[], size=(40, 10))
        app.notify('Guardado', kind='success', seconds=60)
        app.render(40, 10)
        toast = [n for n in app.walk() if type(n).__name__ == '_Toast']
        assert len(toast) == 1
        assert not toast[0].on_mouse(MouseEvent(0, 0, 0, False))
        assert toast[0].on_mouse(MouseEvent(0, 0, 0, True))
        assert not [n for n in app.walk() if type(n).__name__ == '_Toast']
        app.show_help()
        top = app._modal()
        assert type(top).__name__ == '_Help'
        assert top.on_mouse(MouseEvent(0, 0, 0, True))
        assert app._modal() is None
        app.show_help()
        top = app._modal()
        assert not top.on_mouse(MouseEvent(0, 0, 0, False))
        assert top.handle_key(key('x')) and app._modal() is None

    def test_file_input_a11y_when_open(self, tmp_path):
        (tmp_path / 'b.txt').write_text('x')
        (tmp_path / 'a').mkdir()
        f = C.FileInput('Archivo', directory=str(tmp_path))
        assert 'collapsed' in f.a11y_state()
        f.focused = True
        f.handle_key(key('enter'))
        assert f.open and 'expanded' in f.a11y_state()
        assert f.a11y_value().endswith('(carpeta)') or \
            f.a11y_value() in ('..', 'a', 'b.txt')
