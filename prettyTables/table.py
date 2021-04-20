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
            self.headers == 'first' or self.isarray(self.headers )
            ) else False
        

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

        if Utils.isarray(self.headers):
            headerAdjustment = adjust.Cells(
                tabularData=self.headers,
                columnWidths=adjustedColumnWidths,
                cellMargin=margin,
                alignments=self.strAlign
            )

             # wrap the rows that exceed the width limit
            headerAdjustment.wrapRows()
            
            formatedHeader = headerAdjustment.format()
            self.headers = formatedHeader

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

    import nltk
    from random import choice, randint

    alignment = input("Alignment (0: left, 1: center, 2: right): ")
    alignment = randint(0, 2) if alignment == "" else int(alignment)
    alignment = ['left', 'center', 'right'][alignment]
    expandToWindow = input("Adjust table to window (0: no, 1: yes): ")
    expandToWindow = randint(0, 1) if expandToWindow == "" else int(expandToWindow)
    expandToWindow = [False, True][expandToWindow]

    try:
        nltk.corpus.words.words()
    except:
        nltk.download("words")

    inicio = randint(2000, 200000)
    final = 10
    wordList = nltk.corpus.words.words()[inicio:inicio+final] + ["a", "x", "y", "b", "c", "v", "q", "w", "e", "o", "t", "g"]
    wordList[0] += ' Word'
    wordList[1] += ' Elongated'
    numeros = "1 3 2 4 5 6 7 8 9 0"
    letras = "a b c d e f g h i j k l m n ñ o p q r s t u v w x y z"

    encabezado = ["STRING","LEN","TYPE","ID"]
    datos = [encabezado]
    for x in range(0, len(wordList)):
        datos.append(['' for nuevo in encabezado])
        for y in range(0, len(encabezado)):
            if y == 0:
                datos[x+1][y] = wordList[x]
            elif y == 1:
                datos[x+1][y] = str(len(wordList[x]))
            elif y == 2:
                datos[x+1][y] = (choice(["Word", "String"])) if len(wordList[x]) > 1 else choice(["Letter", "Character"])
            else:
                tamaño = randint(30, 40)
                idEscogido = ""            

                for caracter in range(0, tamaño):
                    eleccion = randint(0, 1)
                    mayuscula = randint(0, 1)
                    aElegir = (numeros if eleccion==0 else letras).split()
                    caracter = choice(aElegir)
                    caracter.upper() if (caracter in letras and mayuscula == 1) else True
                    idEscogido += caracter

                datos[x+1][y] = idEscogido
    

    tabla = Table(
        tabularData=datos,
        headers='first',
        strAlign=alignment,
        style='bold_header',
        expandToWindow=expandToWindow
        ).make()

    print(tabla)

    input("Press enter to exit")