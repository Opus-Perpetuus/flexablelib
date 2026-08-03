"""
Regression tests for the open issues.

https://github.com/Opus-Perpetuus/prettyTables/issues

Every reproduction below is marked ``xfail(strict=False)``: the test states the
behaviour the issue asks for, so it reports ``xfail`` while the bug is present
and ``xpass`` the moment it is fixed -- at which point the marker should be
dropped rather than the assertion changed. ``strict=False`` keeps CI green
either way.

Issue #10 (code formatting and documentation) has no behavioural surface and
is not covered here.
"""

import pytest

from helpers import decimal_point_indexes, table_width, widths_from_border
from prettyTables import Table

INTERSECTION = '┬'   # thin_borderline's top border


# +-------------------------------------------------------------------------+
# Issue #22 -- Hidden (empty) rows with a big missing value still affect the
#              size of the column.
# +-------------------------------------------------------------------------+

def build_issue_22_table():
    """
    The reproduction from the issue, verbatim.

    The last ``add_row()`` is empty, so ``show_empty_rows = False`` hides it.
    Its two missing values are still measured, though, and 'missing_value__'
    is 15 characters wide.
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


@pytest.mark.xfail(
    reason=(
        'Issue #22: the hidden empty row is skipped when the rows are printed '
        'but not when the columns are measured, so header1 is sized to fit a '
        "missing value that never appears. Should be 7 wide ('header1'), "
        'renders 15 wide.'
    ),
    strict=False,
)
def test_issue_22_a_hidden_row_should_not_widen_its_column():
    rendered = str(build_issue_22_table())

    widths = widths_from_border(rendered.splitlines()[0], INTERSECTION)

    assert widths[0] == 7
    assert '│ header1 │' in rendered


# +-------------------------------------------------------------------------+
# Issue #23 -- Wrapping a table messes up float column widths with big
#              missing values.
# +-------------------------------------------------------------------------+

def build_issue_23_table():
    """
    A float column whose missing value dwarfs every number in it, in a table
    just wide enough to trip the shrinking branch of ``__check_columns_size``.

    Unconstrained the table is 31 columns wide (5 + 19 + margins + borders).
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


def test_issue_23_shrinking_switches_a_float_column_to_left_alignment(terminal):
    """
    Characterises the mechanism behind the issue.

    A float column is not in ``CAN_WRAP_TYPES``, so ``__wrap_or_trim_data``
    sends it down the trimming path even when ``auto_wrap`` is on -- and that
    path overwrites the column's alignment with the string default before it
    trims anything. Here nothing is actually long enough to be trimmed, so the
    only visible effect is that the numbers stop lining up.
    """
    terminal(30)
    rendered = str(build_issue_23_table())

    # Flush against the left margin instead of padded onto the decimal axis.
    assert '│ 9.651' in rendered
    assert '│ 245.7' in rendered


@pytest.mark.xfail(
    reason=(
        'Issue #23: once the table has to be shrunk, the float column loses '
        'its decimal alignment because the trimming path rewrites the column '
        'alignment. The points should stay on one axis.'
    ),
    strict=False,
)
def test_issue_23_a_shrunk_float_column_should_stay_aligned(terminal):
    terminal(30)
    rendered = str(build_issue_23_table())

    assert len(decimal_point_indexes(rendered)) == 1


@pytest.mark.xfail(
    reason=(
        'Issue #23, second half: the shrinking pass reports success without '
        'having removed any width, because a float column can neither be '
        'wrapped nor usefully trimmed.'
    ),
    strict=False,
)
def test_issue_23_a_shrunk_table_should_fit_the_terminal(terminal):
    terminal(30)
    rendered = str(build_issue_23_table())

    assert table_width(rendered) <= 30


# +-------------------------------------------------------------------------+
# Issue #24 -- Adding rows with more than one column, without ever adding a
#              column, renders only the first column.
# +-------------------------------------------------------------------------+

@pytest.mark.xfail(
    reason=(
        'Issue #24: rows added without any add_column() call should still '
        'produce every column. Reading add_row/__check_data_and_fill_last_row '
        'suggests this path is now correct, so this may already be fixed and '
        'the issue stale -- an xpass here is the signal to close it.'
    ),
    strict=False,
)
def test_issue_24_rows_added_without_columns_keep_every_column():
    table = Table()
    table.add_row(['a', 'b', 'c'])
    table.add_row(['d', 'e', 'f'])

    rendered = str(table)

    assert table.column_count == 3
    assert table.headers == ['column 1', 'column 2', 'column 3']
    for value in ('a', 'b', 'c', 'd', 'e', 'f'):
        assert value in rendered


@pytest.mark.xfail(
    reason='Issue #24, with a single row.',
    strict=False,
)
def test_issue_24_a_single_wide_row_keeps_every_column():
    table = Table()
    table.add_row(['a', 'b'])

    rendered = str(table)

    assert table.column_count == 2
    assert 'a' in rendered and 'b' in rendered


# +-------------------------------------------------------------------------+
# Issue #16 -- Make auto-wrapping prioritise the biggest columns.
# +-------------------------------------------------------------------------+

@pytest.mark.xfail(
    reason=(
        'Issue #16: __get_amounts_to_reduce spreads the reduction across all '
        'columns proportionally, so a 4-wide column is wrapped even though the '
        '24-wide one could absorb the whole difference on its own.'
    ),
    strict=False,
)
def test_issue_16_a_narrow_column_should_survive_a_shrink(terminal):
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
# +-------------------------------------------------------------------------+

@pytest.mark.skip(
    reason=(
        'Issue #14 is an unimplemented enhancement and the issue does not '
        'specify the message or the API that would expose it, so there is no '
        'behaviour to assert yet. The scenario is kept here as the shape the '
        'test should take once the feature is designed: at 8 columns the '
        'table below degenerates into one character per line instead of '
        'reporting that it does not fit.'
    )
)
def test_issue_14_a_table_that_cannot_fit_shows_a_notice(terminal):
    terminal(8)
    table = Table(style_name='thin_borderline')
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Comment', ['a very long comment here', 'short'])
    table.auto_wrap = True

    rendered = str(table)

    assert 'Jade' in rendered   # placeholder for the real expectation
