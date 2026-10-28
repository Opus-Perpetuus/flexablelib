"""Features shipped in 2.0.13 (zebra, caption, footer, padding, cell_colors, overflow, from_markdown)."""
import re
import pytest
from flexablelib.table import Table


def bare(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def _sample(**opts):
    t = Table.from_records(
        [['A', 10], ['B', 20], ['C', 30], ['Tot', 60]],
        headers=['Name', 'N'],
        style_name='rounded',
        **opts,
    )
    return t


def test_caption_below_title_above():
    t = _sample()
    t.title = 'TITLE'
    t.caption = 'CAPTION'
    out = bare(t.compose()).splitlines()
    assert out[0].strip() == 'TITLE'
    assert out[-1].strip() == 'CAPTION'


def test_zebra_alias_row_stripe_emits_ansi():
    t = _sample()
    t.use_colors = True
    t.zebra = ('', 'on #222233')
    coloured = t.compose()
    assert '\x1b[' in coloured
    t.row_stripe = ('dim', 'bold')
    assert t.zebra == ('dim', 'bold')


def test_footer_rows_color():
    t = _sample()
    t.use_colors = True
    t.footer_rows = 1
    t.footer_color = 'bold yellow'
    coloured = t.compose()
    assert '\x1b[' in coloured
    # Last data row Tot should be painted; first row text still present.
    assert 'Tot' in bare(coloured)


def test_cell_padding_and_show_margin():
    t = _sample()
    assert t.style_composition.margin >= 1
    t.cell_padding = 3
    assert t.style_composition.margin == 3
    t.cell_padding = None
    t.show_margin = False
    assert t.style_composition.margin == 0


def test_cell_colors_by_header_and_index():
    t = _sample()
    t.use_colors = True
    t.cell_colors = {(0, 'Name'): 'green', (1, 1): 'red'}
    coloured = t.compose()
    assert '\x1b[' in coloured
    assert 'A' in bare(coloured)


def test_overflow_sets_auto_wrap():
    t = _sample()
    t.overflow = 'wrap'
    assert t.auto_wrap is True
    assert t.overflow == 'wrap'
    t.overflow = 'truncate'
    assert t.auto_wrap is False
    t.overflow = 'ellipsis'
    assert t.overflow == 'truncate'
    with pytest.raises(ValueError):
        t.overflow = 'explode'


def test_from_markdown_roundtrip_alignment():
    md = '| Name | N |\n| :--- | ---: |\n| A | 10 |\n| B | 20 |\n'
    t = Table.from_markdown(md, style_name='markdown')
    assert t.col_alignment == ['l', 'r']
    assert t.columns['Name'] == ['A', 'B']
    assert t.columns['N'] == [10, 20]
    out = t.to_markdown()
    assert 'Name' in out and 'N' in out


def test_on_background_only_colour_spec():
    from flexablelib.colors import parse_spec
    seq = parse_spec('on #112233')
    assert seq.startswith('\x1b[')
    assert '48;2;17;34;51' in seq
