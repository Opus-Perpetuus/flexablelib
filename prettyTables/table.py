'''
Print formated tabular data in different styles
'''
from utils import Utils
from constants import *
import compositionSet
import composed
import adjust
import tabulate

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
            self.data.insert(0, headers)

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

    from random import  randint

    alignment = input("Alignment (0: left, 1: center, 2: right): ")
    alignment = randint(0, 2) if alignment == "" else int(alignment)
    alignment = ['left', 'center', 'right'][alignment]
    expandToWindow = input("Adjust table to window (0: no, 1: yes): ")
    expandToWindow = randint(0, 1) if expandToWindow == "" else int(expandToWindow)
    expandToWindow = [False, True][expandToWindow]
    
    headers = ['STRING', 'LEN', 'TYPE', 'ID']
    datos = [
            ['gamelang Word', '13', 'Word', '1e8ñrz8ty136s66ñ4b8k38qn9ñadryzb5'],
            ['gameless Elongated', '18', 'String', '4j4ycaicwenh2ñs25ñmmmr239ñ23w0bn803hcs'],
            ['gamelike', '8', 'Word', 'p2in3782mub17480eq72mq3pc7v9zon'],
            ['Gamelion', '8', 'String', '4hv2d710s6vsñ8n0ybfms2c301qr7dj'],
            ['gamelotte', '9', 'Word', '1tg5y3jn7xf9046681qe8o1pul50c046w29xz'],
            ['gamely', '6', 'String', 'mq58xu8vq84x784ngcw44w5410u28fñ'],
            ['gamene', '6', 'Word', '98r75qj996c379tg1kñpz10dw534m22a'],
            ['gameness', '8', 'String', 'yfv5886ff04sp7a1t8z30tugq3bx47jd'],
            ['gamesome', '8', 'Word', 'owus19312vy2hube4rdha0ej9s98v28fz'],
            ['gamesomely', '10', 'String', '0ms888ib3768p3khz32f8272456v219']
            ]

    tabla = Table(
        tabularData=datos,
        headers=headers,
        strAlign=alignment,
        style='bold_borderline',
        expandToWindow=expandToWindow
        ).make()

    print(tabla)

    input("Press enter to exit")