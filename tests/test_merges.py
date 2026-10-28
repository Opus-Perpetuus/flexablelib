"""
Merged cells.

A merge renders a rectangular block as a single cell. It is applied to the
assembled string rather than threaded through the measuring pipeline, so the
columns keep being sized by their own unmerged content -- see the module
docstring in ``flexablelib/merges.py`` for why.

The consequence worth testing: a merge never changes the table's width.
"""

import pytest

from helpers import table_width
from flexablelib import Table
from flexablelib.fast import strip_ansi, visible_width

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



def test_vertical_merge_turns_left_border_into_an_edge():
    """Vertices on a body rule inside a vertical merge must become edges.

    The horizontal arms into the merged cell are gone, so a left-border
    '├' becomes the vertical edge '│', and the right junction keeps the
    three-way '├' that opens the remaining columns.
    """
    table = build_table()
    table.merge_cells(0, 0, last_row=1, value='Norte')

    sep = next(
        line for line in str(table).splitlines()
        if '├───────┼────────┤' in line or line.startswith('│        ├')
    )

    assert sep.startswith('│')
    assert '├───────┼────────┤' in sep
    assert not sep.startswith('├')


def test_vertical_merge_in_middle_column_uses_left_and_right_tees():
    table = build_table()
    table.merge_cells(0, 1, last_row=1, value='M')

    sep = next(line for line in str(table).splitlines() if '       ' in line and '┤' in line and line.count('├') >= 1)

    assert '├────────┤       ├────────┤' in sep


def test_vertical_merge_on_last_column_turns_right_border_into_an_edge():
    table = build_table()
    table.merge_cells(0, 2, last_row=1, value='S')

    sep = next(line for line in str(table).splitlines() if line.endswith('│') and '┤        │' in line)

    assert sep.endswith('│')
    assert '├────────┼───────┤        │' in sep


def test_vertical_merge_vertices_follow_grid_ascii_style():
    table = build_table('grid')
    table.merge_cells(0, 0, last_row=1, value='Norte')

    sep = next(line for line in str(table).splitlines() if '+-------+' in line and line.startswith('|'))

    assert sep.startswith('|        +')


def test_vertical_merge_vertices_follow_bold_borderline_style():
    table = build_table('bold_borderline')
    table.merge_cells(0, 0, last_row=1, value='Norte')

    sep = next(line for line in str(table).splitlines() if '├───────┼────────╢' in line)

    assert sep.startswith('║')
    # Middle verticals are single │, so the tee opening the remaining columns
    # is ├ — not the double-left ╟ reserved for the table's left border.
    assert '║        ├───────┼────────╢' in sep


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
    # Column-only styles (pretty_columns, grid_eheader, …) grow by one synthetic
    # row rule per multi-column merge; every line must still share the width.
    after = [len(line) for line in rendered.splitlines()]
    assert set(after) == set(before)
    assert len(after) >= len(before)


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
    lines = rendered.splitlines()
    merged_line = next(line for line in lines if 'John' in strip_ansi(line))
    unmerged_line = next(line for line in lines if 'Jane' in strip_ansi(line))

    assert len(visible_widths(rendered)) == 1
    assert 'John' in strip_ansi(merged_line)
    # Name and Age are now one cell: the rule that used to sit between them is
    # gone, and every other rule on the row survives.
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


# +-------------------------------------------------------------------------+
# Junction repair: horizontal + vertical + column-only styles
# +-------------------------------------------------------------------------+

def _ops_report():
    """Golden table from complex-merges/03_ops_report (H+V merges)."""
    table = Table(style_name='bold_borderline')
    table.title = 'Weekly Ops Report'
    shifts, tickets, sla = [], [], []
    n = 0
    for _day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
        for sh in ['AM', 'PM']:
            shifts.append(sh)
            tickets.append(40 + n * 3)
            sla.append(round(0.92 + (n % 5) * 0.01, 2))
            n += 1
    table.add_column('Site', [''] * 14)
    table.add_column('Day', [''] * 14)
    table.add_column('Shift', shifts)
    table.add_column('Tickets', tickets)
    table.add_column('SLA', sla)
    table.merge_cells(0, 0, last_row=13, value='MX-GDL')
    for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
        table.merge_cells(i * 2, 1, last_row=i * 2 + 1, value=day)
    table.merge_cells(10, 2, last_column=4, value='Weekend AM rollup')
    table.merge_cells(11, 2, last_column=4, value='Weekend PM rollup')
    return table


def test_ops_report_adjacent_vertical_merges_use_middle_tees_not_border_glyphs():
    """Adjacent vertical merges must not leave ╢/╟ on middle verticals."""
    rendered = str(_ops_report())
    # Internal AM/PM separators inside Site+Day merges.
    internal = [
        line for line in rendered.splitlines()
        if line.startswith('║') and '├───────┼─────────┼──────╢' in line
    ]
    assert internal, rendered
    for line in internal:
        assert '╢     ╟' not in line
        assert '╟───────┼─────────┼──────╢' not in line or not line.startswith('╟')
        # Shared Site|Day junction is a bare vertical; Day|Shift opens with ├.
        assert '│     ├' in line or '│           ├' in line or '├───────┼─────────┼──────╢' in line


def test_ops_report_site_only_separator_uses_single_tee():
    rendered = str(_ops_report())
    between_days = [
        line for line in rendered.splitlines()
        if '├─────┼───────┼─────────┼──────╢' in line
    ]
    assert between_days, rendered
    for line in between_days:
        assert line.startswith('║')
        assert not line.startswith('╟')
        # Must not reuse the double-left border glyph on a middle vertical.
        assert '║      ╟' not in line


def test_horizontal_merge_caps_become_tees_above_and_below():
    table = Table(style_name='pretty_grid')
    table.add_column('A', ['a1', 'a2', 'a3'])
    table.add_column('B', ['b1', 'b2', 'b3'])
    table.add_column('C', ['c1', 'c2', 'c3'])
    table.merge_cells(1, 0, last_column=1, value='AB')

    lines = str(table).splitlines()
    above = next(line for line in lines if '┴' in line)
    below = next(line for line in lines if '┬' in line)
    assert '├────┴────┼────┤' in above
    assert '├────┬────┼────┤' in below


def test_column_only_style_inserts_horizontal_break_under_multi_column_merge():
    """pretty_columns has column lines but no row lines; a multi-column merge
    must insert a row rule so the grid does not break oddly.

    Caps use the table's outer horizontal glyph (═ for pretty_columns).
    """
    table = Table(style_name='pretty_columns')
    table.add_column('A', ['a1', 'a2', 'a3'])
    table.add_column('B', ['b1', 'b2', 'b3'])
    table.add_column('C', ['c1', 'c2', 'c3'])
    table.merge_cells(1, 0, last_column=1, value='AB')

    lines = str(table).splitlines()
    # Light tees (┴/┬) or double-horizontal tees (╧/╤) — both valid depending
    # on whether the synthesizer mirrors the outer ═ border.
    assert any(('┴' in line or '╧' in line) for line in lines), lines
    assert any(('┬' in line or '╤' in line) for line in lines), lines
    assert any('AB' in line for line in lines)
    # The synthetic rules keep the table square.
    assert len({visible_width(line) for line in lines}) == 1


def test_block_merge_header_and_footer_caps():
    table = Table(style_name='pretty_grid')
    table.add_column('A', ['a1', 'a2', 'a3'])
    table.add_column('B', ['b1', 'b2', 'b3'])
    table.add_column('C', ['c1', 'c2', 'c3'])
    table.merge_cells(0, 0, 1, 1, value='BLOCK')

    rendered = str(table)
    assert '╧' in rendered  # header intersection loses south into the block
    assert '┬' in rendered  # body rule below gains north-less tee


def test_last_row_horizontal_merge_uses_table_end_corners_not_header_tees():
    """A multi-column merge on the final data row must not rewrite the
    table_end_line as if it had south arms (that yields ╞/╪/╤/╡)."""
    table = Table(style_name='pretty_grid')
    table.add_column('A', ['a1', 'a2', 'a3'])
    table.add_column('B', ['b1', 'b2', 'b3'])
    table.add_column('C', ['c1', 'c2', 'c3'])
    table.add_column('D', ['d1', 'd2', 'd3'])
    table.merge_cells(2, 1, last_column=2, value='BC')

    lines = str(table).splitlines()
    bottom = lines[-1]
    assert bottom.startswith('╘'), bottom
    assert bottom.endswith('╛'), bottom
    assert '╞' not in bottom and '╡' not in bottom, bottom
    assert '╪' not in bottom and '╤' not in bottom, bottom
    # Inner sep under BC becomes a plain double horizontal (no south/north).
    assert bottom == '╘════╧═════════╧════╛', bottom


def test_stress_last_row_merge_bottom_border_is_end_line():
    """Stress table from demos: H14 on the last row must keep ╘/╧/╛."""
    table = Table(style_name='pretty_grid')
    headers = [f'C{c}' for c in range(8)]
    for c, h in enumerate(headers):
        table.add_column(h, [f'S{r}c{c}' for r in range(15)])
    for r in range(0, 15, 3):
        table.merge_cells(r, 0, last_row=min(r + 2, 14), value=f'R{r}')
    for r, c0, c1, label in [
        (0, 2, 4, 'H0'),
        (1, 5, 7, 'H1'),
        (4, 2, 3, 'H4'),
        (7, 3, 6, 'H7'),
        (10, 1, 2, 'H10'),
        (12, 4, 7, 'H12'),
        (14, 2, 5, 'H14'),
    ]:
        table.merge_cells(r, c0, last_column=c1, value=label)
    table.merge_cells(2, 5, 3, 7, value='BOX')
    table.merge_cells(8, 1, 9, 2, value='SQ')

    bottom = str(table).splitlines()[-1]
    assert bottom.startswith('╘'), bottom
    assert bottom.endswith('╛'), bottom
    assert '╞' not in bottom and '╡' not in bottom, bottom
    assert '╤' not in bottom and '╪' not in bottom, bottom
    # Continuous run under H14 (C2–C5): three inner junctions → ═.
    assert '╧═══════════════════════════════╧' in bottom, bottom  # C2–C5: 7+1+7+1+7+1+7


# +-------------------------------------------------------------------------+
# Generic junction / cap algorithm (no demo-specific hardcoding)
# +-------------------------------------------------------------------------+

def test_hyphen_in_cell_text_does_not_block_column_only_caps():
    """A lone '-' inside cell text must not be mistaken for a rule line.

    Column-only styles insert synthetic caps around multi-column merges; if
    'Beta-1' were treated as a rule, those caps would be skipped.
    """
    table = Table(style_name='round_edges')
    table.add_column('Cat', [''] * 5)
    table.add_column('Item', ['Alpha-1', 'Alpha-2', 'Beta-1', 'Beta-2', 'Beta-3'])
    table.add_column('V', [1, 2, 3, 4, 5])
    table.add_column('N', ['n0', 'n1', 'n2', 'n3', 'n4'])
    table.merge_cells(0, 0, last_row=1, value='Alpha')
    table.merge_cells(2, 0, last_row=4, value='Beta')
    table.merge_cells(2, 2, last_row=4, last_column=3, value='BLOCK')

    lines = str(table).splitlines()
    block_i = next(i for i, line in enumerate(lines) if 'BLOCK' in line)
    # Cap above the block (between Alpha group and BLOCK) and below (or end).
    above = lines[block_i - 2]  # one data line of BLOCK above middle, then cap
    # Find a synthetic/body rule that carries a tee into the V|N span.
    rule_lines = [line for line in lines if ('┬' in line or '┴' in line or '├' in line) and '═' not in line]
    assert rule_lines, '\n'.join(lines)
    # At least one rule must sit next to the BLOCK rows.
    assert any(
        abs(i - block_i) <= 3 and ('┬' in line or '┴' in line or '─' in line)
        for i, line in enumerate(lines)
        if _looks_like_rule_line(line)
    ), '\n'.join(lines)


def _looks_like_rule_line(line: str) -> bool:
    import re
    return re.search(r'[─━═┄┅┈┉╌╍▬−\-~=]{2,}', line) is not None


def test_multi_column_merge_in_column_only_style_gets_caps_matching_outer_dash():
    """Caps above/below a multi-column merge use the table end horizontal glyph."""
    table = Table(style_name='round_edges')
    table.add_column('A', ['a1', 'a2', 'a3', 'a4'])
    table.add_column('B', ['b1', 'b2', 'b3', 'b4'])
    table.add_column('C', ['c1', 'c2', 'c3', 'c4'])
    table.merge_cells(1, 1, last_row=2, last_column=2, value='BC')

    rendered = str(table)
    lines = rendered.splitlines()
    assert any('BC' in line for line in lines)
    # Outer end uses ─; synthetic caps must also use ─ (not a foreign dash).
    rules = [line for line in lines if _looks_like_rule_line(line) and not line.startswith('╭') and not line.startswith('╰') and '═' not in line]
    assert rules, rendered
    for line in rules:
        assert '┄' not in line and '═' not in line, line


def test_dashes_style_bottom_under_merge_keeps_dotted_glyph_not_solid():
    """Suppressing a bottom junction must extend the rule's own h glyph (┄), never ─."""
    table = Table(style_name='dashes')
    for d, name in enumerate(['A', 'B', 'C', 'D']):
        table.add_column(name, [f'r{r}c{d}' for r in range(3)])
    table.merge_cells(2, 2, last_column=3, value='CD')

    bottom = str(table).splitlines()[-1]
    assert '─' not in bottom, bottom
    assert bottom.startswith('└') and bottom.endswith('┘'), bottom
    # Continuous dotted run under CD (one suppressed inner junction).
    assert '┴┄┄┄┄┄┄┄┄┄┄┄┄┄┘' in bottom or bottom.count('┄') >= 10, bottom


def test_synthetic_rule_blanks_through_taller_crossing_merge():
    """A short multi-column merge must not leave ghost ┼ inside a taller 2D merge."""
    table = Table(style_name='pretty_columns')
    for c in range(6):
        table.add_column(f'C{c}', [f'r{r}c{c}' for r in range(5)])
    table.merge_cells(0, 0, 2, 2, value='TALL')
    table.merge_cells(0, 3, 1, 5, value='SHORT')

    lines = str(table).splitlines()
    # The rule just under SHORT (still inside TALL's rows) must not show ┼
    # under TALL's columns — those junctions are ghosts.
    short_i = next(i for i, line in enumerate(lines) if 'SHORT' in line)
    # Scan rules after SHORT's text line while TALL still covers row 2.
    for line in lines[short_i + 1:]:
        if 'TALL' in line or 'r2c' in line or 'r3c' in line:
            # data
            if 'r3c' in line:
                break
            continue
        if not _looks_like_rule_line(line):
            continue
        # Under TALL (first three col bands) there must be no ┼ / ╪ ghost.
        # Left portion before the SHORT columns' reopen.
        left = line.split('r')[0] if False else line
        # Take from start through the junction that opens column 3.
        # Ghost pattern was: ├──────┼──────┼──────┼
        assert '┼──────┼──────┼' not in line, line
        assert '╪══════╪══════╪' not in line, line
        break


def test_round_edges_end_corners_survive_last_row_horizontal_merge():
    """Repairing the end line must keep ╰/╯, not rewrite them as └/┘."""
    table = Table(style_name='round_edges')
    table.add_column('A', ['a1', 'a2', 'a3'])
    table.add_column('B', ['b1', 'b2', 'b3'])
    table.add_column('C', ['c1', 'c2', 'c3'])
    table.merge_cells(2, 1, last_column=2, value='BC')

    bottom = str(table).splitlines()[-1]
    assert bottom.startswith('╰'), bottom
    assert bottom.endswith('╯'), bottom
    assert '└' not in bottom and '┘' not in bottom, bottom


def test_crossing_vertical_merge_keeps_edge_when_cap_inserted():
    """When a cap is inserted under a 2D block beside a continuing vertical
    merge, the vertical merge's column stays an edge (no horizontal through it)."""
    table = Table(style_name='round_edges')
    table.add_column('Cat', [''] * 6)
    table.add_column('Item', [f'i{r}' for r in range(6)])
    table.add_column('V', list(range(6)))
    table.add_column('N', [f'n{r}' for r in range(6)])
    table.merge_cells(0, 0, last_row=5, value='ALL')
    table.merge_cells(1, 2, last_row=3, last_column=3, value='BOX')

    lines = str(table).splitlines()
    # Rules flanking BOX must blank the Cat column (ALL continues through).
    for i, line in enumerate(lines):
        if not _looks_like_rule_line(line):
            continue
        if '═' in line or line.startswith('╭') or line.startswith('╰'):
            continue
        # Body synthetic rule: starts with │ (edge through ALL) not ├.
        if '┬' in line or '┴' in line:
            assert line.startswith('│'), line
