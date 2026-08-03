"""
Type inference, alignment and column widths (``columns.py``).

Most columns are measured as "the longest cell". Float columns are not: they
are measured as *two* widths, the digits left of the decimal point and the
digits right of it, so that every point in the column lands on the same axis.
That two-sided measurement is what the bulk of this file covers.
"""

import pytest

from prettyTables import columns
from prettyTables.columns import (
    ALIGNMENTS_PER_TYPE,
    TYPE_NAMES,
    _column_widths,
    _typify_column,
)
from prettyTables.options import COLUMN_ALIGNS

# Module-level privates, fetched by string so class-body name mangling can
# never rewrite the lookup.
_get_column_type = getattr(columns, '__get_column_type')
_get_float_widths = getattr(columns, '__get_float_widths')
_get_sides_widths = getattr(columns, '__get_sides_widths')
_float_col_total_width = getattr(columns, '__float_col_total_width')
_get_float_column_width = getattr(columns, '__get_float_column_width')
_get_single_column_width = getattr(columns, '__get_single_column_width')


# +-------------------------------------------------------------------------+
# Type inference and the alignment it selects
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('type_names, expected', [
    (['str', 'int'], TYPE_NAMES.str_),
    (['ValuePlacer', 'int'], TYPE_NAMES.int_),
    (['float', 'int'], TYPE_NAMES.float_),
    (['NoneType', 'int'], TYPE_NAMES.str_),
    (['ValuePlacer', 'bool'], TYPE_NAMES.bool_),
    (['NoneType', 'ValuePlacer'], TYPE_NAMES.none_type_),
])
def test_column_type_resolution(type_names, expected):
    assert _get_column_type(type_names) == expected


def test_typify_column_reports_cell_types_column_type_and_alignment():
    cell_types, column_type, alignment = _typify_column(['Jade', 'John'])

    assert cell_types == ('str', 'str')
    assert column_type == TYPE_NAMES.str_
    assert alignment == COLUMN_ALIGNS.left


def test_typify_column_treats_an_empty_string_as_a_missing_value():
    cell_types, column_type, _ = _typify_column(['', 'Jade'])

    assert cell_types == ('NoneType', 'str')
    assert column_type == TYPE_NAMES.str_


def test_typify_column_mixing_floats_and_ints_is_a_float_column():
    _, column_type, alignment = _typify_column([9.651, 3, 245.7])

    assert column_type == TYPE_NAMES.float_
    assert alignment == COLUMN_ALIGNS.float


def test_typify_column_as_index_forces_int():
    cell_types, column_type, alignment = _typify_column(
        ['whatever', object()],
        index_column=True,
    )

    assert cell_types == ('int', 'int')
    assert column_type == TYPE_NAMES.int_
    assert alignment == COLUMN_ALIGNS.right


def test_alignments_per_type_follows_typographic_convention():
    assert ALIGNMENTS_PER_TYPE[TYPE_NAMES.str_] == COLUMN_ALIGNS.left
    assert ALIGNMENTS_PER_TYPE[TYPE_NAMES.int_] == COLUMN_ALIGNS.right
    assert ALIGNMENTS_PER_TYPE[TYPE_NAMES.float_] == COLUMN_ALIGNS.float
    assert ALIGNMENTS_PER_TYPE[TYPE_NAMES.bool_] == COLUMN_ALIGNS.right


# +-------------------------------------------------------------------------+
# __get_float_widths: the three widths of one cell
# +-------------------------------------------------------------------------+

def test_get_float_widths_splits_a_float_into_left_point_right():
    sides, reduce = _get_float_widths(
        cell='12.4325',
        is_float=True,
        head_size=8,
        max_widths_of_sides=[15, 0, 0],
    )

    assert sides == (2, 1, 4)
    assert reduce is False


def test_get_float_widths_puts_an_int_entirely_on_the_left_side():
    sides, reduce = _get_float_widths(
        cell='321111',
        is_float=False,
        head_size=8,
        max_widths_of_sides=[3, 1, 4],
    )

    assert sides == (6, 0, 0)
    assert reduce is False


def test_get_float_widths_flags_a_reduction_for_an_oversized_non_number():
    """
    A missing value wider than anything measured so far takes the whole width
    on the left side and asks the caller to give back the space the decimal
    part would have needed.
    """
    sides, reduce = _get_float_widths(
        cell='missing_value__',
        is_float=None,
        head_size=8,
        max_widths_of_sides=[],
    )

    assert sides == (15, 0, 0)
    assert reduce is True


def test_get_float_widths_ignores_a_non_number_that_already_fits():
    sides, reduce = _get_float_widths(
        cell='missing_value__',
        is_float=None,
        head_size=8,
        max_widths_of_sides=[15, 0, 0],
    )

    assert sides == ()
    assert reduce is False


# +-------------------------------------------------------------------------+
# __get_sides_widths: accumulating the maximum of each side
# +-------------------------------------------------------------------------+

def test_get_sides_widths_seeds_the_maximums_from_the_first_float():
    max_len_of_sides = []

    reduce = _get_sides_widths(
        cell=9.651,
        max_len_of_sides=max_len_of_sides,
        head_size=7,
        will_reduce=False,
    )

    assert max_len_of_sides == [1, 1, 3]
    assert reduce is False


def test_get_sides_widths_grows_only_the_side_that_got_bigger():
    max_len_of_sides = [1, 1, 3]

    _get_sides_widths(
        cell=245.7,
        max_len_of_sides=max_len_of_sides,
        head_size=7,
        will_reduce=False,
    )

    # 245 is wider on the left, but .7 is narrower on the right, so only the
    # left maximum moves.
    assert max_len_of_sides == [3, 1, 3]


def test_get_sides_widths_leaves_an_int_alone_when_it_already_fits():
    max_len_of_sides = [3, 1, 3]

    reduce = _get_sides_widths(
        cell=3,
        max_len_of_sides=max_len_of_sides,
        head_size=7,
        will_reduce=False,
    )

    assert max_len_of_sides == [3, 1, 3]
    assert reduce is False


def test_get_sides_widths_gives_the_decimal_space_back_after_an_oversized_cell():
    """
    The reduce handshake, in two steps.

    A missing value wider than the floats takes the whole column on the left
    side and returns ``True``. The next cell is then measured with
    ``will_reduce=True``, which subtracts the point plus the decimal digits
    from the left maximum -- otherwise that much blank space would be left
    hanging on the left of every row -- and reports ``None`` to switch the
    flag back off.
    """
    max_len_of_sides = [1, 1, 3]

    reduce = _get_sides_widths(
        cell='missing_value__',
        max_len_of_sides=max_len_of_sides,
        head_size=7,
        will_reduce=False,
    )
    assert max_len_of_sides == [15, 1, 3]
    assert reduce is True

    reduce = _get_sides_widths(
        cell=12.4325,
        max_len_of_sides=max_len_of_sides,
        head_size=7,
        will_reduce=True,
    )
    # 15 - (4 decimals + 1 point) = 10 on the left; the right side grows to 4.
    assert max_len_of_sides == [10, 1, 4]
    assert reduce is None


# +-------------------------------------------------------------------------+
# __float_col_total_width: the header can widen the left side
# +-------------------------------------------------------------------------+

def test_float_col_total_width_is_the_sum_of_the_sides():
    max_len_of_sides = [3, 1, 3]

    assert _float_col_total_width(max_len_of_sides, head_size=7) == 7
    assert max_len_of_sides == [3, 1, 3]


def test_float_col_total_width_pads_the_left_side_to_reach_the_header():
    """
    When the header is wider than the number, the slack goes to the *left*
    side, which keeps the decimal points aligned and pushes the column right.
    """
    max_len_of_sides = [2, 1, 2]

    total = _float_col_total_width(max_len_of_sides, head_size=7)

    assert total == 7
    assert max_len_of_sides == [4, 1, 2]  # mutated in place


def test_float_col_total_width_does_not_shrink_for_a_narrow_header():
    max_len_of_sides = [3, 1, 4]

    assert _float_col_total_width(max_len_of_sides, head_size=7) == 8
    assert max_len_of_sides == [3, 1, 4]


def test_float_col_total_width_with_hidden_headers():
    max_len_of_sides = [2, 1, 2]

    assert _float_col_total_width(max_len_of_sides, head_size=0) == 5
    assert max_len_of_sides == [2, 1, 2]


# +-------------------------------------------------------------------------+
# Whole-column measurement
# +-------------------------------------------------------------------------+

def test_get_single_column_width_reports_header_and_body_separately():
    head_size, body_size = _get_single_column_width(
        {'header': 'header1', 'data': ('data1', 'data2')},
        show_headers=True,
    )

    assert (head_size, body_size) == (7, 5)


def test_get_single_column_width_measures_a_wrapped_cell_by_its_longest_line():
    head_size, body_size = _get_single_column_width(
        {'header': ('Na', 'me'), 'data': (('Piotr', 'Baltimore'), 'Sam')},
        show_headers=True,
    )

    assert (head_size, body_size) == (2, 9)


def test_get_single_column_width_skips_the_header_when_hidden():
    head_size, body_size = _get_single_column_width(
        {'header': 'a very long header', 'data': ('ab',)},
        show_headers=False,
    )

    assert (head_size, body_size) == (0, 2)


def test_get_float_column_width_measures_the_readme_results_column():
    head_size, total, sides = _get_float_column_width(
        {'header': 'Results', 'data': (9.651, 3, 245.7)},
        show_headers=True,
    )

    assert head_size == 7
    assert sides == (3, 1, 3)   # 245 | . | 651
    assert total == 7


def test_get_float_column_width_of_a_column_with_a_wrapped_cell():
    head_size, total, sides = _get_float_column_width(
        {'header': ('Test', 'Results'), 'data': (9.651, 3, 245.7, (3.5, ''), 0.6519)},
        show_headers=True,
    )

    assert head_size == 7
    assert sides == (3, 1, 4)   # 245 | . | 6519
    assert total == 8           # wider than the 7-char header


def test_column_widths_returns_widths_and_the_float_sides():
    widths, float_widths = _column_widths(
        processed_columns={
            'header1': {'header': 'header1', 'data': ['data1', 'data2']},
            'header2': {'header': 'header2', 'data': [1.2, 12.43]},
        },
        column_type_names={'header1': TYPE_NAMES.str_, 'header2': TYPE_NAMES.float_},
        show_headers=True,
    )

    assert widths == [7, 7]
    # The float sides sum to 7 too: the header slack went to the left side.
    assert float_widths == {'header2': (4, 1, 2)}


def test_column_widths_without_float_columns_reports_no_float_sides():
    widths, float_widths = _column_widths(
        processed_columns={
            'Name': {'header': 'Name', 'data': ['Jade', 'John']},
            'Age': {'header': 'Age', 'data': [20, 30]},
        },
        column_type_names={'Name': TYPE_NAMES.str_, 'Age': TYPE_NAMES.int_},
        show_headers=True,
    )

    assert widths == [4, 3]
    assert float_widths is None


def test_column_widths_ignores_headers_when_they_are_hidden():
    widths, _ = _column_widths(
        processed_columns={
            'a very long header': {'header': 'a very long header', 'data': ['ab']},
        },
        column_type_names={'a very long header': TYPE_NAMES.str_},
        show_headers=False,
    )

    assert widths == [2]
