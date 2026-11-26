"""3.7.10: bugs found by property-based fuzzing (hypothesis).

``truncate_to_width`` with a width no larger than the marker returned
``suffix[:width]``: a wide marker overflowed (``'省略'`` at width 1 gave
``'省'``, two columns) and a coloured one was split, leaking a bare ESC.
The C ``truncate`` did the same.

``wrap_to_width`` dropped a zero-width character (U+200B) that followed a
wide one on a width-1 line, and a lone combining mark or zero-width
character left alone on the last line after a break.
"""

import pytest

from flexablelib.text_width import (
    wrap_to_width, sgr_is_open, strip_ansi, truncate_to_width, visible_width,
)
from flexablelib import _frames as F

BACKENDS = [truncate_to_width] + (
    [F._C['truncate']] if F._C is not None else [])
DIM = '\x1b[2m…\x1b[0m'


@pytest.mark.parametrize('truncate', BACKENDS)
@pytest.mark.parametrize('suffix', ['省略', '…省', DIM, '\x1b[31m>>\x1b[0m'])
@pytest.mark.parametrize('width', [1, 2, 3])
def test_marker_wider_than_width_is_cut_by_columns(truncate, suffix, width):
    if width > visible_width(suffix):
        pytest.skip('room for content: ordinary truncation')
    result = truncate('abcdefgh漢字', width, suffix)
    assert visible_width(result) <= width
    assert not sgr_is_open(result)
    assert '\x1b' not in strip_ansi(result)
    assert strip_ansi(suffix).startswith(strip_ansi(result))


@pytest.mark.parametrize('truncate', BACKENDS)
def test_narrow_ascii_marker_unchanged(truncate):
    assert truncate('abcdef', 2, '...') == '..'
    assert truncate('abcdef', 0, '...') == ''
    result = truncate('abcdef', 1, DIM)
    assert strip_ansi(result) == '…' and not sgr_is_open(result)
    assert truncate('abcdef', 1, '省略') == ''


@pytest.mark.parametrize('truncate', BACKENDS)
def test_wide_marker_fills_what_fits(truncate):
    assert truncate('abcdef', 3, '省略') == '省'


@pytest.mark.parametrize('text', ['漢\u200b', '漢\u2060漢', 'a漢\u200b'])
def test_wrap_keeps_zero_width_after_wide_char(text):
    lines = wrap_to_width(text, 1)
    assert ''.join(lines) == text
    assert '' not in lines


@pytest.mark.parametrize('text', ['a \u0301', 'a \u200b', 'ab \u2060'])
def test_wrap_keeps_zero_width_last_word(text):
    lines = wrap_to_width(text, 1 if len(text) < 4 else 2)
    assert ''.join(lines).replace(' ', '') == text.replace(' ', '')


def test_wrap_trailing_escape_still_no_blank_line():
    assert wrap_to_width('ab cd\x1b[0m', 2) == ['ab', 'cd\x1b[0m']
