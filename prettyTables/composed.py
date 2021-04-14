""" 
CREACION DE ESTILOS PARA LAS TABLAS
"""

from os import name
from compositionSet import getCompositions
from collections import namedtuple


# class Style(object):

#     def __init__(self):
#         pass

#     def __str__(self):
#         pass



class Separator(object):

    def __init__(
        self,
        composition: tuple,
        margin: int,
        colsWidth: list,
        alignments: list
        ):

        self.composition = composition # expects (char, char, char, char)
        self.colsWidth = colsWidth
        self.alignments = alignments
        self.margin = margin

    def __str__(self):
        pass

    def makeMiddlePart(self, middle: str, singleColWidht: int, ):
        return f'{f"{middle}"*(singleColWidht+(self.margin*2))}'

    def make(self):

        inter = self.composition.intersection
        midChar = self.composition.middle
        left = self.composition.left
        right = self.composition.right
        
        mid = map(
            self.makeMiddlePart,
            [midChar for x in range(len(self.colsWidth))],
            self.colsWidth
            )

        mid = f'{inter}'.join(mid)

        return left + mid + right




# class DataRow(object):



if __name__ == "__main__":

    compositions = getCompositions()
    separatorCompositions = [
        sepcomp for sepcomp in compositions['clean'].horizontalComposition if (
            sepcomp != None
        )
    ]
    margin = compositions['clean'].tableOptions.margin
    colsWidth = [5, 5, 4, 1, 5]

    # print(separatorCompositions)

    for sepToDo in separatorCompositions:

        sepParam = Separator(sepToDo, margin, colsWidth, [])
        separator = Separator.make(sepParam)

        print(separator)