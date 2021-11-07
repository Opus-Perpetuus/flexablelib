"""
COMPOSITION SETS - STYLES

A composition set is a named tuple  wich contain the characters
for each part of the table. Here are are the ones currently added.

*This part was based (mainly) in the "tabulate" package structure!
"""

from typing import NamedTuple, Union
from options import *


class TableComposition(NamedTuple):
    horizontalComposition: NamedTuple
    verticalComposition: NamedTuple
    tableOptions: NamedTuple


class HorizontalComposition(NamedTuple):
    headerSuperior: Union[str, NamedTuple, None]
    headerInferior: Union[str, NamedTuple, None]
    startsWithNoHeader: Union[str, NamedTuple, None]
    tableBody: Union[str, NamedTuple, None]
    tableEnd: Union[str, NamedTuple, None]


class VerticalComposition(NamedTuple):
    header: Union[NamedTuple, None]
    tableBody: Union[NamedTuple, None]


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


class CompositionNames(NamedTuple):
    plain: TableComposition

    # Box drawing Tables
    pretty_grid: TableComposition
    pretty_columns: TableComposition
    bold_header: TableComposition
    bheader_columns: TableComposition
    bold_eheader: TableComposition
    beheader_columns: TableComposition
    bheader_ebody: TableComposition
    round_edges: TableComposition
    re_eheader: TableComposition
    re_ebody: TableComposition
    # Thin borderline
    thin_borderline: TableComposition
    th_bd_eheader: TableComposition
    th_bd_ebody: TableComposition
    th_bd_empty: TableComposition
    # Bold Borderline
    bold_borderline: TableComposition
    bd_bl_eheader: TableComposition
    bd_bl_ebody: TableComposition
    bd_bl_empty: TableComposition

    # +-|~oO:
    pwrshll_alike: TableComposition
    presto: TableComposition
    grid: TableComposition
    grid_eheader: TableComposition
    grid_ebody: TableComposition
    grid_empty: TableComposition
    pipes: TableComposition
    tilde_grid: TableComposition
    tilg_eheader: TableComposition
    tilg_columns: TableComposition
    tilg_empty: TableComposition
    orgtbl: TableComposition

    # Simple (horizontal lines)
    clean: TableComposition
    simple: TableComposition
    simple_bold: TableComposition
    simple_head: TableComposition
    simple_head_bold: TableComposition
    sim_th_bl: TableComposition
    sim_bd_bl: TableComposition
    sim_head_th_bl: TableComposition
    sim_head_bd_bl: TableComposition

    # Other
    dashes: TableComposition


StyleCompositions = CompositionNames(
    plain=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=None,
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

    ###################################
    ####     Box drawing Tables    ####
    ###################################
    pretty_grid=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╒', '═', '╤', '╕'),
            headerInferior=SeparatorLine('╞', '═', '╪', '╡'),
            startsWithNoHeader=SeparatorLine('╒', '═', '╤', '╕'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('╘', '═', '╧', '╛'),
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
    pretty_columns=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╒', '═', '╤', '╕'),
            headerInferior=SeparatorLine('╞', '═', '╪', '╡'),
            startsWithNoHeader=SeparatorLine('╒', '═', '╤', '╕'),
            tableBody=None,
            tableEnd=SeparatorLine('╘', '═', '╧', '╛'),
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
    bold_header=TableComposition(
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
    bheader_columns=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '╦', '╗'),
            headerInferior=SeparatorLine('╚', '═', '╩', '╝'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=None,
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
    bold_eheader=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '═', '╗'),
            headerInferior=SeparatorLine('╚', '═', '═', '╝'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    beheader_columns=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '═', '╗'),
            headerInferior=SeparatorLine('╚', '═', '═', '╝'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=None,
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    bheader_ebody=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '═', '╗'),
            headerInferior=SeparatorLine('╚', '═', '═', '╝'),
            startsWithNoHeader=SeparatorLine('┌', '─', '─', '┐'),
            tableBody=None,
            tableEnd=SeparatorLine('└', '─', '─', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            tableBody=SeparatorLine('│', ' ', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    round_edges=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╭', '─', '┬', '╮'),
            headerInferior=SeparatorLine('╞', '═', '╪', '╡'),
            startsWithNoHeader=SeparatorLine('╭', '─', '┬', '╮'),
            tableBody=None,
            tableEnd=SeparatorLine('╰', '─', '┴', '╯'),
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
    re_eheader=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╭', '─', '─', '╮'),
            headerInferior=SeparatorLine('╞', '═', '╤', '╡'),
            startsWithNoHeader=SeparatorLine('╭', '─', '┬', '╮'),
            tableBody=None,
            tableEnd=SeparatorLine('╰', '─', '┴', '╯'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    re_ebody=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╭', '─', '─', '╮'),
            headerInferior=SeparatorLine('╞', '═', '═', '╡'),
            startsWithNoHeader=SeparatorLine('╭', '─', '─', '╮'),
            tableBody=None,
            tableEnd=SeparatorLine('╰', '─', '─', '╯'),
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
    ###########################
    ####  Thin borderline  ####
    ###########################
    thin_borderline=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '┬', '┐'),
            headerInferior=SeparatorLine('╞', '═', '╪', '╡'),
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
    th_bd_eheader=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '─', '┐'),
            headerInferior=SeparatorLine('╞', '═', '╤', '╡'),
            startsWithNoHeader=SeparatorLine('┌', '─', '┬', '┐'),
            tableBody=SeparatorLine('├', '─', '┼', '┤'),
            tableEnd=SeparatorLine('└', '─', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            tableBody=SeparatorLine('│', '│', None, '│')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    th_bd_ebody=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '┬', '┐'),
            headerInferior=SeparatorLine('╞', '═', '╧', '╡'),
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
    th_bd_empty=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '─', '─', '┐'),
            headerInferior=SeparatorLine('╞', '═', '═', '╡'),
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
    ###########################
    ####  Bold borderline  ####
    ###########################
    bold_borderline=TableComposition(
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
    bd_bl_eheader=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('╔', '═', '═', '╗'),
            headerInferior=SeparatorLine('╠', '═', '╤', '╣'),
            startsWithNoHeader=SeparatorLine('╔', '═', '╤', '╗'),
            tableBody=SeparatorLine('╟', '─', '┼', '╢'),
            tableEnd=SeparatorLine('╚', '═', '╧', '╝'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            tableBody=SeparatorLine('║', '│', None, '║')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    bd_bl_ebody=TableComposition(
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
    bd_bl_empty=TableComposition(
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
    ),

    ###########################
    ####      +-|~oO:      ####
    ###########################
    pwrshll_alike=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '-', ' ', None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, ' ', None, None),
            tableBody=SeparatorLine(None, ' ', None, None)
        ),
        tableOptions=TableOptions(
            margin=0,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    presto=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '-', '+', None),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine(None, '|', None, None),
            tableBody=SeparatorLine(None, '|', None, None)
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    ),
    grid=TableComposition(
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
    grid_eheader=TableComposition(
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
    grid_ebody=TableComposition(
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
    grid_empty=TableComposition(
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
    pipes=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('|', '-', '|', '|'),
            startsWithNoHeader=SeparatorLine('|', '-', '|', '|'),
            tableBody=None,
            tableEnd=None,
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
    tilde_grid=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '+', '+'),
            headerInferior=SeparatorLine('O', '~', 'O', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', 'O', 'O'),
            tableBody=SeparatorLine('+', '-', '+', '+'),
            tableEnd=SeparatorLine('O', '~', 'O', 'O')
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
    tilg_eheader=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '-', '+'),
            headerInferior=SeparatorLine('O', '~', 'O', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', 'O', 'O'),
            tableBody=SeparatorLine('+', '-', '+', '+'),
            tableEnd=SeparatorLine('O', '~', 'O', 'O')
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
    tilg_columns=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '+', '+'),
            headerInferior=SeparatorLine('O', '~', 'O', 'O'),
            startsWithNoHeader=SeparatorLine('O', '~', 'O', 'O'),
            tableBody=None,
            tableEnd=SeparatorLine('O', '~', 'O', 'O')
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
    tilg_empty=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('+', '-', '-', '+'),
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
    orgtbl=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine('|', '-', '+', '|'),
            startsWithNoHeader=None,
            tableBody=None,
            tableEnd=None,
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

    ###################################
    #### Simple (horizontal lines) ####
    ###################################
    clean=TableComposition(
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
    simple=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None)
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
    simple_bold=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None)
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
    simple_head=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
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
    simple_head_bold=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
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
    sim_th_bl=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None)
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
    sim_bd_bl=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            headerInferior=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            startsWithNoHeader=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            tableBody=None,
            tableEnd=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None)
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
    sim_head_th_bl=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
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
    sim_head_bd_bl=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=None,
            headerInferior=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
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

    ##################
    ####   Other  ####
    ##################
    dashes=TableComposition(
        horizontalComposition=HorizontalComposition(
            headerSuperior=SeparatorLine('┌', '┄', '┬', '┐'),
            headerInferior=SeparatorLine('┝', '╍', '┿', '┥'),
            startsWithNoHeader=SeparatorLine('┌', '┄', '┬', '┐'),
            tableBody=None,
            tableEnd=SeparatorLine('└', '┄', '┴', '┘'),
        ),
        verticalComposition=VerticalComposition(
            header=SeparatorLine('┊', '┊', None, '┊'),
            tableBody=SeparatorLine('┊', '┊', None, '┊')
        ),
        tableOptions=TableOptions(
            margin=MARGIN,
            alignSensitive=False,
            alignIndicator=None,
            whenCenteredPutInSides=False
        )
    )
)
