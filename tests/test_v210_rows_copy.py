"""2.1.0: ``Table.rows`` is a copy with ``None`` in the gaps; ``set_cell``."""
import pytest

from flexablelib import Table


def _table():
    table = Table(rows=[['api', 99.9], ['auth']], headers=['Service', 'Uptime'])
    table.add_row()
    table.add_column('Region', ['us', table.missing, 'eu'])
    return table


def test_rows_is_a_new_list_each_call():
    table = _table()
    first, second = table.rows, table.rows
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_mutating_rows_does_not_change_the_table():
    table = Table(rows=[['a', 1], ['b', 2]], headers=['k', 'v'])
    before = str(table)
    rows = table.rows
    rows[0][1] = 999
    rows.append(['c', 3])
    del rows[1]
    assert table.rows == [['a', 1], ['b', 2]]
    assert str(table) == before
    assert table.row_count == 2


def test_empty_and_missing_cells_are_none():
    table = _table()
    table.add_row(['x', table.missing, 'mx'])
    rows = table.rows
    assert rows[1] == ['auth', None, None]
    assert rows[2][:2] == [None, None]
    assert rows[3] == ['x', None, 'mx']
    assert 'ValuePlacer' not in repr(rows)


def test_rows_match_records_and_exports():
    table = _table()
    records = table.to_records()
    assert [list(r.values()) for r in records] == table.rows
    assert [list(r.keys()) for r in records][0] == table.headers
    csv_lines = table.to_csv().splitlines()[1:]
    expected = [','.join('' if v is None else str(v) for v in row)
                for row in table.rows]
    assert csv_lines == expected


def test_set_cell_updates_render_and_rows():
    table = Table(rows=[['api', 99.9], ['auth', 98.0]],
                  headers=['Service', 'Uptime'])
    table.set_cell(0, 'Uptime', 12.5)
    table.set_cell(-1, 0, 'login')
    assert table.rows == [['api', 12.5], ['login', 98.0]]
    assert table.columns['Uptime'] == [12.5, 98.0]
    out = str(table)
    assert '12.5' in out and 'login' in out and 'auth' not in out
    table.show_index = True
    assert 'login' in str(table)


def test_set_cell_missing_empties_cell():
    table = Table(rows=[[1, 2]], headers=['a', 'b'])
    table.set_cell(0, 'b', table.missing)
    assert table.rows == [[1, None]]
    assert table.to_records() == [{'a': 1, 'b': None}]


def test_set_cell_parses_numbers_when_enabled():
    table = Table(rows=[['x', 1]], headers=['k', 'v'])
    table.parse_str_numbers = True
    table.set_cell(0, 'v', '42')
    assert table.rows == [['x', 42]]


@pytest.mark.parametrize('row, column, error', [
    (5, 0, IndexError),
    (0, 9, IndexError),
    (0, 'nope', KeyError),
    (1.0, 0, TypeError),
    (True, 0, TypeError),
    (0, 1.5, TypeError),
])
def test_set_cell_rejects_bad_coordinates(row, column, error):
    table = Table(rows=[[1, 2]], headers=['a', 'b'])
    with pytest.raises(error):
        table.set_cell(row, column, 0)
    assert table.rows == [[1, 2]]
