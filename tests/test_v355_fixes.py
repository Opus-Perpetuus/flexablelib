"""3.5.5: single-line exports (Markdown, reStructuredText, AsciiDoc, LaTeX)
flatten every line break, not only '\\n'; a float column narrowed to fit
max_width never pads short numbers with zeros, and a number written with
an exponent counts whole towards how narrow its column can go."""

import io
import random

import pytest

from flexablelib import Table
from flexablelib.text_width import visible_width

BREAKS = ['\r\n', '\r', '\n', '\x0b', '\x0c', '\x1c', '\x1d', '\x1e',
          '\x85', '\u2028', '\u2029']


def table(rows, headers):
    return Table.from_records(rows, headers=headers, parse_numbers=False)


class TestLineBreaksInExports:
    @pytest.mark.parametrize('brk', BREAKS)
    def test_markdown_row_stays_one_line(self, brk):
        t = table([['a' + brk + 'b', 'z']], ['h' + brk + '1', 'k'])
        md = t.to_markdown()
        assert len(md.splitlines()) == 3
        assert md.splitlines()[2].count('|') == 3

    @pytest.mark.parametrize('brk', BREAKS)
    def test_markdown_round_trip_keeps_rows_and_columns(self, brk):
        t = table([['a' + brk + 'b', 'z'], ['c', 'd']], ['h', 'k'])
        back = Table.from_markdown(t.to_markdown(), parse_numbers=False)
        assert back.to_records() == [
            {'h': 'a b', 'k': 'z'}, {'h': 'c', 'k': 'd'},
        ]

    def test_windows_line_ending_is_one_space(self):
        t = table([['first\r\nsecond']], ['h'])
        assert 'first second' in t.to_markdown()
        assert '\r' not in t.to_markdown()

    @pytest.mark.parametrize('brk', BREAKS)
    def test_rst_grid_lines_all_same_width(self, brk):
        t = table([['a' + brk + 'b', 'z']], ['h', 'k'])
        lines = t.to_rst().splitlines()
        assert len(lines) == 5
        assert len({visible_width(line) for line in lines}) == 1

    @pytest.mark.parametrize('brk', BREAKS)
    def test_asciidoc_one_source_line_per_row(self, brk):
        t = table([['a' + brk + 'b', 'z']], ['h', 'k'])
        assert t.to_asciidoc().splitlines() == [
            '|===', '| h | k', '| a b | z', '|===',
        ]

    @pytest.mark.parametrize('brk', BREAKS)
    def test_latex_row_on_one_line(self, brk):
        t = table([['a' + brk + 'b', 'z']], ['h', 'k'])
        assert 'a b & z \\\\' in t.to_latex().splitlines()

    def test_pipes_still_escaped(self):
        t = table([['x|y\r\nw']], ['h'])
        assert '| x\\|y w |' in t.to_markdown()
        assert '| x\\|y w' in t.to_asciidoc()

    def test_csv_keeps_line_breaks_quoted(self):
        t = table([['a\r\nb', 'c\rd']], ['h', 'k'])
        back = Table.from_csv(io.StringIO(t.to_csv()), parse_numbers=False)
        assert back.to_records() == [{'h': 'a\r\nb', 'k': 'c\rd'}]

    def test_random_markdown_round_trip(self):
        rng = random.Random(355)
        alphabet = ['a', 'Z', ' ', '9', '.', '中', 'é', '|', '\\'] + BREAKS
        for _ in range(300):
            ncols = rng.randint(1, 4)
            headers = ['h%d' % i for i in range(ncols)]
            rows = [[''.join(rng.choice(alphabet)
                             for _ in range(rng.randint(0, 6)))
                     for _ in range(ncols)]
                    for _ in range(rng.randint(1, 4))]
            md = table(rows, headers).to_markdown()
            assert len(md.splitlines()) == 2 + len(rows), md
            back = Table.from_markdown(md, parse_numbers=False)
            assert len(back.to_records()) == len(rows), md


class TestFloatColumnNarrowing:
    def fitted(self, rows, headers, max_width):
        t = table(rows, headers)
        t.max_width = max_width
        return t.compose()

    def test_short_number_not_padded_with_zeros(self):
        out = self.fitted([[6.013009189981389e+16, 1.123456789],
                           [-0.5, 2.5]], ['R', 'S'], 30)
        assert '-0.5 ' in out
        assert '0.50' not in out

    def test_other_column_gives_up_decimals_instead(self):
        # R cannot narrow (the exponent keeps all its digits), so S takes
        # the whole reduction, down to the three-character column floor.
        out = self.fitted([[6.013009189981389e+16, 1.123456789],
                           [-0.5, 2.5]], ['R', 'S'], 32)
        assert '6.013009189981389e+16' in out
        assert '| 1.1 |' in out
        assert max(visible_width(line) for line in out.splitlines()) <= 32

    def test_negative_zero_keeps_its_text(self):
        rows = [[None, -1339, -6612, -1046],
                [-4.06238450900009e+16, 168, -6.013009189981389e+16, None],
                [-3.613745969155277e+16, -0.0, -0.0, -2846763.25]]
        out = self.fitted(rows, ['P', 'abcdefghijkl', 'R', 'S'], 80)
        assert '-0.000' not in out

    def test_lines_stay_aligned(self):
        out = self.fitted([[1.5e+16, 1.123456789, 'x' * 30],
                           [-0.25, 2.5, 'y']], ['A', 'B', 'C'], 40)
        assert len({visible_width(line) for line in out.splitlines()}) == 1

    def test_rounding_still_happens_when_needed(self):
        out = self.fitted([[1.123456789, 'x' * 70], [22.5, 'y']],
                          ['F', 'T'], 30)
        assert '1.123456789' not in out
        assert '22.5' in out or '23' in out or '22' in out

    def test_stream_matches_compose_after_fit(self):
        rows = [[6.013009189981389e+16, 1.123456789], [-0.5, 2.5]]
        t = table(rows, ['R', 'S'])
        t.max_width = 30
        assert '\n'.join(t.stream([])) == t.compose()

    def test_hidden_exponent_row_does_not_hold_the_column_wide(self):
        rows = [[6.013009189981389e+16, 1.5, 'x' * 40], [2.25, 2.5, 'y']]
        t = table(rows, ['R', 'S', 'T'])
        t.row_filter = lambda row: row[0] != 6.013009189981389e+16
        t.max_width = 20
        out = t.compose()
        assert 'e+16' not in out
        assert max(visible_width(line) for line in out.splitlines()) <= 20


class TestExportAlignmentSources:
    """Where Markdown and LaTeX take each column's alignment from."""

    def base(self):
        return Table.from_records([['a', 1], ['b', 2]], headers=['x', 'y'])

    def test_one_code_for_every_column(self):
        t = self.base()
        t.col_alignment = 'c'
        assert t.to_markdown().splitlines()[1] == '| :-: | :-: |'
        assert t.to_latex().splitlines()[0] == r'\begin{tabular}{cc}'

    def test_short_list_leaves_the_rest_to_the_data(self):
        t = self.base()
        t.col_alignment = ['c']
        assert t.to_markdown().splitlines()[1] == '| :-: | --: |'
        assert t.to_latex().splitlines()[0] == r'\begin{tabular}{cr}'

    def test_mapping_by_header(self):
        t = self.base()
        t.col_alignment = {'y': 'l'}
        assert t.to_markdown().splitlines()[1] == '| :-- | :-- |'
        assert t.to_latex().splitlines()[0] == r'\begin{tabular}{ll}'

    def test_merged_html_cell_takes_the_column_colour(self):
        t = self.base()
        t.column_colors = {'x': 'red'}
        t.merge_cells(0, 0, 1, 0)
        html = t._repr_html_()
        assert 'rowspan="2"' in html
        assert 'color:#' in html.split('rowspan="2"')[1].split('>')[0]
