from functools import reduce
from utils import Utils
from constants import *
import compositionSet
import textwrap
import composed

class TableMeasures(object):

    def __init__(self, expandToWindow, rawData,  cellMargin, composition, windowSize):
        self.verticalDivisions =  composition.verticalComposition.tableBody
        self.lenOfMidDiv = len(self.verticalDivisions.middle)
        self.lenOfRight = len(self.verticalDivisions.right)
        self.lenOfLeft = len(self.verticalDivisions.left)
        self.windowMeasures = windowSize
        self.windowWidht = int(self.windowMeasures[1])
        self.expandToWindow = expandToWindow # replace number for boolean
        self.cellMargin = cellMargin
        self.rawData = rawData

    def makeRowsEquals(self):
        '''
        Aqui se comprueba si todas las columnas tienen el mismo ancho.
        '''
        # falta completar comprobación del mismo ancho.

        pass
       
    def getRawDataCellsWidths(self):
        '''
        Here the widths of each cell are obtained iterating trough each
        row of the raw data.

        [[cell1, cell2],[cell3, cell4]] --> [[len1, len2],[len3, len4]]
        '''
        
        # Get len of each element in each row.
        cellsWidths = [
            [
                len(cell) for cell in row
            ] for row in self.rawData
            ]

        return cellsWidths

    def getFullColumnWidths(self, cellsWidths):
        '''
        Returns the Width of each column including the margin.
        '''

        # Each array in here is a column instead of a row.
        columnOrdenatedWidths = [] 
        for col in range(len(cellsWidths[0])):
            columnOrdenatedWidths.append([])
            for row in range(len(cellsWidths)):
                columnOrdenatedWidths[-1].append(cellsWidths[row][col])

        # Here the max of each array is obtained and appended in a
        # single array and are additioned with the product of the margin
        # by 2; it's important to add the margin at the beining, to ensure
        # that the space calculations include it.
        fullColumnWidths = [
            (
                max(singleCol) + (self.cellMargin*2)
            ) for singleCol in columnOrdenatedWidths
            ]
        
        return fullColumnWidths

    def getMaxWidth(self, columnWidths):        
        '''
        Returns:
            - maxWidhtPerCol: A list of the max widht of each column to
                fill the window, to be stretched or reduced.    
            - maxWidhtOfColumns: The max width of the columns, excluding
                the witdht of the vertical divisions of the table.
        '''

        # The widths of the vertical divisions are substracted of the
        # window width to ensure that the total width of the table, wich
        # includes the divisions, fit the window.
        maxWidhtOfColumns = (self.windowWidht - 1) - sum([
            self.lenOfLeft,
            ((self.lenOfMidDiv * len(columnWidths)) - 1),
            self.lenOfRight
        ])

        # The sum of column widths.
        WidhtOfColumns = sum(columnWidths)

        # What percentage of the sum represents each column.
        percentages = [column/WidhtOfColumns for column in columnWidths]

        # The maximun width per column, obtained multiplying the percentage
        # of each column by the maxWidhtOfColumns.
        maxWidhtPerCol = [
            (
                round(perc*maxWidhtOfColumns) 
            )for perc in percentages
            ]

        # sometimes the new size of the columns exceed the max width, 
        # so this substract that diference of the biggest column.
        newWidhtOfColumns = sum(maxWidhtPerCol)
        if newWidhtOfColumns > maxWidhtOfColumns:
            toReduce = maxWidhtPerCol.index(max(maxWidhtPerCol))
            if maxWidhtOfColumns > 0: 
                maxWidhtPerCol[toReduce] -= newWidhtOfColumns - maxWidhtOfColumns

        # Now the margin is substracted of the max widths per column, 
        # to avoid miscalculations in the wrapping of multilines in the
        # cells .
        maxWidhtPerColWithoutMargin = [width - (self.cellMargin*2) for width in maxWidhtPerCol]

        # Here each column is checked to see if there are 0 len columns 
        # (due to reduced space). If it is the case, the width is
        # incremented to fit the minimu width of a column (constant),
        # and the widest column gets decreased to keep to total width
        # the same 
        for current in range(len(maxWidhtPerColWithoutMargin)):

            # the biggest is re-calculated each time in case that the one
            # that was is no longer, because it will be reduced 
            biggestWidth = max(maxWidhtPerColWithoutMargin)
            biggestWidth = maxWidhtPerColWithoutMargin.index(biggestWidth)

            currentWidth = maxWidhtPerColWithoutMargin[current]
            if currentWidth < MIWCOL:
                incremented = 0
                while currentWidth <= MIWCOL:
                    currentWidth += 1
                    incremented += 1
                maxWidhtPerColWithoutMargin[current] = currentWidth
                maxWidhtPerColWithoutMargin[biggestWidth] -= incremented




        return maxWidhtPerColWithoutMargin, maxWidhtOfColumns

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

    def __init__(self, tabularData, columnWidths, cellMargin, alignments):
        self.columnWidths = columnWidths
        self.tabularData = tabularData
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

    # def getWrapInfo(self):
    #     '''
    #     Returns a list of lists. Each is a multiline, and contain the
    #     indexes of the rows that will conform the same line.
    #     '''
    #     multiLines = []

    #     currentLine = 0
    #     for multiline in self.tabularData:
    #         multiLines.append([])
    #         for row in multiline:
    #             multiLines[-1].append(currentLine)
    #             currentLine += 1

    #     return multiLines
    
    def wrapRows(self):
        '''
        Makes the tabularData a list of list's. Each list is a multiline,
        containing the rows that conforms it.

        Returns Nothing.
        '''

        maxWidhts = self.columnWidths

        currentRow = 0
        for row in self.tabularData:
            currentCell = 0
            for cell in row:
                currWidth = maxWidhts[currentCell]

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

        # Get the len of the string in the current cell
        lenOfStr = lambda mtline, row, col: len(dataToFormat[mtline][row][col])

        currentMultiline = 0 # The actual multiline in wich rows to work
        for multiline in self.tabularData:
            currentRow = 0 # Current row of the tabularData iterated.
            for row in multiline:
                currentCol = 0 # It's the same that the curren cell.
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



if __name__ == "__main__":

    pass

    # def isarray(var):

    #     try:
    #         var[0]
    #         return True
    #     except:
    #         return False


    # header = 'first'
    

    # tabularData = [
    #     ['stirpicultural',        '1444', 'String', 'g0jxjq4xk105vy7ss73nb8e7j79ug7kuf8'],
    #     ['stirpiculture',         '13', 'String', 'tt30\n48h0lz5xi38dk41qk2qxat9foj03'],
    #     ['bend culture laxation', '4',  'Word',   'eebmibc23045t7ox1a8ñbcj3321w4123i'],
    #     ['benda\nsap',            '5',  'Word',   'uc3sw\n23ui4wofi6z2qz2v11712zd937t17x'],
    #     ['bendability',           '11', 'String', '48p22n2s2o3eos418977i8r3o358pr97cl2d'],
    #     ]
    
   
    # composition = compositionSet.getCompositions()['bold_borderline']

    
    # for obt in obtainedSeparators:
    #     print(obt)

    
    # # print(obtainedRows)
    # print(obtainedRows.header)
    # for obt in obtainedRows.tableBody:
    #     print(obt, end='')
    

   
    


