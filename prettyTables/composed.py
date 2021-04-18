""" 
CREACION DE ESTILOS PARA LAS TABLAS
"""

from compositionSet import getCompositions, HorizontalComposition, VerticalComposition
from collections import namedtuple
# from _typeshed import NoneType
from tabulate import tabulate

class Separators(object):

    def __init__(
        self,
        styleName: str,
        colsWidth: list,
        alignments: list,
        headerIncluded: bool=False
        ):
        self.styleComposition = getCompositions()[styleName]
        self.headerIncluded = headerIncluded
        self.colsWidths = colsWidth
        self.alignments = alignments
        self.cellMargin = self.styleComposition.tableOptions.margin
        
        # These are the composition of each type of separator, or
        # the characters that will conform them
        self.separatorsCompositions = self.styleComposition.horizontalComposition

        # This is the named tuple with empty fields. Here the separators 
        # will be delivered
        self.separatorsPositions = HorizontalComposition
        
    def __str__(self):
        pass

    def makeMiddlePart(self, middle: str, singleColWidht: int, ):
        return f'{f"{middle}"*(singleColWidht+(self.cellMargin*2))}'

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
        fullSeparator = leftChar + f'{intersection}'.join(HorLines) + rightChar

        return fullSeparator
    
    def makeAll(self):
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
        madeSeparators = self.separatorsPositions(
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

    def __init__(self, adjustedTableCells: list, styleName: str, headers=None):
        self.headerCells = adjustedTableCells[0] if headers.lower() == 'first' else headers
        self.rowCells = adjustedTableCells
        self.styleComposition = getCompositions()[styleName]

        # These are the compositions of the divisions or vertical separators
        self.divisionsCompositions = self.styleComposition.verticalComposition

        # This is the named tuple with empty fields. Here the fully-formed 
        # dataRows will be delivered.
        self.rowsPositions = VerticalComposition

    def __str__(self):
        pass

    def makeOne(self, dataRow: list, isHeader: bool):
        divCompositionsKeys = {'header': 0, 'tableBody': 1}

        if isHeader:
            position = divCompositionsKeys['header']
        else:
            position = divCompositionsKeys['tableBody']

        leftChar = self.divisionsCompositions[position].left
        rightChar = self.divisionsCompositions[position].right
        middleChar = self.divisionsCompositions[position].middle
        dataWithDivisions = f'{middleChar}'.join(dataRow)
        fullDataRow = leftChar + dataWithDivisions + rightChar

        return fullDataRow

    def makeAll(self):
        providedHeader = self.headerCells
        headerRow = None
        if providedHeader != None:
            headerRow = self.makeOne(providedHeader, True)

        bodyRows = []
        for row in self.rowCells:
            fullRow = self.makeOne(row, False)
            bodyRows.append(fullRow + '\n')

        madeRows = self.rowsPositions(
            header=headerRow,
            tableBody=bodyRows
        )

        return madeRows



if __name__ == "__main__":
    tabularData = [
        [' stirpicultural ', ' 14 ', ' String ', ' g0jxjq4xk105vy7ss73nb8e7j79ug7kuf8   '],
        [' stirpiculture  ', ' 13 ', ' String ', ' tt30p48h0lz5xi38dk41qk2qxat9foj03    '],
        [' bend           ', ' 4  ', ' Word   ', ' eebmibc23045t7ox1a8ñbcj3321w4123i    '],
        [' benda          ', ' 5  ', ' Word   ', ' uc3swk23ui4wofi6z2qz2v11712zd937t17x '],
        [' bendability    ', ' 11 ', ' String ', ' 48p22n2s2o3eos418977i8r3o358pr97cl2d ']
        ]

    obtainedSeparators = Separators('bold_borderline', [len(l)-2 for l in tabularData[0]], [], True).makeAll()
    print(obtainedSeparators)
    for obt in obtainedSeparators:
        print(obt)

    obtainedRows = DataRows(tabularData, 'bold_borderline', 'first')
    obtainedRows = obtainedRows.makeAll()
    print(obtainedRows)
    for obt in obtainedRows:
        print(obt)
    

    # def decideIfSeparatorExists(self, separator):
    #     """
    #     This checks if the separator is unused by checking if is None, in which case
    #     returns an empty ('') string.

    #     If the separator is used (exists), returns separator + '\\n'
    #     """

    #     if separator == None:
    #         return ''
    #     else:
    #         return separator + '\n'
    
    # headerSuperiorSeparator = decideIfSeparatorExists(obtainedSeparators.headerSuperior)
    # headerInferiorSeparator = decideIfSeparatorExists(obtainedSeparators.headerInferior)
    # tableStartWhenNoHeader = decideIfSeparatorExists(obtainedSeparators.startWithNoHeader)
    # tableBodySeparator = decideIfSeparatorExists(obtainedSeparators.tableBody)
    # tableEndSeparator = decideIfSeparatorExists(obtainedSeparators.tableEnd)

    # tableBody = bodyRows.insert(0, headerSuperiorSeparator)
    # tableBody = bodyRows.insert(2, headerInferiorSeparator)
    # tableBody = tableBodySeparator.join(bodyRows)
    # table = tableStartWhenNoHeader + tableBody 
    # table = table + tableEndSeparator

    # print(table)

