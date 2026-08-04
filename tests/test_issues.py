"""
Regression tests for the issues.

https://github.com/Opus-Perpetuus/prettyTables/issues

Every issue ever filed against prettyTables has a reproduction here, stated
as the behaviour the report asked for. There are no ``xfail`` markers left:
all of them pass, and each one fails again the moment its bug comes back.

``docs/ISSUES.md`` is the prose companion -- what each issue asked, how it was
answered, and which tests below hold the answer in place.

Two of them are covered indirectly rather than by reproduction. #10 is about
formatting and documentation, so the test that stands for it asserts that
every public name on ``Table`` carries a docstring. #16 and #14 both concern
the shrinking pass and are grouped with it.
"""

from textwrap import dedent

import pytest

from helpers import decimal_point_indexes, table_width, widths_from_border
from prettyTables import Table

INTERSECTION = '┬'   # thin_borderline's top border


# +-------------------------------------------------------------------------+
# Issue #22 -- Hidden (empty) rows with a big missing value still affected the
#              size of the column.  FIXED.
# +-------------------------------------------------------------------------+

def build_issue_22_table():
    """
    The reproduction from the issue, verbatim.

    The last ``add_row()`` is empty, so ``show_empty_rows = False`` hides it.
    It still holds the 15-character missing value in every column, and before
    the fix those values were measured even though they are never printed.
    """
    table = Table()
    table.add_column('header1', ['data1', 'data2'])
    table.add_row(['data3', 12.4325])
    table.add_row(['data4', 111.22])
    table.add_row(['data5'])
    table.add_row(['data6', .4])
    table.add_row(['data7', 321111])
    table.add_row()
    table.add_column()
    table.missing_value = 'missing_value__'
    table.style_name = 'thin_borderline'
    table.show_empty_columns = False
    table.show_empty_rows = False
    return table


def test_issue_22_the_empty_row_is_not_printed():
    rendered = str(build_issue_22_table())

    # Seven data rows are printed; the eighth, empty one is hidden.
    body_lines = [
        line for line in rendered.splitlines()
        if line.startswith('│ data')
    ]
    assert len(body_lines) == 7


def test_issue_22_the_empty_column_is_not_printed():
    rendered = str(build_issue_22_table())

    assert 'column 3' not in rendered
    assert len(widths_from_border(rendered.splitlines()[0], INTERSECTION)) == 2


def test_issue_22_a_hidden_row_does_not_widen_its_column():
    """
    'header1' holds 'data1'..'data7' plus one hidden missing value. It must be
    sized to the header, 7 wide -- not to the 15-character value that the
    hidden row carries and that nothing ever prints.
    """
    rendered = str(build_issue_22_table())

    widths = widths_from_border(rendered.splitlines()[0], INTERSECTION)

    assert widths[0] == 7
    assert '│ header1 │' in rendered


def test_issue_22_the_visible_missing_values_still_count():
    """
    The other side of the fix. 'column 2' *does* show 'missing_value__' on
    three visible rows, so it stays 15 wide -- skipping hidden rows must not
    turn into skipping missing values.
    """
    rendered = str(build_issue_22_table())

    widths = widths_from_border(rendered.splitlines()[0], INTERSECTION)

    assert widths[1] == 15
    assert '│ missing_value__ │' in rendered


def test_issue_22_renders_exactly_the_output_the_report_asked_for():
    expected = dedent("""
        ┌─────────┬─────────────────┐
        │ header1 │        column 2 │
        ╞═════════╪═════════════════╡
        │ data1   │ missing_value__ │
        ├─────────┼─────────────────┤
        │ data2   │ missing_value__ │
        ├─────────┼─────────────────┤
        │ data3   │         12.4325 │
        ├─────────┼─────────────────┤
        │ data4   │        111.22   │
        ├─────────┼─────────────────┤
        │ data5   │ missing_value__ │
        ├─────────┼─────────────────┤
        │ data6   │          0.4    │
        ├─────────┼─────────────────┤
        │ data7   │     321111      │
        └─────────┴─────────────────┘
    """).strip('\n')

    assert str(build_issue_22_table()) == expected


# +-------------------------------------------------------------------------+
# Issue #23 -- Wrapping a table messes up float column widths with big
#              missing values.  FIXED.
# +-------------------------------------------------------------------------+

def build_issue_23_table():
    """
    A float column whose missing value dwarfs every number in it.

    Unconstrained the table is 27 columns wide: 5 for the names, 15 for the
    missing value, four margin characters and three vertical rules. It used
    to measure 31, because the 15-wide missing value was booked against the
    left of the decimal axis and the point and the three decimals were then
    added on top of it.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('name', ['alpha', 'beta', 'gamma'])
    table.add_column('value', [9.651, 3, 245.7])
    table.add_row(['delta'])
    table.missing_value = 'missing_value__'
    table.auto_wrap = True
    return table


def test_issue_23_the_float_column_is_aligned_while_the_table_fits(terminal):
    terminal(200)
    rendered = str(build_issue_23_table())

    assert len(decimal_point_indexes(rendered)) == 1
    assert 'missing_value__' in rendered


def test_issue_23_a_wide_missing_value_does_not_widen_the_column(terminal):
    """
    The column is as wide as its widest cell, and no wider.
    """
    terminal(200)
    rendered = str(build_issue_23_table())

    assert table_width(rendered) == 27
    assert widths_from_border(rendered.splitlines()[0], INTERSECTION)[1] == 15


def test_issue_23_a_shrunk_float_column_stays_aligned(terminal):
    terminal(22)
    rendered = str(build_issue_23_table())

    assert len(decimal_point_indexes(rendered)) == 1


def test_issue_23_a_shrunk_table_fits_the_terminal(terminal):
    terminal(22)
    rendered = str(build_issue_23_table())

    assert table_width(rendered) <= 22


@pytest.mark.parametrize('width', [17, 18, 19, 20, 22, 24, 26, 27, 40])
def test_issue_23_the_table_fits_at_every_width_it_can_be_drawn_at(terminal, width):
    terminal(width)
    rendered = str(build_issue_23_table())

    assert table_width(rendered) <= width
    assert len(decimal_point_indexes(rendered)) == 1


def test_issue_23_shrinking_drops_decimals_rather_than_digits(terminal):
    """
    Rounding a number leaves a number. Cutting characters off the end of one
    prints a different number, so the digits before the point are never
    touched -- only what comes after it.
    """
    terminal(18)
    rendered = str(build_issue_23_table())

    assert '245.7' in rendered      # every integer digit survives
    assert '9.7' in rendered        # 9.651 rounded to the room available
    assert '9.651' not in rendered


def test_issue_23_a_trimmed_cell_respects_its_budget(terminal):
    """
    The marker is inside the width, not added to it. Appending it afterwards
    made every trimmed cell three columns wider than the width it had just
    been trimmed to.
    """
    terminal(22)
    rendered = str(build_issue_23_table())

    trimmed = [line for line in rendered.splitlines() if '...' in line]
    assert trimmed
    assert all(len(line) <= 22 for line in trimmed)


# +-------------------------------------------------------------------------+
# Issue #24 -- Adding rows with more than one column, without ever adding a
#              column, rendered only the first column.  NO LONGER REPRODUCES.
# +-------------------------------------------------------------------------+

def test_issue_24_rows_added_without_columns_keep_every_column():
    table = Table()
    table.add_row(['a', 'b', 'c'])
    table.add_row(['d', 'e', 'f'])

    rendered = str(table)

    assert table.column_count == 3
    assert table.headers == ['column 1', 'column 2', 'column 3']
    for value in ('a', 'b', 'c', 'd', 'e', 'f'):
        assert value in rendered


def test_issue_24_a_single_wide_row_keeps_every_column():
    table = Table()
    table.add_row(['a', 'b'])

    rendered = str(table)

    assert table.column_count == 2
    assert 'a' in rendered and 'b' in rendered


# +-------------------------------------------------------------------------+
# Issue #16 -- Make auto-wrapping prioritise the biggest columns.
# +-------------------------------------------------------------------------+

def test_issue_16_a_narrow_column_survives_a_shrink(terminal):
    # Fixed: __get_amounts_to_reduce levels the widest column down instead of
    # reducing every column in proportion, so a 4-wide column is left alone
    # while the 24-wide one absorbs the whole difference.
    terminal(20)
    table = Table(style_name='thin_borderline')
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Comment', ['a very long comment here', 'short'])
    table.auto_wrap = True

    rendered = str(table)

    # 'Name' only needs 4 of the 20 available columns; it should not be split
    # into 'Na' / 'me' just because the neighbouring column is too wide.
    assert 'Jade' in rendered
    assert 'John' in rendered
    assert widths_from_border(rendered.splitlines()[0], INTERSECTION)[0] == 4


# +-------------------------------------------------------------------------+
# Issue #14 -- Show a special message when the table is too big for the space.
#              IMPLEMENTED as too_narrow_message.
# +-------------------------------------------------------------------------+

def build_issue_14_table():
    table = Table(style_name='thin_borderline')
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Comment', ['a very long comment here', 'short'])
    table.auto_wrap = True
    return table


def test_issue_14_a_table_that_cannot_fit_shows_the_message(terminal):
    """
    The floor comes from the style: two columns at MIN_COLUMN_SIZE (3) plus
    two margin characters each, plus the three vertical rules thin_borderline
    draws, is 13. Below that the table cannot be drawn legibly at all.
    """
    terminal(8)
    table = build_issue_14_table()
    table.too_narrow_message = 'Needs {needed} columns, only {available} here.'

    assert str(table) == 'Needs 13 columns, only 8 here.'


def test_issue_14_the_message_is_not_used_when_the_table_can_be_squeezed(terminal):
    terminal(13)
    table = build_issue_14_table()
    table.too_narrow_message = 'Needs {needed} columns, only {available} here.'

    rendered = str(table)

    assert 'Needs' not in rendered
    assert rendered.startswith('┌')


def test_issue_14_the_floor_is_lower_for_a_borderless_style(terminal):
    """
    ``plain`` draws no vertical rules and has a margin of 0, so the same two
    columns need only 2 * MIN_COLUMN_SIZE and fit where thin_borderline
    does not.
    """
    terminal(8)
    table = build_issue_14_table()
    table.style_name = 'plain'
    table.too_narrow_message = 'needs {needed}, has {available}'

    rendered = str(table)

    assert 'needs' not in rendered
    # Both columns sit at MIN_COLUMN_SIZE, so every cell is broken into
    # three-character fragments and no whole word survives on one line. What
    # this test asserts is that a table was rendered at all, where
    # thin_borderline at the same width refuses.
    assert 'Jad' in rendered
    assert len(rendered.splitlines()) > 4


def test_issue_14_without_a_message_a_hopeless_width_still_renders(terminal):
    """
    With no message set, a hopeless width must still produce a table.

    This used to raise. The proportional reduction handed 'Name' a budget of
    exactly 0 and ``textwrap.wrap(piece, 0)`` rejects a width of zero. Now
    that the reduction levels the widest column down and floors every column
    at MIN_COLUMN_SIZE, no budget can reach zero, so the default path renders
    something cramped rather than raising.
    """
    terminal(8)
    table = build_issue_14_table()

    assert table.too_narrow_message is None
    rendered = str(table)

    assert rendered.startswith('┌')
    assert 'Jade' in rendered or 'Jad' in rendered


def test_issue_14_shrinking_never_hands_a_column_a_budget_of_zero(terminal):
    # Fixed: the reduction floors every column at MIN_COLUMN_SIZE, so no
    # budget reaches zero and textwrap.wrap() is never handed a width of 0.
    terminal(8)
    table = build_issue_14_table()

    str(table)


# +-------------------------------------------------------------------------+
# Issue #1 -- ValueError when rendering: reading the console blew up.
# +-------------------------------------------------------------------------+

def test_issue_1_a_console_that_cannot_be_measured_still_renders(monkeypatch):
    """
    The first bug ever filed. Rendering read the terminal size through a
    hand-rolled parser that raised ``ValueError`` on the reporter's machine,
    so no table could be printed at all.

    ``get_window_size`` now falls back rather than propagating, whatever the
    platform hands back.
    """
    import os

    from prettyTables import utils

    def explode():
        raise ValueError('Lines is not in list')

    monkeypatch.setattr(os, 'get_terminal_size', lambda *a, **k: explode())
    monkeypatch.delenv('COLUMNS', raising=False)
    monkeypatch.delenv('LINES', raising=False)

    columns, lines = utils.get_window_size()

    assert columns > 0 and lines > 0


def test_issue_1_a_console_that_is_not_a_tty_still_renders(monkeypatch):
    import os

    from prettyTables import utils

    def explode():
        raise OSError('not a tty')

    monkeypatch.setattr(os, 'get_terminal_size', lambda *a, **k: explode())
    monkeypatch.delenv('COLUMNS', raising=False)
    monkeypatch.delenv('LINES', raising=False)

    assert utils.get_window_size() == (80, 24)


# +-------------------------------------------------------------------------+
# Issue #2 -- Show the row index in a column of its own.
# +-------------------------------------------------------------------------+

def build_indexed_table():
    table = Table(style_name='thin_borderline')
    table.add_column('n', ['a', 'b', 'c'])
    table.show_index = True
    return table


def test_issue_2_the_index_column_appears_on_the_left():
    rendered = str(build_indexed_table())

    assert '│ i │ n │' in rendered
    assert '│ 0 │ a │' in rendered
    assert '│ 2 │ c │' in rendered


def test_issue_2_index_start_and_step_are_honoured():
    table = build_indexed_table()
    table.index_start = 10
    table.index_step = 5

    rendered = str(table)

    assert '│ 10 │ a │' in rendered
    assert '│ 15 │ b │' in rendered
    assert '│ 20 │ c │' in rendered


def test_issue_2_the_index_counts_from_its_origin_on_every_render():
    """
    The counter is shared and consumed as the render walks the column, so it
    has to be put back before the next one. A deep copy used to hand out a
    fresh counter as a side effect; when that copy went, rendering twice
    returned 0,1 and then 2,3.
    """
    table = build_indexed_table()

    assert str(table) == str(table)


def test_issue_2_the_index_does_not_change_the_public_counts():
    table = build_indexed_table()

    str(table)

    assert (table.row_count, table.column_count) == (3, 1)
    assert (table.internal_row_count, table.internal_column_count) == (3, 2)


# +-------------------------------------------------------------------------+
# Issue #3, #7, #8, #9 -- Hiding empty rows and empty columns.
# +-------------------------------------------------------------------------+

def build_table_with_empties():
    table = Table(style_name='thin_borderline')
    table.add_column('n', ['a', '', 'c'])
    table.add_column('empty', ['', '', ''])
    return table


def test_issue_3_an_empty_column_is_hidden_and_not_counted():
    table = build_table_with_empties()
    table.show_empty_columns = False

    rendered = str(table)

    assert 'empty' not in rendered
    assert table.column_count == 1


def test_issue_3_an_empty_row_is_hidden_and_not_counted():
    table = build_table_with_empties()
    table.show_empty_rows = False

    rendered = str(table)

    assert rendered.count('\n│') >= 1
    assert table.row_count == 2


def test_issue_9_hiding_columns_does_not_hide_rows():
    """
    ``show_empty_columns = False`` used to hide the empty rows as well.
    """
    table = build_table_with_empties()
    table.show_empty_columns = False

    rendered = str(table)

    assert table.row_count == 3
    assert len([line for line in rendered.splitlines() if line.startswith('│ ')]) == 4


def test_issue_9_hiding_rows_does_not_hide_columns():
    """
    And the mirror image: setting only ``show_empty_rows`` used to do nothing.
    """
    table = build_table_with_empties()
    table.show_empty_rows = False

    rendered = str(table)

    assert 'empty' in rendered
    assert table.row_count == 2


def test_issue_9_a_row_of_empty_strings_counts_as_empty():
    """
    A column of ``''`` was empty but a row of ``''`` was not: rows only
    counted the padding placeholder. The two now agree.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('a', ['x', ''])
    table.add_column('b', ['y', ''])
    table.show_empty_rows = False

    assert table.empty_rows_i == [1]
    assert table.row_count == 1


def test_issue_7_columns_hide_correctly_while_the_index_shows():
    table = build_table_with_empties()
    table.show_index = True
    table.show_empty_columns = False

    rendered = str(table)

    assert 'empty' not in rendered
    assert '│ i │ n │' in rendered


def test_issue_8_the_index_stays_contiguous_when_rows_are_hidden():
    """
    Hiding the middle row must not leave a hole in the index.
    """
    table = build_table_with_empties()
    table.show_index = True
    table.show_empty_rows = False

    rendered = str(table)

    assert '│ 0 │ a │' in rendered
    assert '│ 1 │ c │' in rendered
    assert '│ 2 │' not in rendered


# +-------------------------------------------------------------------------+
# Issue #4 -- Alignment: per type, per column, and the missing value.
# +-------------------------------------------------------------------------+

def build_every_type_table():
    table = Table(style_name='thin_borderline')
    table.add_column('s', ['a', 'bb'])
    table.add_column('i', [1, 22])
    table.add_column('f', [1.5, 22.25])
    table.add_column('b', [True, False])
    return table


def test_issue_4_each_type_gets_its_typographic_default():
    rendered = str(build_every_type_table())

    assert '│ a  │  1 │  1.5  │  True │' in rendered


def test_issue_4_str_align_moves_the_string_column():
    table = build_every_type_table()
    table.str_align = 'r'

    assert '│  a │' in str(table)


def test_issue_4_int_align_moves_the_integer_column():
    table = build_every_type_table()
    table.int_align = 'l'

    assert '│ 1  │' in str(table)


def test_issue_4_bool_align_moves_the_boolean_column():
    """
    ``bool_align`` wrote to ``__float_align`` and read it back again, so it
    moved the float column and reported the float column's setting.
    """
    table = build_every_type_table()
    table.bool_align = 'c'

    assert table.bool_align == 'c'
    assert table.float_align is None
    assert '│ True  │' in str(table)


def test_issue_4_col_alignment_takes_a_sequence():
    table = build_every_type_table()
    table.col_alignment = ['c', 'c', 'c', 'c']

    rendered = str(table)

    assert '│ a  │ 1  │   f   │' in rendered or '│ a  │ 1  │' in rendered
    assert '│   f   │' in rendered


def test_issue_4_col_alignment_takes_a_mapping():
    table = build_every_type_table()
    table.col_alignment = {'s': 'r'}

    rendered = str(table)

    assert '│  a │' in rendered
    assert '│  1 │' in rendered      # untouched, still the int default


def test_issue_4_col_alignment_beats_the_type_override():
    table = build_every_type_table()
    table.str_align = 'r'
    table.col_alignment = {'s': 'c'}

    assert '│ a  │' in str(table)


def test_issue_4_a_bad_alignment_code_is_rejected():
    table = build_every_type_table()

    with pytest.raises(ValueError):
        table.str_align = 'middle'


def test_issue_4_decimal_alignment_is_not_forced_onto_a_string_column():
    """
    ``'f'`` needs the two-sided measurement only a float column carries.
    Asking for it elsewhere falls back rather than blowing up in the aligner.
    """
    table = build_every_type_table()
    table.col_alignment = {'s': 'f'}

    assert '│ a  │' in str(table)


def test_issue_6_the_missing_value_can_be_set_after_the_data():
    """
    It used to be stored as an ordinary cell when the data was added, so
    setting it afterwards showed nothing.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('a', ['x', 'y'])
    table.add_column('n', [1.5, 2.25])
    table.add_row(['z'])

    table.missing_value = '?'
    assert '│    ? │' in str(table)

    table.missing_value = 'N/A'
    rendered = str(table)
    assert '│  N/A │' in rendered
    assert '?' not in rendered


def test_issue_6_the_missing_value_does_not_change_the_alignment():
    """
    It aligns as though it were the type of the column around it.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('n', [9.651, 245.7])
    table.add_row([])
    table.missing_value = '?'

    rendered = str(table)

    assert len(decimal_point_indexes(rendered)) == 1


# +-------------------------------------------------------------------------+
# Issue #5, #11, #12, #13 -- Fitting the console: wrapping and trimming.
# +-------------------------------------------------------------------------+

def build_wide_table():
    table = Table(style_name='thin_borderline')
    table.add_column('n', [123456789012345, 2])
    table.add_column('s', ['abcdefghijklmno', 'z'])
    return table


def test_issue_5_the_table_is_squeezed_into_the_console(terminal):
    terminal(20)
    table = build_wide_table()
    table.auto_wrap = True

    assert table_width(str(table)) <= 20


def test_issue_13_auto_wrap_off_trims_instead_of_wrapping(terminal):
    terminal(20)
    table = build_wide_table()
    table.auto_wrap = False

    rendered = str(table)

    assert '...' in rendered
    assert len(rendered.splitlines()) == 7      # no cell became two lines


def test_issue_13_auto_wrap_on_breaks_the_text_over_lines(terminal):
    terminal(20)
    table = build_wide_table()
    table.auto_wrap = True

    rendered = str(table)

    assert 'abcdef' in rendered
    assert len(rendered.splitlines()) > 7


def test_issue_11_a_trimmed_cell_carries_the_marker(terminal):
    terminal(20)
    table = build_wide_table()
    table.auto_wrap = False

    assert '...' in str(table)


def test_issue_12_a_trimmed_number_column_aligns_left(terminal):
    """
    A trimmed number is not a number any more, so it stops pretending to be
    one and lines up on the left like the text it has become.
    """
    terminal(20)
    table = build_wide_table()
    table.auto_wrap = False

    assert '│ 123... │' in str(table)


def test_issue_18_trimming_does_not_touch_the_stored_data(terminal):
    """
    Trimming used to overwrite the table's own data, so a console that grew
    back could not undo it.
    """
    terminal(16)
    table = build_wide_table()
    table.auto_wrap = False

    assert '...' in str(table)
    assert table.columns['s'] == ['abcdefghijklmno', 'z']

    terminal(200)
    assert 'abcdefghijklmno' in str(table)


def test_issue_17_wrapping_into_almost_no_room_does_not_raise(terminal):
    """
    ``textwrap.wrap`` raises on a width of zero, and the proportional
    reduction used to hand out exactly that.
    """
    terminal(8)
    table = Table(style_name='thin_borderline')
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Comment', ['a very long comment here', 'short'])
    table.auto_wrap = True

    rendered = str(table)

    assert rendered.startswith('┌')


# +-------------------------------------------------------------------------+
# Issue #15, #19 -- The constructor arguments.
# +-------------------------------------------------------------------------+

def test_issue_15_rows_and_headers_together():
    table = Table(headers=['a', 'b'], rows=[[1, 2], [3, 4]])

    assert table.headers == ['a', 'b']
    assert table.rows == [[1, 2], [3, 4]]


def test_issue_15_columns_and_headers_together():
    """
    ``columns`` is column-oriented, so ``[[1, 3], [2, 4]]`` is 'a' holding
    1 and 3 and 'b' holding 2 and 4 -- two rows of [1, 2] and [3, 4].
    """
    table = Table(headers=['a', 'b'], columns=[[1, 3], [2, 4]])

    assert table.headers == ['a', 'b']
    assert table.columns == {'a': [1, 3], 'b': [2, 4]}
    assert table.rows == [[1, 2], [3, 4]]


def test_issue_15_fewer_headers_than_columns_names_the_rest():
    table = Table(headers=['a'], rows=[[1, 2, 3]])

    assert table.headers == ['a', 'column 2', 'column 3']
    assert table.column_count == 3
    for value in ('1', '2', '3'):
        assert value in str(table)


def test_issue_15_more_headers_than_columns_keeps_them_all():
    table = Table(headers=['a', 'b', 'c', 'd'], rows=[[1, 2]])

    assert table.headers == ['a', 'b', 'c', 'd']
    assert table.column_count == 4
    assert str(table).startswith('┌') is False   # default style


def test_issue_15_rows_without_headers_still_render():
    table = Table(rows=[[1, 2], [3, 4]])

    rendered = str(table)

    assert table.headers == ['column 1', 'column 2']
    for value in ('1', '2', '3', '4'):
        assert value in rendered


def test_issue_19_passing_headers_stops_the_automatic_naming():
    """
    Every header given was also counted as a column that needed naming, so
    seven headers produced seven more.
    """
    table = Table(
        headers=['HORA', 'L', 'M', 'I', 'J', 'V', 'S'],
        rows=[['01:33 p.m.\n03:00 p.m.', '', '', 'MM II', '', 'MM II', '']],
    )

    assert table.headers == ['HORA', 'L', 'M', 'I', 'J', 'V', 'S']
    assert table.column_count == 7


# +-------------------------------------------------------------------------+
# Issue #10 -- Code formatting and documentation.
# +-------------------------------------------------------------------------+

def test_issue_10_every_public_name_on_table_is_documented():
    """
    The one part of #10 with a surface a test can hold: every property and
    public method the class exposes has a docstring.
    """
    undocumented = []
    for name in dir(Table):
        if name.startswith('_'):
            continue
        attribute = getattr(Table, name)
        if isinstance(attribute, property):
            target = attribute.fget
        elif callable(attribute):
            target = attribute
        else:
            continue
        if not (target.__doc__ or '').strip():
            undocumented.append(name)

    assert undocumented == []
