"""3.7.0: a ScrollView that follows the focus, menus and sidebars that keep
to their height, responsive form columns with spans and minimum widths,
tables that fill their slot, a grid component with an accessible name and
its own audit, and a status line with the status role."""

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib import Card  # noqa: E402
from flexablelib.layout import GridCell  # noqa: E402
from flexablelib_tui import (App, Key, ScrollView,  # noqa: E402
                             accessibility as a11y)
from flexablelib_tui.keys import MouseEvent  # noqa: E402
from flexablelib.text_width import strip_ansi  # noqa: E402


def key(name):
    if len(name) == 1:
        return Key(name, name)
    return Key(name)


@pytest.fixture(autouse=True)
def plain_a11y():
    with a11y.configure(screen_reader=False, ascii=False, reduced_motion=False,
                        focus_marker=False):
        yield


def lines(comp, width=30, height=None):
    return [l.rstrip() for l in
            strip_ansi(comp.render(width=width, height=height)).split('\n')]


# 9. ScrollView follows the focus

class TestScrollViewFocus:
    def test_follows_tab(self):
        fields = [C.TextInput('Campo {0}'.format(i)) for i in range(10)]
        view = ScrollView(C.Stack(fields), height=6)
        app = App(body=view)
        app.run(keys=[], size=(40, 6))
        while app.focused is not fields[7]:
            app.dispatch(key('tab'))
        frame = strip_ansi(app.render(40, 6))
        assert 'Campo 7' in frame
        assert view.offset > 0
        assert view.focus_rows(39) is not None
        view.scroll_to(0)                      # by hand: left alone
        app.render(40, 6)
        assert view.offset == 0
        app.dispatch(key('tab'))               # focus moves again: follows
        app.render(40, 6)
        assert 'Campo 8' in strip_ansi(app.render(40, 6))
        while app.focused is not fields[1]:
            app.dispatch(key('tab'))
            app.render(40, 6)
        assert view.offset <= 4

    def test_off_and_edges(self):
        fields = [C.TextInput('Campo {0}'.format(i)) for i in range(10)]
        view = ScrollView(C.Stack(fields), height=6, follow_focus=False)
        app = App(body=view)
        app.run(keys=[], size=(40, 6))
        for _ in range(8):
            app.dispatch(key('tab'))
        app.render(40, 6)
        assert view.offset == 0
        assert ScrollView('texto').focus_rows(10) is None
        lone = ScrollView(C.TextInput('x'))
        assert lone.focus_rows(10) is None          # no app
        big = C.TextArea('Notas', '\n'.join('l%d' % i for i in range(20)),
                         rows=15)
        tall = ScrollView(C.Stack([C.TextInput('a'), big]), height=5)
        app2 = App(body=tall)
        app2.run(keys=[], size=(30, 5))
        app2.focus(big)
        app2.render(30, 5)
        assert tall.offset == tall.focus_rows(29)[0]


# 10. Menu and Sidebar keep to the height

class TestMenuHeight:
    def test_menu_window(self):
        picked = []
        m = C.Menu(['Opción {0}'.format(i) for i in range(20)],
                   on_select=lambda i, it: picked.append(i), use_colors=False)
        out = lines(m, 20, 6)
        assert len(out) == 6 and out[-1] == ' v 15 más'
        m.focused = True
        for _ in range(10):
            m.handle_key(key('down'))
        out = lines(m, 20, 6)
        assert out[0].startswith(' ^') and out[-1].startswith(' v')
        assert any('Opción 10' in l for l in out)
        assert m.handle_key(key('pagedown')) and m.index == 14
        assert m.handle_key(key('scrollup')) and m.index == 11
        m.handle_key(key('end'))
        out = lines(m, 20, 6)
        assert 'Opción 19' in out[-1] and out[0].startswith(' ^')
        m.render(width=20, height=6)
        m.on_mouse(MouseEvent(0, 2, 0, True))     # click the ▲ line: page up
        assert m.index < 19
        m.render(width=20, height=6)
        m.on_mouse(MouseEvent(0, 2, 2, True))     # an item: selects it
        assert picked
        for _ in range(30):
            m.handle_key(key('pagedown'))
        assert m.index == 19
        for _ in range(30):
            m.handle_key(key('pageup'))
        assert m.index == 0
        m.render(width=20, height=6)
        m.on_mouse(MouseEvent(0, 2, 5, True))     # the ▼ line: page down
        assert m.index > 0
        assert len(lines(m, 20, 2)) == 2           # too short for arrows
        assert C.Menu([]).handle_key(key('pagedown')) is False

    def test_coloured_arrows_and_max_visible(self):
        m = C.Menu(['x%d' % i for i in range(9)], max_visible=4,
                   use_colors=True)
        assert '▼ 6 más' in strip_ansi(m.render(width=20))

    def test_sidebar_window(self):
        sections = {'Ventas': ['V%d' % i for i in range(10)],
                    'Compras': ['C%d' % i for i in range(10)]}
        sb = C.Sidebar(sections, title='Menú', use_colors=False)
        out = lines(sb, 20, 8)
        assert len(out) == 8 and out[0] == ' Menú' and \
            out[-1].startswith(' v')
        sb.focused = True
        for _ in range(15):
            sb.handle_key(key('down'))
        out = lines(sb, 20, 8)
        assert out[0] == ' Menú' and out[2].startswith(' ^')
        assert any('C' in l and '>' in l for l in out)
        sb.render(width=20, height=8)
        sb.on_mouse(MouseEvent(0, 3, 4, True))
        assert sb.active == sb.index
        app = App(body=C.AppShell(sidebar=sb, content='hola'))
        app.run(keys=[], size=(40, 8))
        assert len(app.last_frame.split('\n')) == 8
        full = C.Sidebar({'A': ['a', 'b']}, use_colors=False)
        out = lines(full, 20, 10)
        assert out[:3] == [' A', '*a', ' b'] and not any(
            l.startswith((' ^', ' v')) for l in out)


# 11. Form: responsive columns, spans, minimum widths

class TestFormGrid:
    def make(self, **kw):
        a = C.TextInput('Nombre')
        b = C.TextInput('Apellido')
        c = C.TextInput('Dirección')
        d = C.TextInput('CP')
        form = C.Form([a, b, C.FormCell(c, span=2), 'Más',
                       C.FormCell(d, min_width=30)], columns=2,
                      use_colors=False, cancel_label=None, **kw)
        return form, (a, b, c, d)

    def test_spans_and_min_width(self):
        form, (a, b, c, d) = self.make()
        out = lines(form, 60)
        assert 'Nombre' in out[0] and 'Apellido' in out[0]
        addr = [l for l in out if 'Dirección' in l][0]
        assert 'CP' not in addr
        cp = [l for l in out if l.startswith('CP')]
        assert cp                         # 29 < 30: takes the whole row
        assert form.fields() == [a, b, c, d]
        assert form.grid_columns(60) == 2

    def test_responsive_columns(self):
        form, _ = self.make(min_column_width=30)
        assert form.grid_columns(70) == 2 and form.grid_columns(50) == 1
        out = lines(form, 50)
        nombre = [l for l in out if 'Nombre' in l][0]
        assert 'Apellido' not in nombre
        wide = lines(form, 80)
        assert any('Nombre' in l and 'Apellido' in l for l in wide)

    def test_tuple_rows_and_set_layout(self):
        a, b, c = C.TextInput('A'), C.TextInput('B'), C.TextInput('C')
        form = C.Form([(a, b), c], columns=3, use_colors=False)
        form.set_layout(c, span=3)
        out = lines(form, 60)
        assert any(l.startswith('A') and 'B' in l for l in out)
        assert form._draw_grid(60)
        assert C.FormCell(a, span=0).span == 1


# 12. DataTable fits the height

class TestTableHeight:
    def test_fill_in_a_vstack(self):
        t = C.DataTable(['n'], [[i] for i in range(50)], fill=True,
                        use_colors=False)
        st = C.VStack([C.TextInput('Buscar'), t], height=12)
        assert st.weights == [0, 1]
        app = App(body=st)
        app.run(keys=[], size=(30, 12))
        app.focus(t)
        for _ in range(20):
            app.dispatch(key('down'))
        frame = [l.rstrip() for l in strip_ansi(app.render(30, 12))
                 .split('\n')]
        assert len(frame) == 12 and frame[-1] == '21/50'
        assert t.visible_rows == 12 - 2 - 2 - 1
        assert any(l.strip() == '> 20' or l.startswith('> 20') or
                   '20' in l for l in frame)

    def test_fill_pads_short_tables(self):
        t = C.DataTable(['n'], [[1], [2]], fill=True, use_colors=False)
        out = lines(t, 20, 8)
        assert len(out) == 8 and out[-1] == '1/2' and t.expand
        assert C.DataTable(['n'], []).visible_rows == 10


# 13. GridView

class TestGridView:
    def test_name_role_and_audit(self):
        ok = C.Button('Guardar', lambda: None)
        field = C.TextInput('Nombre')
        g = C.GridView([Card('A', 'a'), (field, 1), GridCell(ok)],
                       title='Tablero', columns=3, use_colors=False)
        info = g.a11y()
        assert info['role'] == 'group' and info['label'] == 'Tablero'
        assert info['value'] == '3 elementos'
        assert g.children()[1:] == [field, ok]
        out = lines(g, 60)
        assert out[0] == 'Tablero' and 'Nombre' in ' '.join(out)
        assert g.audit(width=30) == []
        assert g.natural_width() > 0
        assert len(lines(g, 60, 3)) == 3
        app = App(body=g)
        app.run(keys=['tab'], size=(60, 6))
        assert app.focused in (field, ok)

    def test_audit_reports(self):
        class Plain(C.Box.__mro__[1]):
            focusable = True
            role = 'button'

            def draw(self, width, height):
                return [self.paint('x', 'cyan' if self.focused else 'blue')]
        g = C.GridView([Plain(), C.Stack([C.Image(b'', alt=None)])],
                       role='grid')
        checks = sorted(i.check for i in g.audit())
        assert checks.count('label') >= 3          # grid, button, image
        assert 'focus' in checks and g.a11y()['role'] == 'grid'
        named = C.GridView(['x'], a11y_label='Resumen')
        assert named.a11y_name() == 'Resumen' and named.children() == []


# 14. StatusLine

class TestStatusLine:
    def test_render_and_role(self):
        clock = ['12:00']
        sl = C.StatusLine('Listo', center='3 elementos',
                          right=lambda: clock[0], kind='success',
                          use_colors=False)
        out = strip_ansi(sl.render(width=40))
        assert out.startswith(' ✔ Listo') and out.endswith('12:00 ')
        assert '3 elementos' in out
        info = sl.a11y()
        assert info['role'] == 'status' and info['label'] == 'Estado'
        assert info['value'] == 'Éxito: Listo · 3 elementos · 12:00'
        clock[0] = '12:01'
        assert '12:01' in sl.render(width=40)
        coloured = C.StatusLine('x', use_colors=True)
        assert '\x1b[' in coloured.render(width=20)
        assert coloured.natural_width() >= 3
        assert C.StatusLine(a11y_label='Barra').a11y_name() == 'Barra'
        assert C.StatusLine(kind='error').a11y_value() == 'Error'
        assert C.StatusLine(left=None).parts() == ('', '', '')

    def test_announces_changes(self):
        said = []
        sl = C.StatusLine('Listo')
        app = App(body=sl)
        app.announce = lambda text, priority='polite': said.append(
            (text, priority))
        app.run(keys=[], size=(30, 2))
        sl.message('Guardado', 'success')
        sl.set(kind='error', left='Sin conexión')
        sl.set(center='')                         # nothing new: silent
        assert said == [('Éxito: Guardado', 'polite'),
                        ('Error: Sin conexión', 'assertive')]
        quiet = C.StatusLine('x', announce=False)
        quiet.app = app
        quiet.set(left='y', right='z', kind=None)
        assert len(said) == 2 and quiet.parts() == ('y', '', 'z')
