"""
VISIBLE TEXT WIDTH

Every layout decision in this package depends on one question: how many terminal
columns does this string occupy? `len()` is the wrong answer twice over.

1. ANSI escape sequences take zero columns. `len('\\x1b[31mab\\x1b[0m')` is 11,
   but the terminal shows two characters. Measuring with `len()` makes every
   coloured table drift out of alignment.
2. Not every character is one column wide. CJK ideographs, Hangul, and most
   emoji occupy two. Combining marks, zero-width joiners, and variation
   selectors occupy none.

This module is the single source of truth for that measurement, and for the
padding, truncation, and wrapping built on top of it. Nothing else in the
package should call `len()` on user data.

A C implementation of the hot paths lives in `_speedups`; it is loaded by
`fast.py` when available. The functions here are the reference behaviour and
the fallback, and the two must agree exactly.
"""

import re
import unicodedata
from typing import Iterator, List, Tuple

# Matches the escape sequences a terminal consumes without advancing the cursor.
#
# Three families, and the order of alternation matters:
#   CSI  \x1b[ ... final byte in @-~     colours, cursor movement
#   OSC  \x1b] ... terminated by BEL or ST    hyperlinks (OSC 8), window titles
#   Fe   \x1b followed by one byte in @-_     two-byte escapes
#
# OSC must be tried before the two-byte form, because ']' (0x5D) falls inside
# the 0x5C-0x5F range and would otherwise match as a bare two-byte escape,
# leaving the hyperlink payload to be counted as visible text.
_ANSI_RE = re.compile(
    r'\x1b'
    r'(?:'
    r'\][^\x07\x1b]*(?:\x07|\x1b\\)'
    r'|\[[0-?]*[ -/]*[@-~]'
    r'|[@-Z\\-_]'
    r')'
)

_RESET = '\x1b[0m'

# ASCII control characters, which are zero-width. Used to guard the fast path
# in visible_width().
_CONTROL_RE = re.compile(r'[\x00-\x1f\x7f]')

# Character widths are looked up far more often than they are distinct, so the
# results are memoised. In the C implementation this becomes a lookup table.
_width_cache = {}


def char_width(char: str) -> int:
    """
    Terminal columns occupied by a single character: 0, 1, or 2.

    Zero-width: combining marks (Mn), enclosing marks (Me), and format
    characters (Cf, which covers the zero-width joiner and directional marks).
    Double-width: anything East Asian Wide or Fullwidth, which in current
    Unicode includes the emoji blocks.

    East Asian Ambiguous (category 'A') is treated as one column. It renders as
    two only in legacy CJK terminal fonts; one is correct everywhere else, and
    it is what every other table library assumes.
    """
    cached = _width_cache.get(char)
    if cached is not None:
        return cached

    codepoint = ord(char)
    if codepoint == 0:
        width = 0
    elif codepoint < 32 or 0x7F <= codepoint < 0xA0:
        # Control characters. They do not advance the cursor predictably, and
        # they have no business in a table cell, but they must not be counted.
        width = 0
    elif unicodedata.category(char) in ('Mn', 'Me', 'Cf'):
        width = 0
    elif unicodedata.east_asian_width(char) in ('W', 'F'):
        width = 2
    else:
        width = 1

    _width_cache[char] = width
    return width


def strip_ansi(text: str) -> str:
    """Remove every escape sequence, leaving only the characters that print."""
    return _ANSI_RE.sub('', text)


def has_ansi(text: str) -> bool:
    """True if the string carries any escape sequence."""
    return _ANSI_RE.search(text) is not None


def visible_width(text: str) -> int:
    """
    Terminal columns occupied by a string.

    This is the function that replaces `len()` throughout the package.
    """
    if not text:
        return 0
    # The common case is printable ASCII, where the width is simply the length.
    # Checking for that is much cheaper than walking the string.
    #
    # The control-character test is not optional: tabs, backspaces and bells
    # are ASCII but measure zero, so returning len() for a string containing
    # them would contradict char_width and put this function out of step with
    # the C implementation.
    if text.isascii() and not _CONTROL_RE.search(text):
        return len(text)
    return sum(char_width(char) for char in strip_ansi(text))


def tokenize(text: str) -> Iterator[Tuple[str, str]]:
    """
    Split into ('ansi', sequence) and ('text', run) pairs, in order.

    Padding, truncation, and wrapping all need to walk the printable characters
    while carrying the escape sequences along untouched. Reassembling every
    token in order reproduces the input exactly.
    """
    position = 0
    for match in _ANSI_RE.finditer(text):
        if match.start() > position:
            yield ('text', text[position:match.start()])
        yield ('ansi', match.group())
        position = match.end()
    if position < len(text):
        yield ('text', text[position:])


def pad_to_width(text: str, width: int, align: str = 'l', fill: str = ' ') -> str:
    """
    Pad to an exact visible width.

    `align` is 'l', 'r', or 'c'. Padding is appended outside any escape
    sequences, so the fill never inherits the cell's colour — a right-aligned
    red cell gets uncoloured leading spaces, not a red block.

    A string already at or over the width is returned unchanged; truncation is
    a separate decision, made by the caller.
    """
    padding_needed = width - visible_width(text)
    if padding_needed <= 0:
        return text

    if align == 'r':
        return (fill * padding_needed) + text
    if align == 'c':
        left = padding_needed // 2
        right = padding_needed - left
        return (fill * left) + text + (fill * right)
    return text + (fill * padding_needed)


def truncate_to_width(text: str, width: int, suffix: str = '...') -> str:
    """
    Cut to at most `width` visible columns, marking the cut with `suffix`.

    Escape sequences are preserved and never split — cutting through the middle
    of `\\x1b[31m` would leak raw bytes into the terminal. If any sequence was
    active at the cut point, a reset is appended so the colour does not bleed
    into the next cell. This is the failure mode behind tabulate #307.

    Double-width characters are never half-included; the result may come in one
    column under `width` rather than split an ideograph.
    """
    if visible_width(text) <= width:
        return text

    suffix_width = visible_width(suffix)
    if width <= suffix_width:
        # No room for content alongside the marker. Return as much of the
        # marker as fits, rather than something misleading.
        return suffix[:width] if width > 0 else ''

    budget = width - suffix_width
    used = 0
    pieces = []
    saw_ansi = False

    for kind, value in tokenize(text):
        if kind == 'ansi':
            pieces.append(value)
            saw_ansi = True
            continue
        for char in value:
            char_w = char_width(char)
            if used + char_w > budget:
                pieces.append(suffix)
                if saw_ansi:
                    pieces.append(_RESET)
                return ''.join(pieces)
            pieces.append(char)
            used += char_w

    pieces.append(suffix)
    if saw_ansi:
        pieces.append(_RESET)
    return ''.join(pieces)


def wrap_to_width(text: str, width: int) -> List[str]:
    """
    Break into lines of at most `width` visible columns, preferring word breaks.

    Words longer than the line are broken mid-word rather than allowed to
    overflow. Escape sequences travel with the text and are never split; when a
    line ends with a sequence still active, that line is closed with a reset and
    the sequence is reopened on the next, so colour survives the break intact.

    Existing newlines are honoured as hard breaks.

    `width` below 1 is treated as 1. A zero or negative width would otherwise
    loop forever on wide characters, which is tabulate #399.
    """
    if width < 1:
        width = 1
    if not text:
        return ['']

    lines = []
    for hard_line in text.split('\n'):
        lines.extend(_wrap_single_line(hard_line, width))
    return lines


def _wrap_single_line(text: str, width: int) -> List[str]:
    """Wrap one newline-free string. Helper for `wrap_to_width`."""
    if visible_width(text) <= width:
        return [text]

    lines = []
    current = []
    current_width = 0
    # Escape sequences seen so far on this line, so a break can reopen them.
    active_codes = []
    pending_codes = []

    def flush():
        """Close the current line, resetting colour if any is open."""
        nonlocal current, current_width, active_codes
        if active_codes:
            current.append(_RESET)
        lines.append(''.join(current))
        current = list(active_codes)
        current_width = 0

    # Split into words while keeping the escape sequences attached to whichever
    # word they precede, so colour boundaries land where the author put them.
    for word, leading_codes in _split_words(text):
        word_width = visible_width(word)

        # A trailing escape sequence arrives as an empty word carrying only its
        # codes. It must not get a word separator, or the line ends a column
        # wider than it measures and the whole column drifts.
        if word:
            if current_width and current_width + 1 + word_width > width:
                flush()
            elif current_width:
                current.append(' ')
                current_width += 1

        current.extend(leading_codes)
        active_codes.extend(code for code in leading_codes if code != _RESET)
        if _RESET in leading_codes:
            active_codes = []

        if word_width <= width - current_width:
            current.append(word)
            current_width += word_width
            continue

        # The word does not fit on a line of its own; break it by characters.
        for char in word:
            char_w = char_width(char)
            if current_width + char_w > width:
                flush()
            current.append(char)
            current_width += char_w

    if current_width or not lines:
        if active_codes:
            current.append(_RESET)
        lines.append(''.join(current))

    return lines


def _split_words(text: str) -> List[Tuple[str, List[str]]]:
    """
    Split on whitespace, returning (word, escape sequences preceding it).

    Keeping the sequences separate lets the wrapper reopen them after a line
    break without re-parsing.
    """
    words = []
    pending_codes = []
    current_word = []

    for kind, value in tokenize(text):
        if kind == 'ansi':
            if current_word:
                words.append((''.join(current_word), pending_codes))
                current_word = []
                pending_codes = []
            pending_codes.append(value)
            continue
        for char in value:
            if char.isspace():
                if current_word:
                    words.append((''.join(current_word), pending_codes))
                    current_word = []
                    pending_codes = []
            else:
                current_word.append(char)

    if current_word or pending_codes:
        words.append((''.join(current_word), pending_codes))

    return words
