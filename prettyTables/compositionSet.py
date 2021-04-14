from collections import namedtuple
from constants import *

"""
*¡This part was based (majority) in the "tabulate" package structure!
*Here the CONSTANT names comes all from the constants module
"""


CompositionSet = namedtuple(
    'CompositionSet',
    [
        'horizontalComposition',
        'verticalComposition',
        'tableOptions'
    ]
)

HorizontalComposition = namedtuple(
    'HorizontalComposition',
    [
        'headerSuperior',
        'headerInferior',
        'tableBody',
        'tableEnd'
    ]
)

VerticalComposition = namedtuple(
    'VerticalComposition', 
    [
        'header',
        'tableBody'
    ]
)

Separator = namedtuple(
    'Separator',
    [
        'left',
        'middle',
        'intersection',
        'right'
    ]
)

TableOptions = namedtuple(
    'TableOptions',
    [
        'margin',
        'hideWhenNoHeader'
    ]
)

_styleCompositions = {
    'clean': CompositionSet(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=Separator('', '─', STIVISP, ''),
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=Separator('', STIVISP, None, ''),
            tableBody=Separator('', STIVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            hideWhenNoHeader=[0, 2, 3]
        )
    )
}

def getCompositions():
    return _styleCompositions














