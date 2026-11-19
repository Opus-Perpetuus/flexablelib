"""3.7.4: a bare string where a ``(title, content)`` / ``(label, value)``
pair is expected -- tabs, accordion sections, wizard steps, detail fields,
attachments -- is one title with nothing under it, not its first two
characters; scrolled inputs and lists fill the room they get back after a
resize instead of keeping the offset the small layout needed; plus the
Python PNG ``unfilter`` refusing the sizes the C one refuses and the
column bookkeeping of ``box_topology.visible_cells`` for wide characters."""

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib.text_width import strip_ansi  # noqa: E402
from flexablelib_components.base import pairs  # noqa: E402


def _lines(component, width, height=None):
    return strip_ansi(component.render(width, height)).split('\n')


# -- bare titles ---------------------------------------------------------------

def test_pairs_helper():
    assert pairs({'a': 1}) == [('a', 1)]
    assert pairs(['Uno', ('Dos', 2), ('Tres',), ['Cuatro', 4]]) == [
        ('Uno', None), ('Dos', 2), ('Tres', None), ['Cuatro', 4]]
    assert pairs(iter(['ab'])) == [('ab', None)]
    three = ('a', 'b', 'c')
    assert pairs([three])[0] is three


def test_tabs_bare_titles():
    tabs = C.Tabs(['Datos', 'Extra'])
    assert [t for t, _ in tabs.tabs] == ['Datos', 'Extra']
    assert tabs.current is None and tabs.children() == []
    head = _lines(tabs, 40, 4)[0]
    assert 'Datos' in head and 'Extra' in head    # was "[D]  E" and "a" below
    assert tabs.a11y_value() == 'Datos (1 de 2)'
    tabs.select(1)
    assert tabs.a11y_value() == 'Extra (2 de 2)'
    assert tabs.natural_width() >= len('Datos') + len('Extra')


def test_tabs_mixes_bare_titles_and_pairs():
    field = C.TextInput(label='Nombre')
    tabs = C.Tabs(['Inicio', ('Cliente', field)])
    assert tabs.form_children() == [field]
    tabs.select(1)
    assert tabs.current is field


def test_accordion_bare_titles():
    acc = C.Accordion(['Uno', 'Dos'], open=(0, 1))
    assert [t for t, _ in acc.sections] == ['Uno', 'Dos']
    text = _lines(acc, 30, 4)
    assert text[0].strip().endswith('Uno') and text[1].strip().endswith('Dos')
    assert acc.children() == [] and acc.form_children() == []
    assert acc.a11y_value() == 'Uno (1 de 2)'


def test_wizard_bare_titles_and_mapping():
    wiz = C.Wizard(['Datos', 'Pago'])
    assert [t for t, _ in wiz.steps] == ['Datos', 'Pago']
    assert wiz.a11y_value() == 'paso 1 de 2: Datos'
    assert 'Datos' in _lines(wiz, 40, 4)[0]
    field = C.TextInput(label='Nombre')
    wiz = C.Wizard({'Cliente': field, 'Fin': None})   # keys were split
    assert wiz.steps[0] == ('Cliente', field)
    assert field in wiz.children()


def test_detail_view_bare_labels():
    view = C.DetailView(['Nombre', ('Total', 25)])
    assert view.fields == [('Nombre', None), ('Total', 25)]
    text = _lines(view, 30)
    assert text[0].strip() == 'Nombre'
    assert text[1].split() == ['Total', '25']
    assert view.a11y_value() == 'Nombre; Total: 25'
    # A missing value does not count as the four letters of "None".
    assert C.DetailView([('Nombre', None)]).natural_width() == len('Nombre') + 2


def test_attachment_list_bare_names():
    files = C.AttachmentList(['acta.pdf', ('datos.csv', 2048), ('nota',),
                              {'name': 'x.txt'}])
    assert files.files == [('acta.pdf', None), ('datos.csv', 2048),
                           ('nota', None), ('x.txt', None)]
    text = _lines(files, 40)
    assert 'acta.pdf' in text[0] and 'datos.csv' in text[1]
    assert '2.0 KB' in text[1]
    assert files.a11y_value() == 'acta.pdf, datos.csv (2.0 KB), nota, x.txt'


# -- scrolling after a resize --------------------------------------------------

def test_text_input_shows_from_start_when_wide_again():
    field = C.TextInput(value='ana@x.mx', use_colors=False)
    field.focused = True
    assert _lines(field, 6) == ['› .mx_']
    field.focused = False
    assert _lines(field, 30)[0].strip() == 'ana@x.mx'   # was ".mx"
    field.focused = True
    assert _lines(field, 30)[0].rstrip() == '› ana@x.mx_'


def test_text_input_scroll_keeps_cursor_visible():
    field = C.TextInput(value='abcdefghij', use_colors=False)
    field.focused = True
    field.cursor_pos = 10
    assert _lines(field, 6) == ['› hij_']
    assert _lines(field, 12) == ['› bcdefghij_']    # the cursor needs one
    assert _lines(field, 13) == ['› abcdefghij_']
    field.cursor_pos = 0
    assert _lines(field, 6) == ['› abcd']
    wide = C.TextInput(value='中文中文中文', use_colors=False)
    wide.focused = True
    assert _lines(wide, 7) == ['› 中文_']
    assert _lines(wide, 20)[0].rstrip() == '› 中文中文中文_'


def test_unfocused_text_input_fills_the_field():
    field = C.TextInput(value='ana@x.mx', use_colors=False)
    field.focused = True
    field.render(6)
    field.focused = False
    assert _lines(field, 6) == ['  x.mx']


def test_text_area_fills_from_above_when_wider():
    area = C.TextArea(value='\n'.join('linea numero %d larga' % i
                                      for i in range(5)), rows=3,
                      use_colors=False)
    area.focused = True
    area.row, area.col = 4, len(area.lines[4])
    area.render(10, 4)
    text = _lines(area, 60, 4)
    assert [line[2:].strip() for line in text] == [
        'linea numero 2 larga', 'linea numero 3 larga',
        'linea numero 4 larga']                     # was line 4 and blanks


def test_data_table_fills_the_room_when_taller():
    table = C.DataTable(['n', 'x'], [[i, 'v%d' % i] for i in range(20)],
                        use_colors=False)
    table.focused = True
    table.cursor_row = 19
    table.render(30, 6)
    assert table.top == 17
    text = _lines(table, 30, 14)
    assert table.top == 9
    body = [line for line in text[2:] if line.strip()]
    assert body[0].split() == ['9', 'v9'] and body[10].split()[-1] == 'v19'
    table.cursor_row = 0
    table.render(30, 6)
    assert table.top == 0


def test_tree_fills_the_room_when_taller():
    tree = C.Tree({'k%d' % i: i for i in range(20)}, use_colors=False)
    tree.focused = True
    tree.index = 19
    tree.render(30, 4)
    text = _lines(tree, 30, 10)
    assert len([line for line in text if line.strip()]) == 10
    assert text[0].strip() == 'k10: 10' and 'k19' in text[-1]


def test_catalog_grid_fills_the_room_when_wider():
    grid = C.CatalogGrid([{'title': 'P%d' % i} for i in range(12)],
                         min_width=10, use_colors=False)
    grid.focused = True
    grid.index = 11
    grid.render(22, 12)                 # two columns: card row 5 of 6
    assert grid.top_row == 4
    text = '\n'.join(_lines(grid, 60, 12))   # five columns, three rows
    assert grid.top_row == 1
    assert 'P5' in text and 'P11' in text and 'P4' not in text
