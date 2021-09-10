"""
COMPOSITION SETS - STYLES

A composition set is a named tuple  wich contain the characters
for each part of the table. Here are are the ones currently added.

*This part was based (mainly) in the "tabulate" package structure!
"""

from typing import NamedTuple, Union, get_origin
from constants import *


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
    whenCenteredPutInSides: bool


class StyleNames(NamedTuple):
    clean: TableComposition
    plain: TableComposition
    thin_borderline: TableComposition
    bold_borderline: TableComposition
    grid: TableComposition
    windows_alike: TableComposition
    bold_header: TableComposition
    pipes: TableComposition
    

StyleCompositions = StyleNames(
    clean = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '─', STINVISP, None),
            startsWithNoHeader=SeparatorLine(None, '─', STINVISP, None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '─', STINVISP, None),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, STINVISP, None, None),
            tableBody=SeparatorLine(None, STINVISP, None, None)
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    plain = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, STINVISP, None, None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, STINVISP, None, None),
            tableBody=SeparatorLine(None, STINVISP, None, None)
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
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
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    bold_borderline= TableComposition(
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
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
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
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    windows_alike = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '-', STINVISP, None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, STINVISP, None, None),
            tableBody=SeparatorLine(None, STINVISP, None, None)
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
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
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
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
            alignIndicator=AlignIndicator(':', ':'),
            whenCenteredPutInSides=True
        )
    )
)

#print(StyleCompositions._asdict())

