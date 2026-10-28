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

from typing import List, NamedTuple, Optional

from .fast import (
    has_ansi,
    pad_to_width,
    partition_by_width,
    slice_by_width,
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
    if has_ansi(removed) and not replacement.startswith(_RESET):
        replacement = _RESET + replacement
    return before + replacement + after


class MergedRegion(NamedTuple):
    """
    One rectangular block of cells rendered as a single cell.

    Coordinates are inclusive and zero-based, in the table's own row and
    column numbering -- the index column, when shown, is not counted.
    """

    first_row: int
    first_column: int
    last_row: int
    last_column: int
    value: Optional[str]
    align: str

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
              row_count, column_count, existing):
    """
    Validate a merge request and turn it into a MergedRegion.

    Accepts the corners in either order, so callers may give them the way they
    think of them. Raises ValueError on anything that cannot be rendered: a
    single cell, coordinates outside the table, an unknown alignment, or an
    overlap with a merge already in place.
    """
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
                          value, align)

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
    margin = 1 if composition.margin else 0
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


# Replacement for apply() and helpers — pasted into merges.py below Layout helpers.

# Horizontal dash characters used by the shipped styles (and ASCII grids).
_H_CHARS = set('─━═┄┅┈┉╌╍▬−' '-~=')

# Light / heavy / double / ascii junction tables keyed by (N, S, E, W) booleans.
_LIGHT = {
    (1, 1, 1, 1): '┼', (1, 1, 1, 0): '├', (1, 1, 0, 1): '┤',
    (1, 0, 1, 1): '┴', (0, 1, 1, 1): '┬', (1, 1, 0, 0): '│',
    (0, 0, 1, 1): '─', (1, 0, 1, 0): '└', (1, 0, 0, 1): '┘',
    (0, 1, 1, 0): '┌', (0, 1, 0, 1): '┐', (1, 0, 0, 0): '│',
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


def _is_h(ch: str) -> bool:
    return ch in _H_CHARS


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
    if layout.spans and v.left:
        out.append((layout.spans[0][0] - len(v.left), v.left))
    for sep_x in layout.separators:
        if v.middle:
            out.append((sep_x, v.middle))
    if layout.spans and v.right:
        out.append((layout.spans[-1][1], v.right))
    return out


def _pick_junction(v_glyph: str, h_glyph: str, n: bool, s: bool, e: bool, w: bool) -> str:
    key = (1 if n else 0, 1 if s else 0, 1 if e else 0, 1 if w else 0)
    if key == (0, 0, 0, 0):
        return ' '
    if v_glyph in '|+' or h_glyph in '-=':
        # ASCII grid / pipes family
        if v_glyph in '|+' and h_glyph in '-=+':
            return _ASCII.get(key, '+')
    if v_glyph == '║' and h_glyph == '═':
        return _DOUBLE.get(key, '║')
    if v_glyph == '║':
        return _DOUBLE_V_SINGLE_H.get(key, '║')
    if h_glyph == '═' and v_glyph in ('│', '┃'):
        return _SINGLE_V_DOUBLE_H.get(key, '│')
    return _LIGHT.get(key, v_glyph or '│')


def _synthesize_body_rule(composition):
    """Body SeparatorLine for styles that draw column lines but no row lines."""
    from .style_compositions import SeparatorLine
    existing = composition.table_body_line
    if existing is not None and existing.middle:
        return existing
    v = composition.vertical_table_body_lines
    if v is None or not v.middle or v.middle == ' ':
        return None
    if v.middle in '|+':
        return SeparatorLine(
            left='+' if v.left else None,
            middle='-',
            intersection='+',
            right='+' if v.right else None,
        )
    # Unicode column style (pretty_columns, round_edges, …)
    left = '├' if v.left else None
    right = '┤' if v.right else None
    if v.left == '║':
        left = '╟'
    if v.right == '║':
        right = '╢'
    return SeparatorLine(left=left, middle='─', intersection='┼', right=right)


def _build_rule_line(layout, composition, column_widths, hidden, rule=None):
    """Assemble one full horizontal rule matching the column layout."""
    rule = rule or _synthesize_body_rule(composition)
    if rule is None:
        return None
    v = composition.vertical_table_body_lines
    margin = 1 if composition.margin else 0
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


def _looks_like_rule(line: str, h_glyph: str) -> bool:
    if not line:
        return False
    plain = line
    if h_glyph and h_glyph in plain:
        return True
    return any(ch in plain for ch in _H_CHARS)


def _repair_rule_junctions(line, layout, composition, h_glyph, missing_south=None, missing_north=None,
                          no_south=False, no_north=False):
    """
    Rebuild every junction on a horizontal rule from the arms that remain.

    ``missing_south`` / ``missing_north`` are sets of visible x positions where
    a vertical arm was removed by a horizontal (or 2D) merge on that side.

    ``no_south`` / ``no_north`` force every junction to drop that arm — used for
    the table's outer end/start rules, which never continue past the border.
    """
    missing_south = missing_south or set()
    missing_north = missing_north or set()
    v = composition.vertical_table_body_lines
    if v is None:
        return line
    h_glyph = h_glyph or '─'
    rewritten = line
    for x, v_glyph in _junction_positions(layout, composition):
        if visible_width(rewritten) <= x:
            continue
        here = _char_at(rewritten, x)
        # Interior of a multi-column vertical blank: junction was wiped to space.
        if here == ' ' or here == '':
            continue
        left = _char_at(rewritten, x - 1)
        right = _char_at(rewritten, x + 1)
        west = _is_h(left)
        east = _is_h(right)
        north = (not no_north) and (x not in missing_north)
        south = (not no_south) and (x not in missing_south)
        # A junction with no arms at all becomes the bare vertical.
        glyph = _pick_junction(v_glyph, h_glyph, north, south, east, west)
        rewritten = _repaint(rewritten, x, x + 1, glyph)
    return rewritten


def apply(lines, row_line_map, regions, column_widths, composition,
          index_offset, hidden_columns=(), filler=' '):
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

    Returns the rewritten lines.
    """
    if not regions:
        return lines

    layout = compute_layout(column_widths, composition, hidden_columns)
    lines = list(lines)
    margin = 1 if composition.margin else 0
    body_rule = composition.table_body_line
    h_glyph = body_rule.middle if body_rule is not None else None
    # Separator lines whose horizontal run was blanked by a vertical span.
    touched_seps = set()
    # Horizontal (or 2D) merges: verticals removed between their columns on
    # their data lines; caps above/below need ┴/┬ repair.
    horiz_caps = []  # (above_line, below_line, inner_separator_xs)
    # Column-only styles: insert a synthetic row rule around multi-column merges.
    col_only_inserts = []  # (after_index, rule_line)  insert AT after_index+1

    synthesized = _synthesize_body_rule(composition)
    col_only = (
        composition.table_body_line is None
        and synthesized is not None
        and composition.vertical_table_body_lines is not None
        and composition.vertical_table_body_lines.middle not in (None, '', ' ')
    )

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

        if visible_width(text) > span_width:
            text = truncate_to_width(text, span_width)
        painted = (filler * margin
                   + pad_to_width(text, span_width, region.align, filler)
                   + filler * margin)
        blank = filler * (end - start)

        text_line = target_lines[len(target_lines) // 2]
        for line_index in target_lines:
            line = lines[line_index]
            if visible_width(line) < end:
                continue
            replacement = painted if line_index == text_line else blank
            lines[line_index] = _repaint(line, start, end, replacement)

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
            touched_seps.add(line_index)

        inner_seps = [
            layout.separators[i]
            for i in range(first_span, last_span)
            if i < len(layout.separators)
        ]

        if region.column_count >= 2 and inner_seps:
            above = min(target_lines) - 1
            below = max(target_lines) + 1
            # Existing rules (body / header / end) get ┴/┬ via horiz_caps.
            horiz_caps.append((above, below, set(inner_seps)))

            if col_only:
                rule_line = _build_rule_line(
                    layout, composition, column_widths, hidden_columns, synthesized
                )
                if rule_line is not None:
                    # Only insert a synthetic row rule where the style has no
                    # rule already. Duplicating a header/end rule looks broken;
                    # those are repaired in pass 3 instead.
                    above_is_rule = (
                        above >= 0 and any(_is_h(ch) for ch in lines[above])
                    )
                    below_is_rule = (
                        below < len(lines) and any(_is_h(ch) for ch in lines[below])
                    )
                    if not above_is_rule:
                        capped = _repair_rule_junctions(
                            rule_line, layout, composition,
                            synthesized.middle,
                            missing_south=set(inner_seps),
                        )
                        col_only_inserts.append((min(target_lines), capped))
                    if not below_is_rule:
                        capped_below = _repair_rule_junctions(
                            rule_line, layout, composition,
                            synthesized.middle,
                            missing_north=set(inner_seps),
                        )
                        col_only_inserts.append((max(target_lines) + 1, capped_below))

    # --- Pass 2: repair junctions on body rules touched by vertical blanks ---
    if h_glyph:
        for sep_index in sorted(touched_seps):
            line = lines[sep_index]
            if not _looks_like_rule(line, h_glyph):
                continue
            lines[sep_index] = _repair_rule_junctions(
                line, layout, composition, h_glyph
            )

    # --- Pass 3: ┴ / ┬ on rules above and below horizontal / 2D merges -----
    # Combine missing arms when several merges share a cap line.
    missing_south_by_line = {}
    missing_north_by_line = {}
    for above, below, xs in horiz_caps:
        if above >= 0:
            missing_south_by_line.setdefault(above, set()).update(xs)
        if below < len(lines):
            missing_north_by_line.setdefault(below, set()).update(xs)

    cap_lines = set(missing_south_by_line) | set(missing_north_by_line)
    for line_index in cap_lines:
        line = lines[line_index]
        # Header / body / end rules all use horizontal glyphs.
        if not any(_is_h(ch) for ch in line):
            continue
        # Guess h glyph from the line itself.
        line_h = next((ch for ch in line if _is_h(ch)), h_glyph or '─')
        # Outer borders never grow an arm past the table.
        lines[line_index] = _repair_rule_junctions(
            line, layout, composition, line_h,
            missing_south=missing_south_by_line.get(line_index),
            missing_north=missing_north_by_line.get(line_index),
            no_south=(line_index >= len(lines) - 1),
            no_north=(line_index == 0),
        )

    # --- Pass 4: insert synthetic row rules for column-only styles ----------
    # Adjacent multi-column merges on neighbouring rows both want a rule in
    # the same gap; coalesce those into one line with every missing arm.
    if col_only_inserts and synthesized is not None:
        # Map insert index → (missing_south xs, missing_north xs)
        gap_arms = {}
        for above, below, xs in horiz_caps:
            # insert above merge lands at above+1 (== min target_lines)
            if above + 1 >= 0:
                arms = gap_arms.setdefault(above + 1, [set(), set()])
                arms[0] |= set(xs)  # missing south into the merge below
            arms = gap_arms.setdefault(below, [set(), set()])
            arms[1] |= set(xs)  # missing north into the merge above
        # Only keep gaps we actually planned to insert (skip header/end).
        planned = {at for at, _ in col_only_inserts}
        for at in sorted(planned, reverse=True):
            miss_s, miss_n = gap_arms.get(at, [set(), set()])
            rule = _build_rule_line(
                layout, composition, column_widths, hidden_columns, synthesized
            )
            rule = _repair_rule_junctions(
                rule, layout, composition, synthesized.middle,
                missing_south=miss_s or None,
                missing_north=miss_n or None,
            )
            lines.insert(max(0, min(at, len(lines))), rule)

    return lines
