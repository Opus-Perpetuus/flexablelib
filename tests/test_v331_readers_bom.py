"""A UTF-8 byte-order mark is not part of the first header."""

from flexablelib import Table


def test_from_csv_text_with_bom():
    table = Table.from_csv('\ufeffName,Age\nAna,3\n')
    assert table.headers == ['Name', 'Age']
    assert table.rows == [['Ana', 3]]


def test_from_csv_file_saved_with_bom(tmp_path):
    path = tmp_path / 'excel.csv'
    path.write_text('Name,Age\nAna,3\n', encoding='utf-8-sig')
    assert Table.from_csv(str(path)).headers == ['Name', 'Age']
    # Without a header row the mark is not left on the first value either.
    assert Table.from_csv(str(path), has_header=False).rows[0] == [
        'Name', 'Age']


def test_from_csv_keeps_a_bom_that_is_not_leading():
    table = Table.from_csv('a,b\n\ufeffx,2\n')
    assert table.rows[0][0] == '\ufeffx'


def test_to_csv_utf8_sig_round_trips(tmp_path):
    path = tmp_path / 'out.csv'
    Table(rows=[['Ana', 3]], headers=['Name', 'Age']).to_csv(
        str(path), encoding='utf-8-sig')
    assert path.read_bytes().startswith(b'\xef\xbb\xbf')
    back = Table.from_csv(str(path))
    assert back.headers == ['Name', 'Age']
    assert back.rows == [['Ana', 3]]


def test_from_markdown_with_bom():
    table = Table.from_markdown('\ufeff| a | b |\n|---|---|\n| 1 | 2 |\n')
    assert table.headers == ['a', 'b']
    assert table.rows == [[1, 2]]


def test_from_markdown_file_with_bom(tmp_path):
    path = tmp_path / 't.md'
    path.write_text('| a | b |\n|---|---|\n| 1 | 2 |\n', encoding='utf-8-sig')
    assert Table.from_markdown(str(path)).headers == ['a', 'b']
