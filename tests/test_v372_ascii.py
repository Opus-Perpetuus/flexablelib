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


class TestMarksReference:
    """The pure-Python mark extraction (used without the C package) on
    nested, unclosed and malformed marks, checked against the C one."""

    CASES = [
        F.mark_open(1) + 'ab' + F.MARK_CLOSE + 'cd',
        F.mark_open(1) + 'a' + F.mark_open(2) + '中' + F.MARK_CLOSE + 'b',
        F.mark_open(3) + 'unclosed',
        F.mark_open(4) + 'x' + F.mark_open(5) + 'y',
        'a' + F.MARK_CLOSE + 'b',                   # close with no open
        '\x1b]8970;x1\x07plain',                    # ident not a number
        '\x1b]8970;1234567890\x07ten digits',       # ident too long
        '\x1b]8970;12 no terminator',
        '\x1b[31m' + F.mark_open(7) + 'red' + F.MARK_CLOSE + '\x1b[0m',
    ]

    def test_regions(self):
        py = F._PYTHON['extract_marks']
        clean, regions = py([self.CASES[1]])
        assert clean == ['a中b']
        assert sorted(regions) == [(1, 0, 0, 4, 0), (2, 0, 1, 3, 1)]
        clean, regions = py([self.CASES[3]])
        assert clean == ['xy']
        assert sorted(regions) == [(4, 0, 0, 2, 0), (5, 0, 1, 2, 1)]
        clean, regions = py([self.CASES[5]])
        assert clean == ['plain'] and regions == []

    def test_c_matches(self):
        if not F.available():
            pytest.skip('speedups not built')
        for line in self.CASES:
            assert F._C['extract_marks']([line, 'x', line]) == \
                F._PYTHON['extract_marks']([line, 'x', line]), repr(line)


class TestExpandGraphics:
    def test_without_marks_unchanged(self):
        assert F.expand_graphics('plain') == 'plain'

    def test_finds_the_module_again_after_a_reload(self, monkeypatch):
        import sys
        import types
        line = F.GRAPHICS_MARK + '1\x07'
        monkeypatch.setattr(F, '_graphics_expander', None)
        fake = types.SimpleNamespace(expand=lambda text: 'EXPANDED')
        monkeypatch.setitem(sys.modules, 'flexablelib_tui.graphics', fake)
        assert F.expand_graphics(line) == 'EXPANDED'
        monkeypatch.delitem(sys.modules, 'flexablelib_tui.graphics')
        assert F.expand_graphics(line) == line
