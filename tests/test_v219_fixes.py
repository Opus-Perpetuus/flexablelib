"""2.0.19: bugs found by the edge-case sweep."""
import pytest

from flexablelib import Table
from flexablelib.text_width import strip_ansi, visible_width


def _widths(table):
    return {visible_width(line) for line in strip_ansi(table.compose()).splitlines()}


# column_max_width measured characters, not terminal columns ----------------

def test_max_width_trims_cjk_by_terminal_columns():
    table = Table(rows=[['東京'], ['大阪府']], headers=['city'])
    table.style_name = 'ascii'
    table.column_max_width = 4
    lines = strip_ansi(table.compose()).splitlines()
    assert '| 東京 |' in lines
    assert '| ...  |' in lines
    assert len(_widths(table)) == 1


def test_max_width_keeps_a_short_cell_that_fits():
    table = Table(rows=[['ab'], ['abcdef']], headers=['c'])
    table.style_name = 'ascii'
    table.column_max_width = 3
    body = strip_ansi(table.compose()).splitlines()
    assert '| ab  |' in body
    assert '| ... |' in body


def test_max_width_trims_each_line_of_a_multiline_cell():
    table = Table(rows=[['a\nbb\nccccc']], headers=['m'])
    table.style_name = 'ascii'
    table.column_max_width = 3
    body = strip_ansi(table.compose()).splitlines()
    assert '| a   |' in body
    assert '| bb  |' in body
    assert '| ... |' in body
    assert len(_widths(table)) == 1


def test_max_width_trims_none_cells_like_before():
    table = Table(rows=[[None], ['x']], headers=['c'])
    table.style_name = 'ascii'
    table.column_max_width = 3
    assert '| ... |' in strip_ansi(table.compose()).splitlines()


@pytest.mark.parametrize('style', Table().possible_styles)
def test_max_width_wide_text_keeps_every_style_rectangular(style):
    if style in ('plain', 'blank', 'empty', 'markdown', 'psql'):
        pytest.skip('style has no closing border')
    table = Table(rows=[['東京', 1], ['大阪府', 22]], headers=['名前', 'n'])
    table.style_name = style
    table.column_max_width = 3
    assert len(_widths(table)) == 1


# sticks indicators overhung narrow columns -----------------------------------

@pytest.mark.parametrize('rows', [[['a']], [['é'], ['ab']]])
def test_sticks_indicator_fits_narrow_columns(rows):
    table = Table(rows=rows, headers=['c'])
    table.style_name = 'sticks'
    assert len(_widths(table)) == 1


def test_sticks_indicator_fits_the_index_column():
    table = Table(rows=[['alpha', 1]], headers=['name', 'n'])
    table.style_name = 'sticks'
    table.show_index = True
    lines = strip_ansi(table.compose()).splitlines()
    assert len(_widths(table)) == 1
    assert lines[0].startswith('+~>~+')


def test_sticks_wide_columns_are_unchanged():
    table = Table(rows=[['alpha', 100]], headers=['name', 'qty'])
    table.style_name = 'sticks'
    assert strip_ansi(table.compose()).splitlines()[0] == '+ ~<~   + ~>~ +'
