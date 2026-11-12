"""
Frame benchmark: milliseconds per frame and frames per second for a full
terminal dashboard at three terminal sizes, with the pure-Python frame
primitives and with the C ones (``pip install flexablelib[speed]``).

    python tools/bench_frames.py            # both backends when available
    python tools/bench_frames.py --json out.json

Each frame is a complete re-layout and redraw of examples/dashboard.py (grid
tracks, borders, titles, a table, bars, sparklines, a log) followed by the diff
against the previous frame that a live screen writes to the terminal.
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'examples')]

from flexablelib import _frames  # noqa: E402

import dashboard  # noqa: E402

SIZES = [(80, 24), (160, 48), (300, 80)]


def bench(width, height, frames, colors=True):
    renderables = [dashboard.build('ocean', 'rounded', colors, tick)
                   for tick in range(8)]
    previous = []
    best = None
    diff_bytes = 0
    for _ in range(3):               # best of three runs
        start = time.perf_counter()
        for i in range(frames):
            screen = renderables[i % len(renderables)]
            lines = screen.render(width=width, height=height).split('\n')
            out = _frames.render_diff(previous, lines)
            diff_bytes += len(out)
            previous = lines
        elapsed = (time.perf_counter() - start) / frames
        best = elapsed if best is None else min(best, elapsed)
    return {'ms': best * 1000.0, 'fps': 1.0 / best,
            'diff_bytes': diff_bytes // (3 * frames)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--frames', type=int, default=40)
    parser.add_argument('--json')
    args = parser.parse_args(argv)
    backends = ['python'] + (['c'] if _frames.available() else [])
    results = {}
    for backend in backends:
        _frames.use(backend)
        for width, height in SIZES:
            r = bench(width, height, args.frames)
            results['{0}x{1}/{2}'.format(width, height, backend)] = r
            print('{0:>7}  {1:<6}  {2:7.2f} ms/frame  {3:7.1f} fps  '
                  '{4:>7} B diff'.format('{0}x{1}'.format(width, height),
                                         backend, r['ms'], r['fps'],
                                         r['diff_bytes']))
    _frames.use('auto')
    if args.json:
        with open(args.json, 'w') as handle:
            json.dump(results, handle, indent=2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
