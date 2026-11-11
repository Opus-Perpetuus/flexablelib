"""
Regenerate style_examples.md: every border style, rendered from the source.

    python3 tools/style_examples.py

The descriptions below are checked against the catalogue, so adding a style
without describing it fails loudly instead of leaving a gap in the page.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flexablelib import Table  # noqa: E402
from flexablelib.style_compositions import DEPRECATED_STYLE_NAMES  # noqa: E402

FAMILIES = [
    ('No borders', {
        'borderless': 'Columns separated by spaces, cell margin kept. Use it for background-colour blocks.',
        'borderless_compact': 'Columns separated by one space, no margin.',
        'borderless_compact_header_gap': 'Like `borderless_compact`, with a blank line under the header.',
    }),
    ('Single lines', {
        'single': 'Single-line box, single rule under the header.',
        'single_rows': '`single` plus a rule between every row.',
        'single_double_underline_rows': 'Single-line box, double rule under the header, rule between rows.',
        'single_double_underline_rows_open_header': 'As above, without column separators in the header.',
        'single_double_underline_open_body': 'Double rule under the header, no column separators in the body.',
        'single_double_underline_open': 'Double rule under the header, frame only (no column separators).',
    }),
    ('Rounded corners', {
        'rounded': 'Single-line box with rounded corners.',
        'rounded_rows': '`rounded` plus a rule between every row.',
        'rounded_double_underline': 'Rounded corners, double rule under the header.',
        'rounded_double_underline_open_header': 'As above, without column separators in the header.',
        'rounded_double_underline_open': 'As above, frame only (no column separators).',
    }),
    ('Double lines', {
        'double_rows': 'Everything in double lines, rule between every row.',
        'double_frame_rows': 'Double outer frame, single inner lines, rule between rows.',
        'double_frame_rows_open_header': 'As above, without column separators in the header.',
        'double_frame_open_body': 'Double outer frame, no column separators in the body.',
        'double_frame_open': 'Double outer frame only (no column separators).',
        'double_horizontal': 'Double horizontal rules, single vertical lines.',
        'double_horizontal_rows': '`double_horizontal` plus a rule between every row.',
        'double_header': 'Header boxed in double lines, single-line body.',
        'double_header_rows': '`double_header` plus a rule between every row.',
        'double_header_open_header': 'Double header box without column separators.',
        'double_header_rows_open_header': 'As above, plus a rule between every row.',
        'double_header_open': 'Double header box, no column separators anywhere.',
    }),
    ('Dashed and dotted', {
        'dashed': 'Dashed single lines, heavy dashed rule under the header.',
        'dotted_rows': "Dots and colons ('.' and ':'), rule between every row.",
    }),
    ('ASCII', {
        'ascii_rows': "ASCII box (+ - |), rule between every row.",
        'ascii_rounded': "ASCII box with '.' and \"'\" corners, no inner rules.",
        'ascii_double_underline_rows': "ASCII box, '=' under the header, rule between rows.",
        'ascii_double_underline_open_header': "ASCII box, '=' under the header, no column separators in the header. The default style.",
        'ascii_double_underline_open_body': "ASCII box, '=' under the header, no column separators in the body.",
        'ascii_double_underline_open': "ASCII frame, '=' under the header, no column separators.",
        'ascii_align_markers': 'ASCII rules that show each column\'s alignment (~<~, ~^~, ~>~).',
    }),
    ('Tilde', {
        'tilde': "ASCII box with '~' and 'O' rules around the header and at the bottom.",
        'tilde_rows': '`tilde` plus a rule between every row.',
        'tilde_rows_open_header': 'As above, without column separators in the header.',
        'tilde_open': 'Tilde frame only (no column separators).',
    }),
    ('Horizontal lines only', {
        'lines_ascii': "'-' rules above, under the header and at the bottom.",
        'lines_ascii_double': "'=' rules above, under the header and at the bottom.",
        'lines_ascii_header_only': "Only a '-' rule under the header.",
        'lines_ascii_double_header_only': "Only a '=' rule under the header.",
        'lines_single': 'Single-line rules above, under the header and at the bottom.',
        'lines_double': 'Double-line rules above, under the header and at the bottom.',
        'lines_single_header_only': 'Only a single-line rule under the header.',
        'lines_double_header_only': 'Only a double-line rule under the header.',
    }),
    ('Underlined columns', {
        'underlined_ascii': "Each header underlined with '-' (PowerShell look), no margin.",
        'underlined_single': 'Each header underlined with a single line, closing line at the bottom.',
    }),
    ('Text formats', {
        'markdown': 'GitHub-flavoured Markdown table.',
        'markdown_aligned': 'Markdown table with alignment colons (:--, :-:, --:).',
        'org': 'Emacs Org-mode table.',
        'psql': 'PostgreSQL psql output: inner lines only.',
        'rst': 'reStructuredText simple table.',
    }),
]


def render(name):
    table = Table(rows=[['Oslo', 7.25], ['Lima', 19.5]], headers=['City', 'Temp'])
    table.use_colors = False
    table.style_name = name
    return str(table)


def main():
    described = [n for _, styles in FAMILIES for n in styles]
    catalogue = list(Table().possible_styles)
    missing = set(catalogue) - set(described)
    extra = set(described) - set(catalogue)
    if missing or extra or len(described) != len(catalogue):
        raise SystemExit('descriptions out of sync: missing %s, extra %s' % (sorted(missing), sorted(extra)))

    out = ['# Border styles', '',
           '%d styles. Set one with `table.style_name = "<name>"`; '
           '`table.possible_styles` lists them all.' % len(catalogue), '',
           'Names describe the look, read left to right: the line family '
           '(`single`, `rounded`, `double_frame`, `ascii`, `lines`...), then '
           '`_double_underline` (double rule under the header), `_rows` '
           '(a rule between every row), and `_open_header` / `_open_body` / '
           '`_open` (no column separators in the header, the body, or both).', '']
    for family, styles in FAMILIES:
        out += ['## ' + family, '']
        for name, text in styles.items():
            out += ['### `%s`' % name, '', text, '', '```', render(name), '```', '']
    out += ['## Names before 3.0.0', '',
            'The old names still work but emit a `DeprecationWarning`.', '',
            '| Old name | New name |', '| --- | --- |']
    for old, new in DEPRECATED_STYLE_NAMES.items():
        out.append('| `%s` | `%s` |' % (old, new))
    (ROOT / 'style_examples.md').write_text('\n'.join(out) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
