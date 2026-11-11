"""
3.1.0: cards, grids, border titles and responsive tables.

Everything is checked on what a user sees: visible widths, the glyphs on the
frame, which columns survive, how many cards sit side by side, and whether a
background reaches the frame.
"""

import re

import pytest

from flexablelib import Card, Grid, GridCell, Table
from flexablelib.colors import RESET, parse_spec
from flexablelib.layout import add_shadow, inset_label, wrap_panel
from flexablelib.style_compositions import __style_compositions as STYLES
from flexablelib.text_width import strip_ansi, visible_width

ALL_STYLES = list(STYLES._fields)
THEMES = sorted(Table.THEMES)

HEADERS = ['Nombre', 'Grupo', 'Edad', 'Ciudad', 'Correo', 'Pts']
ROWS = [
    ['Ana', 'Norte', 28, 'Guadalajara', 'ana@example.com', 12],
    ['Luna 🌸', 'Centro', 22, 'Mérida', 'luna@example.com', 15],
    ['José', 'Norte', 35, '東京', 'jose@example.com', 18],
]


def people(**settings):
    table = Table(headers=HEADERS)
    for row in ROWS:
        table.add_row(row)
    for name, value in settings.items():
        setattr(table, name, value)
    return table


def widths(text):
    return {visible_width(line) for line in text.split('\n')}


def card(**kw):
    kw.setdefault('use_colors', False)
    return Card(title='Ana 🌸', subtitle='Norte',
                fields=[('Edad', 28), ('Ciudad', '東京 Mérida'), ('Pts', 12)],
                footer='hoy', **kw)


# +--------------------------------------------------------------+ Card

@pytest.mark.parametrize('style', ALL_STYLES)
@pytest.mark.parametrize('width', [14, 22, 37])
def test_card_lines_share_one_width_in_every_style(style, width):
    for chrome in ({}, {'panel': True}, {'shadow': True},
                   {'panel': 'double', 'shadow': True}):
        text = card(style_name=style, **chrome).render(width=width)
        assert widths(text) == {width}, (style, chrome, text)


@pytest.mark.parametrize('style', ALL_STYLES)
def test_card_height_stretches_exactly(style):
    c = card(style_name=style, actions=['Ver'])
    natural = c.render(width=30).count('\n') + 1
    for height in (natural, natural + 4):
        lines = c.render(width=30, height=height).split('\n')
        assert len(lines) == height
        assert {visible_width(line) for line in lines} == {30}


def test_card_title_sits_in_the_top_border_when_the_style_has_one():
    text = card(style_name='rounded').render(width=30)
    first = text.split('\n')[0]
    assert first.startswith('╭─ Ana 🌸 ─') and first.endswith('╮')
    # No top rule: the title opens the card instead.
    borderless = card(style_name='borderless').render(width=30)
    assert borderless.split('\n')[0].strip() == 'Ana 🌸'


def test_card_title_alignment_and_inside_position():
    right = card(title_align='r').render(width=30).split('\n')[0]
    assert right.endswith('─ Ana 🌸 ─╮')
    centre = card(title_align='c').render(width=30).split('\n')[0]
    left_pad = centre.index('Ana') - 1
    assert abs(left_pad - (30 - centre.index('🌸') - 2)) <= 3
    inside = card(title_position='inside').render(width=30).split('\n')
    assert set(inside[0][1:-1]) == {'─'}
    assert 'Ana 🌸' in inside[1]


def test_card_fields_in_a_grid_of_tiles():
    c = Card(title='Pedido', fields=[('Cliente', 'José'), ('Total', '$1,200'),
                                    ('Estado', 'Enviado'), ('Fecha', '11/11')],
             field_columns=2, use_colors=False)
    lines = c.render(width=36).split('\n')
    assert 'Cliente' in lines[1] and 'Total' in lines[1]
    assert 'José' in lines[2] and '$1,200' in lines[2]
    assert 'Estado' in lines[3] and 'Fecha' in lines[3]
    auto = Card(fields=[(k, 1) for k in 'abcd'], field_columns='auto',
                use_colors=False)
    assert 'a' in auto.render(width=40).split('\n')[1]
    assert 'd' in auto.render(width=40).split('\n')[1]
    assert 'b' not in auto.render(width=8).split('\n')[1]


def test_card_values_wrap_instead_of_overflowing():
    c = Card(title='T', fields={'Nota': 'una nota bastante larga ' * 3},
             use_colors=False)
    text = c.render(width=24)
    assert widths(text) == {24}
    assert text.count('\n') > 4


def test_card_body_holds_any_renderable():
    inner = people(style_name='single', hide_columns=('Correo', 'Grupo'))
    c = Card(title='Equipo', body=inner, use_colors=False)
    text = c.render(width=60)
    assert widths(text) == {60}
    assert '┌' in text and 'Luna 🌸' in text


def test_card_actions_are_right_aligned_chips():
    text = card(actions=['Ver', 'Editar']).render(width=30)
    line = [l for l in text.split('\n') if '[ Ver ]' in l][0]
    assert line.rstrip('│ ').endswith('[ Editar ]')


def test_card_validation():
    with pytest.raises(ValueError):
        Card(style_name='no_such_style')
    with pytest.raises(ValueError):
        Card(field_columns=0)
    with pytest.raises(TypeError):
        Card(fields=[1, 2])
    with pytest.raises(ValueError):
        Card(title_position='floating')
    with pytest.raises(ValueError):
        Card(fields={'a': 1}, use_colors=False).render(width=2)


# +-------------------------------------------------------------- colours

def _check_fill(line, fill_prefix):
    """Every visible column between the frame carries ``fill_prefix``."""
    # Walk the line tracking whether the fill is open.
    open_fill = False
    column = 0
    plain = strip_ansi(line)
    width = len(plain)
    for token in re.split(r'(\x1b\[[0-9;]*m)', line):
        if not token:
            continue
        if token.startswith('\x1b['):
            if token == RESET:
                open_fill = False
            elif token == fill_prefix or fill_prefix in token:
                open_fill = True
            continue
        for _ in token:
            if 0 < column < width - 1:
                assert open_fill, (column, repr(line))
            column += 1


@pytest.mark.parametrize('theme', THEMES)
def test_card_themes_keep_widths_and_never_double_reset(theme):
    c = card(theme=theme, use_colors=True)
    c.use_colors = True
    text = c.render(width=32)
    assert widths(text) == {32}
    assert RESET + RESET not in text


def test_card_background_fills_every_interior_column():
    c = card(color='white on #1e293b', border_color='cyan',
             use_colors=True, zebra=('', 'on #334155'))
    fill = parse_spec('white on #1e293b')
    stripe = parse_spec('on #334155')
    for line in c.render(width=30).split('\n')[1:-1]:
        plain = strip_ansi(line)
        if set(plain[1:-1]) <= set('─├┤'):
            continue
        open_ok = fill in line
        assert open_ok, repr(line)
        _check_fill(line, fill if stripe not in line else stripe)
    assert RESET + RESET not in c.render(width=30)


def test_card_value_with_its_own_colour_keeps_the_fill():
    c = Card(fields={'a': '\x1b[31mrojo\x1b[0m'}, color='on #1e293b',
             use_colors=True)
    line = c.render(width=20).split('\n')[1]
    fill = parse_spec('on #1e293b')
    assert '\x1b[0m' + fill in line
    _check_fill(line, fill)


def test_card_colours_off():
    text = card(theme='neon', use_colors=False).render(width=30)
    assert '\x1b' not in text


# +--------------------------------------------------------- panel/shadow

def test_card_and_table_share_panel_and_shadow_chrome():
    block = 'ab\ncde'
    assert wrap_panel(block).split('\n') == ['╭───╮', '│ab │', '│cde│',
                                             '╰───╯']
    assert add_shadow(block).split('\n') == ['ab  ', 'cde░', ' ░░░']
    table = people(style_name='single', panel='double', shadow=True)
    lines = str(table).split('\n')
    assert lines[0].startswith('╔') and lines[-1].startswith(' ░')
    c = card(panel='heavy', shadow='▒').render(width=30).split('\n')
    assert c[0].startswith('┏') and c[-1] == ' ' + '▒' * 29


# +------------------------------------------------------- table titles

def test_border_title_never_covers_a_junction():
    plain = people(style_name='single')
    titled = people(style_name='single', title='Personas',
                    title_position='border')
    top_plain = str(plain).split('\n')[0]
    top = str(titled).split('\n')[0]
    assert 'Personas' in top
    assert len(top) == len(top_plain)
    for i, char in enumerate(top_plain):
        if char in '┌┬┐':
            assert top[i] == char


def test_border_title_falls_back_above_when_it_cannot_fit():
    table = people(style_name='single', title='Un título muy largo aquí, sí',
                   title_position='border', title_align='l')
    lines = str(table).split('\n')
    assert lines[0].strip() == 'Un título muy largo aquí, sí'
    assert lines[1].startswith('┌──')
    # No top rule at all: the title stays above.
    md = people(style_name='psql', title='T', title_position='border')
    assert str(md).split('\n')[0].strip() == 'T'


def test_border_caption_and_subtitle():
    table = people(style_name='rounded', title='Personas', subtitle='2026',
                   caption='3 filas', caption_position='border',
                   title_position='border')
    lines = strip_ansi(str(table)).split('\n')
    assert lines[0].strip() == '2026'
    assert 'Personas' in lines[1] and lines[1].startswith('╭')
    assert '3 filas' in lines[-1] and lines[-1].startswith('╰')


def test_title_align_left_and_right_above():
    left = people(title='T', title_align='l')
    assert str(left).split('\n')[0] == 'T'
    right = people(title='T', title_align='r')
    first, second = str(right).split('\n')[:2]
    assert len(first) == visible_width(second)


def test_border_title_in_colour_reopens_the_border_colour():
    table = people(style_name='single', border_color='cyan', use_colors=True,
                   title='Personas', title_position='border',
                   title_color='bold yellow')
    top = str(table).split('\n')[0]
    assert parse_spec('bold yellow') + ' Personas ' + RESET + \
        parse_spec('cyan') in top
    assert RESET + RESET not in str(table)


def test_inset_label_helper():
    assert inset_label('┌──────────┐', 'Hi', 'l') == '┌─ Hi ─────┐'
    assert inset_label('┌──────────┐', 'Hi', 'r') == '┌───── Hi ─┐'
    assert inset_label('┌──┬──┐', 'Hi', 'c') is None
    # 'l' / 'r' take the first stretch long enough from their side.
    assert inset_label('┌──┬──────────┬──┐', 'Hi', 'l') == '┌──┬─ Hi ─────┬──┐'
    assert inset_label('┌──┬──────────┬──┐', 'Hi', 'r') == '┌──┬───── Hi ─┬──┐'
    assert inset_label('      ', 'Hi') is None


# +--------------------------------------------------------- responsive

def test_render_switches_table_compact_hidden_cards():
    table = people(style_name='rounded', column_priority={'Correo': 3,
                                                          'Grupo': 2})
    natural = table.natural_width()
    assert table.render_mode(natural) == 'table'
    # Hiding a low-priority column comes before squeezing every column.
    assert table.render_mode(natural - 10) == 'hidden'
    assert table.render_mode(45) == 'hidden'
    plain = people(style_name='rounded')
    assert plain.render_mode(natural - 10) == 'compact'
    squeezed = plain.render(width=natural - 10)
    assert 'Correo' in squeezed and max(widths(squeezed)) <= natural - 10
    assert table.render_mode(20) == 'cards'
    hidden = table.render(width=45)
    assert 'Correo' not in hidden and widths(hidden) <= set(range(46))
    cards = strip_ansi(table.render(width=30))
    assert cards.count('╭─ ') == 3
    assert widths(cards) <= set(range(31))


@pytest.mark.parametrize('width', [100, 70, 50, 40, 30, 22])
def test_render_never_exceeds_the_width(width):
    table = people(style_name='double_frame_rows', title='Personas',
                   column_priority={'Correo': 2})
    assert max(widths(table.render(width=width))) <= width


def test_cards_breakpoint_and_card_options():
    table = people(breakpoints={'cards': 80},
                   card_options={'subtitle_field': 'Grupo',
                                 'fields': ['Edad', 'Ciudad']})
    assert table.render_mode(79) == 'cards'
    assert table.render_mode(120) == 'table'
    text = table.render(width=79)
    assert 'Correo' not in text and 'Norte' in text
    table.breakpoints = 50
    assert table.breakpoints == {'cards': 50}
    with pytest.raises(ValueError):
        table.breakpoints = {'phone': 3}


def test_cards_sit_side_by_side_when_they_fit():
    table = people(breakpoints={'cards': 500}, style_name='rounded',
                   card_options={'min_width': 30})
    first = table.render(width=100).split('\n')[0]
    assert first.count('╭') == 3
    first = table.render(width=64).split('\n')[0]
    assert first.count('╭') == 2


def test_responsive_flag_makes_str_responsive(terminal):
    terminal(30)
    table = people(responsive=True, style_name='rounded')
    assert '─ Ana ─' in strip_ansi(str(table))
    assert Table(headers=['a'], responsive=True).responsive


def test_to_cards_uses_formatted_values_and_column_colours():
    table = people(float_format='.1f', use_colors=True,
                   column_colors={'Pts': 'green'}, header_color='bold red')
    table.add_row(['Sin', None, None, None, None, None])
    cards = table.to_cards(title_field='Nombre', subtitle_field='Grupo',
                           footer_field='Correo')
    assert len(cards) == 4
    assert cards[0].title == 'Ana' and cards[0].subtitle == 'Norte'
    assert cards[0].footer == 'ana@example.com'
    assert [label for label, _ in cards[0].fields] == ['Edad', 'Ciudad',
                                                        'Pts']
    assert cards[0].value_colors == {'Pts': 'green'}
    assert cards[0].title_color == 'bold red'
    assert cards[3].fields[0] == ('Edad', '')
    with pytest.raises(KeyError):
        table.to_cards(title_field='Nope')


def test_hidden_columns_do_not_take_width_from_the_fit():
    table = people(hide_columns=('Correo',), max_width=48)
    text = str(table)
    assert 'Guadalajara' in text  # nothing had to wrap
    assert max(widths(text)) <= 48


# +--------------------------------------------------------------- Grid

def _cards(n=3):
    return [card(style_name='single') for _ in range(n)]


@pytest.mark.parametrize('width,expected', [(100, 3), (62, 2), (40, 1)])
def test_grid_reflows_columns(width, expected):
    grid = Grid(_cards(), min_width=28)
    assert grid.column_count(width) == expected
    first = grid.render(width=width).split('\n')[0]
    assert first.count('┌') == expected
    assert max(widths(grid.render(width=width))) <= width


def test_grid_fixed_columns_and_min_width():
    grid = Grid(_cards(4), columns=2)
    assert grid.render(width=80).split('\n')[0].count('┌') == 2
    grid.min_width = 50
    assert grid.column_count(80) == 1


def test_grid_spans_nesting_and_equal_heights():
    tall = Card(title='Alta', fields=[(str(i), i) for i in range(6)],
                use_colors=False)
    short = Card(title='Baja', fields={'a': 1}, use_colors=False)
    layout = Grid([
        GridCell('Encabezado del tablero', span=3),
        GridCell(people(style_name='single', hide_columns=('Correo',)),
                 span=2),
        Grid([tall, short], columns=1, row_gap=0),
        (short, 1), tall,
    ], columns=3, gap=2)
    text = layout.render(width=110)
    lines = text.split('\n')
    assert lines[0] == 'Encabezado del tablero'
    assert max(widths(text)) <= 110
    row = Grid([tall, short], columns=2).render(width=60).split('\n')
    assert row[-1].count('╰') == 2  # both cards close on the same line


def test_grid_strings_wrap_and_empty_grid():
    grid = Grid(['palabra ' * 10], columns=1)
    assert max(widths(grid.render(width=20))) <= 20
    assert Grid().render(width=20) == ''
    with pytest.raises(ValueError):
        Grid(columns=0)


def test_card_inside_grid_inside_card():
    inner = Grid(_cards(2), columns=2, gap=1)
    outer = Card(title='Panel', body=inner, use_colors=False)
    text = outer.render(width=70)
    assert widths(text) == {70}
    assert text.split('\n')[1].count('┌') == 2


# +--------------------------------------------------------- README

def test_readme_card_example():
    card_ = Card(title='Ana', subtitle='Norte',
                 fields={'Edad': 28, 'Ciudad': 'Guadalajara'},
                 footer='actualizado hoy', use_colors=False)
    assert card_.render(width=30) == '\n'.join([
        '╭─ Ana ──────────────────────╮',
        '│ Norte                      │',
        '├────────────────────────────┤',
        '│ Edad    28                 │',
        '│ Ciudad  Guadalajara        │',
        '├────────────────────────────┤',
        '│ actualizado hoy            │',
        '╰────────────────────────────╯',
    ])


def test_readme_responsive_example():
    table = Table(headers=['Nombre', 'Grupo', 'Edad', 'Ciudad', 'Correo'])
    table.add_row(['Ana', 'Norte', 28, 'Guadalajara', 'ana@example.com'])
    table.add_row(['Luna 🌸', 'Centro', 22, 'Mérida', 'luna@example.com'])
    table.style_name = 'rounded'
    table.title, table.title_position = 'Personas', 'border'
    table.use_colors = False
    table.column_priority = {'Correo': 3}
    table.card_options = {'subtitle_field': 'Grupo',
                          'fields': ['Edad', 'Ciudad']}
    assert table.render(width=80).split('\n')[0] == (
        '╭─────────┬────────┬──────┬─ Personas ──┬──────────────────╮')
    assert 'Correo' not in table.render(width=46)
    assert table.render(width=30).split('\n')[:2] == [
        '           Personas', '╭─ Ana ──────────────────────╮']


# +------------------------------------------------- options and edges

def test_setters_validate():
    table = people()
    for name, value, error in (
            ('title_position', 'top', ValueError),
            ('caption_position', 'top', ValueError),
            ('title_align', 'middle', ValueError),
            ('breakpoints', 'wide', TypeError),
            ('breakpoints', {'cards': 0}, ValueError),
            ('column_priority', [1], TypeError),
            ('column_priority', {'Pts': 0}, ValueError),
            ('card_options', [1], TypeError)):
        with pytest.raises(error):
            setattr(table, name, value)
    table.title_position = None
    table.caption_position = None
    table.breakpoints = None
    table.column_priority = None
    table.card_options = None
    assert (table.title_position, table.caption_position) == ('above',
                                                               'below')
    assert table.breakpoints == {} and table.column_priority == {}
    assert table.card_options == {}
    with pytest.raises(ValueError):
        Grid(['x']).render(width=0)
    with pytest.raises(ValueError):
        Card(field_layout='zigzag', fields={'a': 1}).render(width=20)


def test_empty_table_renders_as_a_table():
    assert Table().render_mode(10) == 'table'
    assert Table(headers=['a']).to_cards() == []


def test_render_defaults_to_max_width_then_terminal(terminal):
    table = people(style_name='rounded')
    terminal(40)
    assert table.render_mode() == 'cards'
    table.max_width = 300
    assert table.render_mode() == 'table'


def test_cards_view_keeps_subtitle_and_caption_and_column_options():
    table = people(title='Personas', subtitle='2026', caption='fin',
                   use_colors=False, breakpoints={'cards': 999},
                   card_options={'columns': 1, 'gap': 1})
    lines = table.render(width=100).split('\n')
    assert lines[0].strip() == 'Personas' and lines[1].strip() == '2026'
    assert lines[-1].strip() == 'fin'
    assert lines[2].count('+-') == 1  # columns=1 even with room for more


def test_card_options_and_theme_edges():
    c = Card(fields={'a': 1}).add_field('b', None)
    assert c.fields == [('a', 1), ('b', None)]
    plain = Card(title='T', fields={'a': 1}, theme='plain')
    assert plain.use_colors is False and plain.title_color is None
    with pytest.raises(ValueError):
        Card(theme='sparkly')
    bounded = Card(title='T', fields={'a': 'x' * 50}, max_width=20)
    assert bounded.natural_width() == 20
    floor = Card(title='T', min_width=40)
    assert floor.natural_width() == 40
    assert Card(width=33).natural_width() == 33
    empty = Card(use_colors=False).render(width=10)
    assert widths(empty) == {10}


def test_long_titles_are_cut_into_the_border():
    c = Card(title='Un título larguísimo que no cabe', fields={'a': 1},
             use_colors=False)
    first = c.render(width=20).split('\n')[0]
    assert visible_width(first) == 20 and '…' in first


def test_tiles_inline_and_stacked_layouts():
    fields = [('Cliente', 'José'), ('Total', '$1,200'), ('Estado', 'Ok')]
    inline = Card(fields=fields, field_columns=2, field_layout='inline',
                  use_colors=False, style_name='single_rows')
    text = inline.render(width=50)
    assert widths(text) == {50}
    assert 'Cliente José' in text
    stacked = Card(fields=fields, field_layout='stacked', use_colors=False)
    lines = stacked.render(width=30).split('\n')
    assert lines[1].strip('│ ') == 'Cliente' and lines[2].strip('│ ') == 'José'
    narrow = Card(fields={'Etiqueta larga': 'valor'}, use_colors=False)
    assert widths(narrow.render(width=12)) == {12}
    assert inline.natural_width() > 0 and stacked.natural_width() > 0


def test_coloured_tiles_and_values():
    c = Card(fields=[('a', 1), ('b', '')], field_columns=2, color='on blue',
             value_colors={'a': 'red'}, use_colors=True)
    text = c.render(width=30)
    assert parse_spec('red') in text and RESET + RESET not in text
    off = Card(fields=[('a', '\x1b[31mx\x1b[0m')], field_columns=2,
               use_colors=False)
    assert '\x1b' not in off.render(width=20)


def test_grid_tuple_children_natural_width_and_max_width():
    grid = Grid([('a' * 10, 2), 'b' * 4], columns=2, gap=1, max_width=15)
    assert grid.natural_width() == 15
    assert max(widths(grid.render(width=80))) <= 15
    assert Grid(['abc'], width=7).natural_width() == 7
    assert Grid(['abc', 'de'], min_width=6).natural_width() == 6 * 2 + 2
    assert Grid(['abc'], width=9).render().split('\n')[0] == 'abc'
    assert str(Grid(['xy'], width=5)) == 'xy'


def test_grid_child_with_a_render_without_width():
    class Legacy(object):
        def render(self):
            return 'old'
    assert Grid([Legacy()]).render(width=10) == 'old'
    assert str(Card(title='T', use_colors=False, width=12)).count('\n') >= 1
