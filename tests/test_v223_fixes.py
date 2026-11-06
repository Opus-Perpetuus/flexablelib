"""2.2.3 regressions: constructor jagged rows, str data rejection, bool coerce."""
import pytest

from flexablelib import Table


def test_constructor_jagged_rows_do_not_spawn_ghost_column():
    """A short first row must not invent a column after a wider later row."""
    table = Table(headers=['a', 'b'], rows=[[1], [2, 3]])
    assert table.headers == ['a', 'b']
    assert table.column_count == 2
    assert table.rows == [[1, None], [2, 3]]


def test_constructor_jagged_rows_with_three_headers():
    table = Table(headers=['a', 'b', 'c'], rows=[[1, 2], [3, 4, 5]])
    assert table.headers == ['a', 'b', 'c']
    assert table.column_count == 3
    assert table.rows == [[1, 2, None], [3, 4, 5]]


def test_constructor_more_headers_than_first_row_still_keeps_them():
    table = Table(headers=['a', 'b', 'c', 'd'], rows=[[1, 2]])
    assert table.headers == ['a', 'b', 'c', 'd']
    assert table.column_count == 4
    assert table.rows == [[1, 2, None, None]]


def test_add_row_rejects_bare_string():
    table = Table()
    with pytest.raises(TypeError, match='sequence of cells'):
        table.add_row('not-cells')


def test_add_column_rejects_bare_string_data():
    table = Table()
    with pytest.raises(TypeError, match='sequence of cells'):
        table.add_column('name', 'abc')


def test_add_row_accepts_single_string_cell_in_a_list():
    table = Table()
    table.add_row(['hello'])
    assert table.rows == [['hello']]


def test_constructor_rejects_string_row_entries():
    with pytest.raises(TypeError, match='sequences of cells'):
        Table(rows=['ab', 'cd'])


def test_constructor_rejects_rows_as_string():
    with pytest.raises(TypeError, match='sequence of rows'):
        Table(rows='ab')


def test_show_empty_columns_coerces_to_bool():
    table = Table()
    table.add_column('a', [1, 2])
    table.add_column('b', ['', ''])
    table.show_empty_columns = 0
    assert table.show_empty_columns is False
    assert 'b' not in table.compose()
    table.show_empty_columns = 1
    assert table.show_empty_columns is True
    assert 'b' in table.compose()
