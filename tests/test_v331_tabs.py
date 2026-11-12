"""
Tabs and line breaks in cells, titles, captions and cards.

A tab measures nothing, so text holding one used to be measured and wrapped
as if it were narrower than the spaces it later became: tables came out wider
than ``max_table_width`` and card frames lost their right border. A newline
in a card title or a border title split the frame in two.
"""

import pytest

from flexablelib import Card, Table
from flexablelib.text_width import (
    expand_tabs, strip_ansi, visible_width, wrap_to_width)


def _widths(text):
    text = strip_ansi(text)
    return {visible_width(line) for line in text.split('\n')}


# -- expand_tabs -------------------------------------------------------------

@pytest.mark.parametrize('text, expected', [
    ('', ''),
    ('no tabs', 'no tabs'),
    ('\tx', ' ' * 8 + 'x'),
    ('ab\tc', 'ab' + ' ' * 6 + 'c'),
    ('a\nb\tc', 'a\nb' + ' ' * 7 + 'c'),
    ('a\r\n\tb', 'a\r\n' + ' ' * 8 + 'b'),
])
def test_expand_tabs_matches_str_expandtabs_on_ascii(text, expected):
    assert expand_tabs(text) == expected
    assert expand_tabs(text) == text.expandtabs(8)


def test_expand_tabs_counts_wide_characters_as_two_columns():
    # '漢' is two columns, so the stop at 8 is six spaces away, not seven.
    assert expand_tabs('漢\tx') == '漢' + ' ' * 6 + 'x'
    assert visible_width(expand_tabs('漢\tx')) == 9


def test_expand_tabs_ignores_escape_sequences():
    coloured = '\x1b[31mab\x1b[0m\tc'
    assert expand_tabs(coloured) == '\x1b[31mab\x1b[0m' + ' ' * 6 + 'c'


def test_expand_tabs_custom_size_and_floor():
    assert expand_tabs('a\tb', 4) == 'a   b'
    assert expand_tabs('a\tb', 0) == 'a b'


def test_wrap_to_width_never_returns_a_line_wider_than_asked():
    for text in ('\t tab', 'a\tb\tc', '漢\t字', 'x' * 5 + '\t' + 'y' * 5):
        # From 2: a wide character alone on a 1-column line is documented.
        for width in range(2, 20):
            for line in wrap_to_width(text, width):
                assert '\t' not in line
                assert visible_width(line) <= width, (text, width, line)


# -- tables ------------------------------------------------------------------

@pytest.mark.parametrize('cell', ['\t tab', 'a\tb', '漢\tx', '\t\t'])
@pytest.mark.parametrize('limit', [12, 20, 40])
def test_table_with_tabs_respects_max_table_width(cell, limit):
    table = Table(rows=[['a', 3.14159, '', cell], ['b', 1, 'c', 'd']],
                  headers=['漢字', 'h', '漢字', 'long header'])
    table.max_table_width = limit
    out = table.render()
    assert '\t' not in out
    assert max(_widths(out)) <= limit


def test_table_tab_cell_lines_are_all_the_same_width():
    table = Table(rows=[['x\ty', 1], ['\t', 2]], headers=['a', 'b'])
    out = str(table)
    assert '\t' not in out
    assert len(_widths(out)) == 1


def test_exports_keep_the_tab():
    table = Table(rows=[['a\tb']], headers=['h'])
    assert 'a\tb' in table.to_csv()
    assert table.to_records()[0]['h'] == 'a\tb'


def test_multiline_title_and_caption_are_aligned_per_line():
    table = Table(rows=[[1, 2222222222]], headers=['a', 'b'])
    table.title = 'Top\nsecond'
    table.caption = 'c\td\nzz'
    lines = table.render(40).split('\n')
    width = max(visible_width(line) for line in lines)
    assert lines[0].strip() == 'Top'
    assert lines[1].strip() == 'second'
    # Centred lines start further in than column 0.
    assert lines[1].startswith(' ')
    assert lines[-1].strip() == 'zz' and lines[-1].startswith(' ')
    assert lines[-2].strip() == 'c' + ' ' * 7 + 'd'
    assert all(visible_width(line) <= width for line in lines)
    assert '\t' not in '\n'.join(lines)


def test_border_title_with_newline_stays_on_the_top_rule():
    table = Table(rows=[[1, 2222222222]], headers=['a', 'b'])
    table.title = 'one\ntwo'
    table.title_position = 'border'
    lines = table.render(40).split('\n')
    assert 'one two' in lines[0]
    assert len(_widths('\n'.join(lines))) == 1


# -- cards -------------------------------------------------------------------

def test_card_border_title_with_newline_and_tab_keeps_the_frame():
    out = Card(title='a\tb\nc', fields=[('k\tx', 'v\ty')],
               footer='f\tg', use_colors=False).render()
    lines = out.split('\n')
    assert '\t' not in out
    assert len(_widths(out)) == 1
    assert 'a' + ' ' * 7 + 'b c' in lines[0]
    # The label keeps its expanded width instead of wrapping at the tab.
    assert 'k' + ' ' * 7 + 'x' in out


def test_card_inside_title_with_newline_is_two_lines():
    out = Card(title='first\nsecond', title_position='inside',
               fields=[('k', 'v')], use_colors=False).render()
    assert len(_widths(out)) == 1
    assert any(line.strip('│ ') == 'first' for line in out.split('\n'))
    assert any(line.strip('│ ') == 'second' for line in out.split('\n'))


def test_responsive_cards_with_tab_and_newline_in_the_title_column():
    table = Table(rows=[['line1\nline2', 'é', '\t tab', ' lead']],
                  headers=['h', 'h\tx', 'long header', 'multi\nline'])
    out = table.render(30)
    assert table.render_mode(30) == 'cards'
    assert '\t' not in out
    assert _widths(out) == {30}
    assert 'line1 line2' in out.split('\n')[0]
