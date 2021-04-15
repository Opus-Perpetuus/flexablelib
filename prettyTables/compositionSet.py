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

SeparatorLine = namedtuple(
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
            headerInferior=SeparatorLine('', '─', STINVISP, ''),
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0,
            hideWhenNoHeader=[0, 2, 3]
        )
    ),
     'bold_header': CompositionSet(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╦', '╗'),
            headerInferior=SeparatorLine('╚', '═', '╩', '╝'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '║', None, '║'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            hideWhenNoHeader=[0, 2, 3]
        )
    )
}

def getCompositions():
    return _styleCompositions














