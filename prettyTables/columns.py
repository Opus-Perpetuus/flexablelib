from .cells import (
    _center_cell, 
    _ljust_cell, 
    _rjust_cell,
    _fljust_cell,
    _add_cell_spacing
)
from .style_compositions import TableComposition
from .fast import visible_width
from .utils import (
    is_some_instance,
    IndexCounter,
    ValuePlacer
)
from .options import (
    DEFAULT_FILL_CHAR, 
    FLT_FILTER,
    INT_FILTER,
    EXP_FILTER,
    COLUMN_ALIGNS
)

from typing import (
    Any, 
    Dict, 
    List, 
    Tuple, 
    Union, 
    Generator
)
from collections import namedtuple

TypeNames = namedtuple(
    'TypeNames',
    [
        'bool_',
        'str_',
        'int_',
        'float_',
        'bytes_',
        'none_type_',
        'index_counter_',
        'value_placer_',
    ]
)


TYPE_NAMES = TypeNames(
    bool_=bool.__name__,
    str_=str.__name__,
    int_=int.__name__,
    float_=float.__name__,
    bytes_=bytes.__name__,
    none_type_=type(None).__name__,
    index_counter_=IndexCounter.__name__,
    value_placer_=ValuePlacer.__name__,
)


FLOAT_SEPARATOR = '.'


# Positions inside the ``(left, point, right)`` triple that describes how a
# float column is laid out around its decimal axis.
LEFT_SIDE_WIDTH = 0
POINT_WIDTH = 1
RIGHT_SIDE_WIDTH = 2


ALIGNMENTS_PER_TYPE = {
    TYPE_NAMES.bool_: COLUMN_ALIGNS.right,
    TYPE_NAMES.str_: COLUMN_ALIGNS.left,
    TYPE_NAMES.int_: COLUMN_ALIGNS.right,
    TYPE_NAMES.float_: COLUMN_ALIGNS.float,
    TYPE_NAMES.bytes_: COLUMN_ALIGNS.bytes,
    TYPE_NAMES.none_type_: COLUMN_ALIGNS.left,
}


CAN_WRAP_TYPES = [
    TYPE_NAMES.str_,
    TYPE_NAMES.none_type_,
    TYPE_NAMES.value_placer_
]


def __check_for_types_in_column(column_types: list, 
                                accepted_types: list
                               ) -> bool:
    """
    Compares two list of type names.
    
    Example::

        __check_for_types_in_column(
            column_types=['str', 'int'], 
            accepted_types=['str', 'int']
        ) -> True
        __check_for_types_in_column(
            column_types=['str', 'int', 'float'], 
            accepted_types=['str', 'int']
        ) -> False
    """
    for type_ in column_types:
        if type_ not in accepted_types:
            return False
                
    return True


def __is_str_column(column_types: list) -> bool:
    """
    Receives a list of type names and returns True if
    all of the names are one of those::
    
        'bool',         'str',         'int', 
        'float',        'bytes',       'NoneType',
        'IndexCounter'  'ValuePlacer' 
    """
    test = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=list(TYPE_NAMES)
    )
    return test


def __is_byte_column(column_types: list) -> bool:
    """
    Receives a list of type names and returns True if
    all of the names are one of those:: 
    
        'bytes', 'ValuePlacer' 
    """
    test = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.bytes_,
            TYPE_NAMES.value_placer_
        ]
    )
    return test


def __is_int_column(column_types: list) -> bool:
    """
    Receives a list of type names and returns True if
    all of the names are one of those::
    
        'int', 'bool', 'ValuePlacer', 'IndexCounter' 
    """
    test = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.int_,
            TYPE_NAMES.bool_,
            TYPE_NAMES.value_placer_,
            TYPE_NAMES.index_counter_
        ]
    )
    return test
    
    
def __is_float_column(column_types: list) -> bool:
    """
    Receives a list of type names and returns True if
    all of the names are one of those:: 
    
        'int', 'float', 'ValuePlacer'
    """
    test = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.int_,
            TYPE_NAMES.float_,
            TYPE_NAMES.value_placer_,
        ]
    )
    return test


def __is_bool_column(column_types: bool) -> bool:
    """
    Receives a list of type names and returns True if
    all of the names are one of those:: 

        'bool', 'ValuePlacer'
    """
    test = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.bool_,
            TYPE_NAMES.value_placer_
        ]
    )
    return test


def __is_none_type(column_types: list) -> bool:
    """
    Receives a list of type names and returns True if
    all of the names are one of those::

        'NoneType', 'ValuePlacer'
    """
    test = __check_for_types_in_column(
        column_types=column_types,
        accepted_types=[
            TYPE_NAMES.none_type_,
            TYPE_NAMES.value_placer_
        ]
    )
    return test


def __get_column_type(column_types):
    """
    Will return the type of the column depending
    on what combination of types it has.
    
    Examples::
    
        __get_column_type(['str', 'int']) -> 'str'
        __get_column_type(['ValuePlacer', 'int']) -> 'int'
        __get_column_type(['float', 'int']) -> 'float'
        __get_column_type(['NoneType', 'int']) -> 'str'
        __get_column_type(['ValuePlacer', 'bool']) -> 'bool'
    """
    if __is_none_type(column_types):
        return TYPE_NAMES.none_type_
    # if __is_byte_column(column_types):
    #     return TYPE_NAMES.bytes_
    if __is_bool_column(column_types):
        return TYPE_NAMES.bool_
    if __is_int_column(column_types):
        return TYPE_NAMES.int_
    if __is_float_column(column_types):
        return TYPE_NAMES.float_
    if __is_str_column(column_types):
        return TYPE_NAMES.str_
    else:
        return TYPE_NAMES.none_type_
    
    
def __header_width(header: Union[Any, list, tuple]) -> int:
    """
    Returns the width of the header.
    """
    if is_some_instance(header, tuple, list):
        # If it's wrapped, will be a tuple or list. To get
        # the size, will get first the widths of all the sub-rows
        # and the the max of them.
        return (
            max([visible_width(str(sub_row)) for sub_row in header])
        )
    else:
        # If it's not wrapped, will be a string, so will only
        # get it's width.
        return visible_width(str(header))


def __get_single_column_width(column: dict,
                             show_headers: bool,
                             skip_rows: frozenset = frozenset()
                            ) -> Tuple[int, int]:
    """
    Will return the max size of the data in the column
    and the header size.
    
    Should receive a column with one of the following structures::

        # WITH WRAPPED HEADER AND DATA
        {
            'header': (('wrapped', 'header'), ...), 
            'data': ('data', ('wrapped', 'cell'), ...)
        }
        
        # NO WRAPPER HEADER OR DATA
        {
            'header': 'header1', 
            'data': ('data', ...)
        }
    
    Returns::

        (header_size: int, body_max_size: int)
    """
    head_size = 0
    body_sizes = []
    if show_headers:
        # If headers will show, get them.
        header = column['header']
        head_size += __header_width(header)
    for row_i, row in enumerate(column['data']):
        # Rows that will not be rendered must not be measured. A hidden empty
        # row still carries the missing value, and letting it through widened
        # the column to fit text nobody would ever see -- issue #22.
        if row_i in skip_rows:
            continue
        # The same principle as the header is applied here but for each cell.
        # Every length will be added to the body_sizes list.
        if is_some_instance(row, tuple, list):
            body_sizes.append(
                max([visible_width(str(sub_row)) for sub_row in row])
            )
        else:
            body_sizes.append(visible_width(str(row)))
    
    # And once more will get the max to get the length of the column.
    # Every row may have been skipped, in which case the body contributes
    # nothing and the header alone decides the width.
    body_max_size = max(body_sizes) if body_sizes else 0
            
    return head_size, body_max_size

def __split_float_cell(cell: Any) -> Union[Tuple[int, int, int], None]:
    """
    Measure one numeric cell of a float column, by side of the point.

    Returns ``(left, point, right)`` for a float, ``(width, 0, 0)`` for an
    integer, and ``None`` for anything that is not a number -- a missing
    value, or text that landed in a numeric column.

    Examples::

        __split_float_cell('123.45')  -> (3, 1, 2)
        __split_float_cell('321111')  -> (6, 0, 0)
        __split_float_cell('missing') -> None
    """
    text = str(cell)

    if FLT_FILTER(text) is not None:
        left, point, right = text.partition(FLOAT_SEPARATOR)
        return (
            visible_width(left),
            len(point),
            visible_width(right),
        )

    if INT_FILTER(text) is not None:
        # An integer aligns against the left side of the floats, so all of
        # its width belongs there and it contributes no point and no
        # decimals.
        return visible_width(text), 0, 0

    return None


def __measure_float_cell(cell: Any,
                         numeric_sides: List[int],
                         text_widths: List[int],
                        ) -> None:
    """
    Fold one cell into the running measurement of a float column.

    Numbers widen ``numeric_sides``; anything else is recorded in
    ``text_widths`` and measured whole. Wrapped cells (lists or tuples of
    lines) are folded in line by line.
    """
    if is_some_instance(cell, tuple, list):
        for sub_cell in cell:
            __measure_float_cell(sub_cell, numeric_sides, text_widths)
        return

    sides = __split_float_cell(cell)
    if sides is None:
        text_widths.append(visible_width(str(cell)))
        return

    left, point, right = sides
    numeric_sides[LEFT_SIDE_WIDTH] = max(numeric_sides[LEFT_SIDE_WIDTH], left)
    numeric_sides[POINT_WIDTH] = max(numeric_sides[POINT_WIDTH], point)
    numeric_sides[RIGHT_SIDE_WIDTH] = max(numeric_sides[RIGHT_SIDE_WIDTH], right)


def __get_float_column_width(column: dict,
                             show_headers: bool,
                             skip_rows: frozenset = frozenset()
                            ) -> Tuple[int, int, Tuple[int, int, int]]:
    """
    Will get the header size, body size and the max size of the sides
    of a float column.

    The numbers and the text are measured **separately** and only then
    combined. A float column is as wide as the widest of three things: the
    numbers laid out on their shared decimal axis, the widest non-numeric
    cell, and the header. Whichever wins, the decimal axis is then pushed
    right so the widest number's last decimal lands on the column's right
    edge.

    Measuring them together is what issue #23 was: a 15-character missing
    value went into the left-hand slot, and the point and the decimals were
    then added on top of it, making the column four characters wider than
    anything in it. A correction existed but only fired for numbers that
    came *after* the wide text, so the width depended on the row order.

    Returns::

        (head_size: int, total_width: int, sides: (left, point, right))

    Example::

        __get_float_column_width(
            column={
                'header': ('Test', 'Results'),
                'data': (9.651, 3, 245.7, (3.5, ''), '?')
            },
            show_headers=False
        )

    Results in::

        (0, 7, (3, 1, 3))

    """
    head_size = 0
    if show_headers:
        # If headers will show, get them.
        header = column['header']
        head_size += __header_width(header)

    numeric_sides = [0, 0, 0]
    text_widths = []

    for row_i, row in enumerate(column['data']):
        # Hidden rows must not contribute to the decimal-side widths either.
        if row_i in skip_rows:
            continue
        __measure_float_cell(row, numeric_sides, text_widths)

    point = numeric_sides[POINT_WIDTH]
    right = numeric_sides[RIGHT_SIDE_WIDTH]
    numeric_width = numeric_sides[LEFT_SIDE_WIDTH] + point + right

    total_width = max(
        numeric_width,
        max(text_widths) if text_widths else 0,
        head_size,
    )

    # Everything the numbers do not need goes to the left of the point, so
    # the decimal axis sits as far right as the column allows and text cells
    # right-align flush with the widest number.
    sides = (total_width - point - right, point, right)

    return head_size, total_width, sides


FloatExtents = namedtuple(
    'FloatExtents',
    ['left', 'point', 'right', 'text']
)


def _is_numeric_cell(cell: Any) -> bool:
    """
    Whether a cell holds something that aligns on the decimal axis.

    A wrapped cell never does: it is text that had to be broken over
    several lines.
    """
    if is_some_instance(cell, tuple, list):
        return False
    return __split_float_cell(cell) is not None


def _float_extents(cells: Union[list, tuple],
                   skip_rows: frozenset = frozenset()
                  ) -> FloatExtents:
    """
    The raw extents of a float column, before any padding is applied.

    ``left``/``point``/``right`` are what the *numbers* need around the
    decimal axis and ``text`` is the widest non-numeric cell. Unlike the
    sides reported by ``__get_float_column_width``, none of these has been
    stretched to fill the column, which is what makes them the right input
    for deciding how far a column may be narrowed: the integer digits are
    the one part that cannot be given up.

    Example::

        _float_extents([9.651, 3, 245.7, 'missing_value__'])
        -> FloatExtents(left=3, point=1, right=3, text=15)
    """
    numeric_sides = [0, 0, 0]
    text_widths = []

    for row_i, cell in enumerate(cells):
        if row_i in skip_rows:
            continue
        __measure_float_cell(cell, numeric_sides, text_widths)

    return FloatExtents(
        left=numeric_sides[LEFT_SIDE_WIDTH],
        point=numeric_sides[POINT_WIDTH],
        right=numeric_sides[RIGHT_SIDE_WIDTH],
        text=max(text_widths) if text_widths else 0,
    )


def _round_float_cell(cell: Any, decimals: int) -> Any:
    """
    Re-render one numeric cell with ``decimals`` digits after the point.

    Anything that is not a number is returned untouched -- a missing value
    cannot be rounded, and neither can a wrapped cell. Integers are left
    alone as well: they carry no decimals to give up, and padding them out
    to some would only widen the column this is trying to narrow.

    Examples::

        _round_float_cell(9.651, 2)   -> '9.65'
        _round_float_cell(245.7, 0)   -> '246'
        _round_float_cell(3, 2)       -> 3
        _round_float_cell('n/a', 2)   -> 'n/a'
    """
    text = str(cell)
    if FLT_FILTER(text) is None or EXP_FILTER(text) is not None:
        # An exponential says how big a number is, not how precise it is.
        # Rounding 1.5e-05 to two decimals writes 0.00, which is a different
        # claim entirely.
        return cell

    if decimals <= 0:
        # No point either: a column with nothing after the point should not
        # keep paying a character for one.
        return format(float(text), '.0f')

    return format(float(text), '.{0}f'.format(decimals))


def _column_widths(processed_columns: Dict[str, tuple],
                  column_type_names: dict,
                  show_headers: bool,
                  skip_rows: frozenset = frozenset()
                 ) -> Tuple[tuple, Union[None, dict]]:
    """
    Will return the widths of the columns. Float columns widths
    are calculated by side of the point.
    
    Returns::

        (widths: tuple, float_column_widths: None | dict)
    
    Example::

        _column_widths(
            processed_columns={
                {'header': 'header1', 'data': ['data1', 'data2']},
                {'header': 'header2', 'data': [1.2, 12.43]}
            },
            column_type_names={'header1': 'str', 'header2': 'float'},
        )
    
    Results in::

        ((7, 7), {'header2': (4, 1, 2)})
    """
    # TODO add support for coloring codes

    head_sizes = []
    body_sizes = []
    float_column_widths = None
    for header, column in processed_columns.items():
        if column_type_names[header] == TYPE_NAMES.float_:
            
            # If it's a float column, get the body size, 
            # header size and float sizes.
            head_size, body_size, decimal_sides = __get_float_column_width(
                column,
                show_headers,
                skip_rows
            )
            
            # Save header and body size separately to prevent 
            # the header size # from being added to the 
            # calculation in case of turning off the headers.
            head_sizes.append(head_size)
            body_sizes.append(body_size)
            
            # Save float column sizes as a dict.
            try:
                float_column_widths[header] = decimal_sides
            except TypeError:
                float_column_widths = {header: decimal_sides}
                
        else:
            
            # If it's not a float column, get the body and header size,
            # and save them separately.
            head_size, body_size = __get_single_column_width(
                column,
                show_headers,
                skip_rows
            )
            head_sizes.append(head_size)
            body_sizes.append(body_size)

    if show_headers:
        # Get the max width between the header and body sizes if the header
        # is set to show.
        widths = list(map(lambda x, y: max(x, y), head_sizes, body_sizes))
        
    else:
        # Only the body sizes if the header is not set to show.    
        widths = body_sizes

    return widths, float_column_widths


def _typify_column(column: Union[list, tuple], 
                   index_column=False,
                  ) -> Tuple[Tuple[str], str, str]:  
    """
    Get the types of the column and it's alignments.
    
    Uses the ``__name__`` property to get the type class' name
    traversing the column and using the ``type`` class do so::

        type(data).__name__
    
    Returns::

        (identified_types: tuple, column_type: str, column_alignment: str)
    """
    identified_types = []

    for row in column:
        if index_column:
            # If it is the index column, it will be took in count as int.
            identified_types.append(int.__name__)
        elif row != '':
            # Get the type as long as is not an empty string.
            identified_types.append(type(row).__name__)
        else:
            # If it's an empty string, should be considered as None.
            identified_types.append(type(None).__name__)

    # Get the type of the column.
    column_type = __get_column_type(identified_types)
    # Using the column type, get the alignment.
    column_alignment = ALIGNMENTS_PER_TYPE[column_type]
    identified_types = tuple(identified_types)

    return identified_types, column_type, column_alignment


def __align_single_cell(cell: Union[Any, List[Any], Tuple[Any]],
                        col_width: int, 
                        to_where: str, 
                        margin: int, 
                        float_column_sizes: list=None
                       ) -> Union[str, Tuple[str]]:
    """
    Will add space to the cell to align it.
    
    Returns::

        new_cell: str | tuple
    
    Examples::

        __align_single_cell(
            cell="data1",
            col_width=7,
            to_where="l",
            margin=1,
            float_column_sizes=None
        )
        __align_single_cell(
            cell="missing_value__",
            col_width=15,
            to_where="f",
            margin=1,
            float_column_sizes=(10, 1, 4)
        )
        __align_single_cell(
            cell=12.4325,
            col_width=15,
            to_where="f",
            margin=1,
            float_column_sizes=(10, 1, 4)
        )
        __align_single_cell(
            cell=111.22,
            col_width=15,
            to_where="f",
            margin=1,
            float_column_sizes=(10, 1, 4)
        )
    
    Results in::
    
        ' data1   '
        ' missing_value__ '
        '         12.4325 '
        '        111.22   '
    """
    new_cell = cell
    if to_where == COLUMN_ALIGNS.left:
        # Adjust the cell to the left.
        new_cell = _ljust_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR
        )
    elif to_where == COLUMN_ALIGNS.center:
        # Adjust the cell to the center.
        new_cell = _center_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR
        )
    elif to_where == COLUMN_ALIGNS.right:
        # Adjust the cell to the right.
        new_cell = _rjust_cell(
            cell, 
            col_width, 
            DEFAULT_FILL_CHAR
        )
    elif to_where == COLUMN_ALIGNS.float:
        # Adjust the cell as a float.
        new_cell = _fljust_cell(
            cell, 
            col_width, 
            float_column_sizes,
            DEFAULT_FILL_CHAR, 
        )
    # Add the margin (if any) to the cell.
    new_cell = _add_cell_spacing(new_cell, margin, margin, 0)
    
    if is_some_instance(new_cell, tuple, list):
        return tuple(new_cell)
    else:
        return new_cell


def __align_one_column(column: Union[list, tuple],
                       column_i: int, 
                       col_alignments: list, 
                       col_widths: list, 
                       margin: int, 
                       float_column_sizes: dict = None
                      ) -> Generator[str, None, None]:
    """
    Aligns a single row of a column.
    
    Yields::
    
        aligned_column: Generator[str]
    """
    aligned_column = []
    to_where = col_alignments[column_i]
    col_width = col_widths[column_i]
    for cell in column:
        aligned_column.append(
            __align_single_cell(
                cell, 
                col_width, 
                to_where, 
                margin,
                float_column_sizes
            )
        )

    yield tuple(aligned_column)


def _align_columns(style_composition: TableComposition, 
                   columns: Union[List[Union[list, tuple]], Tuple[Union[list, tuple]]],
                   headers: Union[list, tuple],
                   col_alignments: List[str], 
                   col_widths: List[int],
                   empty_columns_i: List[int], 
                   show_empty: bool, 
                   float_cols_sizes: dict
                  ) -> Generator[str, None, None]:
    """
    Aligns the columns and adds margin to the cells.
    """
    # The margin that the selected style has.
    margin = style_composition.margin
    
    for column_i, column in enumerate(columns):
        
        # Align only the columns that are shown.
        if (not show_empty and column_i not in empty_columns_i
        ) or show_empty:

            # Get the header of the column.
            header = headers[column_i]
            
            # Try to get the float sizes (if it is a float column).
            try:
                float_column_sizes = float_cols_sizes[header]
            except KeyError:
                float_column_sizes = None
                
            # Align the column.
            yield from __align_one_column(
                column, 
                column_i, 
                col_alignments, 
                col_widths, 
                margin,
                float_column_sizes
            )
            
        else:
            continue
    
        
def __align_one_header(column: Union[str, list, tuple], 
                       col_width: int, 
                       to_where: str, 
                       margin: int, 
                       float_column_sizes: dict
                      ) -> Union[str, Tuple[str]]:
    """
    Aligns a single cell of the header.
    """
    # Check if it's a wrapped cell.
    if is_some_instance(column, tuple, list):
        # Apply to each sub-row.
        yield tuple(map(
            lambda cell: __align_single_cell(
                cell, 
                col_width, 
                to_where, 
                margin,
                float_column_sizes
            ),
            column
        ))
    else:
        # Apply to the cell.
        yield __align_single_cell(column, col_width, to_where, margin)


def _align_headers(style_composition: TableComposition, 
                   headers: Union[list, tuple],
                   col_alignments: List[str], 
                   col_widths: List[int],
                   empty_columns_i: List[int], 
                   show_empty: bool,
                   float_cols_sizes: dict):
    """
    Will align the headers using the provided column alignments.
    """
    
    # The margin that the selected style has.
    margin = style_composition.margin
    
    for column_i, column in enumerate(headers):
        # Get the alignment of the current column.
        to_where = col_alignments[column_i]
        
        # Get the width that the current column should have.
        col_width = col_widths[column_i]
        
        # Get the column name to try to get the float sizes (in case of the
        # column a float column).
        if is_some_instance(column, tuple, list):
            # If it's wrapped, it will come splitted
            col_name = ''.join(column)
        else:
            col_name = column
        try:
            float_column_sizes = float_cols_sizes[col_name]
        except KeyError:
            float_column_sizes = None
            
        # Only align the headers if its column is shown.
        if (not show_empty and column_i not in empty_columns_i
        ) or show_empty:
            yield from __align_one_header(
                column, 
                col_width, 
                to_where, 
                margin,
                float_column_sizes
            )
        else:
            continue
             


if __name__ == '__main__':
    print('Hey! This is not to be executed.')
