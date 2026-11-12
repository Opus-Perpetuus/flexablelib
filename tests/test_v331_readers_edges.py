"""Reader edge cases: merges in spreadsheets and HTML, ragged Markdown."""

import pytest

from flexablelib import Table


def _spans(table):
    return sorted((r.first_row, r.first_column, r.last_row, r.last_column)
                  for r in table.merged_regions)


# -- Excel -------------------------------------------------------------------

@pytest.fixture
def merged_workbook(tmp_path):
    openpyxl = pytest.importorskip('openpyxl')
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in (['A', 'B', 'C'], [1, 2, 3], [4, 5, 6], [7, None, 9]):
        sheet.append(row)
    sheet.merge_cells('A1:B1')   # header only: not a body merge
    sheet.merge_cells('A2:A3')   # down two body rows
    sheet.merge_cells('B4:C4')   # across the last row
    path = tmp_path / 'merged.xlsx'
    workbook.save(str(path))
    return str(path)


def test_from_excel_keeps_body_merges_and_skips_header_ones(merged_workbook):
    table = Table.from_excel(merged_workbook)
    assert table.row_count == 3
    assert _spans(table) == [(0, 0, 1, 0), (2, 1, 2, 2)]
    assert table.rows[0] == [1, 2, 3]


def test_from_excel_without_header_shifts_merges(merged_workbook):
    table = Table.from_excel(merged_workbook, has_header=False)
    assert table.headers == ['column 1', 'column 2', 'column 3']
    assert table.rows[0] == ['A', '', 'C']
    assert _spans(table) == [(0, 0, 0, 1), (1, 0, 2, 0), (3, 1, 3, 2)]


def test_from_excel_empty_sheet(tmp_path):
    openpyxl = pytest.importorskip('openpyxl')
    path = tmp_path / 'empty.xlsx'
    openpyxl.Workbook().save(str(path))
    table = Table.from_excel(str(path))
    assert table.headers == [] and table.rows == []


def test_from_excel_round_trips_merges(tmp_path):
    pytest.importorskip('openpyxl')
    source = Table(rows=[['a', 'b'], ['c', 'd'], ['e', 'f']],
                   headers=['x', 'y'])
    source.merge_cells(0, 0, 1, 0)
    source.merge_cells(2, 0, 2, 1)
    path = str(tmp_path / 'out.xlsx')
    source.to_excel(path)
    assert _spans(Table.from_excel(path)) == _spans(source)


# -- HTML --------------------------------------------------------------------

def test_from_html_spans_become_merges_except_in_the_header():
    markup = ('<table><tr><th colspan=2>H</th></tr>'
              '<tr><td rowspan=2>x</td><td>1</td></tr><tr><td>2</td></tr>'
              '<tr><td colspan=3>w</td></tr></table>')
    table = Table.from_html(markup)
    assert table.headers[0] == 'H'
    assert table.rows[0][:2] == ['x', 1]
    assert _spans(table) == [(0, 0, 1, 0), (2, 0, 2, 2)]


def test_from_html_round_trips_merges():
    source = Table(rows=[['a', 'b'], ['c', 'd']], headers=['x', 'y'])
    source.merge_cells(0, 0, 1, 0)
    assert _spans(Table.from_html(source.to_html())) == [(0, 0, 1, 0)]


# -- Markdown ----------------------------------------------------------------

def test_from_markdown_pads_and_cuts_ragged_rows():
    table = Table.from_markdown(
        '| a | b |\n|:-:|--:|\n| 1 |\n| 1 | 2 | 3 |\n')
    assert table.headers == ['a', 'b']
    assert table.rows == [[1, ''], [1, 2]]
    assert table.col_alignment == ['c', 'r']


def test_from_markdown_without_separator_row_keeps_every_row():
    table = Table.from_markdown('| a | b |\n| 1 | 2 |\n')
    assert table.headers == ['a', 'b']
    assert table.rows == [[1, 2]]


def test_from_markdown_empty_text():
    table = Table.from_markdown('')
    assert table.headers == [] and table.rows == []
