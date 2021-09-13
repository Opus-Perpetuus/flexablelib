"""
COMPOSITION SETS - STYLES

A composition set is a named tuple  wich contain the characters
for each part of the table. Here are are the ones currently added.

*This part was based (mainly) in the "tabulate" package structure!
"""

from typing import NamedTuple, Union, get_origin
from options import *


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
    curly_grid: TableComposition
    curlyg_eheader: TableComposition
    curlyg_ebody: TableComposition
    curlyg_empty: TableComposition
    grid_eheader: TableComposition
    grid_ebody: TableComposition
    grid_empty: TableComposition
    simple: TableComposition
    simple_bold: TableComposition
    simple_head: TableComposition
    simple_head_bold: TableComposition
    sim_th_bl: TableComposition
    sim_bd_bl: TableComposition
    sim_head_th_bl: TableComposition
    sim_head_bd_bl: TableComposition
    th_bd_eheader: TableComposition
    th_bd_ebody: TableComposition
    th_bd_empty: TableComposition
    bd_bl_eheader: TableComposition
    bd_bl_ebody: TableComposition
    bd_bl_empty: TableComposition

    

StyleCompositions = StyleNames(
    clean = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
            startsWithNoHeader=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
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
            headerInferior=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
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
            headerSuperior=SeparatorLine('┌', '─', '┬', '┐'),
            headerInferior=SeparatorLine('├', '─', '┼', '┤'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
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
            margin=MARGIN,
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
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    windows_alike = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '-', INVISIBLE_SEPARATOR, None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
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
            margin=MARGIN,
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
            margin=MARGIN,
            alignSensitive=True,
            alignIndicator=AlignIndicator(':', ':'),
            whenCenteredPutInSides=True
        )
    ),
    curly_grid = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('o', '-', 'o', 'o'),
            headerInferior=SeparatorLine('O', '~', 'O', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', 'O', 'O'),
            tableBody=SeparatorLine('o', '-', 'o', 'o'),
            tableEnd=SeparatorLine('O', '~', 'O', 'O')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            tableBody=SeparatorLine('|', '|', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=True,
            alignIndicator=AlignIndicator(':', ':'),
            whenCenteredPutInSides=False
        )
    ),
    curlyg_eheader = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('o', '-', '-', 'o'),
            headerInferior=SeparatorLine('O', '~', 'O', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', 'O', 'O'),
            tableBody=SeparatorLine('o', '-', 'o', 'o'),
            tableEnd=SeparatorLine('O', '~', 'O', 'O')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            tableBody=SeparatorLine('|', '|', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=True,
            alignIndicator=AlignIndicator(':', ':'),
            whenCenteredPutInSides=False
        )
    ),
    curlyg_ebody = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('o', '-', 'o', 'o'),
            headerInferior=SeparatorLine('O', '~', 'O', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', 'O', 'O'),
            tableBody=None,
            tableEnd=SeparatorLine('O', '~', '~', 'O')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            tableBody=SeparatorLine('|', ' ', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=True,
            alignIndicator=AlignIndicator(':', ':'),
            whenCenteredPutInSides=False
        )
    ),
    curlyg_empty = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('o', '-', '-', 'o'),
            headerInferior=SeparatorLine('O', '~', '~', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', '~', 'O'),
            tableBody=None,
            tableEnd=SeparatorLine('O', '~', '~', 'O')
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            tableBody=SeparatorLine('|', ' ', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    grid_eheader = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '-', '+'),
            headerInferior=SeparatorLine('+', '=', '+', '+'),
            startsWithNoHeader=SeparatorLine('+', '-', '+', '+'),
            tableBody=None,
            tableEnd=SeparatorLine('+', '-', '+', '+'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            tableBody=SeparatorLine('|', '|', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    grid_ebody = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '+', '+'),
            headerInferior=SeparatorLine('+', '=', '+', '+'),
            startsWithNoHeader=SeparatorLine('+', '-', '-', '+'),
            tableBody=None,
            tableEnd=SeparatorLine('+', '-', '-', '+'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            tableBody=SeparatorLine('|', ' ', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    grid_empty = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '-', '+'),
            headerInferior=SeparatorLine('+', '=', '=', '+'),
            startsWithNoHeader=SeparatorLine('+', '-', '-', '+'),
            tableBody=None,
            tableEnd=SeparatorLine('+', '-', '-', '+'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            tableBody=SeparatorLine('|', ' ', None, '|')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    simple = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '-', '-'*len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '-', '-'*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '-', '-'*len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '-', '-'*len(INVISIBLE_SEPARATOR), None)
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    simple_bold = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '=', '='*len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '=', '='*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '=', '='*len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '=', '='*len(INVISIBLE_SEPARATOR), None)
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    simple_head = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '-', '-'*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    simple_head_bold = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '=', '='*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    sim_th_bl = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '─', '─'*len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '─', '─'*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '─', '─'*len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '─', '─'*len(INVISIBLE_SEPARATOR), None)
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    sim_bd_bl = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '═', '═'*len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '═', '═'*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '═', '═'*len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '═', '═'*len(INVISIBLE_SEPARATOR), None)
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    sim_head_th_bl = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '─', '─'*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    sim_head_bd_bl = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '═', '═'*len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            tableBody=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    th_bd_eheader = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '─', '┐'),
            headerInferior=SeparatorLine('├', '─', '┬', '┤'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    th_bd_ebody = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '┬', '┐'),
            headerInferior=SeparatorLine('├', '─', '┴', '┤'),
            startsWithNoHeader=SeparatorLine('┌', '─', '─', '┐'),
            tableBody=None,
            tableEnd=SeparatorLine('└', '─', '─', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            tableBody=SeparatorLine('│', ' ', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    th_bd_empty = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '─', '┐'),
            headerInferior=SeparatorLine('├', '─', '─', '┤'),
            startsWithNoHeader=SeparatorLine('┌', '─', '─', '┐'),
            tableBody=None,
            tableEnd=SeparatorLine('└', '─', '─', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            tableBody=SeparatorLine('│', ' ', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    bd_bl_eheader = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '═', '╗'),
            headerInferior=SeparatorLine('╠', '═', '═', '╣'),
            startsWithNoHeader=SeparatorLine('╔', '═', '╤', '╗'),
            tableBody=SeparatorLine('╟', '─', '┼', '╢'),
            tableEnd=SeparatorLine('╚', '═', '╧', '╝'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '│', None, '║'),
            tableBody=SeparatorLine('║', '│', None, '║')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    bd_bl_ebody = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╤', '╗'),
            headerInferior=SeparatorLine('╠', '═', '╧', '╣'),
            startsWithNoHeader=SeparatorLine('╔', '═', '═', '╗'),
            tableBody=None,
            tableEnd=SeparatorLine('╚', '═', '═', '╝'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', '│', None, '║'),
            tableBody=SeparatorLine('║', ' ', None, '║')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    bd_bl_empty = TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '═', '╗'),
            headerInferior=SeparatorLine('╠', '═', '═', '╣'),
            startsWithNoHeader=SeparatorLine('╔', '═', '═', '╗'),
            tableBody=None,
            tableEnd=SeparatorLine('╚', '═', '═', '╝'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            tableBody=SeparatorLine('║', ' ', None, '║')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    )
)

#print(StyleCompositions._asdict())

