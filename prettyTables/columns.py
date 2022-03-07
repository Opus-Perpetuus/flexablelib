from cells import _center_cell, _ljust_cell, _rjust_cell, _add_cell_spacing
from styleCompositions import TableComposition
from utils import is_some_instance
from typing import List, Union


DEFAULT_FILL_CHAR = ' '


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


# def __get_side_size(formatted):
#     if formatted != '':
#         if '.' in formatted:
#             sides = formatted.split('.')
#             return len(sides[0]), len(sides[1])
#         else:
#             return len(formatted), -1


_alignments_per_type = {
    'bool': 'r',
    'str': 'l',
    'int': 'r',
    'float': 'f',
    'bytes': 'b',
    'NoneType': 'l',
}


def _column_sizes(columns):
    # TODO add support for colouring codes

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

    sizes = list(map(lambda x, y: max(x, y), head_sizes, body_sizes))

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


#     def _align_float_columns(self):
#         """ This must be done before calculating col sizes """
#         float_column_ind = [
#             i for i in range(len(self.column_types)) if self.column_types[i] == float
#         ]
#
#         left_column_spacing = []
#         right_column_spacing = []
#         left_spaces = []
#         right_spaces = []
#         for i in float_column_ind:
#             left_space = []
#             right_space = []
#             for row in range(len(self.body[i])):
#                 if isarray(self.body[i][row]):
#                     for subRow in range(len(self.body[i][row])):
#                         formatted = str(self.__checkFlatDot(self.body[i][row][subRow]))
#                         left, right = __get_side_size(formatted)
#                         left_space.append(left)
#                         right_space.append(right)
#                 else:
#                     formatted = str(self.__checkFlatDot(self.body[i][row]))
#                     left, right = __get_side_size(formatted)
#                     left_space.append(left)
#                     right_space.append(right)
#
#             left_column_spacing.append(max(left_space))
#             right_column_spacing.append(max(right_space))
#             left_spaces.append(left_space)
#             right_spaces.append(right_space)
#
#         left_spaces = [
#             [left_column_spacing[left_spaces.index(column)] - space for space in column]
#             for column in left_spaces
#         ]
#         right_spaces = [
#             [right_column_spacing[right_spaces.index(column)] - space for space in column]
#             for column in right_spaces
#         ]
#         diffs = []
#         for col in float_column_ind:
#             diffs.append([])
#             for row in self.body[col]:
#                 if isarray(row):
#                     diffs[-1].append(len(str(row[0])))
#                 else:
#                     diffs[-1].append(0)
#
#         aligned = list(map(self.__alignFloatColum, float_column_ind, left_spaces, right_spaces, diffs))
#         return aligned
#

#
#         return self.body
#
#     def _alignHeaders(self):
#         margin = margin = self.style.table_options.margin
#         if self.colSizes != None and self.__headers != None:
#             for x in range(len(self.__headers)):
#                 toWhere = self.column_alignment[x]
#                 colSize = self.colSizes[x]
#                 if toWhere == 'l':
#                     self._ljustHeadCell(x, colSize, ' ')
#                 elif toWhere == 'c':
#                     self._centerHeadCell(x, colSize, ' ')
#                 elif toWhere == 'r' or toWhere == 'f':
#                     self._rjustHeadCell(x, colSize, ' ')
#                 self._addHeaderSpacing(x, margin, margin)
#
#         return self.__headers
#
#     def _addVerticalSeparators(self):
#         if not self.asColumns:
#             if self.__headers != None:
#                 __rows = []
#                 midChar = self.__checkNone(
#                     self.style.vertical_composition.header.middle)
#                 leftChar = self.__checkNone(
#                     self.style.vertical_composition.header.left)
#                 rightChar = self.__checkNone(
#                     self.style.vertical_composition.header.right)
#                 if isarray(self.__headers[0]):
#                     for row in range(len(self.__headers)):
#                         middle = f'{midChar}'.join(self.__headers[row])
#                         fullHeadRow = ''.join([leftChar, middle, rightChar])
#                         __rows.append(fullHeadRow)
#                 else:
#                     middle = f'{midChar}'.join(self.__headers)
#                     fullHeadRow = ''.join([leftChar, middle, rightChar])
#                     __rows.append(fullHeadRow)
#
#                 self.__headers = __rows
#
#             multiRows = []
#             midChar = self.__checkNone(
#                 self.style.vertical_composition.__columns.middle)
#             leftChar = self.__checkNone(
#                 self.style.vertical_composition.__columns.left)
#             rightChar = self.__checkNone(
#                 self.style.vertical_composition.__columns.right)
#             for row in range(len(self.body)):
#                 multiRows.append([])
#                 for subRow in range(len(self.body[row])):
#                     middle = f'{midChar}'.join(self.body[row][subRow])
#                     fullBodyRow = ''.join([leftChar, middle, rightChar])
#                     multiRows[-1].append(fullBodyRow)
#
#             for multiRow in multiRows:
#                 if len(multiRow) == 1:
#                     multiRows[multiRows.index(multiRow)] = multiRow
#                 else:
#                     fullMultiRow = '\n'.join(multiRow)
#                     multiRows[multiRows.index(multiRow)] = fullMultiRow
#
#             self.body = multiRows
#
#         return self.__headers, self.body
#
# # -----------------------------------------------
#     def _unifyAll(self):
#         if self.formedSeparators is not None:
#             hor_comp = self.formedSeparators
#             head_sup = self.__checkNoneHeader(hor_comp.header_superior)
#             head_inf = self.__checkNoneHeader(hor_comp.header_inferior, True)
#             none_hea = self.__checkNoneHeader(hor_comp.starts_with_no_header)
#             tab_body = self.__checkNoneHeader(hor_comp.__columns, True)
#             tab_end = self.__checkNoneHeader(hor_comp.table_end)
#
#             if self.__headers is not None:
#                 headInterior = '\n'.join(self.__headers)
#                 header = ''.join([head_sup, headInterior, head_inf])
#                 subrows = []
#                 for multiRow in self.body:
#                     subrowInt = ''.join(multiRow)
#                     subrows.append(subrowInt)
#                 body = f'{tab_body}'.join(subrows)
#                 self.fully_formed = ''.join([header, body, '\n', tab_end])
#             else:
#                 subrows = []
#                 for multiRow in self.body:
#                     subrowInt = ''.join(multiRow)
#                     subrows.append(subrowInt)
#                 body = f'{tab_body}'.join(subrows)
#                 self.fully_formed = ''.join([none_hea, body, '\n', tab_end])
#
#             return self.fully_formed
#
#     def __checkNone(self, x):
#         if x == None:
#             return ''
#         else:
#             return x
#
#     def __checkFlatDot(self, number):
#         if not self.__format_exponential:
#             if isinstance(number, float):
#                 return '{:.2f}'.format(number)
#         else:
#             return number
#
#     def __alignFloatColum(self, index, leftSpacings, rightSpacings, diffs):
#         xs = [index for _ in leftSpacings]
#         ys = [i for i in range(len(xs))]
#         al = list(map(self._addBodySpacing, xs, ys, leftSpacings, rightSpacings, diffs))
#
#         return al
#
#     def __ZipColumn(self, index):
#         row = []
#         for column in range(len(self.body)):
#             row.append(self.body[column][index])
#
#         return [row]
#
#     def __zipMultiRowColumn(self, index):
#         multiRow = []
#         for column in range(len(self.body)):
#             multiRow.append(self.body[column][index])
#
#         return [list(x) for x in zip(*multiRow)]
#
#     def __zipHeaderMultiRow(self, row):
#         if not isarray(row[0]):
#             return row
#         else:
#             zpd = list(zip(*row))
#             zpd = [list(x) for x in zpd]
#             return zpd
#
#     def __zipMultiRow(self, row):
#         if len(row) == 1:
#             return row[0]
#         else:
#             zpd = list(zip(*row))
#             zpd = [list(x) for x in zpd]
#             return zpd
#
#     def __getUnifyedHeaderAndBody(self):
#         if self.asColumns:
#             body = self.body
#             for i in range(len(self.__headers)):
#                 body[i].insert(0, self.__headers[i])
#             return body
#         else:
#             pass


if __name__ == '__main__':
    print('Hey! This is not to be executed.')
