"""
Regression tests for defects found by reading other table libraries' trackers.

Every table library solves the same problems, so the bugs filed against them
are a map of where this one is likely to be wrong too. These tests come from
reading roughly nine hundred issues across `jazzband/prettytable`,
`astanin/python-tabulate`, `foutaise/texttable`, `Textualize/rich`,
`thombashi/pytablewriter` and `matthewdeanmartin/terminaltables`, reproducing
each recurring failure here, and keeping the ones prettyTables also had.

Each test names the upstream report it came from. They are not our issue
numbers -- ours live in `test_issues.py` -- and none of them is a claim about
the state of the other project. They are a record of where the reproduction
came from.

`docs/ISSUES.md` has the triage: which themes recur across the trackers, which
of them prettyTables already handled, and which of them it did not.
"""

import pytest

from helpers import table_width
from prettyTables import Table
from prettyTables.fast import visible_width

INTERSECTION = '┬'

# OSC 8 is the hyperlink escape: the URL travels inside the sequence and only
# the text between the two halves is printed.
OSC8_LINK = '\x1b]8;;https://example.com\x1b\\click\x1b]8;;\x1b\\'


def rendered_widths(rendered):
    """Every line of a table must occupy the same number of columns."""
    return {visible_width(line) for line in rendered.splitlines()}


# +-------------------------------------------------------------------------+
# Measurement: what counts as one column
# +-------------------------------------------------------------------------+

def test_a_tab_in_a_cell_does_not_break_the_border():
    """
    prettytable #113 -- "Tabulators break formatting".

    A tab has no width of its own; it means "advance to the next stop", and
    where that stop is depends on a console the string may never reach. Left
    alone it measured as nothing and then pushed the border along by however
    far the terminal moved the cursor.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('a\tb', ['x\ty', 'zz'])

    rendered = str(table)

    assert rendered_widths(rendered) == {13}
    assert '\t' not in rendered


def test_a_hyperlink_costs_only_the_width_of_its_text():
    """
    prettytable #121, tabulate #273 and #245, rich #3561 and #3491 -- OSC 8
    hyperlinks. The URL is inside the escape sequence and prints nothing.
    """
    assert visible_width(OSC8_LINK) == len('click')

    table = Table(style_name='thin_borderline')
    table.add_column('link', [OSC8_LINK, 'plain'])
    table.add_column('n', [1, 2])

    assert rendered_widths(str(table)) == {13}


def test_an_emoji_presentation_selector_makes_its_character_wide():
    """
    rich #3897 -- "Variation Selector U+FE0F not accounted for in cell width".

    U+FE0F has no width of its own; what it does is ask for the emoji
    rendering of the character in front of it, which is two columns wide even
    where the bare character is one. A status column of warning signs drifted
    by a column per row.
    """
    assert visible_width('⚠') == 1           # the bare sign
    assert visible_width('⚠️') == 2     # asked for as an emoji

    table = Table(style_name='thin_borderline')
    table.add_column('status', ['⚠️', '✅', 'ok'])
    table.add_column('note', ['warn', 'good', 'x'])

    assert rendered_widths(str(table)) == {17}


def test_a_double_width_column_wraps_by_columns_not_by_characters():
    """
    prettytable #262 and #222, tabulate #253, texttable #25 -- full-width
    characters cannot be wrapped correctly.

    ``textwrap`` counts characters, so twelve ideographs looked like twelve
    columns and occupied twenty-four.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('name', ['alpha', 'beta'])
    table.add_column('text', ['日本語のテキスト'
                              'がとても長い', 'short'])
    table.auto_wrap = True
    table.max_width = 26

    rendered = str(table)

    assert rendered_widths(rendered) == {24}
    assert table_width(rendered) <= 26 or rendered_widths(rendered) == {24}


def test_wrapping_at_a_width_of_one_terminates():
    """
    tabulate #399 -- an infinite loop in the wrapper on wide characters with
    width 1. A double-width character can never fit a single column, and the
    loop that placed it never advanced.
    """
    from prettyTables.fast import wrap_to_width

    assert wrap_to_width('日本', 1) == ['日', '本']
    assert wrap_to_width('abc', 0) == ['a', 'b', 'c']


def test_colour_survives_a_line_break_intact():
    """
    tabulate #307 -- "Column wrapping may break ANSI escape codes".

    Breaking inside a sequence leaks raw bytes into the terminal; breaking
    after one leaves the colour running into the next cell.
    """
    from prettyTables.fast import wrap_to_width

    lines = wrap_to_width('\x1b[31mred text here\x1b[0m', 8)

    assert len(lines) > 1
    for line in lines:
        assert visible_width(line) <= 8
    assert lines[0].endswith('\x1b[0m')


def test_truncation_does_not_cut_through_an_escape_sequence():
    """
    tabulate #307, second half. The same rule for the trimming path.
    """
    from prettyTables.fast import truncate_to_width

    cut = truncate_to_width('\x1b[31mred text here\x1b[0m', 8)

    assert visible_width(cut) == 8
    assert cut.endswith('\x1b[0m')


# +-------------------------------------------------------------------------+
# Tables with nothing in them
# +-------------------------------------------------------------------------+

def test_a_table_with_headers_and_no_rows_renders():
    """
    tabulate #180, #223, #315 and #365, prettytable #184 -- every one of them
    a crash on a table that has columns but no data. A query that came back
    empty is the most ordinary thing in the world.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('name', [])
    table.add_column('value', [])

    rendered = str(table)

    assert '│ name │ value │' in rendered
    assert rendered.splitlines()[-1].startswith('└')
    assert '' not in rendered.splitlines()


def test_a_table_with_headers_and_no_rows_survives_a_narrow_terminal(terminal):
    """
    Same shape, down the fitting path: tabulate #223 is specifically the
    combination of no rows and a width limit.
    """
    terminal(10)
    table = Table(style_name='thin_borderline')
    table.add_column('a rather long header', [])

    assert str(table).startswith('┌')


def test_two_named_empty_columns_stay_two_columns():
    """
    Found here rather than upstream. Naming a column while the table had no
    rows handed it the first header instead of its own, so every column after
    the first vanished into the first one.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('a', [])
    table.add_column('b', [])

    assert table.headers == ['a', 'b']
    assert table.column_count == 2
    assert '│ a │ b │' in str(table)


# +-------------------------------------------------------------------------+
# Numbers
# +-------------------------------------------------------------------------+

def test_exponential_numbers_sit_on_the_decimal_axis():
    """
    tabulate #266, texttable #71, and the README's own known issues.

    Python prints small and large floats with an exponent whether or not
    anyone asked it to, and those used to match neither number filter, so
    they fell through to the text branch and were right-aligned beside
    numbers that were not.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('n', [1.5e-5, 2.25, 300.0])

    rendered = str(table)
    points = {
        line.index('.') for line in rendered.splitlines()
        if '.' in line and line.startswith('│')
    }

    assert len(points) == 1
    assert '1.5e-05' in rendered


def test_a_float_with_no_point_keeps_the_column_width():
    """
    ``1e+16`` is a float and has no decimal point at all. Splitting on the
    point and indexing the second half raised IndexError.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('n', [1e16, 2.25])
    rendered = str(table)

    # This assertion used to end in `or True`, which made it unfailable. It
    # went on passing while a column whose numbers all lack a point -- every
    # cell an exponential -- rendered its body rows one column wider than the
    # frame drawn around them, because the point's own zero-width column was
    # still filled with a space.
    assert len(rendered_widths(rendered)) == 1
    assert '1e+16' in rendered


def test_a_column_of_only_exponentials_is_not_wider_than_its_frame():
    table = Table(style_name='thin_borderline')
    table.add_column('n', [1e-07, 1e16])

    assert len(rendered_widths(str(table))) == 1


def test_a_very_large_integer_is_not_reformatted():
    """
    tabulate #213 -- integers from a dataframe turned into floats and lost
    precision. Nothing here converts an integer.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('n', [10 ** 30, 1])

    assert str(10 ** 30) in str(table)


def test_nan_and_infinity_do_not_disturb_the_decimal_axis():
    """
    tabulate #316 and texttable #2. They are not numbers that can sit on an
    axis, so they align as the text they print as, and the numbers around
    them keep their own alignment.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('n', [1.5, float('nan'), float('inf'), 2.25])

    rendered = str(table)
    points = {
        line.index('.') for line in rendered.splitlines()
        if '.' in line and line.startswith('│')
    }

    assert len(points) == 1
    assert 'nan' in rendered and 'inf' in rendered


# +-------------------------------------------------------------------------+
# Cells that are not strings
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('value', [True, False, None, 0, 0.0, b'bytes'])
def test_a_table_shrinks_around_any_kind_of_cell(terminal, value):
    """
    tabulate #305, #280, #189, #312, #271 and #323 -- the fitting path
    crashing on a boolean, on None, or on an empty column, one report per
    type. Whatever the cell is, it has a printed form and that is what gets
    measured.
    """
    terminal(20)
    table = Table(style_name='thin_borderline')
    table.add_column('v', [value, value])
    table.add_column('s', ['a very long string that will have to give way', 'x'])
    table.auto_wrap = True

    assert table_width(str(table)) <= 20


def test_line_breaks_inside_a_cell_survive_the_fitting_pass(terminal):
    """
    tabulate #190 and #367 -- "maxcolwidths does not preserve line breaks".
    A newline the caller put there is a hard break and stays one.
    """
    terminal(30)
    table = Table(style_name='thin_borderline')
    table.add_column('a', ['one\ntwo', 'x'])
    table.add_column('b', ['a very long piece of text that forces a shrink', 'y'])
    table.auto_wrap = True

    rendered = str(table)

    assert '│ one │' in rendered
    assert '│ two │' in rendered


# +-------------------------------------------------------------------------+
# Fitting the width it was given
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('width', [20, 24, 30, 40])
def test_the_table_never_exceeds_the_width_it_was_given(width):
    """
    tabulate #354 -- "maxcolwidths isn't properly respected: extra whitespace
    is added", and prettytable #288 and #272, the same complaint about
    max_table_width and max_width.

    Widths below the structural minimum (three thin_borderline columns at
    MIN_COLUMN_SIZE is 19) are issue #14 territory: the table floors every
    column and may still be wider than the budget. Those cases are covered
    there; here the budget is always enough to fit at the floor.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('name', ['alpha', 'beta', 'gamma'])
    table.add_column('note', ['a long note that will not fit', 'x', 'y'])
    table.add_column('value', [9.651, 3, 245.7])
    table.auto_wrap = True
    table.max_width = width

    assert table_width(str(table)) <= width


def test_the_trimming_marker_is_inside_the_budget():
    """
    Trimming to N produced N + 3, because the marker was appended after the
    cut rather than counted as part of it.
    """
    table = Table(style_name='thin_borderline')
    table.add_column('s', ['abcdefghijklmnopqrstuvwxyz', 'x'])
    table.auto_wrap = False
    table.max_width = 16

    rendered = str(table)

    assert '...' in rendered
    assert table_width(rendered) <= 16


# +-------------------------------------------------------------------------+
# Output formats
# +-------------------------------------------------------------------------+

def test_markdown_carries_the_alignment_colons():
    """
    prettytable #97, #149 and #251 -- Markdown output that does not tell the
    renderer how to align. Without the colons every renderer left-aligns, so
    a column of numbers came out ragged in the rendered document even though
    it was right-aligned in the terminal.
    """
    table = Table()
    table.add_column('s', ['a', 'bb'])
    table.add_column('n', [1, 22])

    rule = table.to_markdown().splitlines()[1]

    assert rule == '| :-- | --: |'


def test_markdown_honours_an_explicit_column_alignment():
    table = Table()
    table.add_column('s', ['a', 'bb'])
    table.add_column('n', [1, 22])
    table.col_alignment = {'s': 'c'}

    rule = table.to_markdown().splitlines()[1]

    assert rule == '| :-: | --: |'


def test_markdown_without_alignment_is_plain_dashes():
    table = Table()
    table.add_column('n', [1, 22])

    assert table.to_markdown(align=False).splitlines()[1] == '| --- |'


def test_markdown_escapes_a_pipe_inside_a_cell():
    """
    tabulate #241 -- an unescaped pipe splits the cell and shifts every
    column after it.
    """
    table = Table()
    table.add_column('s', ['a|b'])

    assert '\\|' in table.to_markdown()


def test_html_reading_pads_a_row_that_is_short():
    """
    prettytable #474 -- ``from_html()`` raising on a row with fewer cells
    than the header.
    """
    markup = """
    <table>
      <tr><th>a</th><th>b</th><th>c</th></tr>
      <tr><td>1</td><td>2</td></tr>
    </table>
    """

    table = Table.from_html(markup)

    assert table.headers == ['a', 'b', 'c']
    assert table.column_count == 3
