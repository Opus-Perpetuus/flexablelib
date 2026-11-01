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


# a float column narrower than its integer digits broke the frame --------------

def test_float_column_below_its_integer_width_keeps_the_frame_square():
    table = Table(rows=[[1.5], [22.25], [3.0]], headers=['v'])
    table.style_name = 'ascii'
    table.column_max_width = 1
    lines = strip_ansi(table.compose()).splitlines()
    assert len(_widths(table)) == 1
    assert '| 22 |' in lines


def test_float_column_cap_that_fits_still_applies():
    table = Table(rows=[[1.125], [22.25]], headers=['v'])
    table.style_name = 'ascii'
    table.column_max_width = 4
    lines = strip_ansi(table.compose()).splitlines()
    assert len(_widths(table)) == 1
    assert max(len(line) for line in lines) == 8


# show_index + column_max_width on a text column ------------------------------

def test_index_with_max_width_trims_the_last_text_column():
    table = Table(rows=[['é', 'abcdef']], headers=['a', 'b'])
    table.show_index = True
    table.column_max_width = 2
    table.style_name = 'ascii'
    lines = strip_ansi(table.compose()).splitlines()
    assert '| 0 | é | .. |' in lines


def test_index_with_max_width_leaves_other_alignments_alone():
    table = Table(rows=[['abcdef', 5], ['x', 10]], headers=['name', 'qty'])
    table.show_index = True
    table.column_max_width = {'name': 3}
    table.col_alignment = ['l', 'l']
    table.style_name = 'ascii'
    lines = strip_ansi(table.compose()).splitlines()
    assert '| 0 | ... | 5   |' in lines


# merges on styles whose frame has no horizontal glyph ------------------------

@pytest.mark.parametrize('hrules', ['none', 'frame', 'header'])
def test_merge_with_hrules_on_ascii_rounded(hrules):
    table = Table(rows=[['a', 'b'], ['c', 'd']], headers=['x', 'y'])
    table.style_name = 'ascii_rounded'
    table.hrules = hrules
    table.merge_cells(0, 0, 1, 0)
    assert len(_widths(table)) == 1


# sort_by over mixed types ------------------------------------------------------

def _mixed():
    table = Table(rows=[['a', None], ['b', 3], ['c', 'x'], ['d', 1.5],
                        ['e', float('nan')], ['f', 'w']], headers=['k', 'v'])
    table.style_name = 'ascii'
    table.sort_by = 'v'
    return table


def test_sort_by_mixed_numbers_text_and_none():
    table = _mixed()
    order = [line.split('|')[1].strip()
             for line in strip_ansi(table.compose()).splitlines()
             if line.startswith('|')][1:]
    assert order == ['d', 'b', 'f', 'c', 'a', 'e']


def test_sort_by_reverse_keeps_missing_last():
    table = _mixed()
    table.sort_reverse = True
    order = [line.split('|')[1].strip()
             for line in strip_ansi(table.compose()).splitlines()
             if line.startswith('|')][1:]
    assert order == ['c', 'f', 'b', 'd', 'a', 'e']


def test_sort_by_plain_numbers_is_unchanged():
    table = Table(rows=[[3], [1], [2]], headers=['n'])
    table.sort_by = 'n'
    assert [r for r in table.rows] == [[3], [1], [2]]
    body = [line.strip('| ') for line in strip_ansi(table.compose()).splitlines()
            if line.startswith('|')][1:]
    assert body == ['1', '2', '3']


# numeric-looking header over a float column ----------------------------------

@pytest.mark.parametrize('valign', [None, 'top', 'middle', 'bottom'])
@pytest.mark.parametrize('header', ['0', '2024', '1.25', 'a'])
def test_numeric_header_over_float_column(valign, header):
    table = Table(rows=[[1.5, 'x\ny'], [22.25, 'z']], headers=[header, 'b'])
    table.style_name = 'ascii'
    if valign:
        table.valign = valign
    lines = strip_ansi(table.compose()).splitlines()
    assert len(_widths(table)) == 1
    assert lines[1].startswith('| ' + header.rjust(5) + ' |')


# --- colours stay off when colours are off --------------------------------

def _coloured_frame(**kw):
    t = Table(rows=[['b', 'c'], ['d', 'e']], headers=['h', 'k'])
    t.style_name = 'ascii'
    t.border_color = 'blue'
    t.header_color = 'red'
    t.border_text('TOP', 'top', color='red')
    t.border_text('LR', 'left', color='green')
    for key, value in kw.items():
        setattr(t, key, value)
    return t


def test_border_color_emits_nothing_when_colours_disabled():
    assert '\x1b' not in _coloured_frame(use_colors=False).compose()


def test_border_color_respects_no_color(monkeypatch):
    monkeypatch.setenv('NO_COLOR', '1')
    monkeypatch.delenv('FORCE_COLOR', raising=False)
    assert '\x1b' not in _coloured_frame().compose()


def test_border_color_still_paints_when_colours_enabled():
    out = _coloured_frame(use_colors=True).compose()
    assert '\x1b[34m' in out and '\x1b[31m' in out


def test_theme_does_not_force_colour_into_a_pipe(monkeypatch):
    monkeypatch.setenv('NO_COLOR', '1')
    monkeypatch.delenv('FORCE_COLOR', raising=False)
    t = Table(rows=[['b', 'c']], headers=['h', 'k'])
    t.apply_theme('dark')
    assert t.use_colors is None
    assert '\x1b' not in t.compose()
    t.use_colors = True
    assert '\x1b' in t.compose()


def test_vertical_border_text_skips_title_and_caption():
    plain = Table(rows=[['b', 'c'], ['d', 'e']], headers=['h', 'k'])
    plain.style_name = 'ascii'
    plain.border_text('LR', 'left')
    framed = plain.compose()
    plain.title = 't'
    plain.caption = 'c'
    lines = plain.compose().split('\n')
    assert lines[0].strip() == 't' and lines[-1].strip() == 'c'
    assert '\n'.join(lines[1:-1]) == framed
    assert lines[1].startswith('+')


# --- float cells fill wider columns ----------------------------------------

@pytest.mark.parametrize('style', ['ascii', 'grid_eheader', 'modern'])
def test_float_column_fills_min_width(style):
    t = Table(rows=[[1.5, 'x'], [22.25, 'y']], headers=['h', 'k'])
    t.style_name = style
    t.column_min_width = {'h': 10}
    widths = {visible_width(line) for line in t.compose().split('\n')}
    assert len(widths) == 1


def test_float_column_fills_long_header():
    t = Table(rows=[[1.5], [22.25]], headers=['a long header'])
    t.style_name = 'ascii'
    lines = t.compose().split('\n')
    assert len({visible_width(line) for line in lines}) == 1
    assert lines[3].rstrip('| ').endswith('1.5')


# --- divider on a style without a body rule --------------------------------

@pytest.mark.parametrize('style', ['dashes', 'grid_eheader'])
def test_divider_matches_table_width_after_wrapped_row(style):
    t = Table(rows=[['a\nbb', 'c'], ['d', 'e']], headers=['h', 'k'])
    t.style_name = style
    t.add_divider(0)
    lines = t.compose().split('\n')
    assert len({visible_width(line) for line in lines}) == 1


# --- a width cap never cuts below content that cannot shrink ---------------

def test_max_width_leaves_index_column_whole():
    t = Table(rows=[['a'], ['b'], ['c']], headers=['h'])
    t.style_name = 'ascii'
    t.show_index = True
    t.roman_index = True
    t.column_max_width = 1
    lines = t.compose().split('\n')
    assert len({visible_width(line) for line in lines}) == 1
    assert '| II | c |' in lines


@pytest.mark.parametrize('overflow', ['wrap', 'truncate'])
def test_max_width_one_with_wide_glyphs(overflow):
    t = Table(rows=[['x']], headers=['名前0'])
    t.style_name = 'ascii'
    t.column_max_width = 1
    t.overflow = overflow
    lines = t.compose().split('\n')
    assert len({visible_width(line) for line in lines}) == 1


def test_max_width_beats_min_width():
    t = Table(rows=[['abcdef']], headers=['h'])
    t.style_name = 'ascii'
    t.column_min_width = 8
    t.column_max_width = 4
    assert '| a... |' in t.compose()


# --- merges follow cell_padding -------------------------------------------

def _merged(style, pad):
    t = Table(rows=[['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']],
              headers=['x', 'y', 'z'])
    t.style_name = style
    t.cell_padding = pad
    t.merge_cells(0, 0, 1, 1, value='M')
    return t.compose()


@pytest.mark.parametrize('style', ['modern', 'ascii', 'rounded', 'double'])
@pytest.mark.parametrize('pad', [0, 2, 3])
def test_merge_respects_cell_padding(style, pad):
    lines = _merged(style, pad).split('\n')
    assert len({visible_width(line) for line in lines}) == 1
    assert any('M' in line for line in lines)


def test_merge_with_zero_padding_repairs_junctions():
    assert _merged('modern', 0) == '\n'.join([
        '┌─┬─┬─┐',
        '│x│y│z│',
        '├─┴─┼─┤',
        '│   │c│',
        '│   ├─┤',
        '│ M │f│',
        '├─┬─┼─┤',
        '│g│h│i│',
        '└─┴─┴─┘',
    ])


def test_merge_with_wide_padding_matches_layout():
    assert _merged('ascii', 2).split('\n')[3:6] == [
        '|           |  c  |',
        '|           +-----+',
        '|     M     |  f  |',
    ]


# --- colour specs exported to CSS / XLSX ----------------------------------

from flexablelib.colors import background_hex, foreground_hex, spec_to_css


@pytest.mark.parametrize('spec, bg, fg', [
    ('on red', 'DC2626', None),
    ('on  blue', '2563EB', None),
    ('black on grey15', '262626', '111827'),
    ('red on 236', '303030', '991B1B'),
    ('grey50', None, '808080'),
    ('color:196', None, 'FF0000'),
    ('bold #ff8800 on #112233', '112233', 'FF8800'),
    ('bright_red on blue', '2563EB', 'B91C1C'),
    (None, None, None),
])
def test_spec_hex_matches_terminal_grammar(spec, bg, fg):
    assert background_hex(spec) == bg
    assert foreground_hex(spec) == fg


def test_background_only_merge_colour_reaches_html():
    t = Table(rows=[['a', 'b'], ['c', 'd']], headers=['x', 'y'])
    t.merge_cells(0, 0, 0, 1, value='M', color='on red')
    assert 'background-color:#DC2626' in t.to_html()
    assert spec_to_css('on red') == 'background-color:#DC2626'
