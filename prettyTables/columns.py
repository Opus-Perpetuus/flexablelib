from .cells import (
    _center_cell, 
    _ljust_cell, 
    _rjust_cell,
    _fljust_cell,
    _add_cell_spacing
)
from .style_compositions import TableComposition
from .utils import (
    is_some_instance,
    IndexCounter,
    ValuePlacer
)
from .options import DEFAULT_FILL_CHAR, FLT_FILTER, INT_FILTER

from typing import List
from collections import namedtuple


TypeNames = namedtuple(
    'TypeNames',
    [
        'bool_',
        'str_',
        'int_',
        'float_',
        'bytes_',
        'none_type_',
        'index_counter_',
        'value_placer_',
    ]
)


TYPE_NAMES = TypeNames(
    bool_=bool.__name__,
    str_=str.__name__,
    int_=int.__name__,
    float_=float.__name__,
    bytes_=bytes.__name__,
    none_type_=type(None).__name__,
    index_counter_=IndexCounter.__name__,
    value_placer_=ValuePlacer.__name__,
)


ALIGNMENTS_PER_TYPE = {
    TYPE_NAMES.bool_: 'r',
    TYPE_NAMES.str_: 'l',
    TYPE_NAMES.int_: 'r',
    TYPE_NAMES.float_: 'f',
    TYPE_NAMES.bytes_: 'b',
    TYPE_NAMES.none_type_: 'l',
}


CAN_WRAP_TYPES = [
    TYPE_NAMES.str_,
    TYPE_NAMES.none_type_,
    TYPE_NAMES.value_placer_
]


def __check_for_types_in_column(column_types: list, 
                                accepted_types: list):
    for type_ in column_types:
        if type_ not in accepted_types:
            return False
                
    return True


def __is_str_column(column_types: list):
    comprobation = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=list(TYPE_NAMES)
    )
    return comprobation


def __is_byte_column(column_types: list):
    comprobation = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.bytes_,
            TYPE_NAMES.value_placer_
        ]
    )
    return comprobation


def __is_int_column(column_types: list):
    comprobation = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.int_,
            TYPE_NAMES.bool_,
            TYPE_NAMES.value_placer_,
            TYPE_NAMES.index_counter_
        ]
    )
    return comprobation
    
    
def __is_float_column(column_types: list):
    comprobation = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.float_,
            TYPE_NAMES.int_,
            TYPE_NAMES.value_placer_,
        ]
    )
    return comprobation


def __is_bool_column(column_types: bool):
    comprobation = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.bool_,
            TYPE_NAMES.value_placer_
        ]
    )
    return comprobation


def __is_none_type(column_types: list):
    comprobation = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.none_type_,
            TYPE_NAMES.value_placer_
        ]
    )
    return comprobation


def __get_column_type(column_types):
    if __is_none_type(column_types):
        return TYPE_NAMES.none_type_
    # if __is_byte_column(column_types):
    #     return TYPE_NAMES.bytes_
    if __is_int_column(column_types):
        return TYPE_NAMES.int_
    if __is_float_column(column_types):
        return TYPE_NAMES.float_
    if __is_bool_column(column_types):
        return TYPE_NAMES.bool_
    if __is_str_column(column_types):
        return TYPE_NAMES.str_
    else:
        return TYPE_NAMES.none_type_


def __get_single_column_size(column, show_headers):
    head_size = 0
    body_sizes = []
    if show_headers:
        header = column['header']
        if is_some_instance(header, tuple, list):
            head_size += (
                max([len(str(sub_row)) for sub_row in header])
            )
        else:
            head_size += (len(str(header)))
    for row in column['data']:
        if is_some_instance(row, tuple, list):
            body_sizes.append(
                max([len(str(sub_row)) for sub_row in row])
            )
        else:
            body_sizes.append(len(str(row)))
            
    return head_size, max(body_sizes)
            

def __get_max_side_len(row: str, is_float, max_len_of_sides, head_size):
    sides_len = []
    separator = '.'
    row_len = len(row)
    biggest_float_len = sum(max_len_of_sides)
    if head_size > biggest_float_len:
        current_column_size = head_size
    else:
        current_column_size = biggest_float_len
    if is_float and is_float is not None:
        all_sides = row.split(separator)
        sides_len.append(len(all_sides[0]))
        sides_len.append(len(separator))  # Size of the dot
        sides_len.append(len(all_sides[1]))
    elif not is_float and is_float is not None:
        sides_len.append(row_len)
        sides_len.append(0)  # No dot
        sides_len.append(0)
    else:
        if row_len > current_column_size:
            right_and_dot = max_len_of_sides[1] + max_len_of_sides[2]
            corrected_new_len = row_len - right_and_dot
            sides_len.append(corrected_new_len)
            sides_len.append(0)  # No dot
            sides_len.append(0)
            
    return sides_len


def __get_float_column_width(column, show_headers):
    head_size = 0
    if show_headers:
        header = column['header']
        if is_some_instance(header, tuple, list):
            head_size += (
                max([len(str(sub_row)) for sub_row in header])
            )
        else:
            head_size += (len(str(header)))
        
    def compare_one_side(side_i, sides_len):
        if sides_len[side_i] > max_len_of_sides[side_i]:
                max_len_of_sides[side_i] = sides_len[side_i]
                
    def compare_all_sides():
        sum_of_len_of_sides = sum(max_len_of_sides)
        if sum_of_len_of_sides < head_size > 0:
            max_len_of_sides[0] += head_size - sum_of_len_of_sides
            sum_of_len_of_sides = sum(max_len_of_sides)
            
        return sum_of_len_of_sides
    
    max_len_of_sides = []
    def __get_sides_len(row):
        row_ = str(row)
        is_float = FLT_FILTER(row_) is not None
        is_int = INT_FILTER(row_) is not None
        if is_float:
            sides_len = __get_max_side_len(
                row_, 
                is_float=True,
                max_len_of_sides=max_len_of_sides,
                head_size=head_size
            )
        elif is_int:
            sides_len = __get_max_side_len(
                row_, 
                is_float=False,
                max_len_of_sides=max_len_of_sides,
                head_size=head_size
            )
        else:
            sides_len = __get_max_side_len(
                row_, 
                is_float=None,
                max_len_of_sides=max_len_of_sides,
                head_size=head_size
            )
        for side_i in range(len(sides_len)):
            try:
                compare_one_side(side_i, sides_len)
            except IndexError:
                max_len_of_sides.append(sides_len[side_i])
            
    for row in column['data']:
        if is_some_instance(row, tuple, list):
            for sub_row in row:
                __get_sides_len(sub_row)
        else:
            __get_sides_len(row)
    sum_of_len_of_sides = compare_all_sides()
    
    return head_size, sum_of_len_of_sides, max_len_of_sides


def _column_sizes(processed_columns: dict, column_types: dict,  show_headers: bool):
    # TODO add support for colouring codes

    head_sizes = []
    body_sizes = []
    float_column_sizes = None
    for header, column in processed_columns.items():
        if column_types[header] == TYPE_NAMES.float_:
            head_size, body_size, decimal_sides = __get_float_column_width(
                column,
                show_headers
            )
            head_sizes.append(head_size)
            body_sizes.append(body_size)
            try:
                float_column_sizes[header] = decimal_sides
            except TypeError:
                float_column_sizes = {header: decimal_sides}
        else:
            head_size, body_size = __get_single_column_size(
                column, 
                show_headers
            )
            head_sizes.append(head_size)
            body_sizes.append(body_size)

    if show_headers:
        sizes = list(map(lambda x, y: max(x, y), head_sizes, body_sizes))
    else:    
        sizes = body_sizes

    return sizes, float_column_sizes


def _typify_column(column, index_column=False):  # TODO make typify work with missing val to not alter column type
    """
    Get the types of the column and it's alignments
    """
    identified_types = []

    for row in column:
        if index_column:
            identified_types.append(int.__name__)
        elif row != '':
            identified_types.append(type(row).__name__)
        else:
            identified_types.append(type(None).__name__)

    column_type = __get_column_type(identified_types)
    column_alignment = ALIGNMENTS_PER_TYPE[column_type]

    return identified_types, column_type, column_alignment


def __align_single_cell(cell, col_width, to_where, 
                        margin, float_column_sizes: list=None):
    new_cell = cell
    if to_where == 'l':
        new_cell = _ljust_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR
        )
    elif to_where == 'c':
        new_cell = _center_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR
        )
    elif to_where == 'r':
        new_cell = _rjust_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR
        )
    elif to_where == 'f':
        new_cell = _fljust_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR, 
            float_column_sizes
        )
    new_cell = _add_cell_spacing(new_cell, margin, margin, 0)
    return new_cell


def __align_one_column_row(cell, col_width, to_where,
                           margin, float_column_sizes: dict=None):
    new_cell = __align_single_cell(
        cell, 
        col_width, 
        to_where, 
        margin,
        float_column_sizes
    )
    if is_some_instance(new_cell, tuple, list):
        return tuple(new_cell)
    else:
        return new_cell


def __align_one_column(column, column_i, col_alignments, 
                       col_widths, margin, float_column_sizes: dict = None):
    aligned_column = list()
    to_where = col_alignments[column_i]
    col_width = col_widths[column_i]
    for row_i, cell in enumerate(column):
        aligned_column.append(
            __align_one_column_row(
                cell, 
                col_width, 
                to_where, 
                margin,
                float_column_sizes
            )
        )

    yield tuple(aligned_column)


def _align_columns(style_composition: TableComposition, columns, headers,
                   col_alignments: List[str], col_widths: List[int],
                   empty_columns_i: List[int], show_empty: bool, 
                   float_cols_sizes: dict):
    
    margin = style_composition.margin
    def __align_column(column, column_i):
        header = headers[column_i]
        try:
            float_column_sizes = float_cols_sizes[header]
        except KeyError:
            float_column_sizes = None
        yield from __align_one_column(
            column, 
            column_i, 
            col_alignments, 
            col_widths, 
            margin,
            float_column_sizes
        )
    
    for column_i, column in enumerate(columns):
        if not show_empty and column_i not in empty_columns_i:
            yield from __align_column(column, column_i)
        elif show_empty:
            yield from __align_column(column, column_i)
        else:
            continue
    
        
def __align_one_header(column, col_width, to_where, 
                       margin, flaot_column_sizes):
    if is_some_instance(column, tuple, list):
        yield tuple(map(
            lambda cell: __align_single_cell(
                str(cell), 
                col_width, 
                to_where, 
                margin,
                flaot_column_sizes
            ),
            column
        ))
    else:
        yield __align_single_cell(column, col_width, to_where, margin)


def _align_headers(style_composition: TableComposition, headers,
                   col_alignments: List[str], col_widths: List[int],
                   empty_columns_i: List[int], show_empty: bool,
                   float_cols_sizes: dict):
    margin = style_composition.margin
    for column_i, column in enumerate(headers):
        to_where = col_alignments[column_i]
        col_width = col_widths[column_i]
        if is_some_instance(column, tuple, list):
            col_name = ''.join(column)
        else:
            col_name = column
        try:
            float_column_sizes = float_cols_sizes[col_name]
        except KeyError:
            float_column_sizes = None
        if not show_empty and column_i not in empty_columns_i:
            yield from __align_one_header(
                column, 
                col_width, 
                to_where, 
                margin,
                float_column_sizes
            )
        elif show_empty:
            yield from __align_one_header(
                column, 
                col_width, 
                to_where, 
                margin,
                float_column_sizes
            )
        else:
            continue
             


if __name__ == '__main__':
    print('Hey! This is not to be executed.')
