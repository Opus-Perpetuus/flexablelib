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

    assert len(coloured) == 13
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
