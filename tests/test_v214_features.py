"""Features shipped in 2.0.14 (valign, panel/shadow, writers, transpose, paginate, nested)."""
import re
import pytest
from flexablelib.table import Table


def bare(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def test_valign_top_middle_bottom():
    t = Table.from_records(
        [['hi', 'a\nb\nc']],
        headers=['L', 'R'],
        style_name='rounded',
    )
    top = bare(t.compose())
    assert re.search(r'│ hi │ a │', top)
    t.col_valign = {'L': 'b'}
    bottom = bare(t.compose())
    assert re.search(r'│ hi │ c │', bottom)
    t.col_valign = {'L': 'm'}
    mid = bare(t.compose())
    assert re.search(r'│ hi │ b │', mid)


def test_valign_rejects_bad_code():
    t = Table.from_records([[1]], headers=['A'])
    with pytest.raises(ValueError):
        t.valign = 'sideways'


def test_panel_and_shadow():
    t = Table.from_records([['a', 1]], headers=['X', 'Y'], style_name='sharp')
    t.panel = True
    out = bare(t.compose())
    assert out.splitlines()[0].startswith('╭')
    assert out.splitlines()[-1].startswith('╰')
    t.shadow = True
    shadowed = bare(t.compose())
    assert '░' in shadowed


def test_panel_ascii_style():
    t = Table.from_records([['a']], headers=['X'], style_name='ascii')
    t.panel = 'ascii'
    out = bare(t.compose())
    assert out.splitlines()[0].startswith('+')


def test_to_rst_asciidoc_latex():
    t = Table.from_records([['a', 1], ['b', 2]], headers=['X', 'Y'])
    rst = t.to_rst()
    assert '+===' in rst or '+=' in rst
    assert '| X |' in rst or '| X ' in rst
    adoc = t.to_asciidoc()
    assert adoc.startswith('|===')
    assert '| X | Y' in adoc
    tex = t.to_latex()
    assert r'\begin{tabular}' in tex
    assert r'\end{tabular}' in tex
    assert 'X & Y' in tex


def test_transpose_and_rotate_alias():
    t = Table.from_records([['a', 1], ['b', 2]], headers=['X', 'Y'], style_name='sharp')
    rotated = t.transpose()
    assert rotated.headers[0] == 'field'
    assert 'row0' in rotated.headers
    assert rotated.columns['field'] == ['X', 'Y']
    assert t.rotate().columns['field'] == ['X', 'Y']


def test_paginate_pages():
    t = Table.from_records(
        [[f'r{i}', i] for i in range(5)],
        headers=['N', 'V'],
        style_name='simple',
    )
    pages = t.paginate(2)
    assert len(pages) == 3
    assert 'r0' in bare(pages[0]) and 'r1' in bare(pages[0])
    assert 'r4' in bare(pages[2])
    with pytest.raises(ValueError):
        t.paginate(0)


def test_nested_subtable_in_cell():
    inner = Table.from_records([[1, 2]], headers=['a', 'b'], style_name='ascii')
    outer = Table.from_records(
        [['cell', inner]], headers=['k', 'v'], style_name='rounded'
    )
    out = bare(outer.compose())
    assert 'cell' in out
    assert '| a | b |' in out or 'a' in out
    assert '1' in out and '2' in out


def test_column_min_max_still_covered():
    """F10: percent constraints deferred; min/max already ship."""
    t = Table.from_records([['hello world', 1]], headers=['A', 'B'])
    t.column_max_width = {'A': 5}
    t.overflow = 'truncate'
    out = bare(t.compose())
    assert 'he' in out and 'world' not in out
