"""
COMPOSITION SETS - STYLES

A composition set is a named tuple  wich contain the characters
for each part of the table. Here are are the ones currently added.

*¡This part was based (mainly) in the "tabulate" package structure!
"""

from typing import NamedTuple, Union
from .constants import *


class TableComposition(NamedTuple):
    horizontalComposition: NamedTuple
    verticalComposition: NamedTuple
    tableOptions: NamedTuple


class HorizontalComposition(NamedTuple):
    headerSuperior: Union[str, None]
    headerInferior: Union[str, None]
    startsWithNoHeader: Union[str, None]
    tableBody: Union[str, None]
    tableEnd: Union[str, None]


class VerticalComposition(NamedTuple): 
    header: Union[str, None]
    tableBody: Union[str, None]


class SeparatorLine(NamedTuple):
    left: Union[str, None]
    middle: Union[str, None]
    intersection: Union[str, None]
    right: Union[str, None]


class AlignIndicator(NamedTuple):
    sides: Union[str, None]
    center: Union[str, None]


class TableOptions(NamedTuple):
    margin: int
    alignSensitive: bool
    alignIndicator: Union[NamedTuple, None]
    

class StyleCompositions(NamedTuple):
    clean = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('', '─', STINVISP, ''),
            startsWithNoHeader=SeparatorLine('', '─', STINVISP, ''),
            tableBody=None,
            tableEnd=SeparatorLine('', '─', STINVISP, ''),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    plain = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('', STINVISP, None, ''),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    bold_borderline = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╤', '╗'),
            headerInferior=SeparatorLine('╠', '═', '╪', '╣'),
            startsWithNoHeader=SeparatorLine('╔', '═', '╤', '╗'),
            tableBody=SeparatorLine('╟', '─', '┼', '╢'),
            tableEnd=SeparatorLine('╚', '═', '╧', '╝'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '│', None, '║'),
            tableBody=SeparatorLine('║', '│', None, '║')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    grid = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '+', '+'),
            headerInferior=SeparatorLine('+', '=', '+', '+'),
            startsWithNoHeader=SeparatorLine('+', '-', '+', '+'),
            tableBody=SeparatorLine('+', '-', '+', '+'),
            tableEnd=SeparatorLine('+', '-', '+', '+'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            tableBody=SeparatorLine('|', '|', None, '|')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    windows_alike = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('', '-', STINVISP, ''),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('', STINVISP, None, ''),
            tableBody=SeparatorLine('', STINVISP, None, '')
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    thin_borderline = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '─', '┐'),
            headerInferior=SeparatorLine('├', '─', '┬', '┤'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    bold_header = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╦', '╗'),
            headerInferior=SeparatorLine('╚', '═', '╩', '╝'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '║', None, '║'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            alignSensitive=False,
            alignIndicator=None
        )
    )
    pipes = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('|', '-', '|', '|'),
            startsWithNoHeader=SeparatorLine('|', '-', '|', '|'),
            tableBody=None,
            tableEnd=SeparatorLine('|', '-', '|', '|'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            tableBody=SeparatorLine('|', '|', None, '|')
        ),
        tableOptions=TableOptions(
            margin=STAMA,
            alignSensitive=True,
            alignIndicator=AlignIndicator(':', None)
        )
    )

