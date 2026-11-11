"""2.2.1 regressions: merges on the first/last drawn row, and merges that
hiding leaves with a single column."""
import re

import pytest

from flexablelib import Table
from flexablelib.style_compositions import __style_compositions as catalogue
from flexablelib.text_width import visible_width

ROWS = [['a', 3, 'x'], ['b', 1, 'y'], ['c', 2, 'z'], ['d', 4, 'w']]


def make(rows=ROWS, **options):
    table = Table(rows=[list(r) for r in rows], headers=['N', 'V', 'T'])
    table.use_colors = False
    for key, value in options.items():
        setattr(table, key, value)
    return table


# -- merge on the first visible row (after row_filter / sort_by) ------------

ORDERINGS = [
    ('sort_by', lambda t: setattr(t, 'sort_by', 'V')),
    ('sort_reverse', lambda t: (setattr(t, 'sort_by', 'V'),
                                setattr(t, 'sort_reverse', True))),
    ('row_filter', lambda t: setattr(t, 'row_filter', lambda r: r[0] != 'a')),
]


@pytest.mark.parametrize('name,order', ORDERINGS)
def test_top_border_under_title_survives_first_row_merge(name, order):
    table = make(style_name='rounded', show_headers=False, title='T')
    table.merge_cells(0, 0, last_column=1, value='M')
    order(table)
    lines = table.compose().split('\n')
    assert lines[1] == '╭───────┬───╮', lines
    assert lines[-1].startswith('╰')


@pytest.mark.parametrize('name,order', ORDERINGS)
def test_bottom_border_over_caption_survives_last_row_merge(name, order):
    table = make(style_name='single_rows', caption='cap')
    order(table)
    last = 3 if name != 'row_filter' else 2
    table.merge_cells(last, 0, last_column=1, value='M')
    lines = table.compose().split('\n')
    assert lines[-2] == '└───────┴───┘', lines


def test_eheader_separator_drops_junction_over_first_row_merge():
    table = make(sort_by='V')  # default ascii_double_underline_open_header
    table.merge_cells(0, 0, last_column=1, value='M')
    lines = table.compose().split('\n')
    assert lines[2] == '+=======+===+'


def test_markdown_header_separator_kept_over_first_row_merge():
    table = make(style_name='markdown', row_filter=lambda r: r[0] != 'a')
    table.merge_cells(0, 0, last_column=1, value='M')
    assert table.compose().split('\n')[1] == '|---|---|---|'


@pytest.mark.parametrize('style', catalogue._fields)
@pytest.mark.parametrize('options', [
    {'show_headers': False, 'title': 'Title'},
    {'caption': 'caption'},
    {'sort_by': 'V', 'title': 'Title', 'caption': 'caption'},
])
def test_outer_borders_unchanged_by_edge_merges(style, options):
    """A merge on the first or last drawn row never rewrites the frame."""
    def frame(lines):
        head = 1 if options.get('title') else 0
        tail = 1 if options.get('caption') else 0
        return lines[head:len(lines) - tail]

    plain = frame(make(style_name=style, **options).compose().split('\n'))
    for first in (0, 3):
        table = make(style_name=style, **options)
        table.merge_cells(first, 0, last_column=1, value='M')
        lines = frame(table.compose().split('\n'))
        assert len({visible_width(line) for line in lines}) == 1, lines
        # The top and bottom lines keep their outer corners.
        for got, want in ((lines[0], plain[0]), (lines[-1], plain[-1])):
            if re.search(r'\w', want):
                continue  # frameless style: this is a row, not a border
            assert (got[:1], got[-1:]) == (want[:1], want[-1:]), (
                style, options, first, '\n'.join(lines))


# -- merge covering a hidden column ----------------------------------------

@pytest.mark.parametrize('hidden', [['T'], ['V'], [2]])
def test_merge_over_hidden_column_shows_its_text(hidden):
    table = make(hide_columns=hidden)
    table.merge_cells(0, 1, last_column=2, value='Merged')
    out = table.compose()
    assert 'Merged' in out
    assert '| . |' not in out
    assert len({visible_width(line) for line in out.split('\n')}) == 1


def test_merge_over_hidden_column_matches_export():
    table = make(hide_columns=['T'], style_name='ascii_rows')
    table.merge_cells(0, 1, last_column=2, value='Merged')
    (region,) = table._export_view().merges
    assert (region.first_column, region.last_column) == (1, 1)
    row = table.compose().split('\n')[3]
    assert re.fullmatch(r'\| a \| +Merged +\|', row), row


def test_merge_over_hidden_column_with_index_and_rows():
    table = make(hide_columns=['V'], show_index=True, style_name='rounded')
    table.merge_cells(1, 1, last_row=2, last_column=2, value='Total')
    out = table.compose()
    assert 'Total' in out
    assert len({visible_width(line) for line in out.split('\n')}) == 1


def test_merge_still_spanning_two_columns_does_not_widen():
    table = make(hide_columns=['N'])
    table.merge_cells(0, 0, last_column=2, value='Much longer text')
    widths = {visible_width(line) for line in table.compose().split('\n')}
    assert widths == {9}
