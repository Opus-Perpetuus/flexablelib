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


def __check_if_not_none(value):
    return value if value is not None else NONE_VALUE_REPLACEMENT


def __get_single_column_group(line_style: SeparatorLine, widths: tuple, margin: int,
                              empty_column_i: List[int], show_empty: bool) -> Generator:
    for width_i, width in enumerate(widths):
        if not show_empty and width_i not in empty_column_i:
            yield line_style.middle * (width + margin)
        elif show_empty:
            yield line_style.middle * (width + margin)
        else:
            pass


def __join_group(line_style: SeparatorLine, group: Generator) -> str:
    left = __check_if_not_none(line_style.left)
    right = __check_if_not_none(line_style.right)
    intersection = __check_if_not_none(line_style.intersection)
    return ''.join([left, intersection.join(group), right])


def __get_column_lines(line_styles: List[SeparatorLine], widths: tuple, margin: int,
                       empty_column_i: List[int], show_empty: bool) -> Generator:
    for line_style in line_styles:
        if line_style is not None:
            yield __join_group(
                line_style, 
                __get_single_column_group(
                    line_style,
                    widths, 
                    margin,
                    empty_column_i,
                    show_empty
                )
            )
        else:
            yield None


def _get_separators(style_composition: TableComposition, col_widths: tuple,
                    empty_column_i: List[int], show_empty: bool) -> HorizontalComposition:
    superior_header: SeparatorLine = (
        style_composition.superior_header_line
    )
    superior_no_header: SeparatorLine = (
        style_composition.superior_header_line_no_header
    )
    inferior_header: SeparatorLine = (
        style_composition.inferior_header_line
    )
    table_body: SeparatorLine = (
        style_composition.table_body_line
    )
    table_end: SeparatorLine = ( 
        style_composition.table_end_line
    )
    margin: int = style_composition.margin * 2  # multiplied by the sides of a cell

    line_styles = [
        superior_header, 
        inferior_header, 
        superior_no_header, 
        table_body, 
        table_end
    ]
    separator_lines = __get_column_lines(
        line_styles, 
        col_widths, 
        margin,
        empty_column_i,
        show_empty
    )
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


def _get_data_rows(style_composition: TableComposition, 
                   header: tuple, body: tuple, show_headers: bool,
                   empty_rows_i: List[int], show_empty_rows: bool) -> DataRows:
    if show_headers:
        header_lines: SeparatorLine = style_composition.vertical_header_lines
        header_left = __check_if_not_none(header_lines.left)
        header_middle = __check_if_not_none(header_lines.middle)
        header_right = __check_if_not_none(header_lines.right)
        str_header = __convert_single_row_to_string(
            header_left, 
            header_middle, 
            header_right, 
            header
        )
    else:
        str_header = None

    body_lines: SeparatorLine = style_composition.vertical_table_body_lines
    body_left = __check_if_not_none(body_lines.left)
    body_middle = __check_if_not_none(body_lines.middle)
    body_right = __check_if_not_none(body_lines.right)
    strs_body = []
    
    def __get_body_row(row):
        return __convert_single_row_to_string(
            body_left, 
            body_middle, 
            body_right, 
            row
        )
    
    for row_i, row in enumerate(body):
        if not show_empty_rows and row_i not in empty_rows_i:
            strs_body.append(__get_body_row(row))
        elif show_empty_rows:
            strs_body.append(__get_body_row(row))
        else:
            pass
    
    return DataRows(str_header, tuple(strs_body))


if __name__ == '__main__':
    print('Don\'t do it')
