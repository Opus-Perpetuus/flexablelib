"""
Generate the Unicode width tables used by the C extension.

The C code cannot call `unicodedata`, so the character categories it needs are
baked into sorted range tables at build-preparation time and searched with a
binary search at runtime.

Both tables are derived from the same `unicodedata` module the pure-Python
fallback consults, so the two implementations agree by construction. Run this
after a CPython upgrade brings in a new Unicode revision:

    python3 tools/generate_width_tables.py

It rewrites prettyTables/_width_tables.h in place.
"""

import sys
import unicodedata

MAX_CODEPOINT = 0x110000
HEADER_PATH = 'prettyTables/_width_tables.h'


def classify(codepoint: int) -> int:
    """
    Width of a codepoint: 0, 1, or 2.

    Mirrors `text_width.char_width` exactly. Any change here must be made there
    too, or the extension and the fallback will render differently.
    """
    if codepoint == 0:
        return 0
    if codepoint < 32 or 0x7F <= codepoint < 0xA0:
        return 0
    char = chr(codepoint)
    if unicodedata.category(char) in ('Mn', 'Me', 'Cf'):
        return 0
    if unicodedata.east_asian_width(char) in ('W', 'F'):
        return 2
    return 1


def build_ranges(width: int):
    """Collapse every codepoint of the given width into (start, end) ranges."""
    ranges = []
    start = None
    for codepoint in range(MAX_CODEPOINT):
        if classify(codepoint) == width:
            if start is None:
                start = codepoint
        elif start is not None:
            ranges.append((start, codepoint - 1))
            start = None
    if start is not None:
        ranges.append((start, MAX_CODEPOINT - 1))
    return ranges


def format_table(name: str, ranges) -> str:
    lines = [f'static const struct width_range {name}[] = {{']
    for start, end in ranges:
        lines.append(f'    {{0x{start:05X}, 0x{end:05X}}},')
    lines.append('};')
    lines.append(f'#define {name.upper()}_COUNT '
                 f'(sizeof({name}) / sizeof({name}[0]))')
    return '\n'.join(lines)


def main() -> int:
    zero_ranges = build_ranges(0)
    wide_ranges = build_ranges(2)

    header = f'''/*
 * Unicode width tables for the prettyTables C extension.
 *
 * GENERATED FILE -- do not edit by hand.
 * Regenerate with: python3 tools/generate_width_tables.py
 *
 * Built against Unicode {unicodedata.unidata_version} (CPython
 * {sys.version_info.major}.{sys.version_info.minor}).
 *
 * Codepoints absent from both tables are one column wide.
 */

#ifndef PRETTYTABLES_WIDTH_TABLES_H
#define PRETTYTABLES_WIDTH_TABLES_H

struct width_range {{
    unsigned int start;
    unsigned int end;
}};

/* Zero-width: control characters, combining marks, format characters. */
{format_table('zero_width_ranges', zero_ranges)}

/* Double-width: East Asian Wide and Fullwidth, which includes emoji. */
{format_table('wide_ranges', wide_ranges)}

#endif /* PRETTYTABLES_WIDTH_TABLES_H */
'''

    with open(HEADER_PATH, 'w') as handle:
        handle.write(header)

    print(f'Unicode {unicodedata.unidata_version}: '
          f'{len(zero_ranges)} zero-width ranges, '
          f'{len(wide_ranges)} wide ranges -> {HEADER_PATH}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
