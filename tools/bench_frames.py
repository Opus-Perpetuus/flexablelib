"""
Frame benchmark: milliseconds per frame and frames per second for a full
terminal dashboard at three terminal sizes, with the pure-Python frame
primitives and with the C ones (``pip install flexablelib[speed]``).

    python tools/bench_frames.py            # both backends when available
    python tools/bench_frames.py --demo admin --json out.json
    python tools/bench_frames.py --pure     # no C anywhere (measurement too)

Each frame is a complete re-layout and redraw of examples/dashboard.py (grid
tracks, borders, titles, a table, bars, sparklines, a log) -- or, with
``--demo admin``, of the pages of examples/admin.py (components, dialogs) --
followed by the diff against the previous frame that a live screen writes to
the terminal.
"""

import argparse
import json
import os
import sys
import time

if '--pure' in sys.argv:
    # No C at all: hide the core package's measurement extension too.
    sys.modules['flexablelib._speedups'] = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'examples')] + [
    os.path.join(ROOT, 'packages', name)
    for name in ('tui', 'components', 'speedups')]

from flexablelib import _frames  # noqa: E402

import dashboard  # noqa: E402

SIZES = [(80, 24), (160, 48), (300, 80)]


class _AdminPage(object):
    """One page of examples/admin.py, rendered through its App."""

    def __init__(self, page, dialog=None):
        import admin
        from flexablelib_tui import Component
        Component.use_colors = True
        self.admin = admin.Admin()
        self.admin.shell.open_page(page)
        if dialog:
            getattr(self.admin, dialog)()

    def render(self, width, height):
        return self.admin.app.render(width, height)


def renderables_for(demo, colors=True):
    if demo == 'admin':
        return [_AdminPage(page, dialog) for page, dialog in (
            ('Resumen', None), ('Pedidos', None), ('Agenda', None),
            ('Clientes', None), ('Ajustes', None), ('Resumen', 'help'),
            ('Pedidos', 'palette'), ('Resumen', 'new_customer'))]
    return [dashboard.build('ocean', 'rounded', colors, tick)
            for tick in range(8)]


def bench(width, height, frames, colors=True, demo='dashboard'):
    renderables = renderables_for(demo, colors)
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
    parser.add_argument('--pure', action='store_true',
                        help='also disable the core C measurement code')
    parser.add_argument('--demo', choices=['dashboard', 'admin'],
                        default='dashboard')
    args = parser.parse_args(argv)
    backends = ['python'] + (['c'] if _frames.available() and
                             not args.pure else [])
    results = {}
    for backend in backends:
        _frames.use(backend)
        for width, height in SIZES:
            r = bench(width, height, args.frames, demo=args.demo)
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
