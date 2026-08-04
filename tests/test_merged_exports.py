"""
Merges, sentinels and the browser, on the way out of the table.

Everything here is about what leaves the table rather than what the console
draws. Three things used to stop at the terminal door:

1. A merge was painted onto the assembled console string, so no other format
   knew about it. A table that read as one merged cell in the terminal
   exported as separate cells everywhere else.

2. The two storage sentinels -- ``ValuePlacer`` for an absent cell and the
   shared ``IndexCounter`` for the index column -- were handed straight back
   by ``rows``, ``columns`` and their ``internal_`` variants, so printing them
   showed ``<prettyTables.utils.ValuePlacer object at 0x7f...>``.

3. There was no way to see the HTML page without writing a file and opening
   it yourself.
"""

import os

import pytest

from prettyTables import Table
from prettyTables.utils import IndexCounter, ValuePlacer


def merged_table(**options):
    """
    The reported case: two merges, a gap, and a column of numbers.

    ``Age`` is short one value and ``Name`` short two, so the table carries
    ``ValuePlacer`` sentinels as well as merges -- the two things this module
    is about meet in the same cells.
    """
    table = Table(**options)
    table.add_column('Name', ['John', 'Jane'])
    table.add_column('Age', [20])
    table.add_column('Height', [1.75, 1.60, 1.75])
    table.missing_value = '?'
    table.merge_cells(0, 0, last_row=1)
    table.merge_cells(1, 1, last_column=2, last_row=2, align='c')
    return table


# +-------------------------------------------------------------------------+
# The sentinels stay inside the table
# +-------------------------------------------------------------------------+

def test_rows_resolve_the_absent_cell_sentinel():
    table = merged_table()
    assert table.rows == [
        ['John', 20, 1.75],
        ['Jane', '?', 1.6],
        ['?', '?', 1.75],
    ]


def test_columns_resolve_the_absent_cell_sentinel():
    table = merged_table()
    assert table.columns['Age'] == [20, '?', '?']


def test_internal_rows_number_the_index_column():
    table = merged_table()
    table.show_index = True
    table.index_start = 10
    table.index_step = 5

    # The index header is equal only to itself -- see IndexColumnTitle -- so
    # it has to be looked up with the object the table is actually keyed by.
    index_header = table.internal_headers[0]

    assert [row[0] for row in table.internal_rows] == [10, 15, 20]
    assert table.internal_columns[index_header] == [10, 15, 20]


def test_no_accessor_hands_out_a_sentinel():
    table = merged_table()
    table.show_index = True

    exported = repr([
        table.rows, table.columns,
        table.internal_rows, table.internal_columns,
        table.to_records(), table.to_csv(), table.to_markdown(),
        table.to_html(), table._repr_html_(),
    ])

    assert 'ValuePlacer' not in exported
    assert 'IndexCounter' not in exported


def test_the_raw_views_still_carry_the_sentinel():
    """
    The sentinel is compared by identity, so telling a gap apart from a cell
    that genuinely holds the missing text needs a view that keeps it.
    """
    table = merged_table()

    assert table.raw_rows[1][1] is table.missing
    assert table.raw_columns['Age'][1] is table.missing

    table.show_index = True
    index_header = table.internal_headers[0]
    assert isinstance(table.raw_internal_rows[0][0], IndexCounter)
    assert isinstance(table.raw_internal_columns[index_header][0], IndexCounter)


def test_resolving_does_not_expose_the_table_s_own_storage():
    table = merged_table()

    table.rows[0][0] = 'mutated'
    table.columns['Name'][0] = 'mutated'

    assert table.rows[0][0] == 'John'


def test_the_sentinel_says_what_it_is_rather_than_where_it_lives():
    """
    One escaping is a bug in whatever let it out, but the old repr told the
    reader nothing and was wide enough to wreck any layout it landed in.
    """
    placer = ValuePlacer()

    assert repr(placer) == '<missing>'
    assert str(placer) == ''
    assert '0x' not in repr(placer)


# +-------------------------------------------------------------------------+
# Formats that can express a span
# +-------------------------------------------------------------------------+

def test_simple_html_spells_a_merge_as_rowspan_and_colspan():
    markup = merged_table()._repr_html_()

    assert '<td rowspan="2" style="text-align:center">John</td>' in markup
    assert '<td rowspan="2" colspan="2" style="text-align:center">?</td>' in markup


def test_a_merged_cell_is_emitted_once_not_once_per_cell_it_covers():
    markup = merged_table()._repr_html_()

    # Nine cells, of which the two merges cover four: one under the vertical
    # merge and three under the block. Five cells are left to write.
    assert markup.count('<td') == 5


def test_the_span_moves_with_the_index_column():
    """
    Merge coordinates ignore the index column even when it is displayed, so
    the writers have to shift them by one. Getting this wrong merges the
    wrong cells rather than failing loudly.
    """
    table = merged_table()
    table.show_index = True

    with_index = table.to_html(include_index=True)
    without = table.to_html(include_index=False)

    assert '"origins": [[0, 1, 2, 1, "center"], [1, 2, 2, 2, "center"]]' in with_index
    assert '"origins": [[0, 0, 2, 1, "center"], [1, 1, 2, 2, "center"]]' in without


def test_excel_writes_real_merged_cells():
    openpyxl = pytest.importorskip('openpyxl')

    table = merged_table()
    path = os.path.join(os.path.dirname(__file__), '_merged_test.xlsx')
    try:
        table.to_excel(path)
        sheet = openpyxl.load_workbook(path).active
        ranges = sorted(str(cell_range) for cell_range in sheet.merged_cells.ranges)
        values = [row for row in sheet.iter_rows(values_only=True)]
    finally:
        if os.path.exists(path):
            os.remove(path)

    # Row 1 is the header, so the body starts at row 2.
    assert ranges == ['A2:A3', 'B3:C4']
    assert values[1] == ('John', 20, 1.75)


def test_excel_shifts_its_ranges_for_the_index_column():
    openpyxl = pytest.importorskip('openpyxl')

    table = merged_table()
    table.show_index = True
    path = os.path.join(os.path.dirname(__file__), '_merged_index_test.xlsx')
    try:
        table.to_excel(path, include_index=True)
        sheet = openpyxl.load_workbook(path).active
        ranges = sorted(str(cell_range) for cell_range in sheet.merged_cells.ranges)
    finally:
        if os.path.exists(path):
            os.remove(path)

    assert ranges == ['B2:B3', 'C3:D4']


# +-------------------------------------------------------------------------+
# Formats that cannot
# +-------------------------------------------------------------------------+

def test_csv_puts_the_merged_text_in_the_top_left_field():
    lines = merged_table().to_csv().strip().splitlines()

    assert lines == ['Name,Age,Height', 'John,20,1.75', ',?,', '?,,']


def test_markdown_empties_the_cells_a_merge_covers():
    rows = merged_table().to_markdown().splitlines()

    assert rows[2].split('|')[1].strip() == 'John'
    assert rows[3].split('|')[1].strip() == ''
    assert rows[3].split('|')[2].strip() == '?'


def test_records_keep_every_key_so_the_rows_stay_the_same_shape():
    records = merged_table().to_records()

    assert [sorted(record) for record in records] == [['Age', 'Height', 'Name']] * 3
    assert records[1] == {'Name': '', 'Age': '?', 'Height': ''}


def test_a_merge_with_its_own_text_exports_that_text():
    table = Table()
    table.add_column('a', [1, 2])
    table.add_column('b', [3, 4])
    table.merge_cells(0, 0, last_column=1, value='Total')

    assert table.to_csv().splitlines()[1] == 'Total,'
    assert '<td colspan="2" style="text-align:center">Total</td>' in table._repr_html_()


def test_a_table_with_no_merges_exports_exactly_as_before():
    table = Table()
    table.add_column('a', [1, 2])
    table.add_column('b', [3, 4])

    assert table.to_csv().strip().splitlines() == ['a,b', '1,3', '2,4']
    assert '<td>1</td><td>3</td>' in table._repr_html_()
    assert '"origins": []' in table.to_html()


# +-------------------------------------------------------------------------+
# Opening a browser
# +-------------------------------------------------------------------------+

@pytest.fixture
def opened_urls(monkeypatch):
    """Record what would have been opened instead of opening it."""
    urls = []
    monkeypatch.setattr(
        'webbrowser.open_new_tab', lambda url: urls.append(url) or True
    )
    monkeypatch.setattr(
        'webbrowser.open', lambda url: urls.append(url) or True
    )
    return urls


def test_open_in_browser_writes_the_page_and_opens_it(opened_urls, tmp_path):
    table = merged_table()
    path = table.open_in_browser(path=str(tmp_path / 'report.html'), title='Q3')

    assert opened_urls == ['file://' + path]
    markup = open(path, encoding='utf-8').read()
    assert markup.startswith('<!DOCTYPE html>')
    assert '<title>Q3</title>' in markup
    assert '"origins": [[0, 0, 2, 1, "center"]' in markup


def test_open_in_browser_leaves_its_temporary_file_readable(opened_urls):
    """
    The browser is a separate process and may not have read the file by the
    time this returns, so deleting it here would race with that.
    """
    path = merged_table().open_in_browser()
    try:
        assert os.path.exists(path)
        assert path.endswith('.html')
    finally:
        os.remove(path)


def test_open_in_browser_escapes_a_path_the_browser_would_mangle(opened_urls,
                                                                 tmp_path):
    path = merged_table().open_in_browser(path=str(tmp_path / 'my table.html'))

    assert opened_urls == ['file://' + path.replace(' ', '%20')]


def test_open_in_browser_returns_the_path_it_wrote(opened_urls, tmp_path):
    target = str(tmp_path / 'a.html')

    assert merged_table().open_in_browser(path=target, new_tab=False) == target
    assert opened_urls == ['file://' + target]
