"""
Small helpers shared by the test modules.

Kept out of ``conftest.py`` on purpose: a conftest is loaded by pytest as a
plugin, and importing it as a normal module from test files is fragile.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Wide enough that no fixture table ever triggers the shrinking branch of
# ``Table.__check_columns_size``. Tests that want that branch ask for a
# narrow terminal explicitly through the ``terminal`` fixture.
DEFAULT_TERMINAL_COLS = 200
DEFAULT_TERMINAL_LINES = 50


def widths_from_border(border_line, intersection):
    """
    Recover the column content widths from a horizontal separator line.

    A separator is built as ``middle * (width + margin)`` per column, joined by
    the style's intersection character, where ``margin`` already counts both
    sides. With ``CELL_MARGIN`` of 1 each segment is ``width + 2`` long::

        widths_from_border('┌────┬─────────┐', '┬') -> [2, 7]

    Only usable with styles whose intersection character differs from their
    middle character.
    """
    inner = border_line[1:-1]
    return [len(segment) - 2 for segment in inner.split(intersection)]


def table_width(rendered):
    """
    The width of the widest line of a rendered table.
    """
    return max(len(line) for line in rendered.splitlines())


def decimal_point_indexes(rendered):
    """
    The index of the decimal point on every line that shows a number.

    A point only counts when it has a digit on each side, so the trimming
    marker ``...`` in a neighbouring cell is not mistaken for one.

    A float column is aligned correctly when this set has a single element.
    """
    indexes = set()
    for line in rendered.splitlines():
        for position, char in enumerate(line):
            if char != '.' or position == 0 or position + 1 == len(line):
                continue
            if line[position - 1].isdigit() and line[position + 1].isdigit():
                indexes.add(position)
                break
    return indexes
