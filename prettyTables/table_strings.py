""" TABLE SEPARATORS """

from typing import List, Generator
from collections import namedtuple

from .style_compositions import HorizontalComposition, TableComposition, SeparatorLine
from .options import NONE_VALUE_REPLACEMENT
from .utils import is_multi_row


DataRows = namedtuple(
    'DataRows',
    [
        'header_row',
        'body_rows'
    ]
)


def __get_single_column_group(line_style: SeparatorLine, widths: tuple, margin: int) -> Generator:
    for width in widths:
        yield line_style.middle * (width + margin)


def __join_group(line_style: SeparatorLine, group: Generator) -> str:
    left = line_style.left if line_style.left is not None else NONE_VALUE_REPLACEMENT
    right = line_style.right if line_style.right is not None else NONE_VALUE_REPLACEMENT
    intersection = line_style.intersection if line_style.intersection is not None else NONE_VALUE_REPLACEMENT
    return ''.join([left, intersection.join(group), right])


def __get_column_lines(line_styles: List[SeparatorLine], widths: tuple, margin: int) -> Generator:
    for line_style in line_styles:
        if line_style is not None:
            yield __join_group(line_style, __get_single_column_group(line_style, widths, margin))
        else:
            yield None


def _get_separators(style_composition: TableComposition, col_widths: tuple) -> HorizontalComposition:
    superior_header: SeparatorLine = style_composition.superior_header_line
    superior_no_header: SeparatorLine = style_composition.superior_header_line_no_header
    inferior_header: SeparatorLine = style_composition.inferior_header_line
    table_body: SeparatorLine = style_composition.table_body_line
    table_end: SeparatorLine = style_composition.table_end_line
    margin: int = style_composition.margin * 2  # multiplied by the sides of a cell

    line_styles = [superior_header, inferior_header, superior_no_header, table_body, table_end]
    separator_lines = __get_column_lines(line_styles, col_widths, margin)
    horizontal_composition = HorizontalComposition(*separator_lines)

    return horizontal_composition


def __convert_single_row_to_string(left: str, middle: str, right: str, row):
    if is_multi_row(row):
        return '\n'.join(map(
            lambda sb_row: ''.join([left, middle.join([*sb_row]), right]),
            tuple(row)
        ))
    else:
        return ''.join([left, middle.join([*row]), right])


def _get_data_rows(style_composition: TableComposition, header: tuple, body: tuple) -> DataRows:
    header_lines: SeparatorLine = style_composition.vertical_header_lines
    header_left = header_lines.left if header_lines.left is not None else NONE_VALUE_REPLACEMENT
    header_middle = header_lines.middle if header_lines.middle is not None else NONE_VALUE_REPLACEMENT
    header_right = header_lines.right if header_lines.right is not None else NONE_VALUE_REPLACEMENT

    body_lines: SeparatorLine = style_composition.vertical_table_body_lines
    body_left = body_lines.left if body_lines.left is not None else NONE_VALUE_REPLACEMENT
    body_middle = body_lines.middle if body_lines.middle is not None else NONE_VALUE_REPLACEMENT
    body_right = body_lines.right if body_lines.right is not None else NONE_VALUE_REPLACEMENT

    str_header = __convert_single_row_to_string(header_left, header_middle, header_right, header)
    strs_body = tuple(map(
        lambda row: __convert_single_row_to_string(body_left, body_middle, body_right, row),
        body
    ))

    return DataRows(str_header, strs_body)


if __name__ == '__main__':
    print('Don\'t do it')
