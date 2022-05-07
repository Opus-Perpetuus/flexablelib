""" CELL WRAPPING AND ADJUSTMENT """

from .utils import is_some_instance
from .options import FLT_FILTER, INT_FILTER

from textwrap import wrap


def _add_cell_spacing(cell, left: int, right: int, diff_if_empty: int):
    left = ' ' * left  # Space for the left
    right = ' ' * right  # Space for the right
    diff = ' ' * diff_if_empty

    if is_some_instance(cell, tuple, list):
        spaced = list(map(str, cell))
        for part_i, cell_part in enumerate(cell):
            if diff_if_empty != 0 and part_i != 0:
                spaced[part_i] = ''.join([left, diff, right])
            else:
                spaced[part_i] = ''.join([left, cell_part, right])
    else:
        if diff_if_empty != 0:
            spaced = ''.join([left, diff, right])
        else:
            spaced = ''.join([left, cell, right])

    return spaced


def _center_cell(cell, cell_length, fill_char):
    if is_some_instance(cell, tuple, list):
        centered = list(map(str, cell))
        for part_i, cell_part in enumerate(centered):
            centered[part_i] = cell_part.center(cell_length, fill_char)
        centered = tuple(centered)
    else:
        centered = str(cell).center(cell_length, fill_char)

    return centered


def _ljust_cell(cell, cell_length, fill_char):
    if is_some_instance(cell, list, tuple):
        ljusted = list(map(str, cell))
        for part_i, cell_part in enumerate(ljusted):
            ljusted[part_i] = cell_part.ljust(cell_length, fill_char)
        ljusted = tuple(ljusted)
    else:
        ljusted = str(cell).ljust(cell_length, fill_char)

    return ljusted


def _rjust_cell(cell, cell_length, fill_char):
    if is_some_instance(cell, list, tuple):
        rjusted = list(map(str, cell))
        for part_i, cell_part in enumerate(rjusted):
            rjusted[part_i] = cell_part.rjust(cell_length, fill_char)
        rjusted = tuple(rjusted)
    else:
        rjusted = str(cell).rjust(cell_length, fill_char)

    return rjusted


def fljust(string, sides_widhts, __fillchar=' '):
    splitted = string.split('.')
    left_string = splitted[0]
    right_string = splitted[1]
    left_width = sides_widhts[0]
    right_width = sides_widhts[-1]
    left = left_string.rjust(left_width, __fillchar)
    right = right_string.ljust(right_width, __fillchar)
    return '.'.join([left, right])


def __fljust_part(cell_part, cell_length, float_column_sizes, fill_char):
    str_cell = str(cell_part)
    is_float_number = FLT_FILTER(
        str_cell
    ) is not None
    is_int_number = INT_FILTER(
        str_cell
    ) is not None
    if is_float_number:
        return fljust(
            str_cell, 
            float_column_sizes, 
            fill_char
        )
    if is_int_number:
        cell_ = str_cell
        cell_len = len(cell_)
        left_width = float_column_sizes[0]
        fixed_left_width = left_width - cell_len
        right_width = float_column_sizes[-1]
        fixed_right_width = right_width + float_column_sizes[1]
        return _add_cell_spacing(
            str_cell,
            fixed_left_width,
            fixed_right_width,
            0
        )
    else:
        return str_cell.rjust(
            cell_length, fill_char
        )


def _fljust_cell(cell: str, cell_length, fill_char, float_column_sizes):
    if is_some_instance(cell, list, tuple):
        fljusted = list(map(str, cell))
        for part_i, cell_part in enumerate(fljusted):
            fljusted[part_i] = __fljust_part(
                cell_part,
                cell_length,
                float_column_sizes,
                fill_char
            )
        fljusted = tuple(fljusted)
    else:
        fljusted = __fljust_part(
            cell,
            cell_length,
            float_column_sizes,
            fill_char
        )
            
    return fljusted


def _wrap_cells(headers, data, columns=False):
    if columns:
        wrapped = __wrap_columns(headers, data)
    else:
        wrapped = __wrap_rows(headers, data)
    return wrapped


def __wrap_columns(wrapped_headers: list, wrapped_rows: list):
    medium_zipped_columns = []
    for column_i, column in enumerate(wrapped_rows):
        medium_zipped_columns.append(__zip_single_column(column))
    fully_zipped_columns = list(zip(*medium_zipped_columns))
    zipped_headers = __zip_single_column(wrapped_headers)

    return fully_zipped_columns, zipped_headers


def __zip_single_column(row: list):
    if len(row) > 1:
        return list(zip(*row))
    else:
        return row[0]


def __wrap_rows(headers: list, data: list):
    wrapped_headers = None
    if headers is not None:
        wrapped_headers = __wrap_single_row(headers)
    wrapped_data = list(map(__wrap_single_row, data))

    return wrapped_headers, wrapped_data


def __wrap_single_row(data):
    split_cells = list(map(__wrap_cell, data))
    to_add = max([len(x) for x in split_cells])
    composed_row = [['' for x in data] for _ in range(to_add)]

    for cell in range(len(split_cells)):
        for level in range(len(split_cells[cell])):
            composed_row[level][cell] = split_cells[cell][level]

    return composed_row


def __wrap_cell(cell):
    if isinstance(cell, str):
        if cell != '':
            return cell.splitlines()
        else:
            return ['']
    else:
        return [cell]
    
    
def _apply_wrapping_to_cell(cell, width):
    if is_some_instance(cell, list, tuple):
        wrapped = []
        for element in cell:
            print(element, width)
            if width < len(element):
                wrapped += wrap(
                    element, 
                    width, 
                    drop_whitespace=True
                )
            else:
                wrapped.append(element)
        return tuple(wrapped), True
    if width < len(str(cell)):
        return tuple(wrap(
            str(cell), 
            width, 
            drop_whitespace=True
        )), True
    else:
        return cell, False


if __name__ == '__main__':
    print('This shouldn\'t be printing.')
