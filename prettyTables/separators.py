""" TABLE SEPARATORS """

from styleCompositions import __style_compositions, \
    HorizontalComposition, TableComposition, SeparatorLine
from typing import List, Generator

NONE_VALUE_REPLACEMENT = ''


def __get_single_column_group(line_style: SeparatorLine, widths: tuple, margin: int) -> Generator:
    for width in widths:
        yield line_style.middle * (width + margin)


def __join_group(line_style: SeparatorLine, group: Generator) -> str:
    left = line_style.left if line_style.left is not None else NONE_VALUE_REPLACEMENT
    right = line_style.right if line_style.right is not None else NONE_VALUE_REPLACEMENT
    return ''.join([left, line_style.intersection.join(group), right])


def __get_column_lines(line_styles: List[SeparatorLine], widths: tuple, margin: int) -> Generator:
    for line_style in line_styles:
        if line_style is not None:
            yield __join_group(line_style, __get_single_column_group(line_style, widths, margin))
        else:
            yield None


def _get_separators(style_name: str, col_widths: tuple) -> HorizontalComposition:
    style_composition: TableComposition = __style_compositions.__getattribute__(style_name)
    superior_header: SeparatorLine = style_composition.superior_header_line
    superior_no_header: SeparatorLine = style_composition.superior_header_line_no_header
    inferior_header: SeparatorLine = style_composition.inferior_header_line
    table_body: SeparatorLine = style_composition.table_body_line
    table_end: SeparatorLine = style_composition.table_end_line
    margin: int = style_composition.margin * 2  # multiplied by the sides of a cell

    line_styles = [superior_header, inferior_header, superior_no_header, table_body, table_end]
    separator_lines = __get_column_lines(line_styles, col_widths, margin)
    horizontal_comp = HorizontalComposition(*separator_lines)
    print(horizontal_comp)

    return horizontal_comp


if __name__ == '__main__':
    print('Don\'t do it')
