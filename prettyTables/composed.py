""" 
CREACION DE ESTILOS PARA LAS TABLAS
"""

from os import name, sep
# from prettyTables.prettyTables.table import table
from compositionSet import getCompositions, HorizontalComposition
from collections import namedtuple


# class Style(object):

#     def __init__(self):
#         pass

#     def __str__(self):
#         pass



class Separators(object):

    def __init__(self, styleName: str, colsWidth: list, alignments: list):
        self.compositions = getCompositions()[styleName]
        self.sepPositions = HorizontalComposition #This is the named tuple without 
        self.colsWidth = colsWidth
        self.alignments = alignments
        self.margin = self.compositions.tableOptions.margin

    def __str__(self):
        pass

    def makeMiddlePart(self, middle: str, singleColWidht: int, ):
        return f'{f"{middle}"*(singleColWidht+(self.margin*2))}'

    def makeOne(self, singleComposition: tuple):
        inter = singleComposition.intersection
        midChar = singleComposition.middle
        left = singleComposition.left
        right = singleComposition.right
        
        mid = map(
            self.makeMiddlePart,
            [midChar for x in range(len(self.colsWidth))],
            self.colsWidth
            )

        fullSeparator = left + f'{inter}'.join(mid) + right

        return fullSeparator
    
    def makeAll(self):
        """ 
        Returns named tuple with the same structure that the horizontalComposition,
        but with the separator string or "None" if it isn´t used

        HorizontalComposition(  

            headerSuperior=None,

            headerInferior='───────  ──────  ───  ────  ─────  ───────', 

            tableBody=None, 

            tableEnd=None

            )   
        """

        separatorsCompositions = [
        sepcomp for sepcomp in self.compositions.horizontalComposition
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
        
        madeSeparators = self.sepPositions(
            headerSuperior=madeSeparators[0],
            headerInferior=madeSeparators[1],
            tableBody=madeSeparators[2],
            tableEnd=madeSeparators[3],
        )

        return madeSeparators




# class DataRow(object):


if __name__ == "__main__":
    sepParam = Separators('bold_header', [5, 4, 1, 2, 3, 5], [])
    obtainedSeparators = Separators.makeAll(sepParam)

    print(obtainedSeparators)
    
    for obt in obtainedSeparators:
        print(obt)
