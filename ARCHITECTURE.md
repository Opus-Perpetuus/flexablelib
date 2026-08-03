<!-- omit in toc -->
# Architecture

How `prettyTables` is put together, for anyone who wants to fix a bug or add a style.

- [Overview](#overview)
- [Module map](#module-map)
- [The rendering pipeline](#the-rendering-pipeline)
- [Internal state](#internal-state)
- [How styles work](#how-styles-work)
- [Type inference and alignment](#type-inference-and-alignment)
- [Column widths](#column-widths)
- [Wrapping and terminal fitting](#wrapping-and-terminal-fitting)
- [Release process](#release-process)
- [Known gaps](#known-gaps)

## Overview

`prettyTables` is a pure-Python package with **no runtime dependencies**. It takes tabular
data held in memory and returns a formatted string. Everything is synchronous and in-process;
there is no I/O beyond reading the terminal size.

The public API is deliberately small — `prettyTables/__init__.py` exports exactly three names:

```python
from .table import Table
from .style_compositions import TableComposition, SeparatorLine
```

`Table` is the only one most users touch. `TableComposition` and `SeparatorLine` are exported
so that callers can define custom styles.

Rendering is triggered by `Table.__str__`, which simply calls `Table.compose()`. That means
`print(table)` and `str(table)` re-render the table from scratch every time — there is no
caching of the composed string.

## Module map

| Module | LOC | Responsibility |
| --- | ---: | --- |
| `table.py` | 2489 | The `Table` class. Holds all state, exposes ~30 properties, orchestrates rendering. |
| `columns.py` | 932 | Per-column type inference, alignment selection, and width computation. |
| `style_compositions.py` | 872 | The catalogue of 42 border styles, as data. |
| `table_strings.py` | 703 | Builds horizontal separator lines and joins data rows. |
| `cells.py` | 501 | Cell-level padding, justification, and text wrapping. |
| `options.py` | 75 | Constants and defaults (margins, default style, regex filters). |
| `utils.py` | 162 | Type predicates, terminal size, flatten, index counter. |

Dependencies flow in one direction — `table.py` imports from every other module, and the
others never import from `table.py`:

```
                 table.py
                    │
      ┌──────┬──────┼───────┬────────────┐
      ▼      ▼      ▼       ▼            ▼
  columns  cells  table_  options  style_compositions
      │      │    strings    ▲            ▲
      └──────┴───────┴───────┘            │
                    └────────────────────-┘
```

`options.py` and `style_compositions.py` are the leaves — they import nothing from the package
except each other (`style_compositions` reads `INVISIBLE_SEPARATOR` and `CELL_MARGIN` from
`options`).

## The rendering pipeline

`Table.compose()` (`table.py:1869`) is the entry point. It runs the data through **two
measuring passes**:

```
compose()
├── __call_table_objects()        rebuild row/column views from stored data
├── __typify_table()              infer a type per column  ──> columns._typify_column
├── __wrap_data(semi=True)        first wrap  ─────────────> cells._wrap_rows
├── __get_column_widths(semi=True)  first measure ────────> columns._column_widths
├── __get_string_table_width()    sum widths + separators
├── __check_columns_size()        does it fit the terminal? shrink columns if not
├── __wrap_data(semi=False)       re-wrap at the corrected widths
├── __get_column_widths(semi=False)  re-measure
└── __form_string()               assemble the final string
    ├── columns._align_headers    pad each header cell to its column width
    ├── columns._align_columns    pad each data cell to its column width
    ├── table_strings._get_separators   build the horizontal rules
    ├── table_strings._get_data_rows    build the body rows
    └── join everything with newlines
```

The two passes exist because of a circular dependency in the measurement: you cannot know
whether a column needs wrapping until you know its width, but wrapping changes the width. The
first pass (`semi=True`) measures the unconstrained table; if that exceeds the terminal width,
`__check_columns_size` shrinks the offending columns and the second pass re-wraps and
re-measures against those new widths.

`__form_string()` handles the four combinations of "has a top border" and "has a bottom
border" separately (`table.py:2444-2451`), because styles like `plain` and `presto` have
neither, and the join logic differs for each case.

## Internal state

`Table.__init__` sets up roughly **40 instance attributes**. The important thing to understand
is that the data is held in **four parallel representations**, all kept in sync manually:

| Attribute | Shape | Purpose |
| --- | --- | --- |
| `__columns` | `dict[header, list]` | Column-oriented view |
| `__rows` | `list[list]` | Row-oriented view |
| `__columns_with_i` | `dict[header, list]` | Same, plus the index column |
| `__rows_with_i` | `list[list]` | Same, plus the index column |

Every mutating method maintains both orientations. `add_column()` appends to `__columns`, then
calls `__transpose_column_to_rows()` to push the same data into `__rows`. `add_row()` does the
mirror image via `__transpose_row_to_columns()`. Adding data through one orientation always
back-fills the other, and both are padded to a rectangular shape by
`__adjust_columns_to_row_count()` / `__adjust_rows_to_column_count()`.

The `_with_i` variants exist so the index column (`'i'`) can be included or excluded without
recomputing anything. The same doubling applies to widths, types, and alignments:
`__column_widths` / `__column_widths_with_i`, `__column_types` / `__column_types_with_i`, and
so on. `__show_index` selects which set `__form_string()` reads from.

**Consequence:** the public `row_count` / `column_count` properties report the user-facing
counts, while `internal_row_count` / `internal_column_count` report the `_with_i` counts. With
the index shown these differ by one column — which is exactly what the README demonstrates.

## How styles work

Styles are **data, not code**. A style is a `TableComposition` namedtuple with 15 fields
(`style_compositions.py:14`):

```python
TableComposition = namedtuple('TableComposition', [
    'superior_header_line',            # SeparatorLine | None
    'inferior_header_line',            # SeparatorLine | None
    'superior_header_line_no_header',  # used when show_headers is False
    'table_body_line',
    'table_end_line',
    'vertical_header_lines',
    'vertical_table_body_lines',
    'margin',
    'align_sensitive',                 # does this style draw alignment indicators?
    'align_indicator',
    'centered_indicator_on_sides',
    'left_and_right_when_centered',
    'lines_with_indicator',
    'align_indicator_margin',
    'always_center_indicator',
])
```

Each horizontal rule is a `SeparatorLine(left, middle, intersection, right)` — the four
characters needed to draw a line such as `+----+----+`: `+` on the left, `-` repeated in the
middle, `+` at each intersection, `+` on the right. A field set to `None` means "this style has
no such line", which is how `plain` and `presto` end up borderless.

All 42 styles live in the `__style_compositions` namedtuple (`style_compositions.py:136`),
grouped by character family: box-drawing, thin/bold borderline, ASCII (`+-|~oO:`), simple
horizontal-rule styles, and `dashes`.

**Adding a style is purely additive:** add a name to the `Compositions` field list, then add
the corresponding `TableComposition(...)` entry. No logic changes anywhere. The structure of
this part was adapted from `tabulate`, as the module docstring notes.

`Table.possible_styles` returns the field names, and the `style_name` setter validates against
them.

## Type inference and alignment

`columns._typify_column()` (`columns.py:654`) inspects every cell in a column and returns a
`(cell_types, column_type, column_alignment)` triple. Detection runs through a chain of
predicates — `__is_str_column`, `__is_int_column`, `__is_float_column`, `__is_bool_column`,
`__is_byte_column`, `__is_none_type` — and the resolved type maps to a default alignment via
`ALIGNMENTS_PER_TYPE` (`columns.py:61`).

The defaults follow the usual typographic convention: strings left, numbers right, floats on
the decimal point. Per-type overrides are exposed as `str_align`, `int_align`, `float_align`,
and `bool_align`; `col_alignment` overrides a specific column outright.

Only the types in `CAN_WRAP_TYPES` (`columns.py:71`) are eligible for text wrapping —
wrapping a number would be meaningless.

Note that type detection works on the **actual Python type** of each value. A column of
`'123'` strings is a string column, not an int column. This is the first item in the README's
Known Issues, and `__parse_data()` (`table.py:2362`) is the empty stub reserved for fixing it.

## Column widths

Most columns are measured trivially: the width is the longest cell, plus margins, floored at
`MIN_COLUMN_SIZE`.

**Float columns are the exception**, and they are where most of `columns.py` goes. A float
column is not measured as a single width — it is measured as *two* widths, the digits to the
left of the decimal point and the digits to the right:

```
__get_float_widths()      split each cell on FLOAT_SEPARATOR ('.')
__get_sides_widths()      measure left side and right side independently
__compare_one_side()      find the max width of each side across the column
__float_col_total_width() total = max_left + point + max_right
```

Each cell is then padded so its decimal point lands on the shared axis, which is what
`fljust` / `_fljust_cell` in `cells.py` do (a "float justify", alongside the conventional
`_ljust_cell`, `_rjust_cell`, and `_center_cell`).

This is why the README's example renders as:

```
|   9.651 |
|   3     |
| 245.7   |
```

The values have different digit counts on both sides, but the points line up. The float widths
are carried separately all the way through rendering, in `__float_columns_widths` and its
`_with_i` twin.

## Wrapping and terminal fitting

`utils.get_window_size()` reads the terminal dimensions. `__check_columns_size()` compares the
measured table width against it and, when the table is too wide, shrinks columns and re-wraps.

Wrapping itself happens in `cells.py`:

- `_wrap_rows()` wraps each cell that exceeds its budget, turning a single-line cell into a
  list of lines.
- `__zip_sub_rows()` / `_zip_wrapped_rows()` then transpose those per-cell line lists back into
  physical output rows, so a logical row that wrapped to three lines becomes three printed
  rows with the other columns blank-padded.

That transposition is what produces the multi-line cells in the README (`Piotr\nBaltimore`
occupying two printed lines while `Age` and `Results` stay blank on the second).

When `auto_wrap` is `False`, the fitting step is skipped and a table wider than the terminal
will simply overflow — the second item in Known Issues.

Trimming is the fallback when wrapping is not possible: `__trim_with_sign()` cuts the cell and
appends `DEFAULT_TRIMMING_SIGN` (`'...'`).

## Release process

Versioning is driven from the **JavaScript** side of the repo, which is unusual for a Python
package and worth knowing before you cut a release:

- `package.json` holds the canonical version number.
- `setup.py` reads it at build time: `version = read_json('./package.json')['version']`.
- `standard-version` (`npm run release`) bumps `package.json`, writes `CHANGELOG.md`, and tags,
  based on Conventional Commits.
- `commitlint` + `husky` enforce the commit message format.
- `npm run install-local-linux` builds a wheel and installs it locally.

So `setup.py` must be run from the repository root — it resolves `./package.json` relative to
the working directory, not to the file.

## Known gaps

Things that are deliberately unfinished, so you do not mistake them for bugs:

**Empty stubs.** `__parse_data()`, `__parse_int_boolean()`, `__parse_exponentials()`,
`__parse_bytes()`, `__parse_escape_codes()`, and the whole data-reading section
(`__read_pandas_dataframe()`, `__read_csv_file()`, `__read_html_table()`, `__read_text_file()`)
are placeholders. `__expand_to_window` is flagged `TODO` in `__init__`.

**No test suite.** There is no `tests/` directory, and `tests/` is listed in `.gitignore`.
Nothing verifies the two-pass measurement logic.

**No CI.** There is no `.github/` directory — no workflows, no issue templates.

**Duplicate licence files.** `LICENSE` and `LICENSE.txt` are byte-identical. GitHub's licence
detector reports no licence for the repository as a result, even though the content is a
standard MIT licence.

**Version drift.** `setup.py` declares support for Python 3.8 and 3.9 only, and does not set
`python_requires`. It also still uses `distutils.core.setup`, which was removed from the
standard library in Python 3.12 — building on a modern interpreter requires `setuptools` to
provide the shim.

For behavioural bugs, see the [open issues](https://github.com/Opus-Perpetuus/prettyTables/issues)
and the Known Issues section of the [README](README.md).
