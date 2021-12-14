""" CELLS OF THE TABLE """

from utils import is_array


""" 
Cells

Cells of data that conforms the table.
headers : list[any] | tuple[any] | str
body    : list[list[any]] | tuple[tuple[any]]

# Where to adjust body and headers
exBoTo  : 'l' | 'r' 
exHeTo  : 'l' | 'r' 
"""

# def __init__(self, headers, body, exBoTo, exHeTo) -> None:
#     self.headers = headers
#     self.body = body
#     self.exBoTo = exBoTo
#     self.exHeTo = exHeTo
#
# def _addBodySpacing(self, x: int, y: int, left: int, right: int, diffIfEmpty: int):
#     """
#     ### Add Body Spacing
#
#     Add spaces to a specific cell of the body
#     ```
#     x     : int (column)
#     y     : int (row)
#     left  : int (space to ad to the left)
#     right : int (space to ad to the right)
#     ```
#     """
#     l = ' ' * left  # Space for the left
#     r = ' ' * right  # Space for the right
#     d = ' ' * diffIfEmpty
#
#     if is_array(self.body[x][y]):
#         for i in range(len(self.body[x][y])):
#             if diffIfEmpty != 0 and i != 0:
#                 self.body[x][y][i] = ''.join([l, d, r])
#             else:
#                 self.body[x][y][i] = ''.join([l, str(self.body[x][y][i]), r])
#     else:
#         if diffIfEmpty != 0 and i != 0:
#             self.body[x][y] = ''.join([l, f, r])
#         else:
#             self.body[x][y] = ''.join([l, str(self.body[x][y]), r])
#
#     return self.body[x][y]
#
# def _addHeaderSpacing(self, x: int, left: int, right: int):
#     """
#     ### Add Header Spacing
#
#     Add spaces to a specific cell of the header
#     ```
#     x     : int (column)
#     left  : int (space to ad to the left)
#     right : int (space to ad to the right)
#     ```
#     """
#     l = ' ' * left  # Space for the left
#     r = ' ' * right  # Space for the right
#
#     if is_array(self.headers[x]):
#         for i in range(len(self.headers[x])):
#             self.headers[x][i] = ''.join([l, str(self.headers[x][i]), r])
#     else:
#         self.headers[x] = ''.join([l, str(self.headers[x]), r])
#
#     return self.headers[x]
#
# def _centerBodyCell(self, x: int, y: int, cellLen: int, fillchar: str):
#     """
#     ### Center Body Cell
#     ```
#     x        : int (column)
#     y        : int (row)
#     cellLen  : int (width of the cell or column)
#     fillchar : int (char to fill the space)
#     ```
#     """
#     if is_array(self.body[x][y]):
#         for i in range(len(self.body[x][y])):
#             self.body[x][y][i] = str(self.body[x][y][i]).center(cellLen, fillchar)
#     else:
#         self.body[x][y] = str(self.body[x][y]).center(cellLen, fillchar)
#
#     return self.body[x][y]
#
# def _ljustBodyCell(self, x: int, y: int, cellLen: int, fillchar: str):
#     """
#     ### Left Adjust Body Cell
#     ```
#     x        : int (column)
#     y        : int (row)
#     cellLen  : int (width of the cell or column)
#     fillchar : int (char to fill the space)
#     ```
#     """
#     if is_array(self.body[x][y]):
#         for i in range(len(self.body[x][y])):
#             self.body[x][y][i] = str(self.body[x][y][i]).ljust(cellLen, fillchar)
#     else:
#         self.body[x][y] = str(self.body[x][y]).ljust(cellLen, fillchar)
#
#     return self.body[x][y]
#
# def _rjustBodyCell(self, x: int, y: int, cellLen: int, fillchar: str):
#     """
#     ### Right Adjust Body Cell
#     ```
#     x        : int (column)
#     y        : int (row)
#     cellLen  : int (width of the cell or column)
#     fillchar : int (char to fill the space)
#     ```
#     """
#     if is_array(self.body[x][y]):
#         for i in range(len(self.body[x][y])):
#             self.body[x][y][i] = str(self.body[x][y][i]).rjust(cellLen, fillchar)
#     else:
#         self.body[x][y] = str(self.body[x][y]).rjust(cellLen, fillchar)
#
#     return self.body[x][y]
#
# def _centerHeadCell(self, x: int, cellLen: int, fillchar: str):
#     """
#     ### Center Head Cell
#     ```
#     x        : int (column)
#     cellLen  : int (width of the cell or column)
#     fillchar : int (char to fill the space)
#     ```
#     """
#     if is_array(self.headers[x]):
#         for i in range(len(self.headers[x])):
#             self.headers[x][i] = str(self.headers[x][i]).center(cellLen, fillchar)
#     else:
#         self.headers[x] = str(self.headers[x]).center(cellLen, fillchar)
#
#     return self.headers[x]
#
# def _ljustHeadCell(self, x: int, cellLen: int, fillchar: str):
#     """
#     ### Left Adjust Head Cell
#     ```
#     x        : int (column)
#     cellLen  : int (width of the cell or column)
#     fillchar : int (char to fill the space)
#     ```
#     """
#     if is_array(self.headers[x]):
#         for i in range(len(self.headers[x])):
#             self.headers[x][i] = str(self.headers[x][i]).ljust(cellLen, fillchar)
#     else:
#         self.headers[x] = str(self.headers[x]).ljust(cellLen, fillchar)
#
#     return self.headers[x]
#
# def _rjustHeadCell(self, x: int, cellLen: int, fillchar: str):
#     """
#     ### Right Adjust Head Cell
#     ```
#     x        : int (column)
#     cellLen  : int (width of the cell or column)
#     fillchar : int (char to fill the space)
#     ```
#     """
#     if is_array(self.headers[x]):
#         for i in range(len(self.headers[x])):
#             self.headers[x][i] = str(self.headers[x][i]).rjust(cellLen, fillchar)
#     else:
#         self.headers[x] = str(self.headers[x]).rjust(cellLen, fillchar)
#
#     return self.headers[x]


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


#
# def _adjustCellsPerRow(self):
#     """
#     ### Adjust Cells Per Row
#
#     This makes the cells per row the same  (if different)
#     """
#     if self.headers is not None:
#         hlen = len(self.headers)
#     else:
#         hlen = 0
#     mlen = max([len(x) for x in self.body] + [hlen])
#
#     if self.headers is not None:
#         if hlen < mlen:
#             self.headers = self.__adjustSingleRow(self.headers, mlen - hlen, True)
#     for row in range(len(self.body)):
#         blen = len(self.body[row])
#         if blen < mlen:
#             self.body[row] = self.__adjustSingleRow(self.body[row], mlen - blen)
#
#     return self.headers, self.body
#

#

#
# def __adjustSingleRow(self, row, diff, header=False):
#     for _ in range(diff):
#         if header:
#             if self.exHeTo == 'l':
#                 row.insert(0, '')
#             elif self.exHeTo == 'r':
#                 row.append('')
#         else:
#             if self.exBoTo == 'l':
#                 row.insert(0, '')
#             elif self.exBoTo == 'r':
#                 row.append('')
#
#     return row


if __name__ == '__main__':
    print('This shouldn\'t be printing.')
