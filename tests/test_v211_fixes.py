"""2.1.1: paginate/stream keep the parent's look; color_rule after sort; index_title."""
import io
import os

import pytest

from flexablelib import Table


ROWS = [[3, 'c', 1.5], [1, 'a', 2.25], [None, None, None], [2, 'b', 10.0]]


def _table():
    return Table(rows=[list(r) for r in ROWS], headers=['n', 's', 'f'])


def _colour(table):
    table.use_colors = True
    return table


SETTINGS = {
    'float_format': lambda t: setattr(t, 'float_format', '.1f'),
    'int_format': lambda t: setattr(t, 'int_format', '{:>4}'),
    'custom_format': lambda t: setattr(t, 'custom_format', {'s': lambda v: str(v).upper()}),
    'leading_zeros': lambda t: setattr(t, 'leading_zeros', 3),
    'str_align': lambda t: setattr(t, 'str_align', 'r'),
    'show_index': lambda t: setattr(t, 'show_index', True),
    'index_title': lambda t: (setattr(t, 'show_index', True),
                              setattr(t, 'index_title', '#')),
    'missing_value': lambda t: setattr(t, 'missing_value', '-'),
    'hide_empty_rows': lambda t: setattr(t, 'show_empty_rows', False),
    'column_colors': lambda t: setattr(_colour(t), 'column_colors', {'s': 'green'}),
    'row_colors': lambda t: setattr(_colour(t), 'row_colors', {1: 'red'}),
    'cell_colors': lambda t: setattr(_colour(t), 'cell_colors', {(1, 's'): 'blue'}),
    'color_rule': lambda t: setattr(
        _colour(t), 'color_rule', lambda v, r, c: 'red' if v == 'a' else None),
    'zebra': lambda t: setattr(_colour(t), 'zebra', 'dim'),
    'footer': lambda t: (setattr(_colour(t), 'footer_rows', 1),
                         setattr(t, 'footer_color', 'bold')),
    'divider': lambda t: t.add_divider(0),
    'merge': lambda t: t.merge_cells(0, 0, 0, 1),
    'border_text': lambda t: t.border_text('T', where='top'),
    'row_filter': lambda t: setattr(t, 'row_filter', lambda r: r[0] != 1),
}


@pytest.mark.parametrize('name', sorted(SETTINGS))
def test_single_page_equals_the_table(name):
    table = _table()
    SETTINGS[name](table)
    assert table.paginate(100) == [table.compose()]


@pytest.mark.parametrize('name', sorted(SETTINGS))
def test_stream_of_nothing_equals_the_table(name):
    table = _table()
    SETTINGS[name](table)
    assert '\n'.join(table.stream([])) == table.compose()


def test_single_page_equals_the_table_when_sorted():
    table = _table()
    table.sort_by = 'n'
    assert table.paginate(100) == [table.compose()]


def test_pages_keep_text_that_looks_like_a_number():
    table = Table(rows=[['007', '1e3']], headers=['zip', 'code'])
    for out in (table.paginate()[0], '\n'.join(table.stream([]))):
        assert '007' in out and '1e3' in out
        assert '1000.0' not in out


def test_pages_follow_sort_and_filter():
    table = Table(rows=[[5], [1], [4], [2], [3]], headers=['n'])
    table.sort_by = 'n'
    table.row_filter = lambda row: row[0] != 4
    pages = table.paginate(2)
    assert len(pages) == 2
    assert '| 1 |' in pages[0] and '| 2 |' in pages[0]
    assert '| 3 |' in pages[1] and '| 5 |' in pages[1]
    assert '4' not in pages[1].split('+===+')[1]


def test_pages_skip_hidden_empty_rows():
    table = Table(rows=[['a'], [None], ['b'], ['c']], headers=['x'])
    table.show_empty_rows = False
    pages = table.paginate(2)
    assert len(pages) == 2
    assert 'a' in pages[0] and 'b' in pages[0]
    assert 'c' in pages[1]
    assert 'None' not in ''.join(pages)


def test_index_keeps_counting_across_pages():
    table = Table(rows=[[c] for c in 'abcde'], headers=['x'])
    table.show_index = True
    table.index_start = 1
    pages = table.paginate(2)
    assert '| 3 | c |' in pages[1]
    assert '| 5 | e |' in pages[2]


def test_row_keyed_colours_follow_their_rows():
    table = _colour(Table(rows=[[c] for c in 'abcd'], headers=['x']))
    table.row_colors = {2: 'red'}
    table.cell_colors = {(3, 'x'): 'blue'}
    first, second = table.paginate(2)
    assert '\x1b[' not in first
    assert '\x1b[31m c ' in second
    assert '\x1b[34m d ' in second


def test_color_rule_sees_parent_row_numbers():
    seen = []
    table = _colour(Table(rows=[[c] for c in 'abcd'], headers=['x']))
    table.color_rule = lambda v, r, c: seen.append((v, r))
    table.paginate(2)
    assert ('c', 2) in seen and ('d', 3) in seen


def test_zebra_parity_continues_on_odd_page_breaks():
    table = _colour(Table(rows=[[c] for c in 'abcd'], headers=['x']))
    table.zebra = 'dim'
    pages = table.paginate(3)
    # Row 'b' (1) is striped on page one, row 'd' (3) on page two.
    assert '\x1b[2m b ' in pages[0]
    assert '\x1b[2m d ' in pages[1]


def test_footer_band_only_on_the_last_rows():
    table = _colour(Table(rows=[[c] for c in 'abcd'], headers=['x']))
    table.footer_rows = 1
    table.footer_color = 'bold'
    first, second = table.paginate(2)
    assert '\x1b[1m' not in first
    assert '\x1b[1m d ' in second
    assert '\x1b[1m c ' not in second


def test_merges_and_dividers_follow_their_rows():
    table = Table(rows=[[i, 'x'] for i in range(4)], headers=['a', 'b'])
    table.merge_cells(2, 0, 3, 0, value='M')   # inside page two
    table.merge_cells(1, 1, 2, 1, value='S')   # split by the break: dropped
    table.add_divider(2)
    first, second = table.paginate(2)
    assert 'S' not in first and 'S' not in second
    assert 'M' in second
    assert len(table.paginate(2)[1].splitlines()) > len(first.splitlines())


def test_color_rule_gets_the_displayed_value_after_sort():
    seen = []
    table = _colour(Table(rows=[['c'], ['a'], ['b']], headers=['x']))
    table.sort_by = 'x'
    table.color_rule = lambda v, r, c: seen.append((r, v))
    table.compose()
    assert sorted(set(seen)) == [(0, 'a'), (1, 'b'), (2, 'c')]


def test_color_rule_gets_the_displayed_value_after_filter():
    table = _colour(Table(rows=[['a', 1], ['b', 2], ['c', 3]], headers=['x', 'n']))
    table.row_filter = lambda row: row[0] != 'a'
    table.color_rule = lambda v, r, c: 'red' if c == 'n' and v == 2 else None
    out = table.compose()
    assert '\x1b[31m 2 ' in out
    assert '\x1b[31m 3 ' not in out


def test_index_title_keeps_column_alignment():
    table = Table(rows=[[1, 'xx', 1.25], [22, 'y', 10.5]], headers=['n', 's', 'f'])
    table.show_index = True
    before = table.compose().splitlines()[3:]
    table.index_title = '#'
    after = table.compose().splitlines()[3:]
    assert [line.replace('#', 'i') for line in after] == before
    table.index_title = 'i'
    assert table.compose().splitlines()[3:] == before


def test_setting_the_same_index_title_changes_nothing():
    table = _table()
    table.show_index = True
    before = table.compose()
    table.index_title = table.index_title
    assert table.compose() == before


# Uncovered public paths ---------------------------------------------------

def test_stream_honours_column_max_width():
    table = Table(rows=[['aaaaaaaaaaaa', 1]], headers=['h', 'k'])
    table.column_max_width = 4
    lines = list(table.stream([['bbbbbbbbbb', 2]]))
    assert len({len(line) for line in lines if line.startswith('|')}) == 1
    assert any('b...' in line for line in lines)


def test_paginate_of_empty_table_is_one_page():
    table = Table(headers=['a'])
    assert table.paginate(3) == [table.compose()]


def test_row_colors_from_a_sequence_and_none():
    table = Table(rows=[[1], [2]], headers=['a'])
    table.row_colors = ['red', 'green']
    assert table.row_colors == {0: 'red', 1: 'green'}
    table.row_colors = None
    assert table.row_colors == {}


def test_cell_colors_validation():
    table = Table(rows=[[1]], headers=['a'])
    table.cell_colors = {(0, 'a'): 'red'}
    assert table.cell_colors == {(0, 'a'): 'red'}
    table.cell_colors = None
    assert table.cell_colors == {}
    with pytest.raises(TypeError):
        table.cell_colors = {0: 'red'}


def test_leading_zeros_none_and_negative():
    table = Table(rows=[[7]], headers=['a'])
    table.leading_zeros = 3
    assert '007' in table.compose()
    table.leading_zeros = None
    assert table.leading_zeros is None
    assert '007' not in table.compose()
    with pytest.raises(ValueError):
        table.leading_zeros = -1


def test_vrules_true_and_invalid():
    table = Table(rows=[[1]], headers=['a'])
    table.vrules = True
    assert table.vrules == 'all'
    with pytest.raises(ValueError):
        table.vrules = 'bogus'


def test_add_divider_defaults_and_validation():
    Table().add_divider()   # no rows: nothing to divide, no error
    table = Table(rows=[[1], [2], [3]], headers=['a'])
    table.style_name = 'grid_eheader'
    with pytest.raises(ValueError):
        table.add_divider(-1)
    table.add_divider()
    plain = Table(rows=[[1], [2], [3]], headers=['a'])
    assert table.compose() == plain.compose()


def test_empty_columns_i_ignores_the_index_column():
    table = Table(rows=[[1, None], [2, None]], headers=['a', 'b'])
    plain = table.empty_columns_i
    table.show_index = True
    assert table.empty_columns_i == plain


def test_columns_dict_skips_non_iterables():
    table = Table(columns={'x': [1, 2], 'y': 5})
    assert table.headers == ['x']
    assert table.rows == [[1], [2]]


def test_from_markdown_file_objects_and_odd_input():
    text = '| a | b |\n|---|---|\n| 1 | é |\n'
    assert Table.from_markdown(io.StringIO(text)).rows == [[1, 'é']]
    assert Table.from_markdown(io.BytesIO(text.encode('utf-8'))).rows == [[1, 'é']]
    titled = Table.from_markdown('Report\n' + text)
    assert titled.headers == ['a', 'b']
    empty = Table.from_markdown('no table here\n')
    assert empty.headers == [] and empty.rows == []
    no_sep = Table.from_markdown('| a | b |\n| 1 | 2 |\n')
    assert no_sep.headers == ['a', 'b'] and no_sep.rows == [[1, 2]]


def test_from_html_file_object_and_empty_table():
    markup = '<table><tr><th>a</th></tr><tr><td>1</td></tr></table>'
    table = Table.from_html(io.StringIO(markup))
    assert table.headers == ['a'] and table.rows == [[1]]
    empty = Table.from_html('<table></table>')
    assert empty.headers == [] and empty.rows == []


def test_from_csv_path(tmp_path):
    path = tmp_path / 'data.csv'
    path.write_text('a,b\n1,中文\n', encoding='utf-8')
    for source in (str(path), path):
        table = Table.from_csv(source)
        assert table.headers == ['a', 'b']
        assert table.rows == [[1, '中文']]


def test_from_records_with_nothing():
    assert Table.from_records([]).headers == []


def test_exports_of_a_table_without_headers():
    assert Table().to_markdown() == ''
    assert Table().to_rst() == ''
