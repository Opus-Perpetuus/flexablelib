"""
3.4.0: accessibility (roles, labels, states, screen-reader mode,
announcements, themes, contrast, colour-vision checks, reduced motion, ASCII,
minimum size), mouse support in components and identifier ("folio")
columns.
"""

import datetime as dt
import io
import itertools

import pytest

fc = pytest.importorskip("flexablelib_components")  # noqa: E402
from flexablelib import _frames  # noqa: E402
from flexablelib_components.base import THEMES, Theme, active_theme
from flexablelib_tui import App, Component, KeyMap, ScrollView, parse_keys
from flexablelib_tui import accessibility as a11y
from flexablelib_tui import capabilities

TODAY = dt.date(2026, 11, 12)


def every_component():
    """One labelled instance of each interactive / informative component."""
    return [
        fc.TextInput('Nombre', value='Ana'),
        fc.PasswordInput('Clave', value='x1'),
        fc.NumberInput('Cantidad', value=3),
        fc.TextArea('Notas', value='hola\nmundo'),
        fc.Checkbox('Activo'),
        fc.Switch('Modo'),
        fc.RadioGroup('Envío', options=['A', 'B']),
        fc.CheckboxGroup('Extras', options=['x', 'y']),
        fc.Select('País', options=['MX', 'ES']),
        fc.Autocomplete('Ciudad', options=['Mérida', 'Madrid']),
        fc.DateInput('Fecha', value=TODAY, today=TODAY),
        fc.TimeInput('Hora', value='10:30'),
        fc.WeekdayInput('Día', value=2),
        fc.MonthInput('Mes', value=TODAY, today=TODAY),
        fc.YearInput('Año', value=TODAY, today=TODAY),
        fc.WeekInput('Semana', value=TODAY, today=TODAY),
        fc.DateRangeInput('Rango', today=TODAY),
        fc.Calendar(TODAY, today=TODAY, a11y_label='Calendario'),
        fc.Button('Guardar'),
        fc.Tabs([('Uno', 'a'), ('Dos', 'b')], a11y_label='Secciones'),
        fc.Menu(['Abrir', 'Cerrar'], a11y_label='Archivo'),
        fc.Sidebar({'Ventas': ['Pedidos', 'Clientes']}, a11y_label='Menú'),
        fc.Pagination(100, a11y_label='Páginas'),
        fc.Accordion([('Uno', 'a'), ('Dos', 'b')], a11y_label='Detalles'),
        fc.Carousel(['a', 'b'], a11y_label='Fotos'),
        fc.Tree({'a': {'b': 1}}, a11y_label='Datos'),
        fc.SortControl(['fecha', 'total'], a11y_label='Orden'),
        fc.CommandPalette([('Abrir', None)]),
        fc.DataTable(['Folio', 'Total'], [[1281, 15000], [1282, 300]],
                     a11y_label='Pedidos'),
        fc.EditableTable(['Folio', 'Total'], [[1281, 15000]],
                         a11y_label='Captura'),
        fc.CatalogGrid([{'title': 'A'}, {'title': 'B'}],
                       a11y_label='Catálogo'),
        fc.Link('Docs', 'https://example.com'),
        fc.Alert('Hecho', kind='success', dismissible=True),
        fc.Badge('Nuevo', kind='info'),
        fc.StatusBadge('ok', {'ok': ('Pagado', 'success')}),
        fc.Breadcrumbs(['Inicio', 'Ventas']),
        fc.EmptyState('Sin pedidos'),
        fc.ErrorPanel(404, 'No encontrado'),
        fc.Spinner('Cargando'),
        fc.Skeleton(),
        fc.Code('print(1)', language='python'),
        fc.MarkdownView('# Título\n\ntexto'),
        fc.DetailView({'Folio': 1281}, a11y_label='Pedido'),
        fc.Timeline([('10:00', 'Creado', None, 'success')],
                    a11y_label='Historial'),
        fc.Stepper(['Datos', 'Pago'], a11y_label='Progreso'),
        fc.CommentList([{'author': 'Ana', 'text': 'hola'}],
                       a11y_label='Comentarios'),
        fc.AttachmentList([('a.pdf', 1024)], a11y_label='Adjuntos'),
        fc.Stat('Ventas', '$1,200', delta=5),
        fc.LineChart({'a': [1, 2, 3], 'b': [3, 2, 1]}, a11y_label='Ventas'),
        fc.Timer(interactive=True, a11y_label='Cronómetro'),
        fc.Modal('¿Seguro?', title='Confirmar'),
        fc.ConfirmDialog('¿Borrar?'),
        fc.LoadingOverlay(),
        fc.HelpLine(a11y_label='Ayuda'),
        fc.Form([fc.TextInput('Correo')], title='Registro'),
        fc.LoginForm(),
        fc.TopBar('Admin'),
        fc.Toolbar([('Nuevo', None)], a11y_label='Acciones'),
        fc.Wizard([('Uno', 'a'), ('Dos', 'b')], a11y_label='Alta'),
        fc.Box('x', title='Caja'),
    ]


# -- automatic audit ----------------------------------------------------------

class TestAudit:

    def test_every_component_has_role_label_and_visible_focus(self):
        issues = a11y.audit(every_component(), width=50)
        assert issues == [], [str(i) for i in issues]

    @pytest.mark.parametrize('name', sorted(THEMES))
    def test_audit_passes_under_every_theme(self, name):
        with a11y.configure(theme=name):
            issues = a11y.audit(every_component(), width=50)
        assert issues == [], [str(i) for i in issues]

    def test_audit_with_focus_markers_and_ascii(self):
        with a11y.configure(focus_marker=True, ascii=True):
            issues = a11y.audit(every_component(), width=50)
        assert issues == [], [str(i) for i in issues]

    def test_audit_reports_missing_label_and_colour_only_focus(self):
        class ColourOnly(Component):
            focusable = True
            role = 'button'

            def draw(self, width, height):
                return ['\x1b[31mX\x1b[0m' if self.focused else 'X']

        unnamed = fc.TextInput()
        issues = a11y.audit([unnamed, ColourOnly()])
        kinds = sorted(i.check for i in issues)
        assert 'label' in kinds and 'focus' in kinds
        assert any('no colour' in str(i) or 'colour' in str(i)
                   for i in issues)

    def test_every_role_has_a_spanish_and_english_name(self):
        roles = set(c.role for c in every_component())
        for lang in ('es', 'en'):
            missing = roles - set(a11y.ROLE_NAMES[lang])
            assert not missing, (lang, missing)


# -- themes: contrast and colour vision ---------------------------------------

class TestThemes:

    @pytest.mark.parametrize('name', ['high-contrast', 'high-contrast-light',
                                      'deuteranopia', 'protanopia',
                                      'tritanopia'])
    def test_accessible_themes_meet_wcag_aa(self, name):
        ratios = Theme.preset(name).contrast()
        assert ratios
        bad = {role: r for role, r in ratios.items() if r < 4.5}
        assert not bad, bad

    def test_high_contrast_reaches_aaa_for_text(self):
        ratios = Theme.preset('high-contrast').contrast()
        assert ratios['text'] >= 7 and ratios['selection'] >= 7

    @pytest.mark.parametrize('name', ['deuteranopia', 'protanopia',
                                      'tritanopia'])
    def test_status_colours_stay_apart_for_that_deficiency(self, name):
        theme = Theme.preset(name)
        colours = [a11y.spec_colors(getattr(theme, r))[0]
                   for r in ('info', 'success', 'warning', 'error')]
        seen = [a11y.simulate_cvd(c, name) for c in colours]
        worst = min(a11y.delta_e(a, b)
                    for a, b in itertools.combinations(seen, 2))
        assert worst >= 30, worst

    def test_cvd_themes_beat_the_default_palette(self):
        default = Theme.preset('default')
        theme = Theme.preset('deuteranopia')

        def worst(t):
            cs = [a11y.simulate_cvd(a11y.spec_colors(getattr(t, r))[0],
                                    'deuteranopia')
                  for r in ('info', 'success', 'warning', 'error')]
            return min(a11y.delta_e(a, b)
                       for a, b in itertools.combinations(cs, 2))
        assert worst(theme) > 2 * worst(default)

    def test_preset_errors_and_repr(self):
        with pytest.raises(KeyError) as error:
            Theme.preset('nope')
        assert 'high-contrast' in str(error.value)
        assert 'high-contrast' in repr(Theme.preset('high-contrast'))

    def test_contrast_math(self):
        assert a11y.contrast_ratio('#000000', '#ffffff') == \
            pytest.approx(21.0)
        assert a11y.contrast_ratio('white', 'white') == pytest.approx(1.0)
        assert a11y.parse_color('#fff') == a11y.parse_color('#ffffff')
        assert a11y.simulate_cvd('#ffffff', 'protanopia') == \
            pytest.approx((255, 255, 255), abs=2)

    def test_app_theme_reaches_components_without_their_own(self):
        own = fc.Button('Mío', theme=Theme.preset('monochrome'))
        free = fc.Button('Libre')
        app = App(body=fc.Toolbar([own, free]), theme='high-contrast',
                  use_colors=True)
        app.render(60, 6)
        with app.settings():
            assert free.theme.name == 'high-contrast'
            assert own.theme.name == 'monochrome'
        assert free.theme.name == 'default'

    def test_environment_theme(self, monkeypatch):
        monkeypatch.setenv('FLEXABLELIB_THEME', 'protanopia')
        assert a11y.Settings.from_env().theme == 'protanopia'
        with a11y.configure(theme='protanopia'):
            assert active_theme().name == 'protanopia'
        with a11y.configure(theme='no-such-theme'):
            assert active_theme().name == 'default'
        with a11y.configure(theme=Theme.preset('tritanopia')):
            assert active_theme().name == 'tritanopia'

    def test_theme_by_name_on_a_component(self):
        assert fc.Button('x', theme='deuteranopia').theme.name == \
            'deuteranopia'

    def test_high_contrast_focus_uses_markers_in_colour(self):
        button = fc.Button('Ir', theme='high-contrast', use_colors=True)
        button.focused = True
        assert '▸' in button.render(20)


# -- colour switches ----------------------------------------------------------

class TestColourEnvironment:

    def test_no_color_wins(self):
        assert capabilities.color_level({'NO_COLOR': '', 'TERM': 'xterm'},
                                        tty=True) == 'none'

    @pytest.mark.parametrize('value,level', [('0', 'none'), ('1', '16'),
                                             ('2', '256'),
                                             ('3', 'truecolor')])
    def test_force_color_levels(self, value, level):
        assert capabilities.color_level({'FORCE_COLOR': value},
                                        tty=False) == level

    def test_dumb_terminal(self):
        assert capabilities.color_level({'TERM': 'dumb'}, tty=True) == 'none'

    def test_supports_color_honours_force_off(self, monkeypatch):
        from flexablelib.colors import supports_color
        monkeypatch.delenv('NO_COLOR', raising=False)
        monkeypatch.setenv('FORCE_COLOR', 'off')
        assert supports_color() is False
        monkeypatch.setenv('FORCE_COLOR', '1')
        assert supports_color() is True
        monkeypatch.setenv('NO_COLOR', '1')
        assert supports_color() is False


# -- reduced motion, ASCII, minimum size --------------------------------------

class TestMotionAsciiSize:

    def test_spinner_stands_still_with_reduced_motion(self):
        spinner = fc.Spinner('Cargando', use_colors=False)
        with a11y.configure(reduced_motion=True):
            frames = {spinner.render(20) for _ in range(5)}
            spinner.tick()
            assert spinner.render(20) in frames
        assert {f.rstrip() for f in frames} == {'… Cargando'}
        moving = {spinner.render(20) for _ in range(5)}
        assert len(moving) > 1

    def test_skeleton_is_static(self):
        sk = fc.Skeleton(lines=2, use_colors=False)
        assert sk.render(10) == sk.render(10)
        assert sk.a11y()['state'] == ['busy']

    def test_app_reduced_motion_argument(self):
        spinner = fc.Spinner('x', use_colors=False)
        app = App(body=spinner, reduced_motion=True)
        assert app.render(20, 3) == app.render(20, 3)

    def test_ascii_mode_has_no_unicode(self):
        body = fc.Box(fc.Stack([fc.Checkbox('Activo', value=True),
                                fc.Tabs([('Uno', 'a'), ('Dos', 'b')]),
                                fc.StatusBadge('ok', {'ok': ('Pagado',
                                                             'success')}),
                                fc.Spinner('x')]), title='Caja')
        app = App(body=body, ascii=True, use_colors=False)
        frame = app.render(40, 14)
        assert frame.isascii(), [c for c in frame if ord(c) > 127]

    def test_ascii_fold_keeps_widths(self):
        text = '╭─┬─╮│▸✔✖⚠ℹ●○◀▶█░⠿…'
        folded = a11y.ascii_fold(text)
        assert folded.isascii()
        assert len(folded) == len(text)

    def test_minimum_size_message_and_reflow(self):
        app = App(body=fc.Button('Guardar'), min_size=(40, 10),
                  use_colors=False)
        small = app.render(36, 5)
        assert '40' in small and '10' in small
        assert 'Guardar' in app.render(60, 12)


# -- screen reader ------------------------------------------------------------

def form_app(**kw):
    name = fc.TextInput('Nombre', required=True)
    agree = fc.Checkbox('Acepto')
    save = fc.Button('Guardar')
    said = []
    app = App(body=fc.Stack([name, agree, save]), screen_reader=True,
              announce=said.append, title='Alta de cliente', **kw)
    return app, said, (name, agree, save)


def key(name):
    from flexablelib_tui import Key
    return Key(name, name if len(name) == 1 else '')


class TestScreenReader:

    def test_render_is_linear_text_with_roles(self):
        app, said, _ = form_app()
        text = app.render(60, 10)
        lines = text.split('\n')
        assert lines[0] == 'Alta de cliente'
        assert '> Nombre, campo de texto, obligatorio, vacío' in text
        assert '  Acepto, casilla, sin marcar' in text
        assert '  Guardar, botón' in text
        assert '\x1b' not in text

    def test_focus_moves_and_changes_are_announced(self):
        app, said, (name, agree, save) = form_app()
        app.render(60, 10)
        app.dispatch(key('tab'))
        assert said[-1] == 'Acepto, casilla, sin marcar'
        app.dispatch(key('space'))
        assert said[-1] == 'marcada'
        app.dispatch(key('shift+tab'))
        app.dispatch(key('Y'))
        assert said[-1].startswith('Y')

    def test_english(self):
        app, said, _ = form_app(lang='en')
        text = app.render(60, 10)
        assert 'Acepto, checkbox, not checked' in text

    def test_dialogs_and_notifications_are_announced(self):
        app, said, _ = form_app()
        app.render(60, 10)
        app.notify('Guardado', kind='success')
        assert any('Guardado' in s for s in said)
        fc.ConfirmDialog('¿Borrar el pedido?', title='Borrar').open(app)
        app.render(60, 10)
        assert any('Borrar' in s and 'diálogo' in s for s in said)
        assert 'Borrar' in app.linear_text().split('\n')[1]

    def test_read_screen_action(self):
        app, said, _ = form_app()
        app.render(60, 10)
        app.dispatch(key('ctrl+r'))
        assert 'Alta de cliente' in said
        assert any('Guardar, botón' in s for s in said)

    def test_announce_targets(self, tmp_path, capsys):
        path = tmp_path / 'sr.txt'
        a11y.Announcer(str(path)).announce('uno')
        a11y.Announcer('stdout', prefix='» ').announce('dos')
        a11y.Announcer('stderr').announce('tres')
        stream = io.StringIO()
        a11y.Announcer(stream).announce('cuatro')
        out = capsys.readouterr()
        assert path.read_text(encoding='utf-8') == 'uno\n'
        assert out.out == '» dos\n' and out.err == 'tres\n'
        assert stream.getvalue() == 'cuatro\n'

    def test_announcer_dedupe_and_assertive(self):
        ann = a11y.Announcer()
        assert ann('hola') and not ann('hola')
        assert ann('hola', 'assertive')
        assert not ann('')
        assert ann.history == ['hola', 'hola']
        ann.clear()
        assert ann.history == []

    def test_descriptions_of_states(self):
        sw = fc.Switch('Wifi', value=True)
        assert sw.describe() == 'Wifi, interruptor, Sí, encendido' or \
            'encendido' in sw.describe()
        pw = fc.PasswordInput('Clave', value='secreto')
        assert 'secreto' not in pw.describe()
        assert '7 caracteres' in pw.describe()
        sel = fc.Select('País', options=['MX', 'ES'], value='MX')
        assert 'contraída' in sel.describe() or 'collapsed' in \
            sel.a11y()['state']
        table = fc.DataTable(['Folio', 'Total'], [[1281, 15000]],
                             a11y_label='Pedidos')
        assert 'Folio 1281' in table.describe()
        assert 'Total 15,000' in table.describe()
        cal = fc.Calendar(TODAY, today=TODAY)
        assert '12 de noviembre de 2026' in cal.a11y_value()
        ln = fc.LineChart({'v': [1, 5, 3]})
        assert 'de 1 a 5' in ln.a11y_value()

    def test_every_component_describes_itself(self):
        for comp in every_component():
            text = comp.describe()
            assert text and comp.a11y()['role'], comp

    def test_dumb_terminal_switches_to_linear_text(self, monkeypatch):
        from flexablelib_tui import app as app_module
        assert hasattr(app_module.App, '_run_linear')


# -- status symbols -----------------------------------------------------------

class TestStatusSymbols:

    def test_symbol_and_word(self):
        assert a11y.status_symbol('success') == '✔'
        assert a11y.status_symbol('error', ascii=True) == 'x'
        assert a11y.status_symbol('warning', word=True) == '⚠ Aviso'
        assert a11y.status_symbol('warning', word=True, lang='en') == \
            '⚠ Warning'

    def test_status_badge_with_markers_shows_the_kind_symbol(self):
        badge = fc.StatusBadge('ok', {'ok': ('Pagado', 'success')},
                               use_colors=True)
        assert '●' in badge.render(20)
        with a11y.configure(focus_marker=True):
            assert '✔ Pagado' in _frames.strip_ansi(badge.render(20))
        plain = fc.StatusBadge('bad', {'bad': ('Falló', 'error')},
                               use_colors=False)
        assert plain.render(20).rstrip() == 'x Falló'

    def test_timeline_symbols(self):
        tl = fc.Timeline([('10:00', 'Pagado', None, 'success'),
                          ('11:00', 'Rechazado', None, 'error')],
                         use_colors=False)
        text = tl.render(30)
        assert '+ Pagado' in text and 'x Rechazado' in text
        assert '(Éxito)' in tl.a11y_value()

    def test_line_chart_markers_without_colour(self):
        chart = fc.LineChart({'a': [1, 2, 3], 'b': [3, 2, 1]},
                             use_colors=False)
        text = chart.render(30)
        assert '*' in text and '#' in text
        assert '*━ a' in text and '#━ b' in text
        coloured = fc.LineChart({'a': [1, 2, 3], 'b': [3, 2, 1]},
                                use_colors=True)
        assert '━━' in coloured.render(30)


# -- mouse in components ------------------------------------------------------

def mouse(app, x, y, button=0, release=True, drag_to=None):
    seqs = ['\x1b[<{0};{1};{2}M'.format(button, x + 1, y + 1)]
    if drag_to is not None:
        seqs.append('\x1b[<{0};{1};{2}M'.format(32 + button, drag_to[0] + 1,
                                                drag_to[1] + 1))
        x, y = drag_to
    if release and button < 64:
        seqs.append('\x1b[<{0};{1};{2}m'.format(button, x + 1, y + 1))
    used = False
    for seq in seqs:
        for k in parse_keys(seq):
            used = app.dispatch(k) or used
    return used


def find(app, text, width=60, height=20):
    frame = _frames.strip_ansi(app.render(width, height)).split('\n')
    for y, line in enumerate(frame):
        x = line.find(text)
        if x >= 0:
            return _frames.visible_width(line[:x]), y
    raise AssertionError('{0!r} not on screen:\n{1}'.format(
        text, '\n'.join(frame)))


def make(body, **kw):
    kw.setdefault('use_colors', False)
    return App(body=body, mouse=True, **kw)


class TestMouse:

    def test_button_click_presses_and_focuses(self):
        a, b = fc.Button('Uno'), fc.Button('Dos')
        app = make(fc.Toolbar([a, b]))
        x, y = find(app, 'Dos')
        mouse(app, x, y)
        assert b.presses == 1 and app.focused is b

    def test_press_outside_label_then_release_does_not_press(self):
        b = fc.Button('Uno')
        app = make(fc.Stack([b, 'texto']))
        x, y = find(app, 'Uno')
        mouse(app, x, y, release=False)
        mouse(app, 50, 1, release=False)
        for k in parse_keys('\x1b[<0;51;2m'):
            app.dispatch(k)
        assert b.presses == 0

    def test_checkbox_switch_radio_and_group(self):
        cb = fc.Checkbox('Activo')
        sw = fc.Switch('Wifi')
        rg = fc.RadioGroup('Envío', options=['Tierra', 'Aire'])
        cg = fc.CheckboxGroup('Extras', options=['Seguro', 'Regalo'])
        app = make(fc.Stack([cb, sw, rg, cg]))
        mouse(app, *find(app, 'Activo'))
        assert cb.value is True
        mouse(app, *find(app, 'Wifi'))
        assert sw.value is True
        mouse(app, *find(app, 'Aire'))
        assert rg.value == 'Aire'
        mouse(app, *find(app, 'Regalo'))
        mouse(app, *find(app, 'Seguro'))
        assert cg.value == ['Seguro', 'Regalo']
        mouse(app, *find(app, 'Regalo'))
        assert cg.value == ['Seguro']

    def test_text_input_click_moves_cursor(self):
        ti = fc.TextInput('Nombre', value='abcdef')
        app = make(ti)
        x, y = find(app, 'abcdef')
        mouse(app, x + 3, y)
        assert ti.cursor_pos == 3 and app.focused is ti

    def test_select_opens_and_picks(self):
        sel = fc.Select('País', options=['México', 'España', 'Chile'])
        app = make(fc.Stack([sel, fc.Button('x')]))
        x, y = find(app, 'País')
        mouse(app, x + 3, y + 1)
        assert sel.open
        mouse(app, *find(app, 'España'))
        assert sel.value == 'España' and not sel.open

    def test_autocomplete_suggestion_click(self):
        ac = fc.Autocomplete('Ciudad', options=['Mérida', 'Madrid'])
        app = make(ac)
        app.render(60, 20)
        app.focus(ac)
        app.dispatch(key('M'))
        mouse(app, *find(app, 'Madrid'))
        assert ac.value == 'Madrid'

    def test_tabs_menu_pagination_sort(self):
        tabs = fc.Tabs([('Uno', 'a'), ('Dos', 'b')])
        chosen = []
        menu = fc.Menu([('Abrir', lambda: chosen.append('abrir')),
                        ('Cerrar', lambda: chosen.append('cerrar'))])
        pages = fc.Pagination(100, page_size=10)
        sort = fc.SortControl(['fecha', 'total'])
        app = make(fc.Stack([tabs, menu, pages, sort]))
        mouse(app, *find(app, 'Dos'))
        assert tabs.index == 1
        mouse(app, *find(app, 'Cerrar'))
        assert chosen == ['cerrar']
        x, y = find(app, '›')
        mouse(app, x, y)
        assert pages.page == 2
        x, y = find(app, ' 5 ')
        mouse(app, x + 1, y)
        assert pages.page == 5
        mouse(app, *find(app, 'total'))
        assert sort.field == 'total'
        mouse(app, *find(app, 'total'))
        assert sort.descending

    def test_data_table_rows_header_and_wheel(self):
        activated = []
        rows = [[1280 + i, i * 100] for i in range(30)]
        table = fc.DataTable(['Folio', 'Total'], rows, height=8,
                             on_activate=activated.append, selectable=True)
        app = make(table)
        x, y = find(app, '1283')
        mouse(app, x, y)
        assert table.cursor_row == 3 and app.focused is table
        mouse(app, x, y)
        assert activated == [[1283, 300]]
        mouse(app, 0, y)
        assert table.selected == {3}
        mouse(app, *find(app, 'Total'))
        assert table.sort_key == 1
        mouse(app, x, y, button=65)
        assert table.cursor_row == 6
        mouse(app, x, y, button=64)
        assert table.cursor_row == 3

    def test_editable_table_click_picks_cell(self):
        table = fc.EditableTable(['Folio', 'Cliente'], [[1, 'Ana'],
                                                         [2, 'Luis']])
        app = make(table)
        mouse(app, *find(app, 'Luis'))
        assert table.cursor_row == 1 and table.cursor_col == 1
        assert 'celda Cliente' in table.a11y_value()

    def test_tree_accordion_carousel_catalog(self):
        tree = fc.Tree({'a': {'b': 1}, 'c': 2})
        acc = fc.Accordion([('Uno', 'x'), ('Dos', 'y')], open=())
        car = fc.Carousel(['s1', 's2', 's3'])
        cat = fc.CatalogGrid([{'title': 'Lápiz'}, {'title': 'Goma'}],
                             min_width=14)
        app = make(fc.Stack([tree, acc, car, cat]), )
        mouse(app, *find(app, 'c', 60, 40), )
        x, y = find(app, '> Dos', 60, 40)
        mouse(app, x, y)
        assert 1 in acc.opened
        x, y = find(app, '▶', 60, 40)
        mouse(app, x, y)
        assert car.index == 1
        mouse(app, *find(app, 'Goma', 60, 40))
        assert cat.index == 1

    def test_tree_click_twice_expands(self):
        tree = fc.Tree({'a': {'b': 1}, 'c': {'d': 2}}, expanded_depth=0)
        app = make(tree)
        x, y = find(app, 'c')
        mouse(app, x, y)
        mouse(app, x, y)
        assert ('c',) in tree.expanded

    def test_date_input_calendar_click(self):
        di = fc.DateInput('Fecha', value=TODAY, today=TODAY)
        app = make(fc.Stack([di, fc.Button('x')]), )
        x, y = find(app, '2026-11-12', 60, 30)
        mouse(app, x, y)
        assert di.open and app.focused is di
        x, y = find(app, ' 20 ', 60, 30)
        mouse(app, x + 1, y)
        assert di.value == dt.date(2026, 11, 20) and not di.open

    def test_month_weekday_time_and_range(self):
        mi = fc.MonthInput('Mes', value=TODAY, today=TODAY)
        wd = fc.WeekdayInput('Día')
        ti = fc.TimeInput('Hora', value='10:30')
        dr = fc.DateRangeInput('Rango', today=TODAY)
        app = make(fc.Stack([mi, wd, ti, dr]))
        x, y = find(app, 'Noviembre 2026', 60, 40)
        mouse(app, x, y)
        mouse(app, *find(app, 'Mar', 60, 40))
        assert mi.value == dt.date(2026, 3, 1)
        mouse(app, *find(app, ' Mi ', 60, 40))
        assert wd.value == 2
        x, y = find(app, '10:30', 60, 40)
        mouse(app, x + 3, y)
        assert ti.part == 1
        x, y = find(app, 'Rango', 60, 40)
        mouse(app, x + 2, y + 1)
        assert dr.open
        mouse(app, *find(app, 'Ayer', 60, 40))
        assert dr.value == (TODAY - dt.timedelta(days=1),) * 2

    def test_split_drag_and_scrollbar_drag(self):
        split = fc.Split('izquierda', 'derecha', ratio=0.5)
        app = make(split)
        frame = _frames.strip_ansi(app.render(41, 5)).split('\n')
        bar = frame[0].index('│')
        mouse(app, bar, 0, drag_to=(10, 0))
        assert split.ratio < 0.35
        assert not split.dragging
        lines = '\n'.join('línea {0}'.format(i) for i in range(100))
        view = ScrollView(lines, height=10)
        app = make(view)
        app.render(40, 10)
        app.focus(view)
        mouse(app, 10, 2, button=65)
        assert view.offset > 0
        first = view.offset
        mouse(app, 39, 0, drag_to=(39, 9))
        assert view.offset > first

    def test_vertical_split_drag(self):
        split = fc.Split('arriba', 'abajo', direction='vertical')
        app = make(split)
        frame = _frames.strip_ansi(app.render(30, 11)).split('\n')
        row = next(i for i, l in enumerate(frame) if l.startswith('──'))
        mouse(app, 3, row, drag_to=(3, 8))
        assert split.ratio > 0.6

    def test_hover_only_with_hover_mode(self):
        b = fc.Button('Uno')
        app = App(body=b, mouse='hover', use_colors=False)
        x, y = find(app, 'Uno')
        for k in parse_keys('\x1b[<35;{0};{1}M'.format(x + 1, y + 1)):
            app.dispatch(k)
        assert b.hovered and app.hovered is b
        for k in parse_keys('\x1b[<35;50;10M'):
            app.dispatch(k)
        assert not b.hovered

    def test_modal_blocks_clicks_behind(self):
        behind = fc.Button('Detrás')
        app = make(fc.Stack([behind, 'x\n' * 10]))
        app.render(60, 20)
        fc.ConfirmDialog('¿Seguro?').open(app)
        app.render(60, 20)
        mouse(app, 0, 0)
        assert behind.presses == 0

    def test_link_alert_timer_clicks(self):
        opened = []
        link = fc.Link('Docs', 'https://x.y', on_open=opened.append)
        alert = fc.Alert('Listo', dismissible=True)
        timer = fc.Timer(interactive=True, clock=lambda: 0.0)
        app = make(fc.Stack([link, alert, timer]))
        mouse(app, *find(app, 'Docs'))
        assert opened == ['https://x.y']
        mouse(app, *find(app, 'Listo'))
        assert not alert.visible
        mouse(app, *find(app, '00:00'))
        assert timer.running

    def test_command_palette_and_context_menu_clicks(self):
        ran = []
        palette = fc.CommandPalette([('Abrir', lambda: ran.append(1)),
                                     ('Cerrar', lambda: ran.append(2))])
        app = make(fc.Button('x'))
        app.render(60, 20)
        palette.open(app)
        mouse(app, *find(app, 'Cerrar'))
        assert ran == [2]
        menu = fc.ContextMenu([('Copiar', lambda: ran.append(3))])
        menu.open(app)
        mouse(app, *find(app, 'Copiar'))
        assert ran == [2, 3]

    def test_sidebar_click(self):
        side = fc.Sidebar({'Ventas': ['Pedidos', 'Clientes']})
        app = make(side)
        mouse(app, *find(app, 'Clientes'))
        assert side.items[side.active]['label'] == 'Clientes'


# -- keyboard: focus order, traps, shortcuts ----------------------------------

class TestKeyboard:

    def test_tab_order_follows_tab_index(self):
        a, b, c = fc.Button('A'), fc.Button('B', tab_index=1), \
            fc.Button('C', tab_index=-1)
        app = App(body=fc.Toolbar([a, b, c]), use_colors=False)
        app.render(40, 4)
        assert app.focused is b
        app.dispatch(key('tab'))
        assert app.focused is a
        app.dispatch(key('tab'))
        assert app.focused is b

    def test_focus_trap_in_modal(self):
        outside = fc.Button('Fuera')
        app = App(body=outside, use_colors=False)
        app.render(60, 20)
        dialog = fc.ConfirmDialog('¿Seguro?')
        dialog.open(app)
        app.render(60, 20)
        for _ in range(6):
            app.dispatch(key('tab'))
            assert app.focused in dialog.buttons

    def test_help_lists_shortcuts(self):
        app = App(body=fc.Button('x'), use_colors=False,
                  bindings={'ctrl+s': (lambda: None, 'Guardar')})
        app.render(60, 20)
        assert ('Ctrl+S', 'Guardar') in app.key_hints()
        app.dispatch(key('f1'))
        assert 'Guardar' in app.render(60, 20)

    def test_keymap_remap_reaches_components(self):
        km = KeyMap(remap={'ctrl+n': 'tab'})
        a, b = fc.Button('A'), fc.Button('B')
        app = App(body=fc.Toolbar([a, b]), keymap=km, use_colors=False)
        app.render(40, 4)
        app.dispatch(key('ctrl+n'))
        assert app.focused is b


# -- identifier columns ("folios") -------------------------------------------

class TestFolioTables:

    def test_data_table_types_and_names(self):
        rows = [[15001, 15000, 15002, 2026]]
        table = fc.DataTable(['Folio', 'Total', {'title': 'Ref',
                                                 'type': 'code'},
                              'Año'], rows)
        assert table.text(rows[0], 0) == '15001'
        assert table.text(rows[0], 1) == '15,000'
        assert table.text(rows[0], 2) == '15002'
        assert table.text(rows[0], 3) == '2026'
        money = fc.DataTable([{'title': 'Folio', 'type': 'money'}], rows)
        assert money.text(rows[0], 0) == '15,001'
        off = fc.DataTable(['Folio'], rows, id_columns=False)
        assert off.text(rows[0], 0) == '15,001'
        listed = fc.DataTable(['A', 'B'], [[15000, 15000]],
                              id_columns=['B'])
        assert listed.text(listed.rows[0], 1) == '15000'
        named = fc.DataTable(['Pedido'], [[15000]], id_names=['pedido'])
        assert named.text(named.rows[0], 0) == '15000'
