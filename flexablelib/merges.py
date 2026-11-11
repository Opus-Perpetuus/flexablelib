"""
MERGED CELLS

A merge makes one rectangular block of cells render as a single cell, spanning
columns, rows, or both.

The merge is applied to the finished table string rather than threaded through
the measuring pipeline. That pipeline sizes each column independently, which is
what makes decimal-point alignment and terminal fitting work; making a column's
width depend on a cell that belongs to several columns at once would put a
cycle in it. Rewriting the assembled lines keeps the measurement honest -- the
columns are still sized by their own unmerged content -- and the merge becomes
a presentation step that cannot affect layout correctness.

The consequence is that a merged region never widens the table. Content longer
than the span it was given is truncated, not accommodated.
"""

import operator
import re
from typing import List, NamedTuple, Optional

from .colors import colorize
from .text_width import sgr_is_open
from .fast import (
    has_ansi,
    pad_to_width,
    partition_by_width,
    slice_by_width,
    strip_ansi,
    strip_by_width,
    truncate_to_width,
    visible_width,
)

# Painting over a stretch of line can remove the escape that closed a colour --
# the reset ending a coloured border, say, when the merge starts just after it.
# The replacement then inherits a colour nobody asked for. Opening the painted
# span with a reset of its own costs nothing on a plain table, because it is
# only added where escapes were actually removed.
_RESET = '\x1b[0m'


def _repaint(line, start, end, replacement):
    """Replace the visible columns [start, end) of a line, ending any colour."""
    before, removed, after = partition_by_width(line, start, end)
    if (has_ansi(removed) and sgr_is_open(before)
            and not replacement.startswith(_RESET)):
        replacement = _RESET + replacement
    # The removed span often keeps its trailing RESET, which partition leaves
    # at the start of `after`. If the replacement already closed its colour,
    # that leftover is a doubled reset (`ESC[0mESC[0m`).
    if replacement.endswith(_RESET):
        while after.startswith(_RESET):
            after = after[len(_RESET):]
    elif after.startswith(_RESET) and not sgr_is_open(before + replacement):
        after = after[len(_RESET):]
    return before + replacement + after


class MergedRegion(NamedTuple):
    """
    One rectangular block of cells rendered as a single cell.

    Coordinates are inclusive and zero-based, in the table's own row and
    column numbering -- the index column, when shown, is not counted.

    ``color`` is an optional colour spec (same language as ``column_colors`` /
    ``row_colors``). When set, the whole painted span -- text, padding and
    blank continuation lines -- carries that background so a merge reads as
    one solid fill rather than a dark hole.
    """

    first_row: int
    first_column: int
    last_row: int
    last_column: int
    value: Optional[str]
    align: str
    color: Optional[str] = None

    @property
    def row_count(self) -> int:
        return self.last_row - self.first_row + 1

    @property
    def column_count(self) -> int:
        return self.last_column - self.first_column + 1

    def covers(self, row: int, column: int) -> bool:
        return (self.first_row <= row <= self.last_row
                and self.first_column <= column <= self.last_column)

    def overlaps(self, other: 'MergedRegion') -> bool:
        return not (
            self.last_row < other.first_row
            or other.last_row < self.first_row
            or self.last_column < other.first_column
            or other.last_column < self.first_column
        )


def normalise(first_row, first_column, last_row, last_column, value, align,
              row_count, column_count, existing, color=None):
    """
    Validate a merge request and turn it into a MergedRegion.

    Accepts the corners in either order, so callers may give them the way they
    think of them. Raises ValueError on anything that cannot be rendered: a
    single cell, coordinates outside the table, an unknown alignment, or an
    overlap with a merge already in place.
    """
    # Coordinates are indexes. ``operator.index`` accepts ints and integer
    # types such as numpy's, and turns anything else -- a float, or a
    # ``(row, column)`` pair given where a single number goes -- into a
    # TypeError naming the argument, instead of a comparison error from
    # deep inside the validation or the renderer.
    coordinates = []
    for name, coordinate in (('first_row', first_row),
                             ('first_column', first_column),
                             ('last_row', last_row),
                             ('last_column', last_column)):
        try:
            coordinates.append(operator.index(coordinate))
        except TypeError:
            raise TypeError(
                f'{name} must be an integer, not '
                f'{type(coordinate).__name__} ({coordinate!r})'
            ) from None
    first_row, first_column, last_row, last_column = coordinates

    first_row, last_row = sorted((first_row, last_row))
    first_column, last_column = sorted((first_column, last_column))

    if first_row < 0 or first_column < 0:
        raise ValueError('merge coordinates cannot be negative')
    if last_row >= row_count:
        raise ValueError(
            f'last_row {last_row} is outside the table, which has '
            f'{row_count} row(s)'
        )
    if last_column >= column_count:
        raise ValueError(
            f'last_column {last_column} is outside the table, which has '
            f'{column_count} column(s)'
        )
    if first_row == last_row and first_column == last_column:
        raise ValueError(
            'a merge must cover more than one cell; '
            'give a different last_row or last_column'
        )
    if align not in ('l', 'r', 'c'):
        raise ValueError(f"align must be 'l', 'r' or 'c', not {align!r}")

    region = MergedRegion(first_row, first_column, last_row, last_column,
                          value, align, color)

    for other in existing:
        if region.overlaps(other):
            raise ValueError(
                f'this merge overlaps the one covering rows '
                f'{other.first_row}-{other.last_row}, columns '
                f'{other.first_column}-{other.last_column}'
            )

    return region


class Layout(NamedTuple):
    """
    Where each column sits inside a rendered line.

    ``spans`` holds one (start, end) pair per *drawn* column, as visible-column
    bounds within the line, covering the cell text and its margins but not the
    separators around it. ``separators`` holds the offset of each vertical rule
    between columns, so a horizontal merge knows which characters to paint
    over. ``span_of_column`` maps a table column index to its entry in
    ``spans``, and has no entry for a column the table is not drawing.
    """

    spans: List[tuple]
    separators: List[int]
    span_of_column: dict


def compute_layout(column_widths, composition, hidden=()) -> Layout:
    """
    Work out the column offsets for a style and set of widths.

    Mirrors how table_strings assembles a row: an optional left rule, then for
    each column its margins and content, with a rule between neighbours and an
    optional one at the end.

    ``hidden`` lists the columns the table is leaving out -- empty ones, when
    ``show_empty_columns`` is off. They take up no room in the rendered line,
    so counting them here would put every offset after them too far right.
    """
    body = composition.vertical_table_body_lines
    margin = max(0, int(composition.margin or 0))
    hidden = set(hidden)

    offset = len(body.left) if body.left is not None else 0
    spans = []
    separators = []
    span_of_column = {}

    for index, width in enumerate(column_widths):
        if index in hidden:
            continue
        if spans:
            if body.middle is not None:
                separators.append(offset)
                offset += len(body.middle)
        cell_width = width + margin * 2
        span_of_column[index] = len(spans)
        spans.append((offset, offset + cell_width))
        offset += cell_width

    return Layout(spans, separators, span_of_column)


def _region_bounds(region, layout, index_offset):
    """
    Where a region sits in a line, as visible-column offsets.

    Returns the span covering the whole block, the span of its top-left cell,
    and the index of its rightmost drawn column. A merge given no replacement
    text reads its content from that top-left cell -- not from the strip of
    table under the whole block, which is the neighbouring columns and the
    rules between them.

    Columns the table is not drawing are skipped over, so a merge that reaches
    across a hidden empty column still lands on the columns either side of it.
    Returns None when the region is drawn nowhere at all.
    """
    drawn = [
        layout.span_of_column[column]
        for column in range(region.first_column + index_offset,
                            region.last_column + index_offset + 1)
        if column in layout.span_of_column
    ]
    if not drawn:
        return None

    first, last = drawn[0], drawn[-1]
    return (
        (layout.spans[first][0], layout.spans[last][1]),
        layout.spans[first],
        first,
        last,
    )


# Junction / rule helpers for merge painting.

# Horizontal dash characters used by the shipped styles (and ASCII grids).
_H_CHARS = set('─━═┄┅┈┉╌╍▬−' '-~=')
# A real rule has a *run* of dashes. A lone '-' inside "Beta-1" is not a rule.
_H_RUN = re.compile(r'[─━═┄┅┈┉╌╍▬−\-~=]{2,}')
# Corner and tee glyphs a rule may carry; plain verticals are left out.
_JUNCTIONS = set('+') | {
    chr(c) for c in range(0x2500, 0x2580)
} - set('│┃║┊┋┆┇╎╏')
_PURE_H = {(0, 0, 1, 1), (0, 0, 1, 0), (0, 0, 0, 1)}
_ROUND_CORNERS = set('╭╮╰╯')

# Light / heavy / double / ascii / round junction tables keyed by (N, S, E, W).
_LIGHT = {
    (1, 1, 1, 1): '┼', (1, 1, 1, 0): '├', (1, 1, 0, 1): '┤',
    (1, 0, 1, 1): '┴', (0, 1, 1, 1): '┬', (1, 1, 0, 0): '│',
    (0, 0, 1, 1): '─', (1, 0, 1, 0): '└', (1, 0, 0, 1): '┘',
    (0, 1, 1, 0): '┌', (0, 1, 0, 1): '┐', (1, 0, 0, 0): '│',
    (0, 1, 0, 0): '│', (0, 0, 1, 0): '─', (0, 0, 0, 1): '─',
}
_ROUND = {
    (1, 1, 1, 1): '┼', (1, 1, 1, 0): '├', (1, 1, 0, 1): '┤',
    (1, 0, 1, 1): '┴', (0, 1, 1, 1): '┬', (1, 1, 0, 0): '│',
    (0, 0, 1, 1): '─', (1, 0, 1, 0): '╰', (1, 0, 0, 1): '╯',
    (0, 1, 1, 0): '╭', (0, 1, 0, 1): '╮', (1, 0, 0, 0): '│',
    (0, 1, 0, 0): '│', (0, 0, 1, 0): '─', (0, 0, 0, 1): '─',
}
_DOUBLE_V_SINGLE_H = {
    (1, 1, 1, 1): '╫', (1, 1, 1, 0): '╟', (1, 1, 0, 1): '╢',
    (1, 0, 1, 1): '╨', (0, 1, 1, 1): '╥', (1, 1, 0, 0): '║',
    (0, 0, 1, 1): '─', (1, 0, 0, 0): '║', (0, 1, 0, 0): '║',
    (1, 0, 1, 0): '╙', (1, 0, 0, 1): '╜', (0, 1, 1, 0): '╓',
    (0, 1, 0, 1): '╖',
}
_DOUBLE = {
    (1, 1, 1, 1): '╬', (1, 1, 1, 0): '╠', (1, 1, 0, 1): '╣',
    (1, 0, 1, 1): '╩', (0, 1, 1, 1): '╦', (1, 1, 0, 0): '║',
    (0, 0, 1, 1): '═', (1, 0, 0, 0): '║', (0, 1, 0, 0): '║',
    (1, 0, 1, 0): '╚', (1, 0, 0, 1): '╝', (0, 1, 1, 0): '╔',
    (0, 1, 0, 1): '╗',
}
_SINGLE_V_DOUBLE_H = {
    (1, 1, 1, 1): '╪', (1, 1, 1, 0): '╞', (1, 1, 0, 1): '╡',
    (1, 0, 1, 1): '╧', (0, 1, 1, 1): '╤', (1, 1, 0, 0): '│',
    (0, 0, 1, 1): '═', (1, 0, 0, 0): '│', (0, 1, 0, 0): '│',
    (1, 0, 1, 0): '╘', (1, 0, 0, 1): '╛', (0, 1, 1, 0): '╒',
    (0, 1, 0, 1): '╕',
}
_ASCII = {
    (1, 1, 1, 1): '+', (1, 1, 1, 0): '+', (1, 1, 0, 1): '+',
    (1, 0, 1, 1): '+', (0, 1, 1, 1): '+', (1, 1, 0, 0): '|',
    (0, 0, 1, 1): '-', (1, 0, 0, 0): '|', (0, 1, 0, 0): '|',
    (1, 0, 1, 0): '+', (1, 0, 0, 1): '+', (0, 1, 1, 0): '+',
    (0, 1, 0, 1): '+', (0, 0, 1, 0): '-', (0, 0, 0, 1): '-',
}


def _glyph(ch: str) -> str:
    """Visible character from a slice that may still carry SGR wraps."""
    if not ch:
        return ''
    plain = strip_ansi(ch)
    return plain[:1] if plain else ''


def _is_h(ch: str) -> bool:
    return _glyph(ch) in _H_CHARS


def _visible_vertical(ch: str) -> bool:
    """True when a style's vertical glyph is a real column rule, not a spacer."""
    g = _glyph(ch)
    return bool(g) and not g.isspace()


def _char_at(line: str, index: int) -> str:
    if index < 0 or index >= visible_width(line):
        return ''
    return slice_by_width(line, index, index + 1)


def _junction_positions(layout, composition):
    """(x, vertical_glyph) for every vertical rule that can host a junction."""
    v = composition.vertical_table_body_lines
    if v is None:
        return []
    out = []
    if layout.spans and _visible_vertical(v.left):
        out.append((layout.spans[0][0] - len(v.left), v.left))
    for sep_x in layout.separators:
        if _visible_vertical(v.middle):
            out.append((sep_x, v.middle))
    if layout.spans and _visible_vertical(v.right):
        out.append((layout.spans[-1][1], v.right))
    return out


def _pick_junction(v_glyph: str, h_glyph: str, n: bool, s: bool, e: bool, w: bool,
                   round_corners: bool = False) -> str:
    key = (1 if n else 0, 1 if s else 0, 1 if e else 0, 1 if w else 0)
    if key == (0, 0, 0, 0):
        return ' '
    # Pure horizontal: keep THIS rule's dash (┄/═/─/-), never a foreign glyph.
    if key in _PURE_H:
        if v_glyph in '|+' or (h_glyph and h_glyph in '-=~'):
            return h_glyph if h_glyph in '-=~' else '-'
        return h_glyph or '─'
    if v_glyph in '|+':
        # ASCII column lines join with '+' whatever the dash ('-', '=', '~').
        return _ASCII.get(key, '+')
    if v_glyph == ':':
        # dotted_rows: ':' is a through vertical. When a vertical arm is
        # missing, fall back to the dotted dash so the junction does not
        # point into a merge interior.
        return ':' if (n and s) else (h_glyph if h_glyph and h_glyph != ':' else '.')
    if v_glyph and not ('\u2500' <= v_glyph <= '\u257f'):
        # Other non-box column glyphs are their own junction; a light box
        # tee next to them is a foreign glyph.
        return v_glyph
    if v_glyph == '║' and h_glyph == '═':
        return _DOUBLE.get(key, '║')
    if v_glyph == '║':
        return _DOUBLE_V_SINGLE_H.get(key, '║')
    if h_glyph == '═' and v_glyph in ('│', '┃', '┊'):
        return _SINGLE_V_DOUBLE_H.get(key, '│')
    if round_corners:
        return _ROUND.get(key, v_glyph or '│')
    return _LIGHT.get(key, v_glyph or '│')


def _synthesize_body_rule(composition):
    """Body SeparatorLine for styles that draw column lines but no row lines.

    Uses the table's outer (end/header) horizontal glyph so synthetic caps
    match the top/bottom border style.
    """
    from .style_compositions import SeparatorLine
    existing = composition.table_body_line
    if existing is not None and existing.middle:
        return existing
    v = composition.vertical_table_body_lines
    if v is None or not v.middle or v.middle == ' ':
        return None
    end = composition.table_end_line
    header = composition.inferior_header_line
    h = None
    if end is not None and end.middle:
        h = end.middle
    elif header is not None and header.middle:
        h = header.middle
    if not ('\u2500' <= v.middle <= '\u257f') and v.middle not in '|+':
        # Non-box column glyphs (``dotted_rows`` draws ':') are their own junction.
        return SeparatorLine(
            left=v.left or None,
            middle=h if h and not ('\u2500' <= h <= '\u257f') else '-',
            intersection=v.middle,
            right=v.right or None,
        )
    if v.middle in '|+':
        return SeparatorLine(
            left='+' if v.left else None,
            middle=h if h and h in '-=~' else '-',
            intersection='+',
            right='+' if v.right else None,
        )
    if h == '═':
        return SeparatorLine(
            left='╞' if v.left else None,
            middle='═',
            intersection='╪',
            right='╡' if v.right else None,
        )
    # Light / dotted / round outer borders → matching light body rule.
    left = '├' if v.left else None
    right = '┤' if v.right else None
    if v.left == '║':
        left = '╟'
    if v.right == '║':
        right = '╢'
    return SeparatorLine(
        left=left,
        middle=h or '─',
        intersection='┼',
        right=right,
    )


_FRAME_TEES = {
    # vertical glyph -> (left tee, right tee) for a light horizontal
    '│': ('├', '┤'), '┊': ('├', '┤'), '┆': ('├', '┤'), '╎': ('├', '┤'),
    '┃': ('┠', '┨'), '║': ('╟', '╢'), '|': ('+', '+'),
}
_FRAME_TEES_DOUBLE_H = {
    '│': ('╞', '╡'), '║': ('╠', '╣'), '|': ('+', '+'),
}


def _frame_only_body_rule(composition):
    """Body rule for styles with outer verticals but no column lines.

    ``*_ebody`` / ``*_empty`` styles frame the body without separating its
    columns, so the rule runs edge to edge and only meets the frame.
    Returns None when the body has no outer verticals either.
    """
    from .style_compositions import SeparatorLine
    v = composition.vertical_table_body_lines
    if v is None:
        return None
    left_v = _glyph(v.left or '')
    right_v = _glyph(v.right or '')
    if not (left_v.strip() or right_v.strip()):
        return None
    end = composition.table_end_line
    h = _glyph(end.middle) if end is not None and end.middle else ''
    if not h or h.isspace():
        h = '-' if '|' in (left_v, right_v) else '─'
    tees = _FRAME_TEES_DOUBLE_H if h == '═' else _FRAME_TEES
    if '|' in (left_v, right_v) and h not in '-=~':
        h = '-'

    def tee(glyph, side):
        if not glyph or glyph.isspace():
            return None
        pair = tees.get(glyph) or _FRAME_TEES.get(glyph)
        return pair[side] if pair else glyph

    return SeparatorLine(
        left=tee(left_v, 0),
        middle=h,
        intersection=h,
        right=tee(right_v, 1),
    )


def _build_rule_line(layout, composition, column_widths, hidden, rule=None):
    """Assemble one full horizontal rule matching the column layout."""
    rule = rule or _synthesize_body_rule(composition)
    if rule is None:
        return None
    v = composition.vertical_table_body_lines
    margin = max(0, int(composition.margin or 0))
    hidden = set(hidden or ())
    chunks = []
    first = True
    for index, width in enumerate(column_widths):
        if index in hidden:
            continue
        if not first:
            chunks.append(rule.intersection or '')
        cell = (rule.middle or ' ') * (width + margin * 2)
        chunks.append(cell)
        first = False
    center = ''.join(chunks)
    if rule.left is not None:
        left = rule.left
    elif v and v.left:
        left = v.left
    else:
        left = ''
    if rule.right is not None:
        right = rule.right
    elif v and v.right:
        right = v.right
    else:
        right = ''
    return left + center + right


def _clamp_rule_to_h_ranges(line, layout, composition, h_ranges, filler=' '):
    """
    Keep horizontal runs only inside ``h_ranges`` (merge content spans).

    Synthetic caps are inserted for multi-column merges; without clamping, the
    full-width rule bleeds H into neighbour columns that have no reason for a
    row edge. Outside the ranges, content is blanked and junctions fall back to
    the style's vertical glyph so column rules continue cleanly. Callers that
    also need taller merges punched through should run ``_blank_crossings``
    *after* this so restored verticals inside those merges stay erased.
    """
    if not h_ranges:
        return line
    ranges = sorted((int(a), int(b)) for a, b in h_ranges if b > a)
    if not ranges:
        return line
    # Merge overlapping / abutting ranges.
    merged = [list(ranges[0])]
    for a, b in ranges[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    ranges = [(a, b) for a, b in merged]

    def in_ranges(x):
        return any(a <= x < b for a, b in ranges)

    rewritten = line
    for start, end in layout.spans:
        if any(not (end <= a or start >= b) for a, b in ranges):
            continue
        if end > start:
            rewritten = _repaint(rewritten, start, end, filler * (end - start))

    for x, v_glyph in _junction_positions(layout, composition):
        if in_ranges(x):
            continue
        rewritten = _repaint(rewritten, x, x + 1, v_glyph)
    return rewritten


_OUTER_FRAME_CORNERS = set(".'`")


def _is_outer_frame(line: str) -> bool:
    """True for a top/bottom box or ascii-rounded frame, not a grid rule."""
    if not line:
        return False
    plain = strip_ansi(line)
    if not plain or _re_search_word(plain):
        return False
    return plain[0] in _OUTER_FRAME_CORNERS and plain[-1] in _OUTER_FRAME_CORNERS


def _re_search_word(plain: str) -> bool:
    return any(ch.isalnum() for ch in plain)


def _looks_like_rule(line: str, h_glyph: str = None) -> bool:
    """True only for real separator lines, not cell text that contains '-'."""
    if not line:
        return False
    if h_glyph and len(h_glyph) >= 1 and (h_glyph * 2) in line:
        return True
    if _H_RUN.search(line) is not None:
        return True
    # cell_padding=0 with 1-column cells draws rules like '├─┼─┤', with no
    # run of two dashes (and a merge may have blanked part of it). Such a
    # line is a rule when it holds dashes and junctions and nothing else but
    # spaces; a body line always has text or a plain vertical.
    plain = strip_ansi(line)
    return (
        any(ch in _H_CHARS for ch in plain)
        and any(ch in _JUNCTIONS for ch in plain)
        and all(ch in _H_CHARS or ch in _JUNCTIONS or ch == ' '
                for ch in plain)
    )


# Glyphs that carry a vertical arm out of their bottom / top edge.
_VERTICALS = set('|¦:│┃║┊┋┆┇╎╏')
_NO_DOWN = set('┴└┘╰╯╨╩╧╙╜╚╝╘╛┸┷┻┖┚┗┛')
_NO_UP = set('┬┌┐╭╮╥╦╤╓╖╔╗╒╕┰┯┳┎┒┏┓')


# Light verticals meeting a heavy dash ('╍', '━'): keep the rule's weight.
_HEAVY_H = set('╍━┅┉')
_LIGHT_TO_HEAVY_H = {
    '┼': '┿', '├': '┝', '┤': '┥', '┬': '┯', '┴': '┷',
    '┌': '┍', '┐': '┑', '└': '┕', '┘': '┙',
}


def _has_arm(line, x, down):
    """
    True when the glyph at ``x`` in a neighbouring line reaches this rule.

    ``down`` asks about the line above (does its glyph continue downwards);
    otherwise about the line below. Text, spaces and dashes do not reach it,
    which is what tells a top border under a title, or a bottom border over
    a caption, that it has no arm on that side.
    """
    if line is None:
        return False
    g = _glyph(_char_at(line, x))
    if not g or g.isspace() or g in _H_CHARS:
        return False
    if g in _VERTICALS or g == '+':
        return True
    if g in _JUNCTIONS:
        return g not in (_NO_DOWN if down else _NO_UP)
    return False


def _repair_rule_junctions(line, layout, composition, h_glyph, missing_south=None, missing_north=None,
                          no_south=False, no_north=False, above=False, below=False,
                          only=None):
    """
    Rebuild every junction on a horizontal rule from the arms that remain.

    ``missing_south`` / ``missing_north`` are sets of visible x positions where
    a vertical arm was removed by a horizontal (or 2D) merge on that side.

    ``no_south`` / ``no_north`` force every junction to drop that arm — used for
    the table's outer end/start rules, which never continue past the border.

    ``above`` / ``below``, when not False, are the lines next to this rule (None
    past either end of the table). An arm is then kept only where that line
    really reaches the rule, so a top border under a title, a bottom border
    over a caption, or a header separator under a header drawn without
    column rules keep their own shape. A junction drawn as a plain vertical
    (markdown's ``|---|``) stays as it is unless it becomes a pure dash.

    ``only``, when given, limits the rewrite to those x positions; every other
    junction keeps the style's own glyph (corners such as ``O`` or ``╔``).
    """
    missing_south = missing_south or set()
    missing_north = missing_north or set()
    v = composition.vertical_table_body_lines
    if v is None:
        return line
    h_glyph = h_glyph or '─'
    round_corners = any(ch in line for ch in _ROUND_CORNERS)
    rewritten = line
    for x, v_glyph in _junction_positions(layout, composition):
        if visible_width(rewritten) <= x:
            continue
        if only is not None and x not in only:
            continue
        here = _char_at(rewritten, x)
        # Interior of a multi-column vertical blank: junction was wiped to space.
        if _glyph(here) in ('', ' '):
            continue
        left = _char_at(rewritten, x - 1)
        right = _char_at(rewritten, x + 1)
        west = _is_h(left)
        east = _is_h(right)
        north = (not no_north) and (x not in missing_north)
        south = (not no_south) and (x not in missing_south)
        if above is not False:
            north = north and _has_arm(above, x, down=True)
        if below is not False:
            south = south and _has_arm(below, x, down=False)
        glyph = _pick_junction(
            v_glyph, h_glyph, north, south, east, west,
            round_corners=round_corners,
        )
        # Markdown/org header rules are '|---|---|'. Rewriting '|' to '+'
        # would stop the line being a valid markdown separator.
        if v_glyph == '|' and glyph == '+':
            plain = strip_ansi(rewritten)
            if plain.startswith('|') and plain.endswith('|') and '+' not in plain:
                glyph = '|'
        if h_glyph in _HEAVY_H and glyph in _LIGHT_TO_HEAVY_H:
            glyph = _LIGHT_TO_HEAVY_H[glyph]
        # Keep a plain vertical only when it still runs through the rule
        # (both arms). A '|' or ':' that has lost the south (or north) arm
        # must become a tee or a dash; otherwise it points into the merge.
        if (above is not False and _glyph(here) in _VERTICALS
                and north and south):
            glyph = here
        if only is not None and south and not north and _glyph(here) in _NO_UP:
            glyph = here  # already has no arm upwards, e.g. a header box top
        if only is not None and north and not south and _glyph(here) in _NO_DOWN:
            glyph = here  # already closed below, e.g. ╚═══╩═══╝
        rewritten = _repaint(rewritten, x, x + 1, glyph)
    return rewritten



def paint_rule_cell_backgrounds(line, layout, column_specs, border_color=None):
    """
    Colour a horizontal rule with ``border_color`` only.

    Cell, zebra and merge backgrounds belong on the interior rectangle of
    the cell or merge (text lines and any rule segments absorbed inside a
    merge). Rule glyphs on the outline stay chrome: they keep
    ``border_color`` (or the default foreground) and never inherit a cell
    fill, so a zebra stripe cannot leak onto ``─`` and a junction cannot
    be left as an uncoloured gap.

    ``layout`` and ``column_specs`` are accepted for compatibility and
    ignored. Paint lives in ``apply`` for merge interiors and in the
    table's rule colouring for chrome.
    """
    if not line:
        return line
    return colorize(line, border_color) if border_color else line


def _join_sgr_parts(parts):
    """Concatenate SGR spans, collapsing a reset that is immediately doubled."""
    out = ''
    for part in parts:
        if out.endswith(_RESET) and part.startswith(_RESET):
            part = part[len(_RESET):]
        out += part
    return out


def _apply_border_chrome(line, border_color, protected_ranges=()):
    """
    Recolour every visible column of a rule with ``border_color``, leaving
    merge interiors untouched.

    ``protected_ranges`` is a sequence of ``[start, end)`` visible-column
    spans (the merge rectangle, including absorbed internal separators).
    Those columns already hold the merge fill (spaces or text) and must
    not pick up chrome. Everything else -- outline dashes, tees, outer
    corners, and the rule on either side of a merge -- is stripped and
    wrapped in ``border_color`` so a later ``_repaint`` cannot leave an
    uncoloured hole where a colour was closed early.
    """
    if not line or not border_color:
        return line
    width = visible_width(line)
    ranges = []
    for start, end in protected_ranges:
        start = max(0, start)
        end = min(width, end)
        if end > start:
            ranges.append((start, end))
    ranges.sort()
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    segments = []
    cursor = 0
    for start, end in merged:
        if start > cursor:
            segments.append((cursor, start, False))
        segments.append((start, end, True))
        cursor = max(cursor, end)
    if cursor < width:
        segments.append((cursor, width, False))

    if not merged:
        return colorize(strip_ansi(line), border_color)

    parts = []
    for start, end, kept in segments:
        _, chunk, _ = partition_by_width(line, start, end)
        if kept:
            parts.append(chunk)
        else:
            painted = colorize(strip_ansi(chunk), border_color)
            # The reset that closed the previous (merge) span often lands at
            # the start of this chunk and would be stripped with the rest of
            # its ANSI, so a 'red' prefix (fg only) would inherit the merge
            # background. Re-open chrome with a reset when this is not the
            # start of the line; _join_sgr_parts collapses a true double.
            if start > 0 and not painted.startswith(_RESET):
                painted = _RESET + painted
            parts.append(painted)
    return _join_sgr_parts(parts)


def apply(lines, row_line_map, regions, column_widths, composition,
          index_offset, hidden_columns=(), filler=' ', border_color=None):
    """
    Rewrite assembled lines so each region renders as one cell.

    ``lines`` is the rendered table split into lines. ``row_line_map`` maps
    each logical row index to the indexes of the physical lines it occupies,
    which differ once wrapping has turned one row into several. Separator
    lines between rows are not in the map; they are found between the mapped
    lines and painted over where a region spans them vertically.

    ``index_offset`` is 1 when the index column is displayed, since region
    coordinates ignore it. ``hidden_columns`` lists the columns the table is
    not drawing, which take up no room in a line.

    The merge interior is a single rectangle: every physical line from the
    first content line to the last, including separators absorbed between
    those rows, is painted from the first column's left edge to the last
    column's right edge. Internal rule glyphs (including crossings) become
    spaces and, when the region has a colour, carry that background.
    Outline glyphs immediately outside the rectangle -- the rule above and
    below, and the verticals to either side -- stay chrome: they use
    ``border_color`` (or the default foreground) and never pick up the
    merge fill.

    Column-only styles (verticals but no body rule) insert a synthetic cap
    above and below a multi-column merge, drawn only across the merge
    width, with tees that do not send a horizontal arm into neighbour
    columns. A vertical-only merge does not get a cap: the table has no
    row rules, and the left/right verticals already outline the span.

    Returns the rewritten lines.
    """
    if not regions:
        return lines

    layout = compute_layout(column_widths, composition, hidden_columns)
    lines = list(lines)
    margin = max(0, int(composition.margin or 0))
    body_rule = composition.table_body_line
    h_glyph = body_rule.middle if body_rule is not None else None
    # Separator lines whose horizontal run was blanked by a vertical span.
    touched_seps = set()
    # Horizontal (or 2D) merges: verticals removed between their columns on
    # their data lines; caps above/below need ┴/┬ repair.
    # (above_line, below_line, inner_separator_xs, first_row, last_row)
    horiz_caps = []
    # Column-only gaps keyed by logical row *after which* a rule sits
    # (gap after row G = between G and G+1). Values: miss_s, miss_n, insert_at.
    gap_plans = {}
    # Visible-column ranges of every merge interior, per physical line, so
    # the chrome pass can recolour outline glyphs without touching the fill.
    interior_ranges = {}

    synthesized = _synthesize_body_rule(composition)
    col_only = (
        composition.table_body_line is None
        and synthesized is not None
        and composition.vertical_table_body_lines is not None
        and composition.vertical_table_body_lines.middle not in (None, '', ' ')
    )
    syn_h = synthesized.middle if synthesized is not None else None

    def _blank_crossings(rule_line, gap_after_row):
        """Erase horizontal through merges that continue across this gap."""
        for crossing in regions:
            if crossing.first_row <= gap_after_row and crossing.last_row >= gap_after_row + 1:
                cross_bounds = _region_bounds(crossing, layout, index_offset)
                if cross_bounds is None:
                    continue
                (c_start, c_end), _, _, _ = cross_bounds
                if c_end > c_start:
                    rule_line = _repaint(
                        rule_line, c_start, c_end, filler * (c_end - c_start)
                    )
        return rule_line

    def _shift_interiors(at):
        return {
            (k + 1 if k >= at else k): v
            for k, v in interior_ranges.items()
        }

    def _mark_interior(line_index, start, end):
        if end > start:
            interior_ranges.setdefault(line_index, []).append((start, end))

    for region in regions:
        bounds = _region_bounds(region, layout, index_offset)
        if bounds is None:
            continue
        (start, end), (cell_start, cell_end), first_span, last_span = bounds
        span_width = end - start - margin * 2
        if span_width < 1:
            continue

        target_lines = []
        for row in range(region.first_row, region.last_row + 1):
            target_lines.extend(row_line_map.get(row, []))
        if not target_lines:
            continue

        text = region.value
        if text is None:
            first_line = lines[target_lines[0]]
            text = strip_by_width(slice_by_width(first_line, cell_start, cell_end))
        text = str(text)
        # strip_by_width keeps leading/trailing escapes so a cell can keep
        # its colour when the merge has no colour of its own. If we are
        # about to paint a region colour, those escapes must go: a leftover
        # RESET would sit after the left pad and close the fill mid-span
        # ("Mérida" falling out of the background).
        spec = getattr(region, 'color', None)
        if spec:
            text = strip_ansi(text)

        if visible_width(text) > span_width:
            text = truncate_to_width(text, span_width)
        painted = (filler * margin
                   + pad_to_width(text, span_width, region.align, filler)
                   + filler * margin)
        blank = filler * (end - start)
        # Colour the entire span (text line + blank continuations) so a merge
        # fill is flush across its rectangle -- same pad-then-paint contract
        # as ordinary cells. Borders stay outside _repaint's range.
        if spec:
            painted = colorize(painted, spec)
            blank = colorize(blank, spec)

        text_line = target_lines[len(target_lines) // 2]
        for line_index in target_lines:
            line = lines[line_index]
            if visible_width(line) < end:
                continue
            replacement = painted if line_index == text_line else blank
            lines[line_index] = _repaint(line, start, end, replacement)
            _mark_interior(line_index, start, end)

        # Blank separator lines inside a vertical (or 2D) span. Junctions are
        # repaired in a second pass once every region has painted, so adjacent
        # merges share one consistent reading of the surviving arms.
        covered = set(target_lines)
        for line_index in range(min(target_lines), max(target_lines)):
            if line_index in covered:
                continue
            line = lines[line_index]
            if visible_width(line) < end:
                continue
            lines[line_index] = _repaint(line, start, end, blank)
            _mark_interior(line_index, start, end)
            touched_seps.add(line_index)

        inner_seps = [
            layout.separators[i]
            for i in range(first_span, last_span)
            if i < len(layout.separators)
        ]

        if region.column_count >= 2 and inner_seps:
            above = min(target_lines) - 1
            below = max(target_lines) + 1
            horiz_caps.append(
                (above, below, set(inner_seps), region.first_row, region.last_row)
            )

            if col_only and synthesized is not None:
                # Cap above, including a merge on the first body row when
                # the style has no header/body separator (ascii_rounded).
                # If the line above is already a rule, pass 4 repairs it
                # in place; otherwise a cap is inserted there.
                g = region.first_row - 1
                plan = gap_plans.setdefault(
                    g, {'s': set(), 'n': set(), 'at': min(target_lines),
                        'h': []}
                )
                plan['s'] |= set(inner_seps)
                plan['at'] = min(plan['at'], min(target_lines))
                plan.setdefault('h', []).append((start, end))
                # Cap below: gap after last_row (unless last table row — end
                # line is repaired in pass 3).
                max_row = max(row_line_map) if row_line_map else region.last_row
                if region.last_row < max_row:
                    g = region.last_row
                    plan = gap_plans.setdefault(
                        g, {'s': set(), 'n': set(), 'at': max(target_lines) + 1,
                            'h': []}
                    )
                    plan['n'] |= set(inner_seps)
                    plan['at'] = min(plan.get('at', max(target_lines) + 1),
                                     max(target_lines) + 1)
                    plan.setdefault('h', []).append((start, end))

    # --- Pass 2: repair junctions on body rules touched by vertical blanks ---
    # Always run, even when the dash run was fully absorbed: leftover ┼
    # between side-by-side merges must become │ (no H arms into spaces).
    if composition.vertical_table_body_lines is not None:
        for sep_index in sorted(touched_seps):
            line = lines[sep_index]
            line_h = h_glyph or next(
                (ch for ch in strip_ansi(line) if _is_h(ch)), '─'
            )
            lines[sep_index] = _repair_rule_junctions(
                line, layout, composition, line_h,
                above=lines[sep_index - 1] if sep_index > 0 else None,
                below=lines[sep_index + 1] if sep_index + 1 < len(lines) else None,
            )

    # --- Pass 3: ┴ / ┬ on existing rules above and below H / 2D merges -------
    missing_south_by_line = {}
    missing_north_by_line = {}
    for above, below, xs, _fr, _lr in horiz_caps:
        if above >= 0:
            missing_south_by_line.setdefault(above, set()).update(xs)
        if below < len(lines):
            missing_north_by_line.setdefault(below, set()).update(xs)

    cap_lines = set(missing_south_by_line) | set(missing_north_by_line)
    for line_index in cap_lines:
        line = lines[line_index]
        if not _looks_like_rule(line, h_glyph):
            continue
        line_h = next((ch for ch in line if _is_h(ch)), h_glyph or '─')
        lines[line_index] = _repair_rule_junctions(
            line, layout, composition, line_h,
            missing_south=missing_south_by_line.get(line_index),
            missing_north=missing_north_by_line.get(line_index),
            above=lines[line_index - 1] if line_index > 0 else None,
            below=lines[line_index + 1] if line_index + 1 < len(lines) else None,
            only=(missing_south_by_line.get(line_index, set())
                  | missing_north_by_line.get(line_index, set())),
        )

    # --- Pass 4: synthetic caps for column-only styles ----------------------
    # A multi-column merge in a style with no body rule has no top/bottom
    # outline, so a │ on the neighbouring row points into the merge interior
    # (wrong vertex) and the block is easy to misread as continuing. Insert a
    # rule only across the merge width, with ├/┤ (or ┌/┐) at the edges so
    # horizontal arms do not bleed into neighbour columns. Neighbour columns
    # keep their verticals through the new line; they are not given a
    # horizontal cap of their own.
    if col_only and gap_plans and synthesized is not None:
        for g in sorted(gap_plans.keys(), reverse=True):
            plan = gap_plans[g]
            at = plan['at']
            existing = None
            if 0 <= at < len(lines) and _looks_like_rule(lines[at], syn_h):
                existing = at
            elif 0 <= at - 1 < len(lines) and _looks_like_rule(lines[at - 1], syn_h):
                existing = at - 1

            if existing is not None and _is_outer_frame(lines[existing]):
                existing = None

            if existing is not None:
                line = lines[existing]
                line = _blank_crossings(line, g)
                line_h = next((ch for ch in strip_ansi(line) if _is_h(ch)), syn_h or '─')
                lines[existing] = _repair_rule_junctions(
                    line, layout, composition, line_h,
                    missing_south=plan['s'] or None,
                    missing_north=plan['n'] or None,
                    above=lines[existing - 1] if existing > 0 else None,
                    below=lines[existing + 1] if existing + 1 < len(lines) else None,
                )
                continue

            rule = _build_rule_line(
                layout, composition, column_widths, hidden_columns, synthesized
            )
            if rule is None:
                continue
            rule = _clamp_rule_to_h_ranges(
                rule, layout, composition, plan.get('h') or []
            )
            rule = _blank_crossings(rule, g)
            rule = _repair_rule_junctions(
                rule, layout, composition, syn_h,
                missing_south=plan['s'] or None,
                missing_north=plan['n'] or None,
            )
            at = max(0, min(at, len(lines)))
            lines.insert(at, rule)
            interior_ranges = _shift_interiors(at)

    # --- Pass 5: restore border chrome on remaining rule glyphs --------------
    if border_color:
        for line_index, line in enumerate(lines):
            if not _looks_like_rule(line, h_glyph):
                continue
            lines[line_index] = _apply_border_chrome(
                line, border_color, interior_ranges.get(line_index, ()),
            )

    return lines
