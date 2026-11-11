"""
Merge and zebra fills are a single rectangular paint layer.

For every border style: a coloured H, V and 2D merge plus zebra keeps a
uniform visible width, the same skeleton as the uncoloured table, a
contiguous rectangular background, no doubled resets, and no crossing
glyphs inside a merge.
"""

import os
import re

import pytest

from flexablelib import Table
from flexablelib.fast import char_width, strip_ansi, visible_width


_SGR = re.compile(r'\x1b\[([0-9;]*)m')
_RESET = '\x1b[0m'

# Tees and crossings that must not appear inside a merge interior.
_CROSSING = set(
    '┴┬┼╬╪╫╩╦╧╤┞┟┡┢┤╡╢╣├╟╠╨╥╙╜╓╖╩╞╪╡╤╧╫╬+'
    '╂╀╁╃╄╅╆╇╈╉╊'
)

# Unique 24-bit backgrounds so a run can be identified per merge.
H_BG = (255, 0, 170)      # #ff00aa
V_BG = (0, 255, 170)      # #00ffaa
BLOCK_BG = (0, 170, 255)  # #00aaff


def _styles():
    return list(Table().possible_styles)


def _apply_sgr(params, fg, bg):
    if not params:
        return None, None
    i = 0
    n = len(params)
    while i < n:
        p = params[i]
        if p == 0:
            fg, bg = None, None
        elif p == 39:
            fg = None
        elif p == 49:
            bg = None
        elif p in (38, 48):
            kind = 'fg' if p == 38 else 'bg'
            if i + 1 < n and params[i + 1] == 2 and i + 4 < n:
                val = ('2', params[i + 2], params[i + 3], params[i + 4])
                i += 4
            elif i + 1 < n and params[i + 1] == 5 and i + 2 < n:
                val = ('5', params[i + 2])
                i += 2
            else:
                val = ('raw', p)
            if kind == 'fg':
                fg = val
            else:
                bg = val
        elif 40 <= p <= 47 or 100 <= p <= 107:
            bg = p
        elif 30 <= p <= 37 or 90 <= p <= 97:
            fg = p
        i += 1
    return fg, bg


def visible_cells(line):
    """List of (column, character, bg) for each visible column of ``line``."""
    out = []
    i = 0
    col = 0
    fg = bg = None
    while i < len(line):
        match = _SGR.match(line, i)
        if match:
            raw = match.group(1)
            params = [int(part) if part else 0 for part in raw.split(';')] if raw else [0]
            fg, bg = _apply_sgr(params, fg, bg)
            i = match.end()
            continue
        ch = line[i]
        width = char_width(ch)
        if width <= 0:
            i += 1
            continue
        out.append((col, ch, bg))
        for _ in range(width - 1):
            out.append((col + 1, '', bg))
            col += 1
        col += width
        i += 1
    return out


def bg_runs(line, wanted):
    """Contiguous [start, end) column ranges whose background is ``wanted``."""
    runs = []
    start = None
    for col, _ch, bg in visible_cells(line):
        hit = bg == ('2',) + wanted if isinstance(wanted, tuple) and len(wanted) == 3 else bg == wanted
        if hit:
            if start is None:
                start = col
        elif start is not None:
            runs.append((start, col))
            start = None
    if start is not None:
        width = visible_width(line)
        runs.append((start, width))
    return runs


def _build(style, colored):
    table = Table(style_name=style)
    table.add_column('A', ['a0', 'a1', 'a2'])
    table.add_column('B', ['b0', 'b1', 'b2'])
    table.add_column('C', ['c0', 'c1', 'c2'])
    table.add_column('D', ['d0', 'd1', 'd2'])
    if colored:
        os.environ['FORCE_COLOR'] = '1'
        table.use_colors = True
        table.zebra = 'black on #222222'
        table.border_color = 'red'
        table.column_colors = {'D': 'black on yellow'}
        table.merge_cells(0, 0, last_column=1, value='HSPAN', color='black on #ff00aa', align='c')
        table.merge_cells(1, 0, last_row=2, value='VSPAN', color='black on #00ffaa', align='c')
        table.merge_cells(1, 2, 2, 3, value='BLOCK', color='black on #00aaff', align='c')
    else:
        table.use_colors = False
        table.merge_cells(0, 0, last_column=1, value='HSPAN', align='c')
        table.merge_cells(1, 0, last_row=2, value='VSPAN', align='c')
        table.merge_cells(1, 2, 2, 3, value='BLOCK', align='c')
    return table


def _assert_rectangular(rendered, label, wanted):
    """Every line that carries ``wanted`` has one run, same start and width."""
    lines = rendered.splitlines()
    hits = []
    for index, line in enumerate(lines):
        runs = bg_runs(line, wanted)
        if not runs:
            continue
        assert len(runs) == 1, (label, index, runs, line)
        start, end = runs[0]
        assert end > start, (label, line)
        # Crossing glyphs must not sit inside the fill.
        for col, ch, bg in visible_cells(line):
            if start <= col < end and ch in _CROSSING:
                raise AssertionError(
                    f'{label}: crossing {ch!r} inside merge at col {col}: {line!r}'
                )
        hits.append((index, start, end))
    assert hits, f'{label} background {wanted} never appeared in:\n{rendered}'
    # The lines that carry the fill must be a contiguous block of rows
    # (the interior rectangle), all with the same column span.
    indexes = [index for index, _s, _e in hits]
    assert indexes == list(range(indexes[0], indexes[-1] + 1)), (label, indexes)
    span = {(start, end) for _i, start, end in hits}
    assert len(span) == 1, (label, span, hits)


@pytest.mark.parametrize('style', _styles())
def test_coloured_merges_and_zebra_paint_cleanly(style):
    os.environ['FORCE_COLOR'] = '1'
    plain = str(_build(style, colored=False))
    colored = str(_build(style, colored=True))

    colored_lines = colored.splitlines()
    plain_lines = plain.splitlines()

    assert strip_ansi(colored) == plain
    assert len(colored_lines) == len(plain_lines)
    assert _RESET * 2 not in colored

    plain_widths = {visible_width(line) for line in plain_lines}
    if len(plain_widths) == 1:
        color_widths = {visible_width(line) for line in colored_lines}
        assert color_widths == plain_widths

    for label, wanted in (
        ('HSPAN', H_BG),
        ('VSPAN', V_BG),
        ('BLOCK', BLOCK_BG),
    ):
        _assert_rectangular(colored, label, wanted)


@pytest.mark.parametrize('style', _styles())
def test_column_only_styles_do_not_insert_synthetic_caps(style):
    """A multi-column merge must not grow the table by a synthetic rule."""
    table = Table(style_name=style)
    table.add_column('A', ['a1', 'a2', 'a3'])
    table.add_column('B', ['b1', 'b2', 'b3'])
    table.add_column('C', ['c1', 'c2', 'c3'])
    before = str(table)
    table.merge_cells(1, 0, last_column=1, value='AB')
    after = str(table)
    assert 'AB' in after
    # No synthetic cap: the merged table does not gain a line.
    assert len(after.splitlines()) == len(before.splitlines())
    widths = {visible_width(line) for line in after.splitlines()}
    if len({visible_width(line) for line in before.splitlines()}) == 1:
        assert len(widths) == 1


def test_zebra_plus_border_color_on_rows_keeps_rule_chrome():
    os.environ['FORCE_COLOR'] = '1'
    table = Table(style_name='single_rows')
    table.use_colors = True
    table.zebra = 'black on #333333'
    table.border_color = 'red'
    table.add_column('A', ['a0', 'a1', 'a2'])
    table.add_column('B', ['b0', 'b1', 'b2'])
    rendered = str(table)
    assert _RESET * 2 not in rendered
    for line in rendered.splitlines():
        if '─' not in strip_ansi(line):
            continue
        for _col, ch, bg in visible_cells(line):
            if ch in '─├┼┤┌┐└┘':
                assert bg is None, (ch, bg, line)
        assert '31m' in line, line


def test_theme_slate_2d_merge_is_rectangular():
    os.environ['FORCE_COLOR'] = '1'
    table = Table()
    table.apply_theme('slate')
    table.use_colors = True
    table.add_column('A', ['a0', 'a1', 'a2'])
    table.add_column('B', ['b0', 'b1', 'b2'])
    table.add_column('C', ['c0', 'c1', 'c2'])
    table.merge_cells(1, 1, 2, 2, value='Centro', color='black on #facc15', align='c')
    rendered = str(table)
    assert _RESET * 2 not in rendered
    assert 'Centro' in strip_ansi(rendered)
    _assert_rectangular(rendered, 'Centro', (250, 204, 21))
