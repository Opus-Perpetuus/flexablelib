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
from .compositionSets import _styleCompositions


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
        startWithNoHeadSep = self.sepExists(self.formatedSeparators.startWithNoHeader)
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
            
    def make(self):
        '''
        This crafts the separators and data rows of the table.
        Returns a table in the form of a string.
        '''

        composition = _styleCompositions[self.style]
        margin = composition.tableOptions.margin
        windowSize = Utils.getWIndowsSize()

        # TODO Make the class manage the header separated of the data.
        # NOTE: This was commented to avoid inserting the header on the data first. 
        # if Utils.isarray(self.headers):
        #     self.data.insert(0, self.headers)
        #     self.headers = 'first'

        headerIncluded = True if (
            self.headers == 'first' or Utils.isarray(self.headers)
            ) else False
        
        if self.headers == 'first':
            self.headers = self.data[0]

        cellsData = TableMeasures(
            expandToWindow=self.expandToWindow,
            rawData=self.data,
            headers=self.headers,
            headerIncluded=headerIncluded,
            cellMargin=margin,
            composition=composition,
            windowSize=windowSize,
            adjustWidthTo=self.adjustWidthsTo,
            adjustHeaderWidthTo=self.adjustHeaderWidthTo
            )

        # Make length of all data arrays the same
        self.data = cellsData.makeRowsEquals()
            
        cellsWidths = cellsData.getRawDataCellsWidths()
        columnWidths = cellsData.getFullColumnWidths(cellsWidths)
        adjustedColumnWidths = cellsData.adjustWidthToWindow(columnWidths)

        cellsAdjustment = Cells(
            tabularData=self.data,
            headers=self.headers,
            headerIncluded=headerIncluded,
            columnWidths=adjustedColumnWidths,
            cellMargin=margin,
            alignments=self.strAlign
            )

        # wrap the rows that exceed the width limit
        cellsAdjustment.wrapRows()

        formatedCells = cellsAdjustment.format()
        self.formatedCells = formatedCells
 
        obtainedSeparators = Separators(
            headerIncluded=headerIncluded,
            alignments=[],                  #TODO add multi-alignments functionality
            cellMargin=margin,
            composition=composition,
            colsWidth=adjustedColumnWidths
            )
        obtainedSeparators = obtainedSeparators.makeAll()
        self.formatedSeparators = obtainedSeparators


        obtainedRows = DataRows(
            adjustedTableCells=formatedCells,
            composition=composition,
            headerIncluded=headerIncluded,
            headers=self.headers
            )
        obtainedRows = obtainedRows.makeAll()
        self.formatedDataRows = obtainedRows
    
        return self.compose()



if __name__ == '__main__':

    print('This is not supposed to be executed!')
