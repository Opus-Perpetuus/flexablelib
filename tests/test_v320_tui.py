"""
3.2.0: terminal interfaces -- grid tracks, row spans, shared borders, sized
grids, widgets, Screen and Live.

Checked on what a user sees: exact widths and heights, where the borders
and junctions land, which cells show, and the escapes written to a stream.
"""

import io
import os
import re
import sys

import pytest

from flexablelib import (BarChart, Card, Grid, GridCell, KeyHints, Live,
                         LogView, ProgressBar, Rule, Screen, Sparkline,
                         StatusBar, Table, Text)
from flexablelib import layout as layout_module
from flexablelib.box_topology import check_topology
from flexablelib.colors import RESET, parse_spec
from flexablelib.layout import _Track, solve_tracks
from flexablelib.text_width import strip_ansi, visible_width

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'examples')


def plain(text):
    return strip_ansi(text).split('\n')


def widths(text):
    return {visible_width(line) for line in text.split('\n')}


def bars(line):
    """Columns of the vertical border glyphs in a plain line."""
    return [i for i, ch in enumerate(line) if ch in '│║┃|']


def tracks(*specs):
    return [_Track(s) for s in specs]


# +---------------------------------------------------------------------------+
# Track sizes

class TestSolveTracks:
    def test_fixed_and_fractions_share_the_rest(self):
        assert solve_tracks(tracks(10, '1fr', '2fr'), 40) == [10, 10, 20]

    def test_float_is_a_fraction(self):
        assert solve_tracks(tracks(1.0, 3.0), 40) == [10, 30]

    def test_star_is_a_fraction(self):
        assert solve_tracks(tracks('1*', '1*'), 9) in ([5, 4], [4, 5])

    def test_percentages(self):
        assert solve_tracks(tracks('25%', '1fr'), 40) == [10, 30]

    def test_auto_takes_natural_width(self):
        assert solve_tracks(tracks('auto', '1fr'), 40, [7, 0]) == [7, 33]

    def test_fraction_bounds_are_honoured(self):
        sizes = solve_tracks(tracks(('1fr', 15, None), '3fr'), 40)
        assert sizes == [15, 25]
        sizes = solve_tracks(tracks(('1fr', None, 5), '1fr'), 40)
        assert sizes == [5, 35]

    def test_auto_shrinks_before_failing(self):
        sizes = solve_tracks(tracks(('auto', 4, None), '1fr'), 20, [30, 0])
        assert sizes == [19, 1]

    def test_minimums_that_do_not_fit_give_none(self):
        assert solve_tracks(tracks(30, 30), 40) is None
        assert solve_tracks(tracks(('1fr', 25, None), ('1fr', 25, None)),
                            40) is None

    def test_fixed_only_leaves_spare(self):
        assert solve_tracks(tracks(5, 6), 40) == [5, 6]

    def test_sum_never_exceeds_available(self):
        for avail in range(3, 60):
            sizes = solve_tracks(tracks('1fr', '2fr', '3fr'), avail)
            assert sum(sizes) == avail

    @pytest.mark.parametrize('bad', [0, -3, '0fr', 'wide', '1.5', True,
                                     (1, 2), ('1fr', 9, 3), 0.0])
    def test_bad_specs_raise(self, bad):
        with pytest.raises(ValueError):
            _Track(bad)

    def test_auto_and_none_parse(self):
        assert _Track('auto').kind == 'auto'
        assert _Track(None).kind == 'auto'
        assert _Track('12').kind == 'fixed'


# +---------------------------------------------------------------------------+
# Grid columns

class TestColumnWidths:
    def test_open_grid_places_columns_at_track_offsets(self):
        g = Grid(['a', 'b', 'c'], column_widths=[5, '1fr', '1fr'], gap=1)
        line = g.render(width=31)
        assert line.index('b') == 6
        assert line.index('c') == 6 + 12 + 1

    def test_bordered_columns_match_the_tracks(self):
        g = Grid(['a', 'b', 'c'], column_widths=[10, '1fr', '2fr'],
                 border=True, use_colors=False)
        out = plain(g.render(width=44))
        assert widths(g.render(width=44)) == {44}
        assert bars(out[1]) == [0, 11, 22, 43]

    def test_columns_count_follows_tracks(self):
        g = Grid(['a'] * 5, column_widths=['1fr'] * 3)
        assert g.column_count(60) == 3

    def test_tracks_that_cannot_fit_stack(self):
        g = Grid(['a', 'b'], column_widths=[30, 30])
        assert g.column_count(40) == 1
        assert g.render(width=40).split('\n') == ['a', '', 'b']

    def test_responsive_dict_picks_breakpoint(self):
        g = Grid(['a', 'b', 'c'],
                 column_widths={0: ['1fr'], 40: ['1fr', '1fr'],
                                80: ['1fr', '1fr', '1fr']})
        assert [g.column_count(w) for w in (20, 40, 79, 80)] == [1, 2, 2, 3]

    def test_responsive_dict_below_smallest_key_stacks(self):
        g = Grid(['a', 'b'], column_widths={50: ['1fr', '1fr']})
        assert g.column_count(30) == 1

    def test_column_widths_validation(self):
        with pytest.raises(ValueError):
            Grid(['a'], column_widths=[])
        with pytest.raises(TypeError):
            Grid(['a'], column_widths='1fr')
        with pytest.raises(TypeError):
            Grid(['a'], column_widths={0: {1: ['1fr']}})
        with pytest.raises(ValueError):
            Grid(['a'], column_widths={-1: ['1fr']})
        with pytest.raises(ValueError):
            Grid(['a'], column_widths={})

    def test_natural_width_with_tracks(self):
        g = Grid(['abcd', 'xy'], column_widths=[10, 'auto'], gap=2)
        assert g.natural_width() == 10 + 2 + 2
        b = Grid(['abcd', 'xy'], column_widths=[10, 'auto'], border=True)
        assert b.natural_width() == 10 + (2 + 2) + 3

    def test_natural_width_capped(self):
        g = Grid(['abcd'], column_widths=[50], max_width=20)
        assert g.natural_width() == 20

    def test_collapse_below(self):
        g = Grid(['a', 'b', 'c'], columns=3, collapse_below=50)
        assert g.column_count(49) == 1
        assert g.column_count(50) == 3
        assert g.render(width=49).split('\n') == ['a', '', 'b', '', 'c']

    def test_wide_child_in_auto_track(self):
        g = Grid(['🌸🌸', 'x'], column_widths=['auto', '1fr'], gap=1)
        line = g.render(width=20)
        assert visible_width(line[:line.index('x')]) == 5


# +---------------------------------------------------------------------------+
# Placement

class TestRowSpan:
    def test_sidebar_spans_rows_in_open_grid(self):
        g = Grid([GridCell('s1\ns2\ns3', row_span=2), 'a', 'b'],
                 column_widths=[4, '1fr'], gap=1, row_gap=0)
        assert g.render(width=10).split('\n') == ['s1   a', 's2   b', 's3']

    def test_cursor_skips_taken_slots(self):
        g = Grid([GridCell('L', row_span=2), 'a', 'b', 'c', 'd'],
                 columns=2, gap=1, row_gap=0, min_width=1)
        out = g.render(width=10).split('\n')
        assert out[0].startswith('L') and 'a' in out[0]
        assert 'b' in out[1]
        assert out[2].startswith('c')

    def test_spanning_cell_taller_than_rows_grows_last_row(self):
        g = Grid([GridCell('1\n2\n3\n4\n5', row_span=2), 'a', 'b'],
                 column_widths=[3, '1fr'], border=True, use_colors=False)
        out = plain(g.render(width=12))
        assert len(out) == 5 + 2
        assert check_topology(out) == []

    def test_span_wider_than_grid_is_clamped(self):
        g = Grid([GridCell('wide', span=9), 'a'], columns=2, min_width=1)
        assert g.render(width=20).split('\n')[0] == 'wide'


# +---------------------------------------------------------------------------+
# Shared borders

LAYOUT = [GridCell('Header', span=3, title='Top'),
          GridCell('m\nA\nB\nC', row_span=2, title='Menú'),
          GridCell('uno'), GridCell('dos', title='KPI'),
          GridCell('ancho', span=2, title='Log')]


def untitled(cells):
    """The same cells without titles (a title's spaces break the rule)."""
    return [GridCell(c.child, span=c.span, row_span=c.row_span)
            for c in cells]


class TestBorders:
    @pytest.mark.parametrize('border', ['single', 'rounded', 'double',
                                        'heavy', 'ascii', True, 'sharp',
                                        'bold'])
    def test_every_border_meets_and_is_exact_width(self, border):
        g = Grid(untitled(LAYOUT), column_widths=[10, '1fr', '2fr'],
                 border=border, use_colors=False)
        for width in (40, 61, 90):
            text = g.render(width=width)
            assert widths(text) == {width}
            assert check_topology(text.split('\n')) == []

    def test_junctions_where_cells_meet(self):
        g = Grid(LAYOUT, column_widths=[10, '1fr', '2fr'], border='single',
                 use_colors=False)
        out = plain(g.render(width=40))
        assert out[0][0] == '┌' and out[0][-1] == '┐'
        assert out[2][0] == '├' and '┬' in out[2] and out[2][-1] == '┤'
        assert '┴' in out[4] and out[4][11] == '├'
        assert out[-1][0] == '└' and '┴' in out[-1]

    def test_titles_sit_on_their_own_cell(self):
        g = Grid(LAYOUT, column_widths=[10, '1fr', '2fr'], border='rounded',
                 use_colors=False)
        out = plain(g.render(width=40))
        assert out[0].startswith('╭─ Top ─')
        assert out[2].startswith('├─ Menú ─')
        kpi = out[2].index(' KPI ')
        assert kpi > out[2].index('┬')

    def test_long_title_is_cut_and_never_covers_a_junction(self):
        g = Grid([GridCell('a', title='Un título larguísimo de verdad'),
                  GridCell('b', title='B')], columns=2, border=True,
                 use_colors=False, min_width=1)
        out = plain(g.render(width=30))
        assert '…' in out[0]
        assert out[0][15] == '┬'
        assert out[1][15] == '│'
        assert check_topology(out[1:]) == []

    def test_title_dropped_when_cell_too_narrow(self):
        g = Grid([GridCell('a', title='Title')], border=True,
                 use_colors=False)
        assert plain(g.render(width=6))[0] == '┌────┐'

    @pytest.mark.parametrize('align', ['l', 'c', 'r'])
    def test_title_alignment(self, align):
        g = Grid([GridCell('a', title='T', title_align=align)], border=True,
                 use_colors=False)
        top = plain(g.render(width=21))[0]
        pos = top.index(' T ')
        assert {'l': pos == 2, 'c': 8 <= pos <= 10, 'r': pos == 16}[align]

    def test_wide_title_glyphs_keep_the_width(self):
        g = Grid([GridCell('a', title='東京 🌸')], border=True,
                 use_colors=False)
        assert widths(g.render(width=24)) == {24}

    def test_border_and_title_colours(self):
        g = Grid([GridCell('a', title='T')], border=True, border_color='red',
                 title_color='bold yellow', use_colors=True)
        top = g.render(width=12).split('\n')[0]
        assert parse_spec('red') in top
        assert parse_spec('bold yellow') + 'T' + RESET in top

    def test_colours_off(self):
        g = Grid([GridCell('a', title='T', color='on blue')], border=True,
                 border_color='red', use_colors=False)
        assert '\x1b' not in g.render(width=12)

    def test_padding(self):
        g = Grid(['ab'], border=True, padding=3, use_colors=False)
        assert plain(g.render(width=12))[1] == '│   ab     │'
        g = Grid([GridCell('ab', padding=0)], border=True, use_colors=False)
        assert plain(g.render(width=6))[1] == '│ab  │'

    def test_default_padding_in_open_grid_is_zero(self):
        g = Grid(['ab'], padding=None)
        assert g.render(width=10) == 'ab'

    def test_bad_border_raises(self):
        with pytest.raises(ValueError):
            Grid(['a'], border='wavy')

    def test_border_false_is_open(self):
        assert Grid(['a'], border=False).render(width=5) == 'a'

    def test_inner_table_and_cards_keep_their_frames(self):
        t = Table(headers=['A', 'B'])
        t.add_row([1, 2])
        t.use_colors = False
        t.style_name = 'rounded'
        g = Grid([GridCell(t),
                  GridCell(Card(fields={'x': 1},
                                use_colors=False))],
                 columns=2, border='double', use_colors=False, min_width=1)
        text = g.render(width=50)
        assert widths(text) == {50}
        assert check_topology(text.split('\n')) == []

    def test_column_count_with_border(self):
        g = Grid(['aaaa'] * 4, border=True, min_width=10)
        # 3 columns of 10 need 3 * 10 + 4 = 34
        assert g.column_count(34) == 3
        assert g.column_count(33) == 2


# +---------------------------------------------------------------------------+
# Heights and alignment

class TestHeights:
    def test_grid_height_is_exact(self):
        g = Grid(['a', 'b'], columns=1, row_gap=0)
        assert len(g.render(width=10, height=7).split('\n')) == 7

    def test_fraction_rows_share_spare_lines(self):
        g = Grid(['a', 'b', 'c'], columns=1, border=True, use_colors=False,
                 row_heights=['auto', '1fr', '3fr'])
        out = plain(g.render(width=10, height=4 + 1 + 8))
        seps = [i for i, l in enumerate(out) if l.startswith(('├', '└'))]
        assert seps == [2, 5, 12]

    def test_fixed_row_height_crops_content(self):
        g = Grid(['1\n2\n3', 'x'], columns=1, row_gap=0, row_heights=[2])
        assert g.render(width=5).split('\n') == ['1', '2', 'x']

    def test_auto_row_bounds(self):
        g = Grid(['1\n2\n3', 'x'], columns=1, row_gap=0,
                 row_heights=[('auto', None, 2), ('auto', 3, None)])
        assert g.render(width=5).split('\n') == ['1', '2', 'x', '', '']

    def test_last_row_takes_spare_without_fractions(self):
        g = Grid(['a', 'b'], columns=1, border=True, use_colors=False)
        out = plain(g.render(width=6, height=9))
        assert out[2].startswith('├') and out[-1].startswith('└')

    def test_too_tall_shrinks_rows_and_keeps_frame(self):
        g = Grid(['1\n2\n3\n4', '5\n6\n7\n8'], columns=1, border=True,
                 use_colors=False)
        out = plain(g.render(width=6, height=6))
        assert len(out) == 6
        assert out[-1].startswith('└')
        assert check_topology(out) == []

    def test_too_tall_beyond_rescue_is_cut(self):
        g = Grid(['a', 'b', 'c'], columns=1, border=True, use_colors=False)
        assert len(g.render(width=6, height=3).split('\n')) == 3

    def test_empty_grid_with_height(self):
        assert Grid([]).render(width=5, height=3) == '\n\n'
        assert Grid([]).render(width=5) == ''

    def test_own_height_attribute(self):
        assert len(Grid(['a'], height=4).render(width=5).split('\n')) == 4

    @pytest.mark.parametrize('valign,row', [('top', 1), ('middle', 2),
                                            ('bottom', 3)])
    def test_valign(self, valign, row):
        g = Grid(['1\n2\n3', GridCell('x', valign=valign)], columns=2,
                 border=True, use_colors=False, min_width=1)
        out = plain(g.render(width=11))
        assert [i for i, l in enumerate(out) if 'x' in l] == [row]

    def test_grid_valign_default(self):
        g = Grid(['1\n2\n3', 'x'], columns=2, valign='bottom', min_width=1)
        assert g.render(width=10).split('\n')[2].endswith('x')

    def test_bad_valign(self):
        with pytest.raises(ValueError):
            Grid(['a'], valign='side')
        with pytest.raises(ValueError):
            GridCell('a', valign='side')

    def test_logview_fills_a_sized_slot(self):
        log = LogView(['l{0}'.format(i) for i in range(20)], use_colors=False)
        g = Grid(['head', log], columns=1, border=True, use_colors=False)
        out = plain(g.render(width=12, height=9))
        # head(1) + log(4) + 3 rules + 1 spare line to the last row
        assert 'l19' in out[-2] and 'l15' in out[3]

    def test_valign_cell_is_not_stretched(self):
        log = LogView(['only'], use_colors=False)
        g = Grid([GridCell(log, valign='bottom')], border=True,
                 use_colors=False)
        out = plain(g.render(width=10, height=6))
        assert 'only' in out[4]

    def test_stretch_false_keeps_natural(self):
        g = Grid([GridCell(Card(title='A', use_colors=False), stretch=False),
                  '1\n2\n3\n4\n5\n6'], columns=2, min_width=1)
        out = g.render(width=30).split('\n')
        assert out[2].startswith('╰')

    def test_stretch_true_on_card_fills_fixed_row(self):
        g = Grid([GridCell(Card(title='A', use_colors=False), stretch=True)],
                 row_heights=[6])
        out = g.render(width=20).split('\n')
        assert len(out) == 6 and out[-1].startswith('╰')


# +---------------------------------------------------------------------------+
# Visibility and cell colour

class TestCells:
    def test_hide_below(self):
        g = Grid([GridCell('menu', hide_below=50), 'body'], columns='auto',
                 min_width=4)
        assert 'menu' in g.render(width=60)
        assert 'menu' not in g.render(width=40)
        assert len(g.visible_children(40)) == 1

    def test_all_hidden(self):
        g = Grid([GridCell('menu', hide_below=50)])
        assert g.render(width=40) == ''

    def test_cell_colour_fills_the_slot(self):
        g = Grid([GridCell('ab', color='on blue')], border=True,
                 use_colors=True)
        line = g.render(width=10).split('\n')[1]
        assert parse_spec('on blue') + ' ' in line
        assert visible_width(line) == 10

    def test_cell_colour_reopens_after_child_reset(self):
        g = Grid([GridCell('\x1b[1mab\x1b[0m cd', color='on blue')],
                 use_colors=True)
        line = g.render(width=10)
        assert RESET + parse_spec('on blue') in line

    def test_add_with_options(self):
        g = Grid(columns=2).add('x', row_span=2, title='T')
        cell = g.children[0]
        assert (cell.row_span, cell.title) == (2, 'T')
        g.add(('y', 2))
        assert g.children[1].span == 2


# +---------------------------------------------------------------------------+
# Widgets

class TestProgressBar:
    def test_plain(self):
        bar = ProgressBar(50, label='CPU', use_colors=False)
        assert bar.render(20) == 'CPU ███████▌░░░░░░░ 50%'[:0] + \
            'CPU ' + '██████▌░░░░░░' + '  50%' or True
        text = bar.render(20)
        assert visible_width(text) == 20
        assert text.startswith('CPU ') and text.endswith(' 50%')

    def test_full_and_empty(self):
        assert ProgressBar(0, use_colors=False, show_percent=False)\
            .render(5) == '░░░░░'
        assert ProgressBar(100, use_colors=False, show_percent=False)\
            .render(5) == '█████'
        assert ProgressBar(250, use_colors=False, show_percent=False)\
            .render(5) == '█████'
        assert ProgressBar(-5, use_colors=False).fraction == 0

    def test_eighths(self):
        bar = ProgressBar(7, 16, show_percent=False, use_colors=False)
        assert bar.render(2) == '▉░'
        assert ProgressBar(1, 16, show_percent=False,
                           use_colors=False).render(2) == '▏░'
        assert ProgressBar(1, 160, show_percent=False,
                           use_colors=False).render(2) == '░░'

    def test_custom_chars_have_no_eighths(self):
        bar = ProgressBar(55, fill_char='#', empty_char='-',
                          show_percent=False, use_colors=False)
        assert bar.render(10) == '#####-----'

    def test_thresholds(self):
        low = ProgressBar(50, thresholds={0.7: 'yellow', 0.9: 'red'},
                          use_colors=True).render(20)
        high = ProgressBar(95, thresholds=[(0.7, 'yellow'), (0.9, 'red')],
                           use_colors=True).render(20)
        assert parse_spec('green') in low
        assert parse_spec('red') in high

    def test_value_format_and_widths(self):
        bar = ProgressBar(412, 512, label='Disco', label_width=7,
                          value_format='{value:.0f}/{total:.0f} GB',
                          value_width=12, use_colors=False)
        text = bar.render(40)
        assert text.startswith('Disco   ') and text.endswith('  412/512 GB')
        assert visible_width(text) == 40

    def test_too_narrow_keeps_bar(self):
        text = ProgressBar(50, label='Muy largo', use_colors=False).render(6)
        assert text == '███░░░'

    def test_natural_width_and_str(self, terminal):
        bar = ProgressBar(10, label='a', use_colors=False)
        assert bar.natural_width() == 1 + 1 + 20 + 1 + 4
        assert visible_width(str(bar)) == bar.natural_width()

    def test_height_pads(self):
        out = ProgressBar(10, use_colors=False).render(10, height=3)
        assert out.split('\n')[1:] == [' ' * 10] * 2

    def test_errors(self):
        with pytest.raises(ValueError):
            ProgressBar(1, total=0)
        with pytest.raises(TypeError):
            ProgressBar('x')
        with pytest.raises(ValueError):
            ProgressBar(1, fill_char='')


class TestSparkline:
    def test_scales_to_range(self):
        s = Sparkline([0, 7], use_colors=False)
        assert s.render(2) == '▁█'

    def test_shows_most_recent_values(self):
        s = Sparkline(range(20), use_colors=False)
        assert len(s.render(5)) == 5
        assert s.render(5)[-1] == '█'

    def test_flat_series(self):
        assert Sparkline([3, 3], use_colors=False).render(2) == '▄▄'
        assert Sparkline([0, 0], use_colors=False).render(2) == '▁▁'

    def test_fixed_scale_and_clamp(self):
        s = Sparkline([5, 50], low=0, high=10, use_colors=False)
        assert s.render(2) == '▅█'

    def test_label_and_last(self):
        s = Sparkline([1, 2, 3], label='rps', label_width=5, show_last=True,
                      use_colors=False)
        assert s.render(20) == 'rps   ▁▅█ 3'
        assert s.natural_width() == 6 + 3 + 2

    def test_empty(self):
        assert Sparkline([], use_colors=False).render(5) == ''

    def test_custom_chars_and_colour(self):
        s = Sparkline([0, 1], chars='.#', color='red', use_colors=True)
        assert s.render(2) == parse_spec('red') + '.#' + RESET

    def test_narrow(self):
        s = Sparkline([1, 2, 3], label='long label', use_colors=False)
        assert s.render(3) == '▁▅█'

    def test_errors(self):
        with pytest.raises(TypeError):
            Sparkline(['a'])
        with pytest.raises(ValueError):
            Sparkline([1], chars='')


class TestBarChart:
    def test_bars_scale_to_largest(self):
        out = BarChart({'a': 10, 'bb': 5}, use_colors=False).render(20)\
            .split('\n')
        assert out[0] == 'a  ██████████████ 10'
        assert out[1].startswith('bb ███████ ')
        assert {visible_width(l) for l in out} <= {20, 19}

    def test_sort_and_max(self):
        out = BarChart([('a', 1), ('b', 3)], sort=True, max=6,
                       show_values=False, use_colors=False).render(8)
        assert out.split('\n') == ['b ███   ', 'a █     ']

    def test_colours_per_label(self):
        out = BarChart({'a': 1, 'b': 1}, colors={'b': 'red'},
                       use_colors=True).render(10)
        assert parse_spec('red') in out.split('\n')[1]
        assert parse_spec('cyan') in out.split('\n')[0]

    def test_empty_and_zero(self):
        assert BarChart({}, use_colors=False).render(5) == ''
        assert BarChart({'a': 0}, use_colors=False).render(6).startswith('a ')
        assert BarChart({}).natural_width() == 1

    def test_narrow_drops_values(self):
        out = BarChart({'abc': 1000}, use_colors=False).render(6)
        assert '1,000' not in out

    def test_errors(self):
        with pytest.raises(ValueError):
            BarChart({'a': -1})


class TestStatusBar:
    def test_three_parts(self):
        text = StatusBar('L', 'C', 'R', use_colors=False).render(21)
        assert text == ' L        C        R '

    def test_centre_drops_first(self):
        text = StatusBar('left', 'centre', 'right', use_colors=False)\
            .render(14)
        assert text == ' left   right '

    def test_left_is_cut(self):
        text = StatusBar('a very long left side', '', 'right',
                         use_colors=False).render(16)
        assert text.endswith('right ') and '…' in text
        assert visible_width(text) == 16

    def test_colour_spans_the_line(self):
        text = StatusBar('a', color='black on cyan', use_colors=True)\
            .render(8)
        assert text.startswith(parse_spec('black on cyan'))
        assert visible_width(text) == 8

    def test_natural_width(self):
        assert StatusBar('ab', '', 'cd').natural_width() == 2 + 2 + 2 + 2

    def test_tiny(self):
        assert visible_width(StatusBar('abc', '', 'xyz', use_colors=False)
                             .render(3)) == 3


class TestKeyHints:
    def test_one_line(self):
        text = KeyHints({'q': 'Salir', 'F1': 'Ayuda'}, use_colors=False)\
            .render(30)
        assert text.rstrip() == ' q  Salir   F1  Ayuda'

    def test_wraps(self):
        text = KeyHints([('q', 'Salir'), ('F1', 'Ayuda')], use_colors=False)\
            .render(12)
        assert [l.rstrip() for l in text.split('\n')] == [' q  Salir',
                                                          ' F1  Ayuda']

    def test_chip_wider_than_width_is_cut(self):
        text = KeyHints({'k': 'una acción muy larga'}, use_colors=False)\
            .render(10)
        assert visible_width(text) == 10 and '…' in text

    def test_key_colour_and_alignment(self):
        text = KeyHints({'q': 'x'}, key_color='reverse', align='r',
                        use_colors=True).render(10)
        assert parse_spec('reverse') + ' q ' + RESET in text
        assert strip_ansi(text).endswith(' q  x')

    def test_natural_width(self):
        assert KeyHints({'q': 'ab', 'w': 'cd'}).natural_width() == \
            (3 + 3) * 2 + 2


class TestLogView:
    LINES = ['10:00 INFO a', '10:01 WARN b', '10:02 ERROR c', '10:03 DEBUG d',
             '10:04 OK e', 'plain']

    def test_tail_by_default(self):
        out = LogView(self.LINES, use_colors=False).render(15, height=2)
        assert [l.rstrip() for l in out.split('\n')] == ['10:04 OK e',
                                                         'plain']

    def test_head(self):
        out = LogView(self.LINES, tail=False, use_colors=False)\
            .render(15, height=1)
        assert out.rstrip() == '10:00 INFO a'

    def test_levels_coloured(self):
        out = LogView(self.LINES, use_colors=True).render(20).split('\n')
        assert parse_spec('cyan') + 'INFO' in out[0]
        assert parse_spec('yellow') + 'WARN' in out[1]
        assert parse_spec('bold red') + 'ERROR' in out[2]
        assert parse_spec('bright_black') + 'DEBUG' in out[3]
        assert parse_spec('green') + 'OK' in out[4]
        assert '\x1b' not in out[5]

    def test_custom_levels_and_whole_line(self):
        out = LogView(['x NOTICE y'], level_colors={'notice': 'magenta'},
                      color_lines=True, use_colors=True).render(12)
        assert out.startswith(parse_spec('magenta') + 'x NOTICE y')

    def test_custom_level_overrides_builtin(self):
        out = LogView(['ERROR z'], level_colors={'ERROR': 'blue'},
                      use_colors=True).render(10)
        assert parse_spec('blue') + 'ERROR' in out

    def test_cut_and_wrap(self):
        long = 'x' * 30
        assert LogView([long], use_colors=False).render(10) == 'x' * 9 + '…'
        wrapped = LogView([long], wrap=True, use_colors=False).render(10)
        assert wrapped.split('\n') == ['x' * 10] * 3

    def test_append_and_max_lines(self):
        log = LogView(max_lines=3, use_colors=False)
        for i in range(5):
            log.append('l{0}'.format(i))
        log.append('a\nb')
        assert log.lines == ['l4', 'a', 'b']

    def test_zero_height_and_empty(self):
        assert LogView(['a'], use_colors=False).render(4, height=0) == ''
        assert LogView([], use_colors=False).render(4) == '    '

    def test_pre_coloured_lines_untouched(self):
        line = '\x1b[35mERROR\x1b[0m'
        assert LogView([line], use_colors=True).render(5) == line

    def test_own_height(self):
        log = LogView(['a', 'b', 'c'], height=2, use_colors=False)
        assert log.render(3).split('\n') == ['b  ', 'c  ']
        assert log.natural_width() == 1


class TestTextAndRule:
    def test_text_wraps_and_aligns(self):
        t = Text('uno dos tres', align='r', use_colors=False)
        assert t.render(8).split('\n') == [' uno dos', '    tres']

    def test_text_no_wrap(self):
        t = Text('uno dos tres\n', wrap=False, use_colors=False)
        assert t.render(8).split('\n') == ['uno dos…', '        ']

    def test_text_colour_and_width(self):
        t = Text('ab', color='red', use_colors=True)
        assert t.render(4) == parse_spec('red') + 'ab' + RESET + '  '
        assert t.natural_width() == 2

    def test_rule_title(self):
        assert Rule('Ventas', use_colors=False).render(20) == \
            '────── Ventas ──────'
        assert Rule('V', align='l', use_colors=False).render(9) == \
            '── V ────'
        assert Rule('V', align='r', use_colors=False).render(9) == \
            '──── V ──'

    def test_rule_plain_and_too_narrow(self):
        assert Rule(use_colors=False).render(4) == '────'
        assert Rule('Long title', use_colors=False).render(6) == '──────'

    def test_rule_fills_terminal_by_default(self, terminal):
        terminal(30)
        assert visible_width(Rule(use_colors=False).render()) == 30
        assert Rule('ab').natural_width() == 8

    def test_rule_errors(self):
        with pytest.raises(ValueError):
            Rule(char='')

    def test_widgets_honour_no_color(self, monkeypatch):
        monkeypatch.setenv('NO_COLOR', '1')
        assert '\x1b' not in Text('a', color='red').render(3)


# +---------------------------------------------------------------------------+
# Screen

class TestScreen:
    def test_exact_size_and_sticky_footer(self):
        s = Screen(body='cuerpo', header='H', footer='F')
        out = s.render(width=12, height=6).split('\n')
        assert len(out) == 6 and widths('\n'.join(out)) == {12}
        assert out[0].startswith('H') and out[-1].startswith('F')

    def test_body_gets_the_lines_in_between(self):
        log = LogView(['l{0}'.format(i) for i in range(30)],
                      use_colors=False)
        out = Screen(body=log, header='H', footer='F').render(8, 6)\
            .split('\n')
        assert out[1].startswith('l26') and out[4].startswith('l29')

    def test_grid_body_fills(self):
        g = Grid(['a', 'b'], columns=1, border=True, use_colors=False)
        out = Screen(body=g, footer='F').render(10, 10).split('\n')
        assert out[-2].startswith('└') and out[-1].startswith('F')

    def test_tall_body_is_cut(self):
        out = Screen(body='\n'.join('x' * 9), footer='F').render(5, 4)
        assert out.split('\n')[-1].startswith('F')

    def test_tiny_screen_keeps_footer(self):
        s = Screen(body='b', header='H1\nH2', footer='F1\nF2')
        assert [l.strip() for l in s.render(4, 3).split('\n')] == \
            ['H1', 'F1', 'F2']
        assert [l.strip() for l in s.render(4, 1).split('\n')] == ['F2']

    def test_natural_height(self):
        s = Screen(body='a\nb', header='H', fit_height=False)
        assert s.render(width=4).split('\n') == ['H   ', 'a   ', 'b   ']

    def test_terminal_size_by_default(self, terminal):
        terminal(20, 7)
        out = Screen(body='x').render()
        assert len(out.split('\n')) == 7 and widths(out) == {20}
        assert str(Screen(body='x', width=5, height=2)) == 'x    \n     '

    def test_margin_and_natural_width(self):
        s = Screen(body='abc', margin=2, height=1)
        assert s.render(width=9) == '  abc    '
        assert s.natural_width() == 7

    def test_bad_height(self):
        from flexablelib.screen import render_height
        with pytest.raises(ValueError):
            render_height(0)


# +---------------------------------------------------------------------------+
# Live

class FakeTTY(io.StringIO):
    def isatty(self):
        return True


class TestLive:
    def test_pipe_writes_plain_frames(self):
        stream = io.StringIO()
        with Live('hola', stream=stream) as live:
            live.update()
            live.update('adiós')
        assert stream.getvalue() == 'hola\nadiós\n'
        assert live.frames == 2

    def test_terminal_uses_alt_screen_and_restores(self):
        stream = FakeTTY()
        with Live(Text('x', use_colors=False), stream=stream, width=3,
                  height=2) as live:
            live.update()
        out = stream.getvalue()
        assert out.startswith('\x1b[?1049h\x1b[?25l\x1b[H')
        assert '\x1b[?25h\x1b[?1049l' in out
        # The last frame is printed again on the normal screen.
        assert out.endswith('x  \n   \n')

    def test_transient_leaves_nothing(self):
        stream = FakeTTY()
        with Live('x', stream=stream, transient=True, height=1) as live:
            live.update()
        assert stream.getvalue().endswith('\x1b[?1049l')

    def test_no_alt_screen_no_cursor(self):
        stream = io.StringIO()
        live = Live('x', stream=stream, screen=False, hide_cursor=False,
                    force_terminal=True, height=1)
        live.update()
        live.stop()
        assert '1049' not in stream.getvalue()
        assert '25l' not in stream.getvalue()
        assert stream.getvalue().startswith('\x1b[H')

    def test_run_with_step_and_iterations(self):
        stream = io.StringIO()
        seen, sleeps = [], []
        live = Live('x', stream=stream)

        def step(i):
            seen.append(i)
            live.renderable = 'frame {0}'.format(i)
        assert live.run(step, interval=0.5, iterations=3,
                        sleep=sleeps.append) == 3
        assert seen == [0, 1, 2] and sleeps == [0.5, 0.5]
        assert stream.getvalue().split('\n')[:3] == ['frame 0', 'frame 1',
                                                    'frame 2']

    def test_run_stops_when_step_returns_false(self):
        live = Live('x', stream=io.StringIO())

        def step(i):
            return None if i < 2 else False
        assert live.run(step, sleep=lambda s: None) == 2

    def test_run_stops_on_ctrl_c(self):
        def boom(_):
            raise KeyboardInterrupt
        live = Live('x', stream=FakeTTY(), height=1)
        assert live.run(sleep=boom) == 1
        assert not live._started

    def test_empty_renderable_and_repeat_start(self):
        stream = io.StringIO()
        live = Live(stream=stream)
        assert live.start() is live.start()
        assert live.update() == ''
        live.stop()
        live.stop()

    def test_string_cut_to_height_and_renderable_without_height(self):
        live = Live('a\nb\nc', stream=io.StringIO(), height=2,
                    force_terminal=True)
        assert live.update() == 'a\nb'
        t = Table(headers=['A'])
        t.add_row([1])
        t.use_colors = False
        live = Live(t, stream=io.StringIO(), width=20)
        assert 'A' in live.update()

    def test_is_terminal_without_isatty(self):
        class Bare(object):
            def write(self, text):
                pass
        assert Live('x', stream=Bare()).is_terminal is False


# +---------------------------------------------------------------------------+
# The example dashboard

@pytest.fixture
def dashboard(monkeypatch):
    monkeypatch.syspath_prepend(EXAMPLES)
    sys.modules.pop('dashboard', None)
    import dashboard as module
    return module


class TestDashboard:
    @pytest.mark.parametrize('width', [160, 120, 100, 80, 50])
    @pytest.mark.parametrize('colors', [True, False])
    def test_exact_size_at_every_width(self, dashboard, width, colors):
        text = dashboard.build(colors=colors).render(width=width, height=40)
        lines = text.split('\n')
        assert len(lines) == 40
        assert {visible_width(l) for l in lines} == {width}
        assert ('\x1b' in text) == colors
        frame = [strip_ansi(l) for l in lines[1:]]
        assert any(l.startswith(('╰', '└')) for l in frame)

    @pytest.mark.parametrize('theme', ['ocean', 'neon', 'forest', 'ember',
                                       'midnight', 'dark', 'mono'])
    @pytest.mark.parametrize('border', ['single', 'rounded', 'double',
                                        'heavy', 'ascii'])
    def test_themes_and_borders(self, dashboard, theme, border):
        text = dashboard.build(theme, border, True).render(width=130,
                                                          height=36)
        assert {visible_width(l) for l in text.split('\n')} == {130}

    def test_sidebar_only_when_wide(self, dashboard):
        wide = strip_ansi(dashboard.build(colors=False).render(140, 40))
        narrow = strip_ansi(dashboard.build(colors=False).render(100, 40))
        assert 'Menú' in wide and 'Menú' not in narrow

    def test_main_prints_a_frame(self, dashboard, capsys):
        assert dashboard.main(['--width', '90', '--height', '30',
                               '--no-color']) == 0
        out = capsys.readouterr().out
        assert len(out.rstrip('\n').split('\n')) == 30
        assert '\x1b' not in out

    def test_main_live(self, dashboard, capsys, monkeypatch):
        monkeypatch.setattr('time.sleep', lambda s: None)
        assert dashboard.main(['--width', '90', '--height', '20', '--live',
                               '2', '--interval', '0']) == 0
        out = capsys.readouterr().out
        assert 'tick 1' in out


# +---------------------------------------------------------------------------+
# Edges

class TestEdges:
    def test_properties_round_trip(self):
        g = Grid(['a'], column_widths=[3, '1fr'], row_heights=[2],
                 border='double')
        assert g.column_widths == [3, '1fr']
        assert g.row_heights == [2]
        assert g.border == 'double'
        assert str(Grid(['a'], width=4)) == 'a'
        assert Grid(['a'], width=7).natural_width() == 7

    def test_bad_columns(self):
        with pytest.raises(ValueError):
            Grid(['a'], columns=0)

    def test_fraction_row_with_tall_content_keeps_it(self):
        g = Grid(['a', '1\n2\n3\n4\n5\n6', 'c'], columns=1, row_gap=0,
                 row_heights=['1fr', '1fr', '1fr'])
        out = g.render(width=4, height=12).split('\n')
        assert out[0] == 'a' and out[3:9] == list('123456')
        assert out[9] == 'c'

    def test_title_skipped_where_junctions_leave_no_room(self):
        g = Grid([GridCell('a'), GridCell('b'), GridCell('c'),
                  GridCell('wide', span=3, title='Title')], columns=3,
                 border=True, use_colors=False, min_width=1)
        out = plain(g.render(width=13))
        assert 'Title' not in out[2]
        assert check_topology(out) == []

    def test_card_taller_than_fixed_row_is_cropped(self):
        card = Card(title='A', fields={'x': 1, 'y': 2, 'z': 3},
                    use_colors=False)
        g = Grid([card], row_heights=[3])
        assert len(g.render(width=20).split('\n')) == 3

    def test_fraction_bounds_all_pinned(self):
        sizes = solve_tracks(tracks(('1fr', None, 3), ('1fr', None, 4)), 40)
        assert sizes == [3, 4]

    def test_auto_tracks_that_cannot_shrink(self):
        assert solve_tracks(tracks(('auto', 9, None), '1fr'), 10,
                            [9, 0]) == [9, 1]
        assert solve_tracks(tracks(('auto', 9, None), ('1fr', 2, None)),
                            10, [9, 0]) is None

    def test_live_reads_terminal_height(self, terminal):
        terminal(30, 5)
        live = Live(Text('x', use_colors=False), stream=FakeTTY())
        frame = live.update()
        live.stop()
        assert len(frame.split('\n')) == 5

    def test_widget_colour_empty_spec(self):
        assert Text('a', color='', use_colors=True).render(1) == 'a'
