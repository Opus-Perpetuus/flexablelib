'''
Print formated tabular data in different styles
'''

''' 
FORMATION OF THE TABLE

Main Class.
Here the whole table is formed
'''

from .utils import *
from .adjust import *
from .compose import *
from .compositionSets import StyleCompositions

# TODO Add more documentation to make package easiear to read
# TODO Make the class manage the header separated of the data.

class Table(object):
    '''
    # TABLE
    
    Makes a table out of tabular like data:

    ```
    tabularData: list[list[any]]
    headers: 'first' | list[] | None
    style:  'clean '
            'plain '
            'bold_borderline'
            'grid'
            'windows_alike'
            'thin_borderline'
            'bold_header'
            'pipes'
    strAlign: 'left' | 'center' | 'right'
    adjustWidthsTo: 'left' | 'right'
    adjustHeaderWidthTo: 'left' | 'right'
    expandToWindow: True | False
    '''  
    
    def __init__(
        self,
        tabularData,
        headers=None,
        style='clean',
        strAlign='left',
        adjustWidthsTo = 'right',
        adjustHeaderWidthTo = 'left',
        expandToWindow=False
    ):
        self.adjustHeaderWidthTo = adjustHeaderWidthTo
        self.adjustWidthsTo = adjustWidthsTo
        self.expandToWindow = expandToWindow
        self.strAlign = strAlign
        self.data = tabularData
        self.headers = headers
        self.style = style
        self.headerIncluded = False
        self.composition = getattr(StyleCompositions(), style)
        self.windowSize = Utils.getWIndowsSize()
        self.formatedSeparators = ()
        self.formatedDataRows = ()
        self.formatedCells = []
    
    def sepExists(self, separator):
        """
        This checks if the separator is unused by checking if is None, in which case
        returns an empty ('') string.

        If the separator is used (exists), returns separator + '\\n'
        """

        if separator == None:
            return ''
        else:
            return separator + '\n'

    def compose(self):
        '''
        Joining of all the parts of the table
        '''
        
        # Finished string separators to put in the final table
        headSuperSep = self.sepExists(self.formatedSeparators.headerSuperior)
        headInferSep = self.sepExists(self.formatedSeparators.headerInferior)
        startWithNoHeadSep = self.sepExists(self.formatedSeparators.startsWithNoHeader)
        bodySep = self.sepExists(self.formatedSeparators.tableBody)
        endSep = self.sepExists(self.formatedSeparators.tableEnd)

        # The data rows in arrays so wether or not is multi-line it will join all in 
        # each array with separators. If it is a multi line, it will result in
        # multiple rows betwin two separators, if not, only one, but the structure of 
        # "every table row in arrays" is the same.
        headerRows =  self.formatedDataRows.header
        bodyRows =  self.formatedDataRows.tableBody

        if headerRows == None:
            headerRows = ''

        headerString = ''.join(headerRows)
        completeRows = [''.join(multiline) for multiline in bodyRows]
        bodyString = f'{bodySep}'.join(completeRows)

        # Yes! Here is the final product in a string. A fully formed table :).
        fullTableString = ''.join([
            headSuperSep,
            headerString,
            headInferSep,
            startWithNoHeadSep,
            bodyString,
            endSep
        ])

        return fullTableString
    
    def separateHeader(self):
        '''
        Looks for the headers
        '''
        # HeaderIncluded: tihs variable determines wether if the header comes in the
        # header property or as the first row of the data, in which case the header
        # property will be the string 'fisrst'; in both of this cases, it's value 
        # will be True, in any other case, False.
        headerIncluded = True if (
            self.headers == 'first' or Utils.isarray(self.headers)
            ) else False
        
        # If the header property comes as 'first', the first row of the data will be
        # assigned to that property and poped out of the array of arrays. 
        if self.headers == 'first':
            self.headers = self.data[0]
            self.data.pop(0)
        
        return headerIncluded

    def adjustTableMeasures(self):
        measures = TableMeasures(
            expandToWindow=self.expandToWindow,
            rawData=self.data,
            headers=self.headers,
            headerIncluded=self.headerIncluded,
            cellMargin=self.composition.tableOptions.margin,
            composition=self.composition,
            windowSize=self.windowSize,
            adjustWidthTo=self.adjustWidthsTo,
            adjustHeaderWidthTo=self.adjustHeaderWidthTo
            )
        
        # Make length of all data arrays the same
        equalData, equalHeaders = measures.makeRowsEquals()
        cellsWidths = measures.getTotalTableCellsWidths()
        columnWidths = measures.getFullColumnWidths(cellsWidths)
        adjustedColumnWidths = measures.adjustWidthToWindow(columnWidths)

        return cellsWidths, columnWidths, adjustedColumnWidths, equalData, equalHeaders

    def adjustTableData(self, adjustedWidths):
        
        cellsAdjustment = Cells(
            tabularData=self.data,
            headers=self.headers,
            headerIncluded=self.headerIncluded,
            columnWidths=adjustedWidths,
            cellMargin=self.composition.tableOptions.margin,
            alignments=self.strAlign
            )

        # wrap the rows that exceed the width limit
        cellsAdjustment.wrapRows()

        formatedCells = cellsAdjustment.format()

        return formatedCells
    
    def craftSeparators(self, adjustedWidths):
        separators = Separators(
            headerIncluded=self.headerIncluded,
            alignments=[],                  #TODO add multi-alignments functionality
            cellMargin=self.composition.tableOptions.margin,
            composition=self.composition,
            colsWidth=adjustedWidths
            )
        obtainedSeparators = separators.makeAll()
        
        return obtainedSeparators

    def craftDataRows(self):
        obtainedRows = DataRows(
            adjustedTableCells=self.formatedCells,
            composition=self.composition,
            headerIncluded=self.headerIncluded,
            headers=self.headers
            )
        obtainedRows = obtainedRows.makeAll()
        
        return obtainedRows

    def craftTableStructure(self):
        self.headerIncluded = self.separateHeader()     
        cellsWidths, columnWidths, adjustedColumnWidths, equalData, equalHeaders = self.adjustTableMeasures()
        self.data = equalData
        self.formatedCells = self.adjustTableData(adjustedColumnWidths)
        self.formatedSeparators = self.craftSeparators(adjustedColumnWidths)
        self.formatedDataRows = self.craftDataRows()

        return (cellsWidths,
                columnWidths,
                adjustedColumnWidths,
                equalHeaders,
                equalData,
                self.headerIncluded,
                self.data,
                self.formatedCells,
                self.formatedSeparators,
                self.formatedDataRows)
            
    def make(self):
        '''
        This crafts the separators and data rows of the table.
        Returns a table in the form of a string.
        '''

        craftedTable = self.compose()
            
        return craftedTable



if __name__ == '__main__':

    print('This is not supposed to be executed!')
