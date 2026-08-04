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
- [Issues](docs/ISSUES.md)

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
`'123'` strings is a string column, not an int column. `__parse_data()` remains the empty
stub reserved for optional string-to-number parsing if that ever becomes a product decision.

## Column widths

Most columns are measured trivially: the width is the longest cell, plus margins, floored at
`MIN_COLUMN_SIZE`.

**Float columns are the exception**, and they are where most of `columns.py` goes. A float
column is not measured as a single width -- it is measured as left / point / right extents
via `FloatExtents` and `_float_extents`. Numbers and non-numeric cells (a missing value, a
label) are measured separately and combined only at the end, so a wide text cell cannot
inflate the integer side and make the column wider than any of its own numbers (issue #23).

```
__split_float_cell()       left / point / right for one cell
__measure_float_cell()     accumulate extents for one cell
__get_float_column_width() combine numeric and text measurements
```

Each cell is then padded so its decimal point lands on the shared axis, which is what
`fljust` / `_fljust_cell` in `cells.py` do (a "float justify", alongside the conventional
`_ljust_cell`, `_rjust_cell`, and `_center_cell`). Scientific notation is accepted by the
float filter and aligned through the same path.

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

Shrink reduces the widest columns first (issue #16), never below each column's floor
(`MIN_COLUMN_SIZE` for text; the integer-part width for floats). A float column that must
give up space drops decimals rather than chopping digits (`__shrink_float_column`). Display
width -- including East Asian characters, emoji with variation selectors, and ANSI
sequences -- is measured by `text_width` (C extension when built, pure Python otherwise).

Wrapping itself happens in `cells.py` and `text_width.wrap_to_width`:

- `_wrap_rows()` wraps each cell that exceeds its budget, turning a single-line cell into a
  list of lines.
- `__zip_sub_rows()` / `_zip_wrapped_rows()` then transpose those per-cell line lists back into
  physical output rows, so a logical row that wrapped to three lines becomes three printed
  rows with the other columns blank-padded.

That transposition is what produces the multi-line cells in the README (`Piotr\nBaltimore`
occupying two printed lines while `Age` and `Results` stay blank on the second).

When `auto_wrap` is `False`, over-wide cells are trimmed instead of wrapped. Trimming is
`truncate_to_width` via `__trim_with_sign`: the marker (`'...'` by default) counts inside
the budget, so a cell never prints wider than it was allowed.

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

## Performance

`fast.py` selects a C implementation of the measurement primitives when the
extension built, and falls back to `text_width.py` when it did not. On the
primitives themselves the extension is worth 17-34x:

| Operation | Speedup |
| --- | ---: |
| `visible_width`, plain text | 17.3x |
| `visible_width`, with ANSI | 34.4x |
| `strip_ansi` | 5.1x |
| `pad_to_width` | 5.3x |
| `widths_of`, whole column | 20.6x |

**The extension alone did not make the render faster, and the reason is worth
recording.** Profiling showed measurement was a small share of the total; the
cost was in the orchestration. Three changes to that orchestration did the
work:

- `compose()` ran the second wrap-and-measure pass unconditionally. When the
  table already fits -- most tables -- that pass reproduces the first one
  exactly. It is now skipped, and the final structures point at the first
  pass's output.
- `is_some_instance` ran one `isinstance` call per type where `isinstance`
  accepts a tuple, and `is_multi_row` built two intermediate sequences and a
  lambda per cell.
- `__call_table_objects` deep-copied every row on every render. The pipeline
  replaces whole cells and never mutates one, so one level of copying is
  enough.

Rendering 2000x4 went from 30.6 ms to 16.9 ms. Against the alternatives on
identical data:

| Library | 100x4 | 2000x4 | 10000x6 |
| --- | ---: | ---: | ---: |
| **prettyTables** | **1.0 ms** | **16.9 ms** | **147 ms** |
| prettytable | 1.4 ms | 23.2 ms | 174 ms |
| tabulate | 1.7 ms | 27.5 ms | 193 ms |
| pandas `.to_string()` | 1.7 ms | 22.9 ms | 228 ms |

Reproduce with `python3 tools/benchmark.py`.

Note what this does and does not claim. It is a rendering benchmark: turning
tabular data already in memory into formatted text. pandas is an analysis
engine over NumPy arrays, and `to_string` is a debugging convenience within
it, not its purpose. Being faster at this one job says nothing about groupby,
joins, or anything else pandas exists for.

Removing the deepcopy exposed something it had been hiding. The index column
holds one shared `IndexCounter` that counts as the render consumes it, and the
deep copy had been handing it a fresh instance each time as a side effect.
Rendering twice returned 0,1 then 2,3. It is now reset explicitly, which is
what the code meant to do.

## Merged cells

`merge_cells()` renders a rectangular block as one cell. Merges are applied to
the assembled string, in `merges.py`, rather than threaded through the
measuring pipeline.

That is a deliberate boundary. The pipeline sizes each column from its own
content, which is what makes decimal-point alignment and terminal fitting
tractable. A cell belonging to several columns at once would make one column's
width depend on another's, putting a cycle in the measurement. Rewriting the
finished lines keeps the columns sized by their unmerged content and makes
merging a presentation step that cannot affect layout correctness.

The visible consequence: **a merge never widens the table.** Content longer
than its span is truncated.

`compute_layout()` derives each column's offsets within a line from the widths
and the style's own separator characters, so the rewrite lands in the right
place for all 42 styles. Where a horizontal rule meets the right edge of a
merged block, the four-way junction is replaced by the body rule's `left`
character, since no line arrives from the left there any more.

**Those offsets are terminal columns, and must be applied as terminal
columns.** `merges.py` cuts lines with `partition_by_width()` from
`text_width.py`, never with a plain string slice. The two agree only for
uncoloured ASCII: `\x1b[1;35m` is seven characters and no columns, so a raw
slice taken at a column offset lands inside the escape, splits it, and puts
every later offset out by seven. That single mistake surfaced as two apparently
separate bugs -- a coloured row rendered wider than the rest of the table, and
a merge that silently did nothing -- which is worth remembering the next time
either symptom shows up.

Which rows a merge covers comes from the line map that `__join_body_rows()`
returns, because only that function knows how many rule lines it put between
rows; and where the body starts is counted off the same list of parts that gets
joined into the table. Reconstructing either of them separately is how a title
line, or a divider, used to shift every merge out of place.

## Known gaps

Things that are deliberately unfinished, so you do not mistake them for bugs:

**Empty stubs.** `__parse_data()` is a placeholder, and `__parse_int_boolean()`,
`__parse_bytes()` and `__parse_escape_codes()` are still commented out.
`__parse_exponentials` is no longer needed: the float filter and `fljust` accept
scientific notation. Optional string-to-number parsing remains a product
decision, not a render bug.

**Partial test coverage.** `colors.py` and most of `readers.py` still lack
direct tests. Formatters, widths, title, dividers, sort/filter, `_repr_html_`,
`shape`, markdown alignment, text width and the issue/upstream suites are
covered.

**Closed gaps (kept here so the history is obvious).**

- `utils.read_file` opens with `encoding='utf-8'`.
- The `style_name` setter no longer reads `style_examples.md` from disk.
- Short columns added later are padded without shifting existing values.
- `table_align`, `leading_zeros` and `expand_to_window` are wired into render.
- Issue #23 (float shrink alignment) is fixed; see [docs/ISSUES.md](docs/ISSUES.md).

For behavioural history, see [docs/ISSUES.md](docs/ISSUES.md) and the
[open issues](https://github.com/Opus-Perpetuus/prettyTables/issues).

## Testing

`tests/` holds a pytest suite and `.github/workflows/tests.yml` runs it on Python 3.8 to 3.14,
plus one job that builds the C extension so both measurement backends are exercised. Run it
from the repository root:

```
pip install -r requirements-dev.txt
python -m pytest
```

| File | Covers |
| --- | --- |
| `tests/test_two_pass_measurement.py` | `compose()`'s measure → fit → re-wrap → re-measure cycle |
| `tests/test_columns.py` | type inference and the two-sided float measurement |
| `tests/test_text_width.py` | visible width, and C/Python backend equivalence |
| `tests/test_cells.py` | padding, justification, wrapping, transposition |
| `tests/test_styles.py` | all 42 styles rendered, plus style selection |
| `tests/test_readme_examples.py` | the README's outputs, as golden strings |
| `tests/test_issues.py` | reproductions for the open issues, as `xfail` |

Two things have to be pinned or the results are not reproducible, and `tests/conftest.py`
does both with autouse fixtures:

- `utils.get_window_size()` reads the real console. It is imported into `table.py`'s namespace,
  so the patch target is `prettyTables.table.get_window_size`, not the one in `utils`.
- the working directory, because of the `style_name` setter described above.

Reproductions of open issues assert the behaviour the issue *asks for*, marked
`xfail(strict=False)`. They report `xfail` while the bug is present and `xpass` once it is
fixed — at which point the marker comes off rather than the assertion changing.
