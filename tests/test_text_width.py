"""
Visible-width measurement (``text_width.py``, ``fast.py``, ``_speedups``).

Two reasons this file exists.

The first is stated by ``fast.py`` itself: a C implementation and a pure-Python
reference must agree exactly, and ``ACCELERATED`` says which one is live. When
the extension is built, every check below runs against both.

The second is that the rest of the suite depends on one invariant. Every table
in it is plain printable ASCII, and every hand-derived column width in
``test_columns.py``, ``test_readme_examples.py`` and
``test_two_pass_measurement.py`` was computed with ``len()``. If
``visible_width`` ever stops agreeing with ``len()`` on that input, those
widths are wrong for a reason that has nothing to do with the code they test.
"""

import pytest

from prettyTables import text_width as reference
from prettyTables.fast import ACCELERATED, implementation

try:
    from prettyTables import _speedups
except ImportError:
    _speedups = None

# Both backends when the extension is built, the reference alone when it is not.
BACKENDS = [pytest.param(reference, id='python')]
if _speedups is not None:
    BACKENDS.append(pytest.param(_speedups, id='c'))

ASCII_SAMPLES = [
    '',
    'a',
    'Jade',
    'a very long comment here',
    'missing_value__',
    '9.651',
    '245.7',
    'header1',
    'column 2',
    "!\"#$%&'()*+,-./0123456789:;<=>?@",
    'ABCXYZ[\\]^_`abcxyz{|}~',
]


# +-------------------------------------------------------------------------+
# The invariant the rest of the suite is built on
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('text', ASCII_SAMPLES)
def test_printable_ascii_measures_exactly_as_len(backend, text):
    assert backend.visible_width(text) == len(text)


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('align', ['l', 'r', 'c'])
def test_padding_printable_ascii_reaches_the_requested_width(backend, align):
    padded = backend.pad_to_width('Jade', 9, align, ' ')

    assert len(padded) == 9
    assert padded.strip() == 'Jade'


@pytest.mark.parametrize('backend', BACKENDS)
def test_padding_left_and_right_matches_str_ljust_and_rjust(backend):
    # The two alignments the default column types use.
    assert backend.pad_to_width('Jade', 9, 'l', ' ') == 'Jade'.ljust(9)
    assert backend.pad_to_width('20', 3, 'r', ' ') == '20'.rjust(3)


@pytest.mark.parametrize('backend', BACKENDS)
def test_a_string_at_or_over_the_width_is_returned_unchanged(backend):
    assert backend.pad_to_width('Jade', 4, 'l', ' ') == 'Jade'
    assert backend.pad_to_width('Jade', 2, 'l', ' ') == 'Jade'


# +-------------------------------------------------------------------------+
# What len() gets wrong
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('backend', BACKENDS)
def test_escape_sequences_take_no_columns(backend):
    coloured = '\x1b[31mab\x1b[0m'

    # Five characters of prefix, two of text, four of reset.
    assert len(coloured) == 11
    assert backend.visible_width(coloured) == 2


@pytest.mark.parametrize('backend', BACKENDS)
def test_wide_characters_take_two_columns(backend):
    assert backend.visible_width('日本') == 4
    assert backend.visible_width('a日') == 3


@pytest.mark.parametrize('backend', BACKENDS)
def test_combining_marks_take_no_columns(backend):
    # 'e' followed by a combining acute accent: two code points, one column.
    decomposed = 'e\u0301'

    assert len(decomposed) == 2
    assert backend.visible_width(decomposed) == 1


@pytest.mark.parametrize('backend', BACKENDS)
def test_control_characters_take_no_columns(backend):
    assert backend.visible_width('a\tb') == 2


@pytest.mark.parametrize('backend', BACKENDS)
def test_stripping_ansi_leaves_only_printable_characters(backend):
    assert backend.strip_ansi('\x1b[1;32mgreen\x1b[0m') == 'green'
    assert backend.strip_ansi('plain') == 'plain'


@pytest.mark.parametrize('backend', BACKENDS)
def test_padding_is_measured_by_visible_width_not_length(backend):
    coloured = '\x1b[31mab\x1b[0m'

    padded = backend.pad_to_width(coloured, 5, 'l', ' ')

    assert backend.visible_width(padded) == 5
    # The fill goes outside the sequence, so it does not inherit the colour.
    assert padded.endswith('   ')


# +-------------------------------------------------------------------------+
# The two implementations must not diverge
# +-------------------------------------------------------------------------+

EQUIVALENCE_SAMPLES = ASCII_SAMPLES + [
    '\x1b[31mab\x1b[0m',
    '\x1b[1;32mgreen\x1b[0m text',
    '日本語',
    'a日b本c',
    'é',
    'a\tb',
    '\x1b]8;;http://example.com\x07link\x1b]8;;\x07',
]


@pytest.mark.skipif(not ACCELERATED, reason='the C extension is not built here')
@pytest.mark.parametrize('text', EQUIVALENCE_SAMPLES)
def test_the_c_extension_measures_like_the_reference(text):
    assert _speedups.visible_width(text) == reference.visible_width(text)


@pytest.mark.skipif(not ACCELERATED, reason='the C extension is not built here')
@pytest.mark.parametrize('text', EQUIVALENCE_SAMPLES)
def test_the_c_extension_strips_ansi_like_the_reference(text):
    assert _speedups.strip_ansi(text) == reference.strip_ansi(text)


@pytest.mark.skipif(not ACCELERATED, reason='the C extension is not built here')
@pytest.mark.parametrize('align', ['l', 'r', 'c'])
@pytest.mark.parametrize('text', EQUIVALENCE_SAMPLES)
def test_the_c_extension_pads_like_the_reference(text, align):
    assert (
        _speedups.pad_to_width(text, 12, align, ' ')
        == reference.pad_to_width(text, 12, align, ' ')
    )


def test_the_active_backend_is_reported():
    assert implementation() == ('C extension' if ACCELERATED else 'pure Python')


# +-------------------------------------------------------------------------+
# Cutting a string at visible-column offsets
# +-------------------------------------------------------------------------+
#
# Every layout offset in this package is a count of terminal columns. Applying
# one with a plain string slice is only correct while the string is
# uncoloured ASCII, which is what made merged cells fail the moment anyone set
# a column colour.

COLOURED_CELL = '\x1b[1;35m John \x1b[0m'


def test_the_three_parts_of_a_partition_reassemble_the_input():
    for start, end in ((0, 0), (0, 3), (2, 4), (1, 6), (6, 6)):
        parts = reference.partition_by_width(COLOURED_CELL, start, end)
        assert ''.join(parts) == COLOURED_CELL


def test_a_partition_splits_on_columns_not_on_characters():
    before, inside, after = reference.partition_by_width(COLOURED_CELL, 1, 5)

    assert reference.visible_width(before) == 1
    assert reference.visible_width(inside) == 4
    assert reference.strip_ansi(inside) == 'John'


def test_a_slice_never_cuts_an_escape_sequence_in_half():
    # The six columns of this cell are eighteen characters. A raw slice taken
    # at the column offset lands inside '\x1b[1;35m', splitting the escape and
    # leaving its remainder to print as literal text.
    assert COLOURED_CELL[0:6].endswith('1;35')

    piece = reference.slice_by_width(COLOURED_CELL, 0, 6)

    assert reference.visible_width(piece) == 6
    assert '\x1b[1;35m' in piece


def test_a_slice_that_carries_colour_is_closed_with_a_reset():
    piece = reference.slice_by_width('\x1b[31mabcd', 0, 2)

    assert piece.endswith('\x1b[0m')
    assert reference.visible_width(piece) == 2


def test_splicing_replaces_exactly_the_columns_asked_for():
    line = '| 0 |' + COLOURED_CELL + '|  20 |'
    width = reference.visible_width(line)

    # Six columns out, six columns in: the line keeps its width even though
    # the piece removed was three times longer as a string.
    spliced = reference.splice_by_width(line, 5, 11, 'MERGED')

    assert reference.visible_width(spliced) == width
    assert '\x1b[1;35m' not in spliced
    assert 'MERGED' in spliced


def test_stripping_reaches_whitespace_sitting_inside_escapes():
    # str.strip() cannot: the string starts with '\x1b' and ends with 'm'.
    assert COLOURED_CELL.strip() == COLOURED_CELL

    stripped = reference.strip_by_width(COLOURED_CELL)

    assert reference.visible_width(stripped) == 4
    assert reference.strip_ansi(stripped) == 'John'
    # The colour the text had is kept; only the padding goes.
    assert stripped.startswith('\x1b[1;35m')
    assert stripped.endswith('\x1b[0m')


def test_stripping_keeps_interior_spaces():
    assert reference.strip_by_width('  a b  ') == 'a b'


def test_stripping_an_all_blank_cell_leaves_no_visible_width():
    stripped = reference.strip_by_width('\x1b[31m   \x1b[0m')

    assert reference.visible_width(stripped) == 0


def test_cutting_a_wide_character_cell_counts_columns_not_characters():
    # Four columns of text in two characters.
    before, inside, after = reference.partition_by_width('|寿司|', 1, 5)

    assert reference.visible_width(inside) == 4
    assert inside == '寿司'
