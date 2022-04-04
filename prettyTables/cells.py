""" CELL WRAPPING AND ADJUSTMENT """

from .utils import is_some_instance, is_list


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


def _wrap_cells(headers, data, columns=False):
    if columns:
        wrapped = __wrap_columns(headers, data)
    else:
        wrapped = __wrap_rows(headers, data)

    return wrapped


def __wrap_columns(wrapped_headers: list, wrapped_rows: list):
    medium_zipped_rows = []
    for row in wrapped_rows:
        medium_zipped_rows.append(__zip_single_row(row))
    fully_zipped_rows = list(zip(*medium_zipped_rows))
    zipped_columns = __zip_single_row(wrapped_headers)

    return fully_zipped_rows, zipped_columns


def __zip_single_row(row: list):
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


if __name__ == '__main__':
    print('This shouldn\'t be printing.')
