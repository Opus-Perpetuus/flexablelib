"""
COMPOSITION SETS - STYLES

A composition set is a named tuple which contain the characters
for each part of the table. Here are are the ones currently added.

*This part was based (mainly) in the "tabulate" package structure!
"""

from collections import namedtuple
from options import *

TableComposition = namedtuple(
    'TableComposition',
    [
        'horizontal_composition',
        'vertical_composition',
        'table_options'
    ]
)

HorizontalComposition = namedtuple(
    'HorizontalComposition',
    [
        'header_superior',
        'header_inferior',
        'starts_with_no_header',
        'table_body',
        'table_end'
    ]
)

VerticalComposition = namedtuple(
    'VerticalComposition',
    [
        'header',
        'table_body'
    ]
)

SeparatorLine = namedtuple(
    'SeparatorLine',
    [
        'left',
        'middle',
        'intersection',
        'right'
    ]
)

AlignIndicator = namedtuple(
    'AlignIndicator',
    [
        'sides',
        'center'
    ]
)

TableOptions = namedtuple(
    'TableOptions',
    [
        'margin',
        'align_sensitive',
        'align_indicator',
        'when_centered_put_in_sides'
    ]
)

Compositions = namedtuple(
    'Compositions',
    [
        'plain',

        # Box drawing Tables
        'pretty_grid',
        'pretty_columns',
        'bold_header',
        'bheader_columns',
        'bold_eheader',
        'beheader_columns',
        'bheader_ebody',
        'round_edges',
        're_eheader',
        're_ebody',
        # Thin borderline
        'thin_borderline',
        'th_bd_eheader',
        'th_bd_ebody',
        'th_bd_empty',
        # Bold Borderline
        'bold_borderline',
        'bd_bl_eheader',
        'bd_bl_ebody',
        'bd_bl_empty',

        # +-|~oO:
        'pwrshll_alike',
        'presto',
        'grid',
        'grid_eheader',
        'grid_ebody',
        'grid_empty',
        'pipes',
        'tilde_grid',
        'tilg_eheader',
        'tilg_columns',
        'tilg_empty',
        'orgtbl',

        # Simple (horizontal lines)
        'clean',
        'simple',
        'simple_bold',
        'simple_head',
        'simple_head_bold',
        'sim_th_bl',
        'sim_bd_bl',
        'sim_head_th_bl',
        'sim_head_bd_bl',

        # Other
        'dashes'
    ]
)

__style_compositions = Compositions(
    plain=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=None,
            starts_with_no_header=None,
            table_body=None,
            table_end=None,
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=0,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),

    ###################################
    ####     Box drawing Tables    ####
    ###################################
    pretty_grid=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╒', '═', '╤', '╕'),
            header_inferior=SeparatorLine('╞', '═', '╪', '╡'),
            starts_with_no_header=SeparatorLine('╒', '═', '╤', '╕'),
            table_body=SeparatorLine('├', '─', '┼', '┤'),
            table_end=SeparatorLine('╘', '═', '╧', '╛'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    pretty_columns=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╒', '═', '╤', '╕'),
            header_inferior=SeparatorLine('╞', '═', '╪', '╡'),
            starts_with_no_header=SeparatorLine('╒', '═', '╤', '╕'),
            table_body=None,
            table_end=SeparatorLine('╘', '═', '╧', '╛'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bold_header=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '╦', '╗'),
            header_inferior=SeparatorLine('╚', '═', '╩', '╝'),
            starts_with_no_header=SeparatorLine('┌', '─', '┬', '┐'),
            table_body=SeparatorLine('├', '─', '┼', '┤'),
            table_end=SeparatorLine('└', '─', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', '║', None, '║'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bheader_columns=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '╦', '╗'),
            header_inferior=SeparatorLine('╚', '═', '╩', '╝'),
            starts_with_no_header=SeparatorLine('┌', '─', '┬', '┐'),
            table_body=None,
            table_end=SeparatorLine('└', '─', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', '║', None, '║'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bold_eheader=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '═', '╗'),
            header_inferior=SeparatorLine('╚', '═', '═', '╝'),
            starts_with_no_header=SeparatorLine('┌', '─', '┬', '┐'),
            table_body=SeparatorLine('├', '─', '┼', '┤'),
            table_end=SeparatorLine('└', '─', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    beheader_columns=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '═', '╗'),
            header_inferior=SeparatorLine('╚', '═', '═', '╝'),
            starts_with_no_header=SeparatorLine('┌', '─', '┬', '┐'),
            table_body=None,
            table_end=SeparatorLine('└', '─', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bheader_ebody=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '═', '╗'),
            header_inferior=SeparatorLine('╚', '═', '═', '╝'),
            starts_with_no_header=SeparatorLine('┌', '─', '─', '┐'),
            table_body=None,
            table_end=SeparatorLine('└', '─', '─', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            table_body=SeparatorLine('│', ' ', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    round_edges=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╭', '─', '┬', '╮'),
            header_inferior=SeparatorLine('╞', '═', '╪', '╡'),
            starts_with_no_header=SeparatorLine('╭', '─', '┬', '╮'),
            table_body=None,
            table_end=SeparatorLine('╰', '─', '┴', '╯'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    re_eheader=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╭', '─', '─', '╮'),
            header_inferior=SeparatorLine('╞', '═', '╤', '╡'),
            starts_with_no_header=SeparatorLine('╭', '─', '┬', '╮'),
            table_body=None,
            table_end=SeparatorLine('╰', '─', '┴', '╯'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    re_ebody=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╭', '─', '─', '╮'),
            header_inferior=SeparatorLine('╞', '═', '═', '╡'),
            starts_with_no_header=SeparatorLine('╭', '─', '─', '╮'),
            table_body=None,
            table_end=SeparatorLine('╰', '─', '─', '╯'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            table_body=SeparatorLine('│', ' ', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    ###########################
    ####  Thin borderline  ####
    ###########################
    thin_borderline=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('┌', '─', '┬', '┐'),
            header_inferior=SeparatorLine('╞', '═', '╪', '╡'),
            starts_with_no_header=SeparatorLine('┌', '─', '┬', '┐'),
            table_body=SeparatorLine('├', '─', '┼', '┤'),
            table_end=SeparatorLine('└', '─', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    th_bd_eheader=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('┌', '─', '─', '┐'),
            header_inferior=SeparatorLine('╞', '═', '╤', '╡'),
            starts_with_no_header=SeparatorLine('┌', '─', '┬', '┐'),
            table_body=SeparatorLine('├', '─', '┼', '┤'),
            table_end=SeparatorLine('└', '─', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            table_body=SeparatorLine('│', '│', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    th_bd_ebody=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('┌', '─', '┬', '┐'),
            header_inferior=SeparatorLine('╞', '═', '╧', '╡'),
            starts_with_no_header=SeparatorLine('┌', '─', '─', '┐'),
            table_body=None,
            table_end=SeparatorLine('└', '─', '─', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', '│', None, '│'),
            table_body=SeparatorLine('│', ' ', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    th_bd_empty=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('┌', '─', '─', '┐'),
            header_inferior=SeparatorLine('╞', '═', '═', '╡'),
            starts_with_no_header=SeparatorLine('┌', '─', '─', '┐'),
            table_body=None,
            table_end=SeparatorLine('└', '─', '─', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('│', ' ', None, '│'),
            table_body=SeparatorLine('│', ' ', None, '│')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    ###########################
    ####  Bold borderline  ####
    ###########################
    bold_borderline=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '╤', '╗'),
            header_inferior=SeparatorLine('╠', '═', '╪', '╣'),
            starts_with_no_header=SeparatorLine('╔', '═', '╤', '╗'),
            table_body=SeparatorLine('╟', '─', '┼', '╢'),
            table_end=SeparatorLine('╚', '═', '╧', '╝'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', '│', None, '║'),
            table_body=SeparatorLine('║', '│', None, '║')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bd_bl_eheader=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '═', '╗'),
            header_inferior=SeparatorLine('╠', '═', '╤', '╣'),
            starts_with_no_header=SeparatorLine('╔', '═', '╤', '╗'),
            table_body=SeparatorLine('╟', '─', '┼', '╢'),
            table_end=SeparatorLine('╚', '═', '╧', '╝'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            table_body=SeparatorLine('║', '│', None, '║')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bd_bl_ebody=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '╤', '╗'),
            header_inferior=SeparatorLine('╠', '═', '╧', '╣'),
            starts_with_no_header=SeparatorLine('╔', '═', '═', '╗'),
            table_body=None,
            table_end=SeparatorLine('╚', '═', '═', '╝'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', '│', None, '║'),
            table_body=SeparatorLine('║', ' ', None, '║')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    bd_bl_empty=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('╔', '═', '═', '╗'),
            header_inferior=SeparatorLine('╠', '═', '═', '╣'),
            starts_with_no_header=SeparatorLine('╔', '═', '═', '╗'),
            table_body=None,
            table_end=SeparatorLine('╚', '═', '═', '╝'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('║', ' ', None, '║'),
            table_body=SeparatorLine('║', ' ', None, '║')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),

    ###########################
    ####      +-|~oO:      ####
    ###########################
    pwrshll_alike=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '-', ' ', None),
            starts_with_no_header=None,
            table_body=None,
            table_end=None,
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, ' ', None, None),
            table_body=SeparatorLine(None, ' ', None, None)
        ),
        table_options=TableOptions(
            margin=0,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    presto=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '-', '+', None),
            starts_with_no_header=None,
            table_body=None,
            table_end=None
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, '|', None, None),
            table_body=SeparatorLine(None, '|', None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    grid=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '+', '+'),
            header_inferior=SeparatorLine('+', '=', '+', '+'),
            starts_with_no_header=SeparatorLine('+', '-', '+', '+'),
            table_body=SeparatorLine('+', '-', '+', '+'),
            table_end=SeparatorLine('+', '-', '+', '+'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    grid_eheader=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '-', '+'),
            header_inferior=SeparatorLine('+', '=', '+', '+'),
            starts_with_no_header=SeparatorLine('+', '-', '+', '+'),
            table_body=None,
            table_end=SeparatorLine('+', '-', '+', '+'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    grid_ebody=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '+', '+'),
            header_inferior=SeparatorLine('+', '=', '+', '+'),
            starts_with_no_header=SeparatorLine('+', '-', '-', '+'),
            table_body=None,
            table_end=SeparatorLine('+', '-', '-', '+'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            table_body=SeparatorLine('|', ' ', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    grid_empty=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '-', '+'),
            header_inferior=SeparatorLine('+', '=', '=', '+'),
            starts_with_no_header=SeparatorLine('+', '-', '-', '+'),
            table_body=None,
            table_end=SeparatorLine('+', '-', '-', '+'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            table_body=SeparatorLine('|', ' ', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    pipes=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine('|', '-', '|', '|'),
            starts_with_no_header=SeparatorLine('|', '-', '|', '|'),
            table_body=None,
            table_end=None,
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=True,
            align_indicator=AlignIndicator(':', ':'),
            when_centered_put_in_sides=True
        )
    ),
    tilde_grid=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '+', '+'),
            header_inferior=SeparatorLine('O', '~', 'O', 'O'),
            starts_with_no_header=SeparatorLine('O', '~', 'O', 'O'),
            table_body=SeparatorLine('+', '-', '+', '+'),
            table_end=SeparatorLine('O', '~', 'O', 'O')
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    tilg_eheader=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '-', '+'),
            header_inferior=SeparatorLine('O', '~', 'O', 'O'),
            starts_with_no_header=SeparatorLine('O', '~', 'O', 'O'),
            table_body=SeparatorLine('+', '-', '+', '+'),
            table_end=SeparatorLine('O', '~', 'O', 'O')
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    tilg_columns=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '+', '+'),
            header_inferior=SeparatorLine('O', '~', 'O', 'O'),
            starts_with_no_header=SeparatorLine('O', '~', 'O', 'O'),
            table_body=None,
            table_end=SeparatorLine('O', '~', 'O', 'O')
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    tilg_empty=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('+', '-', '-', '+'),
            header_inferior=SeparatorLine('O', '~', '~', 'O'),
            starts_with_no_header=SeparatorLine('O', '~', '~', 'O'),
            table_body=None,
            table_end=SeparatorLine('O', '~', '~', 'O')
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', ' ', None, '|'),
            table_body=SeparatorLine('|', ' ', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    orgtbl=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine('|', '-', '+', '|'),
            starts_with_no_header=None,
            table_body=None,
            table_end=None,
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('|', '|', None, '|'),
            table_body=SeparatorLine('|', '|', None, '|')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),

    ###################################
    #### Simple (horizontal lines) ####
    ###################################
    clean=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
            starts_with_no_header=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
            table_body=None,
            table_end=SeparatorLine(None, '─', INVISIBLE_SEPARATOR, None),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=0,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    simple=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            header_inferior=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            table_body=None,
            table_end=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None)
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    simple_bold=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            header_inferior=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            table_body=None,
            table_end=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None)
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    simple_head=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '-', '-' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=None,
            table_body=None,
            table_end=None
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    simple_head_bold=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '=', '=' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=None,
            table_body=None,
            table_end=None
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    sim_th_bl=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            header_inferior=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            table_body=None,
            table_end=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None)
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    sim_bd_bl=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            header_inferior=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            table_body=None,
            table_end=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None)
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    sim_head_th_bl=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '─', '─' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=None,
            table_body=None,
            table_end=None
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),
    sim_head_bd_bl=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=None,
            header_inferior=SeparatorLine(None, '═', '═' * len(INVISIBLE_SEPARATOR), None),
            starts_with_no_header=None,
            table_body=None,
            table_end=None
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None),
            table_body=SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    ),

    ##################
    ####   Other  ####
    ##################
    dashes=TableComposition(
        horizontal_composition=HorizontalComposition(
            header_superior=SeparatorLine('┌', '┄', '┬', '┐'),
            header_inferior=SeparatorLine('┝', '╍', '┿', '┥'),
            starts_with_no_header=SeparatorLine('┌', '┄', '┬', '┐'),
            table_body=None,
            table_end=SeparatorLine('└', '┄', '┴', '┘'),
        ),
        vertical_composition=VerticalComposition(
            header=SeparatorLine('┊', '┊', None, '┊'),
            table_body=SeparatorLine('┊', '┊', None, '┊')
        ),
        table_options=TableOptions(
            margin=MARGIN,
            align_sensitive=False,
            align_indicator=None,
            when_centered_put_in_sides=False
        )
    )
)
