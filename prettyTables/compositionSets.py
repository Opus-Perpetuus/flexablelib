"""
COMPOSITION SETS - STYLES

A composition set is a named tuple  wich contain the characters
for each part of the table. Here are are the ones currently added.

*¡This part was based (mainly) in the "tabulate" package structure!
"""

from collections import namedtuple

from .constants import *


tableComposition = namedtuple(
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
        'startWithNoHeader',
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
        'margin'            #FIX add "TopWithoutHeader" option in the TableOptions
    ]                       #TODO add "lineSpacing" option
)

_styleCompositions = {
    'clean': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('', '─', STINVISP, ''),
            startWithNoHeader=None,
            tableBody=None,
            tableEnd=SeparatorLine('', '─', STINVISP, '')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0
        )
    ),
    'plain': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=None,
            startWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0
        )
    ),
    'bold_borderline': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╤', '╗'),
            headerInferior=SeparatorLine('╠', '═', '╪', '╣'),
            startWithNoHeader=SeparatorLine('╔', '═', '╤', '╗'),
            tableBody=SeparatorLine('╟', '─', '┼', '╢'),
            tableEnd=SeparatorLine('╚', '═', '╧', '╝'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '│', None, '║'),
            tableBody=SeparatorLine('║', '│', None, '║')
        ),
        tableOptions=TableOptions(
            margin=STAMA
        )
    ),
    'grid': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '+', '+'),
            headerInferior=SeparatorLine('+', '=', '+', '+'),
            startWithNoHeader=SeparatorLine('+', '-', '+', '+'),
            tableBody=SeparatorLine('+', '-', '+', '+'),
            tableEnd=SeparatorLine('+', '-', '+', '+')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            tableBody=SeparatorLine('|', '|', None, '|')
        ),
        tableOptions=TableOptions(
            margin=STAMA
        )
    ),
    'windows_alike': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('', '-', STINVISP, ''),
            startWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0
        )
    ),
    'thin_borderline': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '─', '┐'),
            headerInferior=SeparatorLine('├', '─', '┬', '┤'),
            startWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=STAMA
        )
    ),
    'bold_header': tableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╦', '╗'),
            headerInferior=SeparatorLine('╚', '═', '╩', '╝'),
            startWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '║', None, '║'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=STAMA
        )
    ),

}

def getCompositions():
    return _styleCompositions
