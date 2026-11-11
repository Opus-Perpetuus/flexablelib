"""
COMPOSITION SETS - STYLES

A composition set is a named tuple which contain the characters
for each part of the table. Here are are the ones currently added.

*This part was based (mainly) in the "tabulate" package structure!

NAMING
------
Every name describes how the table looks, read left to right:

1. The line family: ``single`` (─ │), ``rounded`` (single with ╭ ╮ ╰ ╯),
   ``double`` (═ ║), ``double_frame`` (double outside, single inside),
   ``double_horizontal`` (double horizontals, single verticals),
   ``double_header`` (double box around the header, single body),
   ``dashed``, ``dotted``, ``ascii`` (+ - |), ``tilde`` (ASCII with ~ O
   rules), ``lines`` (horizontal rules only), ``underlined`` (one rule per
   column under the header), ``borderless``, and the text formats
   ``markdown``, ``org``, ``psql`` and ``rst``.
2. ``_double_underline``: the header rule is double (═ or =) while the
   rest of the family is single.
3. ``_rows``: a rule between every body row.
4. ``_open_header`` / ``_open_body`` / ``_open``: no column separators
   inside the header, the body, or both.

The names used before 3.0.0 still work through ``DEPRECATED_STYLE_NAMES``
and emit a ``DeprecationWarning``.
"""

from collections import namedtuple

from .options import INVISIBLE_SEPARATOR, CELL_MARGIN

TableComposition = namedtuple(
    'TableComposition',
    [
        'superior_header_line',
        'inferior_header_line',
        'superior_header_line_no_header',
        'table_body_line',
        'table_end_line',
        'vertical_header_lines',
        'vertical_table_body_lines',
        'margin',
        'align_sensitive',
        'align_indicator',
        'centered_indicator_on_sides',
        'left_and_right_when_centered',
        'lines_with_indicator',
        'align_indicator_margin',
        'always_center_indicator',
    ]
)

HorizontalComposition = namedtuple(
    'HorizontalComposition',
    [
        'superior_header_line',
        'inferior_header_line',
        'superior_header_line_no_header',
        'table_body_line',
        'table_end_line'
    ]
)

SeparatorLine = namedtuple(
    'SeparatorLine',
    [
        'left',
        'middle',
        'intersection',
        'right'
    ]
)

AlignIndicator = namedtuple(
    'AlignIndicator',
    [
        'left',
        'center',
        'right'
    ]   
)

AlignIndicatorIndexes = namedtuple(
    'AlignIndicatorIndexes',
    [
        'left',
        'center',
        'right'
    ]   
)

ALIGN_INDICATOR_INDEXES = AlignIndicatorIndexes(
    *[i for i in range(len(AlignIndicatorIndexes._fields))]
)

Compositions = namedtuple(
    'Compositions',
    [
        # No borders
        'borderless_compact_header_gap',
        'borderless_compact',
        'borderless',

        # Single box lines
        'single',
        'single_rows',
        'single_double_underline_rows',
        'single_double_underline_rows_open_header',
        'single_double_underline_open_body',
        'single_double_underline_open',

        # Single box lines, rounded corners
        'rounded',
        'rounded_rows',
        'rounded_double_underline',
        'rounded_double_underline_open_header',
        'rounded_double_underline_open',

        # Double box lines (all double, double frame, double horizontals, double header box)
        'double_rows',
        'double_frame_rows',
        'double_frame_rows_open_header',
        'double_frame_open_body',
        'double_frame_open',
        'double_horizontal',
        'double_horizontal_rows',
        'double_header',
        'double_header_rows',
        'double_header_open_header',
        'double_header_rows_open_header',
        'double_header_open',

        # Dashed / dotted
        'dashed',
        'dotted_rows',

        # ASCII (+ - | =)
        'ascii_rows',
        'ascii_rounded',
        'ascii_double_underline_rows',
        'ascii_double_underline_open_header',
        'ascii_double_underline_open_body',
        'ascii_double_underline_open',
        'ascii_align_markers',

        # ASCII with tilde rules (~ O)
        'tilde',
        'tilde_rows',
        'tilde_rows_open_header',
        'tilde_open',

        # Horizontal rules only
        'lines_ascii',
        'lines_ascii_double',
        'lines_ascii_header_only',
        'lines_ascii_double_header_only',
        'lines_single',
        'lines_double',
        'lines_single_header_only',
        'lines_double_header_only',

        # Per-column underline
        'underlined_ascii',
        'underlined_single',

        # Text-format tables
        'markdown',
        'markdown_aligned',
        'org',
        'psql',
        'rst',
    ]
)

__style_compositions = Compositions(
    borderless_compact_header_gap=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, INVISIBLE_SEPARATOR, INVISIBLE_SEPARATOR, None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=0,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),

    ###################################
    ####  Box drawing: double mixes ####
    ###################################
    double_horizontal_rows=TableComposition(
        superior_header_line=SeparatorLine('╒', '═', '╤', '╕'),
        inferior_header_line=SeparatorLine('╞', '═', '╪', '╡'),
        superior_header_line_no_header=SeparatorLine('╒', '═', '╤', '╕'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('╘', '═', '╧', '╛'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_horizontal=TableComposition(
        superior_header_line=SeparatorLine('╒', '═', '╤', '╕'),
        inferior_header_line=SeparatorLine('╞', '═', '╪', '╡'),
        superior_header_line_no_header=SeparatorLine('╒', '═', '╤', '╕'),
        table_body_line=None,
        table_end_line=SeparatorLine('╘', '═', '╧', '╛'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_header_rows=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '╦', '╗'),
        inferior_header_line=SeparatorLine('╚', '═', '╩', '╝'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('║', '║', None, '║'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_header=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '╦', '╗'),
        inferior_header_line=SeparatorLine('╚', '═', '╩', '╝'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('║', '║', None, '║'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_header_rows_open_header=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '═', '╗'),
        inferior_header_line=SeparatorLine('╚', '═', '═', '╝'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('║', ' ', None, '║'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_header_open_header=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '═', '╗'),
        inferior_header_line=SeparatorLine('╚', '═', '═', '╝'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('║', ' ', None, '║'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_header_open=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '═', '╗'),
        inferior_header_line=SeparatorLine('╚', '═', '═', '╝'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '─', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '─', '─', '┘'),
        vertical_header_lines=SeparatorLine('║', ' ', None, '║'),
        vertical_table_body_lines=SeparatorLine('│', ' ', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    rounded_double_underline=TableComposition(
        superior_header_line=SeparatorLine('╭', '─', '┬', '╮'),
        inferior_header_line=SeparatorLine('╞', '═', '╪', '╡'),
        superior_header_line_no_header=SeparatorLine('╭', '─', '┬', '╮'),
        table_body_line=None,
        table_end_line=SeparatorLine('╰', '─', '┴', '╯'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    rounded_double_underline_open_header=TableComposition(
        superior_header_line=SeparatorLine('╭', '─', '─', '╮'),
        inferior_header_line=SeparatorLine('╞', '═', '╤', '╡'),
        superior_header_line_no_header=SeparatorLine('╭', '─', '┬', '╮'),
        table_body_line=None,
        table_end_line=SeparatorLine('╰', '─', '┴', '╯'),
        vertical_header_lines=SeparatorLine('│', ' ', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    rounded_double_underline_open=TableComposition(
        superior_header_line=SeparatorLine('╭', '─', '─', '╮'),
        inferior_header_line=SeparatorLine('╞', '═', '═', '╡'),
        superior_header_line_no_header=SeparatorLine('╭', '─', '─', '╮'),
        table_body_line=None,
        table_end_line=SeparatorLine('╰', '─', '─', '╯'),
        vertical_header_lines=SeparatorLine('│', ' ', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', ' ', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ###########################
    ####  Single box lines ####
    ###########################
    single_double_underline_rows=TableComposition(
        superior_header_line=SeparatorLine('┌', '─', '┬', '┐'),
        inferior_header_line=SeparatorLine('╞', '═', '╪', '╡'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    single_double_underline_rows_open_header=TableComposition(
        superior_header_line=SeparatorLine('┌', '─', '─', '┐'),
        inferior_header_line=SeparatorLine('╞', '═', '╤', '╡'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('│', ' ', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    single_double_underline_open_body=TableComposition(
        superior_header_line=SeparatorLine('┌', '─', '┬', '┐'),
        inferior_header_line=SeparatorLine('╞', '═', '╧', '╡'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '─', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '─', '─', '┘'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', ' ', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    single_double_underline_open=TableComposition(
        superior_header_line=SeparatorLine('┌', '─', '─', '┐'),
        inferior_header_line=SeparatorLine('╞', '═', '═', '╡'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '─', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '─', '─', '┘'),
        vertical_header_lines=SeparatorLine('│', ' ', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', ' ', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ###########################
    ####  Double frame     ####
    ###########################
    double_frame_rows=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '╤', '╗'),
        inferior_header_line=SeparatorLine('╠', '═', '╪', '╣'),
        superior_header_line_no_header=SeparatorLine('╔', '═', '╤', '╗'),
        table_body_line=SeparatorLine('╟', '─', '┼', '╢'),
        table_end_line=SeparatorLine('╚', '═', '╧', '╝'),
        vertical_header_lines=SeparatorLine('║', '│', None, '║'),
        vertical_table_body_lines=SeparatorLine('║', '│', None, '║'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_frame_rows_open_header=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '═', '╗'),
        inferior_header_line=SeparatorLine('╠', '═', '╤', '╣'),
        superior_header_line_no_header=SeparatorLine('╔', '═', '╤', '╗'),
        table_body_line=SeparatorLine('╟', '─', '┼', '╢'),
        table_end_line=SeparatorLine('╚', '═', '╧', '╝'),
        vertical_header_lines=SeparatorLine('║', ' ', None, '║'),
        vertical_table_body_lines=SeparatorLine('║', '│', None, '║'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_frame_open_body=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '╤', '╗'),
        inferior_header_line=SeparatorLine('╠', '═', '╧', '╣'),
        superior_header_line_no_header=SeparatorLine('╔', '═', '═', '╗'),
        table_body_line=None,
        table_end_line=SeparatorLine('╚', '═', '═', '╝'),
        vertical_header_lines=SeparatorLine('║', '│', None, '║'),
        vertical_table_body_lines=SeparatorLine('║', ' ', None, '║'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    double_frame_open=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '═', '╗'),
        inferior_header_line=SeparatorLine('╠', '═', '═', '╣'),
        superior_header_line_no_header=SeparatorLine('╔', '═', '═', '╗'),
        table_body_line=None,
        table_end_line=SeparatorLine('╚', '═', '═', '╝'),
        vertical_header_lines=SeparatorLine('║', ' ', None, '║'),
        vertical_table_body_lines=SeparatorLine('║', ' ', None, '║'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),

    ###########################
    ####  ASCII, tilde, md ####
    ###########################
    underlined_ascii=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '-', ' ', None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, ' ', None, None),
        vertical_table_body_lines=SeparatorLine(None, ' ', None, None),
        margin=0,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ascii_double_underline_rows=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '+', '+'),
        inferior_header_line=SeparatorLine('+', '=', '+', '+'),
        superior_header_line_no_header=SeparatorLine('+', '-', '+', '+'),
        table_body_line=SeparatorLine('+', '-', '+', '+'),
        table_end_line=SeparatorLine('+', '-', '+', '+'),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ascii_double_underline_open_header=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '-', '+'),
        inferior_header_line=SeparatorLine('+', '=', '+', '+'),
        superior_header_line_no_header=SeparatorLine('+', '-', '+', '+'),
        table_body_line=None,
        table_end_line=SeparatorLine('+', '-', '+', '+'),
        vertical_header_lines=SeparatorLine('|', ' ', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ascii_double_underline_open_body=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '+', '+'),
        inferior_header_line=SeparatorLine('+', '=', '+', '+'),
        superior_header_line_no_header=SeparatorLine('+', '-', '-', '+'),
        table_body_line=None,
        table_end_line=SeparatorLine('+', '-', '-', '+'),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', ' ', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ascii_double_underline_open=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '-', '+'),
        inferior_header_line=SeparatorLine('+', '=', '=', '+'),
        superior_header_line_no_header=SeparatorLine('+', '-', '-', '+'),
        table_body_line=None,
        table_end_line=SeparatorLine('+', '-', '-', '+'),
        vertical_header_lines=SeparatorLine('|', ' ', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', ' ', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    markdown_aligned=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine('|', '-', '|', '|'),
        superior_header_line_no_header=SeparatorLine('|', '-', '|', '|'),
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=True,
        align_indicator=AlignIndicator(':', ':', ':'),
        centered_indicator_on_sides=True,
        left_and_right_when_centered=False,
        lines_with_indicator=[1, 2],
        align_indicator_margin=CELL_MARGIN,
        always_center_indicator=False
    ),
    tilde_rows=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '+', '+'),
        inferior_header_line=SeparatorLine('O', '~', 'O', 'O'),
        superior_header_line_no_header=SeparatorLine('O', '~', 'O', 'O'),
        table_body_line=SeparatorLine('+', '-', '+', '+'),
        table_end_line=SeparatorLine('O', '~', 'O', 'O'),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    tilde_rows_open_header=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '-', '+'),
        inferior_header_line=SeparatorLine('O', '~', 'O', 'O'),
        superior_header_line_no_header=SeparatorLine('O', '~', 'O', 'O'),
        table_body_line=SeparatorLine('+', '-', '+', '+'),
        table_end_line=SeparatorLine('O', '~', 'O', 'O'),
        vertical_header_lines=SeparatorLine('|', ' ', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    tilde=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '+', '+'),
        inferior_header_line=SeparatorLine('O', '~', 'O', 'O'),
        superior_header_line_no_header=SeparatorLine('O', '~', 'O', 'O'),
        table_body_line=None,
        table_end_line=SeparatorLine('O', '~', 'O', 'O'),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    tilde_open=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '-', '+'),
        inferior_header_line=SeparatorLine('O', '~', '~', 'O'),
        superior_header_line_no_header=SeparatorLine('O', '~', '~', 'O'),
        table_body_line=None,
        table_end_line=SeparatorLine('O', '~', '~', 'O'),
        vertical_header_lines=SeparatorLine('|', ' ', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', ' ', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    org=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine('|', '-', '+', '|'),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ascii_align_markers=TableComposition(
        superior_header_line=SeparatorLine('+', ' ', '+', '+'),
        inferior_header_line=SeparatorLine('+', ' ', '+', '+'),
        superior_header_line_no_header=SeparatorLine('+', ' ', '+', '+'),
        table_body_line=None,
        table_end_line=SeparatorLine('+', ' ', '+', '+'),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=True,
        align_indicator=AlignIndicator('~<~', '~^~', '~>~'),
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[0, 1, 2, 4],
        align_indicator_margin=CELL_MARGIN,
        always_center_indicator=False
    ),

    ###################################
    ####  Horizontal lines only  ####
    ###################################
    underlined_single=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
        superior_header_line_no_header=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
        table_body_line=None,
        table_end_line=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=0,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_ascii=TableComposition(
        superior_header_line=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
        inferior_header_line=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
        table_body_line=None,
        table_end_line=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_ascii_double=TableComposition(
        superior_header_line=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
        inferior_header_line=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
        table_body_line=None,
        table_end_line=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_ascii_header_only=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_ascii_double_header_only=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_single=TableComposition(
        superior_header_line=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
        inferior_header_line=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
        table_body_line=None,
        table_end_line=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_double=TableComposition(
        superior_header_line=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
        inferior_header_line=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
        table_body_line=None,
        table_end_line=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_single_header_only=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    lines_double_header_only=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    ##################
    ####  Dashed  ####
    ##################
    dashed=TableComposition(
        superior_header_line=SeparatorLine('┌', '┄', '┬', '┐'),
        inferior_header_line=SeparatorLine('┝', '╍', '┿', '┥'),
        superior_header_line_no_header=SeparatorLine('┌', '┄', '┬', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '┄', '┴', '┘'),
        vertical_header_lines=SeparatorLine('┊', '┊', None, '┊'),
        vertical_table_body_lines=SeparatorLine('┊', '┊', None, '┊'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),

    ############################################
    ####  Shapes shared with tabled         ####
    ####  https://github.com/zhiburt/tabled ####
    ############################################
    # ascii_rows: full ASCII grid; all rules use '-' (ascii_double_underline_rows uses '=' under the header).
    ascii_rows=TableComposition(
        superior_header_line=SeparatorLine('+', '-', '+', '+'),
        inferior_header_line=SeparatorLine('+', '-', '+', '+'),
        superior_header_line_no_header=SeparatorLine('+', '-', '+', '+'),
        table_body_line=SeparatorLine('+', '-', '+', '+'),
        table_end_line=SeparatorLine('+', '-', '+', '+'),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # single_rows: thin box with body horizontals; header rule is also ─ (not ═).
    single_rows=TableComposition(
        superior_header_line=SeparatorLine('┌', '─', '┬', '┐'),
        inferior_header_line=SeparatorLine('├', '─', '┼', '┤'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # single: single_rows without body horizontals.
    single=TableComposition(
        superior_header_line=SeparatorLine('┌', '─', '┬', '┐'),
        inferior_header_line=SeparatorLine('├', '─', '┼', '┤'),
        superior_header_line_no_header=SeparatorLine('┌', '─', '┬', '┐'),
        table_body_line=None,
        table_end_line=SeparatorLine('└', '─', '┴', '┘'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # rounded: single with rounded corners.
    rounded=TableComposition(
        superior_header_line=SeparatorLine('╭', '─', '┬', '╮'),
        inferior_header_line=SeparatorLine('├', '─', '┼', '┤'),
        superior_header_line_no_header=SeparatorLine('╭', '─', '┬', '╮'),
        table_body_line=None,
        table_end_line=SeparatorLine('╰', '─', '┴', '╯'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # rounded_rows: rounded corners with body horizontals.
    rounded_rows=TableComposition(
        superior_header_line=SeparatorLine('╭', '─', '┬', '╮'),
        inferior_header_line=SeparatorLine('├', '─', '┼', '┤'),
        superior_header_line_no_header=SeparatorLine('╭', '─', '┬', '╮'),
        table_body_line=SeparatorLine('├', '─', '┼', '┤'),
        table_end_line=SeparatorLine('╰', '─', '┴', '╯'),
        vertical_header_lines=SeparatorLine('│', '│', None, '│'),
        vertical_table_body_lines=SeparatorLine('│', '│', None, '│'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # double_rows: double-line box (all ═/║ junctions).
    double_rows=TableComposition(
        superior_header_line=SeparatorLine('╔', '═', '╦', '╗'),
        inferior_header_line=SeparatorLine('╠', '═', '╬', '╣'),
        superior_header_line_no_header=SeparatorLine('╔', '═', '╦', '╗'),
        table_body_line=SeparatorLine('╠', '═', '╬', '╣'),
        table_end_line=SeparatorLine('╚', '═', '╩', '╝'),
        vertical_header_lines=SeparatorLine('║', '║', None, '║'),
        vertical_table_body_lines=SeparatorLine('║', '║', None, '║'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # psql: PostgreSQL-like; header rule only, no outer frame.
    psql=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine(None, '-', '+', None),
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, '|', None, None),
        vertical_table_body_lines=SeparatorLine(None, '|', None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # markdown: GitHub-flavoured markdown pipe table.
    markdown=TableComposition(
        superior_header_line=None,
        inferior_header_line=SeparatorLine('|', '-', '|', '|'),
        superior_header_line_no_header=SeparatorLine('|', '-', '|', '|'),
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # rst: reStructuredText simple table (== rules, space gutters).
    rst=TableComposition(
        superior_header_line=SeparatorLine(None, '=', ' ', None),
        inferior_header_line=SeparatorLine(None, '=', ' ', None),
        superior_header_line_no_header=SeparatorLine(None, '=', ' ', None),
        table_body_line=None,
        table_end_line=SeparatorLine(None, '=', ' ', None),
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # dotted_rows: '.' frame / horizontals and ':' verticals (tabled Style::dots).
    dotted_rows=TableComposition(
        superior_header_line=SeparatorLine('.', '.', '.', '.'),
        inferior_header_line=SeparatorLine(':', '.', ':', ':'),
        superior_header_line_no_header=SeparatorLine('.', '.', '.', '.'),
        table_body_line=SeparatorLine(':', '.', ':', ':'),
        table_end_line=SeparatorLine(':', '.', ':', ':'),
        vertical_header_lines=SeparatorLine(':', ':', None, ':'),
        vertical_table_body_lines=SeparatorLine(':', ':', None, ':'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # ascii_rounded: '.' / "'" corners, no header or body horizontals.
    ascii_rounded=TableComposition(
        superior_header_line=SeparatorLine('.', '-', '-', '.'),
        inferior_header_line=None,
        superior_header_line_no_header=SeparatorLine('.', '-', '-', '.'),
        table_body_line=None,
        table_end_line=SeparatorLine("'", '-', '-', "'"),
        vertical_header_lines=SeparatorLine('|', '|', None, '|'),
        vertical_table_body_lines=SeparatorLine('|', '|', None, '|'),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # borderless: no rules; columns separated by a space (with cell margin).
    # Also the style for background-colour blocks (it replaces 'blocks').
    borderless=TableComposition(
        superior_header_line=None,
        inferior_header_line=None,
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, ' ', None, None),
        vertical_table_body_lines=SeparatorLine(None, ' ', None, None),
        margin=CELL_MARGIN,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    ),
    # borderless_compact: no chrome and no margin (tabled Style::empty base).
    borderless_compact=TableComposition(
        superior_header_line=None,
        inferior_header_line=None,
        superior_header_line_no_header=None,
        table_body_line=None,
        table_end_line=None,
        vertical_header_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        vertical_table_body_lines=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
        margin=0,
        align_sensitive=False,
        align_indicator=None,
        centered_indicator_on_sides=False,
        left_and_right_when_centered=False,
        lines_with_indicator=[],
        align_indicator_margin=0,
        always_center_indicator=False
    )
)


# Names used before 3.0.0 -> current name. Setting one of these still works
# but emits a DeprecationWarning. ``presto`` was identical to ``psql`` and
# ``blocks`` to ``blank``, so both pairs now share one name.
DEPRECATED_STYLE_NAMES = {
    'plain': 'borderless_compact_header_gap',
    'empty': 'borderless_compact',
    'blank': 'borderless',
    'blocks': 'borderless',
    'sharp': 'single',
    'modern': 'single_rows',
    'thin_borderline': 'single_double_underline_rows',
    'th_bd_eheader': 'single_double_underline_rows_open_header',
    'th_bd_ebody': 'single_double_underline_open_body',
    'th_bd_empty': 'single_double_underline_open',
    'modern_rounded': 'rounded_rows',
    'round_edges': 'rounded_double_underline',
    're_eheader': 'rounded_double_underline_open_header',
    're_ebody': 'rounded_double_underline_open',
    'extended': 'double_rows',
    'bold_borderline': 'double_frame_rows',
    'bd_bl_eheader': 'double_frame_rows_open_header',
    'bd_bl_ebody': 'double_frame_open_body',
    'bd_bl_empty': 'double_frame_open',
    'pretty_columns': 'double_horizontal',
    'pretty_grid': 'double_horizontal_rows',
    'bheader_columns': 'double_header',
    'bold_header': 'double_header_rows',
    'beheader_columns': 'double_header_open_header',
    'bold_eheader': 'double_header_rows_open_header',
    'bheader_ebody': 'double_header_open',
    'dashes': 'dashed',
    'dots': 'dotted_rows',
    'ascii': 'ascii_rows',
    'grid': 'ascii_double_underline_rows',
    'grid_eheader': 'ascii_double_underline_open_header',
    'grid_ebody': 'ascii_double_underline_open_body',
    'grid_empty': 'ascii_double_underline_open',
    'sticks': 'ascii_align_markers',
    'tilg_columns': 'tilde',
    'tilde_grid': 'tilde_rows',
    'tilg_eheader': 'tilde_rows_open_header',
    'tilg_empty': 'tilde_open',
    'simple': 'lines_ascii',
    'simple_bold': 'lines_ascii_double',
    'simple_head': 'lines_ascii_header_only',
    'simple_head_bold': 'lines_ascii_double_header_only',
    'sim_th_bl': 'lines_single',
    'sim_bd_bl': 'lines_double',
    'sim_head_th_bl': 'lines_single_header_only',
    'sim_head_bd_bl': 'lines_double_header_only',
    'pwrshll_alike': 'underlined_ascii',
    'clean': 'underlined_single',
    'pipes': 'markdown_aligned',
    'orgtbl': 'org',
    'presto': 'psql',
    're_structured_text': 'rst',
}
