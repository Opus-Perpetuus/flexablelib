import pytest

from flexablelib import Table


def _table():
    return Table(rows=[[1, 'a'], [2, 'b'], [3, 'c']], headers=['n', 's'])


def test_add_dividers_accepts_one_iterable():
    by_iterable = _table()
    by_iterable.add_dividers([0, 1])
    by_args = _table()
    by_args.add_dividers(0, 1)
    assert by_iterable.compose() == by_args.compose()
    assert by_iterable.compose() != _table().compose()


def test_hrules_true_means_all():
    table = _table()
    table.hrules = True
    assert table.hrules == 'all'


def test_invalid_hrules_and_vrules_raise():
    table = _table()
    with pytest.raises(ValueError):
        table.hrules = 'sometimes'
    with pytest.raises(ValueError):
        table.vrules = 'sometimes'


def test_border_text_rejects_unknown_where_and_align():
    table = _table()
    with pytest.raises(ValueError, match='where'):
        table.border_text('x', where='middle')
    with pytest.raises(ValueError, match='align'):
        table.border_text('x', align='justify')


def test_clear_border_texts_restores_plain_render():
    table = _table()
    plain = table.compose()
    table.border_text('hi', where='bottom')
    assert table.compose() != plain
    assert table.clear_border_texts() is table
    assert table.compose() == plain


@pytest.mark.parametrize('name', ['row_filter', 'color_rule'])
def test_callable_options_reject_non_callables(name):
    table = _table()
    with pytest.raises(TypeError):
        setattr(table, name, 'not callable')
    setattr(table, name, None)
    assert getattr(table, name) is None


def test_hide_columns_out_of_range_index_raises():
    table = _table()
    table.hide_columns = [5]
    with pytest.raises(ValueError, match='out of range'):
        table.compose()
