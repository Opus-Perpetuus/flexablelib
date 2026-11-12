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
    truncate_to_width as _py_truncate,
)
# Measuring, stripping and padding go through flexablelib.fast, so the
# "python" frame backend still uses the core package's own C measurement code
# when the wheel ships it; only the per-line frame logic is Python then.
from .fast import (
    pad_to_width as _pad,
    strip_ansi as _py_strip_ansi,
    visible_width as _py_visible_width,
    widths_of as _fast_widths_of,
)

__all__ = ['ACCELERATED', 'BACKEND', 'use', 'available', 'visible_width',
           'strip_ansi', 'widths_of', 'truncate', 'fit_line', 'fit_lines',
           'slice_columns',
           'border_grid', 'changed_lines', 'render_diff', 'ascii_fold',
           'extract_marks', 'mark_open', 'MARK_CLOSE', 'GLYPH_ORDER',
           'ASCII_FOLD', 'GRAPHICS_MARK', 'expand_graphics',
           'set_graphics_expander']

# The order border_grid() expects its 11 glyphs in.
GLYPH_ORDER = ('h', 'v', 'tl', 'tr', 'bl', 'br', 'lt', 'rt', 'tt', 'bt', 'x')

# (up, down, left, right) -> index into GLYPH_ORDER, -1 for no border.
_JUNCTIONS = (-1, 0, 0, 0, 1, 2, 3, 8, 1, 4, 5, 9, 1, 6, 7, 10)


# +---------------------------------------------------------------------------+
# Pure-Python reference implementations

def _py_widths_of(texts):
    return _fast_widths_of(list(texts))


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


# +---------------------------------------------------------------------------+
# ASCII fallback: one ASCII character for each one-column symbol the
# interface draws (box drawing, blocks, braille, arrows, shapes, checks), so
# a frame keeps its exact layout on terminals without Unicode.

def _build_ascii_fold():
    table = {}

    def put(chars, ascii_char):
        for ch in chars:
            table[ord(ch)] = ascii_char
    # Box drawing U+2500-U+257F: lines, then everything else is a junction.
    for cp in range(0x2500, 0x2580):
        table[cp] = '+'
    put('─━┄┅┈┉╌╍╼╾╴╶╸╺', '-')
    put('═', '=')
    put('│┃┆┇┊┋╎╏║╽╿╵╷╹╻', '|')
    put('╱', '/')
    put('╲', '\\')
    put('╳', 'X')
    # Block elements U+2580-U+259F.
    for cp in range(0x2580, 0x25A0):
        table[cp] = '#'
    put('▁▂', '_')
    put('▃', '.')
    put('▄▀▔', '-')
    put('▅▆▋▌▐', '=')
    put('▍▎', '-')
    put('▏▕', '|')
    put('░', '.')
    put('▒', ':')
    # Geometric shapes U+25A0-U+25FF.
    for cp in range(0x25A0, 0x2600):
        table[cp] = '*'
    put('■▪▬▮', '#')
    put('□▫▭▯', 'o')
    put('▲△▴▵', '^')
    put('▶▷▸▹►▻', '>')
    put('▼▽▾▿', 'v')
    put('◀◁◂◃◄◅', '<')
    put('○◌◯◐◑◒◓◦', 'o')
    del table[0x25FD], table[0x25FE]           # two columns wide: kept
    # Arrows.
    put('←⇐⟵↤↞', '<')
    put('→⇒⟶↦↠', '>')
    put('↑⇑', '^')
    put('↓⇓', 'v')
    put('↔⇔', '-')
    put('↕⇕', '|')
    put('↵⏎↩', '<')
    # Checks, crosses, warnings, stars, ballot boxes.
    put('✔✓√', '+')
    put('✖✗✘×', 'x')
    put('⚠', '!')
    put('ℹ', 'i')
    put('★☆✦✧⭑', '*')
    put('☐', '.')
    put('☑☒', 'x')
    # Punctuation and maths.
    put('…⋯·•∙', '.')
    put('‣', '>')
    put('⁃‐‑‒–—―−', '-')
    put('‘’‚′', "'")
    put('“”„″', '"')
    put('«‹', '<')
    put('»›', '>')
    put('≤', '<')
    put('≥', '>')
    put('≠', '#')
    put('≈∼', '~')
    put('±', '+')
    put('÷', '/')
    put('°', 'o')
    put('∅', '0')
    put('∞', '8')
    put('\u00a0', ' ')
    put('¦', '|')
    put('¬', '-')
    put('€', 'E')
    put('␣', '_')
    # Braille U+2800-U+28FF (charts, spinners): by how many dots are set.
    for cp in range(0x2800, 0x2900):
        dots = bin(cp - 0x2800).count('1')
        table[cp] = ' ' if dots == 0 else '.' if dots <= 2 else \
            ':' if dots <= 5 else '#'
    return table


#: Code point -> ASCII replacement used by :func:`ascii_fold`.
ASCII_FOLD = _build_ascii_fold()


def _py_ascii_fold(text):
    """``text`` with every symbol of :data:`ASCII_FOLD` replaced by its
    one-column ASCII stand-in (escapes, letters and wide characters kept)."""
    if text.isascii():
        return text
    return text.translate(ASCII_FOLD)


# +---------------------------------------------------------------------------+
# Hit regions: zero-width marks (OSC 8970) a component puts around each of its
# lines while an app tracks the mouse. extract_marks() removes them from a
# frame and reports where every component ended up on screen.

_MARK = '\x1b]8970;'
MARK_CLOSE = _MARK + '\x07'


def mark_open(ident):
    """The mark that opens region ``ident`` (a non-negative int)."""
    return '{0}{1}\x07'.format(_MARK, ident)


def _py_extract_marks(lines):
    """
    ``(clean_lines, regions)``: the lines without marks, and one
    ``(ident, row, x0, x1, depth)`` per marked span -- columns ``[x0, x1)``
    of ``row``, ``depth`` 0 for the outermost. A span still open at the end
    of its line closes there.
    """
    out = []
    regions = []
    for row, line in enumerate(lines):
        if _MARK not in line:
            out.append(line)
            continue
        parts = []
        stack = []
        col = pos = 0
        while True:
            k = line.find(_MARK, pos)
            if k < 0:
                seg = line[pos:]
                parts.append(seg)
                col += _py_visible_width(seg)
                break
            seg = line[pos:k]
            parts.append(seg)
            col += _py_visible_width(seg)
            end = line.find('\x07', k)
            if end < 0:
                break
            ident = line[k + 7:end]
            if ident.isdigit() and ident.isascii() and len(ident) <= 9:
                stack.append((int(ident), col))
            elif not ident and stack:
                i, x0 = stack.pop()
                regions.append((i, row, x0, col, len(stack)))
            pos = end + 1
        while stack:
            i, x0 = stack.pop()
            regions.append((i, row, x0, col, len(stack)))
        out.append(''.join(parts))
    return out, regions


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
    'ascii_fold': _py_ascii_fold,
    'extract_marks': _py_extract_marks,
}


def _load_c():
    try:
        from flexablelib_speedups import _frames as module
    except ImportError:
        return None
    # An older speedups build may lack the newer functions: those stay Python.
    return {name: getattr(module, name, _PYTHON[name]) for name in _PYTHON}


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
ascii_fold = _py_ascii_fold
extract_marks = _py_extract_marks

use('python' if os.environ.get('FLEXABLELIB_FRAMES', '').lower() == 'python'
    else 'auto')


# +---------------------------------------------------------------------------+
# Pictures: frames carry a zero-width mark (ESC ] 8971 ; id BEL) where a
# picture goes; flexablelib_tui.graphics registers the function that turns
# marks into kitty / iTerm2 / sixel sequences when a frame is printed.

GRAPHICS_MARK = '\x1b]8971;'
_graphics_expander = None


def set_graphics_expander(function):
    """Install the function :func:`expand_graphics` calls (or ``None``)."""
    global _graphics_expander
    _graphics_expander = function


def expand_graphics(text):
    """``text`` with picture marks expanded, when a picture module is
    loaded and the text has any; otherwise ``text`` unchanged."""
    if GRAPHICS_MARK not in text:
        return text
    function = _graphics_expander
    if function is None:
        # This module may have been reloaded after the picture module
        # registered itself: find it again.
        import sys
        module = sys.modules.get('flexablelib_tui.graphics')
        if module is None:
            return text
        function = module.expand
    return function(text)
