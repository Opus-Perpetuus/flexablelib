"""
Print formatted tabular data in different styles
"""

# FORMATION OF THE TABLE
#
# Main Class.
# Here the whole table is formed

from .style_compositions import __style_compositions as style_catalogue, HorizontalComposition, TableComposition
from .columns import _column_sizes, _typify_column, _align_columns, _align_headers
from .table_strings import _get_separators, _get_data_rows, DataRows
from .utils import get_window_size, is_multi_row
from .options import NONE_VALUE_REPLACEMENT, DEFAULT_STYLE
from .cells import _wrap_cells


def _zip_columns(columns, headers=False):
    if headers:
        row = tuple(map(lambda x: x, columns))
        if is_multi_row(row):
            return tuple(zip(*row))
        else:
            return row
    else:
        half_checked_rows = zip(*columns)
        sub_zipped = tuple(map(lambda s_row: tuple(zip(*s_row)) if is_multi_row(s_row) else s_row,
                               half_checked_rows))
        return sub_zipped

class Table(object):
    """
    TABLE
    =====

    Makes a table out of tabular data

    ---------------
    POSSIBLE STYLES
    ---------------
    ### PLAIN
    >>> from prettyTables import Table
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
                 missing_val='', str_align=None, int_align=None, float_align=None,
                 bool_align=None, table_align=None, col_alignment=None, leading_zeros=0,
                 header_style=None):
        # +------------------------+ PARAMETERS +------------------------+
        self.__missing_val = missing_val
        self.__str_align = str_align
        self.__int_align = int_align
        self.__float_align = float_align
        self.__bool_align = bool_align
        self.__table_align = table_align
        self.__column_align = col_alignment
        self.__add_index = False
        self.__roman_index = False
        self.__i_start = 0
        self.__i_step = 1
        self.__parse_numbers = True
        self.__parse_str_numbers = False
        self.__window_size = get_window_size()
        self.__adjust_to_window = True
        self.__auto_wrap_text = False
        self.__expand_body_to = 'r'
        self.__expand_header_to = 'r'
        self.__leading_zeros = leading_zeros
        self.__float_spaces = 2
        self.__format_exponential = True
        # +--------------------------+ STYLE +---------------------------+
        # HEADER STYLES: None, l, u, t, c
        #   None: unmodified
        #   l: lower case
        #   u: upper case
        #   t: title
        #   c: capitalized
        self.__header_style = header_style
        self.__show_margin = True
        self.__show_empty_columns = True
        self.__show_empty_rows = True
        self.__generic_column_name = 'column'
        self.__style_name = style_name
        # +------------------+ TABLE CHARACTERISTICS +-------------------+
        self.__show_headers = True
        self.__table_height = 0
        self.__table_width = 0
        self.__real_row_count = 0
        self.__real_column_count = 0
        self.__line_spacing = 0
        self.__cell_types = {}
        self.__column_types = {}
        self.__column_types_as_list = []
        self.__column_widths = {}
        self.__column_widths_as_list = []
        self.__table_alignment = 'l'
        self.__column_alignments = {}
        self.__column_alignments_as_list = []
        self.__row_alignments = {}
        self.__row_alignments_as_list = []
        self.__cells_alignment = []
        # +------------------------+ TABLE BODY +------------------------+
        self.__columns = columns if columns is not None else {}
        self.__headers = headers if headers is not None else []
        self.__rows = []
        self.__processed_columns = {}
        self.__processed_headers = []
        self.__processed_rows = []
        # +-----------------------+ INIT ACTIONS +-----------------------+
        if rows is not None:
            [self.add_row(row) for row in rows]

    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ METHODS +---------------------------+ start

    def __str__(self) -> str:
        return self.compose()
    
    
    def __repr__(self) -> str:
        return self.compose()

    # end +-----------------------------+ METHODS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+


    # TODO add the rest of getters
    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ GETTERS +---------------------------+ start

    @property
    def columns(self):
        return self.__columns

    @property
    def headers(self):
        return self.__headers
        
    @property
    def rows(self):
        return self.__rows

    @property
    def style_name(self):
        return self.__checked_style_name

    @property
    def missing_val(self):
        return self.__missing_val

    @property
    def str_align(self):
        return self.__str_align

    @property
    def int_align(self):
        return self.__int_align

    @property
    def float_align(self):
        return self.__float_align

    @property
    def bool_align(self):
        return self.__float_align

    @property
    def table_align(self):
        return self.__table_align

    @property
    def col_alignment(self):
        return self.__column_align

    @property
    def leading_zeros(self):
        return self.__leading_zeros

    @property
    def style_composition(self) -> TableComposition:
        return self.__style_composition

    @property
    def empty_rows_i(self):
        return self.__empty_row_indexes

    @property
    def empty_columns_i(self):
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
        This counts the rows of the table conditioned by
        the show_empty_rows property.

        If it is set to True, empty rows are counted.
        If it is set to False, empty rows are not counted.
        """
        return self.__row_count

    @property
    def column_count(self):
        """
        This counts the rows of the table conditioned by
        the show_empty_columns property.

        If it is set to True, empty columns are counted.
        If it is set to False, empty columns are not counted.
        """
        return self.__column_count


    @property
    def internal_row_count(self):
        return self.__real_row_count


    @property
    def internal_column_count(self):
        return self.__real_column_count

    # +----------------------+ SHOW GETTERS +------------------------+

    @property
    def show_headers(self):
        return self.__show_headers
    
    @property    
    def show_margin(self):
        return self.__show_margin

    @property
    def show_empty_rows(self):
        return self.__show_empty_rows

    @property
    def show_empty_columns(self):
        return self.__show_empty_columns

    # end +-----------------------------+ GETTERS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+
    
    
    # TODO add the rest of setters
    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ SETTERS +---------------------------+ start

    @columns.setter
    def columns(self, value: dict):
        self.__columns = {} if value is None else value

    @headers.setter
    def headers(self, value: list):
        self.__headers = [] if value is None else value

    @style_name.setter
    def style_name(self, value):
        self.__style_name = value

    @missing_val.setter
    def missing_val(self, value):
        self.__missing_val = value

    @str_align.setter
    def str_align(self, value):
        self.__str_align = value

    @int_align.setter
    def int_align(self, value):
        self.__int_align = value

    @float_align.setter
    def float_align(self, value):
        self.__float_align = value

    @bool_align.setter
    def bool_align(self, value):
        self.__float_align = value

    @table_align.setter
    def table_align(self, value):
        self.__table_align = value

    @col_alignment.setter
    def col_alignment(self, value):
        self.__column_align = value

    @leading_zeros.setter
    def leading_zeros(self, value):
        """
        leading_zeros = 5

        ```
        00001
        00012
        01235
        00023
        00000
        ```
        """
        self.__leading_zeros = value

    # +----------------------+ SHOW SETTERS +------------------------+

    @show_headers.setter
    def show_headers(self, value: bool):
        self.__show_headers = value

    @show_margin.setter
    def show_margin(self, value: bool):
        self.__show_margin = value

    @show_empty_rows.setter
    def show_empty_rows(self, value: bool):
        self.__show_empty_rows = value

    @show_empty_columns.setter
    def show_empty_columns(self, value: bool):
        self.__show_empty_columns = value

    # end +-----------------------------+ SETTERS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+


    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ PRIVATE PROPERTIES +--------------------------+ start

    @property
    def __style_composition(self):
        return style_catalogue.__getattribute__(self.__checked_style_name)

    @property
    def __checked_style_name(self):
        if self.__style_name in self.__possible_styles:
            return self.__style_name
        else:
            return DEFAULT_STYLE

    @property
    def __empty_row_indexes(self):  # FIX make empty row indexes work with missing val (only works with None)
        empty_rows = []
        for i, row in enumerate(self.__rows):
            if row.count(self.__missing_val) == len(row):
                empty_rows.append(i)
        return empty_rows

    @property
    def __empty_column_indexes(self):  # FIX make empty column indexes work with missing val (doesn't seem to work)
        none_type_columns = []
        for i, type_name in enumerate(self.__column_types_as_list):
            if type_name == 'NoneType':
                none_type_columns.append(i)
        return none_type_columns

    @property
    def __possible_styles(self):
        return style_catalogue._fields

    @property
    def __row_count(self):
        checked_real_row_count = self.__real_row_count
        if self.__show_empty_rows:
            return checked_real_row_count
        else:
            updated_row_count = checked_real_row_count - len(self.__empty_row_indexes)
            return updated_row_count

    @property
    def __column_count(self):
        if self.__show_empty_columns:
            return self.__real_column_count
        else:
            updated_column_count = self.__real_column_count - len(self.__empty_column_indexes)
            return updated_column_count

    # end +-----------------------+ PRIVATE PROPERTIES +------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ COLUMN ADDING +------------------------+ start

    def add_column(self, header=None, data=None):
        """
        Add a column to the table.
        Can be left empty to add an empty column.

        ``header``: The title of the column. If not provided, 
        gets filled with a generic name.
        
        ``data``: Data provided as any iterable. If not 
        provided, column gets filled with the missing value.
        If the column is greater than the table s_row count, 
        new rows gets added, and the new spaces in other
        columns filled with missing value, but if smaller, 
        the remaining spaces of the column get those instead.
        """
        column_header = self.__add_column_header(header)
        self.__add_column_data(data, column_header)
        self.__adjust_columns_to_row_count()
        self.__check_existent_rows_vs_row_count()
        self.__transpose_column_to_rows(data)
        self.__adjust_rows_to_column_count(False, 1)

    def __add_column_header(self, header):
        if header is None:
            header = f'{self.__generic_column_name} {len(self.__headers) + 1}'
        else:
            header = str(header)
            if header in self.__headers:
                header = f'{header} {self.__headers.count(header) + 1}'
        self.__headers.append(header)
        self.__column_widths[header] = 0
        self.__column_types[header] = None
        self.__column_alignments[header] = ''
        self.__cell_types[header] = []
        self.__columns[header] = []

        return header

    def __add_column_data(self, data, column_header):
        self.__real_column_count += 1
        if data is not None:
            if len(data) > self.__real_row_count:
                self.__real_row_count += len(data) - self.__real_row_count
            self.__columns[column_header] += data

        return column_header, self.__columns[column_header]

    def __adjust_columns_to_row_count(self, rows_added_before=False):
        for header, column_body in self.__columns.items():
            if len(column_body) < self.__real_row_count:
                difference = self.__real_row_count - len(column_body)
                if rows_added_before:
                    [self.__columns[header].insert(0, self.__missing_val) for _ in range(difference)]
                else:
                    self.__columns[header] += [self.__missing_val for _ in range(difference)]

    def __transpose_column_to_rows(self, data):
        for column_i in range(self.__real_column_count):
            for row_i in range(self.__real_row_count):
                if data is None:
                    self.__distribute_empty_column_to_rows(row_i, column_i)
                else:
                    self.__distribute_column_to_rows(row_i, column_i, data)

    def __distribute_empty_column_to_rows(self, row_i, column_i):
        if column_i + 1 == self.__real_column_count:  # +1 because column count starts from 1
            self.__rows[row_i].append(self.__missing_val)
        else:
            self.__fill_row_missing_values_from_column(row_i, column_i)

    def __distribute_column_to_rows(self, row_i, column_i, data):
        if column_i + 1 == self.__real_column_count:  # +1 because column count starts from 1
            try:
                self.__rows[row_i].append(data[row_i])
            except IndexError:
                self.__rows[row_i].append(self.__missing_val)
                pass
        else:
            self.__fill_row_missing_values_from_column(row_i, column_i)

    def __fill_row_missing_values_from_column(self, row_i, column_i):
        try:
            self.__rows[row_i][column_i]
        except IndexError:
            self.__rows[row_i].append(self.__missing_val)

    # end +--------------------------+ COLUMN ADDING +--------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ ROW ADDING +--------------------------+ start

    def add_row(self, data=None):
        """
        Add a s_row to the table. Can be left empty to add
        an empty s_row.

        ``data``: Data provided as any iterable
        """
        added_to_column_count = self.__add_row_data(data)
        add_headers = True if added_to_column_count is not None else False
        self.__adjust_rows_to_column_count(add_headers, added_to_column_count)
        self.__transpose_row_to_columns(data)
        self.__adjust_columns_to_row_count(rows_added_before=True)

    def __add_row_data(self, data):
        self.__rows.append([])
        self.__real_row_count += 1
        if data is None:
            [self.__rows[-1].append(self.__missing_val) for _ in range(self.__real_column_count)]
        else:
            return self.__check_data_and_fill_last_row(data)

    def __adjust_rows_to_column_count(self, there_is_headers_to_add, count_of_new_headers):
        if there_is_headers_to_add:
            [self.__add_column_header(None) for _ in range(count_of_new_headers)]
        for row_i in range(self.__real_row_count):
            if len(self.__rows[row_i]) < self.__real_column_count:
                difference = self.__real_column_count - len(self.__rows[row_i])
                [self.__rows[row_i].append(self.__missing_val) for _ in range(difference)]

    def __transpose_row_to_columns(self, data):
        column_headers = tuple(self.__columns.keys())
        for column_i in range(self.__real_column_count):
            if data is None:
                self.__fil_column_from_empty_row(column_headers, column_i)
            else:
                self.__fill_column_from_row(column_headers, column_i, data)

    def __check_existent_rows_vs_row_count(self):
        if len(self.__rows) < self.__real_row_count:
            rows_to_add = self.__real_row_count - len(self.__rows)
            [self.__rows.append([]) for _ in range(rows_to_add)]

    def __check_data_and_fill_last_row(self, data):
        added_columns_to_count = None
        if len(data) > self.__real_column_count:
            added_columns_to_count = len(data) - self.__real_column_count
            self.__real_column_count += added_columns_to_count
        for column_i in range(self.__real_column_count):
            try:
                self.__rows[-1].append(data[column_i])
            except IndexError:
                self.__rows[-1].append(self.__missing_val)
        return added_columns_to_count

    def __fil_column_from_empty_row(self, column_headers, column_i):
        try:
            self.__columns[column_headers[column_i]].append(self.__missing_val)
        except IndexError:
            pass

    def __fill_column_from_row(self, column_headers, column_i, data):
        try:
            self.__columns[column_headers[column_i]].append(data[column_i])
        except IndexError:
            self.__fil_column_from_empty_row(column_headers, column_i)

    # end +---------------------------+ ROW ADDING +----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------+ STRING TABLE COMPOSITION +------------------+ start

    # +----------------------+ NUMBER PARSING +----------------------+
    def __parse_numbers(self):
        pass

    def __parse_float(self):
        pass

    def __parse_int_boolean(self):
        pass

    def __parse_exponentials(self):
        pass

    def __parse_bytes(self):
        pass

    def __parse_escape_codes(self):
        pass

    # +------------------------+ TABLE BODY +------------------------+

    def compose(self):
        if len(self.__columns) != 0:
            self.__typify_table()
            self.__parse_data()  # TODO add parsing
            self.__wrap_data()
            self.__get_column_widths()

        return self.__form_string()
    

    # TODO create index adding function
    # def __add_indexes(self):
    #     self.columns
        

    def __typify_table(self):
        for header, column_content in self.__columns.items():
            cell_types, column_type, column_alignment = _typify_column(column_content)
            self.__column_types[header] = column_type
            self.__cell_types[header] = cell_types
            self.__column_alignments[header] = column_alignment
            self.__column_alignments_as_list.append(column_alignment)
            self.__column_types_as_list.append(column_type)

    def __get_column_widths(self):
        sizes = _column_sizes(self.__processed_columns, show_headers=self.__show_headers)
        self.__column_widths_as_list = sizes
        for i, column in enumerate(self.__columns.items()):
            header, _ = column
            self.__column_widths[header] = sizes[i]

    def __wrap_data(self):
        rows = self.__rows
        headers = self.__headers
        processed_headers, processed_rows = _wrap_cells(headers, rows)
        processed_columns, transformed_headers = _wrap_cells(processed_headers, processed_rows, columns=True)
        self.__processed_headers = processed_headers
        self.__processed_rows = processed_rows
        for i, column in enumerate(self.__columns.items()):
            header, data = column
            self.__processed_columns[header] = {
                'header': transformed_headers[i],
                'data': processed_columns[i]
            }

    def __parse_data(self):
        pass

    def __form_string(self):
        # Data from column dict is put in tuples
        unaligned_columns = self.__get_processed_columns_data()
        unaligned_header = self.__get_processed_columns_data(header=True)

        # Header and body __rows get aligned
        aligned_header = _align_headers(self.__style_composition,
                                        unaligned_header,
                                        self.__column_alignments_as_list,
                                        self.__column_widths_as_list)
        aligned_header = _zip_columns(aligned_header, headers=True)
        aligned_columns = _align_columns(self.__style_composition,
                                         unaligned_columns,
                                         self.__column_alignments_as_list,
                                         self.__column_widths_as_list)
        aligned_columns = _zip_columns(aligned_columns)

        # String separators and data __rows are joined
        separators: HorizontalComposition = _get_separators(
            self.__style_composition,
            tuple(self.__column_widths.values())
        )
        data_rows: DataRows = _get_data_rows(self.__style_composition, aligned_header, aligned_columns)

        # Table string is formed
        header_superior = ''.join([separators.superior_header_line, '\n']) if (
                separators.superior_header_line is not None
        ) else NONE_VALUE_REPLACEMENT
        no_header_superior = separators.superior_header_line_no_header
        header_inferior = ''.join(['\n', separators.inferior_header_line]) if (
                separators.inferior_header_line is not None
        ) else NONE_VALUE_REPLACEMENT
        body_line = ''.join(['\n', separators.table_body_line]) if (
                separators.table_body_line is not None
        ) else NONE_VALUE_REPLACEMENT
        end_line = separators.table_end_line

        header_row = data_rows.header_row
        body_rows = data_rows.body_rows

        if self.__show_headers:
            superior_row = ''.join([header_superior, header_row, header_inferior])
        else:
            superior_row = no_header_superior

        if superior_row is None and end_line is not None:
            table_string = '\n'.join([f'{body_line}\n'.join(body_rows), end_line])
        elif end_line is None and superior_row is not None:
            table_string = '\n'.join([superior_row, f'{body_line}\n'.join(body_rows)])
        elif superior_row is None and end_line is None:
            table_string = f'{body_line}\n'.join(body_rows)
        else:
            table_string = '\n'.join([superior_row, f'{body_line}\n'.join(body_rows), end_line])

        return table_string

    def __get_processed_columns_data(self, header=False):
        columns_with_headers = self.__processed_columns.values()
        for column_w_h in columns_with_headers:
            get = 'header' if header else 'data'
            yield column_w_h[get]

    # +------------------------+ TABLE BODY +------------------------+

    # end +---------------------+ STRING TABLE COMPOSITION +--------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ DATA READING +-------------------------+ start

    def __read_pandas_dataframe(self):
        pass

    def __read_csv_file(self):
        pass

    def __read_html_table(self):
        pass

    def __read_text_file(self):
        pass

    # end +--------------------------+ DATA READING +---------------------------+ end
    # +-----------------------------------------------------------------------------+


if __name__ == '__main__':
    print('This is not supposed to be shown!')
