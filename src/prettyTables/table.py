'''
Print formated tabular data in different styles
'''
from .utils import Utils
from .constants import *
from . import compositionSet
from . import composed
from . import adjust

class Table(object):
    '''
    Makes table out of tabular like data:

    >>> tabularData: list[list[any]]
    >>> headers: 'first' | list[] 
    >>> style: str
    >>> strAlign: 'left' | 'center' | 'right'
    >>> expandToWindow: True | False
    '''  
    
    def __init__(
        self,
        tabularData,
        headers=None,
        style='clean',
        strAlign='left',
        expandToWindow=True
    ):
        self.data = tabularData
        self.headers = headers
        self.style = style
        self.strAlign = strAlign
        self.expandToWindow = expandToWindow
        self.formatedCells = []
        self.formatedSeparators = ()
        self.formatedDataRows = ()
    
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
        headerRows = self.formatedDataRows.header
        bodyRows = self.formatedDataRows.tableBody

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
        composition = compositionSet._styleCompositions[self.style]
        margin = composition.tableOptions.margin
        windowSize = Utils.getWIndowsSize()

        headerIncluded = True if (
            self.headers == 'first' or Utils.isarray(self.headers)
            ) else False
        
        if Utils.isarray(self.headers):
            self.headers = 'first'
            self.data.insert(0, self.headers)

        cellsData = adjust.TableMeasures(
            expandToWindow=self.expandToWindow,
            rawData=self.data,
            cellMargin=margin,
            composition=composition,
            windowSize=windowSize
            )
        cellsWidths = cellsData.getRawDataCellsWidths()
        columnWidths = cellsData.getFullColumnWidths(cellsWidths)
        adjustedColumnWidths = cellsData.adjustWidthToWindow(columnWidths)

        cellsAdjustment =  adjust.Cells(
            tabularData=self.data,
            columnWidths=adjustedColumnWidths,
            cellMargin=margin,
            alignments=self.strAlign
            )

        # wrap the rows that exceed the width limit
        cellsAdjustment.wrapRows()

        formatedCells = cellsAdjustment.format()
        self.formatedCells = formatedCells
 
        obtainedSeparators = composed.Separators(
            headerIncluded=headerIncluded,
            alignments=[],                              # Correct
            cellMargin=margin,
            composition=composition,
            colsWidth=adjustedColumnWidths
            )
        obtainedSeparators = obtainedSeparators.makeAll()
        self.formatedSeparators = obtainedSeparators


        obtainedRows = composed.DataRows(
            adjustedTableCells=formatedCells,
            composition=composition,
            headers=self.headers
            )
        obtainedRows = obtainedRows.makeAll()
        self.formatedDataRows = obtainedRows
    
        return self.compose()



if __name__ == '__main__':

    print('This is not supposed to be executed!')