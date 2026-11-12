"""
Frame primitives: the per-line work of drawing a terminal interface.

Every frame of a layout or a live interface comes down to a handful of string
operations repeated for each line of each cell: measure the visible width, cut
what overflows, pad to an exact width, draw the box-drawing borders where cells
meet, and -- for a live screen -- find the lines that changed since the last
frame so only those are written.

This module is the single front door for them. With the optional C package
installed (``pip install flexablelib[speed]``, which brings in
``flexablelib-speedups``) the functions here are the C ones; without it they
are the pure-Python definitions below. Both give identical results, and the
test suite checks them against each other on random input.

``FLEXABLELIB_FRAMES=python`` in the environment forces the Python versions,
and :func:`use` switches at run time (for benchmarks and tests).
"""

import os

from .text_width import (
    measured_clusters as _clusters,
    tokenize as _tokenize,
    pad_to_width as _pad,
    strip_ansi as _py_strip_ansi,
    truncate_to_width as _py_truncate,
    visible_width as _py_visible_width,
)

__all__ = ['ACCELERATED', 'BACKEND', 'use', 'available', 'visible_width',
           'strip_ansi', 'widths_of', 'truncate', 'fit_line', 'fit_lines',
           'slice_columns',
           'border_grid', 'changed_lines', 'render_diff', 'GLYPH_ORDER']

# The order border_grid() expects its 11 glyphs in.
GLYPH_ORDER = ('h', 'v', 'tl', 'tr', 'bl', 'br', 'lt', 'rt', 'tt', 'bt', 'x')

# (up, down, left, right) -> index into GLYPH_ORDER, -1 for no border.
_JUNCTIONS = (-1, 0, 0, 0, 1, 2, 3, 8, 1, 4, 5, 9, 1, 6, 7, 10)


# +---------------------------------------------------------------------------+
# Pure-Python reference implementations

def _py_widths_of(texts):
    return [_py_visible_width(t) for t in texts]


def _py_fit_line(text, width, align='l'):
    if _py_visible_width(text) > width:
        text = _py_truncate(text, width, '')
    return _pad(text, width, align)


def _py_fit_lines(lines, width, align='l'):
    return [_py_fit_line(line, width, align) for line in lines]


def _py_slice_columns(text, start, width):
    """
    Visible columns ``[start, start + width)`` of ``text``, exactly ``width``
    wide: escapes up to the end are kept (so colours carry over), a wide
    character cut by either edge becomes spaces, and a reset closes the slice
    when it holds an escape.
    """
    if width <= 0:
        return ''
    end = start + width
    out = []
    col = produced = 0
    saw = False
    for kind, value in _tokenize(text):
        if col >= end:
            break
        if kind == 'ansi':
            out.append(value)
            saw = True
            continue
        for cluster, w in _clusters(value):
            if col >= end:
                break
            if col >= start:
                if col + w <= end:
                    out.append(cluster)
                    produced += w
                else:
                    out.append(' ' * (end - col))
                    produced += end - col
            elif col + w > start:
                n = min(col + w, end) - start
                out.append(' ' * n)
                produced += n
            col += w
    if produced < width:
        out.append(' ' * (width - produced))
    if saw:
        out.append('\x1b[0m')
    return ''.join(out)


def _py_border_grid(width, height, horiz, vert, glyphs):
    if width < 0 or height < 0 or len(horiz) < width * height \
            or len(vert) < width * height:
        raise ValueError('edge buffers must hold width*height bytes')
    glyphs = list(glyphs)
    if len(glyphs) != 11 or any(len(g) != 1 for g in glyphs):
        raise ValueError('glyphs must hold 11 one-character strings')
    out = []
    table = [' ' if k < 0 else glyphs[k] for k in _JUNCTIONS]
    for y in range(height):
        row = y * width
        above = row - width
        line = []
        for x in range(width):
            key = 0
            if y and vert[above + x]:
                key |= 8
            if vert[row + x]:
                key |= 4
            if x and horiz[row + x - 1]:
                key |= 2
            if horiz[row + x]:
                key |= 1
            line.append(table[key])
        out.append(''.join(line))
    return out


def _py_changed_lines(old, new):
    n_old = len(old)
    return [i for i, line in enumerate(new) if i >= n_old or old[i] != line]


def _py_render_diff(old, new):
    parts = []
    for i in _py_changed_lines(old, new):
        parts.append('\x1b[{0};1H{1}\x1b[K'.format(i + 1, new[i]))
    if len(new) < len(old):
        parts.append('\x1b[{0};1H\x1b[J'.format(len(new) + 1))
    return ''.join(parts)


_PYTHON = {
    'visible_width': _py_visible_width,
    'strip_ansi': _py_strip_ansi,
    'widths_of': _py_widths_of,
    'truncate': _py_truncate,
    'fit_line': _py_fit_line,
    'fit_lines': _py_fit_lines,
    'slice_columns': _py_slice_columns,
    'border_grid': _py_border_grid,
    'changed_lines': _py_changed_lines,
    'render_diff': _py_render_diff,
}


def _load_c():
    try:
        from flexablelib_speedups import _frames as module
    except ImportError:
        return None
    return {name: getattr(module, name) for name in _PYTHON}


_C = _load_c()


def available():
    """Whether the C frame primitives are installed."""
    return _C is not None


def use(backend='auto'):
    """
    Pick the implementation: ``'c'``, ``'python'`` or ``'auto'`` (C when
    installed). Returns the backend now in use. Asking for ``'c'`` without the
    package installed raises ImportError with the install command.
    """
    global ACCELERATED, BACKEND
    if backend not in ('auto', 'c', 'python'):
        raise ValueError("backend must be 'auto', 'c' or 'python'")
    if backend == 'c' and _C is None:
        raise ImportError('the C frame primitives are not installed; '
                          'pip install "flexablelib[speed]"')
    chosen = _C if backend != 'python' and _C is not None else _PYTHON
    globals().update(chosen)
    ACCELERATED = chosen is _C
    BACKEND = 'c' if ACCELERATED else 'python'
    return BACKEND


ACCELERATED = False
BACKEND = 'python'
visible_width = _py_visible_width
strip_ansi = _py_strip_ansi
widths_of = _py_widths_of
truncate = _py_truncate
fit_line = _py_fit_line
fit_lines = _py_fit_lines
slice_columns = _py_slice_columns
border_grid = _py_border_grid
changed_lines = _py_changed_lines
render_diff = _py_render_diff

use('python' if os.environ.get('FLEXABLELIB_FRAMES', '').lower() == 'python'
    else 'auto')
