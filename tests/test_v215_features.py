"""Features shipped in 2.0.15 (stream, hide_columns, themes, sort callable)."""
import re
import pytest
from flexablelib.table import Table


def bare(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def test_stream_yields_lines_and_leaves_table_untouched():
    t = Table(headers=['Num', 'Sq'], style_name='rounded')
    lines = list(t.stream(([i, i * i] for i in range(4))))
    out = '\n'.join(lines)
    assert 'Num' in out and 'Sq' in out
    assert '│   3 │  9 │' in bare(out) or '3' in bare(out)
    assert t.row_count == 0
    # Full streamed body appears between header and bottom.
    assert bare(out).count('│') >= 4


def test_stream_append_keeps_rows():
    t = Table(headers=['A', 'B'], style_name='sharp')
    list(t.stream(([1, 2], [3, 4]), append=True))
    assert t.row_count == 2
    assert t.columns['A'] == [1, 3]


def test_stream_requires_headers():
    t = Table()
    with pytest.raises(ValueError, match='headers'):
        list(t.stream([[1]]))


def test_stream_with_existing_rows_and_pretty_grid_separators():
    t = Table.from_records([[0, 0]], headers=['A', 'B'], style_name='pretty_grid')
    # Widths freeze from seed content; set floors so later rows are not
    # truncated (beautifultable stream contract).
    t.column_min_width = [4, 4]
    lines = list(t.stream(([1, 10], [2, 20])))
    joined = '\n'.join(lines)
    # Inter-row rules present in pretty_grid.
    assert '├' in joined or '+' in joined
    assert '0' in joined and '20' in joined
    assert t.row_count == 1  # append=False


def test_hide_columns_by_name_and_index():
    t = Table.from_records(
        [[1, 2, 3], [4, 5, 6]],
        headers=['A', 'B', 'C'],
        style_name='sharp',
    )
    t.hide_columns = 'B'
    out = bare(t.compose())
    assert 'B' not in out
    assert '2' not in out and '5' not in out
    assert 'A' in out and 'C' in out
    t.hide_columns = [0, 2]
    out2 = bare(t.compose())
    assert 'B' in out2
    assert 'A' not in out2 and 'C' not in out2


def test_hide_columns_bad_key():
    t = Table.from_records([[1]], headers=['A'])
    with pytest.raises(ValueError):
        t.hide_columns = 'nope'
        t.compose()


def test_apply_theme_and_unknown():
    t = Table.from_records([[1, 2]], headers=['X', 'Y'])
    t.apply_theme('markdown')
    assert t.style_name == 'markdown'
    assert t.use_colors is False
    t.apply_theme('matrix')
    assert t.style_name == 'ascii'
    assert t.header_color == 'bold green'
    with pytest.raises(ValueError, match='unknown theme'):
        t.apply_theme('neon-disco')


def test_sort_by_callable():
    t = Table.from_records(
        [['z', 1], ['a', 2], ['m', 3]],
        headers=['N', 'V'],
        style_name='simple',
    )
    t.sort_by = lambda row: row[0]
    out = bare(t.compose())
    # 'a' row should appear before 'm' before 'z'
    pos_a = out.find('a')
    pos_m = out.find('m')
    pos_z = out.find('z')
    assert pos_a < pos_m < pos_z


def test_themes_catalog_nonempty():
    assert 'dark' in Table.THEMES
    assert 'ocean' in Table.THEMES
