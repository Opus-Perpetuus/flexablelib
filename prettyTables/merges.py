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


class GridSpans(NamedTuple):
    """
    The merges of a table expressed as a grid, for the non-console writers.

    ``origins`` maps the top-left cell of each region to that region.
    ``covered`` holds every other cell the regions swallow. Together they are
    all a writer needs: emit the origin once, carrying its span, and skip the
    covered cells.

    Coordinates here are in *output* space -- the index column, when a writer
    is including it, has already been counted -- so a writer can look a cell up
    with the same indexes it is iterating with.
    """

    origins: dict
    covered: set

    def __bool__(self):
        return bool(self.origins)


def grid_spans(regions, row_count, column_count, index_offset=0) -> GridSpans:
    """
    Turn merged regions into per-cell span information.

    The console renderer paints merges over the finished text, which no other
    format can use: CSV has no notion of a cell covering its neighbours, and
    HTML and Excel each spell it their own way. This gives every writer the
    same starting point -- which cell owns a span, how far it reaches, and
    which cells it hides.

    Regions are clipped to the grid rather than dropped, so a merge that runs
    past the last row (possible once a filter has removed rows) still renders
    over the part of it that exists.
    """
    origins = {}
    covered = set()

    for region in regions:
        first_row = max(0, region.first_row)
        first_column = max(0, region.first_column + index_offset)
        last_row = min(row_count - 1, region.last_row)
        last_column = min(column_count - 1, region.last_column + index_offset)
        if last_row < first_row or last_column < first_column:
            continue
        if last_row == first_row and last_column == first_column:
            continue

        origins[(first_row, first_column)] = MergedRegion(
            first_row, first_column, last_row, last_column,
            region.value, region.align,
        )
        for row in range(first_row, last_row + 1):
            for column in range(first_column, last_column + 1):
                if (row, column) != (first_row, first_column):
                    covered.add((row, column))

    return GridSpans(origins, covered)


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
    return (layout.spans[first][0], layout.spans[last][1]), layout.spans[first], last


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

    for region in regions:
        bounds = _region_bounds(region, layout, index_offset)
        if bounds is None:
            continue
        (start, end), (cell_start, cell_end), last_span = bounds
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
            # No replacement text given: keep what the top-left cell holds.
            # Read that cell alone. Reading the whole span instead used to pull
            # in the next column and the rule between them, and since that text
            # already filled the span exactly, painting it back changed nothing
            # -- the merge silently did not happen.
            first_line = lines[target_lines[0]]
            text = strip_by_width(slice_by_width(first_line, cell_start, cell_end))
        text = str(text)

        if visible_width(text) > span_width:
            text = truncate_to_width(text, span_width)
        painted = (filler * margin
                   + pad_to_width(text, span_width, region.align, filler)
                   + filler * margin)
        blank = filler * (end - start)

        # The text sits on the middle line of the block, so a tall merge reads
        # as one cell rather than a label with empty space under it.
        text_line = target_lines[len(target_lines) // 2]
        for line_index in target_lines:
            line = lines[line_index]
            if visible_width(line) < end:
                continue
            replacement = painted if line_index == text_line else blank
            lines[line_index] = _repaint(line, start, end, replacement)

        # Paint over the separator lines that fall inside the block, so the
        # merged region reads as one cell top to bottom.
        #
        # Where such a line meets the rule at the block's right edge, that
        # junction no longer has a line coming in from the left, so the four
        # way character is wrong there. The body rule's own left character is
        # exactly the three-way junction needed ('├' where '┼' was).
        body_rule = composition.table_body_line
        junction = body_rule.left if body_rule is not None else None
        joins_more_columns = last_span + 1 < len(layout.spans)

        covered = set(target_lines)
        for line_index in range(min(target_lines), max(target_lines)):
            if line_index in covered:
                continue
            line = lines[line_index]
            if visible_width(line) < end:
                continue
            rewritten = _repaint(line, start, end, blank)
            if junction and joins_more_columns and visible_width(rewritten) > end:
                rewritten = _repaint(rewritten, end, end + 1, junction)
            lines[line_index] = rewritten

    return lines
