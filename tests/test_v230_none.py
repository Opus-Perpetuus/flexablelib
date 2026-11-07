"""None is a missing cell, not the string 'None' (visible change in 2.3)."""
import pytest

from flexablelib import Table
from flexablelib.style_compositions import __style_compositions as catalogue
from flexablelib.text_width import visible_width


def make(style, missing, sentinel=False):
    t = Table(headers=['id', 'float', 'int', 'text'], style_name=style,
              missing_val=missing)
    gap = t.missing if sentinel else None
    for row in [['r0', 924.87, 31, '東京 😀'], ['r1', gap, gap, gap],
                ['r2', -1.25, 2, 'épsilon'], ['r3', gap, 107, 'tail']]:
        t.add_row(row)
    t.max_width = 1000
    return t


@pytest.mark.parametrize('style', catalogue._fields)
@pytest.mark.parametrize('missing', ['', '?', '欠測 😀'])
def test_none_matches_padding_sentinel_in_every_render_path(style, missing):
    a, b = make(style, missing), make(style, missing, sentinel=True)
    assert a.compose() == b.compose()
    assert str(a) == str(b)
    assert a.paginate(2) == b.paginate(2)
    assert a.paginate(2, freeze_header=False) == b.paginate(2, freeze_header=False)
    assert list(a.stream([])) == list(b.stream([]))
    assert a.transpose().compose() == b.transpose().compose()
    assert a.rows == b.rows
    assert a.to_records() == b.to_records()
    assert a.to_records(formatted=True) == b.to_records(formatted=True)
    assert a.to_csv() == b.to_csv()
    assert a.to_html() == b.to_html()
    assert a.to_markdown() == b.to_markdown()
    assert 'None' not in a.compose()


@pytest.mark.parametrize('missing', ['', '?', 'missing'])
@pytest.mark.parametrize('index', [False, True])
def test_none_preserves_numeric_alignment_and_decimal_axis_with_wrap(missing, index):
    t = make('ascii', missing)
    t.show_index = index
    t.overflow = 'wrap'
    t.column_max_width = 7
    out = t.compose()
    lines = out.splitlines()
    assert len({visible_width(line) for line in lines}) == 1
    # A missing cell must not turn numbers into text that wraps over lines.
    assert '924.87' in out
    assert '-1.25' in out
    assert '31 |' in out
    numeric = [line for line in lines if '924.87' in line or '-1.25' in line]
    assert numeric[0].index('.') == numeric[1].index('.')


@pytest.mark.parametrize('style', catalogue._fields)
def test_rows_roundtrip_keeps_blanks_and_column_types(style):
    t = Table(rows=[[2.75, 3], [None], [24.5, None]], style_name=style)
    assert Table(rows=t.rows, style_name=style).compose() == t.compose()
    t.missing_value = '?'
    copy = Table(rows=t.rows, headers=t.headers, style_name=style, missing_val='?')
    assert copy.compose() == t.compose()
    assert copy.rows == t.rows


def test_stream_incoming_none_matches_an_incoming_padding_sentinel():
    a = Table(headers=['n', 'i'], missing_val='?')
    b = Table(headers=['n', 'i'], missing_val='?')
    for t in (a, b):
        t.column_min_width = 12
        t.max_width = 100
    rows = [[2.75, 3], [None, None], [24.5, 22]]
    sentinel_rows = [[2.75, 3], [b.missing, b.missing], [24.5, 22]]
    assert list(a.stream(rows, append=True)) == list(b.stream(sentinel_rows, append=True))
    assert a.rows == rows
    assert a.compose() == b.compose()


def test_missing_value_is_dynamic_and_storage_stays_raw():
    t = Table(rows=[[None], [2.75]], headers=['n'])
    assert t.rows == [[None], [2.75]]
    assert 'None' not in t.compose()
    t.missing_value = '?'
    assert '?' in t.compose()
    assert t.rows == [[None], [2.75]]
    assert t.to_records() == [{'n': None}, {'n': 2.75}]
    assert t.to_records(formatted=True)[0] == {'n': None}
