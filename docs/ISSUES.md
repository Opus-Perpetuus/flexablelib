# Issues

What every issue filed against prettyTables asked for, how it was answered,
where the answer lives, and which test holds it in place.

Tracker: https://github.com/Opus-Perpetuus/prettyTables/issues

The executable companion is `tests/test_issues.py`. Defects found by reading
other table libraries' trackers live in `tests/test_upstream_issues.py` and
are summarised at the end of this file.

---

## Status at a glance

| Issue | Title (short) | Status | Held by |
| --- | --- | --- | --- |
| [#1](https://github.com/Opus-Perpetuus/prettyTables/issues/1) | ValueError when measuring the console | Closed | `test_issue_1_*` |
| [#2](https://github.com/Opus-Perpetuus/prettyTables/issues/2) | Show the row index | Closed | `test_issue_2_*` |
| [#3](https://github.com/Opus-Perpetuus/prettyTables/issues/3) | Hide empty rows and columns | Closed | `test_issue_3_*` |
| [#4](https://github.com/Opus-Perpetuus/prettyTables/issues/4) | Alignment per type and per column | Closed | `test_issue_4_*` |
| [#5](https://github.com/Opus-Perpetuus/prettyTables/issues/5) | Fit the table to the console | Closed | `test_issue_5_*` |
| [#6](https://github.com/Opus-Perpetuus/prettyTables/issues/6) | Missing value set after the data | Closed | `test_issue_6_*` |
| [#7](https://github.com/Opus-Perpetuus/prettyTables/issues/7) | Hide columns while the index shows | Closed | `test_issue_7_*` |
| [#8](https://github.com/Opus-Perpetuus/prettyTables/issues/8) | Index stays contiguous when rows hide | Closed | `test_issue_8_*` |
| [#9](https://github.com/Opus-Perpetuus/prettyTables/issues/9) | Empty row/column criteria mismatched | Closed | `test_issue_9_*` |
| [#10](https://github.com/Opus-Perpetuus/prettyTables/issues/10) | Formatting and documentation | Partial | `test_issue_10_*` |
| [#11](https://github.com/Opus-Perpetuus/prettyTables/issues/11) | Trimming with a marker | Closed | `test_issue_11_*` |
| [#12](https://github.com/Opus-Perpetuus/prettyTables/issues/12) | Trimmed number columns align left | Closed | `test_issue_12_*` |
| [#13](https://github.com/Opus-Perpetuus/prettyTables/issues/13) | Auto-wrap depends on `auto_wrap` | Closed | `test_issue_13_*` |
| [#14](https://github.com/Opus-Perpetuus/prettyTables/issues/14) | Message when the table cannot fit | Closed | `test_issue_14_*` |
| [#15](https://github.com/Opus-Perpetuus/prettyTables/issues/15) | Constructor rows/headers/columns | Closed | `test_issue_15_*` |
| [#16](https://github.com/Opus-Perpetuus/prettyTables/issues/16) | Shrink the widest columns first | Closed | `test_issue_16_*` |
| [#17](https://github.com/Opus-Perpetuus/prettyTables/issues/17) | Auto-wrapping raised | Closed | `test_issue_17_*` |
| [#18](https://github.com/Opus-Perpetuus/prettyTables/issues/18) | Trimming mutated stored data | Closed | `test_issue_18_*` |
| [#19](https://github.com/Opus-Perpetuus/prettyTables/issues/19) | Constructor headers still auto-named | Closed | `test_issue_19_*` |
| [#22](https://github.com/Opus-Perpetuus/prettyTables/issues/22) | Hidden rows still widened columns | Closed | `test_issue_22_*` |
| [#23](https://github.com/Opus-Perpetuus/prettyTables/issues/23) | Float columns lose alignment on shrink | Fixed here; close when released | `test_issue_23_*` |
| [#24](https://github.com/Opus-Perpetuus/prettyTables/issues/24) | Wide rows without prior columns | Closed | `test_issue_24_*` |

Issues #20 and #21 never existed on the tracker (or were removed); the suite
jumps from #19 to #22 for that reason.

---

## Per-issue notes

### #1 -- ValueError when measuring the console

Rendering called a hand-rolled terminal-size reader that raised
`ValueError` on some machines, so no table could be printed at all.

**Answer.** `get_window_size` catches `ValueError` as well as `OSError` and
falls back to `shutil.get_terminal_size(fallback=(80, 24))`.

**Where.** `prettyTables/utils.py` (`get_window_size`).

### #2 -- Show the row index

A left-hand index column, driven by `show_index`, `index_start` and
`index_step`.

**Answer.** The index is a synthetic column with an `IndexCounter` that
resets on every render. Removing the old `deepcopy` of every row during
render broke the accidental "new counter each time" behaviour; the reset is
now explicit.

**Where.** `table.py` (index plumbing), `utils.IndexColumnTitle` so a
user column named `"i"` cannot collide with it.

### #3, #7, #8, #9 -- Hiding empty rows and columns

Empty rows and columns should disappear when the matching option is false,
without hiding the other kind, and without breaking the index.

**Answer.** Rows and columns share `utils.is_empty_cell`. Hidden rows are
skipped in measurement (`__hidden_row_indexes`) so a missing value on a
hidden row cannot widen a column (#22). The index stays contiguous over
visible rows only (#8). Showing the index does not keep empty body columns
visible (#7).

**Where.** `table.py` (`show_empty_*`, hide helpers), `utils.is_empty_cell`.

### #4, #6 -- Alignment and the missing value

Alignment options were stored and never read. `bool_align` wrote into the
float slot. A missing value set after the data did not show, and when it
did it stole the column's alignment.

**Answer.** `__alignment_for` / `__checked_alignment` are consulted while
typifying columns. `col_alignment` accepts a single code, a sequence, or a
mapping by header; bad codes raise `ValueError`. The missing value is a
render-time substitution, so it can change after data is loaded and does
not change column type.

**Where.** `table.py` (alignment properties and typify), `columns.py`.

### #5, #11, #12, #13, #16, #17, #18 -- Fitting the console

The table must squeeze into the terminal: wrap when `auto_wrap` is on,
trim with `...` when it is off, prefer shrinking wide columns, never mutate
stored data, never hand a wrap budget of zero.

**Answer.** The shrink pass levels the widest columns down toward the next
width, floored at `MIN_COLUMN_SIZE` (and at the integer-part width for
floats). Wrapping and trimming work on a render copy. `wrap_to_width` /
`truncate_to_width` measure in display columns, not code points, and keep
the marker inside the budget.

**Where.** `table.py` (`__get_amounts_to_reduce`, `__adjust_column_widths`,
`__wrap_or_trim_data`), `text_width.py`, `cells.py`.

### #14 -- Too big for the space

When even the floor is wider than the available width, the caller can set
`too_narrow_message` and get a string instead of a cramped table. Without
that message the table still renders at the floor rather than raising.

**Where.** `table.py` (`compose`, `__minimum_table_width`,
`too_narrow_message`).

### #15, #19 -- Constructor arguments

`Table(rows=..., headers=...)` and `Table(columns=..., headers=...)` used
to raise. Headers passed to the constructor did not stop automatic naming.

**Answer.** Constructor paths share the same add-row / add-column
validation as the mutators. Explicit headers suppress auto-naming.

**Where.** `table.py` (`__init__`, `__check_header`).

### #10 -- Code formatting and documentation (partial)

Still open upstream for the remaining formatting pass and the fuller
examples (`style_examples.md`, the long `Table` docstring gallery). What a
test can hold: every public name on `Table` has a docstring.

**Where.** Docstrings on `Table` properties; `test_issue_10_*`.

### #22 -- Hidden empty rows still widened columns

A hidden empty row carried the long `missing_value` string in every cell,
and measurement counted it.

**Answer.** Measurement skips `__hidden_row_indexes()`.

**Where.** `columns.py` / `table.py` measurement paths.

### #23 -- Float columns lose decimal alignment when shrunk

Measuring a float column as `left + point + right` let a wide text cell
(a missing value) inflate `left`, so the column became wider than any of
its own cells. Shrink then chopped characters and forced string alignment.

**Answer.** Numbers and text are measured separately and combined at the
end (`FloatExtents`, `__get_float_column_width`). On shrink, a float column
drops decimals (rounds) instead of cutting digits, and keeps its alignment.
Each column has a floor it cannot go below, so booked reductions that
cannot be paid never leave the table too wide.

**Where.** `columns.py` (float measurement), `table.py`
(`__shrink_float_column`, `__column_shrink_floors`).

### #24 -- Wide rows without prior columns

Adding a multi-cell row before any column only kept the first cell.

**Answer.** Rows expand the column set to match their width.

**Where.** `table.py` (`add_row` and friends).

---

## Bugs found outside our tracker

These came from reading roughly nine hundred issues across prettytable,
tabulate, texttable, rich, pytablewriter and terminaltables. Each has a
regression in `tests/test_upstream_issues.py`.

| Failure | Upstream signal | Fix |
| --- | --- | --- |
| A tab in a cell broke the border | prettytable #113 | `cells.__wrap_cell` expands tabs (`TAB_SIZE = 8`) |
| Headers, no rows → `IndexError` | tabulate #180/#223/#315/#365, prettytable #184 | `cells._zip_wrapped_rows` returns one empty column per header; shrink path keeps empty column lists when there is no body |
| `add_column` with a name on an empty table fused columns | found here | `__check_header` only lets one unnamed column claim a declared header |
| Short columns padded from the top | ARCHITECTURE gap | `add_column` tracks `is_new_column` correctly |
| Blank line in an empty-bodied table | found here | `__form_string` joins only non-empty parts |
| Column named `'i'` with index visible lost columns | README Known Issue | `utils.IndexColumnTitle` -- equality by identity |
| Exponentials misaligned | README Known Issue, tabulate #266, texttable #71 | `FLT_FILTER` accepts exponents; `cells.fljust` uses `partition` |
| Markdown without alignment colons | prettytable #97/#149/#251 | `writers._markdown_alignment` / `_markdown_rule` |
| Emoji with VS16 measured as 1 | rich #3897 | `text_width.measured_clusters` and the same state in `_speedups.c` |
| Wide character at wrap width 1 | tabulate #399 | `wrap_to_width` places an over-wide cluster alone; never flushes an empty line first |

---

## Still open / follow-ups

- **#10** -- remaining documentation and formatting work
  (`style_examples.md`, gallery docstrings). Public properties are done.
- **#23 on GitHub** -- fixed; close when the release that carries it is
  published.

## Features landed from upstream demand

Held by `tests/test_features.py`:

| Feature | API |
| --- | --- |
| Cell formatters | `float_format`, `int_format`, `custom_format`, `leading_zeros` |
| Per-column width bounds | `column_min_width`, `column_max_width` |
| Header alignment | `header_align` |
| Divider rows | `add_divider()`, `clear_dividers()` |
| Title | `title` |
| Sort / filter | `sort_by`, `sort_reverse`, `row_filter` |
| Jupyter HTML | `_repr_html_()` via `writers.to_simple_html` |
| Shape | `shape` → `(rows, columns)` |
| Table placement | `table_align`, `expand_to_window` |
