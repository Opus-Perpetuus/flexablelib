"""2.2.0: exports follow sort_by, row_filter, hide_columns and the formats."""
import csv
import io
import json
import re

import pytest

from flexablelib import Table


def _table():
    t = Table(
        rows=[['api', 99.982, 1200], ['auth', 98.75, 35000],
              ['db', None, 7], ['cache', 97.1, 15]],
        headers=['svc', 'up', 'reqs'],
    )
    t.sort_by = 'up'
    t.sort_reverse = True
    t.row_filter = lambda row: row[2] > 10
    t.float_format = '.1f'
    t.int_format = ',d'
    return t


EXPECTED = [['api', '100.0', '1,200'], ['auth', '98.8', '35,000'],
            ['cache', '97.1', '15']]


def _md_rows(text):
    lines = text.splitlines()[2:]
    return [[c.strip() for c in line.strip('|').split('|')] for line in lines]


def test_csv_follows_display():
    rows = list(csv.reader(io.StringIO(_table().to_csv())))
    assert rows[0] == ['svc', 'up', 'reqs']
    assert rows[1:] == EXPECTED


def test_markdown_follows_display():
    assert _md_rows(_table().to_markdown()) == EXPECTED


def test_markdown_numeric_alignment_uses_stored_numbers():
    rule = _table().to_markdown().splitlines()[1]
    assert rule.split('|')[3].strip().endswith(':')  # '1,200' still numeric


def test_rst_asciidoc_latex_follow_display():
    t = _table()
    rst = t.to_rst()
    assert rst.index('api') < rst.index('auth') < rst.index('cache')
    assert '35,000' in rst and 'db' not in rst and '99.982' not in rst
    adoc = t.to_asciidoc().splitlines()
    assert adoc[2:5] == ['| api | 100.0 | 1,200', '| auth | 98.8 | 35,000',
                         '| cache | 97.1 | 15']
    latex = t.to_latex()
    assert 'api & 100.0 & 1,200' in latex and 'db' not in latex
    assert r'\begin{tabular}{lrr}' in latex


def test_html_follows_display_and_sorts_on_numbers():
    html = _table().to_html()
    data = json.loads(re.search(r'var DATA = (.*);', html).group(1))
    assert data['rows'] == EXPECTED
    assert data['numeric'] == [False, True, True]
    assert data['keys'][1] == [None, 98.75, 35000]


def test_simple_html_follows_display():
    html = _table()._repr_html_()
    assert html.index('api') < html.index('auth') < html.index('cache')
    assert '35,000' in html and '>db<' not in html


def test_records_raw_in_display_order():
    assert _table().to_records() == [
        {'svc': 'api', 'up': 99.982, 'reqs': 1200},
        {'svc': 'auth', 'up': 98.75, 'reqs': 35000},
        {'svc': 'cache', 'up': 97.1, 'reqs': 15},
    ]


def test_records_formatted():
    t = _table()
    t.row_filter = None
    records = t.to_records(formatted=True)
    assert [r['svc'] for r in records] == ['api', 'auth', 'cache', 'db']
    assert records[0] == {'svc': 'api', 'up': '100.0', 'reqs': '1,200'}
    assert records[-1]['up'] is None  # gaps stay None


def test_callable_sort_and_index_numbering():
    t = Table(rows=[['b', 2], ['a', 1], ['c', 3]], headers=['k', 'v'])
    t.sort_by = lambda row: -row[1]
    t.index_start = 1
    out = list(csv.reader(io.StringIO(t.to_csv(include_index=True))))
    assert [r[1] for r in out[1:]] == ['c', 'b', 'a']
    assert [r[0] for r in out[1:]] == ['1', '2', '3']


def test_roman_index_after_filter():
    t = Table(rows=[['a', 1], ['b', 2], ['c', 3]], headers=['k', 'v'])
    t.row_filter = lambda row: row[1] != 2
    t.index_start = 1
    t.roman_index = True
    assert [r['i'] if 'i' in r else list(r.values())[0]
            for r in t.to_records(include_index=True)] == ['I', 'II']


def test_hide_columns_left_out():
    t = _table()
    t.hide_columns = ['reqs']
    assert _md_rows(t.to_markdown()) == [r[:2] for r in EXPECTED]
    assert list(t.to_records()[0]) == ['svc', 'up']


def test_custom_format_and_strip_cells():
    t = Table(rows=[['  x  ', 0.5]], headers=['s', 'p'])
    t.strip_cells = True
    t.custom_format = {'p': '{:.0%}'}
    assert list(csv.reader(io.StringIO(t.to_csv())))[1] == ['x', '50%']


def test_gaps_are_empty_not_missing_value():
    t = Table(rows=[['a', None], ['b', 2]], headers=['k', 'v'])
    t.missing_value = '-'
    assert list(csv.reader(io.StringIO(t.to_csv())))[1] == ['a', '']
    assert t.to_records()[0]['v'] is None


def test_empty_rows_dropped_when_hidden():
    t = Table(rows=[['a', 1], [None, None], ['b', 2]], headers=['k', 'v'])
    assert len(t.to_records()) == 3
    t.show_empty_rows = False
    assert [r['k'] for r in t.to_records()] == ['a', 'b']


def test_rows_property_stays_raw_and_stored():
    t = _table()
    assert [r[0] for r in t.rows] == ['api', 'auth', 'db', 'cache']
    assert t.rows[0][1] == 99.982


def test_footer_rows_stay_last_without_sort():
    t = Table(rows=[['a', 2], ['b', 1], ['Total', 3]], headers=['k', 'v'])
    t.footer_rows = 1
    assert [r['k'] for r in t.to_records()] == ['a', 'b', 'Total']


def test_merges_follow_hidden_columns_and_filter():
    t = Table(rows=[['a', 'x', 1], ['b', 'y', 2], ['c', 'z', 3]],
              headers=['k', 'h', 'v'])
    t.merge_cells(0, 0, 0, 1, value='AB')
    t.hide_columns = ['h']
    html = t._repr_html_()
    assert 'AB' in html and 'colspan' not in html
    t.hide_columns = None
    t.row_filter = lambda row: row[0] != 'a'
    # Merges sit on display positions, as in compose(): after the filter
    # the first shown row ('b') carries it.
    html = t._repr_html_()
    assert 'colspan="2"' in html and '>AB<' in html and '>y<' not in html
    assert 'AB' in t.compose()


def test_merge_keeps_display_position():
    t = Table(rows=[['a', 1], ['b', 2], ['c', 3]], headers=['k', 'v'])
    t.merge_cells(0, 0, 1, 0, value='top')
    t.sort_by = 'v'
    t.sort_reverse = True
    html = t._repr_html_()
    assert 'rowspan="2"' in html and 'top' in html


def test_excel_numbers_and_number_formats(tmp_path):
    openpyxl = pytest.importorskip('openpyxl')
    t = _table()
    path = tmp_path / 'out.xlsx'
    t.to_excel(str(path))
    ws = openpyxl.load_workbook(str(path)).active
    values = [[c.value for c in row] for row in ws.iter_rows()]
    assert values == [['svc', 'up', 'reqs'], ['api', 99.982, 1200],
                      ['auth', 98.75, 35000], ['cache', 97.1, 15]]
    assert ws['B2'].number_format == '0.0'
    assert ws['C3'].number_format == '#,##0'


@pytest.mark.parametrize('spec,is_int,expected', [
    (',d', True, '#,##0'),
    ('.2f', False, '0.00'),
    (',.2f', False, '#,##0.00'),
    ('.1%', False, '0.0%'),
    ('.3e', False, '0.000E+00'),
    ('{:,.0f}', False, '#,##0'),
    ('$ {:,.2f} MXN', False, '"$ "#,##0.00" MXN"'),
    ('>10', False, None),
    ('d', False, None),
])
def test_excel_spec_translation(spec, is_int, expected):
    from flexablelib.writers import _excel_from_spec
    assert _excel_from_spec(spec, is_int) == expected


def test_excel_leading_zeros_and_text_cells(tmp_path):
    openpyxl = pytest.importorskip('openpyxl')
    t = Table(rows=[[7, True, 'x']], headers=['n', 'b', 's'])
    t.leading_zeros = 3
    t.custom_format = {'s': lambda v: v.upper()}
    path = tmp_path / 'z.xlsx'
    t.to_excel(str(path))
    ws = openpyxl.load_workbook(str(path)).active
    assert ws['A2'].value == 7 and ws['A2'].number_format == '000'
    assert ws['B2'].value == 'True' and ws['C2'].value == 'X'


def test_round_trips_without_formats():
    t = Table(rows=[['a', 1, 2.5], ['b', 2, 0.5]], headers=['k', 'n', 'f'])
    assert Table.from_csv(io.StringIO(t.to_csv())).rows == t.rows
    assert Table.from_markdown(t.to_markdown()).rows == t.rows
    assert Table.from_html(t._repr_html_()).rows == t.rows
    assert Table.from_records(t.to_records()).rows == t.rows


def test_round_trip_reads_what_was_shown():
    t = _table()
    back = Table.from_markdown(t.to_markdown())
    assert [r[0] for r in back.rows] == ['api', 'auth', 'cache']
    assert back.rows[0][1] == 100.0
