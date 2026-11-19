"""3.7.4 core: numbers are read from ASCII digits only and a float past
what a float holds stays text; the Python PNG ``unfilter`` refuses the
sizes the C one refuses; ``box_topology.visible_cells`` keeps the columns
right after a wide character."""

import pytest

from flexablelib import Table
from flexablelib import _images as I
from flexablelib.box_topology import bg_runs, visible_cells
from flexablelib.readers import parse_value


@pytest.mark.parametrize('text', ['1\u0663', '1.\u0663', '1e\u0663',
                                  '1\uff11', '\u0663', '\uff11\uff12'])
def test_parse_value_other_scripts_digits_stay_text(text):
    assert parse_value(text) == text      # '1٣' was 13, '1１' was 11


@pytest.mark.parametrize('text', ['1e400', '-1e400', '1.5e999'])
def test_parse_value_float_overflow_stays_text(text):
    assert parse_value(text) == text      # was inf / -inf


@pytest.mark.parametrize('text, number', [('12', 12), ('-0', 0), (' 7 ', 7),
                                          ('1.5', 1.5), ('.5', 0.5),
                                          ('1e5', 1e5), ('1e-400', 0.0)])
def test_parse_value_numbers(text, number):
    value = parse_value(text)
    assert value == number and type(value) is type(number)


def test_csv_keeps_huge_and_mixed_digit_text():
    table = Table.from_csv('n,m\n1e400,1\u0663\n2.5,7\n')
    assert table.to_records() == [{'n': '1e400', 'm': '1\u0663'},
                                  {'n': 2.5, 'm': 7}]
    assert 'inf' not in table.to_csv()


@pytest.mark.parametrize('rows, stride, bpp', [(-1, 0, 1), (1, -1, 1),
                                               (1, 2, 0)])
def test_python_unfilter_refuses_bad_sizes_like_c(rows, stride, bpp):
    with pytest.raises(ValueError):
        I._py_unfilter(b'\x00' * 8, rows, stride, bpp)
    if I._C is not None:
        with pytest.raises(ValueError):
            I._C.unfilter(b'\x00' * 8, rows, stride, bpp)


def test_visible_cells_wide_characters():
    assert visible_cells('\u4e2da') == [(0, '\u4e2d', None), (1, '', None),
                                         (2, 'a', None)]   # 'a' was at 3
    line = '\x1b[41m\u4e2d\x1b[0ma\x1b[41mb\x1b[0m'
    assert bg_runs(line, 41) == [(0, 2), (3, 4)]
    assert visible_cells('e\u0301x') == [(0, 'e', None), (1, 'x', None)]


def test_read_json_is_utf8(tmp_path):
    from flexablelib import utils
    path = tmp_path / 'datos.json'
    path.write_bytes('{"año": "Pequeño ✓"}'.encode('utf-8'))
    # Windows CI runs with a cp1252 locale, where this read 'aÃ±o'.
    assert utils.read_json(str(path)) == {'año': 'Pequeño ✓'}


# -- box_topology: the checks the merge tests rely on --------------------------

def test_box_topology_arms_and_grid():
    from flexablelib.box_topology import arms, grid
    assert arms('') is None and arms('a') is None
    assert arms('┼') == (True, True, True, True)
    assert arms('┹') == (True, False, True, True)
    assert grid('\x1b[31m中\x1b[0m-\u0301|') == ['中', '', '-', '|']


def test_box_topology_sgr_tracking():
    from flexablelib.box_topology import visible_cells
    line = ('\x1b[48;2;1;2;3ma\x1b[48;5;9mb\x1b[44mc\x1b[49md'
            '\x1b[103me\x1b[mf\x1b[38;5mg\x1b[39;41mh')
    bgs = [bg for _c, _ch, bg in visible_cells(line)]
    assert bgs == [('2', 1, 2, 3), ('5', 9), 44, None, 103, None, None, 41]
    fg_only = visible_cells('\x1b[38;2;1;2;3;31mx')
    assert fg_only == [(0, 'x', None)]


def test_box_topology_check_topology():
    from flexablelib.box_topology import check_topology, signatures
    good = ['┌─┬─┐', '│a│b│', '└─┴─┘']
    assert check_topology(good) == []
    broken = ['┌─┬─┐', '│a b│', '└─┴─┘']
    found = check_topology(broken)
    assert (0, 2, '┬', 'down', ' ') in found
    assert (2, 2, '┴', 'up', ' ') in found
    stray = ['┌───┐', '│a│b│', '└───┘']
    kinds = {d for _r, _c, _ch, d, _n in check_topology(stray)}
    assert {'up', 'down'} <= kinds
    assert ('no-down', '─', '│') in signatures(stray)
    # ASCII '+' stands in for any tee, so unused arms are fine.
    assert check_topology(['+-+', '| |', '+-+']) == []


def test_box_topology_new_breaks_and_markdown_rule():
    from flexablelib.box_topology import new_breaks
    base = ['┌─┬─┐', '│a│b│', '└─┴─┘']
    merged = ['┌─┬─┐', '│ab │', '└─┴─┘']
    assert new_breaks(merged, base)
    assert new_breaks(base, base) == []
    md = ['| a | b |', '|---|---|', '| 1   2 |']
    md_base = ['| a | b |', '|---|---|', '| 1 | 2 |']
    breaks = new_breaks(md, md_base)
    assert all(row != 1 for row, *_ in breaks)


def test_box_topology_check_merge_fill():
    from flexablelib.box_topology import check_merge_fill
    on, off = '\x1b[41m', '\x1b[0m'
    solid = ['x' + on + 'ab' + off, 'x' + on + 'cd' + off]
    assert check_merge_fill(solid, 41, 'ok') == []
    assert check_merge_fill(['plain'], 41, 'none') == [
        'none: background 41 never appeared']
    split = [on + 'a' + off + 'b' + on + 'c' + off]
    assert 'non-contiguous' in check_merge_fill(split, 41, 's')[0]
    gap = [on + 'a' + off, 'b', on + 'c' + off]
    assert any('solid block' in p for p in check_merge_fill(gap, 41, 'g'))
    ragged = [on + 'ab' + off, on + 'a' + off]
    assert any('rectangular' in p for p in check_merge_fill(ragged, 41, 'r'))
    rgb = ['\x1b[48;2;1;2;3mab' + off]
    assert check_merge_fill(rgb, (1, 2, 3), 'rgb') == []
