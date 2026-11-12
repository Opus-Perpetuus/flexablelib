"""Time the picture primitives in pure Python and in C
(``flexablelib-speedups``): ``python tools/bench_images.py``.

A 640x400 RGBA picture is resized to 320x200 (the size a 40-column picture
needs for sixel at 8x16 px cells), quantized to 255 colours, encoded as
sixel and drawn as half blocks / braille for an 80x24 area. Best of 5."""

import sys
import time

from flexablelib import _images as I


def picture(w=640, h=400):
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out += bytes(((x * 255) // w, (y * 255) // h,
                          ((x ^ y) * 3) & 255, 255))
    return I.Bitmap(w, h, out)


def best(fn, repeat=5):
    times = []
    for _ in range(repeat):
        t = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t)
    return min(times) * 1000


def run():
    src = picture()
    small = I.scale(src, 320, 200)
    pal, idx = I.quantize(small.data, 320, 200, 255, 128)
    half = I.scale(src, 80, 48)
    brl = I.scale(src, 160, 96)
    cases = [
        ('resize 640×400 → 320×200',
         lambda: I.resize(src.data, 640, 400, 320, 200)),
        ('quantize 320×200, 255 colours',
         lambda: I.quantize(small.data, 320, 200, 255, 128)),
        ('sixel encode 320×200',
         lambda: I.sixel_encode(idx, 320, 200, pal)),
        ('half blocks 80×24 (truecolor)',
         lambda: I.cells(half.data, 80, 48, 'half', 'truecolor', 128)),
        ('braille 80×24 (mono)',
         lambda: I.cells(brl.data, 160, 96, 'braille', 'none', 128)),
    ]
    results = []
    for name, fn in cases:
        row = [name]
        for backend in ('python', 'c'):
            if backend not in I.available():
                row.append(None)
                continue
            I.use(backend)
            row.append(best(fn, 3 if backend == 'python' else 5))
        results.append(row)
    I.use('auto')
    return results


def main():
    results = run()
    print('| Operation | Python | C | Speed-up |')
    print('| --- | ---: | ---: | ---: |')
    for name, py, c in results:
        if c is None:
            print('| {0} | {1:.1f} ms | – | – |'.format(name, py))
        else:
            print('| {0} | {1:.1f} ms | {2:.2f} ms | {3:.0f}× |'.format(
                name, py, c, py / c))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
