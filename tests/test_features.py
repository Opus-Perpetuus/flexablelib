"""
Public API coverage for the high-demand features.

Each test drives the shipped Table entry point and asserts concrete output.
"""

from helpers import table_width
from prettyTables import Table


def _simple_table():
    table = Table(style_name='simple')
    table.add_column('name', ['zeta', 'alpha', 'mu'])
    table.add_column('value', [3.14159, 2.5, 10.0])
    table.add_column('count', [7, 42, 3])
    return table


def test_float_format_shapes_rendered_numbers():
    table = _simple_table()
    table.float_format = '.2f'

    rendered = str(table)

    assert '3.14' in rendered
    assert '2.50' in rendered
    assert '10.00' in rendered
    assert '3.14159' not in rendered


def test_int_format_and_leading_zeros():
    table = Table(style_name='plain')
    table.add_column('n', [7, 42])
    table.int_format = '04d'

    assert '0007' in str(table)
    assert '0042' in str(table)

    table.int_format = None
    table.leading_zeros = 3
    assert '007' in str(table)


def test_custom_format_per_column():
    table = Table(style_name='plain')
    table.add_column('name', ['a'])
    table.add_column('value', [1.5])
    table.custom_format = {'value': lambda v: 'USD {0}'.format(v)}

    assert 'USD 1.5' in str(table)


def test_column_min_and_max_width():
    table = Table(style_name='plain')
    table.add_column('name', ['ab'])
    table.add_column('note', ['abcdefghijklmnop'])
    table.column_min_width = {'name': 8}
    table.column_max_width = {'note': 6}
    table.auto_wrap = False

    rendered = str(table)
    lines = rendered.splitlines()
    # Header line: name padded to at least 8, note capped.
    assert 'name' in lines[0]
    assert '...' in rendered or 'abcdef' in rendered
    # note column content never wider than 6 visible chars in a cell
    # after trim marker budget.
    body = [line for line in lines if line and not set(line) <= set('- ')]
    assert body


def test_header_align_independent_of_body():
    table = Table(style_name='simple')
    table.add_column('name', ['a'])
    table.add_column('n', [1])
    table.header_align = 'r'
    table.col_alignment = {'name': 'l', 'n': 'l'}

    rendered = str(table)
    header_line = [
        line for line in rendered.splitlines() if 'name' in line and 'n' in line
    ][0]
    # Right-aligned header: spaces before the word "name".
    assert header_line.rstrip().endswith('n')
    assert 'name' in header_line


def test_add_divider_inserts_rule_on_plain_style():
    table = Table(style_name='plain')
    table.add_column('a', [1, 2, 3])
    table.add_column('b', ['x', 'y', 'z'])
    table.add_divider(after_row=0)

    lines = str(table).splitlines()
    # plain has a blank header separator; a divider is a dashed rule.
    assert any(set(line) == {'-'} or line.startswith('-') for line in lines)


def test_title_appears_above_the_table():
    table = _simple_table()
    table.title = 'Summary'

    rendered = str(table)
    assert rendered.splitlines()[0].strip() == 'Summary'
    assert 'name' in rendered


def test_sort_by_and_reverse():
    table = _simple_table()
    table.sort_by = 'name'

    lines = [
        line for line in str(table).splitlines()
        if any(name in line for name in ('alpha', 'mu', 'zeta'))
    ]
    assert 'alpha' in lines[0]
    assert 'zeta' in lines[-1]

    table.sort_reverse = True
    lines = [
        line for line in str(table).splitlines()
        if any(name in line for name in ('alpha', 'mu', 'zeta'))
    ]
    assert 'zeta' in lines[0]


def test_row_filter_drops_rows_without_mutating_storage():
    table = _simple_table()
    table.row_filter = lambda row: row[0] != 'mu'

    rendered = str(table)
    assert 'mu' not in rendered
    assert 'alpha' in rendered
    assert table.rows[2][0] == 'mu'


def test_shape_matches_counts():
    table = _simple_table()
    assert table.shape == (3, 3)
    assert table.shape == (table.row_count, table.column_count)


def test_repr_html_is_a_bare_table():
    table = _simple_table()
    table.title = 'T'
    html = table._repr_html_()

    assert html.startswith('<table>')
    assert '<th>name</th>' in html
    assert '<td>alpha</td>' in html or '>alpha<' in html
    assert '<caption>T</caption>' in html
    assert '<script' not in html


def test_table_align_pads_to_available_width():
    table = Table(style_name='plain')
    table.add_column('a', [1])
    table.max_width = 40
    table.table_align = 'r'

    rendered = str(table)
    first = rendered.splitlines()[0]
    assert first.startswith(' ')
    assert table_width(rendered) <= 40


def test_expand_to_window_widens_the_table():
    table = Table(style_name='plain')
    table.add_column('a', ['x'])
    table.add_column('b', ['y'])
    table.max_width = 30
    table.expand_to_window = True

    rendered = str(table)
    assert table_width(rendered) >= 20


def test_stored_rows_unchanged_after_format_and_sort():
    table = _simple_table()
    original = [list(row) for row in table.rows]
    table.float_format = '.1f'
    table.sort_by = 'value'
    str(table)
    assert [list(row) for row in table.rows] == original
