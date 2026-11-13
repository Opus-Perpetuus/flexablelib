"""3.5.3: index labels stay contiguous when a row_filter (or sort_by) meets
hidden empty rows; stream() sizes the index column like compose(); the
contrast checks understand every colour the core draws; colour tokens with
non-ASCII digits raise ColourError."""

import io

import pytest

from flexablelib import Table
from flexablelib.colors import ColourError, parse_spec, spec_to_css
from flexablelib.text_width import strip_ansi

ROWS = [['a'], [None], ['b'], [''], ['c'], ['zz']]


def body(table):
    """The data lines of a single-column table with an index column."""
    return [line for line in strip_ansi(str(table)).split('\n')
            if line.startswith('|') and ' h ' not in line
            and not line.startswith('| i')]


def indexed(rows=ROWS, **options):
    table = Table(headers=['h'], rows=[list(r) for r in rows])
    table.show_index = True
    table.max_width = 120
    for name, value in options.items():
        setattr(table, name, value)
    return table


class TestIndexWithFilterAndHiddenEmptyRows:
    def test_filter_keeps_numbers_contiguous(self):
        table = indexed(show_empty_rows=False,
                        row_filter=lambda row: row[0] != 'zz')
        assert body(table) == ['| 0 | a |', '| 1 | b |', '| 2 | c |']

    def test_same_numbers_as_without_filter(self):
        plain = indexed(show_empty_rows=False)
        keep_all_but_one = indexed(show_empty_rows=False,
                                   row_filter=lambda row: row[0] != 'a')
        assert [line.split('|')[1] for line in body(keep_all_but_one)] == \
            [line.split('|')[1] for line in body(plain)][:3]

    def test_sort_by_with_hidden_empty_rows(self):
        table = indexed(show_empty_rows=False, sort_by=0, sort_reverse=True)
        labels = [line.split('|')[1].strip() for line in body(table)]
        assert labels == ['0', '1', '2', '3']

    def test_roman_and_start_step(self):
        table = indexed(show_empty_rows=False, roman_index=True,
                        index_start=1, row_filter=lambda row: row[0] != 'b')
        labels = [line.split('|')[1].strip() for line in body(table)]
        assert labels == ['I', 'II', 'III']
        table = indexed(show_empty_rows=False, index_start=10, index_step=5,
                        row_filter=lambda row: row[0] != 'b')
        labels = [line.split('|')[1].strip() for line in body(table)]
        assert labels == ['10', '15', '20']

    def test_empty_rows_shown_keep_their_number(self):
        table = indexed(show_empty_rows=True,
                        row_filter=lambda row: row[0] != 'zz')
        labels = [line.split('|')[1].strip() for line in body(table)]
        assert labels == ['0', '1', '2', '3', '4']

    def test_exports_and_pages_agree(self):
        table = indexed(show_empty_rows=False,
                        row_filter=lambda row: row[0] != 'zz')
        assert [r['i'] for r in table.to_records(include_index=True)] == \
            [0, 1, 2]
        pages = table.paginate(2)
        assert '| 2 | c |' in strip_ansi(pages[-1])


class TestStreamIndexWidth:
    @pytest.mark.parametrize('roman', [False, True])
    @pytest.mark.parametrize('show_empty', [False, True])
    def test_stream_matches_compose(self, roman, show_empty):
        rows = [['x'], [None], [''], ['y']] * 3

        def make(data):
            return indexed(data, show_empty_rows=show_empty,
                           roman_index=roman)

        full = str(make(rows + rows))
        streamed = '\n'.join(make(rows).stream([list(r) for r in rows]))
        assert streamed == full

    def test_stream_with_filter_matches_compose(self):
        rows = [['x%d' % k] for k in range(12)] + [[None]]

        def keep(row):
            return row[0] is None or row[0] in ('x0', 'x1', 'x2')

        full = str(indexed(rows + rows, row_filter=keep,
                           show_empty_rows=False))
        streamed = '\n'.join(indexed(rows, row_filter=keep,
                                     show_empty_rows=False).stream(rows))
        assert streamed == full

    def test_generator_still_streams(self):
        table = indexed([['a']])
        lines = list(table.stream(iter([['b'], ['c']])))
        assert any('| 2 | c |' in strip_ansi(line) for line in lines)

    def test_bad_row_still_reported_by_add_row(self):
        table = indexed([['a']])
        lines = []
        with pytest.raises(TypeError):
            for line in table.stream([['b'], 5]):
                lines.append(line)
        # The rows before the bad one were drawn first, as they always were.
        assert any('| 1 | b |' in strip_ansi(line) for line in lines)


class TestNonAsciiDigits:
    @pytest.mark.parametrize('token', ['²', '٣', 'color:٣', 'grey٣',
                                       'on ²'])
    def test_colour_error(self, token):
        with pytest.raises(ColourError):
            parse_spec(token)

    def test_css_colour_error_or_ignored(self):
        try:
            css = spec_to_css('²')
        except ColourError:
            return
        assert css == ''

    def test_ascii_digits_still_work(self):
        assert parse_spec('93') == '\x1b[38;5;93m'
        assert parse_spec('colour:93') == '\x1b[38;5;93m'
        assert parse_spec('grey50') == '\x1b[38;5;244m'


def _a11y():
    return pytest.importorskip('flexablelib_tui.accessibility')


class TestContrastUnderstandsCoreColours:
    @pytest.mark.parametrize('token, rgb', [
        ('colour:93', (135, 0, 255)),
        ('COLOUR:93', (135, 0, 255)),
        ('color:93', (135, 0, 255)),
        ('ff8800', (255, 136, 0)),
        ('#FF8800', (255, 136, 0)),
        ('#abc', (170, 187, 204)),
        ('93', (135, 0, 255)),
        ('grey23', (58, 58, 58)),    # xterm 237, what parse_spec draws
        ('gray100', (255, 255, 255)),
        ('grey0', (0, 0, 0)),
        ('bright_white', (255, 255, 255)),
    ])
    def test_parse_color(self, token, rgb):
        assert _a11y().parse_color(token) == rgb

    @pytest.mark.parametrize('token', ['grey101', '#ab', '#gggggg', '²',
                                       '300', 'color:300', 'nope', '', None])
    def test_not_a_colour(self, token):
        assert _a11y().parse_color(token) is None

    def test_every_core_colour_is_understood(self):
        a11y = _a11y()
        tokens = (['colour:%d' % n for n in range(0, 256, 7)]
                  + ['grey%d' % n for n in range(0, 101, 3)]
                  + ['%d' % n for n in range(0, 256, 11)]
                  + ['ff8800', '#00aa11', 'bright_blue', 'gray'])
        for token in tokens:
            parse_spec(token)
            assert a11y.parse_color(token) is not None, token

    def test_grey_matches_drawn_xterm_grey(self):
        a11y = _a11y()
        for percent in range(0, 101):
            code = parse_spec('grey%d' % percent)
            index = int(code[:-1].split(';')[-1])
            assert a11y.parse_color('grey%d' % percent) == \
                a11y.parse_color('colour:%d' % index)

    def test_theme_contrast(self):
        C = pytest.importorskip('flexablelib_components')
        ratios = C.Theme(accent='black on colour:226').contrast()
        assert ratios['accent'] > 15
        assert C.Theme(accent='colour:93').contrast()['accent'] == \
            C.Theme(accent='#8700ff').contrast()['accent']
        assert C.Theme(accent='ff8800').contrast()['accent'] == \
            C.Theme(accent='#ff8800').contrast()['accent']

    def test_contrast_ratio_accepts_core_forms(self):
        a11y = _a11y()
        assert round(a11y.contrast_ratio('colour:231', 'colour:16'), 1) == 21.0
        assert round(a11y.contrast_ratio('ffffff', '000000'), 1) == 21.0


class TestAccessibilityEdges:
    def test_settings_update_and_repr(self):
        a11y = _a11y()
        settings = a11y.Settings()
        with pytest.raises(TypeError):
            settings.update(not_a_setting=True)
        settings.update(ascii=1, theme=None)
        assert settings.ascii is True
        assert repr(settings).startswith('Settings(') and 'ascii=True' in \
            repr(settings)

    def test_from_env_flags(self):
        a11y = _a11y()
        out = a11y.Settings.from_env({'FLEXABLELIB_ASCII': ' Yes ',
                                      'FLEXABLELIB_REDUCED_MOTION': '0'})
        assert out.ascii is True and out.reduced_motion is False

    def test_describe_error_and_description(self):
        a11y = _a11y()
        text = a11y.describe({'label': 'Correo', 'role': 'textbox',
                              'value': 'x', 'error': 'inválido',
                              'description': 'Tu correo de trabajo'},
                             lang='es')
        assert text.startswith('Correo')
        assert 'inválido' in text and text.endswith('Tu correo de trabajo')

    def test_announcer_closed_stream_is_quiet(self):
        a11y = _a11y()
        stream = io.StringIO()
        stream.close()
        announcer = a11y.Announcer(stream)
        announcer.announce('hola')
        assert announcer.history[-1:] and 'hola' in str(announcer.history[-1])

    def test_announcer_file_and_callable(self, tmp_path):
        a11y = _a11y()
        path = tmp_path / 'anuncios.txt'
        a11y.Announcer(str(path), prefix='» ').announce('listo')
        assert path.read_text(encoding='utf-8') == '» listo\n'
        seen = []
        a11y.Announcer(seen.append).announce('uno')
        assert seen == ['uno']
