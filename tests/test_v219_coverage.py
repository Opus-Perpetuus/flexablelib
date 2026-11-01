"""Behaviour tests for public paths the suite did not exercise yet."""
import io
import os

import pytest

from flexablelib import Table
from flexablelib.colors import (
    ColourError, colorize, parse_spec, strip_if_unsupported, supports_color,
)


# --- writers -----------------------------------------------------------------

def test_to_latex_escapes_every_special_character():
    t = Table(rows=[['a\\b&c%d$e#f_g{h}i~j^k|l<m>n', 1.5], ['x\ny', 2]],
              headers=['t_1', 'n'])
    out = t.to_latex()
    assert out.splitlines()[0] == r'\begin{tabular}{lr}'
    assert r't\_1 & n \\' in out
    assert (r'a\textbackslash{}b\&c\%d\$e\#f\_g\{h\}i\textasciitilde{}'
            r'j\textasciicircum{}k\textbar{}l\textless{}m\textgreater{}n'
            r' & 1.5 \\') in out
    assert r'x y & 2 \\' in out


def test_text_exports_of_an_empty_table():
    t = Table()
    assert t.to_latex() == ''
    assert t.to_asciidoc() == ''


def test_to_asciidoc_escapes_pipes():
    t = Table(rows=[['a|b', None]], headers=['h', 'n|m'])
    assert t.to_asciidoc().splitlines() == [
        '|===', '| h | n\\|m', '| a\\|b | ', '|===',
    ]


@pytest.mark.parametrize('method', ['to_csv', 'to_html'])
def test_exports_write_to_handles_and_paths(tmp_path, method):
    t = Table(rows=[['a', 1]], headers=['x', 'y'])
    expected = getattr(t, method)()
    handle = io.StringIO()
    assert getattr(t, method)(handle) is None
    assert handle.getvalue() == expected
    path = tmp_path / 'out.txt'
    assert getattr(t, method)(str(path)) is None
    # CSV keeps its own \r\n; HTML is text and follows the platform.
    with open(path, encoding='utf-8',
              newline='' if method == 'to_csv' else None) as handle:
        assert handle.read() == expected


# --- readers -----------------------------------------------------------------

def test_from_csv_delimiter_dialect_and_empty():
    t = Table.from_csv(io.StringIO('a;b\n1;2\n'), delimiter=';')
    assert t.headers == ['a', 'b'] and t.to_records() == [{'a': 1, 'b': 2}]
    t = Table.from_csv(io.StringIO('a\tb\n1\t2\n'), dialect='excel-tab')
    assert t.to_records() == [{'a': 1, 'b': 2}]
    assert Table.from_csv(io.StringIO('')).headers == []


def test_from_markdown_alignment_row_and_short_rows():
    t = Table.from_markdown('| a | b | c |\n|:-|:-:|-:|\n| 1 | x |\n')
    assert t.col_alignment == ['l', 'c', 'r']
    assert t.to_records() == [{'a': 1, 'b': 'x', 'c': ''}]


def test_from_markdown_reads_a_file(tmp_path):
    path = tmp_path / 't.md'
    path.write_text('| a |\n| - |\n| 1 |\n', encoding='utf-8')
    assert Table.from_markdown(str(path)).to_records() == [{'a': 1}]


def test_from_excel_sheet_selection_and_merges(tmp_path):
    pytest.importorskip('openpyxl')
    t = Table(rows=[['a', 1], ['b', 2], ['c', 3]], headers=['n', 'v'])
    t.merge_cells(0, 0, 1, 0)
    path = str(tmp_path / 't.xlsx')
    t.to_excel(path)
    by_name = Table.from_excel(path, sheet='Sheet1')
    by_index = Table.from_excel(path, sheet=0)
    assert by_name.headers == by_index.headers == ['n', 'v']
    assert [r['v'] for r in by_name.to_records()] == [1, 2, 3]
    region = by_name.merged_regions[0]
    assert (region.first_row, region.last_row) == (0, 1)
    raw = Table.from_excel(path, has_header=False)
    assert raw.headers == ['column 1', 'column 2']
    assert raw.row_count == 4


def test_from_pandas_missing_values_series_and_index():
    pd = pytest.importorskip('pandas')
    frame = pd.DataFrame({'a': [1.0, float('nan'), 3.0], 'b': ['x', None, 'z']})
    t = Table.from_pandas(frame)
    assert t.headers == ['a', 'b']
    assert 'nan' not in t.compose() and 'None' not in t.compose()
    s = Table.from_pandas(frame['a'], include_index=True)
    assert s.headers == ['index', 'a']
    assert s.row_count == 3


# --- colours -----------------------------------------------------------------

@pytest.mark.parametrize('spec, expected', [
    ('bold red on white', '\x1b[1;31;47m'),
    ('#ff8800', '\x1b[38;2;255;136;0m'),
    ('on blue', '\x1b[44m'),
    ('grey50', '\x1b[38;5;244m'),
    ('color:196', '\x1b[38;5;196m'),
    (42, '\x1b[38;5;42m'),
    ('', ''),
    (None, ''),
])
def test_parse_spec_forms(spec, expected):
    assert parse_spec(spec) == expected


@pytest.mark.parametrize('spec', ['chartreuse-ish', 'color:300', '300', 'grey101'])
def test_parse_spec_rejects_bad_colours(spec):
    with pytest.raises(ColourError):
        parse_spec(spec)


def test_colorize_is_a_no_op_without_spec():
    assert colorize('x', None) == 'x'
    assert colorize('x', 'red') == '\x1b[31mx\x1b[0m'


class _Stream:
    def __init__(self, tty):
        self._tty = tty

    def isatty(self):
        if self._tty is None:
            raise ValueError('closed')
        return self._tty


def test_supports_color_environment(monkeypatch):
    for var in ('NO_COLOR', 'FORCE_COLOR', 'TERM'):
        monkeypatch.delenv(var, raising=False)
    assert supports_color(_Stream(True)) is True
    assert supports_color(_Stream(False)) is False
    assert supports_color(_Stream(None)) is False
    assert supports_color(object()) is False
    monkeypatch.setenv('TERM', 'dumb')
    assert supports_color(_Stream(True)) is False
    monkeypatch.setenv('FORCE_COLOR', '1')
    assert supports_color(_Stream(False)) is True
    monkeypatch.setenv('NO_COLOR', '')
    assert supports_color(_Stream(True)) is False


def test_strip_if_unsupported(monkeypatch):
    monkeypatch.setenv('NO_COLOR', '1')
    assert strip_if_unsupported('\x1b[31mx\x1b[0m') == 'x'
    monkeypatch.delenv('NO_COLOR')
    monkeypatch.setenv('FORCE_COLOR', '1')
    assert strip_if_unsupported('\x1b[31mx\x1b[0m') == '\x1b[31mx\x1b[0m'
