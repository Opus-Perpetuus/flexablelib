"""
Print formatted tabular data in different styles
"""

# FORMATION OF THE TABLE
#
# Main Class.
# Here the whole table is formed

from .style_compositions import (
    __style_compositions as style_catalogue, 
    HorizontalComposition, 
    SeparatorLine,
    TableComposition
)
from .columns import (
    _column_widths,
    _typify_column,
    _align_columns,
    _align_headers,
    _float_extents,
    _is_numeric_cell,
    _round_float_cell,
    TYPE_NAMES,
    CAN_WRAP_TYPES,
    ALIGNMENTS_PER_TYPE as type_alignments
)
from .fast import truncate_to_width, visible_width, wrap_to_width
from .text_width import strip_ansi
from .table_strings import (
    _get_separators, 
    _get_data_rows, 
    DataRows
)
from .utils import (
    get_window_size,
    is_multi_row,
    is_some_instance,
    is_empty_cell,
    ValuePlacer,
    IndexCounter,
    IndexColumnTitle,
    to_roman,
)
from .options import (
    NONE_VALUE_REPLACEMENT,
    DEFAULT_STYLE,
    I_COL_TIT,
    DEFAULT_TRIMMING_SIGN,
    TABLE_ALIGNS,
    COLUMN_ALIGNS,
    ALIGNMENT_CODES,
    MIN_COLUMN_SIZE,
    CELL_MARGIN,
    INVISIBLE_SEPARATOR,
)
from .cells import (
    _wrap_rows,
    _zip_wrapped_rows
)
from .colors import background_hex, colorize, supports_color

from copy import deepcopy
from typing import (
    Any,
    List,
    Optional,
    Tuple,
    Union
)


class Table(object):
    """
    TABLE
    =====

    Makes a table out of tabular data

    ---------------
    POSSIBLE STYLES
    ---------------
    ### PLAIN
    >>> from flexablelib import Table
    >>> new_table = Table()
    >>> new_table.missing_val = 'n/a'
    >>> new_table.add_row(data=[1])
    >>> new_table.add_column(data=['Kg', 'ml'])
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'plain'
    ... column 1 column 2
    ...
    ... 1        Kg
    ... n/a      ml
    >>> new_table.show_headers = False
    >>> new_table
    ... 1   Kg
    ... n/a ml

    ---------------
    ### PRETTY_GRID
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'pretty_grid'
    ... ╒══════════╤══════════╕
    ... │ column 1 │ column 2 │
    ... ╞══════════╪══════════╡
    ... │ 1        │ Kg       │
    ... ├──────────┼──────────┤
    ... │ n/a      │ ml       │
    ... ╘══════════╧══════════╛
    >>> new_table.show_headers = False
    >>> new_table
    ... ╒═════╤════╕
    ... │ 1   │ Kg │
    ... ├─────┼────┤
    ... │ n/a │ ml │
    ... ╘═════╧════╛

    ---------------
    ### PRETTY_COLUMNS
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'pretty_columns'
    ... ╒══════════╤══════════╕
    ... │ column 1 │ column 2 │
    ... ╞══════════╪══════════╡
    ... │ 1        │ Kg       │
    ... │ n/a      │ ml       │
    ... ╘══════════╧══════════╛
    >>> new_table.show_headers = False
    >>> new_table
    ... ╒═════╤════╕
    ... │ 1   │ Kg │
    ... │ n/a │ ml │
    ... ╘═════╧════╛

    ---------------
    ### BOLD_HEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bold_header'
    ... ╔══════════╦══════════╗
    ... ║ column 1 ║ column 2 ║
    ... ╚══════════╩══════════╝
    ... │ 1        │ Kg       │
    ... ├──────────┼──────────┤
    ... │ n/a      │ ml       │
    ... └──────────┴──────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌─────┬────┐
    ... │ 1   │ Kg │
    ... ├─────┼────┤
    ... │ n/a │ ml │
    ... └─────┴────┘

    ---------------
    ### BHEADER_COLUMNS
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bheader_columns'
    ... ╔══════════╦══════════╗
    ... ║ column 1 ║ column 2 ║
    ... ╚══════════╩══════════╝
    ... │ 1        │ Kg       │
    ... │ n/a      │ ml       │
    ... └──────────┴──────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌─────┬────┐
    ... │ 1   │ Kg │
    ... │ n/a │ ml │
    ... └─────┴────┘

    ---------------
    ### BOLD_EHEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bold_eheader'
    ... ╔═════════════════════╗
    ... ║ column 1   column 2 ║
    ... ╚═════════════════════╝
    ... │ 1        │ Kg       │
    ... ├──────────┼──────────┤
    ... │ n/a      │ ml       │
    ... └──────────┴──────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌─────┬────┐
    ... │ 1   │ Kg │
    ... ├─────┼────┤
    ... │ n/a │ ml │
    ... └─────┴────┘

    ---------------
    ### BEHEADER_COLUMNS
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'beheader_columns'
    ... ╔═════════════════════╗
    ... ║ column 1   column 2 ║
    ... ╚═════════════════════╝
    ... │ 1        │ Kg       │
    ... │ n/a      │ ml       │
    ... └──────────┴──────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌─────┬────┐
    ... │ 1   │ Kg │
    ... │ n/a │ ml │
    ... └─────┴────┘

    ---------------
    ### BHEADER_EBODY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bheader_ebody'
    ... ╔═════════════════════╗
    ... ║ column 1   column 2 ║
    ... ╚═════════════════════╝
    ... │ 1          Kg       │
    ... │ n/a        ml       │
    ... └─────────────────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌──────────┐
    ... │ 1     Kg │
    ... │ n/a   ml │
    ... └──────────┘

    ---------------
    ### ROUND_EDGES
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'round_edges'
    ... ╭──────────┬──────────╮
    ... │ column 1 │ column 2 │
    ... ╞══════════╪══════════╡
    ... │ 1        │ Kg       │
    ... │ n/a      │ ml       │
    ... ╰──────────┴──────────╯
    >>> new_table.show_headers = False
    >>> new_table
    ... ╭─────┬────╮
    ... │ 1   │ Kg │
    ... │ n/a │ ml │
    ... ╰─────┴────╯

    ---------------
    ### RE_EHEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 're_eheader'
    ... ╭─────────────────────╮
    ... │ column 1   column 2 │
    ... ╞══════════╤══════════╡
    ... │ 1        │ Kg       │
    ... │ n/a      │ ml       │
    ... ╰──────────┴──────────╯
    >>> new_table.show_headers = False
    >>> new_table
    ... ╭─────┬────╮
    ... │ 1   │ Kg │
    ... │ n/a │ ml │
    ... ╰─────┴────╯

    ---------------
    ### RE_EBODY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 're_ebody'
    ... ╭─────────────────────╮
    ... │ column 1   column 2 │
    ... ╞═════════════════════╡
    ... │ 1          Kg       │
    ... │ n/a        ml       │
    ... ╰─────────────────────╯
    >>> new_table.show_headers = False
    >>> new_table
    ... ╭──────────╮
    ... │ 1     Kg │
    ... │ n/a   ml │
    ... ╰──────────╯

    ---------------
    ### THIN_BORDERLINE
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'thin_borderline'
    ... ┌──────────┬──────────┐
    ... │ column 1 │ column 2 │
    ... ╞══════════╪══════════╡
    ... │ 1        │ Kg       │
    ... ├──────────┼──────────┤
    ... │ n/a      │ ml       │
    ... └──────────┴──────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌─────┬────┐
    ... │ 1   │ Kg │
    ... ├─────┼────┤
    ... │ n/a │ ml │
    ... └─────┴────┘

    ---------------
    ### TH_BD_EHEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'th_bd_eheader'
    ... ┌─────────────────────┐
    ... │ column 1   column 2 │
    ... ╞══════════╤══════════╡
    ... │ 1        │ Kg       │
    ... ├──────────┼──────────┤
    ... │ n/a      │ ml       │
    ... └──────────┴──────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌─────┬────┐
    ... │ 1   │ Kg │
    ... ├─────┼────┤
    ... │ n/a │ ml │
    ... └─────┴────┘

    ---------------
    ### TH_BD_EBODY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'th_bd_ebody'
    ... ┌──────────┬──────────┐
    ... │ column 1 │ column 2 │
    ... ╞══════════╧══════════╡
    ... │ 1          Kg       │
    ... │ n/a        ml       │
    ... └─────────────────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌──────────┐
    ... │ 1     Kg │
    ... │ n/a   ml │
    ... └──────────┘

    ---------------
    ### TH_BD_EMPTY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'th_bd_empty'
    ... ┌─────────────────────┐
    ... │ column 1   column 2 │
    ... ╞═════════════════════╡
    ... │ 1          Kg       │
    ... │ n/a        ml       │
    ... └─────────────────────┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌──────────┐
    ... │ 1     Kg │
    ... │ n/a   ml │
    ... └──────────┘

    ---------------
    ### BOLD_BORDERLINE
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bold_borderline'
    ... ╔══════════╤══════════╗
    ... ║ column 1 │ column 2 ║
    ... ╠══════════╪══════════╣
    ... ║ 1        │ Kg       ║
    ... ╟──────────┼──────────╢
    ... ║ n/a      │ ml       ║
    ... ╚══════════╧══════════╝
    >>> new_table.show_headers = False
    >>> new_table
    ... ╔═════╤════╗
    ... ║ 1   │ Kg ║
    ... ╟─────┼────╢
    ... ║ n/a │ ml ║
    ... ╚═════╧════╝

    ---------------
    ### BD_BL_EHEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bd_bl_eheader'
    ... ╔═════════════════════╗
    ... ║ column 1   column 2 ║
    ... ╠══════════╤══════════╣
    ... ║ 1        │ Kg       ║
    ... ╟──────────┼──────────╢
    ... ║ n/a      │ ml       ║
    ... ╚══════════╧══════════╝
    >>> new_table.show_headers = False
    >>> new_table
    ... ╔═════╤════╗
    ... ║ 1   │ Kg ║
    ... ╟─────┼────╢
    ... ║ n/a │ ml ║
    ... ╚═════╧════╝

    ---------------
    ### BD_BL_EBODY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bd_bl_ebody'
    ... ╔══════════╤══════════╗
    ... ║ column 1 │ column 2 ║
    ... ╠══════════╧══════════╣
    ... ║ 1          Kg       ║
    ... ║ n/a        ml       ║
    ... ╚═════════════════════╝
    >>> new_table.show_headers = False
    >>> new_table
    ... ╔══════════╗
    ... ║ 1     Kg ║
    ... ║ n/a   ml ║
    ... ╚══════════╝

    ---------------
    ### BD_BL_EMPTY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'bd_bl_empty'
    ... ╔═════════════════════╗
    ... ║ column 1   column 2 ║
    ... ╠═════════════════════╣
    ... ║ 1          Kg       ║
    ... ║ n/a        ml       ║
    ... ╚═════════════════════╝
    >>> new_table.show_headers = False
    >>> new_table
    ... ╔══════════╗
    ... ║ 1     Kg ║
    ... ║ n/a   ml ║
    ... ╚══════════╝

    ---------------
    ### PWRSHLL_ALIKE
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'pwrshll_alike'
    ... column 1 column 2
    ... -------- --------
    ... 1        Kg
    ... n/a      ml
    >>> new_table.show_headers = False
    >>> new_table
    ... 1   Kg
    ... n/a ml

    ---------------
    ### PRESTO
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'presto'
    ...  column 1 | column 2
    ... ----------+----------
    ...  1        | Kg
    ...  n/a      | ml
    >>> new_table.show_headers = False
    >>> new_table
    ...  1   | Kg
    ...  n/a | ml

    ---------------
    ### GRID
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'grid'
    ... +----------+----------+
    ... | column 1 | column 2 |
    ... +==========+==========+
    ... | 1        | Kg       |
    ... +----------+----------+
    ... | n/a      | ml       |
    ... +----------+----------+
    >>> new_table.show_headers = False
    >>> new_table
    ... +-----+----+
    ... | 1   | Kg |
    ... +-----+----+
    ... | n/a | ml |
    ... +-----+----+

    ---------------
    ### GRID_EHEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'grid_eheader'
    ... +---------------------+
    ... | column 1   column 2 |
    ... +==========+==========+
    ... | 1        | Kg       |
    ... | n/a      | ml       |
    ... +----------+----------+
    >>> new_table.show_headers = False
    >>> new_table
    ... +-----+----+
    ... | 1   | Kg |
    ... | n/a | ml |
    ... +-----+----+

    ---------------
    ### GRID_EBODY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'grid_ebody'
    ... +----------+----------+
    ... | column 1 | column 2 |
    ... +==========+==========+
    ... | 1          Kg       |
    ... | n/a        ml       |
    ... +---------------------+
    >>> new_table.show_headers = False
    >>> new_table
    ... +----------+
    ... | 1     Kg |
    ... | n/a   ml |
    ... +----------+

    ---------------
    ### GRID_EMPTY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'grid_empty'
    ... +---------------------+
    ... | column 1   column 2 |
    ... +=====================+
    ... | 1          Kg       |
    ... | n/a        ml       |
    ... +---------------------+
    >>> new_table.show_headers = False
    >>> new_table
    ... +----------+
    ... | 1     Kg |
    ... | n/a   ml |
    ... +----------+

    ---------------
    ### PIPES
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'pipes'
    ... | column 1 | column 2 |
    ... |----------|----------|
    ... | 1        | Kg       |
    ... | n/a      | ml       |
    >>> new_table.show_headers = False
    >>> new_table
    ... |-----|----|
    ... | 1   | Kg |
    ... | n/a | ml |

    ---------------
    ### TILDE_GRID
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'tilde_grid'
    ... +----------+----------+
    ... | column 1 | column 2 |
    ... O~~~~~~~~~~O~~~~~~~~~~O
    ... | 1        | Kg       |
    ... +----------+----------+
    ... | n/a      | ml       |
    ... O~~~~~~~~~~O~~~~~~~~~~O
    >>> new_table.show_headers = False
    >>> new_table
    ... O~~~~~O~~~~O
    ... | 1   | Kg |
    ... +-----+----+
    ... | n/a | ml |
    ... O~~~~~O~~~~O

    ---------------
    ### TILG_EHEADER
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'tilg_eheader'
    ... +---------------------+
    ... | column 1   column 2 |
    ... O~~~~~~~~~~O~~~~~~~~~~O
    ... | 1        | Kg       |
    ... +----------+----------+
    ... | n/a      | ml       |
    ... O~~~~~~~~~~O~~~~~~~~~~O
    >>> new_table.show_headers = False
    >>> new_table
    ... O~~~~~O~~~~O
    ... | 1   | Kg |
    ... +-----+----+
    ... | n/a | ml |
    ... O~~~~~O~~~~O

    ---------------
    ### TILG_COLUMNS
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'tilg_columns'
    ... +----------+----------+
    ... | column 1 | column 2 |
    ... O~~~~~~~~~~O~~~~~~~~~~O
    ... | 1        | Kg       |
    ... | n/a      | ml       |
    ... O~~~~~~~~~~O~~~~~~~~~~O
    >>> new_table.show_headers = False
    >>> new_table
    ... O~~~~~O~~~~O
    ... | 1   | Kg |
    ... | n/a | ml |
    ... O~~~~~O~~~~O

    ---------------
    ### TILG_EMPTY
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'tilg_empty'
    ... +---------------------+
    ... | column 1   column 2 |
    ... O~~~~~~~~~~~~~~~~~~~~~O
    ... | 1          Kg       |
    ... | n/a        ml       |
    ... O~~~~~~~~~~~~~~~~~~~~~O
    >>> new_table.show_headers = False
    >>> new_table
    ... O~~~~~~~~~~O
    ... | 1     Kg |
    ... | n/a   ml |
    ... O~~~~~~~~~~O

    ---------------
    ### ORGTBL
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'orgtbl'
    ... | column 1 | column 2 |
    ... |----------+----------|
    ... | 1        | Kg       |
    ... | n/a      | ml       |
    >>> new_table.show_headers = False
    >>> new_table
    ... | 1   | Kg |
    ... | n/a | ml |

    ---------------
    ### CLEAN
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'clean'
    ... column 1 column 2
    ... ──────── ────────
    ... 1        Kg
    ... n/a      ml
    ... ──────── ────────
    >>> new_table.show_headers = False
    >>> new_table
    ... ─── ──
    ... 1   Kg
    ... n/a ml
    ... ─── ──

    ---------------
    ### SIMPLE
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'simple'
    ... ---------------------
    ...  column 1   column 2
    ... ---------------------
    ...  1          Kg
    ...  n/a        ml
    ... ---------------------
    >>> new_table.show_headers = False
    >>> new_table
    ... ----------
    ...  1     Kg
    ...  n/a   ml
    ... ----------

    ---------------
    ### SIMPLE_BOLD
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'simple_bold'
    ... =====================
    ...  column 1   column 2
    ... =====================
    ...  1          Kg
    ...  n/a        ml
    ... =====================
    >>> new_table.show_headers = False
    >>> new_table
    ... ==========
    ...  1     Kg
    ...  n/a   ml
    ... ==========

    ---------------
    ### SIMPLE_HEAD
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'simple_head'
    ...  column 1   column 2
    ... ---------------------
    ...  1          Kg
    ...  n/a        ml
    >>> new_table.show_headers = False
    >>> new_table
    ...  1     Kg
    ...  n/a   ml

    ---------------
    ### SIMPLE_HEAD_BOLD
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'simple_head_bold'
    ...  column 1   column 2
    ... =====================
    ...  1          Kg
    ...  n/a        ml
    >>> new_table.show_headers = False
    >>> new_table
    ...  1     Kg
    ...  n/a   ml

    ---------------
    ### SIM_TH_BL
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'sim_th_bl'
    ... ─────────────────────
    ...  column 1   column 2
    ... ─────────────────────
    ...  1          Kg
    ...  n/a        ml
    ... ─────────────────────
    >>> new_table.show_headers = False
    >>> new_table
    ... ──────────
    ...  1     Kg
    ...  n/a   ml
    ... ──────────

    ---------------
    ### SIM_BD_BL
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'sim_bd_bl'
    ... ═════════════════════
    ...  column 1   column 2
    ... ═════════════════════
    ...  1          Kg
    ...  n/a        ml
    ... ═════════════════════
    >>> new_table.show_headers = False
    >>> new_table
    ... ══════════
    ...  1     Kg
    ...  n/a   ml
    ... ══════════

    ---------------
    ### SIM_HEAD_TH_BL
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'sim_head_th_bl'
    ...  column 1   column 2
    ... ─────────────────────
    ...  1          Kg
    ...  n/a        ml
    >>> new_table.show_headers = False
    >>> new_table
    ...  1     Kg
    ...  n/a   ml

    ---------------
    ### SIM_HEAD_BD_BL
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'sim_head_bd_bl'
    ...  column 1   column 2
    ... ═════════════════════
    ...  1          Kg
    ...  n/a        ml
    >>> new_table.show_headers = False
    >>> new_table
    ...  1     Kg
    ...  n/a   ml

    ---------------
    ### DASHES
    >>> new_table.show_headers = True
    >>> new_table.style_name = 'dashes'
    ... ┌┄┄┄┄┄┄┄┄┄┄┬┄┄┄┄┄┄┄┄┄┄┐
    ... ┊ column 1 ┊ column 2 ┊
    ... ┝╍╍╍╍╍╍╍╍╍╍┿╍╍╍╍╍╍╍╍╍╍┥
    ... ┊ 1        ┊ Kg       ┊
    ... ┊ n/a      ┊ ml       ┊
    ... └┄┄┄┄┄┄┄┄┄┄┴┄┄┄┄┄┄┄┄┄┄┘
    >>> new_table.show_headers = False
    >>> new_table
    ... ┌┄┄┄┄┄┬┄┄┄┄┐
    ... ┊ 1   ┊ Kg ┊
    ... ┊ n/a ┊ ml ┊
    ... └┄┄┄┄┄┴┄┄┄┄┘

    ---------------
    """

    def __init__(self, rows=None, columns=None, headers=None, style_name='',
                 missing_val='', header_style=None) -> None:
        # +------------------------+ PARAMETERS +------------------------+
        self.__missing_value = missing_val
        self.__value_placer = ValuePlacer()
        # Its own object, so a data column called 'i' cannot collide
        # with it in the dicts that are keyed by header.
        self.__index_title = IndexColumnTitle(I_COL_TIT)
        self.__str_align = None
        self.__int_align = None
        self.__float_align = None
        self.__bool_align = None
        self.__table_align = None
        self.__column_align = None
        self.__show_index = False
        self.__roman_index = False
        self.__i_start = 0
        self.__i_step = 1
        self.__index_counter = IndexCounter()
        # Display-only: number data columns 1..n instead of header names.
        self.__number_columns = False
        # Strip leading/trailing whitespace from displayed cell strings.
        self.__strip_cells = False
        # PrettyTable-style rule toggles: None keeps the style as authored.
        # Values: 'all' | 'frame' | 'header' | 'none' (hrules);
        #         'all' | 'frame' | 'none' (vrules).
        self.__hrules = None
        self.__vrules = None
        self.__parse_numbers = True
        self.__parse_str_numbers = False
        self.__auto_wrap_table = False
        # Grow columns to fill the available width when the table is narrower.
        self.__expand_to_window = False
        self.__leading_zeros = None
        self.__float_spaces = 2
        self.__format_exponential = True
        # Cell formatters applied on the render path only; raw storage and
        # type detection keep the original Python values.
        self.__float_format = None
        self.__int_format = None
        self.__custom_format = None
        # Per-column width floors and ceilings (table.max_width is the
        # whole-table budget and is unrelated).
        self.__column_min_width = None
        self.__column_max_width = None
        # Header alignment independent of the body column alignment.
        self.__header_align = None
        # Optional title drawn above the table.
        self.__title = None
        # Optional caption drawn below the table (Rich/tablewriter style).
        self.__caption = None
        # Alternating body-row colours: None, a single odd-row spec, or (even, odd).
        self.__zebra = None
        # Last N rendered body rows treated as footer (Spectre/tablewriter).
        self.__footer_rows = 0
        self.__footer_color = None
        # Per-cell colour map: keys (row, col_index|header) -> colour spec.
        self.__cell_colors = {}
        # Override style cell margin (spaces each side); None keeps style default.
        self.__cell_padding = None
        # 'wrap' | 'truncate' | None (None defers to auto_wrap bool).
        self.__overflow = None
        # Vertical cell align: 't'/'m'/'b' default, plus per-column / per-cell maps.
        self.__valign = 't'
        self.__col_valign = None
        self.__cell_valign = {}
        # Outer panel frame (tabled/Spectre style) + optional shadow.
        self.__panel = False
        self.__shadow = False
        # Row indexes after which a horizontal rule is forced.
        self.__dividers = set()
        # Columns hidden by name or index (go-pretty / prettytable suppress).
        self.__hide_columns = ()
        # Sort / filter applied to the display copy, not to stored data.
        self.__sort_by = None
        self.__sort_reverse = False
        self.__row_filter = None
        # Filled during compose so filter/sort and empty-row hiding share
        # the same row indices for the current render.
        self.__compose_empty_row_indexes = None
        # +--------------------------+ STYLE +---------------------------+
        # HEADER STYLES: None, l, u, t, c
        #   None: unmodified
        #   l: lower case
        #   u: upper case
        #   t: title
        #   c: capitalized
        self.__header_style = header_style
        # +------------------------+ COLOUR +---------------------------+
        # Specs are resolved to escape sequences once per render, not per
        # cell. None everywhere means no colour and no cost.
        self.__header_color = None
        self.__border_color = None
        # LineText-style overlays (tabled): text drawn onto border runs.
        self.__border_texts = []
        self.__column_colors = {}
        self.__row_colors = {}
        self.__color_rule = None
        # None means "decide from the output stream"; True and False force it.
        self.__use_colors = None
        # +----------------------+ MERGED CELLS +-----------------------+
        self.__merged_regions = []
        # +---------------------+ FITTING +-----------------------------+
        # None means "use the terminal width".
        self.__max_width = None
        # Shown instead of the table when it cannot fit legibly. None keeps
        # the old behaviour of rendering it anyway, however cramped.
        self.__too_narrow_message = None
        self.__show_margin = True
        self.__show_empty_columns = True
        self.__show_empty_rows = True
        self.__generic_column_name = 'column'
        self.__style_name = style_name
        # +------------------+ TABLE CHARACTERISTICS +-------------------+
        self.__show_headers = True
        self.__table_height = 0
        self.__table_height_with_i = 0
        self.__table_width = 0
        self.__table_width_with_i = 0
        self.__real_row_count = 0
        self.__real_column_count = 0
        self.__line_spacing = 0
        self.__cell_types = {}
        self.__cell_types_with_i = {self.__index_title: []}
        self.__column_types = {}
        self.__column_types_with_i = {
            self.__index_title: TYPE_NAMES.int_
        }
        self.__column_types_as_list = []
        self.__column_types_as_list_with_i = []
        self.__column_i_per_type = {}
        self.__column_i_per_type_with_i = {}
        self.__float_columns_widths = {}
        self.__float_columns_widths_with_i = {}
        self.__column_widths = {}
        self.__column_widths_with_i = {}
        self.__column_widths_as_list = []
        self.__column_widths_as_list_with_i = []
        self.__table_alignment = TABLE_ALIGNS.left
        self.__column_alignments = {}
        self.__column_alignments_with_i = {
            self.__index_title: type_alignments[TYPE_NAMES.int_]
        }
        self.__column_alignments_as_list = []
        self.__column_alignments_as_list_with_i = []
        self.__row_alignments = {}
        self.__row_alignments_as_list = []
        self.__cells_alignment = []
        # +------------------------+ TABLE BODY +------------------------+
        self.__columns = {}
        self.__columns_with_i = {self.__index_title: []}
        self.__headers = []
        self.__headers_with_i = [self.__index_title]
        self.__rows = []
        self.__rows_with_i = []
        self.__processed_columns = {}
        self.__processed_columns_with_i = {self.__index_title: []}
        self.__semi_processed_columns = {}
        self.__semi_processed_columns_with_i = {self.__index_title: []}
        self.__processed_headers = []
        self.__processed_headers_with_i = []
        self.__processed_rows = []
        self.__processed_rows_with_i = []
        # +-----------------------+ INIT ACTIONS +-----------------------+
        try:
            for header, column in columns.items():
                try:
                    column.__iter__
                    self.add_column(header=header, data=list(column))
                except AttributeError:
                    pass
            return None
        except (AttributeError, TypeError):
            pass
        try:
            for header in headers:
                self.__check_add_header_on_init(header)
        except TypeError:
            pass
        try:
            for row in rows:
                try:
                    row.__iter__
                    self.add_row(data=list(row))
                except AttributeError:
                    pass
            empty_to_add = len(headers) - len(rows[0])
            for _ in range(empty_to_add):
                self.add_column()
            return None
        except (TypeError, IndexError):
            pass
        try:
            for column in columns:
                try:
                    column.__iter__
                    self.add_column(data=list(column))
                except AttributeError:
                    pass
            empty_to_add = len(headers) - len(columns)
            for _ in range(empty_to_add):
                self.add_column()
        except TypeError:
            pass

    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ METHODS +---------------------------+ start

    def __str__(self) -> str:
        return self.compose()
    
    
    def __repr__(self) -> str:
        return self.compose()

    # end +-----------------------------+ METHODS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+


    # +-----------------------------------------------------------------------------+
    # start +-----------------------+ STATIC METHODS +------------------------+ start
    
    @staticmethod
    def __apply_wrap(piece: str, new_width: int) -> str:
        """
        Break a cell to fit ``new_width`` visible columns.

        ``textwrap.wrap`` counts characters, so a column of CJK text or of
        coloured cells wrapped a column or more too late and the table drifted
        out of alignment. It also raises on a width of zero, which is what
        issue #17 reported; ``wrap_to_width`` floors the width at one instead.
        """
        return '\n'.join(wrap_to_width(str(piece), new_width))
    
    @staticmethod
    def __trim_with_sign(piece: str, new_width: int) -> str:
        """
        Cut a cell down to ``new_width`` visible columns, marker included.

        The marker is part of the budget, not an addition to it. Appending it
        afterwards -- which this used to do -- made every trimmed cell three
        columns wider than the width it had just been trimmed to, so a table
        that was shrunk to fit overflowed anyway.

        Measurement is by visible width, so a coloured or double-width cell
        is cut where it looks cut, and an escape sequence is never split in
        half.
        """
        return truncate_to_width(
            str(piece), new_width, DEFAULT_TRIMMING_SIGN
        )
        
    @staticmethod
    def __check_if_none_and_get_len(value: Union[str, None]) -> int:
        """
        Checks if a value is::

            None | string
        
        Returns::
        
            None    # The len of the default value for None
            string  # The len of the string
        """
        if value is None:
            value_len = len(NONE_VALUE_REPLACEMENT)
        else:
            value_len = len(value)
        return value_len
    
    @staticmethod
    def __zip_columns(columns: Union[List[Union[list, tuple]], Tuple[Union[list, tuple]]], 
                      headers: Union[list, tuple]=False
                     ) -> Tuple[Union[Tuple[str], Tuple[Tuple[str]]]]:
        """
        Transforms columns into rows by zipping them.
        """
        if headers:
            row = tuple(map(lambda x: x, columns))
            if is_multi_row(row):
                zipped = tuple(zip(*row))
                return zipped
            else:
                zipped = row
        else:
            half_zipped = zip(*columns)
            
            # Map trough the half zipped columns.
            zipped = tuple(map(
                lambda s_row: tuple(
                    zip(*s_row)  # Zip if it's wrapped.
                ) if is_multi_row(
                    s_row  # Don't do anything on contrary.
                ) else s_row,
                half_zipped
            ))

        return zipped

    # @staticmethod
    # def __new_dict(key, value):
    #     """
    #     Simply a new dict out of key and value
    #     """
    #     new_dict = {}
    #     new_dict[key] = value
    #     return new_dict
    
    # end +-------------------------+ STATIC METHODS +--------------------------+ end
    # +-----------------------------------------------------------------------------+


    # TODO add the rest of getters
    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ GETTERS +---------------------------+ start

    @property
    def columns(self) -> dict:
        """
        The data of the table by columns.
        
        Comes arranged in a dictionary with the 
        following structure::
        
            {
                'header': (data, data, ...),
                ...
            }
        """
        return self.__columns

    @property
    def headers(self) -> list:
        """
        The titles or headers of each column.
        A generic name appears if no name was provided
        for the column.
        """
        return self.__headers
    
    @property
    def internal_columns(self) -> dict:
        """
        Includes columns that the class adds internally,
        for now only the index column (when shown). 
        
        Uses the same format as the columns property.
        """
        if self.__show_index:
            return self.__columns_with_i
        else:
            return self.__columns
        
    
    @property
    def internal_headers(self) -> list:
        """
        Headers that includes the index column (when shown).
        """
        if self.__show_index:
            return self.__headers_with_i
        else:
            return self.__headers
        
    @property
    def rows(self) -> List[list]:
        """
        The data of the table as rows.
        """
        return self.__rows
    
    @property
    def internal_rows(self) -> List[list]:
        """
        The data of the table as rows, including the 
        index column (when shown).
        """
        if self.__show_index:
            return self.__rows_with_i
        else:
            return self.__rows

    @property
    def style_name(self) -> str:
        """
        The name of the style used to print the table.
        
        Default style is::
        
            'grid_eheader'
            
        The default style is selected if the provided
        one is incorrect (not one of the following)::
        
            'plain'            'pretty_grid' 
            'pretty_columns'   'bold_header' 
            'bheader_columns'  'bold_eheader' 
            'beheader_columns' 'bheader_ebody' 
            'round_edges'      're_eheader' 
            're_ebody'         'thin_borderline' 
            'th_bd_eheader'    'th_bd_ebody' 
            'th_bd_empty'      'bold_borderline' 
            'bd_bl_eheader'    'bd_bl_ebody' 
            'bd_bl_empty'      'pwrshll_alike' 
            'presto'           'grid' 
            'grid_eheader'     'grid_ebody' 
            'grid_empty'       'pipes' 
            'tilde_grid'       'tilg_eheader' 
            'tilg_columns'     'tilg_empty' 
            'orgtbl'           'clean' 
            'simple'           'simple_bold' 
            'simple_head'      'simple_head_bold' 
            'sim_th_bl'        'sim_bd_bl' 
            'sim_head_th_bl'   'sim_head_bd_bl' 
            'dashes'
            
        """
        return self.__checked_style_name

    @property
    def missing_value(self) -> Any:
        """
        A placeholder for empty cells.

        Default is::

            ''

        ``missing_val`` is an alias of this attribute (same name as the
        ``Table(..., missing_val=...)`` constructor argument).
        """
        return self.__missing_value

    @property
    def missing_val(self) -> Any:
        """Alias of :attr:`missing_value`."""
        return self.__missing_value

    @property
    def str_align(self):
        """
        Alignment for every string column: ``'l'``, ``'c'`` or ``'r'``.

        ``None``, the default, leaves the typographic convention in place --
        strings left, numbers right, floats on the decimal point.
        """
        return self.__str_align

    @property
    def int_align(self):
        """
        Alignment for every integer column. See :attr:`str_align`.
        """
        return self.__int_align

    @property
    def float_align(self):
        """
        Alignment for every float column. See :attr:`str_align`.

        ``'f'`` is the default behaviour written out: pad each cell so the
        decimal points share one axis.
        """
        return self.__float_align

    @property
    def bool_align(self):
        """
        Alignment for every boolean column. See :attr:`str_align`.
        """
        # Returned __float_align until now, so reading this back never
        # reported what had been set.
        return self.__bool_align

    @property
    def table_align(self):
        """
        Where the finished table sits in the available width.

        ``'l'`` (default), ``'c'`` or ``'r'``, or the table codes
        ``tl`` / ``tc`` / ``tr``. The table is padded with spaces on the left
        (and right for centre) so a narrow table can sit in a wide terminal.
        """
        return self.__table_align

    @property
    def col_alignment(self):
        """
        Alignment for particular columns, overriding the type default.

        One code for the whole table, a sequence in column order, or a
        mapping keyed by header. The index column is never affected.
        """
        return self.__column_align

    @property
    def leading_zeros(self):
        """
        Pad integer cells with leading zeros to this many digits.

        Applied on the render path when ``int_format`` is not set. A value
        of ``None`` or ``0`` leaves integers alone. Negative signs sit outside
        the zero padding (``-007`` for ``-7`` with three digits).
        """
        return self.__leading_zeros

    @property
    def style_composition(self) -> TableComposition:
        """
        A named tuple that indicates the characters used
        for each line of the table.
        """
        return self.__style_composition

    @property
    def empty_rows_i(self) -> list:
        """
        A list with the indexes of the empty rows.
        """
        return self.__empty_row_indexes

    @property
    def empty_columns_i(self) -> list:
        """
        A list with the indexes of the empty columns.
        """
        if self.__show_index:
            
            # If the index column is shown, subtract 1 from the empty
            # columns indexes because it's only meant for visual
            # representation or internal count.
            return list(map(
                lambda empty_col_i: empty_col_i - 1,
                self.__empty_column_indexes
            ))
            
        return self.__empty_column_indexes

    @property
    def possible_styles(self):
        """
        Returns a tuple with the admitted style names.
        """
        return self.__possible_styles

    @property
    def row_count(self):
        """
        Returns the count of rows conditioned byt the
        ``show_empty_rows`` property.
        """
        return self.__row_count

    @property
    def column_count(self):
        """
        Returns the count of columns conditioned byt the
        ``show_empty_columns`` property.
        """
        if self.__show_index:
            return self.__column_count - 1
        return self.__column_count

    @property
    def shape(self):
        """
        ``(rows, columns)`` as currently counted for display.

        Honours ``show_empty_rows`` and ``show_empty_columns``, matching
        ``row_count`` and ``column_count``. Does not re-render.
        """
        return (self.row_count, self.column_count)

    @property
    def float_format(self):
        """
        How float cells are printed.

        A format mini-language string (``.2f``, ``{:.2f}``, ``%.2f``) or a
        callable taking the float and returning a string. Applied only when
        rendering; stored values and type detection stay numeric so decimal
        alignment still works on the formatted text.
        """
        return self.__float_format

    @property
    def int_format(self):
        """
        How integer cells are printed. Same forms as :attr:`float_format`.
        """
        return self.__int_format

    @property
    def custom_format(self):
        """
        Per-column or global formatter applied after type-specific ones.

        A callable ``(value) -> str``, or a mapping of header to format string
        or callable. Only cells that still look like their original value
        after ``float_format`` / ``int_format`` are candidates when the
        mapping key matches.
        """
        return self.__custom_format

    @property
    def column_min_width(self):
        """
        Smallest each column may measure, as an int, sequence, or header map.
        """
        return self.__column_min_width

    @property
    def column_max_width(self):
        """
        Largest each column may measure, as an int, sequence, or header map.

        Content beyond the cap is wrapped or trimmed like a terminal fit.
        Distinct from :attr:`max_width`, which budgets the whole table.
        """
        return self.__column_max_width

    @property
    def header_align(self):
        """
        Alignment for header cells only.

        One code, a sequence, or a mapping by header. Body cells keep
        :attr:`col_alignment` and the type defaults.
        """
        return self.__header_align

    @property
    def title(self):
        """
        Optional text drawn above the table, centred on the table width.
        """
        return self.__title

    @property
    def caption(self):
        """
        Optional text drawn below the table, centred on the table width.

        Distinct from :attr:`title` (above). Inspired by Rich captions and
        go ``tablewriter`` / Spectre footers' companion labels.
        """
        return self.__caption

    @property
    def zebra(self):
        """
        Alternating body-row colours (Rich ``row_styles`` / zebra striping).

        Accepts ``None`` (off), a single colour spec applied to odd rows
        (1, 3, …), or a two-item sequence ``(even_spec, odd_spec)``. Empty
        / falsy specs leave that parity uncoloured. Alias: :attr:`row_stripe`.
        """
        return self.__zebra

    @property
    def row_stripe(self):
        """Alias of :attr:`zebra`."""
        return self.__zebra

    @property
    def footer_rows(self):
        """
        Number of trailing body rows treated as a footer band.

        Combined with :attr:`footer_color`. Does not change stored data.
        """
        return self.__footer_rows

    @property
    def footer_color(self):
        """Colour spec applied to the trailing :attr:`footer_rows` band."""
        return self.__footer_color

    @property
    def cell_colors(self):
        """
        Per-cell colour map.

        Keys are ``(row_index, column)`` where ``column`` is a header name or
        0-based column index (index column excluded, matching merges)::

            table.cell_colors = {(0, 'Status'): 'bold green', (2, 1): 'reverse'}
        """
        return self.__cell_colors

    @property
    def cell_padding(self):
        """
        Spaces on each side of every cell, overriding the style margin.

        ``None`` keeps the style default (and honours :attr:`show_margin`).
        """
        return self.__cell_padding

    @property
    def overflow(self):
        """
        How cells behave when wider than their column: ``'wrap'``,
        ``'truncate'``, or ``None`` to defer to :attr:`auto_wrap`.
        """
        return self.__overflow

    @property
    def valign(self):
        """
        Default vertical cell alignment inside a multi-line row: ``'t'``,
        ``'m'``, or ``'b'`` (texttable-style). Overridden by
        :attr:`col_valign` and :attr:`cell_valign`.
        """
        return self.__valign

    @property
    def col_valign(self):
        """
        Per-column vertical alignment: a code, list/tuple of codes, or
        ``{header_or_index: code}``.
        """
        return self.__col_valign

    @property
    def cell_valign(self):
        """
        Per-cell vertical alignment map ``{(row, col): 't'|'m'|'b'}``.
        ``col`` may be a header name or 0-based index.
        """
        return self.__cell_valign

    @property
    def panel(self):
        """
        When true (or a box style name), wrap the composed table in an outer
        frame. Inspired by tabled Panel / Spectre Panel.
        """
        return self.__panel

    @property
    def shadow(self):
        """
        When true (or a character), draw a drop-shadow on the right and
        bottom of the composed table (or of the panel, when both are set).
        """
        return self.__shadow

    @property
    def sort_by(self):
        """
        Column header, 0-based index, or callable ``key(row)`` used to order
        rows at render time.
        """
        return self.__sort_by

    @property
    def sort_reverse(self):
        """
        When true, :attr:`sort_by` orders descending.
        """
        return self.__sort_reverse

    @property
    def row_filter(self):
        """
        Callable ``(row) -> bool``; rows that return false are not rendered.

        Receives the stored row (before formatters). Does not mutate storage.
        """
        return self.__row_filter

    @property
    def expand_to_window(self):
        """
        When true, grow columns so the table fills the available width.

        Only expands; it never shrinks. Shrinking is handled by the fit pass
        and :attr:`max_width`.
        """
        return self.__expand_to_window

    @property
    def internal_row_count(self):
        """
        Returns the count of rows including the index column
        and the empty rows (even if hidden).
        """
        return self.__real_row_count

    @property
    def internal_column_count(self):
        """
        Returns the count of rows including the index column
        and the empty rows (even if hidden).
        """
        return self.__checked_real_column_count
    
    @property
    def show_index(self) -> bool:
        """
        If set to::
        
            True  # An index column is added to the left.
            False # No index column is added (default).
        """
        return self.__show_index
    
    @property
    def index_start(self) -> int:
        """
        The starting number of the index count.
        """
        return self.__i_start
    
    @property
    def index_step(self):
        """
        Amount between each index number.
        """
        return self.__i_step

    @property
    def index_title(self):
        """
        Header label for the index column when ``show_index`` is True.

        Default is ``'i'``. Changing it rebinds the internal index key so
        existing rows keep their index cells.
        """
        return str(self.__index_title)

    @property
    def roman_index(self):
        """
        When True with ``show_index``, index values render as Roman numerals.
        """
        return self.__roman_index

    @property
    def number_columns(self):
        """
        When True, data column headers display as ``1``, ``2``, … (1-based).

        Stored header names are unchanged; only the composed table uses
        numbers. The index column (if shown) keeps ``index_title``.
        """
        return self.__number_columns

    @property
    def strip_cells(self):
        """
        When True, strip leading/trailing whitespace from string cells on
        display (storage untouched).
        """
        return self.__strip_cells

    @property
    def hrules(self):
        """
        Horizontal rule mode: ``None``/``'all'`` (style default), ``'frame'``
        (top/bottom only), ``'header'`` (no body separators), or ``'none'``.
        """
        return self.__hrules

    @property
    def vrules(self):
        """
        Vertical rule mode: ``None``/``'all'`` (style default), ``'frame'``
        (outer edges only), or ``'none'``.
        """
        return self.__vrules

    @property
    def max_table_width(self):
        """Alias of :attr:`max_width` (PrettyTable / comfy-table naming)."""
        return self.max_width

    @property
    def justify(self):
        """Alias of :attr:`table_align` (whole-table left/center/right)."""
        return self.table_align

    @property
    def suppress_empty(self):
        """
        When True, hide both empty rows and empty columns
        (``show_empty_rows`` / ``show_empty_columns`` become False).
        """
        return (not self.__show_empty_rows) and (not self.__show_empty_columns)
    
    @property
    def auto_wrap(self):
        """
        If set to::
        
            True  # The cells are wrapped if needed.
            False # They are trimmed instead (default).
        """
        return self.__auto_wrap_table
    
    # +----------------------+ SHOW GETTERS +------------------------+

    @property
    def show_headers(self):
        """
        If set to::
        
            True  # The headers are shown (default).
            False # The headers are hidden.
            
        The widths of the columns are adjusted to fit the headers,
        so if they are hidden the widths of the columns could
        change.
        """
        return self.__show_headers
    
    @property    
    def show_margin(self):
        """
        Whether cells keep the blank column the style puts on each side.
        """
        return self.__show_margin

    @property
    def show_empty_rows(self):
        """
        If set to::
        
            True  # The empty rows are shown (default).
            False # The empty rows are hidden.
        """
        return self.__show_empty_rows

    @property
    def show_empty_columns(self):
        """
        If set to::
        
            True  # The empty columns are shown (default).
            False # The empty columns are hidden.
        """
        return self.__show_empty_columns

    # end +-----------------------------+ GETTERS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+
    
    
    # TODO add the rest of setters
    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ SETTERS +---------------- -----------+ start

    # @columns.setter
    # def columns(self, value: dict):
    #     self.__columns = {} if value is None else value

    # @headers.setter
    # def headers(self, value: list):
    #     self.__headers = [] if value is None else value
    #     self.__headers_with_i = [] if value is None else [I_COL_TIT, *value]

    @style_name.setter
    def style_name(self, value):
        """
        Set the border style by name. See ``possible_styles`` for the list.

        This used to read style_examples.md into a local named __doc__, which
        set no docstring anywhere -- assigning to a local cannot -- but did
        open a file on every assignment, resolved against the working
        directory. Installed as a package that file is not there, so setting
        style_name raised FileNotFoundError from anywhere but the repository
        root.
        """
        self.__style_name = value

    @missing_value.setter
    def missing_value(self, value):
        self.__missing_value = value

    @missing_val.setter
    def missing_val(self, value):
        self.__missing_value = value

    @str_align.setter
    def str_align(self, value):
        self.__str_align = self.__checked_alignment(value, 'str_align')

    @int_align.setter
    def int_align(self, value):
        self.__int_align = self.__checked_alignment(value, 'int_align')

    @float_align.setter
    def float_align(self, value):
        self.__float_align = self.__checked_alignment(value, 'float_align')

    @bool_align.setter
    def bool_align(self, value):
        # Wrote __float_align until now, so setting this silently moved the
        # float columns instead and left the booleans where they were.
        self.__bool_align = self.__checked_alignment(value, 'bool_align')

    @table_align.setter
    def table_align(self, value):
        if value is None:
            self.__table_align = None
            return
        allowed = {
            COLUMN_ALIGNS.left, COLUMN_ALIGNS.center, COLUMN_ALIGNS.right,
            TABLE_ALIGNS.left, TABLE_ALIGNS.center, TABLE_ALIGNS.right,
            'l', 'c', 'r', 'left', 'center', 'right',
        }
        if value not in allowed:
            raise ValueError(
                'table_align must be one of l/c/r (or tl/tc/tr), got {0!r}'
                .format(value)
            )
        self.__table_align = value

    @col_alignment.setter
    def col_alignment(self, value):
        """
        Alignment for particular columns, overriding the type default.

        Accepts one code for the whole table, a sequence in column order, or
        a mapping keyed by header::

            table.col_alignment = 'c'
            table.col_alignment = ['l', 'r', 'c']
            table.col_alignment = {'Name': 'r'}
        """
        if value is None:
            self.__column_align = None
        elif isinstance(value, dict):
            self.__column_align = {
                header: self.__checked_alignment(align, 'col_alignment')
                for header, align in value.items()
            }
        elif is_some_instance(value, list, tuple):
            self.__column_align = [
                self.__checked_alignment(align, 'col_alignment')
                for align in value
            ]
        else:
            self.__column_align = self.__checked_alignment(
                value, 'col_alignment'
            )

    @leading_zeros.setter
    def leading_zeros(self, value):
        if value is None:
            self.__leading_zeros = None
            return
        value = int(value)
        if value < 0:
            raise ValueError('leading_zeros must be >= 0 or None')
        self.__leading_zeros = value or None

    @float_format.setter
    def float_format(self, value):
        self.__float_format = value

    @int_format.setter
    def int_format(self, value):
        self.__int_format = value

    @custom_format.setter
    def custom_format(self, value):
        self.__custom_format = value

    @column_min_width.setter
    def column_min_width(self, value):
        self.__column_min_width = value

    @column_max_width.setter
    def column_max_width(self, value):
        self.__column_max_width = value

    @header_align.setter
    def header_align(self, value):
        if value is None:
            self.__header_align = None
        elif isinstance(value, dict):
            self.__header_align = {
                header: self.__checked_alignment(align, 'header_align')
                for header, align in value.items()
            }
        elif is_some_instance(value, list, tuple):
            self.__header_align = [
                self.__checked_alignment(align, 'header_align')
                for align in value
            ]
        else:
            self.__header_align = self.__checked_alignment(
                value, 'header_align'
            )

    @title.setter
    def title(self, value):
        self.__title = None if value is None else str(value)

    @caption.setter
    def caption(self, value):
        self.__caption = None if value is None else str(value)

    @zebra.setter
    def zebra(self, value):
        self.__zebra = value

    @row_stripe.setter
    def row_stripe(self, value):
        self.__zebra = value

    @footer_rows.setter
    def footer_rows(self, value):
        value = int(value or 0)
        if value < 0:
            raise ValueError('footer_rows must be >= 0')
        self.__footer_rows = value

    @footer_color.setter
    def footer_color(self, value):
        self.__footer_color = value

    @cell_colors.setter
    def cell_colors(self, value):
        if not value:
            self.__cell_colors = {}
            return
        cleaned = {}
        for key, spec in dict(value).items():
            if not (isinstance(key, tuple) and len(key) == 2):
                raise TypeError(
                    'cell_colors keys must be (row, column) tuples, got {0!r}'
                    .format(key)
                )
            cleaned[(int(key[0]), key[1])] = spec
        self.__cell_colors = cleaned

    @cell_padding.setter
    def cell_padding(self, value):
        if value is None:
            self.__cell_padding = None
            return
        value = int(value)
        if value < 0:
            raise ValueError('cell_padding must be >= 0 or None')
        self.__cell_padding = value

    @overflow.setter
    def overflow(self, value):
        if value is None:
            self.__overflow = None
            return
        value = str(value).lower()
        if value not in ('wrap', 'truncate', 'ellipsis'):
            raise ValueError(
                "overflow must be 'wrap', 'truncate', 'ellipsis', or None"
            )
        # ellipsis is truncate with the default trimming sign
        self.__overflow = 'truncate' if value == 'ellipsis' else value
        self.__auto_wrap_table = self.__overflow == 'wrap'

    @valign.setter
    def valign(self, value):
        from .cells import _normalize_valign
        self.__valign = _normalize_valign(value)

    @col_valign.setter
    def col_valign(self, value):
        if value is None:
            self.__col_valign = None
            return
        from .cells import _normalize_valign
        if isinstance(value, dict):
            self.__col_valign = {
                key: _normalize_valign(code) for key, code in value.items()
            }
        elif is_some_instance(value, list, tuple):
            self.__col_valign = [_normalize_valign(code) for code in value]
        else:
            self.__col_valign = _normalize_valign(value)

    @cell_valign.setter
    def cell_valign(self, value):
        if value is None:
            self.__cell_valign = {}
            return
        if not isinstance(value, dict):
            raise TypeError('cell_valign must be a dict of (row, col) -> code')
        from .cells import _normalize_valign
        self.__cell_valign = {
            key: _normalize_valign(code) for key, code in value.items()
        }

    @panel.setter
    def panel(self, value):
        if value is None or value is False:
            self.__panel = False
            return
        if value is True:
            self.__panel = True
            return
        # Named box style: store the string so the renderer can pick glyphs.
        self.__panel = str(value)

    @shadow.setter
    def shadow(self, value):
        if value is None or value is False:
            self.__shadow = False
            return
        if value is True:
            self.__shadow = True
            return
        # Custom shadow glyph (one visible character preferred).
        self.__shadow = str(value) if str(value) else True

    @sort_by.setter
    def sort_by(self, value):
        self.__sort_by = value

    @sort_reverse.setter
    def sort_reverse(self, value):
        self.__sort_reverse = bool(value)

    @row_filter.setter
    def row_filter(self, value):
        if value is not None and not callable(value):
            raise TypeError('row_filter must be callable or None')
        self.__row_filter = value

    @expand_to_window.setter
    def expand_to_window(self, value):
        self.__expand_to_window = bool(value)

    def add_divider(self, after_row=None):
        """
        Draw a horizontal rule after a data row.

        ``after_row`` is a 0-based index into the stored rows. Omit it to
        place the rule after the last row currently present. Styles that
        already separate every row still accept the call; styles without
        inter-row rules gain one at the chosen position.
        """
        if after_row is None:
            if self.__real_row_count == 0:
                return
            after_row = self.__real_row_count - 1
        after_row = int(after_row)
        if after_row < 0:
            raise ValueError('after_row must be >= 0')
        self.__dividers.add(after_row)

    def add_dividers(self, *indexes):
        """
        Place several horizontal rules at once.

        Each argument is a 0-based ``after_row`` index (same as
        :meth:`add_divider`). A single iterable argument is also accepted.
        """
        if len(indexes) == 1 and not isinstance(indexes[0], (int, bool)):
            try:
                indexes = tuple(indexes[0])
            except TypeError:
                pass
        for index in indexes:
            self.add_divider(index)

    def divide_every(self, n, start=0):
        """
        Insert a divider after every ``n`` body rows, starting at ``start``.

        Example: ``divide_every(3)`` rules after rows 2, 5, 8, …
        """
        n = int(n)
        start = int(start)
        if n < 1:
            raise ValueError('n must be >= 1')
        if start < 0:
            raise ValueError('start must be >= 0')
        # First divider after row (start + n - 1).
        first = start + n - 1
        for after in range(first, self.__real_row_count, n):
            self.__dividers.add(after)

    def clear_dividers(self):
        """Remove every divider placed with :meth:`add_divider`."""
        self.__dividers.clear()
        
    @show_index.setter
    def show_index(self, value: bool):
        self.__show_index = bool(value)
    
    @index_start.setter
    def index_start(self, value: int):
        try:
            self.__i_start = int(value)
        except ValueError:
            self.__i_start = 0
    
    @index_step.setter
    def index_step(self, value: int):
        try:
            self.__i_step = int(value)
        except ValueError:
            self.__i_step = 1

    @index_title.setter
    def index_title(self, value):
        label = I_COL_TIT if value is None else str(value)
        new_title = IndexColumnTitle(label)
        old_title = self.__index_title
        if new_title is old_title:
            return
        for mapping in (
            self.__columns_with_i,
            self.__cell_types_with_i,
            self.__column_types_with_i,
            self.__column_alignments_with_i,
            self.__column_widths_with_i,
            self.__float_columns_widths_with_i,
            self.__processed_columns_with_i,
            self.__semi_processed_columns_with_i,
        ):
            if old_title in mapping:
                mapping[new_title] = mapping.pop(old_title)
        if self.__headers_with_i and self.__headers_with_i[0] is old_title:
            self.__headers_with_i[0] = new_title
        self.__index_title = new_title

    @roman_index.setter
    def roman_index(self, value: bool):
        self.__roman_index = bool(value)

    @number_columns.setter
    def number_columns(self, value: bool):
        self.__number_columns = bool(value)

    @strip_cells.setter
    def strip_cells(self, value: bool):
        self.__strip_cells = bool(value)

    @hrules.setter
    def hrules(self, value):
        if value is None or value is False:
            self.__hrules = None
            return
        if value is True:
            self.__hrules = 'all'
            return
        mode = str(value).lower()
        aliases = {
            'all': 'all', 'a': 'all',
            'frame': 'frame', 'f': 'frame',
            'header': 'header', 'h': 'header',
            'none': 'none', 'n': 'none', 'off': 'none',
        }
        if mode not in aliases:
            raise ValueError(
                "hrules must be 'all', 'frame', 'header', or 'none', got {0!r}"
                .format(value)
            )
        self.__hrules = aliases[mode]

    @vrules.setter
    def vrules(self, value):
        if value is None or value is False:
            self.__vrules = None
            return
        if value is True:
            self.__vrules = 'all'
            return
        mode = str(value).lower()
        aliases = {
            'all': 'all', 'a': 'all',
            'frame': 'frame', 'f': 'frame',
            'none': 'none', 'n': 'none', 'off': 'none',
        }
        if mode not in aliases:
            raise ValueError(
                "vrules must be 'all', 'frame', or 'none', got {0!r}"
                .format(value)
            )
        self.__vrules = aliases[mode]

    @max_table_width.setter
    def max_table_width(self, value):
        self.max_width = value

    @justify.setter
    def justify(self, value):
        self.table_align = value

    @suppress_empty.setter
    def suppress_empty(self, value):
        show = not bool(value)
        self.__show_empty_rows = show
        self.__show_empty_columns = show

    def fit_terminal(self, margin=0):
        """
        Set ``max_width`` to the current terminal width minus ``margin``.

        Returns ``self`` for chaining. Equivalent in spirit to comfy-table /
        tty-table "fit the window" helpers; ``max_width=None`` already tracks
        the live terminal, but this pins an explicit budget.
        """
        cols, _ = get_window_size()
        self.max_width = max(1, int(cols) - int(margin))
        return self
        
    @auto_wrap.setter
    def auto_wrap(self, value: bool):
        self.__auto_wrap_table = bool(value)
        if self.__overflow is not None:
            # Keep overflow in sync when callers flip the bool directly.
            self.__overflow = 'wrap' if self.__auto_wrap_table else 'truncate'

    # +----------------------+ SHOW SETTERS +------------------------+

    @show_headers.setter
    def show_headers(self, value: bool):
        self.__show_headers = bool(value)

    @show_margin.setter
    def show_margin(self, value: bool):
        self.__show_margin = bool(value)

    @show_empty_rows.setter
    def show_empty_rows(self, value: bool):
        self.__show_empty_rows = bool(value)

    @show_empty_columns.setter
    def show_empty_columns(self, value: bool):
        self.__show_empty_columns = value

    @property
    def hide_columns(self):
        """
        Column names or indexes to omit from display (go-pretty suppress).

        Accepts ``None``, a single name/index, or an iterable of them.
        Stored data is unchanged; only compose/export chrome hides them.
        """
        return self.__hide_columns

    @hide_columns.setter
    def hide_columns(self, value):
        if value is None:
            self.__hide_columns = ()
            return
        if isinstance(value, (str, bytes)) or not hasattr(value, '__iter__'):
            value = (value,)
        self.__hide_columns = tuple(value)

    # end +-----------------------------+ SETTERS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+


    # +-----------------------------------------------------------------------------+
    # start +---------------------+ PRIVATE PROPERTIES +----------------------+ start

    @property
    def __style_composition(self) -> TableComposition:
        """
        Gets the style composition using a checked name.

        ``cell_padding`` overrides the style's per-side margin; ``show_margin``
        False forces margin 0 when no explicit padding is set. ``hrules`` /
        ``vrules`` optionally thin out horizontal / vertical separators
        (PrettyTable-style) without changing the named style.
        """
        base = style_catalogue.__getattribute__(self.__checked_style_name)
        if self.__cell_padding is not None:
            margin = max(0, int(self.__cell_padding))
        elif not self.__show_margin:
            margin = 0
        else:
            margin = base.margin
        replacements = {}
        if margin != base.margin:
            replacements['margin'] = margin
        hrules = self.__hrules
        if hrules is not None and hrules != 'all':
            replacements.update(self.__hrules_replacements(base, hrules))
        vrules = self.__vrules
        if vrules is not None and vrules != 'all':
            replacements.update(self.__vrules_replacements(base, vrules))
        if not replacements:
            return base
        return base._replace(**replacements)

    @staticmethod
    def __hrules_replacements(base, mode):
        """Map hrules mode -> TableComposition field overrides."""
        mode = str(mode).lower()
        none = {
            'superior_header_line': None,
            'inferior_header_line': None,
            'superior_header_line_no_header': None,
            'table_body_line': None,
            'table_end_line': None,
        }
        if mode in ('none', 'n', 'off', 'false', '0'):
            return none
        if mode in ('frame', 'f'):
            # Top + bottom only; drop body separators and header underline.
            return {
                'inferior_header_line': None,
                'table_body_line': None,
            }
        if mode in ('header', 'h'):
            # Keep only the header underline (and top/bottom frame if present).
            return {
                'table_body_line': None,
            }
        raise ValueError(
            "hrules must be 'all', 'frame', 'header', or 'none', got {0!r}"
            .format(mode)
        )

    @staticmethod
    def __vrules_replacements(base, mode):
        """Map vrules mode -> vertical SeparatorLine overrides."""
        mode = str(mode).lower()
        invisible = SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)

        def drop_intersections(sep):
            """Horizontal rule without column junctions (vrules none/frame)."""
            if sep is None:
                return None
            # Keep the fill character; blank the junction so no leftover ┬/┼.
            fill = sep.middle if sep.middle not in (None, '') else INVISIBLE_SEPARATOR
            return SeparatorLine(sep.left, fill, fill, sep.right)

        if mode in ('none', 'n', 'off', 'false', '0'):
            return {
                'vertical_header_lines': invisible,
                'vertical_table_body_lines': invisible,
                'superior_header_line': drop_intersections(base.superior_header_line),
                'inferior_header_line': drop_intersections(base.inferior_header_line),
                'superior_header_line_no_header': drop_intersections(
                    base.superior_header_line_no_header
                ),
                'table_body_line': drop_intersections(base.table_body_line),
                'table_end_line': drop_intersections(base.table_end_line),
            }
        if mode in ('frame', 'f'):
            def frame_only(sep):
                if sep is None:
                    return SeparatorLine(None, INVISIBLE_SEPARATOR, None, None)
                return SeparatorLine(
                    sep.left, INVISIBLE_SEPARATOR, None, sep.right
                )
            return {
                'vertical_header_lines': frame_only(base.vertical_header_lines),
                'vertical_table_body_lines': frame_only(
                    base.vertical_table_body_lines
                ),
                'superior_header_line': drop_intersections(base.superior_header_line),
                'inferior_header_line': drop_intersections(base.inferior_header_line),
                'superior_header_line_no_header': drop_intersections(
                    base.superior_header_line_no_header
                ),
                'table_body_line': drop_intersections(base.table_body_line),
                'table_end_line': drop_intersections(base.table_end_line),
            }
        raise ValueError(
            "vrules must be 'all', 'frame', or 'none', got {0!r}".format(mode)
        )

    @property
    def __checked_style_name(self) -> str:
        """
        Returns the used style name if it exists, 
        otherwise the default style name.
        """
        if self.__style_name in self.__possible_styles:
            return self.__style_name
        else:
            return DEFAULT_STYLE

    @property
    def __empty_row_indexes(self) -> list:
        """
        Indexes of the rows that hold nothing at all.

        A row is empty when every cell in it is empty, by the same standard
        the column check applies -- the padding placeholder, ``None``, or the
        empty string. Counting only the placeholder, as this did, meant a row
        the caller typed as ``['', '']`` stayed on screen while a column typed
        the same way disappeared, which is the asymmetry issue #9 was about.
        """
        empty_rows = []
        for i, row in enumerate(self.__rows):
            if all(is_empty_cell(cell, self.__value_placer) for cell in row):
                empty_rows.append(i)
        return empty_rows

    def __user_hidden_column_indexes(self, table_with_i=False):
        """
        Resolve ``hide_columns`` keys to drawn column indexes.

        Names match headers; ints are 0-based user column indexes (index
        column excluded). When ``table_with_i`` the drawn index column is
        offset by one, matching ``__empty_column_indexes``.
        """
        keys = self.__hide_columns or ()
        if not keys:
            return ()
        headers = list(self.__headers)
        resolved = []
        for key in keys:
            if isinstance(key, int):
                user_i = key
            else:
                try:
                    user_i = headers.index(key)
                except ValueError:
                    raise ValueError(
                        'hide_columns key {0!r} is not in the table headers'
                        .format(key)
                    )
            if user_i < 0 or user_i >= len(headers):
                raise ValueError(
                    'hide_columns index {0!r} out of range'.format(key)
                )
            drawn = user_i + 1 if table_with_i else user_i
            resolved.append(drawn)
        return tuple(resolved)

    def __effective_hidden_columns(self, table_with_i=False):
        """Empty-column hides plus user ``hide_columns``, as drawn indexes."""
        hidden = set(self.__user_hidden_column_indexes(table_with_i))
        if not self.__show_empty_columns:
            hidden.update(self.__empty_column_indexes)
        return tuple(sorted(hidden))

    @property
    def __empty_column_indexes(self) -> list:
        """
        Search for empty columns using the column types.
        
        A ``NoneType`` is considered empty.
        """
        none_type_columns = []
        for i, type_name in enumerate(self.__column_types_as_list):
            if type_name == TYPE_NAMES.none_type_:
                if self.__show_index:
                    none_type_columns.append(i + 1)
                else:
                    none_type_columns.append(i)
        return none_type_columns

    @property
    def __possible_styles(self) -> tuple:
        """
        The names of all the implemented styles.
        """
        return style_catalogue._fields

    @property
    def __row_count(self) -> int:
        """
        Returns the number of rows. 
        
        Affected by the ``show_empty_rows`` property.
        """
        checked_real_row_count = self.__real_row_count
        if self.__show_empty_rows:
            return checked_real_row_count
        else:
            updated_row_count = sum([
                checked_real_row_count,
                -len(self.__empty_row_indexes)
            ])
            return updated_row_count

    @property
    def __column_count(self) -> int:
        """
        Returns the number of columns.
        
        Affected by the ``show_empty_columns`` property.
        """
        if self.__show_empty_columns:
            return self.__checked_real_column_count
        else:
            updated_column_count = sum([
                self.__checked_real_column_count,
                -len(self.__empty_column_indexes)
            ])
            return updated_column_count
        
    @property
    def __checked_real_column_count(self) -> int:
        """
        Adds one to the real column count if the index 
        column is shown.
        """
        if self.__show_index:
            return self.__real_column_count + 1
        else:
            return self.__real_column_count
                
    # end +-----------------------+ PRIVATE PROPERTIES +------------------------+ end
    # +-----------------------------------------------------------------------------+


    # +-----------------------------------------------------------------------------+
    # start +------------------------+ COLUMN ADDING +------------------------+ start

    @property
    def parse_str_numbers(self):
        """
        Whether text that looks numeric is treated as a number.

        Off by default, which keeps '007' and '1.50' exactly as written.
        Turned on, a column of '12', '3.5', 'True' is recognised as numeric or
        boolean and aligned accordingly, instead of being left-aligned as
        text. This is what makes data arriving from CSV, HTML or any other
        text format line up.

        Setting it re-examines data already added, so the order of the two
        statements does not matter.

        The conversion is deliberately strict -- no leading '+', no
        whitespace, no thousands separators -- so identifiers like '007' or
        version strings like '1.2.3' survive. Note that it does normalise the
        representation: '1.50' becomes 1.5. Where the exact text matters more
        than the alignment, leave this off.
        """
        return self.__parse_str_numbers

    @parse_str_numbers.setter
    def parse_str_numbers(self, value):
        self.__parse_str_numbers = bool(value)
        if self.__parse_str_numbers:
            self.__reparse_stored_strings()

    def __reparse_stored_strings(self):
        """
        Convert numeric-looking strings already stored into numbers.

        Both orientations hold the same data and both are read during
        rendering, so both have to be updated or the table would disagree with
        itself about the type of a column.
        """
        from .readers import parse_value

        for store in (self.__columns, self.__columns_with_i):
            for column in store.values():
                for index, cell in enumerate(column):
                    if isinstance(cell, str):
                        column[index] = parse_value(cell, True)
        for rows in (self.__rows, self.__rows_with_i):
            for row in rows:
                for index, cell in enumerate(row):
                    if isinstance(cell, str):
                        row[index] = parse_value(cell, True)

    @property
    def missing(self):
        """
        The sentinel value that marks a cell as absent.

        A cell holding this renders as ``missing_value`` and does not affect
        the column's inferred type, so a numeric column with gaps stays
        numeric and stays right-aligned. Assigning None or '' instead would
        make the column textual.

        Used by the readers to represent NaN and NULL, and available for
        building tables with gaps by hand::

            table.add_column('temp', [3.5, table.missing, 22.0])

        The sentinel is compared by identity and is per-table, so use the one
        belonging to the table you are filling.
        """
        return self.__value_placer

    # +------------------------+ FITTING +--------------------------+

    @property
    def max_width(self):
        """
        Width the table must fit into, or None to use the terminal width.

        Setting this makes rendering independent of the terminal, which is
        what you want when composing to a file or a fixed-width report.
        """
        return self.__max_width

    @max_width.setter
    def max_width(self, value):
        if value is not None and value < 1:
            raise ValueError('max_width must be positive or None')
        self.__max_width = value

    @property
    def too_narrow_message(self):
        """
        Text shown instead of the table when it cannot fit legibly.

        A table squeezed far below the width of its own data wraps every cell
        to a couple of characters and becomes unreadable. Setting a message
        says so plainly instead. None, the default, renders the table anyway.

        The message may use ``{needed}`` and ``{available}`` placeholders::

            table.too_narrow_message = (
                'Table needs {needed} columns, terminal has {available}.'
            )
        """
        return self.__too_narrow_message

    @too_narrow_message.setter
    def too_narrow_message(self, value):
        self.__too_narrow_message = value

    def __available_width(self) -> int:
        """Width the table has to fit into."""
        if self.__max_width is not None:
            return self.__max_width
        console_columns, _ = get_window_size()
        return console_columns

    def __minimum_table_width(self) -> int:
        """
        Narrowest the table could possibly be rendered.

        Every column shrunk to MIN_COLUMN_SIZE, plus the margins and the
        vertical separators the current style draws between them. Below this
        the table cannot be produced legibly at all.
        """
        column_count = (
            self.internal_column_count if self.__show_index
            else self.column_count
        )
        if column_count == 0:
            return 0
        composition = self.__style_composition
        margins = (CELL_MARGIN * 2) if composition.margin else 0
        body_lines = composition.vertical_table_body_lines
        separator_count = sum(
            1 for part in (body_lines.left, body_lines.right) if part is not None
        )
        if body_lines.middle is not None:
            separator_count += column_count - 1
        return column_count * (MIN_COLUMN_SIZE + margins) + separator_count

    # +----------------------+ MERGED CELLS +-----------------------+

    @property
    def merged_regions(self) -> list:
        """The merges in place, as a list of ``MergedRegion``."""
        return list(self.__merged_regions)

    def merge_cells(self, first_row, first_column, last_row=None,
                    last_column=None, value=None, align='c', color=None):
        """
        Render a rectangular block of cells as a single cell.

        Coordinates are inclusive and zero-based, and ignore the index column
        even when it is displayed. Omitting ``last_row`` or ``last_column``
        leaves that axis unmerged, so a merge can run across columns, down
        rows, or both::

            table.merge_cells(0, 0, last_column=2)        # across three columns
            table.merge_cells(1, 0, last_row=3)           # down four rows
            table.merge_cells(0, 0, 2, 2, value='Total')  # a 3x3 block
            table.merge_cells(0, 0, last_row=2, value='A',
                              color='black on green')    # coloured merge

        ``value`` replaces the text; left as None, the top-left cell's own
        content is kept. ``align`` is 'l', 'r' or 'c' within the merged span.
        ``color`` paints the whole merge span (text + padding + blank lines)
        with a colour spec; when omitted, the top-left cell's row/column/
        cell colour is inherited at render time so existing colour APIs light
        up merges without an extra argument.

        Raises ValueError for a merge covering a single cell, coordinates
        outside the table, or an overlap with a merge already in place.

        A merge never widens the table: the columns are still sized by their
        unmerged content, so text longer than the span it is given is
        truncated. Widen the columns, or shorten the text.
        """
        from .merges import normalise

        if last_row is None:
            last_row = first_row
        if last_column is None:
            last_column = first_column

        region = normalise(
            first_row, first_column, last_row, last_column, value, align,
            self.row_count, self.column_count, self.__merged_regions,
            color=color,
        )
        self.__merged_regions.append(region)
        return region

    def unmerge_all(self):
        """Remove every merge."""
        self.__merged_regions = []

    # +------------------------+ COLOUR +---------------------------+

    @property
    def header_color(self):
        """
        Colour applied to the header row.

        Accepts a name, a 256-colour index, a hex triple, or a combination:
        'cyan', 'bold yellow', '#ff8800', 'color:93', 'black on white'.
        """
        return self.__header_color

    @header_color.setter
    def header_color(self, value):
        self.__header_color = value

    @property
    def border_color(self):
        """Colour applied to every border character."""
        return self.__border_color

    @border_color.setter
    def border_color(self, value):
        self.__border_color = value

    def border_text(self, text, where='top', color=None, offset=None, align='left'):
        """
        Overlay ``text`` on a border line (inspired by tabled ``LineText``).

        ``where`` selects the target rule or vertical::

            'top' / 'superior_header'     – top frame
            'header' / 'header_rule'      – rule under the header
            'body' / 'body_rule'          – inter-row body rules
            'bottom' / 'end'              – bottom frame
            'left' / 'right'              – vertical outer borders

        ``align`` is ``left``, ``center`` or ``right`` (``l``/``c``/``r``).
        On the vertical borders ``left`` means top and ``right`` means bottom.

        ``offset`` is a margin measured from the aligned edge, in visible
        columns (horizontal) or lines (vertical):

        - ``align='left'``: the text starts ``offset`` columns from the left
          edge (the historical meaning; ``offset=0`` overwrites the corner).
        - ``align='right'``: the text ends ``offset`` columns before the
          right edge.
        - ``align='center'``: the text is centred between margins of
          ``offset`` on both sides.

        ``offset=None`` (the default) is automatic: a margin of 1, so the
        label sits just inside the frame corners and never overwrites them.
        ``table.border_text('v2', align='right')`` therefore works without
        any offset. Junctions outside the text are preserved. ``color`` paints
        the text foreground (``border_color`` still paints the remaining
        chrome).

        Multiple calls accumulate; use ``clear_border_texts()`` to reset.
        """
        where_key = str(where).strip().lower()
        aliases = {
            'top': 'top',
            'superior': 'top',
            'superior_header': 'top',
            'header': 'header',
            'header_rule': 'header',
            'inferior_header': 'header',
            'body': 'body',
            'body_rule': 'body',
            'table_body': 'body',
            'bottom': 'bottom',
            'end': 'bottom',
            'table_end': 'bottom',
            'left': 'left',
            'right': 'right',
        }
        if where_key not in aliases:
            raise ValueError(
                f"Unknown border_text where={where!r}; "
                f"expected one of {sorted(set(aliases.values()))}"
            )
        align_key = (align or 'left').lower()
        if align_key not in ('left', 'center', 'right', 'l', 'c', 'r'):
            raise ValueError(f"Unknown border_text align={align!r}")
        if offset is not None:
            try:
                offset = int(offset)
            except (TypeError, ValueError):
                raise TypeError(
                    f"border_text offset must be an int or None, got {offset!r}"
                ) from None
            if offset < 0:
                raise ValueError(
                    f"border_text offset must be >= 0, got {offset!r}"
                )
        align_key = {'l': 'left', 'c': 'center', 'r': 'right'}.get(
            align_key, align_key
        )
        self.__border_texts.append({
            'text': '' if text is None else str(text),
            'where': aliases[where_key],
            'color': color,
            'offset': offset,
            'align': align_key,
        })
        return self

    def clear_border_texts(self):
        """Remove every overlay registered with ``border_text``."""
        self.__border_texts = []
        return self

    @property
    def column_colors(self) -> dict:
        """
        Colour per column, keyed by header name::

            table.column_colors = {'Status': 'green', 'Errors': 'bold red'}
        """
        return self.__column_colors

    @column_colors.setter
    def column_colors(self, value: dict):
        self.__column_colors = dict(value) if value else {}

    @property
    def row_colors(self) -> dict:
        """
        Colour per row, keyed by row index::

            table.row_colors = {0: 'dim', 3: 'bold'}
        """
        return self.__row_colors

    @row_colors.setter
    def row_colors(self, value):
        if value is None:
            self.__row_colors = {}
        elif isinstance(value, dict):
            self.__row_colors = dict(value)
        else:
            # A bare sequence is taken as colours for consecutive rows.
            self.__row_colors = {i: c for i, c in enumerate(value)}

    @property
    def color_rule(self):
        """
        A callable deciding the colour of individual cells.

        Called as ``rule(value, row_index, column_name)`` and returning a
        colour spec, or None to leave the cell alone. It takes precedence over
        ``row_colors`` and ``column_colors``::

            table.color_rule = lambda v, r, c: 'red' if c == 'Delta' and v < 0 else None

        The callable receives the original value, before it is turned into a
        string, so numeric comparisons work directly.
        """
        return self.__color_rule

    @color_rule.setter
    def color_rule(self, value):
        if value is not None and not callable(value):
            raise TypeError('color_rule must be callable or None')
        self.__color_rule = value

    @property
    def use_colors(self):
        """
        Whether to emit colour: True, False, or None to decide automatically.

        Automatic means colour is emitted only when standard output is a
        terminal, and never when NO_COLOR is set. Because ``compose()`` returns
        a string that the caller may send anywhere, this errs toward not
        embedding escape sequences in something destined for a file.
        """
        return self.__use_colors

    @use_colors.setter
    def use_colors(self, value):
        self.__use_colors = value

    @property
    def __colors_active(self) -> bool:
        """Resolve the colour decision for this render."""
        if self.__use_colors is None:
            return supports_color()
        return bool(self.__use_colors)

    def __color_for_cell(self, value, row_index: int, column_name: str,
                         column_index: int = None):
        """
        Colour of a single cell, or None.

        Precedence: ``color_rule``, then ``cell_colors``, then ``row_colors``,
        then footer colour, then zebra stripe, then ``column_colors``.
        """
        if self.__color_rule is not None:
            decided = self.__color_rule(value, row_index, column_name)
            if decided:
                return decided
        cell_spec = self.__lookup_cell_color(row_index, column_name, column_index)
        if cell_spec:
            return cell_spec
        if row_index in self.__row_colors:
            return self.__row_colors[row_index]
        footer_spec = self.__footer_color_for_row(row_index)
        if footer_spec:
            return footer_spec
        zebra_spec = self.__zebra_color_for_row(row_index)
        if zebra_spec:
            return zebra_spec
        return self.__column_colors.get(column_name)

    def __lookup_cell_color(self, row_index, column_name, column_index):
        """Resolve ``cell_colors`` keyed by (row, header) or (row, col index)."""
        if not self.__cell_colors:
            return None
        for key in (
            (row_index, column_name),
            (row_index, column_index) if column_index is not None else None,
        ):
            if key is not None and key in self.__cell_colors:
                return self.__cell_colors[key]
        return None

    def __footer_color_for_row(self, row_index: int):
        """Colour for rows in the trailing footer band, if configured."""
        if not self.__footer_color or self.__footer_rows <= 0:
            return None
        # Body length for the current paint pass is stored when known;
        # fall back to internal row count.
        body_len = getattr(self, "_paint_body_len", None)
        if body_len is None:
            body_len = self.__real_row_count
        if body_len <= 0:
            return None
        threshold = body_len - int(self.__footer_rows)
        if row_index >= threshold:
            return self.__footer_color
        return None

    def __zebra_color_for_row(self, row_index: int):
        """Even/odd body stripe from ``zebra`` / ``row_stripe``."""
        if not self.__zebra:
            return None
        # Footer rows keep footer_color (already handled); still allow zebra
        # on non-footer rows.
        if isinstance(self.__zebra, (list, tuple)) and len(self.__zebra) >= 2:
            even_spec, odd_spec = self.__zebra[0], self.__zebra[1]
        else:
            even_spec, odd_spec = None, self.__zebra
        return odd_spec if (row_index % 2) else even_spec

    def __has_any_color(self) -> bool:
        """True if anything at all was configured to be coloured."""
        return bool(
            self.__header_color
            or self.__border_color
            or self.__column_colors
            or self.__row_colors
            or self.__color_rule
            or self.__zebra
            or self.__footer_color
            or self.__cell_colors
            or any(getattr(r, 'color', None) for r in self.__merged_regions)
        )

    @staticmethod
    def __paint_one(cell, spec):
        """
        Colour a single aligned cell, which may be wrapped into several lines.

        A wrapped cell arrives as a tuple of sub-rows; each is coloured
        separately so the sequence opens and closes within one physical line
        and cannot bleed across the row.
        """
        if is_some_instance(cell, list, tuple):
            return tuple(colorize(str(part), spec) for part in cell)
        return colorize(str(cell), spec)

    def __paint_header(self, header_cells, spec):
        """Colour every header cell. One cell per column."""
        return [self.__paint_one(cell, spec) for cell in header_cells]

    def __paint_cells(self, columns, color_of):
        """
        Colour body cells, consulting ``color_of(column_index, row_index)``.

        Cells whose colour resolves to None are left untouched, so a table with
        one coloured column pays nothing on the others.
        """
        painted = []
        for column_i, column in enumerate(columns):
            cells = []
            for row_i, cell in enumerate(column):
                spec = color_of(column_i, row_i)
                cells.append(self.__paint_one(cell, spec) if spec else cell)
            painted.append(tuple(cells))
        return painted

    def __raw_value_at(self, column_titles, column_i, row_i):
        """
        The original, unformatted value of a cell, for ``color_rule``.

        Handing the rule the padded string would make numeric comparisons
        impossible, so the value is looked up from the stored data instead.
        Returns None when no rule is set, to skip the lookup entirely.
        """
        if self.__color_rule is None:
            return None
        try:
            title = column_titles[column_i]
        except IndexError:
            return None
        source = self.__columns_with_i if self.__show_index else self.__columns
        try:
            return source[title][row_i]
        except (KeyError, IndexError):
            return None

    # +------------------------+ COLUMNS +---------------------------+

    def add_column(self,
                   header=None, 
                   data: Union[list, tuple]=None
                  ) -> None:
        """
        Add a column to the table.
        Can be left empty to add an empty column.

        ``header``: The title of the column. If not provided, 
        gets filled with a generic name.
        
        ``data``: Data provided in a list. If not 
        provided, column gets filled with the missing value.
        The Table class adjusts the columns when one or more
        are smaller or larger.
        
        Example::
        
            table = Table()
            table.add_column('Name', ['John', 'Jane'])
            table.add_column('Age', [20])
            table.add_column('Height', [1.75, 1.60, 1.75])
            table.add_column()
            table.missing_value = '?'
            
        Results in:
        
        >>> +--------------------------------+
        ... | Name   Age   Height   column 4 |
        ... +======+=====+========+==========+
        ... | John |  20 |   1.75 | ?        |
        ... | Jane |   ? |   1.6  | ?        |
        ... | ?    |   ? |   1.75 | ?        |
        ... +------+-----+--------+----------+
        
        """
        checked_header = self.__check_header(header)
        # Asked before the header is added, and remembered. The second test
        # used to be written out again after ``__add_header`` had already put
        # the name in the list, so it was never true and the padding step
        # below never ran: a column shorter than the table stayed short.
        # Nothing noticed until a later ``add_row`` padded it -- from the
        # top, which is right for a column that row had just created and
        # wrong for this one, and its values came out shifted down by one.
        is_new_column = checked_header not in self.__headers
        if is_new_column:
            self.__add_header(checked_header)
        self.__add_column_data(
            data=data,
            column_header=checked_header
        )
        if is_new_column:
            self.__adjust_columns_to_row_count()
        self.__check_existent_rows_vs_row_count()
        self.__transpose_column_to_rows(data)
        self.__adjust_rows_to_column_count(
            there_are_headers_to_add=False, 
            count_of_new_headers=1, 
            columns_added_before=True
        )
        
    def __get_auto_header(self) -> str:
        """
        Returns a generic name for a column.
        """
        return f'{self.__generic_column_name} {len(self.__headers) + 1}'
    
    def __name_duplicated_header(self, header: str) -> str:
        """
        Returns a name for a column if the name is already in use.
        """
        return f'{header} {self.__headers.count(header) + 1}'
        
    def __process_header(self, header: str) -> str:
        """
        Checks if header is None.
        
        If it is, will be replaced with a generic name.
        
        If the header already exists, a number matching
        the column count (starting from 1) will be added.
        """
        if header is None:
            checked = self.__get_auto_header()
        else:
            checked = str(header)
            if checked in self.__headers:
                checked = self.__name_duplicated_header(checked)
        
        return checked
    
    def __add_header(self, checked_header: str) -> None:
        self.__headers.append(checked_header)
        self.__headers_with_i.append(checked_header)
        self.__column_widths[checked_header] = 0
        self.__column_types[checked_header] = None
        self.__column_alignments[checked_header] = ''
        self.__cell_types[checked_header] = []
        self.__columns[checked_header] = []
        self.__columns_with_i[checked_header] = []
    
    def __check_add_header_on_init(self, header: str) -> str:
        checked_header = self.__process_header(header)
        self.__add_header(checked_header)
        
        return checked_header

    def  __check_header(self, header: Union[str, None]) -> str:
        """
        The header a new column should take.

        A column added after rows that were wider than the named headers
        claims the automatic name already standing in that position, rather
        than adding a name beside it. Anything else gets a name of its own.

        Only an unnamed column claims one. A caller who passed a name asked
        for that name, and handing them somebody else's header instead threw
        their data into an existing column: ``add_column('a', [])`` followed
        by ``add_column('b', [])`` produced a single column called 'a',
        because with no rows yet the comparison below read zero and matched
        the first header every time.
        """
        if header is not None:
            return self.__process_header(header)

        try:
            column_count_from_rows = len(self.__rows[0])
        except IndexError:
            column_count_from_rows = 0

        if column_count_from_rows < len(self.__headers):
            # A header was declared for this position and nothing has filled
            # it yet, so this column takes it.
            return self.__headers[column_count_from_rows]

        # The header gets checked here because the add_row method uses
        # __add_column_header too.
        return self.__process_header(header)
    

    def __add_column_data(self, data: Union[list, tuple], column_header: str) -> None:
        """
        Add the data of the column.
        """
        self.__real_column_count += 1
        if data is not None:
            if len(data) > self.__real_row_count:
                
            # If the new column is bigger than the existing columns,
            # add the difference to the real row count.
                difference = len(data) - self.__real_row_count
                self.__real_row_count += difference
                
                for _ in range(difference):
                    # Add index counter to the table with index.
                    # This table is used when the index is shown.
                    self.__columns_with_i[self.__index_title].append(self.__index_counter)

            # Add to the table with and without index
            self.__columns[column_header] += data
            self.__columns_with_i[column_header] += data
            

    def __adjust_columns_to_row_count(self, rows_added_before: bool=False) -> None:
        """
        Make all the columns the same size.
        
        The point of reference is ``__real_row_count`` because
        the height of a column is determined by how many rows
        it has.
        """
        for header, column_body in self.__columns.items():
            
            # Check if the new column is bigger than the existing columns.
            # Once again, the point of reference is __real_row_count.
            difference = self.__real_row_count - len(column_body)
            
            for _ in range(difference):
                if rows_added_before:
                    # If there is rows added already, use insert, to put the
                    # value placer before them.
                    self.__columns[header].insert(0, self.__value_placer) 
                    self.__columns_with_i[header].insert(0, self.__value_placer)
                else:
                    # If there is no rows added yet, use append.
                    self.__columns[header].append(self.__value_placer)
                    self.__columns_with_i[header].append(self.__value_placer)
            
    def __transpose_column_to_rows(self, data: Union[list, tuple]) -> None:
        """
        Pass the column to the rows list.
        """
        for row_i in range(self.__real_row_count):
            self.__distribute_column_to_rows(
                row_i,
                data
            )

    def __distribute_column_to_rows(self, row_i: int, data: Union[list, tuple]) -> None:
        """
        Grab values from the column to put in the row.
        """
        try:
            # Try to get the piece of data from the column.
            value_to_add = data[row_i]
        except (IndexError, TypeError):
            # If there is no data, use the missing value (value placer).
            value_to_add = self.__value_placer
        
        # Add the value to the row.
        self.__rows[row_i].append(value_to_add)
        self.__rows_with_i[row_i].append(value_to_add)
        
    # end +--------------------------+ COLUMN ADDING +--------------------------+ end
    # +-----------------------------------------------------------------------------+


    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ ROW ADDING +--------------------------+ start

    def add_row(self, data: Union[list, tuple]=None) -> None:
        """
        Add a row to the table. Can be left empty to add
        an empty row.

        ``data``: Data provided as any iterable.
        
        Example::
        
            table = Table()
            table.add_row(['size 1', 12.4325])
            table.add_row(['size 2', 111.22])
            table.add_row(['size 3', 0.4])
            table.add_row()
            table.add_row(['size 5', 39865])
            table.missing_value = '?'
        
        Results in:
        
        >>> +-----------------------+
        ... | column 1     column 2 |
        ... +==========+============+
        ... | size 1   |    12.4325 |
        ... | size 2   |   111.22   |
        ... | size 3   |     0.4    |
        ... | ?        |          ? |
        ... | size 5   | 39865      |
        ... +----------+------------+
        """
        self.__columns_with_i[self.__index_title].append(self.__index_counter)
        added_to_column_count = self.__add_row_data(data)
        add_headers = True if added_to_column_count is not None else False
        self.__adjust_rows_to_column_count(add_headers, added_to_column_count)
        self.__adjust_headers_to_data_length(data)
        self.__transpose_row_to_columns(data)
        self.__adjust_columns_to_row_count(rows_added_before=True)
        
    def __adjust_headers_to_data_length(self, data: Union[list, tuple]) -> None:
        if data is None:
            headers_to_add = 0
        else:
            headers_to_add = len(data) - len(self.__headers)
        for _ in range(headers_to_add):
            auto_named_header = self.__get_auto_header()
            self.__add_header(auto_named_header)
        
    def __add_row_data(self, data: Union[list, tuple]) -> Optional[int]:
        """
        Add the data of the new row.
        
        If data is ``None``, value placers are added.
        """
        # Create a new list in the rows list for the new row.
        self.__rows.append([])
        # For the index table, the new list gets added with an
        # index counter first (the index columns it's always first).
        self.__rows_with_i.append([self.__index_counter])
        
        self.__real_row_count += 1
        if data is None:
            # Add value placers if the row is empty.
            for _ in range(self.__checked_real_column_count):
                self.__rows[-1].append(self.__value_placer)
                self.__rows_with_i[-1].append(self.__value_placer)
        else:
            return self.__check_data_and_fill_last_row(data)

    def __adjust_rows_to_column_count(self, 
                                      there_are_headers_to_add: bool, 
                                      count_of_new_headers: int,
                                      columns_added_before: bool=False
                                     ) -> None:
        """
        Make all the rows the same size.
        
        The point of reference is ``__real_column_count`` because
        the width of a row is determined by how many columns
        has.
        """
        if there_are_headers_to_add:
            for _ in range(count_of_new_headers):
                auto_named_header = self.__get_auto_header()
                self.__add_header(auto_named_header)
        for row_i in range(self.__real_row_count):
            # Check if there is a difference between the column count
            # and the length of the new row (the length of the row is the
            # is how many columns it has).
            difference = self.__real_column_count - len(self.__rows[row_i])
            for _ in range(difference):
                if columns_added_before:
                    # If there is columns added already, use insert, to put the
                    # value placer before them.
                    self.__rows[row_i].insert(0, self.__value_placer)
                    self.__rows_with_i[row_i].insert(1, self.__value_placer)
                else:
                    # If there is no columns added yet, use append.
                    self.__rows[row_i].append(self.__value_placer)
                    self.__rows_with_i[row_i].append(self.__value_placer)

    def __transpose_row_to_columns(self, data: list) -> None:
        """
        Grab values from the row to put in the column.
        """
        for column_i in range(self.__checked_real_column_count):
            if data is None:
                self.__fil_column_from_empty_row(column_i)
            else:
                self.__fill_column_from_row(column_i, data)

    def __check_existent_rows_vs_row_count(self) -> None:
        """
        Check if the quantity of rows is less than the real count.
        
        If so, add the necessary rows (new lists).
        """
        if len(self.__rows) < self.__real_row_count:
            rows_to_add = self.__real_row_count - len(self.__rows)
            for _ in range(rows_to_add):
                # Single list for the table without index.
                self.__rows.append([])
                # Lis with index counter for the table with index.
                self.__rows_with_i.append([self.__index_counter])

    def __check_data_and_fill_last_row(self, data: list) -> Optional[int]:
        """
        Add the data to the rows.
        """
        added_columns_to_count = None
        if len(data) > self.__checked_real_column_count:
            if self.column_count < len(self.__headers):
                added_columns_to_count = 0
                self.__real_column_count += len(data) - self.column_count
            else:
                added_columns_to_count = len(data) - self.column_count
                self.__real_column_count += added_columns_to_count
        for column_i in range(self.__checked_real_column_count):
            try:
                self.__rows[-1].append(data[column_i])
                self.__rows_with_i[-1].append(data[column_i])
            except IndexError:
                self.__rows_with_i[-1].append(self.__value_placer)
        return added_columns_to_count

    def __fil_column_from_empty_row(self, column_i: int) -> None:
        """
        Put value placers on the column, because the row is empty.
        """
        try:
            self.__columns[self.__headers[column_i]].append(self.__value_placer)
            self.__columns_with_i[self.__headers[column_i]].append(self.__value_placer)
        except IndexError:
            pass

    def __fill_column_from_row(self, column_i: int, data: list) -> None:
        """
        Put the value from the row in the column.
        """
        try:
            self.__columns[self.__headers[column_i]].append(data[column_i])
            self.__columns_with_i[self.__headers[column_i]].append(data[column_i])
        except IndexError:
            self.__fil_column_from_empty_row(column_i)

    # end +---------------------------+ ROW ADDING +----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------+ STRING TABLE COMPOSITION +------------------+ start

    # +----------------------+ NUMBER PARSING +----------------------+
    
    # def __parse_numbers(self):
    #     pass

    # def __parse_float(self):
    #     pass

    # def __parse_int_boolean(self):
    #     pass

    # def __parse_exponentials(self):
    #     pass

    # def __parse_bytes(self):
    #     pass

    # def __parse_escape_codes(self):
    #     pass

    # +------------------------+ TABLE BODY +------------------------+

    def compose(self) -> str:
        """
        Crafts the table and returns it as a string.
        """
        # Cleared every render; set after the display rows are materialised
        # so filter/sort and empty-row hiding agree on the same indices.
        self.__compose_empty_row_indexes = None
        if len(self.__columns) != 0:
            # Refuse to render into a space where the result would be
            # illegible, if the caller asked to be told -- issue #14.
            if self.__too_narrow_message is not None:
                available = self.__available_width()
                needed = self.__minimum_table_width()
                if needed > available:
                    return self.__too_narrow_message.format(
                        needed=needed, available=available
                    )
            # self.__parse_data()  # TODO add parsing
            rows, rows_with_i = self.__call_table_objects()
            # __call_table_objects fills missing values, so emptiness must be
            # taken from the stored empty-row map (and remapped if filter/sort
            # reordered the display copy), not re-detected on filled cells.
            self.__typify_table()
            self.__wrap_data(
                rows, 
                rows_with_i, 
                semi=True
            )
            self.__get_column_widths(semi=True)
            # Cap content to column_max_width by the same wrap/trim path the
            # terminal fit uses. Must run against the natural content widths
            # -- clamping the numbers first makes every reduction zero and
            # leaves the cells full-size so the body overflows the header.
            max_hit, headers, rows, rows_with_i = (
                self.__enforce_column_max_widths(rows, rows_with_i)
            )
            if max_hit:
                self.__wrap_data(
                    rows,
                    rows_with_i,
                    semi=False,
                    headers_after_semi=headers,
                )
                self.__get_column_widths(semi=False)
            # Raise floors from column_min_width and re-assert max budgets.
            self.__clamp_column_widths()
            table_width = self.__get_string_table_width()
            # Grow first when asked, then shrink if still over budget.
            if self.__expand_to_window:
                self.__expand_columns_to_window(table_width)
                table_width = self.__get_string_table_width()
            adjusted, headers, rows, rows_with_i = self.__check_columns_size(
                table_width,
                rows,
                rows_with_i
            )
            if adjusted:
                # Widths changed, so the data has to be re-wrapped against the
                # new budgets and measured again.
                self.__wrap_data(
                    rows,
                    rows_with_i,
                    semi=False,
                    headers_after_semi=headers
                )
                self.__get_column_widths(semi=False)
                self.__clamp_column_widths()
            elif not max_hit:
                # The table already fits. The second pass would wrap the same
                # data against the same widths, with the same headers, and
                # write the same numbers into the same attributes -- so it is
                # pure duplicated work. Point the final structures at what the
                # first pass produced instead.
                #
                # This is the common case: most tables fit their terminal.
                self.__processed_columns = self.__semi_processed_columns
                self.__processed_columns_with_i = (
                    self.__semi_processed_columns_with_i
                )

        return self.__form_string(
            table_with_i=self.__show_index
        )

    def __get_string_table_width(self) -> int:
        """
        Gets the horizontal width of the table::
        
            |---------- 25 ---------|
        
            +-----------------------+
            | column 1     column 2 |
            +==========+============+
            | size 1   |    12.4325 |
            | size 2   |   111.22   |
            | size 3   |     0.4    |
            | ?        |          ? |
            | size 5   | 39865      |
            +----------+------------+
        """
        one_column_margin = self.__style_composition.margin * 2
        all_columns_margin = one_column_margin * self.column_count
        vertical_body_lines: SeparatorLine = (
            self.__style_composition.vertical_table_body_lines
        )
        separator_count = self.__column_count - 1
        left_len = self.__check_if_none_and_get_len(vertical_body_lines.left)
        right_len = self.__check_if_none_and_get_len(vertical_body_lines.right)
        middle_len = self.__check_if_none_and_get_len(vertical_body_lines.middle)   
        if not self.__show_index:     
            separators_of_table = sum([
                left_len,
                (middle_len * separator_count),
                right_len
            ])
            table_width = sum([
                *self.__column_widths_as_list,
                all_columns_margin,
                separators_of_table
            ])
            return table_width
        else:
            separators_of_table_with_i = sum([
                left_len,
                middle_len * separator_count,
                right_len
            ])
            table_width_with_i = sum([
                *self.__column_widths_as_list_with_i,
                all_columns_margin + one_column_margin,
                separators_of_table_with_i
            ])
            return table_width_with_i
        
    def __check_columns_size(self, 
                             table_width: int, 
                             rows: list, 
                             rows_with_i: list
                            ) -> Tuple[list, list]:
        """
        Checks the difference between the width of the table and the 
        width of the terminal.
        
        It adjusts the column widths if necessary.
        """
        adjust = False
        difference = 0
        available = self.__available_width()
        if available < table_width:
            difference = (table_width - available) + 1
            adjust = True
        if adjust:
            headers, rows, rows_with_i = self.__adjust_column_widths(
                difference,
                rows,
                rows_with_i
            )
        else:
            if self.show_index:
                headers = self.__headers_with_i
            else:
                headers = self.__headers
        return adjust, headers, rows, rows_with_i
    
    def __get_amounts_to_reduce(self, difference: int) -> list:
        """
        Determines the amount of space to reduce to each column.
        
        Index column will never get its space reduced.
        """
        if self.__show_index:
            # Copy: the stored list is read again later, and the original
            # popped the index entry straight out of it.
            widths = list(self.__column_widths_as_list_with_i)[1:]
        else:
            widths = list(self.__column_widths_as_list)

        if not widths:
            return [0] if self.__show_index else []

        # Take the space off the widest columns first, levelling them down
        # towards the next widest, and only reach the narrow ones once the
        # wide ones have nothing left to give.
        #
        # Reducing every column in proportion to its width, as this did
        # before, shrinks a 4-wide column whenever a 24-wide one is beside it,
        # wrapping data that had room to spare while the wide column keeps
        # more than it needs. That is issue #16.
        floors = self.__column_shrink_floors()
        reductions = [0] * len(widths)
        remaining = difference

        while remaining > 0:
            current = [width - taken for width, taken in zip(widths, reductions)]
            # Only columns still above their own floor have anything to give.
            givers = [i for i in range(len(current)) if current[i] > floors[i]]
            if not givers:
                # Nothing may shrink further without becoming unreadable, or
                # without mangling a number.
                break

            widest = max(current[i] for i in givers)
            at_widest = [i for i in givers if current[i] == widest]
            below = [current[i] for i in givers if current[i] < widest]
            # Level down to the next distinct width, but never below the floor
            # of the columns doing the giving.
            floor_here = max(floors[i] for i in at_widest)
            target = max(max(below) if below else floor_here, floor_here)
            drop_each = max(1, widest - target)

            if drop_each * len(at_widest) > remaining:
                # The last of the difference, shared among the widest columns.
                share, leftover = divmod(remaining, len(at_widest))
                for position, index in enumerate(at_widest):
                    wanted = share + (1 if position < leftover else 0)
                    reductions[index] += min(
                        wanted, current[index] - floors[index]
                    )
                remaining = 0
            else:
                for index in at_widest:
                    taken = min(drop_each, current[index] - floors[index])
                    reductions[index] += taken
                    remaining -= taken

        if self.__show_index:
            reductions.insert(0, 0)

        return reductions
    
    def __column_shrink_floors(self) -> list:
        """
        Narrowest each column may become, in the order the widths are held.

        Text can always be wrapped or trimmed down to ``MIN_COLUMN_SIZE``. A
        float column cannot: its decimals can be dropped, but the digits in
        front of the point *are* the number, and cutting those would print a
        different one. So a float column's floor is however wide its longest
        integer part is. A caller-set ``column_min_width`` raises the floor
        further.

        Handing a column a reduction it cannot absorb is how a shrunk table
        ended up still too wide -- the space was booked against a column that
        then gave nothing back.
        """
        if self.__show_index:
            # The index column is never reduced, so it is not in this list.
            headers = list(self.__headers_with_i)[1:]
            type_names = list(self.__column_types_as_list_with_i)[1:]
            processed = self.__semi_processed_columns_with_i
        else:
            headers = list(self.__headers)
            type_names = list(self.__column_types_as_list)
            processed = self.__semi_processed_columns

        skip_rows = self.__hidden_row_indexes()
        floors = []
        for user_i, (header, type_name) in enumerate(zip(headers, type_names)):
            column = processed.get(header)
            if type_name != TYPE_NAMES.float_ or column is None:
                floor = MIN_COLUMN_SIZE
            else:
                extents = _float_extents(column['data'], skip_rows)
                floor = max(MIN_COLUMN_SIZE, extents.left)
            lo = self.__bound_for_column(
                self.__column_min_width, header, user_i
            )
            if lo is not None:
                floor = max(floor, int(lo))
            floors.append(floor)
        return floors

    def __shrink_float_column(self,
                              column_i: int,
                              columns: List[list],
                              new_width: int,
                             ) -> Tuple[str, List[list]]:
        """
        Narrow a float column without breaking its decimal axis.

        Decimals go first: a rounded number is still a number, and every
        point stays on the one axis. Text in the column -- a missing value,
        say -- is trimmed like any other string, since it has no decimals to
        give up. The digits in front of the point are never touched.

        The alternative, which is what this used to do, was to send the whole
        column down the trimming path and overwrite its alignment with the
        string default first. The numbers stopped lining up even when nothing
        was long enough to be trimmed. That is issue #23.
        """
        column = columns[column_i]
        extents = _float_extents(column)

        if extents.point:
            room_for_decimals = new_width - extents.left - extents.point
            if room_for_decimals < extents.right:
                decimals = max(0, room_for_decimals)
                for row_i, cell in enumerate(column):
                    column[row_i] = _round_float_cell(cell, decimals)

        for row_i, cell in enumerate(column):
            if _is_numeric_cell(cell):
                continue
            if is_some_instance(cell, tuple, list):
                column[row_i] = tuple(
                    self.__trim_with_sign(part, new_width)
                    if visible_width(str(part)) > new_width else part
                    for part in cell
                )
            elif visible_width(str(cell)) > new_width:
                column[row_i] = self.__trim_with_sign(cell, new_width)

        if self.show_index:
            header = self.__headers_with_i[column_i]
        else:
            header = self.__headers[column_i]

        # The header is words, so it wraps like words.
        if self.__auto_wrap_table:
            header = self.__apply_wrap(header, new_width)
        elif visible_width(str(header)) > new_width:
            header = self.__trim_with_sign(header, new_width)

        return header, column

    def __adjust_column_widths(self,
                               difference: int,
                               rows: List[list],
                               rows_with_i: List[list]
                              ) -> Tuple[list, List[list], List[list]]:
        """
        Reduces the difference provided to each column.
        """
        # zip(*rows) is empty when the table has headers but no body rows.
        # The shrink path still has to touch every header, so keep one empty
        # column list per header rather than indexing into [].
        if self.__show_index:
            if rows_with_i:
                columns_with_i = list(map(list, zip(*rows_with_i)))
            else:
                columns_with_i = [[] for _ in self.__headers_with_i]
            columns = rows  # will remain untouched
        else:
            columns_with_i = rows_with_i  # will remain untouched
            if rows:
                columns = list(map(list, zip(*rows)))
            else:
                columns = [[] for _ in self.__headers]
        to_reduce_per_col = self.__get_amounts_to_reduce(difference)
        adjusted_headers = []
        adjusted_columns = []
        for col_i , to_reduce in enumerate(to_reduce_per_col):
            if self.__show_index:
                wpped_header, wpped_body = self.__adjust_column_to_new_width(
                    col_i, 
                    to_reduce,
                    columns_with_i,
                )
            else:
                wpped_header, wpped_body = self.__adjust_column_to_new_width(
                    col_i, 
                    to_reduce,
                    columns,
                )
            adjusted_headers.append(wpped_header)
            adjusted_columns.append(wpped_body)
        if self.__show_index:
            return adjusted_headers, rows, zip(*adjusted_columns)
        else:
            return adjusted_headers, zip(*adjusted_columns), rows_with_i
    
    def __wrap_columns(self, 
                       column_i: int, 
                       columns: List[list], 
                       new_width: int, 
                       index: int
                      ) -> Tuple[str, List[list]]:
        """
        Wraps the column with the provided width::
        
            'Wrapped\\ndata'
        """
        col_to_wrap = columns[column_i]
        if self.show_index:
            header_to_wrap = self.__headers_with_i[column_i]
        else:            
            header_to_wrap = self.__headers[column_i]
        header_to_wrap = self.__apply_wrap(
            header_to_wrap, 
            new_width
        )
        for row_i, row in enumerate(col_to_wrap):
            wrapped = self.__apply_wrap(row, new_width)
            col_to_wrap[row_i] = wrapped
            
        return header_to_wrap, col_to_wrap
    
    def __trim_column(self, 
                      column_i: int, 
                      columns: List[list], 
                      new_width: int, 
                      index: int
                     ) -> Tuple[str, List[list]]:
        """
        Trims the column with the provided width::
        
            'Trimmed d...'
        """
        col_to_trim = columns[column_i]
        if self.show_index:
            header_to_trim = self.__headers_with_i[column_i]
        else:
            header_to_trim = self.__headers[column_i]
        if len(str(header_to_trim)) > new_width:
            header_to_trim = self.__trim_with_sign(
                header_to_trim, 
                new_width
            )
        for row_i, row in enumerate(col_to_trim):
            if len(str(row)) > new_width:
                trimmed = self.__trim_with_sign(
                    row,
                    new_width
                )
                col_to_trim[row_i] = trimmed
        
        return header_to_trim, col_to_trim
    
    def __wrap_or_trim_data(self, 
                            column_i: int, 
                            new_width: int, 
                            columns: List[list], 
                            index: bool,
                            col_type_name: str, 
                            column_title: str
                           ) -> Tuple[str, List[list]]:
        """
        Wraps or trims the data of a column, depending on the type
        and the ``__auto_wrap_table`` setting.
        """
        trim_alignment = type_alignments[TYPE_NAMES.str_]
        can_wrap = col_type_name in CAN_WRAP_TYPES and self.__auto_wrap_table
        if can_wrap:
            return self.__wrap_columns(
                column_i=column_i,
                columns=columns,
                new_width=new_width,
                index=True
            )
        elif col_type_name == TYPE_NAMES.float_:
            # A float column keeps its decimal axis; it gives up decimals
            # rather than characters, and its alignment is left alone.
            return self.__shrink_float_column(
                column_i=column_i,
                columns=columns,
                new_width=new_width,
            )
        else:
            if index:
                self.__column_alignments_with_i[
                    column_title
                ] = trim_alignment
                self.__column_alignments_as_list_with_i[
                    column_i
                ] = trim_alignment
            else:
                self.__column_alignments[
                    column_title
                ] = trim_alignment
                self.__column_alignments_as_list[
                    column_i
                ] = trim_alignment
            return self.__trim_column(
                column_i=column_i,
                columns=columns,
                new_width=new_width,
                index=True
            )
        
    def __adjust_column_to_new_width(self, 
                                     column_i: int, 
                                     to_reduce: int, 
                                     columns: List[list]
                                    ) -> Tuple[str, List[list]]:
        """
        Will adjust a column to the provided width.
        """
        if self.__show_index:
            col_title = self.__headers_with_i[column_i]
            col_type = self.__column_types_as_list_with_i[column_i]
            new_width = sum([
                self.__column_widths_with_i[col_title],
                -to_reduce
            ])
        else:
            col_title = self.__headers[column_i]
            col_type = self.__column_types_as_list[column_i]
            new_width = sum([
                self.__column_widths[col_title],
                -to_reduce
            ])
        return self.__wrap_or_trim_data(
            column_i,
            new_width,
            columns,
            index=False,
            col_type_name=col_type,
            column_title=col_title
        )
            
    
    @staticmethod
    def __apply_format_spec(value, fmt):
        """Turn a format string or callable into a printed cell."""
        if callable(fmt):
            return fmt(value)
        if not isinstance(fmt, str):
            return value
        if '{' in fmt:
            return fmt.format(value)
        if '%' in fmt and fmt != '%':
            try:
                return fmt % value
            except (TypeError, ValueError):
                pass
        try:
            return format(value, fmt)
        except (TypeError, ValueError):
            return value

    def __format_display_value(self, value, header, column_i):
        """
        Apply int/float/custom formatters to one cell for display.

        Called after missing-value substitution and before wrapping, so the
        measured text is what the caller asked to print. Raw storage is
        untouched; ``__typify_table`` still reads ``self.__columns``.
        """
        if isinstance(value, bool):
            # bool is a subclass of int; never zero-pad True/False.
            formatted = value
        elif isinstance(value, int):
            if self.__int_format is not None:
                formatted = self.__apply_format_spec(value, self.__int_format)
            elif self.__leading_zeros:
                digits = self.__leading_zeros
                if value < 0:
                    formatted = '-' + str(abs(value)).zfill(digits)
                else:
                    formatted = str(value).zfill(digits)
            else:
                formatted = value
        elif isinstance(value, float):
            if self.__float_format is not None:
                formatted = self.__apply_format_spec(value, self.__float_format)
            else:
                formatted = value
        elif isinstance(value, Table):
            # Minimal nested subtable: compose the child into a multiline cell.
            # Child panel/shadow still apply; avoid cycles by not wrapping self.
            formatted = value.compose()
        else:
            formatted = value

        if self.__strip_cells and isinstance(formatted, str):
            formatted = formatted.strip()

        custom = self.__custom_format
        if custom is None:
            return formatted
        if callable(custom) and not isinstance(custom, dict):
            result = custom(formatted)
        elif isinstance(custom, dict):
            spec = custom.get(header)
            if spec is None and column_i is not None:
                # Allow integer keys for positional columns.
                spec = custom.get(column_i)
            if spec is not None:
                result = self.__apply_format_spec(formatted, spec)
            else:
                result = formatted
        else:
            result = formatted
        if self.__strip_cells and isinstance(result, str):
            return result.strip()
        return result

    def __bound_for_column(self, bounds, header, column_i):
        """Resolve a per-column min/max width for one column."""
        if bounds is None:
            return None
        if isinstance(bounds, dict):
            if header in bounds:
                return bounds[header]
            return bounds.get(column_i)
        if is_some_instance(bounds, list, tuple):
            if column_i is not None and column_i < len(bounds):
                return bounds[column_i]
            return None
        return int(bounds)

    def __clamp_column_widths(self):
        """
        Enforce column_min_width / column_max_width on the measured widths.

        Only the width numbers are changed here. Content that still exceeds a
        max is reduced by :meth:`__enforce_column_max_widths`, which walks the
        same wrap/trim path as a terminal fit.
        """
        if self.__show_index:
            headers = list(self.__headers_with_i)
            widths = list(self.__column_widths_as_list_with_i)
            store = self.__column_widths_with_i
        else:
            headers = list(self.__headers)
            widths = list(self.__column_widths_as_list)
            store = self.__column_widths

        if not widths:
            return

        for column_i, header in enumerate(headers):
            # Index column (position 0 with show_index) is not user-facing.
            user_i = None if (self.__show_index and column_i == 0) else (
                column_i - 1 if self.__show_index else column_i
            )
            lo = self.__bound_for_column(
                self.__column_min_width, header, user_i
            )
            hi = self.__bound_for_column(
                self.__column_max_width, header, user_i
            )
            width = widths[column_i]
            if lo is not None:
                width = max(width, int(lo))
            if hi is not None:
                hi = max(1, int(hi))
                if width > hi:
                    width = hi
            if lo is not None and hi is not None and int(lo) > max(1, int(hi)):
                width = max(1, int(hi))
            widths[column_i] = width
            store[header] = width

        if self.__show_index:
            self.__column_widths_as_list_with_i = widths
        else:
            self.__column_widths_as_list = widths

    def __enforce_column_max_widths(self, rows, rows_with_i):
        """
        Wrap or trim any column whose content exceeds ``column_max_width``.

        Returns ``(changed, headers, rows, rows_with_i)``. When nothing is
        over the cap, ``changed`` is false and the rows are returned as-is.
        """
        if self.__column_max_width is None:
            headers = (
                self.__headers_with_i if self.__show_index else self.__headers
            )
            return False, headers, rows, rows_with_i

        if self.__show_index:
            widths = list(self.__column_widths_as_list_with_i)
            headers = list(self.__headers_with_i)
            if rows_with_i:
                columns = list(map(list, zip(*rows_with_i)))
            else:
                columns = [[] for _ in headers]
        else:
            widths = list(self.__column_widths_as_list)
            headers = list(self.__headers)
            if rows:
                columns = list(map(list, zip(*rows)))
            else:
                columns = [[] for _ in headers]

        reductions = []
        any_reduce = False
        for column_i, header in enumerate(headers):
            user_i = None if (self.__show_index and column_i == 0) else (
                column_i - 1 if self.__show_index else column_i
            )
            hi = self.__bound_for_column(
                self.__column_max_width, header, user_i
            )
            if hi is None or user_i is None and self.__show_index and column_i == 0:
                reductions.append(0)
                continue
            hi = max(1, int(hi))
            if widths[column_i] > hi:
                reductions.append(widths[column_i] - hi)
                any_reduce = True
            else:
                reductions.append(0)

        if not any_reduce:
            return False, headers, rows, rows_with_i

        adjusted_headers = []
        adjusted_columns = []
        for column_i, to_reduce in enumerate(reductions):
            wpped_header, wpped_body = self.__adjust_column_to_new_width(
                column_i,
                to_reduce,
                columns,
            )
            adjusted_headers.append(wpped_header)
            adjusted_columns.append(wpped_body)

        if self.__show_index:
            new_rows_with_i = list(map(list, zip(*adjusted_columns))) if any(
                adjusted_columns
            ) else []
            # Keep the non-index rows in sync with the trimmed body cells.
            new_rows = [
                row[1:] for row in new_rows_with_i
            ] if new_rows_with_i else list(rows)
            return True, adjusted_headers, new_rows, new_rows_with_i

        new_rows = list(map(list, zip(*adjusted_columns))) if any(
            adjusted_columns
        ) else []
        return True, adjusted_headers, new_rows, rows_with_i

    def __expand_columns_to_window(self, table_width):
        """Distribute spare horizontal space across user columns."""
        available = self.__available_width()
        spare = available - table_width
        if spare <= 0:
            return False

        if self.__show_index:
            widths = list(self.__column_widths_as_list_with_i)
            headers = list(self.__headers_with_i)
            store = self.__column_widths_with_i
            start = 1  # never grow the index column
        else:
            widths = list(self.__column_widths_as_list)
            headers = list(self.__headers)
            store = self.__column_widths
            start = 0

        growable = list(range(start, len(widths)))
        if not growable:
            return False

        base, leftover = divmod(spare, len(growable))
        for offset, column_i in enumerate(growable):
            extra = base + (1 if offset < leftover else 0)
            hi = self.__bound_for_column(
                self.__column_max_width,
                headers[column_i],
                column_i - start if self.__show_index else column_i,
            )
            new_width = widths[column_i] + extra
            if hi is not None:
                new_width = min(new_width, int(hi))
            widths[column_i] = new_width
            store[headers[column_i]] = new_width

        if self.__show_index:
            self.__column_widths_as_list_with_i = widths
        else:
            self.__column_widths_as_list = widths
        return True

    def __display_row_order(self, rows):
        """
        Indices of rows to render, after filter and sort.

        Operates on stored row identity; the display copies are reordered to
        match. Filter receives the stored row, before formatters.
        """
        indices = list(range(len(rows)))
        if self.__row_filter is not None:
            indices = [
                i for i in indices
                if self.__row_filter(list(self.__rows[i]))
            ]

        if self.__sort_by is not None and indices:
            key = self.__sort_by
            if callable(key) and not isinstance(key, (str, bytes)):
                def sort_key(row_i, _key=key):
                    row = list(self.__rows[row_i])
                    # Replace ValuePlacer with missing_value for the key fn.
                    cleaned = [
                        self.__missing_value if isinstance(c, ValuePlacer) else c
                        for c in row
                    ]
                    return _key(cleaned)
            else:
                if isinstance(key, int):
                    column_i = key
                else:
                    try:
                        column_i = list(self.__headers).index(key)
                    except ValueError:
                        raise ValueError(
                            'sort_by column {0!r} is not in the table headers'
                            .format(key)
                        )

                def sort_key(row_i, _column_i=column_i):
                    cell = self.__rows[row_i][_column_i]
                    if isinstance(cell, ValuePlacer):
                        # Missing sorts as empty string so it is stable and low.
                        return (1, '')
                    return (0, cell)

            indices.sort(key=sort_key, reverse=self.__sort_reverse)

        return indices

    def __header_alignments_list(self, body_alignments, headers):
        """Body alignments overridden by header_align where set."""
        if self.__header_align is None:
            return list(body_alignments)

        result = list(body_alignments)
        for column_i, header in enumerate(headers):
            user_i = None if (self.__show_index and column_i == 0) else (
                column_i - 1 if self.__show_index else column_i
            )
            chosen = None
            per = self.__header_align
            if isinstance(per, dict):
                chosen = per.get(header)
                if chosen is None and user_i is not None:
                    chosen = per.get(user_i)
            elif is_some_instance(per, list, tuple):
                if user_i is not None and user_i < len(per):
                    chosen = per[user_i]
            else:
                if user_i is not None or not self.__show_index:
                    chosen = per
            if chosen is not None:
                result[column_i] = chosen
        return result

    def __call_table_objects(self):
        """
        This is to call the ``__call__`` method of the 
        stored objects in the table.

        returns:: 
            
            rows, rows_with_i 
        """
        # For adding the index. The index is in the first column
        # or the index 0.
        # The index column holds one shared IndexCounter, which counts up as
        # the render consumes it. It has to start from its configured origin
        # on every render or the second one continues where the first stopped.
        #
        # deepcopy used to give a fresh counter as a side effect of copying
        # the whole table. Resetting it says what is meant, and skips
        # recursing through every value to achieve it.
        self.__index_counter.reset_count()

        # One level of copying is enough: the pipeline replaces whole cells,
        # it never mutates one in place.
        rows_with_i = [list(row) for row in self.__rows_with_i]
        for row_i, row in enumerate(rows_with_i):
            if self.__show_empty_rows:
                rows_with_i[row_i][0] = row[0](
                    self.__i_start,
                    self.__i_step,
                )
            else:
                rows_with_i[row_i][0] = row[0](
                    self.__i_start,
                    self.__i_step,
                    row_i not in self.__empty_row_indexes
                )
            # For adding the missing value where the ValuePlacer
            # is used (in the rows with index).
            for column_i, column in enumerate(row):
                if isinstance(column, ValuePlacer):
                    rows_with_i[row_i][column_i] = column(
                        self.__missing_value
                    )
                
        # For adding the missing value where the ValuePlacer
        # is used.
        rows = [list(row) for row in self.__rows]
        for row_i, row in enumerate(rows):
            for column_i, column in enumerate(row):
                if isinstance(column, ValuePlacer):
                    rows[row_i][column_i] = column(
                        self.__missing_value
                    )

        # Filter and sort the display copies together so the index column
        # stays aligned with its row.
        order = self.__display_row_order(rows)
        empty_stored = set(self.__empty_row_indexes)
        self.__compose_empty_row_indexes = [
            new_i for new_i, old_i in enumerate(order)
            if old_i in empty_stored
        ]
        if order != list(range(len(rows))):
            rows = [rows[i] for i in order]
            rows_with_i = [rows_with_i[i] for i in order]
            # Index was consumed in stored order; renumber visible rows so
            # the column stays contiguous after a filter.
            self.__index_counter.reset_count()
            for row_i, row in enumerate(rows_with_i):
                rows_with_i[row_i][0] = self.__index_counter(
                    self.__i_start,
                    self.__i_step,
                )

        if self.__roman_index and rows_with_i:
            for row_i, row in enumerate(rows_with_i):
                if row:
                    rows_with_i[row_i][0] = to_roman(row[0])

        headers = list(self.__headers)
        for row_i, row in enumerate(rows):
            for column_i, header in enumerate(headers):
                if column_i >= len(row):
                    continue
                rows[row_i][column_i] = self.__format_display_value(
                    row[column_i], header, column_i
                )
                # rows_with_i has the index at 0.
                with_i_i = column_i + 1
                if with_i_i < len(rows_with_i[row_i]):
                    rows_with_i[row_i][with_i_i] = rows[row_i][column_i]

        return rows, rows_with_i
    
    @staticmethod
    def __checked_alignment(value, option_name):
        """
        Validate one alignment code.

        A typo used to be stored happily and then silently ignored by the
        aligner, which left the column where it was and gave no hint why.
        """
        if value is None:
            return None
        if value not in ALIGNMENT_CODES:
            raise ValueError(
                '{0} must be one of {1}, got {2!r}'.format(
                    option_name, ', '.join(sorted(ALIGNMENT_CODES)), value
                )
            )
        return value

    def __alignment_for(self, header, column_i, column_type, default):
        """
        The alignment a column ends up with.

        Three sources, most specific first: an entry in ``col_alignment`` for
        this column, the override for the column's type, and the typographic
        default the type carries. All three were being collected and none of
        them read -- ``_typify_column``'s answer went straight into the
        alignment tables, so setting ``str_align`` or ``col_alignment``
        changed nothing at all. Issue #4 asked for exactly this.

        ``column_i`` counts user-facing columns; the index column passes
        ``None`` and so is never matched by a positional ``col_alignment``.
        """
        chosen = None

        per_column = self.__column_align
        if isinstance(per_column, dict):
            chosen = per_column.get(header)
        elif is_some_instance(per_column, list, tuple):
            if column_i is not None and column_i < len(per_column):
                chosen = per_column[column_i]
        elif per_column is not None:
            chosen = per_column

        if chosen is None:
            chosen = {
                TYPE_NAMES.str_: self.__str_align,
                TYPE_NAMES.int_: self.__int_align,
                TYPE_NAMES.float_: self.__float_align,
                TYPE_NAMES.bool_: self.__bool_align,
            }.get(column_type)

        if chosen is None:
            return default

        if chosen == COLUMN_ALIGNS.float and column_type != TYPE_NAMES.float_:
            # Only a float column carries the two-sided measurement that
            # aligning on the decimal point needs.
            return default

        return chosen

    def __typify_table(self):
        for column_i, column in enumerate(self.__columns.items()):
            self.__typify_single_column(column, column_i)
        for column_i, column in enumerate(self.__columns_with_i.items()):
            self.__typify_single_column_with_i(column, column_i)

    def __typify_single_column(self, column, column_i):
        header, column_content = column
        cell_types, column_type, column_alignment = _typify_column(column_content)
        column_alignment = self.__alignment_for(
            header, column_i, column_type, column_alignment
        )
        try:
            self.__column_i_per_type[column_type].append(column_i)
        except KeyError:
            self.__column_i_per_type[column_type] = []
            self.__column_i_per_type[column_type].append(column_i)
        self.__column_types[header] = column_type
        self.__cell_types[header] = cell_types
        self.__column_alignments[header] = column_alignment
        try:
            self.__column_alignments_as_list[column_i] = column_alignment
            self.__column_types_as_list[column_i] = column_type
        except IndexError:
            self.__column_alignments_as_list.append(column_alignment)
            self.__column_types_as_list.append(column_type)
        
    def __typify_single_column_with_i(self, column, column_i):
        header, column_content = column
        if column_i == 0:
            is_index = True
        else:
            is_index = False
        cell_types, column_type, column_alignment = _typify_column(
            column_content,
            index_column=is_index
        )
        column_alignment = self.__alignment_for(
            header,
            None if is_index else column_i - 1,
            column_type,
            column_alignment,
        )
        try:
            self.__column_i_per_type_with_i[column_type].append(column_i)
        except KeyError:
            self.__column_i_per_type_with_i[column_type] = []
            self.__column_i_per_type_with_i[column_type].append(column_i)
        self.__column_types_with_i[header] = column_type
        self.__cell_types_with_i[header] = cell_types
        self.__column_alignments_with_i[header] = column_alignment
        try:
            self.__column_alignments_as_list_with_i[column_i] = column_alignment
            self.__column_types_as_list_with_i[column_i] = column_type
        except IndexError:
            self.__column_alignments_as_list_with_i.append(column_alignment)
            self.__column_types_as_list_with_i.append(column_type)

    def __display_header_labels(self, headers):
        """
        Headers as shown: optional 1-based numbering for data columns.

        Index column (``IndexColumnTitle``) keeps ``index_title``. Dict keys
        elsewhere still use the real header objects.
        """
        if not self.__number_columns:
            return list(headers)
        labels = []
        n = 0
        for header in headers:
            if isinstance(header, IndexColumnTitle):
                labels.append(header)
            else:
                n += 1
                labels.append(str(n))
        return labels

    def __wrap_data(self, 
                    rows, 
                    rows_with_i, 
                    semi,
                    headers_after_semi = []
                   ) -> None:
        if semi:
            headers_with_i = self.__headers_with_i
            headers = self.__headers
        else:
            headers_with_i = headers_after_semi
            headers = headers_after_semi
            
        if self.show_index:
            headers = headers_with_i
            rows = rows_with_i
            semi_processed_columns = self.__semi_processed_columns_with_i
            processed_columns = self.__processed_columns_with_i
        else:
            semi_processed_columns = self.__semi_processed_columns
            processed_columns = self.__processed_columns
            
        # Fitting can hand back a one-shot zip(); materialise before any
        # pass that walks the rows (valign resolution would otherwise empty it).
        rows = list(rows) if rows is not None else []
        display_headers = self.__display_header_labels(headers)
        header_valigns, row_valigns = self.__valigns_for_wrap(
            headers, rows
        )
        wrapped_headers, wrapped_rows = _wrap_rows(
            display_headers,
            rows,
            header_valigns=header_valigns,
            row_valigns=row_valigns,
        )
        transformed_columns, transformed_headers = _zip_wrapped_rows(
            wrapped_headers, 
            wrapped_rows, 
        )
        
        if self.show_index:
            columns_to_iterate = {
                self.__index_title: [], **self.__columns
            }.items()
        else:
            columns_to_iterate = self.__columns.items()
        for i, column in enumerate(columns_to_iterate):
            header, _ = column
            if semi:
                semi_processed_columns[header] = {
                    'header': transformed_headers[i],
                    'data': transformed_columns[i]
                }
            else:
                processed_columns[header] = {
                    'header': transformed_headers[i],
                    'data': transformed_columns[i]
                }

                
    def __hidden_row_indexes(self) -> frozenset:
        """
        Indexes of rows that will not be rendered.

        Width measurement must skip these. An empty row still holds the
        missing value in every column, and counting it widened columns to fit
        text that is never displayed -- issue #22.

        After filter/sort the display rows are a new sequence; the indexes
        computed for that sequence (``__compose_empty_row_indexes``) win over
        the stored-table ones.
        """
        if self.__show_empty_rows:
            return frozenset()
        if self.__compose_empty_row_indexes is not None:
            return frozenset(self.__compose_empty_row_indexes)
        return frozenset(self.__empty_row_indexes)

    def __get_column_widths(self, semi):
        if self.show_index:
            sizes_with_i, float_sizes_with_i = _column_widths(
                processed_columns=(
                    self.__semi_processed_columns_with_i
                ) if semi else (
                    self.__processed_columns_with_i
                ),
                column_type_names=self.__column_types_with_i,
                show_headers=self.__show_headers,
                skip_rows=self.__hidden_row_indexes()
            )
            self.__column_widths_as_list_with_i = sizes_with_i
            if float_sizes_with_i is not None:
                self.__float_columns_widths_with_i = {
                    **self.__float_columns_widths_with_i,
                    **float_sizes_with_i
                }
            for column_i, column in enumerate(self.__columns_with_i.items()):
                header, _ = column
                self.__column_widths_with_i[header] = sizes_with_i[column_i]
        else:
            sizes, float_sizes = _column_widths(
                processed_columns=(
                    self.__semi_processed_columns
                ) if semi else (
                    self.__processed_columns
                ),
                column_type_names=self.__column_types,
                show_headers=self.__show_headers,
                skip_rows=self.__hidden_row_indexes()
            )
            self.__column_widths_as_list = sizes
            if float_sizes is not None:
                self.__float_columns_widths = {
                    **self.__float_columns_widths,
                    **float_sizes
                }
            for column_i, column in enumerate(self.__columns.items()):
                header, _ = column
                self.__column_widths[header] = sizes[column_i]
        

    def __parse_data(self):
        pass

    def __form_string(self, table_with_i=False):
        # Data from column dict is put in tuples
        unaligned_columns = self.__get_processed_columns_data(
            columns_with_i=table_with_i
        )
        unaligned_header = self.__get_processed_columns_data(
            header=True,
            columns_with_i=table_with_i
        )
        if table_with_i:
            column_titles = self.__headers_with_i
            column_alignments_list = self.__column_alignments_as_list_with_i
            column_widths_list = self.__column_widths_as_list_with_i
            float_column_widths = self.__float_columns_widths_with_i
        else:
            column_titles = self.__headers
            column_alignments_list = self.__column_alignments_as_list
            column_widths_list = self.__column_widths_as_list
            float_column_widths = self.__float_columns_widths
        header_alignments_list = self.__header_alignments_list(
            column_alignments_list, column_titles
        )
        user_hidden = self.__user_hidden_column_indexes(table_with_i)
        # Header and body rows get aligned
        aligned_header = _align_headers(
            self.__style_composition,
            unaligned_header,
            header_alignments_list,
            column_widths_list,
            self.__empty_column_indexes,
            self.__show_empty_columns,
            float_column_widths,
            user_hidden,
        )
        # Colour is applied after alignment, never before. By this point every
        # cell has been padded to its exact visible width, so wrapping it in
        # escape sequences cannot disturb any measurement, and the float
        # aligner has already done its split on the decimal point.
        colors_on = self.__colors_active and self.__has_any_color()
        if colors_on and self.__header_color:
            aligned_header = self.__paint_header(
                aligned_header, self.__header_color
            )
        aligned_header = self.__zip_columns(aligned_header, headers=True)
        aligned_columns = list(_align_columns(
            self.__style_composition,
            unaligned_columns,
            column_titles,  # here the header is used to know the title of the column
            column_alignments_list,
            column_widths_list,
            self.__empty_column_indexes,
            self.__show_empty_columns,
            float_column_widths,
            user_hidden,
        ))
        if colors_on:
            # Stash body length so footer_rows can resolve during paint.
            self._paint_body_len = (
                len(aligned_columns[0]) if aligned_columns else 0
            )
            aligned_columns = self.__paint_cells(
                aligned_columns,
                lambda cell_i, row_i: self.__color_for_cell(
                    self.__raw_value_at(column_titles, cell_i, row_i),
                    row_i,
                    column_titles[cell_i] if cell_i < len(column_titles) else '',
                    column_index=cell_i,
                ),
            )
        aligned_columns = self.__zip_columns(aligned_columns)
        # String separators and data rows are joined. Horizontal rules stay
        # plain here; cell-background fills (and optional border_color) are
        # applied per segment below so coloured cells do not sit above a dark
        # H-rule band.
        separators: HorizontalComposition = _get_separators(
            self.__style_composition,
            column_widths_list,
            self.__empty_column_indexes,
            self.__show_empty_columns,
            column_alignments_list,
            user_hidden,
        )
        empty_rows_for_render = (
            self.__compose_empty_row_indexes
            if self.__compose_empty_row_indexes is not None
            else self.__empty_row_indexes
        )
        data_rows: DataRows = _get_data_rows(
            self.__style_composition,
            aligned_header,
            aligned_columns,
            self.__show_headers,
            empty_rows_for_render,
            self.__show_empty_rows,
            self.__border_color if colors_on else None,
        )

        header_row = data_rows.header_row
        body_rows = data_rows.body_rows
        gap_separator = None
        if colors_on:
            separators, gap_separator = self.__colour_horizontal_rules(
                separators,
                column_widths_list,
                column_titles,
                len(body_rows),
            )
        elif self.__border_color:
            separators = HorizontalComposition(*[
                colorize(line, self.__border_color) if line is not None else None
                for line in separators
            ])

        if self.__border_texts:
            separators, gap_separator = self.__apply_horizontal_border_texts(
                separators, gap_separator
            )

        # Table string is formed
        no_header_superior = separators.superior_header_line_no_header
        body_line = ''.join(['\n', separators.table_body_line]) if (
                separators.table_body_line is not None
        ) else NONE_VALUE_REPLACEMENT

        end_line = separators.table_end_line

        if self.__show_headers:
            superior_row = '\n'.join([
                part for part in (
                    separators.superior_header_line,
                    header_row,
                    separators.inferior_header_line,
                ) if part
            ])
        else:
            superior_row = no_header_superior

        # A style may draw no top rule, no bottom rule, or neither, and a
        # table may have no body at all -- headers describing a query that
        # returned nothing. Whatever is missing is left out rather than
        # joined in as an empty string, which is what used to put a blank
        # line through the middle of a table with no rows.
        body, body_line_map = self.__join_body_rows(
            body_rows, body_line, separators.table_body_line,
            gap_separator=gap_separator,
        )
        title_line = self.__title_line(column_widths_list, table_with_i)
        caption_line = self.__caption_line(column_widths_list, table_with_i)

        # Where the body starts depends on which of the parts before it were
        # drawn at all: a title, a top rule, a header. Counting them off the
        # same list that gets joined keeps the merge line map in step with the
        # string -- a title used to be left out of that count, which shifted
        # every merge one line up, into the header.
        parts = []
        body_offset = 0
        for part in (title_line, superior_row, body, end_line, caption_line):
            if not part:
                continue
            if part is body:
                body_offset = sum(earlier.count('\n') + 1 for earlier in parts)
            parts.append(part)
        table_string = '\n'.join(parts)

        if self.__merged_regions:
            table_string = self.__apply_merges(
                table_string, body_line_map, body_offset,
                column_widths_list, table_with_i
            )

        if self.__border_texts:
            table_string = self.__apply_vertical_border_texts(table_string)

        table_string = self.__apply_panel_and_shadow(table_string)
        return self.__apply_table_align(table_string)

    def __join_body_rows(self, body_rows, body_line, separator_line,
                         gap_separator=None):
        """
        Join body rows, inserting extra divider rules where requested.

        ``body_line`` already carries a leading newline when the style draws
        a rule between every row. When the style has no inter-row rule,
        ``add_divider`` inserts a dashed line after the chosen row index
        (display order after filter/sort).

        ``gap_separator``, when set, is called as ``gap_separator(after_row)``
        to build the rule between that display row and the next (used to paint
        cell backgrounds onto H-rules).

        Returns the joined body and a map from display row index to the
        physical lines that row occupies, numbered from the start of the body.
        Building the map here rather than reconstructing it afterwards is what
        keeps merges aligned with rows: only this function knows how many rule
        lines it put between them, and wrapping has already turned some rows
        into several lines.
        """
        if not body_rows:
            return '', {}

        pieces = []
        line_map = {}
        cursor = 0

        # A style with no inter-row rule still gets the dividers ``add_divider``
        # asked for, drawn as a dashed line. A style that rules between every
        # row already shows them.
        explicit_dividers = (
            self.__dividers if (self.__dividers and separator_line is None)
            else set()
        )
        rule = None
        if explicit_dividers:
            rule = '-' * max(visible_width(body_rows[0]), 1)

        separator_lines = body_line.count('\n') if separator_line is not None else 0

        for display_i, row in enumerate(body_rows):
            if display_i:
                if separator_line is not None:
                    if gap_separator is not None:
                        pieces.append(gap_separator(display_i - 1))
                    else:
                        pieces.append(body_line[1:] if body_line.startswith('\n')
                                      else body_line)
                    cursor += separator_lines
                elif (display_i - 1) in explicit_dividers:
                    pieces.append(rule)
                    cursor += 1
            height = row.count('\n') + 1
            line_map[display_i] = list(range(cursor, cursor + height))
            cursor += height
            pieces.append(row)

        return '\n'.join(pieces), line_map

    def __title_line(self, column_widths_list, table_with_i):
        """Centre the title over the full table width, if any."""
        if not self.__title:
            return None
        table_width = self.__get_string_table_width()
        title = self.__title
        title_width = visible_width(title)
        if title_width >= table_width:
            return title
        left = (table_width - title_width) // 2
        return (' ' * left) + title


    def __valign_for_cell(self, row_index, header, column_i):
        """Resolve t/m/b for one body cell (cell > column > default)."""
        from .cells import _normalize_valign
        cell_map = self.__cell_valign or {}
        if cell_map:
            for key in ((row_index, header), (row_index, column_i)):
                if key in cell_map:
                    return _normalize_valign(cell_map[key])
        per = self.__col_valign
        if per is not None:
            if isinstance(per, dict):
                if header in per:
                    return _normalize_valign(per[header])
                if column_i in per:
                    return _normalize_valign(per[column_i])
            elif is_some_instance(per, list, tuple):
                if column_i is not None and column_i < len(per):
                    return _normalize_valign(per[column_i])
            else:
                return _normalize_valign(per)
        return _normalize_valign(self.__valign)

    def __valigns_for_wrap(self, headers, rows):
        """Build header_valigns and per-row body valign lists for ``_wrap_rows``."""
        from .cells import _normalize_valign
        default = _normalize_valign(self.__valign)
        # Only pay the cost when something is not top: resolving a code per
        # cell is a measurable share of a large render.
        needs = (
            default != 't'
            or self.__col_valign is not None
            or bool(self.__cell_valign)
        )
        if not needs:
            return None, None
        n = len(headers) if headers is not None else 0
        # Headers follow column valign (no per-cell header map).
        header_valigns = []
        for column_i, header in enumerate(headers or []):
            user_i = None if (self.__show_index and column_i == 0) else (
                column_i - 1 if self.__show_index else column_i
            )
            if self.__show_index and column_i == 0:
                header_valigns.append(default)
                continue
            header_valigns.append(
                self.__valign_for_cell(-1, header, user_i)
                if user_i is not None else default
            )
        # Force header-only resolution without cell_valign row hits:
        # __valign_for_cell with row -1 won't match normal cell keys.
        row_valigns = []
        for row_i, row in enumerate(rows or []):
            codes = []
            for column_i in range(len(row)):
                if self.__show_index:
                    if column_i == 0:
                        codes.append(default)
                        continue
                    header = headers[column_i] if column_i < n else ''
                    user_i = column_i - 1
                else:
                    header = headers[column_i] if column_i < n else ''
                    user_i = column_i
                codes.append(self.__valign_for_cell(row_i, header, user_i))
            row_valigns.append(codes)
        return header_valigns, row_valigns

    def __apply_panel_and_shadow(self, table_string):
        """Wrap the finished table in an optional outer panel and/or shadow."""
        if not table_string:
            return table_string
        out = table_string
        if self.__panel:
            out = self.__wrap_panel(out)
        if self.__shadow:
            out = self.__apply_shadow(out)
        return out

    def __panel_glyphs(self):
        """Box-drawing glyphs for the outer panel frame."""
        name = 'rounded'
        if isinstance(self.__panel, str) and self.__panel not in ('True', 'true', '1'):
            name = self.__panel.lower()
        presets = {
            'rounded': ('╭', '─', '╮', '│', '╰', '╯'),
            'sharp':   ('┌', '─', '┐', '│', '└', '┘'),
            'ascii':   ('+', '-', '+', '|', '+', '+'),
            'double':  ('╔', '═', '╗', '║', '╚', '╝'),
            'heavy':   ('┏', '━', '┓', '┃', '┗', '┛'),
        }
        return presets.get(name, presets['rounded'])

    def __wrap_panel(self, table_string):
        tl, hz, tr, vt, bl, br = self.__panel_glyphs()
        lines = table_string.splitlines()
        width = max((visible_width(line) for line in lines), default=0)
        padded = []
        for line in lines:
            pad = width - visible_width(line)
            padded.append(line + (' ' * pad))
        top = tl + (hz * width) + tr
        bottom = bl + (hz * width) + br
        body = [vt + line + vt for line in padded]
        return chr(10).join([top] + body + [bottom])

    def __apply_shadow(self, table_string):
        glyph = '░'
        if isinstance(self.__shadow, str) and self.__shadow not in ('True', 'true', '1'):
            glyph = self.__shadow[:1] or '░'
        lines = table_string.splitlines()
        width = max((visible_width(line) for line in lines), default=0)
        out = []
        for i, line in enumerate(lines):
            pad = width - visible_width(line)
            body = line + (' ' * pad)
            # First line: no right-edge shadow (Spectre-style); later lines get it,
            # plus a bottom shadow row.
            if i == 0:
                out.append(body + ' ')
            else:
                out.append(body + glyph)
        out.append(' ' + (glyph * width))
        return chr(10).join(out)


    def __caption_line(self, column_widths_list, table_with_i):
        """Centre the caption under the full table width, if any."""
        if not self.__caption:
            return None
        table_width = self.__get_string_table_width()
        caption = self.__caption
        caption_width = visible_width(caption)
        if caption_width >= table_width:
            return caption
        left = (table_width - caption_width) // 2
        return (' ' * left) + caption

    def __apply_table_align(self, table_string):
        """Pad every line so the table sits left, centre or right."""
        if not table_string or not self.__table_align:
            return table_string
        align = self.__table_align
        if align in (TABLE_ALIGNS.left, COLUMN_ALIGNS.left, 'l', 'left'):
            return table_string
        available = self.__available_width()
        lines = table_string.splitlines()
        width = max((visible_width(line) for line in lines), default=0)
        spare = available - width
        if spare <= 0:
            return table_string
        if align in (TABLE_ALIGNS.center, COLUMN_ALIGNS.center, 'c', 'center',
                     'tc'):
            left = spare // 2
        else:
            left = spare
        pad = ' ' * left
        return '\n'.join(pad + line for line in lines)

    def __apply_merges(self, table_string, body_line_map, body_offset,
                       column_widths_list, table_with_i):
        """
        Rewrite the assembled table so each merged region reads as one cell.

        Merges are applied to the finished string rather than threaded through
        the measuring pipeline. That pipeline sizes each column from its own
        content, which is what makes decimal alignment and terminal fitting
        work; letting a cell that belongs to several columns influence their
        widths would put a cycle in it.

        ``body_line_map`` comes from the join that produced the body, and is
        numbered from the body's first line; ``body_offset`` says where that
        line sits in the whole table.
        """
        from .merges import apply as apply_merges

        row_line_map = {
            row: [body_offset + line for line in line_indexes]
            for row, line_indexes in body_line_map.items()
        }

        # Columns the table is leaving out take up no room in a line, so the
        # merge offsets must not count them either -- the same list the
        # separators were built from.
        hidden_columns = self.__effective_hidden_columns(table_with_i)

        regions = self.__regions_with_colors()
        merged = apply_merges(
            table_string.split('\n'),
            row_line_map,
            regions,
            column_widths_list,
            self.__style_composition,
            1 if table_with_i else 0,
            hidden_columns,
        )
        return '\n'.join(merged)


    def __rule_spec_for_cell(self, row_index, column_index, column_titles):
        """
        Colour that should back the H-rule segment under a cell.

        Explicit merge colours win (so a wide merge paints one continuous
        band under its span). Otherwise the cell's resolved colour is used.
        """
        for region in self.__regions_with_colors():
            if (region.first_row <= row_index <= region.last_row
                    and region.first_column <= column_index <= region.last_column
                    and region.color):
                return region.color
        name = (
            column_titles[column_index]
            if column_index < len(column_titles) else ''
        )
        try:
            raw = self.__raw_value_at(column_titles, column_index, row_index)
        except Exception:
            raw = None
        return self.__color_for_cell(raw, row_index, name)

    def __rule_specs_for_row(self, row_index, column_titles, column_widths):
        """One colour spec per *drawn* column for the rule under ``row_index``."""
        hidden = set(self.__effective_hidden_columns(self.__show_index))
        specs = []
        for col_i, _width in enumerate(column_widths):
            if col_i in hidden:
                continue
            specs.append(
                self.__rule_spec_for_cell(row_index, col_i, column_titles)
            )
        return specs

    @staticmethod
    def _border_text_span(length, text_len, offset, align, lo, hi):
        """
        Where a ``border_text`` label goes on a line (or column) of
        ``length`` cells: returns ``(start, stop)``; the label is written from
        ``start`` and truncated at ``stop``.

        ``lo``/``hi`` bound the writable span inside the frame corners and are
        used when ``offset`` is None (automatic margin). An explicit
        ``offset`` is a margin from the aligned edge; for ``left`` it is the
        absolute start, exactly as before 2.0.18.
        """
        if offset is None:
            first, last = lo, hi
            if align == 'left':
                # Historic default was offset=1: keep it on corner-less lines.
                first = min(1, length)
        else:
            margin = int(offset)
            if align == 'left':
                first, last = margin, (hi if margin < hi else length)
            elif align == 'right':
                first, last = lo, max(lo, length - margin)
            else:
                first, last = margin, max(margin, length - margin)
        span = max(0, last - first)
        if align == 'center':
            start = first + max(0, (span - text_len) // 2)
        elif align == 'right':
            start = first + max(0, span - text_len)
        else:
            start = first
        return start, last

    def __overlay_line_text(self, line, text, offset=None, color=None,
                              align='left', chrome_color=None):
        """
        Replace a span of ``line`` with ``text`` (tabled LineText spirit).

        Works on ANSI-coloured lines by stripping for geometry, then rebuilding
        ``prefix + colored_text + suffix``. Truncates text that does not fit.
        Placement (``offset`` + ``align``) is worked out by
        ``_border_text_span``.
        ``chrome_color`` (defaults to ``border_color``) repaints the non-text
        segments so overlays do not strip an existing border foreground.
        """
        if line is None:
            return None
        plain = strip_ansi(line)
        if not plain:
            return line
        raw = '' if text is None else str(text)
        # Drop ANSI from the overlay itself; we recolour via ``color``.
        raw = strip_ansi(raw)
        chars = list(plain)
        width = len(chars)
        text_chars = list(raw)
        tw = len(text_chars)
        # The writable span excludes the outer corners, so an aligned or
        # overlong label never eats the frame's closing junction.
        lo = 1 if width > 2 and not chars[0].isspace() else 0
        hi = width - 1 if width > 2 and not chars[-1].isspace() else width
        start, stop = self._border_text_span(width, tw, offset, align, lo, hi)
        if start >= width:
            return line
        available = stop - start
        if tw > available:
            text_chars = text_chars[:available]
            tw = len(text_chars)
        for i, ch in enumerate(text_chars):
            chars[start + i] = ch
        new_plain = ''.join(chars)
        chrome = chrome_color if chrome_color is not None else self.__border_color
        prefix = new_plain[:start]
        mid = new_plain[start:start + tw]
        suffix = new_plain[start + tw:]
        if color or chrome:
            left = colorize(prefix, chrome) if chrome and prefix else prefix
            centre = colorize(mid, color or chrome) if (color or chrome) and mid else mid
            right = colorize(suffix, chrome) if chrome and suffix else suffix
            return left + centre + right
        return new_plain

    def __horizontal_border_specs(self, where):
        return [spec for spec in self.__border_texts if spec['where'] == where]

    def __apply_horizontal_border_texts(self, separators, gap_separator):
        """Overlay registered horizontal ``border_text`` entries onto rules."""
        def paint_field(line, where):
            if line is None:
                return None
            out = line
            for spec in self.__horizontal_border_specs(where):
                out = self.__overlay_line_text(
                    out, spec['text'], spec['offset'],
                    spec['color'], spec['align'],
                )
            return out

        painted = HorizontalComposition(
            paint_field(separators.superior_header_line, 'top'),
            paint_field(separators.inferior_header_line, 'header'),
            paint_field(separators.superior_header_line_no_header, 'top'),
            paint_field(separators.table_body_line, 'body'),
            paint_field(separators.table_end_line, 'bottom'),
        )

        body_specs = self.__horizontal_border_specs('body')
        if gap_separator is None or not body_specs:
            return painted, gap_separator

        def wrapped(after_row, _inner=gap_separator, _specs=body_specs):
            line = _inner(after_row)
            for spec in _specs:
                line = self.__overlay_line_text(
                    line, spec['text'], spec['offset'],
                    spec['color'], spec['align'],
                )
            return line

        return painted, wrapped

    def __apply_vertical_border_texts(self, table_string):
        """
        Overlay left/right ``border_text`` onto outer vertical glyphs.

        Writes one character of the text per successive physical line,
        starting at ``offset`` (0 = first line of the rendered table).
        """
        if not table_string:
            return table_string
        left_specs = [s for s in self.__border_texts if s['where'] == 'left']
        right_specs = [s for s in self.__border_texts if s['where'] == 'right']
        if not left_specs and not right_specs:
            return table_string

        lines = table_string.split('\n')
        n = len(lines)

        for spec in left_specs:
            text = strip_ansi(spec['text'])
            if not text:
                continue
            start, stop = self._border_text_span(
                n, len(text), spec['offset'], spec['align'],
                1 if n > 2 else 0, n - 1 if n > 2 else n,
            )
            for i, ch in enumerate(text):
                row = start + i
                if row < 0 or row >= stop:
                    break
                lines[row] = self.__replace_first_visible(
                    lines[row], ch, spec['color']
                )

        for spec in right_specs:
            text = strip_ansi(spec['text'])
            if not text:
                continue
            start, stop = self._border_text_span(
                n, len(text), spec['offset'], spec['align'],
                1 if n > 2 else 0, n - 1 if n > 2 else n,
            )
            for i, ch in enumerate(text):
                row = start + i
                if row < 0 or row >= stop:
                    break
                lines[row] = self.__replace_last_visible(
                    lines[row], ch, spec['color']
                )

        return '\n'.join(lines)

    @staticmethod
    def __replace_first_visible(line, ch, color):
        """Replace the first visible character of ``line`` with ``ch``."""
        plain = strip_ansi(line)
        if not plain:
            return line
        # Rebuild: find first non-ANSI char span by walking with strip.
        # Simpler path: compose new_plain then, if colouring, colourize ch.
        new_plain = ch + plain[1:]
        if color is None and line == plain:
            return new_plain
        # When the line carries ANSI, keep suffix after first visible char.
        # Locate end of first visible character in the ANSI string.
        from .text_width import has_ansi
        if not has_ansi(line):
            return colorize(ch, color) + plain[1:] if color else new_plain
        # Walk CSI sequences; first real char is the border glyph.
        import re
        sgr = re.compile(r'\x1b\[[0-9;]*m')
        pos = 0
        while pos < len(line):
            m = sgr.match(line, pos)
            if m:
                pos = m.end()
                continue
            # replace this one character
            head = line[:pos]
            # skip one unicode char
            tail_start = pos + 1
            # If original char was the start of a combining sequence, still +1
            # is fine for box-drawing / ascii borders.
            tail = line[tail_start:]
            painted = colorize(ch, color) if color else ch
            return head + painted + tail
        return line

    @staticmethod
    def __replace_last_visible(line, ch, color):
        """Replace the last visible character of ``line`` with ``ch``."""
        plain = strip_ansi(line)
        if not plain:
            return line
        from .text_width import has_ansi
        if not has_ansi(line):
            body = plain[:-1] + ch
            if color:
                return plain[:-1] + colorize(ch, color)
            return body
        import re
        sgr = re.compile(r'\x1b\[[0-9;]*m')
        # Find index of last visible character.
        last = None
        pos = 0
        while pos < len(line):
            m = sgr.match(line, pos)
            if m:
                pos = m.end()
                continue
            last = pos
            pos += 1
        if last is None:
            return line
        painted = colorize(ch, color) if color else ch
        return line[:last] + painted + line[last + 1:]

    def __colour_horizontal_rules(self, separators, column_widths,
                                  column_titles, body_row_count):
        """
        Paint cell backgrounds onto horizontal rules.

        Body gaps use the row above. The header/body rule uses the first body
        row (fill meets the header separator from below). The end rule uses
        the last body row. Superior header keeps ``border_color`` only unless
        ``header_color`` carries a background.
        Returns the updated HorizontalComposition and a gap painter callable
        (or None when the style has no body rule).
        """
        from .merges import compute_layout, paint_rule_cell_backgrounds

        hidden = self.__effective_hidden_columns(self.__show_index)
        layout = compute_layout(
            column_widths, self.__style_composition, hidden
        )
        border = self.__border_color

        def paint(line, specs):
            if line is None:
                return None
            return paint_rule_cell_backgrounds(line, layout, specs, border)

        first_specs = (
            self.__rule_specs_for_row(0, column_titles, column_widths)
            if body_row_count else []
        )
        last_specs = (
            self.__rule_specs_for_row(
                body_row_count - 1, column_titles, column_widths
            )
            if body_row_count else []
        )
        header_specs = []
        if self.__header_color and background_hex(self.__header_color):
            drawn = sum(
                1 for i, _ in enumerate(column_widths)
                if i not in set(hidden)
            )
            header_specs = [self.__header_color] * drawn

        superior = separators.superior_header_line
        if header_specs:
            superior = paint(superior, header_specs)
        elif border and superior is not None:
            superior = colorize(superior, border)

        inferior = separators.inferior_header_line
        if first_specs:
            inferior = paint(inferior, first_specs)
        elif border and inferior is not None:
            inferior = colorize(inferior, border)

        superior_nh = separators.superior_header_line_no_header
        if first_specs:
            superior_nh = paint(superior_nh, first_specs)
        elif border and superior_nh is not None:
            superior_nh = colorize(superior_nh, border)

        end_line = separators.table_end_line
        if last_specs:
            end_line = paint(end_line, last_specs)
        elif border and end_line is not None:
            end_line = colorize(end_line, border)

        plain_body = separators.table_body_line
        body_template = plain_body
        if border and body_template is not None and not first_specs:
            body_template = colorize(body_template, border)

        painted = HorizontalComposition(
            superior,
            inferior,
            superior_nh,
            body_template if not first_specs else plain_body,
            end_line,
        )

        gap_separator = None
        if plain_body is not None and body_row_count:
            def gap_separator(after_row, _plain=plain_body):
                specs = self.__rule_specs_for_row(
                    after_row, column_titles, column_widths
                )
                return paint_rule_cell_backgrounds(
                    _plain, layout, specs, border
                )

        return painted, gap_separator

    def __regions_with_colors(self):
        """
        Merged regions with an effective colour for this render.

        Explicit ``merge_cells(..., color=...)`` wins. Otherwise, when colour
        output is on, the top-left cell's resolved colour is inherited so
        ``column_colors`` / ``row_colors`` / ``cell_color`` fill the whole
        merge span instead of leaving a dark hole.
        """
        colors_on = self.__colors_active and self.__has_any_color()
        headers = list(self.__headers)
        out = []
        for region in self.__merged_regions:
            if region.color is not None or not colors_on:
                out.append(region)
                continue
            col_name = (
                headers[region.first_column]
                if region.first_column < len(headers) else ''
            )
            try:
                raw = self.__raw_value_at(
                    headers, region.first_column, region.first_row
                )
            except Exception:
                raw = None
            spec = self.__color_for_cell(raw, region.first_row, col_name)
            out.append(region if not spec else region._replace(color=spec))
        return out

    def __get_processed_columns_data(self, header=False, columns_with_i=False):
        if columns_with_i:
            columns_with_headers = self.__processed_columns_with_i.values()
        else:
            columns_with_headers = self.__processed_columns.values()
        for column_w_h in columns_with_headers:
            get = 'header' if header else 'data'
            yield column_w_h[get]

    # +------------------------+ TABLE BODY +------------------------+

    # end +---------------------+ STRING TABLE COMPOSITION +--------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ DATA READING +-------------------------+ start

    # Readers and writers are imported inside each method rather than at
    # module scope: readers.py needs the Table class, so importing it here
    # would be circular, and the optional dependencies must not be touched
    # until the corresponding format is actually used.

    @classmethod
    def from_records(cls, rows, headers=None, parse_numbers=True, **options):
        """
        Build a table from a sequence of rows.

        With no headers, the first row supplies them::

            Table.from_records([['Ann', 30], ['Bob', 41]], headers=['Name', 'Age'])
        """
        from .readers import from_records
        return from_records(cls, rows, headers, parse_numbers, **options)

    @classmethod
    def from_dicts(cls, records, parse_numbers=False, **options):
        """
        Build a table from a sequence of mappings, one per row.

        Columns are the union of every key in first-seen order, so records
        with differing keys still line up::

            Table.from_dicts([{'name': 'Ann'}, {'name': 'Bob', 'age': 41}])
        """
        from .readers import from_dicts
        return from_dicts(cls, records, parse_numbers, **options)

    @classmethod
    def from_csv(cls, source, parse_numbers=True, has_header=True,
                 delimiter=',', encoding='utf-8', dialect=None, quoting=None,
                 quotechar=None, escapechar=None, doublequote=None,
                 lineterminator=None, skipinitialspace=None, strict=None,
                 **options):
        """
        Build a table from a CSV path or open handle.

        Numeric-looking text is converted by default; a column left as strings
        would be left-aligned and look wrong. Pass ``parse_numbers=False`` to
        keep the text exactly as written.

        Dialect extras (``dialect``, ``quoting``, ``quotechar``,
        ``escapechar``, ``doublequote``, ``lineterminator``,
        ``skipinitialspace``, ``strict``) go to ``csv.reader``.
        """
        from .readers import from_csv
        return from_csv(
            cls, source, parse_numbers, has_header, delimiter, encoding,
            dialect=dialect, quoting=quoting, quotechar=quotechar,
            escapechar=escapechar, doublequote=doublequote,
            lineterminator=lineterminator, skipinitialspace=skipinitialspace,
            strict=strict, **options
        )

    @classmethod
    def from_html(cls, source, index=0, parse_numbers=True, encoding='utf-8',
                  **options):
        """
        Build a table from an HTML table element.

        ``source`` may be markup, a path, or an open handle; ``index`` picks
        which table to read from a document containing several. Uses the
        standard library parser, so this needs no dependency.
        """
        from .readers import from_html
        return from_html(cls, source, index, parse_numbers, encoding, **options)

    @classmethod
    def from_pandas(cls, dataframe, include_index=False, **options):
        """
        Build a table from a pandas DataFrame or Series.

        Requires pandas: pip install flexablelib[pandas]
        """
        from .readers import from_pandas
        return from_pandas(cls, dataframe, include_index, **options)

    @classmethod
    def from_excel(cls, path, sheet=None, has_header=True,
                   parse_numbers=False, **options):
        """
        Build a table from a worksheet in an .xlsx file.

        Excel merged ranges are restored as ``merge_cells`` regions.
        Requires openpyxl: pip install flexablelib[excel]
        """
        from .readers import from_excel
        return from_excel(cls, path, sheet, has_header, parse_numbers,
                          **options)

    # end +--------------------------+ DATA READING +---------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ DATA WRITING +------------------------+ start

    # Named colour+style bundles (Spectre / Rich theme spirit).
    THEMES = {
        'plain': {
            'style_name': 'plain',
            'use_colors': False,
            'header_color': None,
            'border_color': None,
            'zebra': None,
        },
        'dark': {
            'style_name': 'rounded',
            'use_colors': True,
            'header_color': 'bold cyan',
            'border_color': 'dim',
            'zebra': 'on #2a2a2a',
        },
        'midnight': {
            'style_name': 'sharp',
            'use_colors': True,
            'header_color': 'bold white',
            'border_color': 'blue',
            'zebra': ('', 'on #1a1a2e'),
        },
        'matrix': {
            'style_name': 'ascii',
            'use_colors': True,
            'header_color': 'bold green',
            'border_color': 'green',
            'zebra': 'dim green',
        },
        'report': {
            'style_name': 'simple_bold',
            'use_colors': True,
            'header_color': 'bold',
            'border_color': None,
            'zebra': None,
        },
        'markdown': {
            'style_name': 'markdown',
            'use_colors': False,
            'header_color': None,
            'border_color': None,
            'zebra': None,
        },
        'ocean': {
            'style_name': 'rounded',
            'use_colors': True,
            'header_color': 'bold #7fdbff',
            'border_color': '#0074d9',
            'zebra': ('', 'on #001f3f'),
        },
        'solarized': {
            'style_name': 'sharp',
            'use_colors': True,
            'header_color': 'bold #268bd2',
            'border_color': '#586e75',
            'zebra': ('', 'on #073642'),
        },
        'neon': {
            'style_name': 'bold_borderline',
            'use_colors': True,
            'header_color': 'bold magenta',
            'border_color': 'cyan',
            'zebra': ('', 'on #1a0033'),
        },
        'mono': {
            'style_name': 'simple',
            'use_colors': True,
            'header_color': 'bold',
            'border_color': 'dim',
            'zebra': 'dim',
        },
        'autumn': {
            'style_name': 'rounded',
            'use_colors': True,
            'header_color': 'bold #d75f00',
            'border_color': '#af5f00',
            'zebra': ('', 'on #3a1f00'),
        },
        'contrast': {
            'style_name': 'ascii',
            'use_colors': True,
            'header_color': 'bold reverse',
            'border_color': 'bold',
            'zebra': ('', 'reverse'),
        },
        'forest': {
            'style_name': 'modern',
            'use_colors': True,
            'header_color': 'bold #87d787',
            'border_color': '#005f00',
            'zebra': ('', 'on #002200'),
        },
        'ember': {
            'style_name': 'bold_borderline',
            'use_colors': True,
            'header_color': 'bold #ffaf00',
            'border_color': '#d70000',
            'zebra': ('', 'on #2a0000'),
        },
        'slate': {
            'style_name': 'psql',
            'use_colors': True,
            'header_color': 'bold #a8a8a8',
            'border_color': '#6c6c6c',
            'zebra': ('', 'on #303030'),
        },
    }

    def apply_theme(self, name):
        """
        Apply a named theme: style plus header/border/zebra colours.

        Themes: ``plain``, ``dark``, ``midnight``, ``matrix``, ``report``,
        ``markdown``, ``ocean``, ``solarized``, ``neon``, ``mono``, ``autumn``,
        ``contrast``, ``forest``, ``ember``, ``slate``. Returns ``self`` for
        chaining. See ``THEMES`` for the full map.
        """
        if name not in self.THEMES:
            raise ValueError(
                'unknown theme {0!r}; choose from {1}'.format(
                    name, ', '.join(sorted(self.THEMES))
                )
            )
        for key, value in self.THEMES[name].items():
            setattr(self, key, value)
        return self

    def stream(self, rows, append=False):
        """
        Yield table lines as rows arrive (beautifultable-style streaming).

        Column widths are frozen from headers, existing rows, and any
        ``column_min_width`` / ``column_max_width`` before iteration starts
        (beautifultable contract: set floors ahead of time if later rows are
        wider than the seed). Cells that exceed those widths follow
        ``overflow`` (truncate/wrap).

        Requires headers (or existing columns) so widths can be measured
        before the first streamed row.

        Parameters
        ----------
        rows : iterable
            Yields one row (list/tuple) at a time.
        append : bool
            If True, streamed rows are added to this table when the
            generator is exhausted. If False (default), this table is
            left unchanged; streaming mutates only an internal copy.

        Yields
        ------
        str
            Individual composed lines (borders, header, body, caption).
        """
        if not self.__headers and self.__real_column_count == 0:
            raise ValueError(
                'stream() needs headers or existing columns so widths '
                'can be frozen before rows arrive'
            )

        work = self.__display_clone(include_rows=True)
        # Measure natural widths, then pin min=max so later rows cannot
        # widen the table (beautifultable stream contract).
        work.compose()
        widths = list(work.__column_widths_as_list)
        # Honour caller floors already set on self.
        if self.__column_min_width is not None:
            for i, header in enumerate(work.headers):
                floor = self.__lookup_width_map(
                    self.__column_min_width, header, i
                )
                if floor is not None:
                    widths[i] = max(widths[i], int(floor))
        if self.__column_max_width is not None:
            for i, header in enumerate(work.headers):
                ceil = self.__lookup_width_map(
                    self.__column_max_width, header, i
                )
                if ceil is not None:
                    widths[i] = min(widths[i], int(ceil))
        work.column_min_width = list(widths)
        work.column_max_width = list(widths)

        n_close = self.__stream_closing_line_count(work, widths)
        before = work.compose().splitlines()
        open_part = before[:-n_close] if n_close else before
        for line in open_part:
            yield line

        streamed = []
        for row in rows:
            row = list(row)
            streamed.append(row)
            work.add_row(row)
            after = work.compose().splitlines()
            open_after = after[:-n_close] if n_close else after
            open_before_len = len(before) - n_close if n_close else len(before)
            for line in open_after[open_before_len:]:
                yield line
            before = after

        for line in (before[-n_close:] if n_close else []):
            yield line

        if append and streamed:
            for row in streamed:
                self.add_row(row)

    def __stream_closing_line_count(self, template, widths):
        """
        How many trailing lines are shared by empty-body and one-row tables
        (bottom border + caption). Those are deferred until stream ends.
        """
        empty = self.__display_clone(include_rows=False)
        one = self.__display_clone(include_rows=False)
        empty.column_min_width = list(widths)
        empty.column_max_width = list(widths)
        one.column_min_width = list(widths)
        one.column_max_width = list(widths)
        placeholders = ['' for _ in empty.headers] or ['']
        if empty.headers:
            one.add_row(placeholders)
        else:
            return 0
        la = empty.compose().splitlines()
        lb = one.compose().splitlines()
        n = 0
        while n < len(la) and n < len(lb) and la[-(n + 1)] == lb[-(n + 1)]:
            n += 1
        return n

    def __display_clone(self, include_rows=True):
        """Shallow display copy used by stream/paginate helpers."""
        headers = list(self.headers)
        rows = []
        if include_rows:
            for row_i in range(self.__real_row_count):
                row = []
                for header in headers:
                    col = self.__columns.get(header, [])
                    if row_i < len(col):
                        cell = col[row_i]
                        if isinstance(cell, ValuePlacer):
                            cell = self.__missing_value
                        row.append(cell)
                    else:
                        row.append(self.__missing_value)
                rows.append(row)
        out = type(self).from_records(
            rows,
            headers=headers if headers else None,
            style_name=self.style_name,
            missing_val=self.__missing_value,
        )
        for attr in (
            'title', 'caption', 'show_headers', 'show_index', 'header_color',
            'border_color', 'use_colors', 'zebra', 'footer_rows', 'footer_color',
            'cell_padding', 'overflow', 'auto_wrap', 'valign', 'col_valign',
            'panel', 'shadow', 'col_alignment', 'header_align', 'max_width',
            'table_align', 'hide_columns', 'index_title', 'roman_index',
            'number_columns', 'strip_cells', 'hrules', 'vrules',
            'index_start', 'index_step',
        ):
            try:
                setattr(out, attr, getattr(self, attr))
            except Exception:
                pass
        return out

    def __lookup_width_map(self, spec, header, index):
        """Resolve column_min/max_width entry for one column."""
        if spec is None:
            return None
        if isinstance(spec, dict):
            if header in spec:
                return spec[header]
            return spec.get(index)
        if is_some_instance(spec, list, tuple):
            if index < len(spec):
                return spec[index]
            return None
        return spec

    def transpose(self, **options):
        """
        Return a new table with rows and columns swapped (display rotate).

        The first column of the result is the original header names; remaining
        columns are ``row0`` … ``rowN`` holding the original cells. Style and
        most display options are copied when not overridden in ``options``.
        """
        headers = list(self.headers)
        # Pull raw stored rows (not the composed display copy).
        rows = []
        n = self.row_count
        for row_i in range(n):
            row = []
            for header in headers:
                col = self.__columns.get(header, [])
                row.append(col[row_i] if row_i < len(col) else self.__missing_value)
            rows.append(row)
        new_headers = ['field'] + ['row{}'.format(i) for i in range(len(rows))]
        new_rows = []
        for col_i, header in enumerate(headers):
            new_rows.append(
                [header] + [rows[r][col_i] if col_i < len(rows[r]) else ''
                            for r in range(len(rows))]
            )
        style = options.pop('style_name', self.style_name)
        out = type(self).from_records(
            new_rows, headers=new_headers, style_name=style, **options
        )
        return out

    def rotate(self, **options):
        """Alias of :meth:`transpose` (tabled naming)."""
        return self.transpose(**options)

    def paginate(self, page_length=20, freeze_header=True, page_label=False):
        """
        Split the table into composed string pages of ``page_length`` body rows.

        Each page is a full table. With ``freeze_header`` True (default),
        headers repeat on every page; with False, only the first page shows
        them. ``page_label`` adds ``page k/n`` to each page title.
        Returns a list of strings. ``page_length`` must be >= 1.
        Inspired by PrettyTable ``paginate`` / go-pretty.
        """
        page_length = int(page_length)
        if page_length < 1:
            raise ValueError('page_length must be >= 1')
        headers = list(self.headers)
        n = self.row_count
        if n == 0:
            return [self.compose()]
        total_pages = (n + page_length - 1) // page_length
        pages = []
        for page_num, start in enumerate(range(0, n, page_length), start=1):
            end = min(start + page_length, n)
            slice_rows = []
            for row_i in range(start, end):
                row = []
                for header in headers:
                    col = self.__columns.get(header, [])
                    row.append(col[row_i] if row_i < len(col) else self.__missing_value)
                slice_rows.append(row)
            page = type(self).from_records(
                slice_rows, headers=headers, style_name=self.style_name,
                missing_val=self.__missing_value,
            )
            # Copy common display settings so pages look like the parent.
            for attr in (
                'title', 'caption', 'show_headers', 'show_index', 'header_color',
                'border_color', 'use_colors', 'zebra', 'footer_rows', 'footer_color',
                'cell_padding', 'overflow', 'auto_wrap', 'valign', 'col_valign',
                'panel', 'shadow', 'col_alignment', 'header_align', 'max_width',
                'column_min_width', 'column_max_width', 'table_align',
                'hide_columns', 'index_title', 'roman_index', 'number_columns',
                'strip_cells', 'hrules', 'vrules', 'index_start', 'index_step',
            ):
                try:
                    setattr(page, attr, getattr(self, attr))
                except Exception:
                    pass
            if not freeze_header and page_num > 1:
                page.show_headers = False
            if page_label:
                label = 'page {0}/{1}'.format(page_num, total_pages)
                existing = page.title
                page.title = (
                    '{0} ({1})'.format(existing, label) if existing else label
                )
            if self.__cell_colors:
                # Remap absolute row indexes into the page's local indexes.
                remapped = {}
                for (r, c), spec in self.__cell_colors.items():
                    if isinstance(r, int) and start <= r < end:
                        remapped[(r - start, c)] = spec
                if remapped:
                    page.cell_colors = remapped
            pages.append(page.compose())
        return pages


    @classmethod
    def from_markdown(cls, source, parse_numbers=True, **options):
        """
        Build a table from a GitHub-flavoured Markdown pipe table string.

        Round-trips with :meth:`to_markdown`. Alignment row (``---``, ``:--``)
        is detected and discarded; column align codes are applied when present.
        """
        from .readers import from_markdown
        return from_markdown(cls, source, parse_numbers=parse_numbers, **options)

    def to_records(self, include_index=False):
        """The table as a list of dicts, one per row."""
        from .writers import to_records
        return to_records(self, include_index)

    def to_csv(self, target=None, include_index=False, delimiter=',',
               encoding='utf-8', dialect=None, quoting=None, quotechar=None,
               escapechar=None, doublequote=None, lineterminator=None,
               skipinitialspace=None, strict=None):
        """
        Write the table as CSV.

        Returns the CSV as a string when no target is given. Colour is
        stripped -- escape sequences would corrupt the fields.

        Dialect extras are forwarded to ``csv.writer``.
        """
        from .writers import to_csv
        return to_csv(
            self, target, include_index, delimiter, encoding,
            dialect=dialect, quoting=quoting, quotechar=quotechar,
            escapechar=escapechar, doublequote=doublequote,
            lineterminator=lineterminator, skipinitialspace=skipinitialspace,
            strict=strict,
        )

    def to_markdown(self, include_index=False, align=True):
        """
        Render as a GitHub-flavoured Markdown table.

        Pipes inside cells are escaped, since an unescaped one would split the
        cell and shift every column after it.
        """
        from .writers import to_markdown
        return to_markdown(self, include_index, align)

    def to_rst(self, include_index=False):
        """Render as a reStructuredText grid table."""
        from .writers import to_rst
        return to_rst(self, include_index)

    def to_asciidoc(self, include_index=False):
        """Render as an AsciiDoc table (``|===`` style)."""
        from .writers import to_asciidoc
        return to_asciidoc(self, include_index)

    def to_latex(self, include_index=False):
        """Render as a LaTeX ``tabular`` environment."""
        from .writers import to_latex
        return to_latex(self, include_index)

    def to_html(self, target=None, title='Table', paginate=25,
                include_index=False, searchable=True, encoding='utf-8'):
        """
        Write a self-contained HTML page with sorting, filtering and paging.

        Everything is inline -- no external requests -- so the file works
        offline and from a file:// URL. ``paginate`` is the page size; 0 puts
        every row on one page. Returns the markup when no target is given.
        """
        from .writers import to_html
        return to_html(self, target, title, paginate, include_index,
                       searchable, encoding)

    def _repr_html_(self):
        """
        Compact HTML table for Jupyter and other rich frontends.

        Unlike :meth:`to_html`, this is a bare ``<table>`` with no page chrome,
        script, or pagination -- what a notebook cell expects from
        ``_repr_html_``.
        """
        from .writers import to_simple_html
        return to_simple_html(self)

    def to_excel(self, path, sheet_name='Sheet1', include_index=False,
                 autofit=True, freeze_header=True):
        """
        Write an .xlsx workbook.

        Numbers are written as numbers so the spreadsheet can compute with
        them. ``merged_regions`` become real Excel merges. Requires openpyxl:
        pip install flexablelib[excel]
        """
        from .writers import to_excel
        return to_excel(self, path, sheet_name, include_index, autofit,
                        freeze_header)

    # end +--------------------------+ DATA READING +---------------------------+ end
    # +-----------------------------------------------------------------------------+


if __name__ == '__main__':
    print('This is not supposed to be shown!')
