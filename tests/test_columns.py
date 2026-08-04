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
_split_float_cell = getattr(columns, '__split_float_cell')
_measure_float_cell = getattr(columns, '__measure_float_cell')
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
# __split_float_cell: classifying one cell of a float column
# +-------------------------------------------------------------------------+

def test_split_float_cell_splits_a_float_into_left_point_right():
    assert _split_float_cell('12.4325') == (2, 1, 4)


def test_split_float_cell_puts_an_int_entirely_on_the_left_side():
    assert _split_float_cell('321111') == (6, 0, 0)


def test_split_float_cell_handles_a_number_that_starts_at_the_point():
    assert _split_float_cell('.5') == (0, 1, 1)


def test_split_float_cell_counts_the_minus_sign():
    assert _split_float_cell('-1.25') == (2, 1, 2)


def test_split_float_cell_reads_an_exponential():
    """
    Python prints small and large floats this way whether or not anyone
    asked. The exponent rides on the right of the point, so 1.5e-05 lines up
    with 2.25 on their points.
    """
    assert _split_float_cell('1.5e-05') == (1, 1, 5)


def test_split_float_cell_handles_an_exponential_with_no_point():
    """
    ``1e+16`` is a float with nothing on the decimal axis, so all of it sits
    on the left and it claims no point of its own.
    """
    assert _split_float_cell('1e+16') == (5, 0, 0)


def test_split_float_cell_returns_none_for_anything_that_is_not_a_number():
    assert _split_float_cell('missing_value__') is None
    assert _split_float_cell('12abc') is None
    assert _split_float_cell('1.2.3') is None


# +-------------------------------------------------------------------------+
# __measure_float_cell: numbers and text are accumulated apart
# +-------------------------------------------------------------------------+

def test_measure_float_cell_grows_only_the_side_that_got_bigger():
    sides, texts = [1, 1, 3], []

    _measure_float_cell(245.7, sides, texts)

    # 245 is wider on the left, but .7 is narrower on the right, so only the
    # left maximum moves.
    assert sides == [3, 1, 3]
    assert texts == []


def test_measure_float_cell_keeps_text_out_of_the_numeric_sides():
    """
    The heart of issue #23. A missing value is not a number, so it must never
    land in the left-hand slot -- otherwise the point and the decimals get
    added on top of it and the column ends up wider than any cell in it.
    """
    sides, texts = [1, 1, 3], []

    _measure_float_cell('missing_value__', sides, texts)

    assert sides == [1, 1, 3]
    assert texts == [15]


def test_measure_float_cell_folds_a_wrapped_cell_line_by_line():
    sides, texts = [0, 0, 0], []

    _measure_float_cell((3.5, ''), sides, texts)

    # '' matches the integer filter, so it contributes a zero-wide left side.
    assert sides == [1, 1, 1]
    assert texts == []


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


def test_get_float_column_width_is_never_wider_than_its_widest_cell():
    """
    Issue #23. The missing value is 15 wide and the numbers need 3 + 1 + 3, so
    the column is 15 -- not 15 plus the point and the decimals.
    """
    _, total, sides = _get_float_column_width(
        {'header': 'value', 'data': (9.651, 3, 245.7, 'missing_value__')},
        show_headers=True,
    )

    assert total == 15
    assert sum(sides) == total
    assert sides == (11, 1, 3)   # the decimal axis sits at 11


@pytest.mark.parametrize('data', [
    (9.651, 3, 245.7, 'missing_value__'),
    ('missing_value__', 9.651, 3, 245.7),
    (9.651, 'missing_value__', 3, 245.7),
])
def test_get_float_column_width_does_not_depend_on_the_row_order(data):
    """
    The old measurement corrected for an oversized text cell only on the
    *next* number it saw, so moving that cell changed the column width.
    """
    _, total, sides = _get_float_column_width(
        {'header': 'value', 'data': data},
        show_headers=True,
    )

    assert (total, sides) == (15, (11, 1, 3))


def test_get_float_column_width_skips_hidden_rows():
    _, total, _ = _get_float_column_width(
        {'header': 'value', 'data': (9.651, 3, 245.7, 'missing_value__')},
        show_headers=True,
        skip_rows=frozenset({3}),
    )

    assert total == 7


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
