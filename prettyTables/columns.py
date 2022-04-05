from typing import List

from .cells import _center_cell, _ljust_cell, _rjust_cell, _add_cell_spacing
from .style_compositions import TableComposition
from .utils import is_some_instance
from .options import DEFAULT_FILL_CHAR


def __get_column_type(column):
    if 'str' in column:
        return 'str'
    elif 'bytes' in column and 'float' not in column and 'bool' not in column and 'int' not in column:
        return 'bytes'
    elif 'int' in column and 'float' not in column and 'bool' not in column:
        return 'int'
    elif 'float' in column or 'int' in column and 'bool' not in column:
        return 'float'
    elif 'bool' in column and 'int' not in column and 'float' not in column:
        return 'bool'
    elif 'bool' in column or 'int' in column and 'float' not in column:
        return 'int'
    elif 'bool' in column or 'int' in column or 'float' in column:
        return 'str'
    else:
        return 'NoneType'


_alignments_per_type = {
    'bool': 'r',
    'str': 'l',
    'int': 'r',
    'float': 'f',
    'bytes': 'b',
    'NoneType': 'l',
}


def _column_sizes(columns: dict, show_headers: bool):
    # TODO add support for colouring codes

    if show_headers:
        head_sizes = [
            max([len(str(row)) for row in column['header']]) if (
                is_some_instance(column['header'], tuple, list)
            ) else len(str(column['header']))
            for _, column in columns.items()
        ]
    body_sizes = [
        max([
            max([len(str(sbRow)) for sbRow in row]) if (
                is_some_instance(row, tuple, list)
            ) else len(str(row))
            for row in column['data']
        ])
        for _, column in columns.items()
    ]

    if show_headers:
        sizes = list(map(lambda x, y: max(x, y), head_sizes, body_sizes))
    else:    
        sizes = body_sizes

    return sizes


def _typify_column(column):  # TODO make typify work with missing val to not alter column type
    """
    Get the types of the column and it's alignments
    """
    # create = False
    # if column_alignment is not None:
    #     return colSizes
    # else:
    #     create = True

    identified_types = []

    for row in column:
        if row != '':
            identified_types.append(type(row).__name__)
        else:
            identified_types.append(type(None).__name__)

    column_type = __get_column_type(identified_types)
    column_alignment = _alignments_per_type[column_type]

    return identified_types, column_type, column_alignment


def __align_single_cell(cell, col_width, to_where, margin):
    new_cell = cell
    if to_where == 'l':
        new_cell = _ljust_cell(cell, col_width, DEFAULT_FILL_CHAR)
    elif to_where == 'c':
        new_cell = _center_cell(cell, col_width, DEFAULT_FILL_CHAR)
    elif to_where in ['r']:
        new_cell = _rjust_cell(cell, col_width, DEFAULT_FILL_CHAR)
    new_cell = _add_cell_spacing(new_cell, margin, margin, 0)
    return new_cell


def _align_columns(style_composition: TableComposition, columns,
                   col_alignments: List[str], col_widths: List[int]):
    margin = style_composition.margin

    for column_i, column in enumerate(columns):
        aligned_column = list()
        to_where = col_alignments[column_i]
        col_width = col_widths[column_i]
        for row_i, cell in enumerate(column):
            new_cell = __align_single_cell(cell, col_width, to_where, margin)
            if is_some_instance(new_cell, tuple, list):
                aligned_column.append(tuple(new_cell))
            else:
                aligned_column.append(new_cell)
        yield tuple(aligned_column)


def _align_headers(style_composition: TableComposition, headers,
                   col_alignments: List[str], col_widths: List[int]):
    margin = style_composition.margin

    for column_i, column in enumerate(headers):
        to_where = col_alignments[column_i]
        col_width = col_widths[column_i]
        if is_some_instance(column, tuple, list):
            yield tuple(map(
                lambda cell: __align_single_cell(cell, col_width, to_where, margin),
                column
            ))
        else:
            yield __align_single_cell(column, col_width, to_where, margin)


if __name__ == '__main__':
    print('Hey! This is not to be executed.')
