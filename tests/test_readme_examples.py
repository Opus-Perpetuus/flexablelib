"""
Golden tests for the examples published in README.md.

These are the closest thing the project has to a specification: they are what
a user copy-pastes first. Each expected block below is the README's own output,
verbatim. A failure here means either a rendering regression or documentation
that has drifted from the code -- both worth knowing about.

The terminal is fixed wide by the autouse fixture in conftest, so nothing here
is wrapped or trimmed by the fitting step.
"""

from textwrap import dedent

from prettyTables import Table


def expected(block):
    return dedent(block).strip('\n')


# +-------------------------------------------------------------------------+
# "Creating a table is simple"
# +-------------------------------------------------------------------------+

def test_an_empty_table_renders_the_strange_thing():
    assert str(Table()) == expected("""
        ++

        ++

        ++
    """)


# +-------------------------------------------------------------------------+
# Three columns, default style
# +-------------------------------------------------------------------------+

def test_three_columns_with_the_default_style():
    table = Table()
    table.add_column('Name', ['Jade', 'John', 'Jane'])
    table.add_column('Age', [20, 30, 40])
    table.add_column('Results', [9.651, 3, 245.7])

    assert str(table) == expected("""
        +----------------------+
        | Name   Age   Results |
        +======+=====+=========+
        | Jade |  20 |   9.651 |
        | John |  30 |   3     |
        | Jane |  40 | 245.7   |
        +------+-----+---------+
    """)


def test_the_results_column_is_aligned_on_the_decimal_point():
    """
    The three values have different digit counts on both sides of the point,
    and the bare int has no point at all, yet the column reads as one number.
    """
    table = Table()
    table.add_column('Name', ['Jade', 'John', 'Jane'])
    table.add_column('Age', [20, 30, 40])
    table.add_column('Results', [9.651, 3, 245.7])

    body = [line for line in str(table).splitlines() if line.startswith('| J')]
    nine, three, two_forty_five = body

    # The two floats put their point on the same column of the output.
    assert nine.index('.') == two_forty_five.index('.') == 18
    # And the int sits immediately to the left of that same axis.
    assert three[17] == '3'
    assert three[18] == ' '


# +-------------------------------------------------------------------------+
# A multi-line header and a multi-line cell
# +-------------------------------------------------------------------------+

def build_wrapped_table():
    table = Table()
    table.add_column('Name', ['Jade', 'John', 'Jane'])
    table.add_column('Age', [20, 30, 40])
    table.add_column('Test\nResults', [9.651, 3, 245.7])
    table.add_row(['Piotr\nBaltimore', 27, 3.5])
    table.add_row(['Sam', 21, 0.6519])
    return table


def test_a_newline_splits_both_a_header_and_a_cell_across_printed_rows():
    assert str(build_wrapped_table()) == expected("""
        +----------------------------+
        | Name        Age       Test |
        |                    Results |
        +===========+=====+==========+
        | Jade      |  20 |   9.651  |
        | John      |  30 |   3      |
        | Jane      |  40 | 245.7    |
        | Piotr     |  27 |   3.5    |
        | Baltimore |     |          |
        | Sam       |  21 |   0.6519 |
        +-----------+-----+----------+
    """)


def test_the_neighbours_of_a_wrapped_cell_are_blank_on_the_extra_line():
    lines = str(build_wrapped_table()).splitlines()
    piotr_line = next(line for line in lines if 'Piotr' in line)
    baltimore_line = lines[lines.index(piotr_line) + 1]

    assert len(baltimore_line) == len(piotr_line)

    _, name, age, results, _ = baltimore_line.split('|')
    assert name.strip() == 'Baltimore'
    # Age and Results are blank on the continuation line, but keep their width.
    assert age.strip() == ''
    assert results.strip() == ''
    assert (len(age), len(results)) == (5, 10)


# +-------------------------------------------------------------------------+
# Index column, a named style and a missing value
# +-------------------------------------------------------------------------+

def build_options_table():
    table = Table()
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Age', [20, 30])
    table.add_column('Test\nResults', [9.651, 3, 245.7])
    table.add_row(['Piotr\nBaltimore', 27, 3.5])
    table.add_row(['Sam', 21])
    table.show_index = True
    table.style_name = 'pretty_columns'
    table.missing_value = '?'
    return table


def test_index_column_named_style_and_missing_values():
    assert str(build_options_table()) == expected("""
        ╒═══╤═══════════╤═════╤═════════╕
        │ i │ Name      │ Age │    Test │
        │   │           │     │ Results │
        ╞═══╪═══════════╪═════╪═════════╡
        │ 0 │ Jade      │  20 │   9.651 │
        │ 1 │ John      │  30 │   3     │
        │ 2 │ ?         │   ? │ 245.7   │
        │ 3 │ Piotr     │  27 │   3.5   │
        │   │ Baltimore │     │         │
        │ 4 │ Sam       │  21 │       ? │
        ╘═══╧═══════════╧═════╧═════════╛
    """)


def test_the_missing_value_aligns_as_if_it_were_the_column_type():
    lines = str(build_options_table()).splitlines()

    # Row 2 is missing its Name and Age; row "Sam" is missing its Results.
    row_without_name = next(line for line in lines if line.startswith('│ 2 │'))
    row_without_result = next(line for line in lines if '│ Sam' in line)

    _, _, name, age, _, _ = row_without_name.split('│')
    _, _, _, _, results, _ = row_without_result.split('│')

    # Left-aligned in the str column, like the names around it.
    assert name.startswith(' ?') and name.strip() == '?'
    # Right-aligned in the int column, like the ages.
    assert age.endswith('? ') and age.strip() == '?'
    # Right-aligned to the full width of the float column.
    assert results.endswith('? ') and results.strip() == '?'


def test_the_index_restarts_from_zero_on_every_render():
    """
    The index is produced by a single shared ``IndexCounter``. ``compose()``
    deep-copies the rows before calling it, so the stored counter never
    advances and a second render numbers the rows the same way.
    """
    table = build_options_table()

    assert table.compose() == table.compose()


# +-------------------------------------------------------------------------+
# Hiding the headers and the index, and the counts
# +-------------------------------------------------------------------------+

def test_hiding_the_headers_remeasures_the_columns():
    table = build_options_table()
    table.show_index = False
    table.show_headers = False

    assert str(table) == expected("""
        ╒═══════════╤════╤═════════╕
        │ Jade      │ 20 │   9.651 │
        │ John      │ 30 │   3     │
        │ ?         │  ? │ 245.7   │
        │ Piotr     │ 27 │   3.5   │
        │ Baltimore │    │         │
        │ Sam       │ 21 │       ? │
        ╘═══════════╧════╧═════════╛
    """)


def test_showing_the_index_again_adds_a_column_back():
    table = build_options_table()
    table.show_index = False
    table.show_headers = False
    str(table)              # render once with the index hidden
    table.show_index = True

    assert str(table) == expected("""
        ╒═══╤═══════════╤════╤═════════╕
        │ 0 │ Jade      │ 20 │   9.651 │
        │ 1 │ John      │ 30 │   3     │
        │ 2 │ ?         │  ? │ 245.7   │
        │ 3 │ Piotr     │ 27 │   3.5   │
        │   │ Baltimore │    │         │
        │ 4 │ Sam       │ 21 │       ? │
        ╘═══╧═══════════╧════╧═════════╛
    """)


def test_the_public_counts_ignore_the_index_column():
    table = build_options_table()
    table.show_index = False
    table.show_headers = False
    str(table)

    assert table.row_count == 5
    assert table.column_count == 3


def test_the_internal_counts_include_the_index_column():
    table = build_options_table()
    table.show_index = True

    assert table.internal_row_count == 5
    assert table.internal_column_count == 4


def test_repr_and_str_render_the_same_table():
    table = build_options_table()

    assert repr(table) == str(table)
