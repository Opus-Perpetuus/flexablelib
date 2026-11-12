"""
Format templates on cells they cannot format, and the Excel number formats
the terminal formats translate to.
"""

import io

import pytest

from flexablelib import Table


def _plain(table):
    table.use_colors = False
    return table.compose()


# -- brace templates -----------------------------------------------------------

def test_brace_template_leaves_text_cells_alone():
    # A plain spec already did; the template aborted the whole render.
    for spec in ('{:,.2f}', ',.2f', '%.2f'):
        table = Table(rows=[[1234.5], ['n/a'], [None]], headers=['p'])
        table.custom_format = {'p': spec}
        out = _plain(table)
        assert '1,234.50' in out or '1234.50' in out
        assert 'n/a' in out


def test_brace_template_through_float_format_and_exports():
    table = Table(rows=[[1.5, 'x'], ['-', 'y']], headers=['n', 's'])
    table.float_format = '$ {:,.2f}'
    assert '$ 1.50' in _plain(table)
    assert table.to_records(formatted=True)[1]['n'] == '-'
    assert '$ 1.50' in table.to_csv()


@pytest.mark.parametrize('spec', ['{:.2f} {:.1f}', '{name}', '{1}'])
def test_brace_template_wanting_more_values_says_so(spec):
    table = Table(rows=[[1.5]], headers=['n'])
    table.float_format = spec
    with pytest.raises(ValueError, match='one value'):
        table.compose()


def test_escaped_braces_are_literal():
    table = Table(rows=[[2.0]], headers=['n'])
    table.float_format = '{} {{unit}}'
    assert '2.0 {unit}' in _plain(table)


# -- Excel number formats ---------------------------------------------------

openpyxl = pytest.importorskip('openpyxl')


def _excel_formats(tmp_path, **settings):
    table = Table(rows=[[1234, 1234.5, 'x']], headers=['i', 'f', 's'])
    for name, value in settings.items():
        setattr(table, name, value)
    path = str(tmp_path / 'out.xlsx')
    table.to_excel(path)
    sheet = openpyxl.load_workbook(path).active
    return sheet['A2'].number_format, sheet['B2'].number_format


@pytest.mark.parametrize('settings, expected', [
    (dict(int_format=',', float_format='.3e'), ('#,##0', '0.000E+00')),
    (dict(int_format='n', float_format=','), ('0', '#,##0.##########')),
    (dict(int_format='E'), ('0.000000E+00', 'General')),
    (dict(float_format='.0%'), ('General', '0%')),
    (dict(int_format='{0:,d}', float_format='$ {:,.0f} MXN'),
     ('#,##0', '"$ "#,##0" MXN"')),
    (dict(custom_format={'i': ',d', 1: '.1f'}), ('#,##0', '0.0')),
    (dict(leading_zeros=5), ('00000', 'General')),
])
def test_excel_formats_match_the_terminal(tmp_path, settings, expected):
    assert _excel_formats(tmp_path, **settings) == expected


@pytest.mark.parametrize('settings', [
    dict(float_format='.2n'),             # precision with 'n': no equivalent
    dict(int_format='{:x}'),               # hex has no number format
    dict(float_format='d'),                # 'd' does not apply to a float
    dict(int_format='05d'),                # zero padding through a width
    dict(float_format=lambda v: str(v)),   # callables stay General
    dict(float_format='{} and {{x}}'),     # not a single-field template
    dict(float_format='n'),                # plain 'n' on a float
])
def test_excel_falls_back_to_general(tmp_path, settings):
    formats = _excel_formats(tmp_path, **settings)
    assert 'General' in formats
    key = 'int_format' if 'int_format' in settings else 'float_format'
    assert formats[0 if key == 'int_format' else 1] == 'General'


# -- HTML ----------------------------------------------------------------------

def _merged_html(**colors):
    table = Table(rows=[['a', 'b'], ['c', 'd']], headers=['x', 'y'])
    table.merge_cells(0, 0, 1, 0)
    for name, value in colors.items():
        setattr(table, name, value)
    return table.to_html()


def test_html_merge_inherits_row_colour():
    html = _merged_html(row_colors={0: 'red'})
    cell = html[html.index('rowspan="2"'):].split('>')[0]
    assert 'color:' in cell


def test_html_merge_inherits_column_colour():
    plain = _merged_html()
    coloured = _merged_html(column_colors={'x': 'blue'})
    cell = coloured[coloured.index('rowspan="2"'):].split('>')[0]
    assert 'color:' in cell
    assert cell != plain[plain.index('rowspan="2"'):].split('>')[0]


def test_html_writes_to_a_handle_and_a_path(tmp_path):
    table = Table(rows=[['a']], headers=['h'])
    handle = io.StringIO()
    assert table.to_html(handle) is None
    assert handle.getvalue() == table.to_html()
    path = tmp_path / 'out.html'
    assert table.to_html(str(path)) is None
    assert path.read_text(encoding='utf-8') == table.to_html()


def test_merged_html_writes_to_a_handle_and_a_path(tmp_path):
    table = Table(rows=[['a', 'b'], ['c', 'd']], headers=['x', 'y'])
    table.merge_cells(0, 0, 1, 0)
    expected = table.to_html()
    assert 'rowspan="2"' in expected
    handle = io.StringIO()
    assert table.to_html(handle) is None
    assert handle.getvalue() == expected
    path = tmp_path / 'merged.html'
    assert table.to_html(str(path)) is None
    assert path.read_text(encoding='utf-8') == expected
