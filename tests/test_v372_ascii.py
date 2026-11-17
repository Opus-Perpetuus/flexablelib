"""3.7.2: ASCII mode -- the symbols components put in help lines and status
texts have one-column ASCII stand-ins, in the C and the Python fold alike."""

import os

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib import _frames as F  # noqa: E402
from flexablelib.text_width import strip_ansi, visible_width  # noqa: E402
from flexablelib_tui import App, accessibility as a11y  # noqa: E402


@pytest.fixture(params=['python'] + (['c'] if F.available() else []))
def frames_backend(request):
    old = F.BACKEND
    F.use(request.param)
    yield request.param
    F.use(old)


class TestAsciiFold:
    @pytest.mark.parametrize('glyph,ascii_char', [
        ('⌫', '<'), ('⌦', '>'), ('ⓘ', 'i'), ('✚', '+'), ('⏱', 'o'),
        ('⏲', 'o'), ('⏸', '='), ('⏹', '#'), ('⏺', 'o'), ('↻', 'o'),
        ('↺', 'o'), ('↗', '/'), ('↙', '/'), ('↖', '\\'), ('↘', '\\'),
    ])
    def test_new_stand_ins(self, frames_backend, glyph, ascii_char):
        assert F.ascii_fold(glyph) == ascii_char
        assert F.ascii_fold('\x1b[1m' + glyph + 'x') == \
            '\x1b[1m' + ascii_char + 'x'

    def test_every_stand_in_keeps_the_width(self):
        for cp, char in F.ASCII_FOLD.items():
            if 0x2800 <= cp <= 0x28FF:
                continue
            assert visible_width(chr(cp)) == visible_width(char) == 1, \
                hex(cp)

    def test_c_table_matches_python(self):
        header = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), 'packages', 'speedups',
            'flexablelib_speedups', '_ascii_table.h')
        text = open(header, encoding='utf-8').read()
        count = sum(1 for cp in F.ASCII_FOLD if not 0x2800 <= cp <= 0x28FF)
        assert '#define ASCII_FOLD_COUNT {0}'.format(count) in text
        for cp in (0x232B, 0x24D8, 0x271A, 0x23F1, 0x21BB):
            assert '{{0x{0:04X}, '.format(cp) in text

    def test_signature_help_line_is_ascii(self, frames_backend):
        with a11y.configure(ascii=True, screen_reader=False,
                            reduced_motion=False, focus_marker=False):
            pad = C.SignatureInput('Firma', columns=8, rows=2)
            app = App(body=pad)
            app.run(keys=[], size=(70, 8))
            frame = strip_ansi(app.render(70, 8))
        assert 'deshacer' in frame
        assert frame.isascii(), [ch for ch in frame if not ch.isascii()]

    def test_stopwatch_is_ascii_with_colours(self, frames_backend):
        with a11y.configure(ascii=True, screen_reader=False,
                            reduced_motion=False, focus_marker=False):
            watch = C.Stopwatch('Tiempo', use_colors=True)
            app = App(body=watch)
            app.run(keys=[], size=(70, 4))
            frame = strip_ansi(app.render(70, 4))
        assert '00:00' in frame
        assert frame.isascii(), [ch for ch in frame if not ch.isascii()]
