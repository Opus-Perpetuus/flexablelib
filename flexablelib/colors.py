"""
ANSI COLOUR

Colour is applied by wrapping cell text in escape sequences. Because those
sequences occupy no terminal columns, every width decision must go through
`fast.visible_width` -- see text_width.py. Getting that wrong is what produces
the misaligned coloured tables reported against prettytable (#187, #290) and
tabulate (#289, #307).

Colours may be given as:

    a name        'red', 'bright_blue', 'bold', 'dim'
    a 256 index   'color:93'      or the int 93
    a hex triple  '#ff8800'       true colour, 24-bit
    a combination 'bold red on white'

Resolution happens once per render, not once per cell, so the parsing cost
does not scale with table size.
"""

import os
import re
import sys
from typing import Optional, Union

CSI = '\x1b['
RESET = '\x1b[0m'

# Text attributes.
ATTRIBUTES = {
    'bold': 1,
    'dim': 2,
    'italic': 3,
    'underline': 4,
    'blink': 5,
    'reverse': 7,
    'hidden': 8,
    'strike': 9,
}

# The sixteen named colours. Foreground codes; background is the same plus 10.
COLOURS = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
    'bright_black': 90,
    'grey': 90,
    'gray': 90,
    'bright_red': 91,
    'bright_green': 92,
    'bright_yellow': 93,
    'bright_blue': 94,
    'bright_magenta': 95,
    'bright_cyan': 96,
    'bright_white': 97,
}

_HEX_RE = re.compile(r'^#?([0-9a-fA-F]{6})$')
_INDEX_RE = re.compile(r'^(?:color|colour):(\d{1,3})$')


class ColourError(ValueError):
    """Raised when a colour specification cannot be understood."""


def _colour_codes(token: str, background: bool = False) -> list:
    """Translate one colour token into its SGR parameters."""
    offset = 10 if background else 0

    if token in COLOURS:
        return [COLOURS[token] + offset]

    hex_match = _HEX_RE.match(token)
    if hex_match:
        digits = hex_match.group(1)
        red = int(digits[0:2], 16)
        green = int(digits[2:4], 16)
        blue = int(digits[4:6], 16)
        return [48 if background else 38, 2, red, green, blue]

    index_match = _INDEX_RE.match(token)
    if index_match:
        index = int(index_match.group(1))
        if not 0 <= index <= 255:
            raise ColourError(f'256-colour index out of range: {index}')
        return [48 if background else 38, 5, index]

    if token.isdigit():
        index = int(token)
        if not 0 <= index <= 255:
            raise ColourError(f'256-colour index out of range: {index}')
        return [48 if background else 38, 5, index]

    raise ColourError(f'unknown colour: {token!r}')


def parse_spec(spec: Union[str, int, None]) -> str:
    """
    Turn a colour specification into the escape sequence that starts it.

    Accepts the forms documented in the module docstring. Returns '' for None
    or an empty spec, so callers can apply the result unconditionally.

        parse_spec('bold red on white')  ->  '\\x1b[1;31;47m'
        parse_spec('#ff8800')            ->  '\\x1b[38;2;255;136;0m'
    """
    if spec is None or spec == '':
        return ''
    if isinstance(spec, int):
        spec = str(spec)

    parameters = []
    # 'on' separates foreground from background: 'bold red on white'.
    # A bare 'on <bg>' (Rich-style background-only) is also accepted.
    lowered = spec.lower().strip()
    if lowered.startswith('on '):
        foreground_part, background_part = '', lowered[3:]
    else:
        foreground_part, _, background_part = lowered.partition(' on ')

    for token in foreground_part.split():
        if token in ATTRIBUTES:
            parameters.append(ATTRIBUTES[token])
        else:
            parameters.extend(_colour_codes(token, background=False))

    if background_part:
        for token in background_part.split():
            parameters.extend(_colour_codes(token, background=True))

    if not parameters:
        return ''
    return CSI + ';'.join(str(parameter) for parameter in parameters) + 'm'


def colorize(text: str, spec: Union[str, int, None]) -> str:
    """
    Wrap text in the given colour, closing it with a reset.

    Returns the text untouched when the spec is empty, so this is safe to call
    on every cell whether or not colour is configured.
    """
    prefix = parse_spec(spec)
    if not prefix:
        return text
    return prefix + text + RESET


def supports_color(stream=None) -> bool:
    """
    Whether colour should be emitted to the given stream.

    Honours the NO_COLOR convention (https://no-color.org): any value, even
    empty, disables colour. FORCE_COLOR overrides in the other direction, which
    is what CI systems and pipes into `less -R` need.

    Otherwise colour is emitted only to a terminal, so redirecting output to a
    file does not fill it with escape sequences.
    """
    if 'NO_COLOR' in os.environ:
        return False
    if os.environ.get('FORCE_COLOR'):
        return True

    if stream is None:
        stream = sys.stdout

    if os.environ.get('TERM') == 'dumb':
        return False

    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        # Detached or closed stream. Assume no colour.
        return False


def strip_if_unsupported(text: str, stream=None) -> str:
    """Remove colour from text when the destination cannot display it."""
    if supports_color(stream):
        return text
    from .fast import strip_ansi
    return strip_ansi(text)


__all__ = [
    'colorize',
    'parse_spec',
    'supports_color',
    'strip_if_unsupported',
    'ColourError',
    'COLOURS',
    'ATTRIBUTES',
    'RESET',
]


# Named ANSI background → approximate sRGB for HTML / Excel fills.
_BG_HEX = {
    'black': '1F2937',
    'red': 'DC2626',
    'green': '16A34A',
    'yellow': 'CA8A04',
    'blue': '2563EB',
    'magenta': 'C026D3',
    'cyan': '0891B2',
    'white': 'F3F4F6',
    'bright_black': '4B5563',
    'grey': '6B7280',
    'gray': '6B7280',
    'bright_red': 'EF4444',
    'bright_green': '22C55E',
    'bright_yellow': 'EAB308',
    'bright_blue': '3B82F6',
    'bright_magenta': 'E879F9',
    'bright_cyan': '22D3EE',
    'bright_white': 'FFFFFF',
}

_FG_HEX = {
    'black': '111827',
    'red': '991B1B',
    'green': '14532D',
    'yellow': '713F12',
    'blue': '1E3A8A',
    'magenta': '86198F',
    'cyan': '155E75',
    'white': 'F9FAFB',
    'bright_black': '374151',
    'grey': '6B7280',
    'gray': '6B7280',
    'bright_red': 'B91C1C',
    'bright_green': '15803D',
    'bright_yellow': 'A16207',
    'bright_blue': '1D4ED8',
    'bright_magenta': 'A21CAF',
    'bright_cyan': '0E7490',
    'bright_white': 'FFFFFF',
}


def _split_spec(spec: Union[str, int, None]):
    if spec is None or spec == '':
        return [], None
    if isinstance(spec, int):
        return [], None
    foreground_part, _, background_part = str(spec).lower().partition(' on ')
    fg_tokens = foreground_part.split()
    bg_token = None
    if background_part:
        parts = background_part.split()
        bg_token = parts[0] if parts else None
    return fg_tokens, bg_token


def background_hex(spec: Union[str, int, None]) -> Optional[str]:
    """sRGB hex (no ``#``) for the background half of a colour spec, if any."""
    _fg, bg = _split_spec(spec)
    if bg is None:
        return None
    hex_match = _HEX_RE.match(bg)
    if hex_match:
        return hex_match.group(1).upper()
    return _BG_HEX.get(bg)


def foreground_hex(spec: Union[str, int, None]) -> Optional[str]:
    """sRGB hex (no ``#``) for the first named foreground colour in a spec."""
    fg_tokens, _bg = _split_spec(spec)
    for token in fg_tokens:
        if token in ATTRIBUTES:
            continue
        hex_match = _HEX_RE.match(token)
        if hex_match:
            return hex_match.group(1).upper()
        if token in _FG_HEX:
            return _FG_HEX[token]
    return None


def spec_to_css(spec: Union[str, int, None]) -> str:
    """Inline CSS ``color`` / ``background-color`` from a colour spec."""
    parts = []
    bg = background_hex(spec)
    fg = foreground_hex(spec)
    if bg:
        parts.append(f'background-color:#{bg}')
    if fg:
        parts.append(f'color:#{fg}')
    fg_tokens, _ = _split_spec(spec)
    if 'bold' in fg_tokens:
        parts.append('font-weight:600')
    return ';'.join(parts)
