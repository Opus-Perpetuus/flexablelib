"""2.2.4: bugs found by the 30x50 style x feature stress matrix."""
import pytest

from flexablelib import Table
from flexablelib.style_compositions import __style_compositions as catalogue
from flexablelib.text_width import visible_width


def small(style):
    table = Table(rows=[[c + str(i) for c in 'abcd'] for i in range(4)],
                  headers=['h1', 'h2', 'h3', 'h4'])
    table.style_name = style
    return table


@pytest.mark.parametrize('style', catalogue._fields)
def test_divider_keeps_every_line_the_same_width(style):
    table = small(style)
    table.show_index = True
    table.add_dividers(0, 2)
    widths = {visible_width(line) for line in table.compose().split('\n')}
    assert len(widths) == 1


@pytest.mark.parametrize('style,expected', [
    ('rounded', '├────┼────┼────┼────┤'),
    ('single', '├────┼────┼────┼────┤'),
    ('double_horizontal', '╞════╪════╪════╪════╡'),
    ('dashed', '├┄┄┄┄┼┄┄┄┄┼┄┄┄┄┼┄┄┄┄┤'),
    ('rounded_double_underline_open', '├───────────────────┤'),
    ('double_frame_open_body', '╠═══════════════════╣'),
    ('ascii_double_underline_open_header', '+----+----+----+----+'),
    ('ascii_double_underline_open_body', '+-------------------+'),
    ('markdown', '|----|----|----|----|'),
    ('org', '|----+----+----+----|'),
])
def test_divider_is_drawn_with_the_style_glyphs(style, expected):
    # Used to be a run of ASCII '-' crossing the column lines.
    table = small(style)
    table.add_divider(0)
    lines = table.compose().split('\n')
    a0 = next(i for i, line in enumerate(lines) if 'a0' in line)
    assert lines[a0 + 1] == expected


def test_divider_without_column_lines_stays_dashed():
    table = small('lines_ascii')
    table.add_divider(0)
    lines = table.compose().split('\n')
    a0 = next(i for i, line in enumerate(lines) if 'a0' in line)
    assert set(lines[a0 + 1]) == {'-'}


def test_divider_skips_hidden_columns():
    table = small('rounded')
    table.hide_columns = ['h2']
    table.add_divider(0)
    lines = table.compose().split('\n')
    a0 = next(i for i, line in enumerate(lines) if 'a0' in line)
    assert lines[a0 + 1] == '├────┼────┼────┤'


@pytest.mark.parametrize('style,foreign', [
    ('tilde', set('│├┤┬┴┼─')),
    ('dotted_rows', set('│├┤┬┴┼─')),
    ('psql', set('│├┤┬┴┼─')),
])
def test_merge_junctions_use_the_style_glyphs(style, foreign):
    # ASCII '|' with '~' rules, and ':' columns, used to get light box tees.
    table = small(style)
    table.merge_cells(1, 1, 2, 2, value='M')
    table.merge_cells(3, 0, last_column=1, value='X')
    out = table.compose()
    assert not (set(out) & foreign), sorted(set(out) & foreign)
    assert len({visible_width(line) for line in out.split('\n')}) == 1


def test_stream_with_index_and_column_min_width():
    # IndexError: list index out of range.
    table = Table(rows=[[0, 'zz']], headers=['a', 'b'])
    table.show_index = True
    table.column_min_width = 5
    lines = list(table.stream([[1, 'xx'], [2, 'y']]))
    assert any('xx' in line for line in lines)
    assert len({visible_width(line) for line in lines}) == 1


def test_stream_with_index_honours_column_max_width():
    table = Table(rows=[[0, 'abcdefgh']], headers=['a', 'b'])
    table.show_index = True
    table.column_max_width = {'b': 4}
    table.overflow = 'truncate'
    lines = list(table.stream([[1, 'zzzzzzzzzz']]))
    assert len({visible_width(line) for line in lines}) == 1
    assert 'zzzzzzzzzz' not in '\n'.join(lines)


def test_from_csv_reads_csv_text():
    table = Table(rows=[['a', 'x\ny', 1], ['b', 'q,r', 2]],
                  headers=['h', 'm', 'n'])
    back = Table.from_csv(table.to_csv())
    assert back.headers == ['h', 'm', 'n']
    assert back.rows == [['a', 'x\ny', 1], ['b', 'q,r', 2]]


def test_from_csv_still_reads_a_path(tmp_path):
    path = tmp_path / 't.csv'
    path.write_text('h,n\na,1\n', encoding='utf-8')
    assert Table.from_csv(str(path)).rows == [['a', 1]]


def _int_cells(table, header_i=1):
    out = []
    for line in table.compose().split('\n'):
        parts = line.split('|')
        if len(parts) > header_i + 1 and parts[header_i].strip().isdigit():
            out.append(parts[header_i])
    return out


def test_terminal_fit_keeps_untrimmed_int_column_right_aligned():
    # Shrinking the text columns to fit used to left-align every other
    # column that went through the trim path untouched.
    table = Table(rows=[[n, 'x' * 30, 'y' * 20] for n in (0, 35, 70)],
                  headers=['a', 'b', 'c'])
    table.max_width = 40
    assert _int_cells(table) == ['  0 ', ' 35 ', ' 70 ']


def test_column_max_width_on_one_column_keeps_the_others_aligned():
    table = Table(rows=[[n, 'xxxxxx', 1.5] for n in (0, 35, 70)],
                  headers=['a', 'b', 'f'])
    table.column_max_width = {'b': 3}
    assert _int_cells(table) == ['  0 ', ' 35 ', ' 70 ']


def test_column_max_width_keeps_the_index_right_aligned():
    table = Table(rows=[[n, 'xxxxxx'] for n in range(12)], headers=['a', 'b'])
    table.show_index = True
    table.column_max_width = {'b': 3}
    cells = _int_cells(table)
    assert cells[0] == '  0 ' and cells[-1] == ' 11 '


def test_a_trimmed_int_column_still_trims():
    table = Table(rows=[[1234567, 'x']], headers=['a', 'b'])
    table.column_max_width = 3
    assert '1234567' not in table.compose()


@pytest.mark.parametrize('roman', [False, True])
def test_stream_reserves_the_index_width_for_a_sized_input(roman):
    # The index went 9 -> 10 and every line after it was one column wider.
    table = Table(headers=['a'])
    table.show_index = True
    table.roman_index = roman
    table.index_start = 1
    table.column_min_width = 3
    lines = list(table.stream([[n] for n in range(12)]))
    assert len({visible_width(line) for line in lines}) == 1
    body = [line for line in lines if line.startswith('|')][1:]
    # right-aligned like compose(), not flipped to the left
    assert body[0].split('|')[1].endswith(('1 ', 'I '))
    assert body[0].split('|')[1].startswith('  ')


def _stream_vs_compose(rows, **settings):
    from flexablelib.text_width import strip_ansi
    streamed, composed = Table(headers=['a', 'b']), Table(headers=['a', 'b'])
    for name, value in settings.items():
        setattr(streamed, name, value)
        setattr(composed, name, value)
    lines = [strip_ansi(line) for line in streamed.stream(rows)]
    for row in rows:
        composed.add_row(row)
    return lines, strip_ansi(composed.compose()).split('\n')


ROWS = [[1, 'x'], [2, 'y'], [3, 'z']]


def test_stream_with_zebra_yields_the_rows():
    # The painted bottom rule never matched, so rows were lost and the bottom
    # border came out after the header and after every row.
    lines, expected = _stream_vs_compose(
        ROWS, style_name='single', use_colors=True,
        zebra=('on blue', 'on black'))
    assert lines == expected
    assert sum(line.startswith('└') for line in lines) == 1


@pytest.mark.parametrize('settings', [
    dict(style_name='borderless', panel='double', show_headers=False),
    dict(style_name='borderless', panel='double', shadow=True, show_headers=False,
         caption='cap'),
    dict(style_name='borderless_compact', show_headers=False, shadow=True),
    dict(style_name='rounded', title='T', caption='C', panel=True,
         show_index=True),
    dict(style_name='double_header_open', use_colors=True, zebra=True,
         shadow=True, caption='c'),
])
def test_stream_matches_compose(settings):
    lines, expected = _stream_vs_compose(ROWS, **settings)
    assert lines == expected


def test_stream_with_no_headers_and_no_rows_yet():
    # column_max_width must be >= 1 or None, got 0
    table = Table(headers=['a', 'b'])
    table.show_headers = False
    assert any('1' in line for line in table.stream([[1, 2]]))


def test_title_and_caption_are_centred_on_an_empty_table():
    table = Table(headers=['a', 'b'])
    table.title = 'T'
    table.caption = 'cap'
    lines = table.compose().split('\n')
    width = visible_width(lines[1])
    assert lines[0] == ' ' * ((width - 1) // 2) + 'T'
    assert lines[-1] == ' ' * ((width - 3) // 2) + 'cap'


def test_expand_to_window_does_not_shrink_a_number_column_past_its_cap():
    # column_max_width cannot cut numbers, so the column stays wider than
    # the cap; expand_to_window used to pull it back and break the frame.
    t = Table(rows=[[v, 'x'] for v in [-0.0, 1.5e-07, 12345678901]],
              headers=['c', 'd'])
    t.column_max_width = 10
    t.expand_to_window = True
    t.max_width = 60
    for show_headers in (True, False):
        t.show_headers = show_headers
        lines = t.compose().split('\n')
        assert len({visible_width(l) for l in lines}) == 1, '\n'.join(lines)
