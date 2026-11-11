"""Merges and slices must not leave stray or doubled ANSI resets."""

from flexablelib import Table
from flexablelib.text_width import sgr_is_open, slice_by_width, strip_ansi

RESET = '\x1b[0m'


def _merged(rows):
    table = Table(rows=rows, headers=['h1', 'h2'])
    table.merge_cells(0, 0, 1, 1)
    return str(table)


def test_merge_over_coloured_cell_emits_no_stray_reset():
    out = _merged([['A', 'B'], ['C', '\x1b[31mred\x1b[0m']])
    assert '\x1b' not in out
    assert 'A' in out


def test_merge_keeps_anchor_colour_closed_once():
    out = _merged([['\x1b[32mA\x1b[0m', 'B'], ['C', 'D']])
    assert out.count('\x1b[32m') == 1
    assert out.count(RESET) == 1
    assert '\x1b[32mA' + RESET in out


def test_merge_output_has_same_visible_text_as_plain():
    coloured = _merged([['\x1b[32mA\x1b[0m', 'B'], ['C', 'D']])
    plain = _merged([['A', 'B'], ['C', 'D']])
    assert strip_ansi(coloured) == plain


def test_slice_closes_open_colour():
    assert slice_by_width('\x1b[31mredred', 0, 2) == '\x1b[31mre' + RESET


def test_slice_does_not_double_an_existing_reset():
    assert slice_by_width('\x1b[31mred' + RESET + '   ', 0, 5) == (
        '\x1b[31mred' + RESET + '  ')


def test_sgr_is_open():
    assert not sgr_is_open('plain')
    assert not sgr_is_open('\x1b[31mx\x1b[0m')
    assert not sgr_is_open('\x1b[1mx\x1b[m')
    assert sgr_is_open('\x1b[31mx')
    assert sgr_is_open('\x1b[0m\x1b[1;31mx')
    assert sgr_is_open('\x1b[31mx\x1b[39m')  # partial reset counts as open
    assert not sgr_is_open('\x1b]8;;http://x\x07link\x1b]8;;\x07')


# --- reader edge cases -----------------------------------------------------

def test_from_markdown_without_pipes_gives_empty_table():
    table = Table.from_markdown('just a paragraph\nno table here\n')
    assert table.rows == []
    assert table.headers == []


def test_from_markdown_skips_prose_lines_around_table():
    text = 'Intro text\n| a | b |\n|---|--:|\n| 1 | 2 |\nOutro\n'
    table = Table.from_markdown(text)
    assert table.headers == ['a', 'b']
    assert table.rows == [[1, 2]]


def test_from_html_ignores_corrupt_embedded_payload():
    markup = (
        '<table><tr><th>x</th></tr></table>'
        '<script>\nvar DATA = {not json};\n</script>'
    )
    table = Table.from_html(markup)
    assert table.headers == ['x']
    assert table.rows == []


def test_from_html_payload_must_be_object_with_lists():
    markup = (
        '<table><tr><th>y</th></tr></table>'
        '<script>\nvar DATA = {"headers": "y", "rows": [[3]]};\n</script>'
    )
    table = Table.from_html(markup)
    assert table.headers == ['y']
    assert table.rows == []


def test_from_html_reads_valid_embedded_payload():
    markup = (
        '<table><tr><th>y</th></tr></table>'
        '<script>\nvar DATA = {"headers": ["y"], "rows": [["3"]]};\n</script>'
    )
    assert Table.from_html(markup).rows == [[3]]


def test_from_html_body_rowspan_becomes_merge():
    markup = (
        '<table><tr><th>a</th><th>b</th></tr>'
        '<tr><td rowspan="2">x</td><td>1</td></tr><tr><td>2</td></tr></table>'
    )
    table = Table.from_html(markup)
    assert table.row_count == 2
    assert len(table.merged_regions) == 1


def test_from_html_rowspan_crossing_header_is_not_merged():
    markup = (
        '<table><tr><th rowspan="2">a</th><th>b</th></tr>'
        '<tr><td>1</td></tr><tr><td>2</td><td>3</td></tr></table>'
    )
    table = Table.from_html(markup)
    assert table.headers == ['a', 'b']
    assert table.merged_regions == []
