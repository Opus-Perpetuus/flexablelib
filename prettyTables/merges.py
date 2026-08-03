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

from .fast import pad_to_width, visible_width, truncate_to_width


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

    ``spans`` holds one (start, end) pair per column, as slice bounds into the
    line, covering the cell text and its margins but not the separators around
    it. ``separators`` holds the offset of each vertical rule between columns,
    so a horizontal merge knows which characters to paint over.
    """

    spans: List[tuple]
    separators: List[int]


def compute_layout(column_widths, composition) -> Layout:
    """
    Work out the column offsets for a style and set of widths.

    Mirrors how table_strings assembles a row: an optional left rule, then for
    each column its margins and content, with a rule between neighbours and an
    optional one at the end.
    """
    body = composition.vertical_table_body_lines
    margin = 1 if composition.margin else 0

    offset = len(body.left) if body.left is not None else 0
    spans = []
    separators = []

    for index, width in enumerate(column_widths):
        if index:
            if body.middle is not None:
                separators.append(offset)
                offset += len(body.middle)
        cell_width = width + margin * 2
        spans.append((offset, offset + cell_width))
        offset += cell_width

    return Layout(spans, separators)


def _region_bounds(region, layout, index_offset):
    """Slice bounds in a line for the whole horizontal span of a region."""
    first = region.first_column + index_offset
    last = region.last_column + index_offset
    if first >= len(layout.spans) or last >= len(layout.spans):
        return None
    return layout.spans[first][0], layout.spans[last][1]


def apply(lines, row_line_map, regions, column_widths, composition,
          index_offset, filler=' '):
    """
    Rewrite assembled lines so each region renders as one cell.

    ``lines`` is the rendered table split into lines. ``row_line_map`` maps
    each logical row index to the indexes of the physical lines it occupies,
    which differ once wrapping has turned one row into several. Separator
    lines between rows are not in the map; they are found between the mapped
    lines and painted over where a region spans them vertically.

    ``index_offset`` is 1 when the index column is displayed, since region
    coordinates ignore it.

    Returns the rewritten lines.
    """
    if not regions:
        return lines

    layout = compute_layout(column_widths, composition)
    lines = list(lines)
    margin = 1 if composition.margin else 0

    for region in regions:
        bounds = _region_bounds(region, layout, index_offset)
        if bounds is None:
            continue
        start, end = bounds
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
            first_line = lines[target_lines[0]]
            text = first_line[start:end].strip()
        text = str(text)

        if visible_width(text) > span_width:
            text = truncate_to_width(text, span_width)
        painted = (filler * margin
                   + pad_to_width(text, span_width, region.align, filler)
                   + filler * margin)

        # The text sits on the middle line of the block, so a tall merge reads
        # as one cell rather than a label with empty space under it.
        text_line = target_lines[len(target_lines) // 2]
        for line_index in target_lines:
            line = lines[line_index]
            if len(line) < end:
                continue
            replacement = painted if line_index == text_line else filler * (end - start)
            lines[line_index] = line[:start] + replacement + line[end:]

        # Paint over the separator lines that fall inside the block, so the
        # merged region reads as one cell top to bottom.
        #
        # Where such a line meets the rule at the block's right edge, that
        # junction no longer has a line coming in from the left, so the four
        # way character is wrong there. The body rule's own left character is
        # exactly the three-way junction needed ('├' where '┼' was).
        body_rule = composition.table_body_line
        junction = body_rule.left if body_rule is not None else None
        last_column_index = region.last_column + index_offset
        joins_more_columns = last_column_index + 1 < len(layout.spans)

        for line_index in range(min(target_lines), max(target_lines)):
            if line_index in target_lines:
                continue
            line = lines[line_index]
            if len(line) < end:
                continue
            rewritten = line[:start] + filler * (end - start) + line[end:]
            if junction and joins_more_columns and len(rewritten) > end:
                rewritten = rewritten[:end] + junction + rewritten[end + 1:]
            lines[line_index] = rewritten

    return lines
