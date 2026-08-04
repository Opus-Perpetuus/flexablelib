"""
Merged cells.

A merge renders a rectangular block as a single cell. It is applied to the
assembled string rather than threaded through the measuring pipeline, so the
columns keep being sized by their own unmerged content -- see the module
docstring in ``prettyTables/merges.py`` for why.

The consequence worth testing: a merge never changes the table's width.
"""

import pytest

from helpers import table_width
from prettyTables import Table
from prettyTables.fast import strip_ansi, visible_width

INTERSECTION = '┬'


def build_table(style_name='thin_borderline'):
    table = Table(style_name=style_name)
    table.add_column('Region', ['Norte', 'Norte', 'Sur', 'Sur'])
    table.add_column('Month', ['Jan', 'Feb', 'Jan', 'Feb'])
    table.add_column('Sales', [120.5, 98.25, 210.0, 175.75])
    return table


# +-------------------------------------------------------------------------+
# Merging in each direction
# +-------------------------------------------------------------------------+

def test_a_horizontal_merge_spans_the_columns_it_covers():
    table = build_table()
    table.merge_cells(0, 0, last_column=2, value='Quarter summary')

    lines = str(table).splitlines()
    merged_line = next(line for line in lines if 'Quarter summary' in line)

    # The vertical rules between the spanned columns are gone from that line.
    assert merged_line.count('│') == 2


def test_a_vertical_merge_removes_the_rules_between_its_rows():
    table = build_table()
    table.merge_cells(0, 0, last_row=1, value='Norte')

    rendered = str(table)

    # 'Norte' appears once for the merged block instead of once per row.
    assert rendered.count('Norte') == 1


def test_a_block_merge_covers_both_directions():
    table = build_table()
    table.merge_cells(0, 0, 1, 1, value='Block')

    rendered = str(table)

    assert 'Block' in rendered
    # The four cells it covers are gone.
    assert 'Jan' not in rendered.split('Sur')[0]


def test_a_merge_never_changes_the_table_width():
    plain = build_table()
    width_before = table_width(str(plain))

    merged = build_table()
    merged.merge_cells(0, 0, last_column=2, value='A very long heading indeed')

    assert table_width(str(merged)) == width_before


def test_every_line_keeps_the_same_width_after_a_merge():
    table = build_table()
    table.merge_cells(0, 0, 1, 1, value='Block')

    widths = {len(line) for line in str(table).splitlines()}

    assert len(widths) == 1


# +-------------------------------------------------------------------------+
# Content and alignment
# +-------------------------------------------------------------------------+

def test_without_a_value_the_top_left_cell_content_is_kept():
    table = build_table()
    table.merge_cells(0, 0, last_row=1)

    assert 'Norte' in str(table)


@pytest.mark.parametrize('align', ['l', 'r', 'c'])
def test_the_merged_text_honours_its_alignment(align):
    table = build_table()
    table.merge_cells(0, 0, last_column=2, value='xx', align=align)

    line = next(l for l in str(table).splitlines() if 'xx' in l)
    inner = line.strip('│')
    before, after = inner.split('xx')

    if align == 'l':
        assert len(before) < len(after)
    elif align == 'r':
        assert len(before) > len(after)
    else:
        assert abs(len(before) - len(after)) <= 1


def test_text_longer_than_the_span_is_truncated_not_accommodated():
    table = build_table()
    table.merge_cells(0, 0, last_column=1, value='far too long to ever fit here')

    rendered = str(table)

    assert '...' in rendered
    assert table_width(rendered) == table_width(str(build_table()))


# +-------------------------------------------------------------------------+
# Coordinates
# +-------------------------------------------------------------------------+

def test_coordinates_ignore_the_index_column():
    table = build_table()
    table.show_index = True
    table.merge_cells(0, 0, last_column=1, value='AB')

    line = next(l for l in str(table).splitlines() if 'AB' in l)

    # The index column is untouched: its own cell and both rules survive.
    assert line.startswith('│ 0 │')


def test_the_corners_may_be_given_in_any_order():
    forwards = build_table()
    forwards.merge_cells(0, 0, 1, 1, value='X')

    backwards = build_table()
    backwards.merge_cells(1, 1, 0, 0, value='X')

    assert str(forwards) == str(backwards)


# +-------------------------------------------------------------------------+
# Rejected merges
# +-------------------------------------------------------------------------+

def test_a_single_cell_is_not_a_merge():
    with pytest.raises(ValueError, match='more than one cell'):
        build_table().merge_cells(0, 0)


def test_a_row_outside_the_table_is_rejected():
    with pytest.raises(ValueError, match='outside the table'):
        build_table().merge_cells(0, 0, last_row=99)


def test_a_column_outside_the_table_is_rejected():
    with pytest.raises(ValueError, match='outside the table'):
        build_table().merge_cells(0, 0, last_column=99)


def test_negative_coordinates_are_rejected():
    with pytest.raises(ValueError, match='negative'):
        build_table().merge_cells(-1, 0, last_column=1)


def test_an_unknown_alignment_is_rejected():
    with pytest.raises(ValueError, match='align must be'):
        build_table().merge_cells(0, 0, last_column=1, align='x')


def test_overlapping_merges_are_rejected():
    table = build_table()
    table.merge_cells(0, 0, last_column=1)

    with pytest.raises(ValueError, match='overlaps'):
        table.merge_cells(0, 1, last_column=2)


def test_merges_that_only_touch_are_allowed():
    table = build_table()
    table.merge_cells(0, 0, last_column=1)
    table.merge_cells(1, 0, last_column=1)

    assert len(table.merged_regions) == 2


# +-------------------------------------------------------------------------+
# Bookkeeping
# +-------------------------------------------------------------------------+

def test_merged_regions_reports_what_is_in_place():
    table = build_table()
    table.merge_cells(0, 0, last_column=2, value='X')

    regions = table.merged_regions

    assert len(regions) == 1
    assert regions[0].column_count == 3
    assert regions[0].row_count == 1


def test_unmerge_all_restores_the_plain_table():
    plain = str(build_table())

    table = build_table()
    table.merge_cells(0, 0, last_column=2, value='X')
    table.unmerge_all()

    assert str(table) == plain


def test_rendering_twice_with_a_merge_gives_the_same_string():
    table = build_table()
    table.merge_cells(0, 0, 1, 1, value='Block')

    assert str(table) == str(table)


@pytest.mark.parametrize('style', ['grid', 'pretty_columns', 'simple', 'plain',
                                   'thin_borderline', 'bold_borderline'])
def test_a_merge_works_across_styles(style):
    # Compared against the same table unmerged rather than asserting one
    # uniform width: 'plain' emits a short blank separator line of its own
    # accord, with or without a merge, and that is not this feature's doing.
    before = [len(line) for line in str(build_table(style)).splitlines()]

    table = build_table(style)
    table.merge_cells(0, 0, last_column=2, value='span')
    rendered = str(table)

    assert 'span' in rendered
    assert [len(line) for line in rendered.splitlines()] == before


# +-------------------------------------------------------------------------+
# Regressions
# +-------------------------------------------------------------------------+
#
# Every test above passed while merges were, in practice, unusable: they all
# supply `value=` and none of them colours anything. These cover what that
# left uncovered.

def visible_widths(rendered, skip_first=False):
    """The set of visible widths of a rendered table's lines."""
    lines = rendered.splitlines()
    if skip_first:
        lines = lines[1:]
    return {visible_width(line) for line in lines}


def test_a_merge_without_a_value_removes_the_rules_it_spans():
    # The reported bug. Taking the replacement text from the whole span rather
    # than from the top-left cell picked up the neighbouring columns *and* the
    # rules between them; painting that back changed nothing, so the merge
    # silently did not happen.
    table = build_table()
    table.merge_cells(0, 0, last_column=2)

    merged_line = str(table).splitlines()[3]

    assert 'Norte' in merged_line
    assert merged_line.count('│') == 2
    assert 'Jan' not in merged_line


def test_a_merge_without_a_value_centres_the_cell_it_kept():
    table = build_table()
    table.merge_cells(0, 0, last_column=2)

    merged_line = str(table).splitlines()[3]
    before, after = merged_line.strip('│').split('Norte')

    assert abs(len(before) - len(after)) <= 1


def test_a_coloured_table_keeps_its_width_through_a_merge():
    # Offsets are counted in terminal columns; applying them with a plain
    # string slice put every one of them out by the length of the escape,
    # which widened the merged row and left the table ragged.
    plain = build_table()
    plain.merge_cells(0, 0, last_column=1, value='Merged')

    coloured = build_table()
    coloured.use_colors = True
    coloured.column_colors = {'Region': 'bold magenta', 'Sales': 'green'}
    coloured.merge_cells(0, 0, last_column=1, value='Merged')

    assert len(visible_widths(str(coloured))) == 1
    assert visible_widths(str(coloured)) == visible_widths(str(plain))


def test_a_merge_spans_its_columns_on_a_coloured_table():
    table = build_table()
    table.use_colors = True
    table.column_colors = {'Region': 'bold magenta'}
    table.merge_cells(0, 0, last_column=2)

    merged_line = str(table).splitlines()[3]

    assert 'Jan' not in merged_line
    assert merged_line.count('│') == 2


def test_a_merge_keeps_the_colour_of_the_cell_it_kept():
    table = build_table()
    table.use_colors = True
    table.column_colors = {'Region': 'bold magenta'}
    table.merge_cells(0, 0, last_column=1)

    merged_line = str(table).splitlines()[3]

    assert '\x1b[1;35m' in merged_line
    assert 'Norte' in strip_ansi(merged_line)


def test_a_coloured_border_does_not_leak_through_a_merge():
    table = build_table()
    table.use_colors = True
    table.border_color = 'blue'
    table.merge_cells(0, 0, last_row=1, value='Norte')

    assert len(visible_widths(str(table))) == 1


def test_a_title_does_not_shift_a_merge_into_the_header():
    # The body's first line was counted from the header alone, so a title
    # pushed every merge one line up.
    table = build_table()
    table.title = 'Sales report'
    table.merge_cells(0, 0, last_column=2, value='Quarter summary')

    lines = str(table).splitlines()
    header_line = next(line for line in lines if 'Region' in line)

    assert 'Quarter summary' not in header_line
    assert 'Quarter summary' in lines[lines.index(header_line) + 2]
    assert len(visible_widths(str(table), skip_first=True)) == 1


def test_a_divider_above_a_merge_does_not_shift_it():
    # add_divider inserts a physical line the old line map knew nothing about.
    # A style that already rules between every row shows the divider anyway;
    # the extra physical line only appears on a style that does not.
    table = build_table('grid_eheader')
    table.add_divider(0)
    table.merge_cells(1, 0, last_row=2, value='Down')

    lines = str(table).splitlines()
    divider_index = next(i for i, line in enumerate(lines)
                         if set(line) == {'-'})

    assert 'Down' in lines[divider_index + 2]
    assert 'Norte' in lines[divider_index - 1]


def test_a_merge_over_wide_characters_keeps_the_table_square():
    table = Table()
    table.add_column('Producto', ['Café', '寿司テスト', 'Té'])
    table.add_column('Precio', [10, 20, 30])
    table.merge_cells(0, 0, last_column=1, value='Resumen')

    assert len(visible_widths(str(table))) == 1


def test_the_reported_case_renders_square():
    # Straight from the bug report: ragged columns, a missing value, the index
    # column and a colour, all at once.
    table = Table()
    table.add_column('Name', ['John', 'Jane'])
    table.add_column('Age', [20])
    table.add_column('Height', [1.75, 1.60, 1.75])
    table.missing_value = '?'
    table.show_index = True
    table.use_colors = True
    table.column_colors = {'Name': 'bold magenta'}
    table.merge_cells(0, 0, last_column=1)

    rendered = str(table)
    merged_line = rendered.splitlines()[3]

    assert len(visible_widths(rendered)) == 1
    assert 'John' in strip_ansi(merged_line)
    # Name and Age are now one cell: the rule that used to sit between them is
    # gone, and every other rule on the row survives.
    unmerged_line = rendered.splitlines()[4]
    assert merged_line.count('|') == unmerged_line.count('|') - 1


def test_a_merge_reaches_across_a_column_the_table_is_hiding():
    # An undrawn column occupies no room in the line. Counting it anyway put
    # the merge past the end of every line, where it was silently dropped.
    table = Table()
    table.add_column('A', ['x', 'y'])
    table.add_column('Empty', [None, None])
    table.add_column('B', [1, 2])
    table.show_empty_columns = False
    table.merge_cells(0, 0, last_column=2, value='SPAN')

    rendered = str(table)

    assert 'SPAN' in rendered
    assert len(visible_widths(rendered)) == 1


def test_two_merges_in_one_table_both_land():
    table = Table()
    table.add_column('Alpha', ['1', '2', '3'])
    table.add_column('Beta', ['4', '5', '6'])
    table.add_column('Gamma', ['7', '8', '9'])
    table.merge_cells(0, 0, last_column=1, value='TOP')
    table.merge_cells(1, 1, last_row=2, value='DOWN')

    rendered = str(table)

    assert 'TOP' in rendered
    assert 'DOWN' in rendered
    assert len(visible_widths(rendered)) == 1
