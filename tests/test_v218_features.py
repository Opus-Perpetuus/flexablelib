"""2.0.18: ``border_text`` align works without ``offset=None``."""
import pytest

from flexablelib import Table
from flexablelib.text_width import strip_ansi as bare


def _framed():
    table = Table(rows=[['alpha', 1], ['beta', 2], ['gamma', 3]],
                  headers=['name', 'n'])
    table.style_name = 'modern'
    return table


def _top(table):
    return bare(table.compose()).splitlines()[0]


def test_default_placement_is_unchanged():
    table = _framed()
    table.border_text('v2', where='top')
    assert _top(table) == '┌v2─────┬───┐'


def test_right_align_works_with_the_default_offset():
    table = _framed()
    table.border_text('v2', where='top', align='right')
    assert _top(table) == '┌───────┬─v2┐'


def test_center_align_works_with_the_default_offset():
    table = _framed()
    table.border_text('v2', where='top', align='center')
    top = _top(table)
    assert top[0] == '┌' and top[-1] == '┐'
    assert top.index('v2') in (5, 6)


def test_explicit_left_offset_is_the_absolute_start():
    table = _framed()
    table.border_text('v2', where='top', offset=4)
    assert _top(table) == '┌───v2──┬───┐'
    table = _framed()
    table.border_text('v2', where='top', offset=0)
    assert _top(table).startswith('v2─')


def test_explicit_offset_with_right_align_is_a_right_margin():
    table = _framed()
    table.border_text('v2', where='top', align='right', offset=3)
    assert _top(table) == '┌───────v2──┐'
    table = _framed()
    table.border_text('v2', where='top', align='r', offset=0)
    assert _top(table).endswith('─v2')


def test_explicit_offset_with_center_align_is_a_margin_on_both_sides():
    table = _framed()
    table.border_text('ab', where='top', align='center', offset=2)
    top = _top(table)
    width = len(top)
    start = top.index('ab')
    assert start >= 2 and start + 2 <= width - 2
    assert abs((start - 2) - (width - 2 - (start + 2))) <= 1


def test_right_align_on_bottom_rule_keeps_both_corners():
    table = _framed()
    table.border_text('END', where='bottom', align='right')
    bottom = bare(table.compose()).splitlines()[-1]
    assert bottom.startswith('└') and bottom.endswith('END┘')


def test_vertical_default_skips_the_top_corner():
    table = _framed()
    table.border_text('AB', where='left')
    lines = bare(table.compose()).splitlines()
    assert lines[0][0] == '┌'
    assert lines[1][0] == 'A' and lines[2][0] == 'B'


def test_vertical_right_align_ends_above_the_bottom_corner():
    table = _framed()
    table.border_text('XY', where='right', align='right')
    lines = bare(table.compose()).splitlines()
    assert lines[-1][-1] == '┘'
    assert lines[-3][-1] == 'X' and lines[-2][-1] == 'Y'


def test_vertical_center_align():
    table = _framed()
    table.border_text('Q', where='left', align='center')
    lines = bare(table.compose()).splitlines()
    rows = [i for i, line in enumerate(lines) if line[0] == 'Q']
    assert rows == [(len(lines) - 1) // 2]


def test_colour_still_applies_with_alignment():
    table = _framed()
    table.border_text('v2', where='top', align='right', color='red')
    assert '\x1b[31m' in table.compose()


def test_bad_offset_is_rejected():
    with pytest.raises(ValueError):
        _framed().border_text('x', offset=-1)
    with pytest.raises(TypeError):
        _framed().border_text('x', offset='far')
