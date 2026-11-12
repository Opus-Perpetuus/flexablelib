"""
``max_width`` is the width of everything drawn, panel and shadow included.

The columns used to be sized for ``max_width`` and the panel (one column each
side) and shadow (one on the right) added afterwards, so a panelled table
came out up to three columns too wide -- also when squeezed by ``render``
and when stretched with ``expand_to_window``.
"""

import pytest

from flexablelib import Table
from flexablelib.text_width import strip_ansi, visible_width

ROWS = [
    [1000000000000, 0, '😀👍🏽', 'é'],
    ['', 3.14159, 'ｱｲｳ', ' lead '],
    [True, 'é', ' lead ', 'x' * 25],
]

CHROME = [(False, False), (True, False), (False, True), (True, True)]


def _width(text):
    return max(visible_width(line) for line in strip_ansi(text).split('\n'))


def _table(panel, shadow):
    table = Table(rows=[list(r) for r in ROWS], headers=['a', 'b', 'c', 'd'])
    table.use_colors = False
    table.panel = panel
    table.shadow = shadow
    return table


@pytest.mark.parametrize('panel, shadow', CHROME)
@pytest.mark.parametrize('overflow', ['wrap', 'truncate'])
@pytest.mark.parametrize('limit', [30, 40, 50])
def test_squeezed_table_with_chrome_fits_max_width(panel, shadow, overflow,
                                                   limit):
    table = _table(panel, shadow)
    table.overflow = overflow
    table.max_width = limit
    assert _width(table.compose()) <= limit


@pytest.mark.parametrize('panel, shadow', CHROME)
def test_render_never_exceeds_the_width_it_was_given(panel, shadow):
    table = _table(panel, shadow)
    for width in (30, 45, 60, 80):
        assert _width(table.render(width)) <= width


@pytest.mark.parametrize('panel, shadow', CHROME)
def test_expand_to_window_fills_exactly_with_chrome(panel, shadow):
    table = Table(rows=[[1, 2]], headers=['a', 'b'])
    table.use_colors = False
    table.panel = panel
    table.shadow = shadow
    table.max_width = 30
    table.expand_to_window = True
    lines = strip_ansi(table.compose()).split('\n')
    assert max(visible_width(line) for line in lines) == 30


def test_panel_frame_stays_closed_when_squeezed():
    table = _table(True, False)
    table.max_width = 40
    lines = strip_ansi(table.compose()).split('\n')
    assert lines[0].startswith('╭') and lines[0].endswith('╮')
    assert lines[-1].startswith('╰') and lines[-1].endswith('╯')
    assert len({visible_width(line) for line in lines}) == 1


def test_too_narrow_message_counts_the_panel():
    table = Table(rows=[[1, 2, 3]], headers=['a', 'b', 'c'])
    table.too_narrow_message = 'need {needed}, have {available}'
    table.max_width = 20
    plain = table.compose()
    table.panel = True
    panelled = table.compose()
    # Without the panel it squeezes in (19 columns at the narrowest); the
    # panel's two frame columns tip it over, and both numbers include them.
    assert not plain.startswith('need')
    assert panelled == 'need 21, have 20'
