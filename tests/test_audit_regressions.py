"""
Defects found by running every feature and checking what came back.

Each test here names a bug that shipped. They are grouped by the mistake
rather than by the feature, because most of these surfaced in several places
at once and were one fault underneath.

The recurring invariant, and the one worth stating plainly: **every line of a
rendered table has the same visible width.** Most of the raggedness below came
from two numbers describing the same column and only one of them being
updated.
"""

import json
import re
from html.parser import HTMLParser

import pytest

from prettyTables import Table
from prettyTables.fast import strip_ansi, visible_width


def widths(rendered):
    """The set of visible widths of a rendered table's lines."""
    return {visible_width(line) for line in rendered.splitlines()}


def is_square(rendered):
    return len(widths(rendered)) == 1


# +-------------------------------------------------------------------------+
# A float column is described by two numbers, and both have to agree
# +-------------------------------------------------------------------------+
#
# The column width draws the frame. The (left, point, right) triple pads the
# cells, and the cell aligner never consults the width at all. Changing one
# without the other renders a body that does not fit its own rules.

def test_a_column_of_exponentials_is_not_wider_than_its_frame():
    # No cell has a decimal point, so the point's column measures zero wide --
    # and a fill character was emitted for it regardless.
    table = Table()
    table.add_column('c', [1e-07, 1e16])

    assert is_square(str(table))


def test_a_single_exponential_is_not_wider_than_its_frame():
    table = Table()
    table.add_column('c', [1e-07])

    assert is_square(str(table))


def test_an_exponential_beside_an_integer_keeps_the_column_square():
    table = Table()
    table.add_column('c', [1e-07, 5])

    assert is_square(str(table))


def test_a_column_mixing_points_and_exponentials_still_aligns():
    table = Table()
    table.add_column('c', [1.5, 2.25, 1e16])
    rendered = str(table)

    assert is_square(rendered)
    assert '1e+16' in rendered


@pytest.mark.parametrize('minimum', [6, 10, 15])
def test_column_min_width_widens_a_float_columns_cells_too(minimum):
    # The frame grew and the cells did not, leaving the body rows narrower
    # than the rules drawn around them.
    table = Table()
    table.add_column('v', [1.5, 22.25])
    table.column_min_width = minimum

    assert is_square(str(table))


def test_column_min_width_as_a_mapping_widens_a_float_column():
    table = Table()
    table.add_column('v', [1.5, 22.25])
    table.column_min_width = {'v': 12}

    assert is_square(str(table))


def test_column_min_width_widens_float_and_text_columns_alike():
    table = Table()
    table.add_column('v', [1.5, 22.25])
    table.add_column('s', ['a', 'b'])
    table.column_min_width = 10

    assert is_square(str(table))


def test_expand_to_window_widens_a_float_columns_cells_too():
    table = Table()
    table.add_column('v', [1.5, 22.25])
    table.add_column('s', ['a', 'b'])
    table.expand_to_window = True
    table.max_width = 40

    assert is_square(str(table))


# +-------------------------------------------------------------------------+
# The index column is a column too, and the lists that describe it are longer
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('narrow', [
    {'max_width': 30},
    {'max_width': 25},
    {'column_max_width': 4},
])
def test_show_index_survives_being_narrowed(narrow):
    # The alignment write went into the list without the index column while
    # the loop counted with it, so the last column ran off the end. Every way
    # of narrowing a table hit it: max_width, a small terminal, per-column
    # caps.
    table = Table(style_name='grid')
    table.add_column('a', ['alpha beta gamma delta'])
    table.add_column('b', ['some other long text here'])
    table.show_index = True
    for option, value in narrow.items():
        setattr(table, option, value)

    assert is_square(str(table))


def test_show_index_survives_narrowing_with_a_float_column():
    table = Table()
    table.add_column('a', ['alpha beta gamma delta'])
    table.add_column('n', [1.5])
    table.show_index = True
    table.max_width = 25

    assert is_square(str(table))


def test_show_index_survives_narrowing_while_wrapping():
    table = Table(style_name='grid')
    table.add_column('a', ['alpha beta gamma delta'])
    table.add_column('b', ['some other long text here'])
    table.show_index = True
    table.auto_wrap = True
    table.max_width = 30

    assert is_square(str(table))


# +-------------------------------------------------------------------------+
# A row is not always one line
# +-------------------------------------------------------------------------+

def test_a_divider_under_a_wrapped_row_matches_the_table_width():
    # The rule was drawn as wide as the whole row block, newlines and all --
    # four times the table width for a four-line row. Sorting alone could move
    # a wrapped row into first place and break a table that had been fine.
    table = Table(style_name='pretty_columns')
    table.add_column('note', ['short', 'a very long note that wraps around', 'mid'])
    table.add_column('n', [3, 1, 2])
    table.column_max_width = {'note': 10}
    table.auto_wrap = True
    table.sort_by = 'n'
    table.add_divider(after_row=0)

    assert is_square(str(table))


# +-------------------------------------------------------------------------+
# Internal placeholders must not reach the outside
# +-------------------------------------------------------------------------+
#
# Storage keeps a ValuePlacer where a cell is absent and one shared
# IndexCounter for the index column. Only the console renderer knew to resolve
# them, so every other consumer got the object's repr.

def missing_table():
    table = Table(missing_val='n/a')
    table.add_column('temp', [3.5, table.missing, 22.0])
    table.add_column('city', ['Oslo', 'Rome', 'Lima'])
    return table


def indexed_table():
    table = Table.from_records([['a'], [10], [20]])
    table.show_index = True
    return table


def test_the_missing_sentinel_is_exported_as_the_missing_value():
    table = missing_table()

    assert 'n/a' in table.to_csv()
    assert 'ValuePlacer' not in table.to_csv()
    assert table.to_records()[1]['temp'] == 'n/a'
    assert 'ValuePlacer' not in table.to_markdown()
    assert 'ValuePlacer' not in table._repr_html_()


def test_the_index_column_is_exported_as_its_numbers():
    table = indexed_table()

    assert 'IndexCounter' not in table.to_csv(include_index=True)
    assert [row['i'] for row in table.to_records(include_index=True)] == [0, 1]
    assert 'IndexCounter' not in table.to_markdown(include_index=True)


def test_an_exported_index_honours_index_start_and_step():
    table = indexed_table()
    table.index_start = 5
    table.index_step = 2

    exported = [row['i'] for row in table.to_records(include_index=True)]

    assert exported == [5, 7]
    # The console agrees, which is the point of resolving it the same way.
    body = [line for line in str(table).splitlines() if '10' in line][0]
    assert body.strip().startswith('| 5')


# +-------------------------------------------------------------------------+
# color_rule is told which cell it is looking at
# +-------------------------------------------------------------------------+

def coloured_table():
    table = Table()
    table.add_column('Name', ['a', 'b', 'c'])
    table.add_column('Delta', [5, -7, 1])
    table.use_colors = True
    table.color_rule = lambda value, row, column: (
        'red' if column == 'Delta'
        and isinstance(value, (int, float)) and value < 0
        else None
    )
    return table


def red_cells(rendered):
    """The visible text of every cell carrying a colour."""
    return [strip_ansi(match).strip()
            for match in re.findall(r'\x1b\[31m(.*?)\x1b\[0m', rendered)]


def test_color_rule_follows_the_rows_when_sorted():
    # The rule was handed whatever sat at the same position in storage, which
    # is a different row once anything reorders.
    table = coloured_table()
    table.sort_by = 'Delta'

    assert red_cells(str(table)) == ['-7']


def test_color_rule_follows_the_rows_when_filtered():
    table = coloured_table()
    table.row_filter = lambda row: row[0] != 'a'

    assert red_cells(str(table)) == ['-7']


def test_color_rule_is_unaffected_by_the_index_column():
    # The index column holds a counter object, and a rule comparing it
    # numerically raised TypeError.
    table = coloured_table()
    table.show_index = True

    assert red_cells(str(table)) == ['-7']


def test_column_colors_land_on_the_named_column_past_a_hidden_one():
    # A column that is not drawn still took up a position, so every colour
    # after it painted the neighbour to the right, and the last column got
    # nothing at all.
    def build(target):
        table = Table()
        table.add_column('A', ['x'])
        table.add_column('Empty', [None])
        table.add_column('B', ['p'])
        table.show_empty_columns = False
        table.use_colors = True
        table.column_colors = {target: 'red'}
        return str(table)

    assert red_cells(build('A')) == ['x']
    assert red_cells(build('B')) == ['p']
    # The hidden column has no cells to paint.
    assert red_cells(build('Empty')) == []


# +-------------------------------------------------------------------------+
# HTML is markup, and a cell is not
# +-------------------------------------------------------------------------+

def test_a_cell_cannot_close_the_scripts_element_in_to_html():
    # An HTML parser ends a script at the first '</script', quoting or not, so
    # the cell terminated the element, spilled the rest of the program into the
    # page as text, and had its own markup parsed for real.
    payload = '</script><h1>pwned</h1>'
    markup = Table.from_records([['col'], [payload]]).to_html()

    class Events(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.tags = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(('start', tag))

        def handle_endtag(self, tag):
            self.tags.append(('end', tag))

    parser = Events()
    parser.feed(markup)
    parser.close()

    scripts = [tag for tag in parser.tags if tag[1] == 'script']
    assert scripts == [('start', 'script'), ('end', 'script')]

    # And the value still arrives at the page intact.
    data = re.search(r'var DATA = (\{.*?\});\n', markup, re.S).group(1)
    assert json.loads(data)['rows'] == [[payload]]


def test_a_header_cannot_close_the_scripts_element_either():
    markup = Table.from_records([['</script>x'], ['v']]).to_html()

    assert '</script>x' not in markup.split('<script>')[1]
