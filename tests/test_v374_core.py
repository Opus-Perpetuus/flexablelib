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
