"""Every rendered line has the same terminal width, in every style.

Regression for ``borderless_compact_header_gap``: its header separator line was one column short
because it had no junction between columns.  Also pins that wide (CJK /
emoji) headers and ``column_max_width`` keep all lines aligned.  Note that
``*_eheader`` styles intentionally draw the header row without column
separators (documented design, not a bug).
"""
import pytest

from flexablelib import Table
from flexablelib.style_compositions import __style_compositions as catalogue
from flexablelib.text_width import visible_width

CASES = [
    (['名前', 'n'], [['日本語テキスト', 1.25], ['😀😀', -3]], {'名前': 4}),
    (['名前', 'n'], [['日本語テキスト', 1.25], ['😀😀', -3]], None),
    (['x', 'yy'], [['abc', 1], ['d', 2]], None),
    (['東京', '😀値'], [['東京タワー展望台', 'x'], ['a', '👍 ok']], 3),
]


@pytest.mark.parametrize('style', catalogue._fields)
@pytest.mark.parametrize('headers,rows,max_width', CASES)
def test_all_lines_same_width(style, headers, rows, max_width):
    table = Table(rows=rows, headers=headers)
    table.style_name = style
    if max_width is not None:
        table.column_max_width = max_width
    lines = table.compose().split('\n')
    widths = {visible_width(line) for line in lines}
    assert len(widths) == 1, (style, [visible_width(l) for l in lines])


def test_plain_header_separator_spans_table():
    table = Table(rows=[['abc', 1], ['d', 2]], headers=['x', 'yy'])
    table.style_name = 'borderless_compact_header_gap'
    lines = table.compose().split('\n')
    assert lines[1] == ' ' * len(lines[0])


def test_eheader_header_row_has_no_column_separator_by_design():
    table = Table(rows=[['a', 'b']], headers=['x', 'y'])
    table.style_name = 'ascii_double_underline_open_header'
    assert table.compose().split('\n')[:3] == [
        '+-------+', '| x   y |', '+===+===+']
