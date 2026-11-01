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


# border_text left/right ate cell text on styles with no outer border ---------

@pytest.mark.parametrize('style', ['simple', 'clean', 'psql', 'plain', 'presto'])
@pytest.mark.parametrize('where', ['left', 'right'])
def test_vertical_border_text_never_overwrites_cells(style, where):
    table = Table(rows=[['alpha', 1], ['beta', 2]], headers=['name', 'n'])
    table.style_name = style
    before = table.compose()
    table.border_text('HI', where)
    assert table.compose() == before


def test_vertical_border_text_still_draws_on_framed_styles():
    table = Table(rows=[['alpha', 1], ['beta', 2]], headers=['name', 'n'])
    table.style_name = 'modern'
    table.border_text('HI', 'left')
    lines = strip_ansi(table.compose()).splitlines()
    assert lines[1][0] == 'H' and lines[2][0] == 'I'


# readers ----------------------------------------------------------------------

def test_markdown_round_trips_escaped_pipes():
    table = Table(rows=[['a|b', 'c']], headers=['x|y', 'z'])
    back = Table.from_markdown(table.to_markdown())
    assert back.headers == ['x|y', 'z']
    assert back.rows == [['a|b', 'c']]


def test_markdown_escaped_pipe_at_the_end_of_a_row_is_kept():
    back = Table.from_markdown('| a | b |\n|---|---|\n| 1 | x \\|')
    assert back.rows == [[1, 'x |']]


def test_from_records_accepts_to_records_output():
    table = Table(rows=[['ann', 30], ['bob', 41]], headers=['name', 'age'])
    back = Table.from_records(table.to_records())
    assert back.headers == ['name', 'age']
    assert back.rows == [['ann', 30], ['bob', 41]]


def test_from_records_dict_rows_follow_the_given_headers():
    back = Table.from_records([{'a': 1, 'b': 2}, {'b': 3}], headers=['b', 'a'])
    assert back.headers == ['b', 'a']
    assert back.rows == [[2, 1], [3, '']]


def test_from_html_reads_a_to_html_page():
    table = Table(rows=[['</script>x', 1.5], ['a|b', 7]], headers=['x', 'y'])
    back = Table.from_html(table.to_html())
    assert back.headers == ['x', 'y']
    assert back.rows == [['</script>x', 1.5], ['a|b', 7]]


def test_from_html_of_a_plain_table_is_unchanged():
    markup = '<table><tr><th>a</th></tr><tr><td>1</td></tr></table>'
    assert Table.from_html(markup).rows == [[1]]
