"""Alignment indicators on the align-sensitive styles (pipes, sticks).

Every column's separator segment must name that column's alignment and be
exactly as wide as the cells under it, whatever the alignment, the width or
the characters in the cells.
"""
import re

import pytest

from flexablelib import Table
from flexablelib.text_width import visible_width


def _render(rows, headers, style, align):
    table = Table(rows=rows, headers=headers, style_name=style)
    table.col_alignment = align
    return str(table).splitlines()


def _segments(line, sep):
    return line.strip(sep).split(sep)


def _assert_rules_match_cells(lines, rule_sep, cell_sep='|'):
    cell_widths = [visible_width(s) for s in _segments(lines[1], cell_sep)]
    for line in lines:
        if line.startswith(rule_sep):
            rule = [visible_width(s) for s in _segments(line, rule_sep)]
            assert rule == cell_widths, line


ROWS = [['a', 1, 'x'], ['bbb', 22, 'yyyyyy']]
HEADERS = ['L', 'R', 'Center']


def test_pipes_marks_left_right_and_center():
    lines = _render(ROWS, HEADERS, 'pipes', ['l', 'r', 'c'])
    left, right, center = _segments(lines[1], '|')
    assert re.fullmatch(r' :-+ ', left)
    assert re.fullmatch(r' -+: ', right)
    assert re.fullmatch(r' :-+: ', center)
    _assert_rules_match_cells(lines, '|')


def test_sticks_marks_each_alignment():
    lines = _render(ROWS, HEADERS, 'sticks', ['l', 'r', 'c'])
    left, right, center = _segments(lines[0], '+')
    assert '~<~' in left
    assert '~>~' in right
    assert '~^~' in center
    _assert_rules_match_cells(lines, '+')


@pytest.mark.parametrize('style, rule_sep', [('pipes', '|'), ('sticks', '+')])
def test_centered_wide_characters_keep_rules_aligned(style, rule_sep):
    lines = _render(
        [['漢字', 1.5], ['😀', 22.25]], ['名前', '数'], style, 'c'
    )
    _assert_rules_match_cells(lines, rule_sep)


@pytest.mark.parametrize('style, rule_sep', [('pipes', '|'), ('sticks', '+')])
def test_centered_one_char_columns_drop_margins_not_width(style, rule_sep):
    lines = _render([['a', 'b'], ['c', 'd']], ['x', 'y'], style, 'c')
    _assert_rules_match_cells(lines, rule_sep)
    marker = ':-:' if style == 'pipes' else '~^~'
    assert _segments(lines[1 if style == 'pipes' else 0], rule_sep) == [
        marker, marker
    ]


def test_column_too_narrow_for_indicator_gets_plain_rule():
    lines = _render([['', 1], ['', 2]], ['', 'n'], 'sticks', ['l', 'r'])
    _assert_rules_match_cells(lines, '+')
    empty_segment = _segments(lines[0], '+')[0]
    assert '~' not in empty_segment
