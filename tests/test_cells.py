"""
Cell-level padding, justification, wrapping and transposition (``cells.py``).

The interesting part of this module is the pair ``_wrap_rows`` /
``_zip_wrapped_rows``: a cell containing a newline becomes several printed
rows, with the neighbouring columns blank-padded on the extra lines. That is
what turns ``'Piotr\\nBaltimore'`` into two physical rows in the README.
"""

import pytest

from prettyTables import cells
from prettyTables.cells import (
    _add_cell_spacing,
    _center_cell,
    _fljust_cell,
    _ljust_cell,
    _rjust_cell,
    _wrap_rows,
    _zip_wrapped_rows,
    fljust,
)

# Module-level privates. Fetched with getattr and a string literal so that the
# lookup can never be rewritten by class-body name mangling, whatever shape a
# future test takes.
_wrap_cell = getattr(cells, '__wrap_cell')
_wrap_single_row = getattr(cells, '__wrap_single_row')
_zip_sub_rows = getattr(cells, '__zip_sub_rows')


# +-------------------------------------------------------------------------+
# Spacing and justification primitives
# +-------------------------------------------------------------------------+

def test_add_cell_spacing_pads_both_sides():
    assert _add_cell_spacing('a', 1, 3, 0) == ' a   '


def test_add_cell_spacing_with_placeholder_ignores_the_content():
    # A non-zero placeholder_size replaces the content with blanks entirely.
    assert _add_cell_spacing('', 1, 3, 1) == '     '


def test_add_cell_spacing_on_empty_cell_is_just_the_margins():
    assert _add_cell_spacing('', 1, 3, 0) == '    '


def test_add_cell_spacing_on_a_wrapped_cell_returns_a_list():
    # The docstring claims a tuple; the implementation returns the list it
    # built. Pinned as-is so a future cleanup is a deliberate decision.
    assert _add_cell_spacing(['a', 'b'], 1, 3, 0) == [' a   ', ' b   ']


def test_ljust_cell_on_a_plain_cell():
    assert _ljust_cell('a', 3, '-') == 'a--'


def test_ljust_cell_on_a_wrapped_cell_returns_a_tuple():
    assert _ljust_cell(['a', 'b'], 3, '-') == ('a--', 'b--')


def test_rjust_cell_on_a_wrapped_cell_returns_a_tuple():
    assert _rjust_cell(['a', 'b'], 3, '-') == ('--a', '--b')


def test_center_cell_on_a_wrapped_cell_returns_a_tuple():
    assert _center_cell(['a', 'b'], 3, '-') == ('-a-', '-b-')


def test_justification_coerces_non_strings():
    assert _ljust_cell(12, 4, '-') == '12--'
    assert _rjust_cell(None, 6, '-') == '--None'


# +-------------------------------------------------------------------------+
# Float justification: everything lines up on the decimal point
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('number, expected', [
    ('1.23', '--1.23---'),
    ('1.2', '--1.2----'),
    ('.00321', '---.00321'),
])
def test_fljust_aligns_on_the_point(number, expected):
    assert fljust(number, [3, 5], '-') == expected


def test_fljust_puts_every_point_at_the_same_index():
    sides = [3, 5]
    justified = [fljust(n, sides, '-') for n in ('1.23', '1.2', '.00321')]
    point_indexes = {value.index('.') for value in justified}
    assert point_indexes == {3}
    assert {len(value) for value in justified} == {9}


def test_fljust_cell_aligns_ints_with_the_integer_side_of_the_floats():
    # '5' has no point, so it is pushed left of the shared decimal axis and
    # the space the point would occupy is given back to the right side.
    assert _fljust_cell('5', 9, [3, 1, 5], '-') == '--5------'


def test_fljust_cell_right_aligns_anything_that_is_neither_float_nor_int():
    assert _fljust_cell('?', 9, [3, 1, 5], '-') == '--------?'


def test_fljust_cell_on_a_wrapped_cell_aligns_every_part():
    assert _fljust_cell(['Nothing', 'here'], 9, [3, 1, 5], '-') == (
        '--Nothing',
        '-----here',
    )


def test_fljust_cell_keeps_floats_ints_and_blanks_on_one_axis():
    """
    The three shapes a float column can hold, measured together.

    ``''`` matches INT_FILTER (the regex allows an empty match), so a missing
    value in a float column is padded like an int rather than right-aligned.
    """
    sides = [3, 1, 4]
    rendered = [_fljust_cell(value, 8, sides) for value in ('9.651', '245.7', '3', '')]

    assert rendered[0] == '  9.651 '
    assert rendered[1] == '245.7   '
    assert rendered[2] == '  3     '
    assert rendered[3] == '        '
    assert {len(value) for value in rendered} == {8}
    # Both real floats put their point at the same index.
    assert rendered[0].index('.') == rendered[1].index('.') == 3
    # The int sits immediately left of that axis.
    assert rendered[2][2] == '3' and rendered[2][3] == ' '


# +-------------------------------------------------------------------------+
# Wrapping: a newline in a cell becomes extra sub-rows
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('cell, expected', [
    ('a', ['a']),
    ('a\nb', ['a', 'b']),
    ('', ['']),
    (123, [123]),
    (None, [None]),
])
def test_wrap_cell_splits_only_strings(cell, expected):
    assert _wrap_cell(cell) == expected


def test_wrap_single_row_pads_the_columns_that_did_not_wrap():
    # 'b\nc' produces a second sub-row; column 0 gets a blank on that line.
    assert _wrap_single_row(['a', 'b\nc']) == [['a', 'b'], ['', 'c']]


def test_wrap_single_row_without_newlines_yields_one_sub_row():
    assert _wrap_single_row(['c', 'd']) == [['c', 'd']]


def test_wrap_rows_wraps_headers_and_data():
    wrapped_headers, wrapped_data = _wrap_rows(
        headers=['a', 'b\nc'],
        data=[['a', 'b\nc'], ['c', 'd']],
    )

    assert wrapped_headers == [['a', 'b'], ['', 'c']]
    assert wrapped_data == [
        [['a', 'b'], ['', 'c']],  # wrapped: two sub-rows
        [['c', 'd']],             # not wrapped: one sub-row
    ]


def test_wrap_rows_returns_none_headers_when_there_are_none():
    wrapped_headers, wrapped_data = _wrap_rows(headers=None, data=[['a', 'b']])

    assert wrapped_headers is None
    assert wrapped_data == [[['a', 'b']]]


def test_wrap_rows_keeps_non_string_cells_untouched():
    _, wrapped_data = _wrap_rows(headers=['h'], data=[[20], [9.651]])

    assert wrapped_data == [[[20]], [[9.651]]]


# +-------------------------------------------------------------------------+
# Transposition: sub-rows become columns
# +-------------------------------------------------------------------------+

def test_zip_sub_rows_transposes_several_sub_rows():
    assert _zip_sub_rows([['a', 'b'], ['c', 'd']]) == (('a', 'c'), ('b', 'd'))


def test_zip_sub_rows_returns_the_single_sub_row_unchanged():
    # Returns row[0] as-is, so a list stays a list. The docstring shows a
    # tuple; the implementation does not convert.
    assert _zip_sub_rows([['a', 'b']]) == ['a', 'b']


def test_zip_wrapped_rows_turns_rows_into_columns():
    wrapped_headers, wrapped_rows = _wrap_rows(
        headers=['a', 'b'],
        data=[['Data', 'In a row'], ['More', 'data']],
    )
    columns, headers = _zip_wrapped_rows(wrapped_headers, wrapped_rows)

    assert headers == ['a', 'b']
    assert columns == (('Data', 'More'), ('In a row', 'data'))


def test_zip_wrapped_rows_nests_the_wrapped_cell_inside_its_column():
    """
    The README's ``Piotr\\nBaltimore`` case, end to end.

    The multi-line cell survives transposition as a *tuple inside the column*,
    and the columns that did not wrap get a blank string on the extra line, so
    ``Age`` and ``Results`` stay empty on the second printed row.
    """
    headers = ['Name', 'Age', 'Test\nResults']
    rows = [
        ['Jade', 20, 9.651],
        ['John', 30, 3],
        ['Jane', 40, 245.7],
        ['Piotr\nBaltimore', 27, 3.5],
        ['Sam', 21, 0.6519],
    ]

    wrapped_headers, wrapped_rows = _wrap_rows(headers, rows)
    columns, zipped_headers = _zip_wrapped_rows(wrapped_headers, wrapped_rows)

    # The header wrapped too: 'Test' on line one, 'Results' on line two.
    assert zipped_headers == (('Name', ''), ('Age', ''), ('Test', 'Results'))

    name_column, age_column, results_column = columns

    assert name_column == ('Jade', 'John', 'Jane', ('Piotr', 'Baltimore'), 'Sam')
    # The neighbours of the wrapped cell are blank-padded on the extra line.
    assert age_column == (20, 30, 40, (27, ''), 21)
    assert results_column == (9.651, 3, 245.7, (3.5, ''), 0.6519)


def test_zip_wrapped_rows_handles_a_table_where_nothing_wraps():
    headers = ['Name', 'Age']
    rows = [['Jade', 20], ['John', 30]]

    wrapped_headers, wrapped_rows = _wrap_rows(headers, rows)
    columns, zipped_headers = _zip_wrapped_rows(wrapped_headers, wrapped_rows)

    assert zipped_headers == ['Name', 'Age']
    assert columns == (('Jade', 'John'), (20, 30))
