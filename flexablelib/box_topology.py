"""
Box-drawing topology: every arm of a grid glyph must meet a matching arm.

Used to verify merged tables: a │ must not point into a space, a ┼ must
have lines on all four sides, and a merge cap must not send a horizontal
arm into a neighbour column that has no rule.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple

from .fast import char_width, strip_ansi, visible_width
from .text_width import tokenize


# (north, south, east, west) — 1 if the glyph carries an arm that way.
_ARMS = {}
# Glyphs that can stand in for any tee (ASCII has only '+').
_SOFT = set('+')


def _reg(ch: str, n, s, e, w):
    _ARMS[ch] = (bool(n), bool(s), bool(e), bool(w))


# Light
for ch, key in {
    '─': (0, 0, 1, 1), '│': (1, 1, 0, 0),
    '┌': (0, 1, 1, 0), '┐': (0, 1, 0, 1), '└': (1, 0, 1, 0), '┘': (1, 0, 0, 1),
    '├': (1, 1, 1, 0), '┤': (1, 1, 0, 1), '┬': (0, 1, 1, 1), '┴': (1, 0, 1, 1),
    '┼': (1, 1, 1, 1),
    '╭': (0, 1, 1, 0), '╮': (0, 1, 0, 1), '╰': (1, 0, 1, 0), '╯': (1, 0, 0, 1),
}.items():
    _reg(ch, *key)

# Heavy
for ch, key in {
    '━': (0, 0, 1, 1), '┃': (1, 1, 0, 0),
    '┏': (0, 1, 1, 0), '┓': (0, 1, 0, 1), '┗': (1, 0, 1, 0), '┛': (1, 0, 0, 1),
    '┣': (1, 1, 1, 0), '┫': (1, 1, 0, 1), '┳': (0, 1, 1, 1), '┻': (1, 0, 1, 1),
    '╋': (1, 1, 1, 1),
    '┝': (1, 1, 1, 0), '┥': (1, 1, 0, 1), '┯': (0, 1, 1, 1), '┷': (1, 0, 1, 1),
    '┿': (1, 1, 1, 1),
    '┠': (1, 1, 1, 0), '┨': (1, 1, 0, 1), '┯': (0, 1, 1, 1),
    '┍': (0, 1, 1, 0), '┑': (0, 1, 0, 1), '┕': (1, 0, 1, 0), '┙': (1, 0, 0, 1),
}.items():
    _reg(ch, *key)

# Double and mixed
for ch, key in {
    '═': (0, 0, 1, 1), '║': (1, 1, 0, 0),
    '╔': (0, 1, 1, 0), '╗': (0, 1, 0, 1), '╚': (1, 0, 1, 0), '╝': (1, 0, 0, 1),
    '╠': (1, 1, 1, 0), '╣': (1, 1, 0, 1), '╦': (0, 1, 1, 1), '╩': (1, 0, 1, 1),
    '╬': (1, 1, 1, 1),
    '╒': (0, 1, 1, 0), '╓': (0, 1, 1, 0), '╕': (0, 1, 0, 1), '╖': (0, 1, 0, 1),
    '╘': (1, 0, 1, 0), '╙': (1, 0, 1, 0), '╛': (1, 0, 0, 1), '╜': (1, 0, 0, 1),
    '╞': (1, 1, 1, 0), '╟': (1, 1, 1, 0), '╡': (1, 1, 0, 1), '╢': (1, 1, 0, 1),
    '╤': (0, 1, 1, 1), '╥': (0, 1, 1, 1), '╧': (1, 0, 1, 1), '╨': (1, 0, 1, 1),
    '╪': (1, 1, 1, 1), '╫': (1, 1, 1, 1),
}.items():
    _reg(ch, *key)

# Dashed / dotted / light variants used by shipped styles
for ch in '┄┅┈┉╌╍▬−':
    _reg(ch, 0, 0, 1, 1)
for ch in '┊┋┆┇╎╏':
    _reg(ch, 1, 1, 0, 0)

# ASCII
_reg('-', 0, 0, 1, 1)
_reg('=', 0, 0, 1, 1)
_reg('~', 0, 0, 1, 1)
_reg('|', 1, 1, 0, 0)
_reg('+', 1, 1, 1, 1)

# Extra light/heavy mixed tees often produced by repairs
for ch, key in {
    '┞': (1, 1, 1, 0), '┟': (1, 1, 1, 0), '┡': (1, 1, 1, 0), '┢': (1, 1, 1, 0),
    '┩': (1, 1, 0, 1), '┪': (1, 1, 0, 1), '┦': (1, 1, 0, 1), '┧': (1, 1, 0, 1),
    '┱': (0, 1, 1, 1), '┲': (0, 1, 1, 1), '.items': (1, 0, 1, 1), '┺': (1, 0, 1, 1),
    '╀': (1, 1, 1, 1), '╁': (1, 1, 1, 1), '╂': (1, 1, 1, 1),
    '╃': (1, 1, 1, 1), '╄': (1, 1, 1, 1), '╅': (1, 1, 1, 1), '╆': (1, 1, 1, 1),
    '╇': (1, 1, 1, 1), '╈': (1, 1, 1, 1), '╉': (1, 1, 1, 1), '╊': (1, 1, 1, 1),
}.items():
    if ch != '.items':
        _reg(ch, *key)

# I typo'd one key - fix ┹
_reg('┹', 1, 0, 1, 1)


Break = Tuple[int, int, str, str, str]  # row, col, glyph, direction, neighbor


def arms(ch: str):
    """Return (n, s, e, w) or None if ``ch`` is not a grid glyph."""
    if not ch:
        return None
    return _ARMS.get(ch)


def grid(line: str) -> List[str]:
    """Visible-column list; a width-2 character occupies two cells (second '')."""
    out: List[str] = []
    for ch in strip_ansi(line):
        w = char_width(ch)
        if w <= 0:
            continue
        out.append(ch)
        if w == 2:
            out.append('')
    return out


_SGR = re.compile(r'\x1b\[([0-9;]*)m')


def _apply_sgr(params, fg, bg):
    if not params:
        return None, None
    i = 0
    n = len(params)
    while i < n:
        p = params[i]
        if p == 0:
            fg, bg = None, None
        elif p == 39:
            fg = None
        elif p == 49:
            bg = None
        elif p in (38, 48):
            kind = 'fg' if p == 38 else 'bg'
            if i + 1 < n and params[i + 1] == 2 and i + 4 < n:
                val = ('2', params[i + 2], params[i + 3], params[i + 4])
                i += 4
            elif i + 1 < n and params[i + 1] == 5 and i + 2 < n:
                val = ('5', params[i + 2])
                i += 2
            else:
                val = ('raw', p)
            if kind == 'fg':
                fg = val
            else:
                bg = val
        elif 40 <= p <= 47 or 100 <= p <= 107:
            bg = p
        elif 30 <= p <= 37 or 90 <= p <= 97:
            fg = p
        i += 1
    return fg, bg


def visible_cells(line: str):
    """List of (column, character, bg) for each visible column."""
    out = []
    i = 0
    col = 0
    fg = bg = None
    while i < len(line):
        match = _SGR.match(line, i)
        if match:
            raw = match.group(1)
            params = [int(part) if part else 0 for part in raw.split(';')] if raw else [0]
            fg, bg = _apply_sgr(params, fg, bg)
            i = match.end()
            continue
        ch = line[i]
        width = char_width(ch)
        if width <= 0:
            i += 1
            continue
        out.append((col, ch, bg))
        for _ in range(width - 1):
            out.append((col + 1, '', bg))
            col += 1
        col += width
        i += 1
    return out


def bg_runs(line: str, wanted):
    """Contiguous [start, end) column ranges whose background is ``wanted``."""
    runs = []
    start = None
    for col, _ch, bg in visible_cells(line):
        hit = (
            bg == ('2',) + wanted
            if isinstance(wanted, tuple) and len(wanted) == 3
            else bg == wanted
        )
        if hit:
            if start is None:
                start = col
        elif start is not None:
            runs.append((start, col))
            start = None
    if start is not None:
        runs.append((start, visible_width(line)))
    return runs


def check_topology(lines: Sequence[str]) -> List[Break]:
    """
    Return arm mismatches in ``lines``.

    A glyph with an arm toward a neighbour must meet a glyph with the
    opposite arm. A glyph with no arm that way must not meet an opposite
    arm. Space, text and the edge of the table have no arms.
    """
    rows = [grid(line) for line in lines]
    breaks: List[Break] = []
    # (direction, d_row, d_col, my_arm_index, neighbour_arm_index)
    dirs = (
        ('up', -1, 0, 0, 1),
        ('down', 1, 0, 1, 0),
        ('right', 0, 1, 2, 3),
        ('left', 0, -1, 3, 2),
    )
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            a = arms(ch)
            if not a:
                continue
            for name, dr, dc, mine, theirs in dirs:
                has = a[mine]
                rr, cc = r + dr, c + dc
                if 0 <= rr < len(rows) and 0 <= cc < len(rows[rr]):
                    nch = rows[rr][cc]
                    na = arms(nch)
                    n_has = bool(na and na[theirs])
                    neighbor = nch or ' '
                else:
                    # Off the canvas (including a shorter neighbouring line):
                    # a dangling arm at the edge of the table is allowed.
                    continue
                # ASCII '+' stands in for every tee, so unused arms do not
                # have to meet a neighbour. Incoming arms still match.
                if ch in _SOFT and has and not n_has:
                    continue
                if has and not n_has:
                    breaks.append((r, c, ch, name, neighbor or ''))
                elif n_has and not has:
                    breaks.append((r, c, ch, 'no-' + name, neighbor or ''))
    return breaks


def check_merge_fill(lines: Sequence[str], wanted, label: str = '') -> List[str]:
    """
    The background ``wanted`` (24-bit r,g,b or an SGR code) must form a
    single rectangle: every line that carries it has one run, all runs
    share the same [start, end), and the rows are contiguous.
    """
    problems = []
    hits = []
    for index, line in enumerate(lines):
        runs = bg_runs(line, wanted)
        if not runs:
            continue
        if len(runs) != 1:
            problems.append(
                f'{label}: line {index} has non-contiguous fill {runs}'
            )
            continue
        hits.append((index, runs[0][0], runs[0][1]))
    if not hits:
        problems.append(f'{label}: background {wanted} never appeared')
        return problems
    indexes = [i for i, _, _ in hits]
    if indexes != list(range(indexes[0], indexes[-1] + 1)):
        problems.append(f'{label}: fill rows are not a solid block {indexes}')
    spans = {(s, e) for _, s, e in hits}
    if len(spans) != 1:
        problems.append(f'{label}: fill width is not rectangular {spans}')
    return problems


def signatures(lines: Sequence[str]):
    """Set of (direction, glyph, neighbour) from ``check_topology``."""
    return {(d, ch, n) for _r, _c, ch, d, n in check_topology(lines)}


def new_breaks(merged_lines: Sequence[str], baseline_lines: Sequence[str]) -> List[Break]:
    """Breaks in ``merged_lines`` whose signature is not in the unmerged table."""
    allowed = signatures(baseline_lines)
    out = []
    for brk in check_topology(merged_lines):
        if (brk[3], brk[2], brk[4]) in allowed:
            continue
        row, _c, ch, direction, _n = brk
        if (
            ch == '|'
            and direction in ('up', 'down', 'no-up', 'no-down')
            and 0 <= row < len(merged_lines)
            and _is_markdown_separator(merged_lines[row])
        ):
            continue
        out.append(brk)
    return out


def _is_markdown_separator(line: str) -> bool:
    """'|---|---:|' style header rules must keep '|', even over a merge."""
    plain = strip_ansi(line).strip()
    return bool(plain) and plain[0] == '|' and plain[-1] == '|' and all(
        ch in '|-: ' for ch in plain
    )
