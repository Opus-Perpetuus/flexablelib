"""
3.3.0 frame primitives (flexablelib._frames) and the optional C package.

The C functions must match the Python ones exactly; every check here runs on
both backends when the C package is importable.
"""

import importlib
import os
import random
import subprocess
import sys

import pytest

from flexablelib import _frames as F
from flexablelib.text_width import visible_width

HAVE_C = F.available()
BACKENDS = ['python'] + (['c'] if HAVE_C else [])

POOL = list('abc xyz-|') + [
    '\x1b[31m', '\x1b[0m', '\x1b[1;4m', '\x1b[38;5;196m', '中', '文', 'é',
    'e\u0301', '\u2764\ufe0f', '\ufe0f', '\u200d', '👍', '\t', 'ｱ', '…',
    '\x1b]8;;http://x\x1b\\', '\x1b]8;;\x07', '\x1b', '\x1b[', '\x7f',
]


def rand_text(rng, n=14):
    return ''.join(rng.choice(POOL) for _ in range(rng.randint(0, n)))


@pytest.fixture(params=BACKENDS)
def backend(request):
    F.use(request.param)
    yield request.param
    F.use('auto')


class TestBackendSwitch:
    def test_use_python_and_auto(self):
        assert F.use('python') == 'python'
        assert F.ACCELERATED is False
        assert F.visible_width is F._PYTHON['visible_width']
        expected = 'c' if HAVE_C else 'python'
        assert F.use('auto') == expected

    def test_use_rejects_unknown(self):
        with pytest.raises(ValueError):
            F.use('fortran')

    def test_use_c_without_package(self, monkeypatch):
        monkeypatch.setattr(F, '_C', None)
        with pytest.raises(ImportError, match='flexablelib\\[speed\\]'):
            F.use('c')
        assert F.use('auto') == 'python'
        monkeypatch.undo()
        F.use('auto')

    def test_env_forces_python(self):
        code = ('import flexablelib._frames as F; print(F.BACKEND)')
        env = dict(os.environ, FLEXABLELIB_FRAMES='python',
                   PYTHONPATH=os.pathsep.join(sys.path))
        out = subprocess.run([sys.executable, '-c', code], env=env,
                             capture_output=True, text=True, check=True)
        assert out.stdout.strip() == 'python'

    def test_reload_without_package(self, monkeypatch):
        monkeypatch.setitem(sys.modules, 'flexablelib_speedups', None)
        module = importlib.reload(F)
        try:
            assert module.available() is False
            assert module.BACKEND == 'python'
        finally:
            monkeypatch.undo()
            importlib.reload(F)


@pytest.mark.skipif(not HAVE_C, reason='C frame primitives not built')
class TestParity:
    """Random input through both implementations."""

    def test_text_functions(self):
        rng = random.Random(330)
        C, P = F._C, F._PYTHON
        for _ in range(20000):
            s = rand_text(rng)
            w = rng.randint(-1, 16)
            suffix = rng.choice(['', '...', '…', '>>', '\x1b[2m~\x1b[0m'])
            align = rng.choice('lrc')
            lines = [s, s + 'x', '']
            cases = [('visible_width', (s,)), ('strip_ansi', (s,)),
                     ('truncate', (s, w, suffix)), ('truncate', (s, w)),
                     ('fit_line', (s, w, align)), ('fit_line', (s, w)),
                     ('fit_lines', (lines, w, align)),
                     ('widths_of', (lines,)),
                     ('slice_columns', (s, rng.randint(-2, 12),
                                        rng.randint(-1, 12)))]
            for name, args in cases:
                assert C[name](*args) == P[name](*args), (name, args)

    def test_border_and_diff(self):
        rng = random.Random(7)
        C, P = F._C, F._PYTHON
        glyphs = list('─│┌┐└┘├┤┬┴┼')
        for _ in range(3000):
            W, H = rng.randint(0, 12), rng.randint(0, 8)
            h = bytes(rng.random() < .5 for _ in range(W * H))
            v = bytes(rng.random() < .5 for _ in range(W * H))
            assert C['border_grid'](W, H, h, v, glyphs) == \
                P['border_grid'](W, H, h, v, glyphs)
            old = [rng.choice(['a', 'b', '中', '']) for _ in
                   range(rng.randint(0, 6))]
            new = [rng.choice(['a', 'b', '中', '']) for _ in
                   range(rng.randint(0, 6))]
            for name in ('changed_lines', 'render_diff'):
                assert C[name](old, new) == P[name](old, new)

    @pytest.mark.parametrize('name,args', [
        ('visible_width', (3,)), ('strip_ansi', (None,)),
        ('widths_of', ([1],)), ('widths_of', (5,)),
        ('fit_lines', ([1], 3)), ('fit_lines', (5, 3)),
        ('truncate', (1, 3)), ('fit_line', (1, 3)),
        ('slice_columns', (1, 0, 3)), ('changed_lines', (5, [])),
        ('changed_lines', ([], 5)), ('render_diff', (5, [])),
        ('render_diff', ([], 5)), ('changed_lines', ([1], ['a'])),
        ('render_diff', ([1], ['a'])), ('render_diff', (['a'], [1])),
    ])
    def test_type_errors(self, name, args):
        with pytest.raises(TypeError):
            F._C[name](*args)

    def test_border_grid_errors(self):
        g = list('─│┌┐└┘├┤┬┴┼')
        for fn in (F._C['border_grid'], F._PYTHON['border_grid']):
            with pytest.raises(ValueError):
                fn(3, 3, b'\x00', b'\x00' * 9, g)
            with pytest.raises(ValueError):
                fn(1, 1, b'\x00', b'\x00', g[:5])
            with pytest.raises(ValueError):
                fn(1, 1, b'\x00', b'\x00', ['ab'] + g[1:])
        with pytest.raises(TypeError):
            F._C['border_grid'](1, 1, b'\x00', b'\x00', 5)
        with pytest.raises(TypeError):
            F._C['border_grid'](1, 1, b'\x00', b'\x00', [1] + g[1:])

    def test_wide_input_kinds(self):
        # 1-, 2- and 4-byte string kinds, long enough to grow buffers.
        for text in ('a' * 500, 'é' * 500, '中' * 500, '👍' * 500,
                     '\x1b[31m' + 'x' * 300 + '\x1b[0m'):
            for name, args in [('truncate', (text, 40, '…')),
                               ('fit_line', (text, 1000, 'c')),
                               ('slice_columns', (text, 3, 700)),
                               ('strip_ansi', (text,))]:
                assert F._C[name](*args) == F._PYTHON[name](*args)

    def test_render_diff_many_lines(self):
        old = ['x' * 50] * 300
        new = ['y' * 50] * 290
        assert F._C['render_diff'](old, new) == \
            F._PYTHON['render_diff'](old, new)


class TestBehaviour:
    def test_fit_line_and_truncate(self, backend):
        assert F.fit_line('abc', 5) == 'abc  '
        assert F.fit_line('abc', 5, 'r') == '  abc'
        assert F.fit_line('abc', 6, 'c') == ' abc  '
        assert F.fit_line('abcdef', 3) == 'abc'
        assert F.fit_line('中文字', 5) == '中文 '
        assert F.fit_line('abc', 0) == ''
        assert F.fit_line('abc', 3) == 'abc'
        assert F.truncate('abcdef', 4, '…') == 'abc…'
        assert F.truncate('abc', 2, '...') == '..'
        assert F.truncate('\x1b[31mabcdef', 4, '…') == \
            '\x1b[31mabc…\x1b[0m'

    def test_slice_columns(self, backend):
        assert F.slice_columns('abcdef', 2, 3) == 'cde'
        assert F.slice_columns('ab', 1, 4) == 'b   '
        assert F.slice_columns('a中b', 2, 2) == ' b'
        assert F.slice_columns('a中b', 1, 1) == ' '
        assert F.slice_columns('\x1b[31mabc\x1b[0m', 1, 1) == \
            '\x1b[31mb\x1b[0m'
        assert F.slice_columns('abc', 0, 0) == ''

    def test_border_grid_box(self, backend):
        W, H = 4, 3
        h = bytearray(W * H)
        v = bytearray(W * H)
        for x in range(3):
            h[x] = h[2 * W + x] = 1
        for y in range(2):
            v[y * W] = v[y * W + 3] = 1
        lines = F.border_grid(W, H, bytes(h), bytes(v),
                              list('─│┌┐└┘├┤┬┴┼'))
        assert lines == ['┌──┐', '│  │', '└──┘']

    def test_diff(self, backend):
        assert F.changed_lines(['a', 'b'], ['a', 'c', 'd']) == [1, 2]
        assert F.render_diff(['a', 'b'], ['a', 'c']) == '\x1b[2;1Hc\x1b[K'
        assert F.render_diff(['a', 'b'], ['a']) == '\x1b[2;1H\x1b[J'
        assert F.render_diff(['a'], ['a']) == ''

    def test_widths(self, backend):
        assert F.widths_of(['a', '中', '\x1b[1mb\x1b[0m']) == [1, 2, 1]
        assert F.visible_width('👍x') == 3
        assert F.strip_ansi('\x1b[1mb\x1b[0m') == 'b'
        assert F.fit_lines(['a', 'bb'], 2, 'r') == [' a', 'bb']

    def test_slice_is_exact_width(self, backend):
        rng = random.Random(5)
        for _ in range(2000):
            s = ''.join(rng.choice(['a', '中', '\x1b[31m', 'é', ' '])
                        for _ in range(rng.randint(0, 12)))
            w = rng.randint(1, 10)
            out = F.slice_columns(s, rng.randint(0, 8), w)
            assert visible_width(out) == w


def test_bench_tool_runs(tmp_path):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = tmp_path / 'bench.json'
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
    done = subprocess.run([sys.executable,
                           os.path.join(root, 'tools', 'bench_frames.py'),
                           '--frames', '2', '--json', str(out)],
                          env=env, capture_output=True, text=True,
                          check=True, cwd=root)
    assert 'ms/frame' in done.stdout
    assert out.exists()
