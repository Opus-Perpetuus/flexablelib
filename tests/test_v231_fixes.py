from flexablelib import Table


def _table():
    return Table(rows=[[10, 'a'], [20, 'b']], headers=['n', 's'])


def test_to_html_paginate_none_shows_all_rows():
    html = _table().to_html(paginate=None)
    assert '"perPage": 0' in html
    assert html == _table().to_html(paginate=0)


def test_index_start_none_falls_back_to_zero():
    table = _table()
    table.index_start = 5
    table.index_start = None
    assert table.index_start == 0
    table.show_index = True
    lines = table.compose().splitlines()
    assert any('| 0 |' in line for line in lines)


def test_index_step_none_falls_back_to_one():
    table = _table()
    table.index_step = 3
    table.index_step = None
    assert table.index_step == 1
    table.show_index = True
    out = table.compose()
    assert '| 0 |' in out and '| 1 |' in out
