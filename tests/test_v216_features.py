"""Features shipped in 2.0.16 (index polish, rules, CSV dialect, themes…)."""
import csv
import io
import re

import pytest

from flexablelib.table import Table
from flexablelib.utils import to_roman


def bare(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def test_to_roman_helper():
    assert to_roman(1) == 'I'
    assert to_roman(4) == 'IV'
    assert to_roman(9) == 'IX'
    assert to_roman(2026) == 'MMXXVI'
    assert to_roman(0) == '0'
    assert to_roman(-3) == '-3'


def test_index_title_and_roman_index():
    t = Table.from_records(
        [['a', 1], ['b', 2]],
        headers=['N', 'V'],
        style_name='sharp',
    )
    t.show_index = True
    t.index_title = '#'
    t.roman_index = True
    t.index_start = 1
    out = bare(t.compose())
    assert '#' in out
    assert '│   I │' in out or 'I' in out
    assert 'II' in out
    # stored headers unchanged
    assert t.headers == ['N', 'V']


def test_number_columns_and_strip_cells():
    t = Table.from_records(
        [['  x  ', ' y '], ['z', 'w']],
        headers=['Name', 'Val'],
        style_name='sharp',
    )
    t.number_columns = True
    t.strip_cells = True
    out = bare(t.compose())
    assert 'Name' not in out and 'Val' not in out
    assert '│ 1 │' in out or '| 1 |' in out or ' 1 ' in out
    assert 'x' in out and '  x  ' not in out


def test_suppress_empty():
    t = Table.from_records(
        [['a', 1], ['', ''], ['b', 2]],
        headers=['N', 'V'],
        style_name='simple',
    )
    t.suppress_empty = True
    assert t.show_empty_rows is False
    assert t.show_empty_columns is False
    out = bare(t.compose())
    # three data lines would include blank; suppressed leaves two body rows
    assert out.count('\n') >= 2
    assert 'a' in out and 'b' in out


def test_hrules_and_vrules():
    t = Table.from_records([[1, 2]], headers=['A', 'B'], style_name='pretty_grid')
    t.hrules = 'none'
    out = bare(t.compose())
    # no horizontal box lines
    assert '═' not in out and '─' not in out
    t.hrules = 'all'
    t.vrules = 'none'
    out2 = bare(t.compose())
    assert '│' not in out2
    t.vrules = 'frame'
    out3 = bare(t.compose())
    assert '│' in out3
    with pytest.raises(ValueError):
        t.hrules = 'diagonal'


def test_divide_every_and_add_dividers():
    t = Table.from_records(
        [[i, i] for i in range(6)],
        headers=['a', 'b'],
        style_name='presto',
    )
    t.divide_every(2)
    out = bare(t.compose())
    # presto body separators are dashes
    assert out.count('----') >= 2 or out.count('-') > 10
    t.clear_dividers()
    t.add_dividers(0, 3)
    assert 0 in t._Table__dividers and 3 in t._Table__dividers


def test_fit_terminal_and_aliases():
    t = Table.from_records([[1]], headers=['A'])
    t.fit_terminal(margin=5)
    assert t.max_width is not None and t.max_width >= 1
    t.max_table_width = 40
    assert t.max_width == 40
    t.justify = 'c'
    assert t.table_align in ('c', 'tc')


def test_csv_dialect_roundtrip():
    raw = 'a;b\n"1;x";2\n'
    t = Table.from_csv(
        io.StringIO(raw),
        delimiter=';',
        quotechar='"',
        parse_numbers=False,
    )
    assert t.headers == ['a', 'b']
    assert t.columns['a'] == ['1;x']
    dumped = t.to_csv(quoting=csv.QUOTE_ALL, quotechar="'")
    assert "'a'" in dumped and "'1;x'" in dumped


def test_themes_expanded():
    for name in (
        'solarized', 'neon', 'mono', 'autumn', 'contrast',
        'forest', 'ember', 'slate',
    ):
        assert name in Table.THEMES
    t = Table.from_records([[1]], headers=['x'])
    t.apply_theme('forest')
    assert t.header_color == 'bold #87d787'


def test_paginate_freeze_header_and_page_label():
    t = Table.from_records(
        [[i, i] for i in range(4)],
        headers=['A', 'B'],
        style_name='rounded',
    )
    pages = t.paginate(2, freeze_header=True, page_label=True)
    assert len(pages) == 2
    assert 'page 1/2' in bare(pages[0])
    assert 'page 2/2' in bare(pages[1])
    assert 'A' in bare(pages[1])
    pages2 = t.paginate(2, freeze_header=False)
    assert 'A' in bare(pages2[0])
    # second page should not repeat header label row
    body = bare(pages2[1])
    # title absent; header cells A/B should be gone
    assert '│ A │' not in body and '| A |' not in body
