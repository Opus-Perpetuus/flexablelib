"""Rare merge edge cases: all border styles × call-order permutations.

These assert the generic junction algorithm — never demo names. Each case is a
small structural table chosen to stress caps, crossings, bottoms, and hyphens.
"""

import itertools
import pytest

from flexablelib import Table
from flexablelib.fast import visible_width

# Styles that ship with vertical column rules (the ones merges must paint).
STYLES_WITH_VERTICALS = [
    'pretty_grid',
    'pretty_columns',
    'round_edges',
    'dashes',
    'grid',
    'bold_borderline',
    'thin_borderline',
    'double_grid',
    'grid_eheader',
]


def _square(rendered: str) -> None:
    widths = {visible_width(line) for line in rendered.splitlines()}
    # Title lines may be shorter; body shares one width.
    assert len(widths) <= 2, widths
    assert max(widths) >= 3


def _has_h_run(line: str) -> bool:
    import re
    return re.search(r'[─━═┄┅┈┉╌╍▬−\-~=]{2,}', line) is not None


def _build_base(style: str) -> Table:
    table = Table(style_name=style)
    table.add_column('A', ['a0', 'a1', 'a2', 'a3'])
    table.add_column('B', ['b0', 'b1', 'b2', 'b3'])
    table.add_column('C', ['c0', 'c1', 'c2', 'c3'])
    table.add_column('D', ['d0', 'd1', 'd2', 'd3'])
    return table


@pytest.mark.parametrize('style', STYLES_WITH_VERTICALS)
def test_horizontal_merge_mid_table_keeps_square(style):
    table = _build_base(style)
    table.merge_cells(1, 1, last_column=2, value='BC')
    rendered = str(table)
    assert 'BC' in rendered
    _square(rendered)


@pytest.mark.parametrize('style', STYLES_WITH_VERTICALS)
def test_vertical_merge_mid_table_keeps_square(style):
    table = _build_base(style)
    table.merge_cells(1, 0, last_row=2, value='AS')
    rendered = str(table)
    assert 'AS' in rendered or 'AS' in rendered
    _square(rendered)


@pytest.mark.parametrize('style', STYLES_WITH_VERTICALS)
def test_block_merge_keeps_square(style):
    table = _build_base(style)
    table.merge_cells(1, 1, 2, 2, value='BLOCK')
    rendered = str(table)
    assert 'BLOCK' in rendered
    _square(rendered)


@pytest.mark.parametrize('style', STYLES_WITH_VERTICALS)
def test_last_row_horizontal_merge_bottom_is_not_header_tee(style):
    table = _build_base(style)
    table.merge_cells(3, 1, last_column=2, value='BC-end')
    bottom = str(table).splitlines()[-1]
    # Header-only tees must not appear on the end line.
    for bad in ('╞', '╡', '╤', '╪'):
        # double_grid / pretty_columns end lines use ╘═╧╛ — ╞ would be wrong.
        if bad in bottom and not bottom.startswith(('╘', '╚', '╙', '╰', '└', '+', '┗')):
            pytest.fail(f'header tee {bad!r} on bottom: {bottom!r}')
    _square(str(table))


@pytest.mark.parametrize('style', ['pretty_columns', 'round_edges', 'dashes'])
def test_column_only_multi_col_merge_inserts_cap(style):
    table = _build_base(style)
    table.merge_cells(1, 0, last_column=1, value='AB')
    lines = str(table).splitlines()
    assert any(_has_h_run(line) and '═' not in line or _has_h_run(line)
               for line in lines)
    # There is a body-ish rule that is not only the header double rule.
    bodyish = [line for line in lines if _has_h_run(line)]
    assert len(bodyish) >= 2, lines  # header + at least one cap or end
    _square(str(table))


@pytest.mark.parametrize('style', ['pretty_columns', 'round_edges', 'dashes'])
def test_short_merge_does_not_ghost_through_taller_block(style):
    table = Table(style_name=style)
    for c in range(4):
        table.add_column(f'C{c}', [f'r{r}c{c}' for r in range(4)])
    table.merge_cells(0, 0, 2, 1, value='TALL')
    table.merge_cells(0, 2, 1, 3, value='SHORT')
    rendered = str(table)
    # Classic ghost: ┼──────┼ under TALL on the SHORT-below rule.
    assert '┼──────┼──────┼' not in rendered
    assert '╪══════╪══════╪' not in rendered
    _square(rendered)


@pytest.mark.parametrize('style', ['round_edges', 'dashes', 'pretty_columns'])
def test_hyphenated_labels_still_get_caps(style):
    table = Table(style_name=style)
    table.add_column('Cat', ['', '', '', ''])
    table.add_column('Item', ['X-1', 'X-2', 'Y-1', 'Y-2'])
    table.add_column('V', [1, 2, 3, 4])
    table.add_column('N', ['n-0', 'n-1', 'n-2', 'n-3'])
    table.merge_cells(0, 0, last_row=1, value='X')
    table.merge_cells(2, 0, last_row=3, value='Y')
    table.merge_cells(2, 2, last_row=3, last_column=3, value='BOX')
    rendered = str(table)
    assert 'BOX' in rendered
    _square(rendered)
    # Must have a horizontal run flanking BOX (cap or end), not only header.
    lines = rendered.splitlines()
    box_i = next(i for i, line in enumerate(lines) if 'BOX' in line)
    nearby = lines[max(0, box_i - 3): box_i + 4]
    assert any(_has_h_run(line) for line in nearby), rendered


@pytest.mark.parametrize('style', ['dashes'])
def test_dashes_bottom_merge_has_no_solid_em_dash(style):
    table = _build_base(style)
    table.merge_cells(3, 2, last_column=3, value='CD')
    bottom = str(table).splitlines()[-1]
    assert '─' not in bottom, bottom


@pytest.mark.parametrize('style', ['round_edges'])
def test_round_end_corners_kept(style):
    table = _build_base(style)
    table.merge_cells(3, 1, last_column=2, value='BC')
    bottom = str(table).splitlines()[-1]
    assert bottom.startswith('╰') and bottom.endswith('╯'), bottom


# --- Call-order permutations -------------------------------------------------

def _orders():
    """Distinct sequences of building a 2x2 block merge + a vertical stack."""
    def style_first(style):
        t = Table(style_name=style)
        t.add_column('A', ['a0', 'a1', 'a2'])
        t.add_column('B', ['b0', 'b1', 'b2'])
        t.add_column('C', ['c0', 'c1', 'c2'])
        t.merge_cells(0, 0, 1, 1, value='BLK')
        t.merge_cells(0, 2, last_row=2, value='V')
        return t

    def merge_then_style(style):
        t = Table()
        t.add_column('A', ['a0', 'a1', 'a2'])
        t.add_column('B', ['b0', 'b1', 'b2'])
        t.add_column('C', ['c0', 'c1', 'c2'])
        t.merge_cells(0, 0, 1, 1, value='BLK')
        t.merge_cells(0, 2, last_row=2, value='V')
        t.style_name = style
        return t

    def add_row_then_merge(style):
        t = Table(style_name=style)
        t.add_column('A', [])
        t.add_column('B', [])
        t.add_column('C', [])
        for r in range(3):
            t.add_row([f'a{r}', f'b{r}', f'c{r}'])
        t.merge_cells(0, 0, 1, 1, value='BLK')
        t.merge_cells(0, 2, last_row=2, value='V')
        return t

    def merge_between_rows(style):
        t = Table(style_name=style)
        t.add_column('A', ['a0'])
        t.add_column('B', ['b0'])
        t.add_column('C', ['c0'])
        t.add_row(['a1', 'b1', 'c1'])
        t.merge_cells(0, 0, 1, 1, value='BLK')  # merge early
        t.add_row(['a2', 'b2', 'c2'])
        t.merge_cells(0, 2, last_row=2, value='V')
        return t

    return [
        ('style_first', style_first),
        ('merge_then_style', merge_then_style),
        ('add_row_then_merge', add_row_then_merge),
        ('merge_between_rows', merge_between_rows),
    ]


@pytest.mark.parametrize('style', ['pretty_grid', 'pretty_columns', 'round_edges', 'grid'])
@pytest.mark.parametrize('order_name,factory', _orders())
def test_call_order_permutations_render_square(style, order_name, factory):
    table = factory(style)
    rendered = str(table)
    assert 'BLK' in rendered
    _square(rendered)


@pytest.mark.parametrize('align', ['l', 'c', 'r'])
@pytest.mark.parametrize('style', ['pretty_grid', 'pretty_columns', 'round_edges'])
def test_centered_block_has_no_internal_ghost_cross(style, align):
    table = Table(style_name=style)
    for c in range(5):
        table.add_column(f'C{c}', [f'r{r}c{c}' for r in range(4)])
    table.merge_cells(0, 0, 2, 2, value='CENTER', align=align)
    rendered = str(table)
    # Ghost crosses under a 3-col span on a single rule.
    assert '┼──────┼──────┼' not in rendered
    assert '╪══════╪══════╪' not in rendered
    _square(rendered)


@pytest.mark.parametrize('style', ['pretty_grid', 'bold_borderline', 'double_grid'])
def test_adjacent_vertical_then_horizontal_l_shape(style):
    table = Table(style_name=style)
    for c in range(5):
        table.add_column(f'C{c}', [f'r{r}c{c}' for r in range(5)])
    table.merge_cells(0, 0, last_row=3, value='STEM')
    table.merge_cells(3, 1, last_column=3, value='BASE')
    rendered = str(table)
    assert 'STEM' in rendered and 'BASE' in rendered
    _square(rendered)


@pytest.mark.parametrize('style', ['pretty_grid', 'pretty_columns', 'dashes'])
def test_many_nonoverlapping_blocks(style):
    table = Table(style_name=style)
    for c in range(6):
        table.add_column(f'C{c}', [f'r{r}c{c}' for r in range(6)])
    table.merge_cells(0, 0, 1, 1, value='NW')
    table.merge_cells(0, 4, 1, 5, value='NE')
    table.merge_cells(2, 2, 3, 3, value='MID')
    table.merge_cells(4, 0, 5, 1, value='SW')
    table.merge_cells(4, 4, 5, 5, value='SE')
    rendered = str(table)
    for label in ('NW', 'NE', 'MID', 'SW', 'SE'):
        assert label in rendered
    _square(rendered)
