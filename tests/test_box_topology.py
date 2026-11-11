"""Topology of box-drawing glyphs around merges, for every border style."""

import os

import pytest

from flexablelib import Table
from flexablelib.box_topology import check_merge_fill, new_breaks
from flexablelib.fast import strip_ansi, visible_width


RESET = '\x1b[0m'

H_BG = (255, 0, 170)
V_BG = (0, 255, 170)
BLOCK_BG = (0, 170, 255)


def _styles():
    return list(Table().possible_styles)


def _base(style, colored):
    table = Table(style_name=style)
    table.add_column('A', ['a0', 'a1', 'a2', 'a3'])
    table.add_column('B', ['b0', 'b1', 'b2', 'b3'])
    table.add_column('C', ['c0', 'c1', 'c2', 'c3'])
    table.add_column('D', ['d0', 'd1', 'd2', 'd3'])
    if colored:
        os.environ['FORCE_COLOR'] = '1'
        table.use_colors = True
        table.border_color = 'red'
        table.zebra = 'black on #222222'
    else:
        table.use_colors = False
    return table


def _apply(table, merges, colored):
    colors = {
        'h': 'black on #ff00aa',
        'v': 'black on #00ffaa',
        'b': 'black on #00aaff',
    }
    for kind, coords, value in merges:
        kw = dict(
            last_row=coords[2] if len(coords) > 2 else coords[0],
            last_column=coords[3] if len(coords) > 3 else coords[1],
            value=value,
            align='c',
        )
        if colored:
            kw['color'] = colors[kind]
        table.merge_cells(coords[0], coords[1], **kw)
    return table


# Battery: H, V, 2D, corners, edges, adjacent, against header and footer.
_BATTERY = [
    ('H-mid', [('h', (1, 1, 1, 2), 'HSPAN')]),
    ('V-mid', [('v', (1, 1, 2, 1), 'VSPAN')]),
    ('2D-mid', [('b', (1, 1, 2, 2), 'BLOCK')]),
    ('H-corner-tl', [('h', (0, 0, 0, 1), 'TL')]),
    ('H-corner-br', [('h', (3, 2, 3, 3), 'BR')]),
    ('V-edge-left', [('v', (0, 0, 2, 0), 'LEFT')]),
    ('V-edge-right', [('v', (1, 3, 3, 3), 'RIGHT')]),
    ('2D-first-row', [('b', (0, 1, 1, 2), 'HEAD')]),
    ('2D-last-row', [('b', (2, 1, 3, 2), 'FOOT')]),
    ('adjacent-side', [('v', (1, 0, 2, 0), 'L'), ('v', (1, 1, 2, 1), 'R')]),
    ('adjacent-stacked', [('h', (1, 1, 1, 2), 'TOP'), ('h', (2, 1, 2, 2), 'BOT')]),
    ('adjacent-L', [('v', (0, 0, 2, 0), 'TALL'), ('h', (0, 1, 0, 2), 'WIDE')]),
]


@pytest.mark.parametrize('style', _styles())
@pytest.mark.parametrize('name,merges', _BATTERY, ids=[n for n, _ in _BATTERY])
def test_battery_plain_topology(style, name, merges):
    plain = _base(style, colored=False)
    baseline = str(plain)
    _apply(plain, merges, colored=False)
    rendered = str(plain)
    lines = rendered.splitlines()
    if len({visible_width(l) for l in baseline.splitlines()}) == 1:
        assert len({visible_width(l) for l in lines}) == 1
    assert new_breaks(lines, baseline.splitlines()) == []


@pytest.mark.parametrize('style', _styles())
def test_battery_colored_matches_plain_and_fills(style):
    os.environ['FORCE_COLOR'] = '1'
    # One table with H + V + 2D together (they do not overlap).
    merges = [
        ('h', (0, 0, 0, 1), 'HSPAN'),
        ('v', (1, 0, 2, 0), 'VSPAN'),
        ('b', (1, 2, 2, 3), 'BLOCK'),
    ]
    plain = _apply(_base(style, colored=False), merges, colored=False)
    colored = _apply(_base(style, colored=True), merges, colored=True)
    plain_s = str(plain)
    color_s = str(colored)
    assert strip_ansi(color_s) == plain_s
    assert RESET * 2 not in color_s
    assert new_breaks(plain_s.splitlines(), str(_base(style, False)).splitlines()) == []
    assert new_breaks(color_s.splitlines(), plain_s.splitlines()) == []
    problems = []
    problems += check_merge_fill(color_s.splitlines(), H_BG, 'HSPAN')
    problems += check_merge_fill(color_s.splitlines(), V_BG, 'VSPAN')
    problems += check_merge_fill(color_s.splitlines(), BLOCK_BG, 'BLOCK')
    assert problems == []
