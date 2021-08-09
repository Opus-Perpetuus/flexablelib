'''
ADJUST
Cells and column formatting

Here the column widths are established, and the cells' spaces put.
'''

from functools import reduce
from typing import Union
import textwrap

from .constants import *
from .utils import *


class TableMeasures(object):

    def __init__(self,
                 expandToWindow: bool,
                 headers: list[list], 
                 headerIncluded: bool,
                 rawData: list[list],
                 cellMargin: int,
                 composition: tuple,
                 windowSize: int,
                 adjustWidthTo: str,
                 adjustHeaderWidthTo: str,
                 ):
        self.verticalDivisions =  composition.verticalComposition.tableBody
        self.lenOfMidDiv = len(self.verticalDivisions.middle)
        self.lenOfRight = len(self.verticalDivisions.right)
        self.lenOfLeft = len(self.verticalDivisions.left)
        self.windowMeasures = windowSize
        self.windowWidth = self.windowMeasures.columns
        self.expandToWindow = expandToWindow
        self.adjustWidthTo = adjustWidthTo
        self.adjustHeaderWidthTo = adjustHeaderWidthTo
        self.cellMargin = cellMargin
        self.headerIncluded = headerIncluded
        self.headers = headers
        self.rawData = rawData

    @property
    def totalBody(self):
        'headers + rawData'
        data = self.rawData + [self.headers]
        return data

    def addCells(self, difference, index, side):
        '''
        Adds blank strings ('') until the difference is 0
        '''
        # Will inly do something if there's a difference of widths
        if difference > 0:
            while difference != 0:
                # [..., ['' , 'data', ...], ...]
                #        /\
                #        Inserts at start
                if side == 'right':
                    self.rawData[index].insert(0, '')
                    self.headers.append('')

                # [..., ['data', ..., ''], ...]
                #                     /\
                #                     Inserts at end
                elif side == 'left':
                    self.rawData[index].append('')
                    self.headers.insert(0, '')

                difference -= 1

    def makeRowsEquals(self):
        '''
        Here the widths of the data lists are adjusted if there are bigger
        ones or smaller ones.The smaller ones will always be expanded, and 
        not the other way around.

        This example shows the deafult way, with the "adjustWidthTo" option
        deafult 'right'

        ```
        [                       [
        ['dat','dat'      ],    ['dat','dat',''   ],
        ['dat'            ], -> ['dat',''   ,''   ],
        ['dat','dat','dat']     ['dat','dat','dat']
        ]                       ]
        ```
        '''
        # Get the widest row to adjust the other ones.   
        WidestLine = (max([len(row) for row in self.totalBody]))

        # for each row, compare the lenght with the max width,
        # and add cells if necessary.
        for row in range(0, len(self.rawData)):
            if WidestLine > len(self.totalBody[row]):
                print('ajustando...')
                self.addCells(
                    WidestLine - (len(self.totalBody[row])),
                    row,
                    self.adjustWidthTo if (
                        row > 0
                    ) else self.adjustHeaderWidthTo
                )
        
        print('este: ', self.rawData)
        print('este: ', self.headers)
        return self.rawData, self.headers

    def getTotalTableCellsWidths(self):
        '''
        Here the widths of each cell are obtained iterating trough each
        row of the raw data.

        >>> [                  [
            [cell1, cell2],    [len1, len2],
            [cell3, cell4]  -> [len1, len2]
            ]                  ]
        '''
        
        # Get len of each element in each row.
        cellsWidths = []
        for row in self.totalBody:
            cellsWidths.append([])
            for col in row:
                cellsWidths[-1].append(len(col))

        return cellsWidths

    def getFullColumnWidths(self, cellsWidths):
        '''
        Returns the Width of each column including the margin.
        '''
        # TODO simplify double for cicle

        # Each array in here is a column instead of a row.
        columnOrdenatedWidths = list(zip(*cellsWidths))

        # Here the max of each array is obtained and appended in a
        # single array and are additioned with the product of the margin
        # by 2; it's important to add the margin at the begining, to ensure
        # that the space calculations include it.
        fullColumnWidths = list(
            map(lambda x: max(x) + (self.cellMargin*2), columnOrdenatedWidths)
        )
        
        return fullColumnWidths

    def getMaxWidth(self, columnWidths):        
        '''
        Returns:
            - maxWidthPerCol: A list of the max width of each column to
                fill the window, to be stretched or reduced.    
            - maxWidthOfColumns: The max width of the columns, excluding
                the witdht of the vertical divisions of the table.
        '''

        # The widths of the vertical divisions are substracted of the
        # window width to ensure that the total width of the table, wich
        # includes the divisions, fit the window.
        maxWidthOfColumns = (self.windowWidth - 1) - sum([
            self.lenOfLeft,
            ((self.lenOfMidDiv * len(columnWidths)) - 1),
            self.lenOfRight
        ])

        # The sum of column widths.
        WidthOfColumns = sum(columnWidths)

        # What percentage of the sum represents each column.
        percentages = [column/WidthOfColumns for column in columnWidths]

        # The maximun width per column, obtained multiplying the percentage
        # of each column by the maxWidthOfColumns.
        maxWidthPerCol = [
            (
                round(perc*maxWidthOfColumns) 
            )for perc in percentages
            ]

        # sometimes the new size of the columns exceed the max width, 
        # so this substract that diference of the biggest column.
        newWidthOfColumns = sum(maxWidthPerCol)
        if newWidthOfColumns > maxWidthOfColumns:
            toReduce = maxWidthPerCol.index(max(maxWidthPerCol))
            if maxWidthOfColumns > 0: 
                maxWidthPerCol[toReduce] -= newWidthOfColumns - maxWidthOfColumns

        # Now the margin is substracted of the max widths per column, 
        # to avoid miscalculations in the wrapping of multilines in the
        # cells .
        maxWidthPerColWithoutMargin = [width - (self.cellMargin*2) for width in maxWidthPerCol]

        # Here each column is checked to see if there are 0 len columns 
        # (due to reduced space). If it is the case, the width is
        # incremented to fit the minimu width of a column (constant),
        # and the widest column gets decreased to keep to total width
        # the same 
        for current in range(len(maxWidthPerColWithoutMargin)):

            # the biggest is re-calculated each time in case that the one
            # that was is no longer, because it will be reduced 
            biggestWidth = max(maxWidthPerColWithoutMargin)
            biggestWidth = maxWidthPerColWithoutMargin.index(biggestWidth)

            currentWidth = maxWidthPerColWithoutMargin[current]
            if currentWidth < MIWCOL:
                incremented = 0
                while currentWidth <= MIWCOL:
                    currentWidth += 1
                    incremented += 1
                maxWidthPerColWithoutMargin[current] = currentWidth
                maxWidthPerColWithoutMargin[biggestWidth] -= incremented

        return maxWidthPerColWithoutMargin, maxWidthOfColumns

    def adjustWidthToWindow(self, columnWidths):
        '''
        Returns new columnWidths depending if the expandToWindow option is set to
        True and the size of the window.
        '''
        maxWidthOfTable = self.getMaxWidth(columnWidths=columnWidths)

        if self.expandToWindow == True:
            return maxWidthOfTable[0] # The max widths per column
        else:
            if maxWidthOfTable[1] < sum(columnWidths):
                return maxWidthOfTable[0]
            else:
                return columnWidths

    

class Cells(object):
    '''
    Recives the tabular data and the procesed column widths along with the
    margin to format (add spaces or make multilines) each cell.
    '''

    def __init__(self,
                 tabularData: list[list],
                 headers: Union[list, list[list]],
                 headerIncluded: bool,
                 columnWidths: list,
                 cellMargin: int,
                 alignments,
                 ):
        self.columnWidths = columnWidths
        self.tabularData = tabularData
        self.headers = headers
        self.headerIncluded = headerIncluded
        self.cellMargin = cellMargin
        self.alignments = alignments

    def wrapSingleCell(self, cell, maxWidth):
        '''
        Wrapes the string in the cell by adding a new line scape code
        with the max width as determinant.
        '''
        return textwrap.fill(cell, maxWidth)

    def wrapSingleRow(self, row):
        '''
        Creates a multiline array, being the number lines the number of
        new lines in the cell that contains the most.
        '''
        
        rows = [row]
        linesAdded = 0

        currentCol = 0
        for cell in row:
            parts = cell.splitlines()

            if len(parts)-1 > linesAdded:
                for x in range((len(parts)-1) - linesAdded):
                    linesAdded += 1
                    rows.append(['' for cell in row])
            
            if len(parts) > 1:
                for line in range(len(parts)):
                    rows[line][currentCol] = parts[line]
            
            currentCol += 1
        
        return rows
 
    def wrapRows(self):
        '''
        Makes the tabularData a list of list of lists. Each list of list is a multiline,
        containing the rows that conforms it.
        Returns Nothing.
        '''

        maxWidths = self.columnWidths

        currentCell = 0
        for cell in self.headers:
            currWidth = maxWidths[currentCell]

            if len(cell) > currentCell:
                cell = self.wrapSingleCell(cell, currWidth)
                self.headers[currentCell] = cell
        
        wrapedHeaders = self.wrapSingleRow(self.headers)
        self.headers = wrapedHeaders

        currentRow = 0
        for row in self.tabularData:
            currentCell = 0
            for cell in row:
                currWidth = maxWidths[currentCell]

                if len(cell) > currWidth:
                    cell = self.wrapSingleCell(cell, currWidth)
                    self.tabularData[currentRow][currentCell] = cell
            
                currentCell += 1

            rowToWrap = self.tabularData[currentRow]
            wrapedRow = self.wrapSingleRow(rowToWrap)
            self.tabularData[currentRow] = wrapedRow

            currentRow += 1
        
    def formatSingleCell(self, extraSpace):
        '''
        Calculates the blanks spaces in the left and right of the cell.
        Returns: leftPart, rightPart.
        '''
        # FIX Investigate why some styles result in extra space in the columns

        mrg = self.cellMargin

        if self.alignments == 'left':
            leftPart = ' ' * mrg 
            rightPart = (' ' * extraSpace) + leftPart

        elif self.alignments == 'center':
            leftSpace = extraSpace // 2
            rightSpace = extraSpace - leftSpace
            leftPart = (' ' * mrg) + ' ' * leftSpace
            rightPart = (' ' * mrg) + ' ' * rightSpace

        elif self.alignments == 'right':
            rightPart = ' ' * mrg 
            leftPart = (' ' * extraSpace) + rightPart
        
        return leftPart, rightPart

            

    def format(self):
        '''
        Here the aligments of the text in the cells occurs by adding
        spaces.
        '''
        
        widths = self.columnWidths
        dataToFormat = self.tabularData

        # Get the len of the string in the current cell.
        lenOfStr = lambda mtline, row, col: len(dataToFormat[mtline][row][col])

        currentMultiline = 0 # The actual multiline in wich rows to work.
        for multiline in self.tabularData:
            currentRow = 0 # Current row of the tabularData iterated.
            for row in multiline:
                currentCol = 0 # It's the same that the current cell.
                for cell in row:
                    extraSpace = widths[currentCol] - lenOfStr(currentMultiline, currentRow, currentCol)
                    formatForCel = self.formatSingleCell(extraSpace)
                    left = formatForCel[0]
                    right = formatForCel[1]
                    dataToFormat[currentMultiline][currentRow][currentCol] = left + cell + right 

                    currentCol += 1
                currentRow += 1
            currentMultiline += 1

        return dataToFormat
    