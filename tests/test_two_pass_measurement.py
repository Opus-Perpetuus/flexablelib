"""
The two-pass measurement in ``Table.compose()`` (``table.py:1869``).

``compose()`` measures the table twice on purpose. There is a circular
dependency in the measurement -- you cannot know whether a column needs
wrapping until you know its width, and wrapping changes the width -- so the
first pass (``semi=True``) measures the unconstrained table, and if that
exceeds the terminal, ``__check_columns_size`` shrinks the offending columns
and a second pass re-wraps and re-measures against the new widths.

Nothing here may depend on the real console: the ``terminal`` fixture patches
``prettyTables.table.get_window_size``.

The fixture table below is sized so the arithmetic is checkable by hand:

    columns          'Name' (4 wide)  'Comment' (24 wide)
    unconstrained    4 + 24 + 4 margins + 3 separators = 35 columns
"""

import pytest

from helpers import table_width, widths_from_border
from prettyTables import Table

LONG_COMMENT = 'a very long comment here'   # 24 characters
INTERSECTION = '┬'                          # thin_borderline's top border


def build_table(**settings):
    table = Table(style_name='thin_borderline')
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Comment', [LONG_COMMENT, 'short'])
    for name, value in settings.items():
        setattr(table, name, value)
    return table


# +-------------------------------------------------------------------------+
# The table already fits: the second pass changes nothing
# +-------------------------------------------------------------------------+

def test_a_table_that_fits_is_left_alone(terminal):
    terminal(200)
    rendered = str(build_table(auto_wrap=True))

    assert LONG_COMMENT in rendered
    assert widths_from_border(rendered.splitlines()[0], INTERSECTION) == [4, 24]
    assert table_width(rendered) == 35


def test_a_table_that_exactly_fits_is_not_shrunk(terminal):
    # __check_columns_size only adjusts when console_cols < table_width.
    terminal(35)
    rendered = str(build_table(auto_wrap=True))

    assert LONG_COMMENT in rendered
    assert table_width(rendered) == 35


# +-------------------------------------------------------------------------+
# The table does not fit: shrink, re-wrap, re-measure
# +-------------------------------------------------------------------------+

def test_a_table_wider_than_the_terminal_is_wrapped_to_fit(terminal):
    terminal(20)
    rendered = str(build_table(auto_wrap=True))

    assert LONG_COMMENT not in rendered
    assert table_width(rendered) <= 20


def test_the_second_pass_remeasures_the_wrapped_content(terminal):
    """
    This is the assertion the whole two-pass design exists for.

    With a 20-column terminal the shrink step hands 'Name' a budget of 2 and
    'Comment' a budget of 10. Re-wrapping at those budgets produces content
    that is *narrower* than the budget for 'Comment' -- its longest resulting
    line is 'comment', 7 characters -- so the final border must encode 7, not
    10 and certainly not the 24 the first pass measured.

    If the second ``__get_column_widths(semi=False)`` were skipped, this test
    would see [4, 24].
    """
    terminal(20)
    rendered = str(build_table(auto_wrap=True))
    top_border = rendered.splitlines()[0]

    assert widths_from_border(top_border, INTERSECTION) == [2, 7]
    assert table_width(rendered) == 16


def test_wrapping_turns_one_logical_row_into_several_printed_rows(terminal):
    terminal(20)
    rendered = str(build_table(auto_wrap=True))

    # The four fragments textwrap produces for LONG_COMMENT at width 10.
    for fragment in ('a very', 'long', 'comment', 'here'):
        assert fragment in rendered

    # The header wrapped too: 'Name' at a budget of 2 becomes 'Na' / 'me'.
    assert '│ Na │' in rendered
    assert '│ me │' in rendered


def test_every_line_of_a_wrapped_table_has_the_same_width(terminal):
    terminal(20)
    rendered = str(build_table(auto_wrap=True))

    assert {len(line) for line in rendered.splitlines()} == {16}


# +-------------------------------------------------------------------------+
# auto_wrap = False: trimming instead of wrapping
# +-------------------------------------------------------------------------+

def test_without_auto_wrap_the_cells_are_trimmed_with_a_sign(terminal):
    terminal(20)
    rendered = str(build_table(auto_wrap=False))

    assert '...' in rendered
    assert 'a very ...' in rendered
    # The trimming budget for 'Name' goes negative, so even short cells lose
    # their last character before the sign is appended.
    assert 'Jad...' in rendered
    assert 'Joh...' in rendered


def test_the_second_pass_measures_the_trimmed_content_including_the_sign(terminal):
    # 'Name' was trimmed to 'Nam...' (6) and 'Comment' to 'a very ...' (10),
    # so the sign made both columns wider than the budget they were cut to.
    terminal(20)
    rendered = str(build_table(auto_wrap=False))

    assert widths_from_border(rendered.splitlines()[0], INTERSECTION) == [6, 10]


@pytest.mark.xfail(
    reason=(
        'Known Issue #2 in the README: with auto_wrap=False the adjustment to '
        'the console potentially fails. Appending the trimming sign can make a '
        'column wider than the budget it was trimmed to, and nothing measures '
        'again afterwards.'
    ),
    strict=False,
)
def test_trimmed_table_should_also_fit_the_terminal(terminal):
    terminal(20)
    rendered = str(build_table(auto_wrap=False))

    assert table_width(rendered) <= 20


# +-------------------------------------------------------------------------+
# Terminal reading and re-rendering
# +-------------------------------------------------------------------------+

def test_compose_reads_the_terminal_size_once_per_render(terminal_calls):
    calls = terminal_calls(20)
    table = build_table(auto_wrap=True)

    table.compose()
    assert len(calls) == 1

    table.compose()
    assert len(calls) == 2


def test_an_empty_table_never_reads_the_terminal_size(terminal_calls):
    calls = terminal_calls(20)

    str(Table())

    # compose() short-circuits the whole measuring pipeline when there are no
    # columns, so the fitting step never runs.
    assert calls == []


@pytest.mark.parametrize('show_index', [False, True])
def test_rendering_twice_gives_the_same_string(terminal, show_index):
    """
    ``__str__`` re-runs the whole pipeline, and the two passes write into
    instance state that is never cleared between renders. This pins that the
    accumulated state does not change the result.
    """
    terminal(20)
    table = build_table(auto_wrap=True)
    table.show_index = show_index

    first = table.compose()
    second = table.compose()

    assert first == second


@pytest.mark.parametrize('cols', [16, 20, 25, 30, 35, 60])
def test_wrapped_tables_stay_within_the_terminal_at_several_widths(terminal, cols):
    terminal(cols)
    rendered = str(build_table(auto_wrap=True))

    assert table_width(rendered) <= cols


def test_the_index_column_is_never_shrunk(terminal):
    """
    ``__get_amounts_to_reduce`` drops the index column from the proportions
    and inserts a reduction of 0 for it, so the index stays legible however
    narrow the terminal gets.
    """
    terminal(20)
    table = build_table(auto_wrap=True)
    table.show_index = True

    rendered = str(table)

    # Index values 0 and 1 survive as single, unwrapped characters.
    assert '│ 0 │' in rendered
    assert '│ 1 │' in rendered
