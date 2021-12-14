from utils import is_array, is_tuple


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
#
#
# def __get_side_size(formatted):
#     if formatted != '':
#         if '.' in formatted:
#             sides = formatted.split('.')
#             return len(sides[0]), len(sides[1])
#         else:
#             return len(formatted), -1


# class Columns(object):
#     def __init__(self, data, headers, column_types=None, float_spaces=None, format_exponential=False):
#         self.data = data
#         self.headers = headers
#         self.row_count = row_count
#         self.column_count = colum
#         self.columns = None
#         self.column_alignment = []
#         self.format_exponential = format_exponential
#         self.float_spaces = float_spaces
#         self.float_column_ind = None
#         self.column_types = column_types
#         self.fully_formed = None
#         self.cell_types = None

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
            (is_array(column['header']) or is_tuple(column['header']))
        ) else len(str(column['header']))
        for _, column in columns.items()
    ]
    body_sizes = [
        max([
            max([len(str(sbRow)) for sbRow in row]) if (
                (is_array(row) or is_tuple(row))
            ) else len(str(row))
            for row in column['data']
        ])
        for _, column in columns.items()
    ]

    sizes = list(map(lambda x, y: max(x, y), head_sizes, body_sizes))

    return sizes


def _typify_column(column):
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
#
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
#     def _align_columns(self):
#         margin = self.style.table_options.margin
#         if self.colSizes != None:
#             for x in range(len(self.body)):
#                 toWhere = self.column_alignment[x]
#                 colSize = self.colSizes[x]
#                 for y in range(len(self.body[x])):
#                     if toWhere == 'l':
#                         self._ljustBodyCell(x, y, colSize, ' ')
#                     elif toWhere == 'c':
#                         self._centerBodyCell(x, y, colSize, ' ')
#                     elif toWhere == 'r' or toWhere == 'f':
#                         self._rjustBodyCell(x, y, colSize, ' ')
#                     self._addBodySpacing(x, y, margin, margin, 0)
#
#         return self.body
#
#     def _alignHeaders(self):
#         margin = margin = self.style.table_options.margin
#         if self.colSizes != None and self.headers != None:
#             for x in range(len(self.headers)):
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
#         return self.headers
#
#     def _addVerticalSeparators(self):
#         if not self.asColumns:
#             if self.headers != None:
#                 rows = []
#                 midChar = self.__checkNone(
#                     self.style.vertical_composition.header.middle)
#                 leftChar = self.__checkNone(
#                     self.style.vertical_composition.header.left)
#                 rightChar = self.__checkNone(
#                     self.style.vertical_composition.header.right)
#                 if isarray(self.headers[0]):
#                     for row in range(len(self.headers)):
#                         middle = f'{midChar}'.join(self.headers[row])
#                         fullHeadRow = ''.join([leftChar, middle, rightChar])
#                         rows.append(fullHeadRow)
#                 else:
#                     middle = f'{midChar}'.join(self.headers)
#                     fullHeadRow = ''.join([leftChar, middle, rightChar])
#                     rows.append(fullHeadRow)
#
#                 self.headers = rows
#
#             multiRows = []
#             midChar = self.__checkNone(
#                 self.style.vertical_composition.table_body.middle)
#             leftChar = self.__checkNone(
#                 self.style.vertical_composition.table_body.left)
#             rightChar = self.__checkNone(
#                 self.style.vertical_composition.table_body.right)
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
#         return self.headers, self.body
#
# # -----------------------------------------------
#     def _unifyAll(self):
#         if self.formedSeparators is not None:
#             hor_comp = self.formedSeparators
#             head_sup = self.__checkNoneHeader(hor_comp.header_superior)
#             head_inf = self.__checkNoneHeader(hor_comp.header_inferior, True)
#             none_hea = self.__checkNoneHeader(hor_comp.starts_with_no_header)
#             tab_body = self.__checkNoneHeader(hor_comp.table_body, True)
#             tab_end = self.__checkNoneHeader(hor_comp.table_end)
#
#             if self.headers is not None:
#                 headInterior = '\n'.join(self.headers)
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
#         if not self.format_exponential:
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
#             for i in range(len(self.headers)):
#                 body[i].insert(0, self.headers[i])
#             return body
#         else:
#             pass


if __name__ == '__main__':
    print('Hey! This is not to be executed.')
