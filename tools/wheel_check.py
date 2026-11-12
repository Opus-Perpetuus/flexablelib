"""Check an installed wheel: the C extension loads and gives the same results
as the pure Python code on random input. Run by cibuildwheel on every
architecture: ``python tools/wheel_check.py core`` (flexablelib) or
``python tools/wheel_check.py speedups`` (flexablelib-speedups)."""

import platform
import random
import sys

PIECES = ['a', 'Z', '7', ' ', 'ñ', 'é', '漢', '字', '😀', '👍🏽', 'e\u0301',
          '\u200d', '\t', '│', '─', '╭', '→', '✓', '\x1b[1m', '\x1b[31m',
          '\x1b[0m', '\x1b[38;2;1;2;3m', '\x1b]8;;http://x\x1b\\', '\x1b]8;;\x1b\\']


def text(rnd, n=None):
    return ''.join(rnd.choice(PIECES) for _ in range(n or rnd.randint(0, 30)))


def check_core(rnd):
    from flexablelib import _speedups as c       # must be the compiled module
    from flexablelib import text_width as py
    from flexablelib.fast import ACCELERATED
    assert ACCELERATED, 'flexablelib C extension not active'
    for _ in range(3000):
        s = text(rnd)
        assert c.visible_width(s) == py.visible_width(s), repr(s)
        assert c.strip_ansi(s) == py.strip_ansi(s), repr(s)
        w = rnd.randint(0, 40)
        align = rnd.choice('lrc')
        assert c.pad_to_width(s, w, align) == py.pad_to_width(s, w, align), \
            (repr(s), w, align)
    batch = [text(rnd) for _ in range(50)]
    assert c.widths_of(batch) == [py.visible_width(s) for s in batch]
    return 'core: C text measurement == Python (3000 random strings)'


def check_speedups(rnd):
    from flexablelib import _frames as F, _images as I
    assert F.available() and F.use('c') == 'c', 'C frame code not active'
    assert 'c' in I.available(), 'C picture code not active'
    C = F._C
    for _ in range(1500):
        s = text(rnd)
        w = rnd.randint(0, 40)
        for name, args in (('visible_width', (s,)), ('strip_ansi', (s,)),
                           ('truncate', (s, w)), ('fit_line', (s, w)),
                           ('slice_columns', (s, rnd.randint(0, 10), w)),
                           ('ascii_fold', (s,))):
            if name in C:
                assert C[name](*args) == F._PYTHON[name](*args), (name, args)
    old = [text(rnd) for _ in range(20)]
    new = [t if rnd.random() < .6 else text(rnd) for t in old]
    assert C['render_diff'](old, new) == F._PYTHON['render_diff'](old, new)
    n = 0
    for _ in range(40):
        w, h = rnd.randint(1, 24), rnd.randint(1, 18)
        data = bytes(rnd.randrange(256) for _ in range(w * h * 4))
        nw, nh = rnd.randint(1, 30), rnd.randint(1, 30)
        assert I._C.resize(data, w, h, nw, nh) == \
            I._py_resize(data, w, h, nw, nh)
        colors = rnd.choice([2, 16, 255])
        q = I._py_quantize(data, w, h, colors, 128)
        assert I._C.quantize(data, w, h, colors, 128) == q
        assert I._C.sixel_encode(q[1], w, h, q[0]) == \
            I._py_sixel_encode(q[1], w, h, q[0])
        for mode in ('half', 'quadrant', 'sextant', 'braille', 'ascii'):
            for color in ('truecolor', '256', '16', 'none'):
                assert I._C.cells(data, w, h, mode, color, 128) == \
                    I._py_cells(data, w, h, mode, color, 128), (mode, color)
        n += 1
    return ('speedups: C frames == Python (1500 strings), C pictures == '
            'Python ({0} random pictures)'.format(n))


def main(argv):
    rnd = random.Random(2026)
    what = argv[1] if len(argv) > 1 else 'core'
    result = check_core(rnd) if what == 'core' else check_speedups(rnd)
    print('{0} [{1} {2}, Python {3}]'.format(
        result, platform.system(), platform.machine(),
        platform.python_version()))


if __name__ == '__main__':
    main(sys.argv)
