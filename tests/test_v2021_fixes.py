"""Fixes and coverage added for 2.0.21."""
import pytest

from flexablelib import Table
from flexablelib.text_width import strip_ansi, visible_width


def _widths(text):
    return {visible_width(line) for line in strip_ansi(text).split('\n')}


# --- exponent-only float columns ---------------------------------------------

@pytest.mark.parametrize('values', [
    [1e20], [1e20, -2e30], [1e16, 12345], [1.5e-7, 2e-9],
])
def test_float_column_without_any_point_stays_rectangular(values):
    t = Table(rows=[[v] for v in values], headers=['x'])
    t.style_name = 'ascii_double_underline_rows'
    out = t.compose()
    assert len(_widths(out)) == 1, out
    for v in values:
        assert str(v) in out


def test_exponent_still_aligns_with_decimals_in_the_same_column():
    t = Table(rows=[[1e20], [1.5]], headers=['x'])
    lines = t.compose().split('\n')
    assert len(_widths('\n'.join(lines))) == 1
    body = [line for line in lines if '1e+20' in line or '1.5' in line]
    # The integer part of 1.5 lines up with the end of the mantissa block.
    assert body[0].index('1e+20') + len('1e+20') - 1 == body[1].index('1.5')


def test_exponent_column_next_to_other_columns_with_index():
    t = Table(rows=[[1e20, 'a'], [3e21, 'bb']], headers=['n', 's'])
    t.show_index = True
    t.style_name = 'rounded'
    assert len(_widths(t.compose())) == 1


# --- vrules='none' -----------------------------------------------------------

@pytest.mark.parametrize('style', [
    'ascii_double_underline_rows', 'rounded', 'double_horizontal_rows', 'dashed', 'ascii_rounded',
    'double_header_rows', 'double_horizontal', 'markdown',
])
def test_vrules_none_rules_are_as_wide_as_the_rows(style):
    t = Table(rows=[[1, 'ab'], [2.5, '漢字']], headers=['A', 'B'])
    t.style_name = style
    t.vrules = 'none'
    out = t.compose()
    assert len(_widths(out)) == 1, out


def test_vrules_none_draws_no_corners():
    t = Table(rows=[[1, 2]], headers=['A', 'B'])
    t.style_name = 'rounded'
    t.vrules = 'none'
    out = t.compose()
    for corner in '╭╮╰╯├┤┬┴┼│':
        assert corner not in out


def test_vrules_frame_keeps_the_outer_corners():
    t = Table(rows=[[1, 2]], headers=['A', 'B'])
    t.style_name = 'rounded'
    t.vrules = 'frame'
    out = t.compose()
    assert out.split('\n')[0].startswith('╭')
    assert out.split('\n')[-1].endswith('╯')
    assert len(_widths(out)) == 1


# --- merge_cells argument types ----------------------------------------------

def test_merge_cells_rejects_a_pair_where_a_number_goes():
    t = Table(rows=[[1, 2], [3, 4]], headers=['a', 'b'])
    with pytest.raises(TypeError, match='first_row must be an integer'):
        t.merge_cells((0, 0), (1, 1))
    assert t.merged_regions == []


def test_merge_cells_rejects_floats():
    t = Table(rows=[[1, 2], [3, 4]], headers=['a', 'b'])
    with pytest.raises(TypeError, match='last_column must be an integer'):
        t.merge_cells(0, 0, 1, 1.0)


def test_merge_cells_accepts_integer_like_objects():
    class Idx:
        def __init__(self, n):
            self.n = n

        def __index__(self):
            return self.n

    t = Table(rows=[[1, 2], [3, 4]], headers=['a', 'b'])
    region = t.merge_cells(Idx(0), Idx(0), last_column=Idx(1), value='X')
    assert (region.first_row, region.last_column) == (0, 1)
    assert type(region.first_row) is int
    assert 'X' in t.compose()


# --- coverage: public paths not exercised before -----------------------------

def test_init_with_columns_and_more_headers_pads_the_extra_column():
    t = Table(columns=[[1, 2], [3, 4]], headers=['a', 'b', 'c'])
    assert t.headers == ['a', 'b', 'c']
    assert t.column_count == 3
    assert t.to_records()[0] == {'a': 1, 'b': 3, 'c': None}


def test_init_with_rows_and_more_headers_pads_the_extra_column():
    t = Table(rows=[[1, 2]], headers=['a', 'b', 'c'])
    assert t.column_count == 3
    assert t.to_records() == [{'a': 1, 'b': 2, 'c': None}]


def test_cell_valign_must_be_a_dict():
    t = Table(rows=[[1, 2]], headers=['a', 'b'])
    with pytest.raises(TypeError, match='cell_valign'):
        t.cell_valign = [('t',)]
    t.cell_valign = None
    assert t.cell_valign == {}


def test_col_valign_list_is_normalised_per_column():
    t = Table(rows=[['x\ny\nz', 1, 2]], headers=['a', 'b', 'c'])
    t.col_valign = ['top', 'middle', 'bottom']
    assert t.col_valign == ['t', 'm', 'b']
    lines = t.compose().split('\n')
    body = [line for line in lines if 'x' in line or 'y' in line or 'z' in line]
    assert '1' in body[1] and '2' in body[2]


@pytest.mark.parametrize('args, message', [
    ((0,), 'n must be >= 1'),
    ((2, -1), 'start must be >= 0'),
])
def test_divide_every_rejects_bad_arguments(args, message):
    t = Table(rows=[[i] for i in range(4)], headers=['x'])
    with pytest.raises(ValueError, match=message):
        t.divide_every(*args)


def test_add_dividers_accepts_a_single_iterable():
    t = Table(rows=[[i] for i in range(4)], headers=['x'], style_name='rounded')
    plain = t.compose()
    t.add_dividers([0, 2])
    out = t.compose()
    assert out.count('\n') == plain.count('\n') + 2


def test_title_wider_than_the_table_is_printed_whole():
    t = Table(rows=[[1, 2]], headers=['a', 'b'])
    t.title = 'a title much wider than the table'
    out = t.compose()
    assert out.split('\n')[0] == 'a title much wider than the table'


def test_paginate_without_frozen_header_shows_it_once():
    t = Table(rows=[[i] for i in range(5)], headers=['head'])
    pages = t.paginate(2, freeze_header=False)
    assert len(pages) == 3
    assert 'head' in pages[0]
    assert all('head' not in page for page in pages[1:])


def test_shadow_with_coloured_border_keeps_every_line_equal():
    t = Table(rows=[[1, 2]], headers=['a', 'b'])
    t.shadow = True
    t.border_color = 'red'
    out = t.compose()
    assert '░' in strip_ansi(out)
    assert len(_widths(out)) == 1


# --- exports: gaps and the index column --------------------------------------

def _padded_table():
    return Table(rows=[[1, 2], [3]], headers=['a', 'b', 'c'])


def test_exports_never_write_the_missing_sentinel():
    t = _padded_table()
    t.add_row([4, t.missing, 6])
    outputs = [
        t.to_csv(), t.to_markdown(), t.to_rst(), t.to_asciidoc(),
        t.to_latex(), t.to_html(), str(t.to_records()),
    ]
    for out in outputs:
        assert 'ValuePlacer' not in out
        assert 'object at 0x' not in out
    assert t.to_records() == [
        {'a': 1, 'b': 2, 'c': None},
        {'a': 3, 'b': None, 'c': None},
        {'a': 4, 'b': None, 'c': 6},
    ]
    assert t.to_csv().splitlines() == ['a,b,c', '1,2,', '3,,', '4,,6']


def test_include_index_numbers_the_rows():
    t = Table(rows=[[1, 2], [3, 4]], headers=['a', 'b'])
    t.show_index = True
    assert t.to_csv(include_index=True).splitlines() == [
        'i,a,b', '0,1,2', '1,3,4',
    ]
    for out in (t.to_markdown(include_index=True), t.to_rst(include_index=True),
                t.to_latex(include_index=True), t.to_html(include_index=True),
                t.to_asciidoc(include_index=True)):
        assert 'IndexCounter' not in out


def test_include_index_follows_start_step_title_and_roman():
    t = Table(rows=[[1], [2], [3]], headers=['a'])
    t.show_index = True
    t.index_title = '#'
    t.index_start = 4
    t.index_step = 2
    assert [r['#'] for r in t.to_records(include_index=True)] == [4, 6, 8]
    t.roman_index = True
    assert [r['#'] for r in t.to_records(include_index=True)] == [
        'IV', 'VI', 'VIII',
    ]


def test_include_index_works_without_show_index():
    t = Table(rows=[[1, 2]], headers=['a', 'b'])
    assert t.to_records(include_index=True) == [{'i': 0, 'a': 1, 'b': 2}]
    assert t.to_records() == [{'a': 1, 'b': 2}]


def test_include_index_html_with_merge_has_one_cell_per_column():
    t = Table(rows=[[1, 2], [3, 4]], headers=['a', 'b'])
    t.merge_cells(0, 0, last_row=1, value='m')
    html = t.to_html(include_index=True)
    assert 'IndexCounter' not in html
    assert 'rowspan="2"' in html


# --- transpose keeps gaps as gaps --------------------------------------------

def test_transpose_shows_the_missing_value_in_gaps():
    t = Table(rows=[[1, 2], [3]], headers=['a', 'b', 'c'])
    t.missing_value = '?'
    out = t.transpose()
    assert out.missing_value == '?'
    text = out.compose()
    assert text.count('?') == 3
    assert out.to_csv().splitlines() == [
        'field,row0,row1', 'a,1,3', 'b,2,', 'c,,',
    ]
    assert 'ValuePlacer' not in out.to_csv()


def test_transpose_missing_val_option_wins():
    t = Table(rows=[[1, 2], [3]], headers=['a', 'b'])
    t.missing_value = '?'
    out = t.transpose(missing_val='-')
    assert '-' in out.compose().split('\n')[-2]
    assert '?' not in out.compose()
