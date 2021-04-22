""" 
CREACION DE ESTILOS PARA LAS TABLAS
"""

from .compositionSet import (
    HorizontalComposition,
    VerticalComposition
)
from .utils import Utils

class Separators(object):

    def __init__(
        self,
        headerIncluded: bool,
        alignments: list,
        cellMargin: int,
        composition: tuple,
        colsWidth: list,
        ):
        self.composition = composition
        self.headerIncluded = headerIncluded
        self.cellMargin = cellMargin
        self.colsWidths = colsWidth
        self.alignments = alignments
        
        # These are the composition of each type of separator, or
        # the characters that will conform them
        self.separatorsCompositions = self.composition.horizontalComposition

        # This is the named tuple with empty fields. Here the separators 
        # will be delivered
        self.separatorsPositions = HorizontalComposition
        
    def __str__(self):
        pass

    def makeMiddlePart(self, middle: str, singleColWidht: int, ):
        return f'{f"{middle}"*((singleColWidht)+(self.cellMargin*2))}'

    def makeOne(self, singleComposition: tuple):
        """
        Returns a single separator 
        """
        intersection = singleComposition.intersection
        middleChar = singleComposition.middle
        leftChar = singleComposition.left
        rightChar = singleComposition.right
        
        HorLines = map(
            self.makeMiddlePart,
            [middleChar for x in range(len(self.colsWidths))], #x is irrelevant
            self.colsWidths
            )

        # Here the separator is made joining al the horizontal lines of the
        # separator with the intersection as separator, resulting in a structure:
        #       line + separator + line + separator . . .
        #       ---- +   '  '    + ---  +   '  '    . . .
        # After that is the left char, and at the end the right char
        fullSeparator: str = leftChar + f'{intersection}'.join(HorLines) + rightChar

        return fullSeparator
    
    def makeAll(self) -> tuple:
        """ 
        Returns named tuple with the same structure that the horizontalComposition,
        but with the separator string or "None" if it isn´t used

        HorizontalComposition(  

            headerSuperior=None,

            headerInferior='───────  ──────  ───  ────  ─────  ───────',

            startWithNoHeader=None,

            tableBody=None, 

            tableEnd=None

            )   
        """

        separatorsCompositions = [
        sepcomp for sepcomp in self.separatorsCompositions
        ]

        madeSeparators = []
        current = 0
        for sepToDo in separatorsCompositions:

            if sepToDo != None:
                madeSeparator = self.makeOne(sepToDo)
                madeSeparators.append(madeSeparator)
            else:
                madeSeparators.append(None)

            current += 1

        # This part is to deliver a tuple with all the complete separators or None
        # statements, depending on the style. This is to distiguish easily for which
        # part of the table is each separator
        madeSeparators: tuple = self.separatorsPositions(
            headerSuperior=madeSeparators[0] if (
                self.headerIncluded == True
            ) else None,
            headerInferior=madeSeparators[1]if (
                self.headerIncluded == True
            ) else None,
            startWithNoHeader=madeSeparators[2] if (
                self.headerIncluded == False
            ) else None,
            tableBody=madeSeparators[3],
            tableEnd=madeSeparators[4],
        )

        return madeSeparators



class DataRows(object):

    def __init__(self, adjustedTableCells: list, composition: tuple, headers):
        self.headerCells = adjustedTableCells[0] if(
            (headers.lower() == 'first') if not Utils.isarray(headers) else False
            ) else headers
        self.rowCells = adjustedTableCells[1:]
        self.composition = composition 

        # These are the compositions of the divisions or vertical separators
        self.divisionsPositions = self.composition.verticalComposition

        # This is the named tuple with empty fields. Here the fully-formed 
        # dataRows will be delivered.
        self.rowsPositions = VerticalComposition

    def __str__(self):
        pass

    def makeOne(self, dataRow: list, isHeader: bool) -> str:
        divCompositionsKeys = {'header': 0, 'tableBody': 1}

        if isHeader:
            position = divCompositionsKeys['header']
        else:
            position = divCompositionsKeys['tableBody']

        leftChar = self.divisionsPositions[position].left
        rightChar = self.divisionsPositions[position].right
        middleChar = self.divisionsPositions[position].middle
        dataWithDivisions = f'{middleChar}'.join(dataRow)
        fullDataRow: str = leftChar + dataWithDivisions + rightChar

        return fullDataRow

    def makeAll(self)-> tuple:

        providedHeader = self.headerCells
        headerRow = None
        if providedHeader != None:
            headerRow = []
            for row in providedHeader:
                headerRow.append(self.makeOne(row, True) + '\n')

        bodyRows = []
        for multiline in self.rowCells:
            bodyRows.append([])
            for row in multiline:
                fullRow = self.makeOne(row, False)
                bodyRows[-1].append(fullRow + '\n')

        madeRows: tuple = self.rowsPositions(
            header=headerRow,
            tableBody=bodyRows
        )

        return madeRows



if __name__ == "__main__":
    
    pass
