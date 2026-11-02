"""Fixes and coverage added after 2.0.19."""
import io

import pytest

from flexablelib import Table


def _table():
    return Table.from_records([['hello', 1]], headers=['a', 'b'])


@pytest.mark.parametrize('attr', ['column_min_width', 'column_max_width'])
@pytest.mark.parametrize('value', ['abc', [3, 'x'], {'a': object()}])
def test_width_bounds_reject_non_integers_when_set(attr, value):
    table = _table()
    with pytest.raises(ValueError, match=attr):
        setattr(table, attr, value)


@pytest.mark.parametrize('value', [0, -1, [-1], {'a': -2}])
def test_column_max_width_rejects_caps_below_one(value):
    table = _table()
    with pytest.raises(ValueError, match='column_max_width'):
        table.column_max_width = value


def test_column_min_width_rejects_negative_and_allows_zero():
    table = _table()
    with pytest.raises(ValueError, match='column_min_width'):
        table.column_min_width = -1
    table.column_min_width = 0
    assert '| hello |' in str(table)


def test_rejected_width_bound_keeps_previous_value():
    table = _table()
    table.column_max_width = 3
    with pytest.raises(ValueError):
        table.column_max_width = -1
    assert table.column_max_width == 3


def test_width_bounds_accept_none_entries_and_numeric_strings():
    table = _table()
    table.column_max_width = [None, '4']
    table.column_min_width = {'a': None, 'b': 6}
    assert table.column_max_width == [None, 4]
    rendered = str(table)
    assert '| hello |' in rendered
    assert None is table.column_min_width['a']


def test_width_bounds_reset_with_none():
    table = _table()
    table.column_max_width = 2
    table.column_max_width = None
    assert '| hello |' in str(table)


HTML_ONE = '<table><tr><th>a</th></tr><tr><td>1</td></tr></table>'


@pytest.mark.parametrize('index', [1, -2])
def test_from_html_out_of_range_index_names_the_table_count(index):
    with pytest.raises(IndexError, match='document has 1'):
        Table.from_html(HTML_ONE, index=index)


def test_from_html_negative_index_reads_from_the_end():
    markup = HTML_ONE + '<table><tr><th>b</th></tr><tr><td>2</td></tr></table>'
    table = Table.from_html(markup, index=-1)
    assert table.headers == ['b']
    assert table.rows == [[2]]


def test_from_html_without_table_raises():
    with pytest.raises(ValueError, match='no <table>'):
        Table.from_html('<p>nothing</p>')


def test_from_html_reads_a_path(tmp_path):
    path = tmp_path / 'x.html'
    path.write_text(HTML_ONE, encoding='utf-8')
    assert Table.from_html(path).rows == [[1]]
    assert Table.from_html(str(path)).rows == [[1]]


def test_from_csv_without_header_pads_ragged_rows():
    table = Table.from_csv(io.StringIO('1\n1,2,3\n'), has_header=False)
    assert table.headers == ['column 1', 'column 2', 'column 3']
    assert table.rows == [[1, '', ''], [1, 2, 3]]


def test_from_csv_empty_source_gives_empty_table():
    table = Table.from_csv(io.StringIO(''))
    assert table.headers == []
    assert table.rows == []


def test_from_csv_dialect_with_delimiter_override():
    table = Table.from_csv(io.StringIO('a;b\n1;2\n'), dialect='excel',
                           delimiter=';')
    assert table.headers == ['a', 'b']
    assert table.rows == [[1, 2]]


def test_from_csv_keeps_text_that_only_looks_numeric():
    table = Table.from_csv(io.StringIO('a,b,c\n007,inf,1_000\n'))
    assert table.rows == [['007', 'inf', '1_000']]


def test_from_markdown_reads_bytes_and_paths(tmp_path):
    text = '| a | b |\n|:-:|--:|\n| 1 | 2 | 3 |\n| 4 |\n'
    path = tmp_path / 'x.md'
    path.write_text(text, encoding='utf-8')
    for source in (text.encode('utf-8'), path, str(path)):
        table = Table.from_markdown(source)
        assert table.headers == ['a', 'b']
        assert table.rows == [[1, 2], [4, '']]
        assert table.col_alignment == ['c', 'r']


def test_from_records_with_dicts_and_explicit_headers():
    table = Table.from_records([{'a': 1, 'b': 2}, {'a': 3}],
                               headers=['b', 'a'])
    assert table.rows == [[2, 1], ['', 3]]


def test_from_records_takes_headers_from_a_generator():
    table = Table.from_records(row for row in [['h'], [1]])
    assert table.headers == ['h']
    assert table.rows == [[1]]
