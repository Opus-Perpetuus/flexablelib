from separators import Separators
from utils import Utils
from options import *
isarray = Utils().isarray
flatten = Utils().flatten

class Columns(Separators):
    def __init__(self, body ,styleName='plain', headers=None,
                       colAlignment=None, exBoTo='r', exHeTo='r', 
                       colTypes=None, asColumnus:bool=False,
                       floatSpaces=None, formatExponentials=False):
        super().__init__(colAlignment, self._columnSizes, styleName, 
                         headers, body, exBoTo, exHeTo)
        self.formatExponentials = formatExponentials
        self.floatSpaces = floatSpaces
        self.asColumns = asColumnus
        self.floatColumnInd = None
        self.colTypes = colTypes
        self.fullyFormed = None
        self.cellTypes = None
        self.alignmentsPerType = {
            'bool'    : 'r',
            'str'     : 'l',
            'int'     : 'r',
            'float'   : 'f',
            'NoneType': 'l',
        }
    
    def _columnSizes(self):
        # TODO add support for colouring codes

        if self.headers != None:
            headSizes = [
                max([len(str(row)) for row in headCol]) if (
                    isarray(headCol)
                ) else len(str(headCol))
                for headCol in self.headers
                ]
        else:
            headSizes = [0 for x in self.body]
        bodySizes = [
            max([
                max([len(str(sbRow)) for sbRow in row]) if (
                    isarray(row)
                ) else len(str(row))
                for row in col
            ] )
            for col in self.body
            ]

        sizes = map(lambda x, y: max(x, y), headSizes, bodySizes)
        self.colSizes = list(sizes)

        return self.colSizes

    def _checkHeader(self):
        if self.headers == 'firstrow':
            self.headers = self.body.pop(0)

        return self.headers

    def _transformToColumns(self):
        if not self.asColumns:
            rowsToZip = map(self.__zipMultiRow, self.body)
            zippedRows = list(zip(*rowsToZip))
            zippedRows = [list(x) for x in zippedRows]
            self.body = zippedRows
            if self.headers != None:
                self.headers = self.__zipMultiRow(self.headers)
            self.asColumns = True

        return self.headers, self.body

    def _transformToRows(self):
        if self.asColumns:
            if self.headers != None:
                self.headers = self.__zipHeaderMultiRow(self.headers)
            rows = []
            for row in range(len(self.body[0])):
                if isarray(self.body[0][row]):
                    rows.append(self.__zipMultiRowColumn(row))
                else:
                   rows.append(self.__ZipColumn(row))
            self.body = rows
            self.asColumns = False

        return self.headers, self.body

    def _typify(self):
        """ 
        ## Typify
        Typify to set alignments.
        This also formats float numbers
        """
        create = False
        if self.colAlginment != None:
            return self.colSizes
        else:
            create = True

        typesList = []
        alignmentList = []

        for col in self.body:
            iCol = self.body.index(col)
            identifiedTypes = []
            for row in col:
                if isarray(row):
                    identifiedTypes.append([])
                    for subRow in row:
                        iSubRow = self.body[iCol].index(row)
                        i = self.body[iCol][iSubRow].index(subRow)
                        if subRow != '':
                            identifiedTypes[-1].append(type(subRow))
                            if type(subRow).__name__ == 'float' \
                            and self.floatSpaces != None:
                                self.body[iCol][iSubRow][i] = \
                                    FLOATFMT(subRow, self.floatSpaces)
                            elif type(subRow).__name__ == 'float'\
                            and 'e-' in str(self.body[iCol][iSubRow][i])\
                            and self.formatExponentials:
                                self.body[iCol][iSubRow][i] = \
                                    FLOATFMT(subRow)
                        else:
                            identifiedTypes[-1].append(type(None))
                else:
                    if row != '':
                        identifiedTypes.append(type(row))
                        if type(row).__name__ == 'float' and self.floatSpaces != None:
                            self.body[iCol][self.body[iCol].index(row)] = \
                                FLOATFMT(row, self.floatSpaces)
                        elif type(row).__name__ == 'float'\
                        and 'e-' in str(self.body[iCol][self.body[iCol].index(row)])\
                        and self.formatExponentials:
                                self.body[iCol][self.body[iCol].index(row)] = \
                                    FLOATFMT(row)
                    else:
                        identifiedTypes.append(type(None))
            typesList.append(identifiedTypes)  

        self.cellTypes = typesList

        if self.asColumns:
            self.colTypes = list(map(self.__obtainColumnTypes, self.cellTypes))

        self.colAlginment = []
        for type_ in self.colTypes:
            self.colAlginment.append(self.alignmentsPerType[type_.__name__])

        return self.colTypes, self.colAlginment

    def _alignFloatColumns(self):
        """ This must be done before calculating col sizes """
        floatColumnInd = [
            i for i in range(len(self.colTypes)) if self.colTypes[i] == float
            ]
        
        leftColumnSpacing  = []
        rightColumnSpacing = []
        leftSpaces = []
        rightSpaces = []
        for i in floatColumnInd:
            leftSpace = []
            rightSpace = []
            for row in range(len(self.body[i])):
                if isarray(self.body[i][row]):
                    for subRow in range(len(self.body[i][row])):
                        formated = str(self.__checkFlatDot(self.body[i][row][subRow]))
                        if formated != '':
                            if '.' in formated:
                                sides = formated.split('.')
                                leftSpace.append(len(sides[0]) )
                                rightSpace.append(len(sides[1]) )
                            else:
                                leftSpace.append(len(formated))
                                rightSpace.append(-1)
                else:
                    formated = str(self.__checkFlatDot(self.body[i][row]))
                    if formated != '':
                        if '.' in formated:
                            sides = formated.split('.')
                            leftSpace.append(len(sides[0]) )
                            rightSpace.append(len(sides[1]))
                        else:
                            leftSpace.append(len(formated))
                            rightSpace.append(-1)
            
            leftColumnSpacing.append(max(leftSpace))
            rightColumnSpacing.append(max(rightSpace))
            leftSpaces.append(leftSpace)
            rightSpaces.append(rightSpace)
        
        leftSpaces = [
            [leftColumnSpacing[leftSpaces.index(column)] - space for space in column] 
            for column in leftSpaces
            ]
        rightSpaces = [
            [rightColumnSpacing[rightSpaces.index(column)] - space for space in column] 
            for column in rightSpaces
            ]
        diffs = []
        for col in floatColumnInd:
            diffs.append([])
            for row in self.body[col]:
                if isarray(row):
                    diffs[-1].append(len(str(row[0])))
                else:
                    diffs[-1].append(0)

        aligned = list(map(self.__alignFloatColum, floatColumnInd, leftSpaces, rightSpaces, diffs))
        return aligned

    def _alignColumns(self):
        margin = self.style.tableOptions.margin
        if self.colSizes != None:
            for x in range(len(self.body)):
                toWhere = self.colAlginment[x]
                colSize = self.colSizes[x]
                for y in range(len(self.body[x])):
                    if toWhere == 'l':
                        self._ljustBodyCell(x, y, colSize, ' ')
                    elif toWhere == 'c':
                        self._centerBodyCell(x, y, colSize, ' ')
                    elif toWhere == 'r':
                        self._rjustBodyCell(x, y, colSize, ' ')
                    self._addBodySpacing(x, y, margin, margin, 0)

        return self.body

    def _alignHeaders(self):
        margin = margin = self.style.tableOptions.margin
        if self.colSizes != None and self.headers != None:
            for x in range(len(self.headers)):
                toWhere = self.colAlginment[x]
                colSize = self.colSizes[x]
                if toWhere == 'l':
                    self._ljustHeadCell(x, colSize, ' ')
                elif toWhere == 'c' or toWhere == 'f':
                    self._centerHeadCell(x, colSize, ' ')
                elif toWhere == 'r':
                    self._rjustHeadCell(x, colSize, ' ')
                self._addHeaderSpacing(x, margin, margin)

        return self.headers

    def _addVerticalSeparators(self):
        if not self.asColumns:
            if self.headers != None:
                rows = []
                midChar = self.__checkNone(
                    self.style.verticalComposition.header.middle)
                leftChar = self.__checkNone(
                    self.style.verticalComposition.header.left)
                rightChar = self.__checkNone(
                    self.style.verticalComposition.header.right)
                if isarray(self.headers[0]):
                    for row in range(len(self.headers)):
                        middle = f'{midChar}'.join(self.headers[row])
                        fullHeadRow = ''.join([leftChar, middle, rightChar])
                        rows.append(fullHeadRow)
                else:
                    middle = f'{midChar}'.join(self.headers)
                    fullHeadRow = ''.join([leftChar, middle, rightChar])
                    rows.append(fullHeadRow)

                self.headers = rows

            multiRows = []
            midChar = self.__checkNone(
                self.style.verticalComposition.tableBody.middle)
            leftChar = self.__checkNone(
                self.style.verticalComposition.tableBody.left)
            rightChar = self.__checkNone(
                self.style.verticalComposition.tableBody.right)
            for row in range(len(self.body)):
                multiRows.append([])
                for subRow in range(len(self.body[row])):
                    middle = f'{midChar}'.join(self.body[row][subRow])
                    fullBodyRow = ''.join([leftChar, middle, rightChar])
                    multiRows[-1].append(fullBodyRow)

            for multiRow in multiRows:
                if len(multiRow) == 1:
                    multiRows[multiRows.index(multiRow)] = multiRow
                else:
                    fullMultiRow = '\n'.join(multiRow)
                    multiRows[multiRows.index(multiRow)] = fullMultiRow

            self.body = multiRows

        return self.headers, self.body

    def _unifyAll(self):
        if self.formedSeparators != None:
            horComp = self.formedSeparators
            headSup = self.__checkNoneHeader(horComp.headerSuperior)
            headInf = self.__checkNoneHeader(horComp.headerInferior, True)
            NoneHea = self.__checkNoneHeader(horComp.startsWithNoHeader)
            tabBody = self.__checkNoneHeader(horComp.tableBody, True)
            tablEnd = self.__checkNoneHeader(horComp.tableEnd)

            if self.headers != None:
                headInterior = '\n'.join(self.headers)
                header = ''.join([headSup, headInterior, headInf])
                subrows = []
                for multiRow in self.body:
                    subrowInt = ''.join(multiRow)
                    subrows.append(subrowInt)
                body = f'{tabBody}'.join(subrows)
                self.fullyFormed = ''.join([header, body, '\n', tablEnd])
            else:
                subrows = []
                for multiRow in self.body:
                    subrowInt = ''.join(multiRow)
                    subrows.append(subrowInt)
                body = f'{tabBody}'.join(subrows)
                self.fullyFormed = ''.join([NoneHea, body, '\n', tablEnd])

            return self.fullyFormed

    def __checkNoneHeader(self, x, notEndOrStart=False):
        if x == None:
            return ''
        else:
            if notEndOrStart:
                start = '\n'
            else:
                start = ''

            return ''.join([start, x])

    def __checkNone(self, x):
        if x == None:
            return ''
        else:
            return x

    def __checkFlatDot(self, number):
        if not self.formatExponentials:
            if isinstance(number, float):
               return '{:.2f}'.format(number)
        else:
            return number

    def __alignFloatColum(self, index, leftSpacings, rightSpacings, diffs):
        xs = [index for _ in leftSpacings]
        ys = [i for i in range(len(xs))]
        al = list(map(self._addBodySpacing, xs, ys, leftSpacings, rightSpacings, diffs))

        return al

    def __obtainColumnTypes(self, column):
        column = flatten(column)
        # print(column)        
        if str in column:
            return str
        elif (int in column and float not in column) and bool not in column:
            return int
        elif (float in column or int in column) and bool not in column:
            return float
        elif (bool in column and int not in column) and float not in column:
            return bool
        elif (bool in column or int in column) and float not in column:
            return int
        elif bool in column or int in column or float in column:
            return str
        else:
            return type(None)

    def __ZipColumn(self, index):
        row = []
        for column in range(len(self.body)):
            row.append(self.body[column][index])

        return [row]

    def __zipMultiRowColumn(self, index):
        multiRow = []
        for column in range(len(self.body)):
            multiRow.append(self.body[column][index])

        return [list(x) for x in zip(*multiRow)]
        
    def __zipHeaderMultiRow(self, row):
        if not isarray(row[0]):
            return row
        else:
            zpd = list(zip(*row))
            zpd = [list(x) for x in zpd]
            return zpd

    def __zipMultiRow(self, row):
        if len(row) == 1:
            return row[0]
        else:
            zpd = list(zip(*row))
            zpd = [list(x) for x in zpd]
            return zpd

    def __getUnifyedHeaderAndBody(self):
        if self.asColumns:
            body = self.body
            for i in range(len(self.headers)):
                body[i].insert(0, self.headers[i])
            return body
        else:
            pass


if __name__ == '__main__':
    def main(style, headers):
        a = 1.0 / 96516.51698

        data = [
            ['H1'           , 'H2'      , 'H3'     , 'H4' , 'H5' , 'H4',      ],
            ['Data1'        , a         , True     , True , True , 1   ,      ],
            ['othe1'        , 16.144    , False    , False, False, 4566,      ],
            ['othe1'        , 1229.51155, 'FA\nLSE', 12   , 12.25, 12  , 11   ],
            ['othe1'        , 29.2      , False    , 13   , 13   , 13  , 54654],
            ['othe1'        , 548498.165, False    , 13   , 13   , 13  , 5    ],
            ['othe1'        , 29.545    , False    , 13   , 13   , 13  , 14   ]
        ]
        
        columns = Columns(data, style, headers=headers, formatExponentials=True)
        columns._checkHeader()
        columns._adjustCellsPerRow()
        columns._wrapCells()
        columns._transformToColumns()
        types = columns._typify()
        columns._alignFloatColumns()
        columns._columnSizes()
        columns._makeSeparators()
        columns._alignHeaders()
        columns._alignColumns()
        columns._transformToRows()
        columns._addVerticalSeparators()
        table = columns._unifyAll()

        print(table)

    styles = ['clean', 'windows_alike', 'curly_grid', 'curlyg_ebody', 'pipes', 'bd_bl_empty',
              'sim_head_bd_bl', 'simple', 'simple_head_bold', 'curlyg_empty', 'grid_eheader',
              'grid_ebody','grid_empty', 'grid']

    for style in styles:
        for head in ['firstrow', None, ['H1', 'H2', 'HEADER\nMULTIROW', 'H4' , 'H5' , 'H4',]]:
            main(style, head)
            print()
