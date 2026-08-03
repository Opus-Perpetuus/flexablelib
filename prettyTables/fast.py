"""
ACCELERATED TEXT MEASUREMENT

Selects the C implementation of the measurement primitives when it is
available and falls back to pure Python when it is not.

The extension is optional on purpose. A source install on a machine with no
compiler, an unusual platform with no published wheel, or a restricted build
environment must still end up with a working package -- prettyTables has been
installable with zero dependencies and no build step since 2021, and that must
not regress for the sake of speed.

Import from here rather than from `text_width` or `_speedups` directly:

    from .fast import visible_width, pad_to_width

`ACCELERATED` reports which path is live, which the test suite uses to run its
equivalence checks against both.
"""

from . import text_width as _reference

# Everything the extension does not implement comes from the reference module
# regardless. Truncation and wrapping are comparatively cold -- they only run
# on cells that actually overflow -- and their escape-sequence bookkeeping is
# far easier to get right in Python.
from .text_width import (  # noqa: F401
    char_width,
    has_ansi,
    tokenize,
    truncate_to_width,
    wrap_to_width,
)

try:
    from . import _speedups as _c

    visible_width = _c.visible_width
    strip_ansi = _c.strip_ansi
    pad_to_width = _c.pad_to_width
    widths_of = _c.widths_of
    ACCELERATED = True

except ImportError:  # pragma: no cover - depends on the build environment
    visible_width = _reference.visible_width
    strip_ansi = _reference.strip_ansi
    pad_to_width = _reference.pad_to_width

    def widths_of(strings):
        """Visible width of every string in the sequence."""
        return [_reference.visible_width(text) for text in strings]

    ACCELERATED = False


def implementation() -> str:
    """Name the active backend. Useful in bug reports."""
    return 'C extension' if ACCELERATED else 'pure Python'


__all__ = [
    'visible_width',
    'strip_ansi',
    'pad_to_width',
    'widths_of',
    'truncate_to_width',
    'wrap_to_width',
    'char_width',
    'has_ansi',
    'tokenize',
    'ACCELERATED',
    'implementation',
]
