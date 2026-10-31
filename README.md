<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/logos/export/logo-1024.png" alt="flexablelib" width="440">
</p>

<p align="center">
  <strong>Fast, dependency-free terminal tables for Python.</strong><br>
  56 border styles · ANSI colours · cell merges · decimal alignment · width fitting · CSV / Markdown / HTML / Excel / LaTeX I/O
</p>

<p align="center">
  <a href="https://pypi.org/project/flexablelib/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/flexablelib?style=flat-square&color=4338CA&logo=pypi&logoColor=white"></a>
  <a href="https://pypi.org/project/flexablelib/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/flexablelib?style=flat-square&color=4338CA&logo=python&logoColor=white"></a>
  <a href="https://github.com/Opus-Perpetuus/flexablelib/actions/workflows/tests.yml"><img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/Opus-Perpetuus/flexablelib/tests.yml?branch=main&style=flat-square&label=tests"></a>
  <a href="https://pypistats.org/packages/flexablelib"><img alt="Downloads per month" src="https://img.shields.io/pypi/dm/flexablelib?style=flat-square&color=F59E0B"></a>
  <a href="https://pypi.org/project/flexablelib/"><img alt="Development status" src="https://img.shields.io/pypi/status/flexablelib?style=flat-square&color=F59E0B"></a>
  <a href="https://github.com/Opus-Perpetuus/flexablelib/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/pypi/l/flexablelib?style=flat-square&color=64748B"></a>
  <a href="https://github.com/Opus-Perpetuus/flexablelib/blob/main/flexablelib/py.typed"><img alt="Typed" src="https://img.shields.io/badge/typing-py.typed-64748B?style=flat-square"></a>
</p>

---

**flexablelib** turns rows and columns into readable tables for terminals, logs,
reports and docs. It has **no runtime dependencies**, ships **prebuilt wheels
with an optional C speed-up**, and is covered by **1,000+ tests** on Python
3.8 – 3.14.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/quickstart.png" alt="A rounded flexablelib table with a coloured header and a red value" width="600">
</p>

## Install

```bash
pip install flexablelib
```

Optional extras: `pip install "flexablelib[pandas]"`, `"flexablelib[excel]"`,
`"flexablelib[html]"` or `"flexablelib[all]"`. The base install stays
dependency-free.

## 30-second quickstart

```python
from flexablelib import Table

table = Table(
    rows=[
        ["api-gateway", "eu-west-1", 99.982, 1240],
        ["auth", "us-east-1", 99.9, 312],
        ["billing", "us-east-1", 98.75, 87],
    ],
    headers=["Service", "Region", "Uptime %", "RPS"],
)
table.style_name = "rounded"            # 56 styles, see style_examples.md
table.header_color = "bold cyan"
table.color_rule = lambda value, row, column: (
    "red" if column == "Uptime %" and value < 99.5 else None
)
print(table)
```

```
╭─────────────┬───────────┬──────────┬──────╮
│ Service     │ Region    │ Uptime % │  RPS │
├─────────────┼───────────┼──────────┼──────┤
│ api-gateway │ eu-west-1 │   99.982 │ 1240 │
│ auth        │ us-east-1 │   99.9   │  312 │
│ billing     │ us-east-1 │   98.75  │   87 │
╰─────────────┴───────────┴──────────┴──────╯
```

Numbers align on the decimal point, colours never break alignment, and the
same table exports anywhere:

```python
table.to_markdown()                # GitHub / docs
table.to_html("report.html")       # self-contained, sortable, offline
table.to_csv("out.csv"); table.to_latex(); table.to_rst(); table.to_asciidoc()
table.to_excel("report.xlsx")      # pip install "flexablelib[excel]"
Table.from_csv("sales.csv"); Table.from_markdown(md); Table.from_pandas(df)
```

## Feature gallery

<table>
<tr>
<td width="50%"><b>Styles</b> — 56 presets, from <code>ascii</code> to <code>blocks</code><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/styles.png" alt="Several border styles" width="260"></td>
<td width="50%"><b>Themes</b> — <code>table.apply_theme("ocean")</code><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/themes.png" alt="Theme presets" width="380"></td>
</tr>
<tr>
<td><b>Text on borders</b> — <code>table.border_text("Production", where="top")</code><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/border_text.png" alt="Labels written into the table frame" width="380"></td>
<td><b>Cell merges</b> — <code>table.merge_cells(0, 0, last_row=1)</code><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/merges.png" alt="Vertically merged cells" width="320"></td>
</tr>
<tr>
<td><b>Zebra rows, footer, caption</b><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/zebra_footer.png" alt="Striped rows with a footer and caption" width="380"></td>
<td><b>Decimal alignment</b> — floats and scientific notation<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/decimals.png" alt="Numbers aligned on the decimal point" width="220"></td>
</tr>
</table>

More: [all 56 styles](https://github.com/Opus-Perpetuus/flexablelib/blob/main/style_examples.md) ·
wrapping and ellipsis overflow · per-column / per-cell colour and alignment ·
vertical alignment · `paginate()` · `stream()` for live rows · `transpose()` ·
nested tables · `fit_terminal()` · `hide_columns` · `sort_by` · Roman / custom
index.

## How it compares

A factual feature matrix from our
[survey of 89 table libraries](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/COMPARISON.md). A dash means
the feature was not found in that library's documentation during the survey,
not a claim that it is impossible there.

| | flexablelib | tabulate | prettytable | rich |
| --- | :---: | :---: | :---: | :---: |
| Runtime dependencies | **none** | none | `wcwidth` | `markdown-it-py`, `pygments` |
| Border style presets | 56 | many `tablefmt` | — (hrules/vrules toggles) | box styles |
| Decimal-point alignment | ✓ | ✓ | — | — |
| Row **and** column cell merges | ✓ | — | — | — |
| ANSI colours (header, rows, cells, borders) | ✓ | — | — | ✓ |
| Zebra rows / caption / footer | ✓ | — | — | ✓ |
| Text written on borders | ✓ | — | — | — |
| Wrap / truncate / ellipsis overflow | ✓ | — | max width | ✓ |
| Sorting, pagination | ✓ | — | ✓ | — |
| Exports | CSV, MD, HTML, Excel, RST, AsciiDoc, LaTeX | HTML, LaTeX, MD, RST, org, jira, … | HTML, CSV, JSON, LaTeX | — (console) |
| Readers | CSV, Markdown, HTML, dicts, pandas, Excel | — | CSV, DB cursor, HTML | — |
| Nested tables | ✓ | — | — | ✓ (renderables) |

rich is a full terminal-rendering toolkit (markup, live displays, progress
bars) and tabulate covers many more markup dialects; pick flexablelib when you
want a dependency-free, table-focused library with styling, merges and I/O in
one place.

## Production notes

- **Zero runtime dependencies.** Readers/writers that need a third-party
  package (`pandas`, `openpyxl`, `lxml`) are opt-in extras and imported lazily.
- **Performance.** Rendering 10,000 rows × 6 columns takes ~157 ms with the C
  extension (~172 ms pure Python), on par with prettytable, ~1.3× faster than
  tabulate and ~18× faster than rich's table. pandas `to_string()` is faster
  still (~85 ms). Full method and numbers:
  [docs/BENCHMARKS.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/BENCHMARKS.md).
- **Wheels.** Prebuilt for CPython 3.8 – 3.13 on Linux (manylinux, musllinux),
  Windows x64 and macOS arm64. Anywhere else it builds from source or falls
  back to pure Python — installation never fails for want of a compiler.
  `from flexablelib.fast import implementation; implementation()` tells you
  which backend is live.
- **Colour safety.** Escape sequences are emitted only to a TTY by default,
  never when `NO_COLOR` is set; `FORCE_COLOR` or `table.use_colors = True`
  overrides. Logs and files stay clean.
- **Unicode.** Widths are measured in terminal columns, so CJK, emoji and
  coloured text stay aligned.
- **Windows.** Box-drawing styles need a UTF-8 console (`chcp 65001` or
  `PYTHONUTF8=1`; Windows Terminal is usually UTF-8 already). ASCII styles
  (`ascii`, `grid`, `psql`, `markdown`, …) work on any code page.
- **Typed.** Ships `py.typed` (PEP 561).
- **Stability.** flexablelib follows [semantic versioning](https://semver.org):
  within 2.x, public `Table` attributes and methods are not removed or renamed
  without a deprecation period; new features arrive in minor/patch releases
  and every release is listed in the
  [CHANGELOG](https://github.com/Opus-Perpetuus/flexablelib/blob/main/CHANGELOG.md).
- **Support.** Bugs and requests: [issues](https://github.com/Opus-Perpetuus/flexablelib/issues). Security reports:
  [SECURITY.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/SECURITY.md). Contributions:
  [CONTRIBUTING.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/CONTRIBUTING.md).

### Windows console encoding

```bat
chcp 65001
set PYTHONUTF8=1
```

(PowerShell: `$env:PYTHONUTF8=1`.)

# Guide

## Usage
Creating a table is simple.
### Code Example
```
from flexablelib import Table

new_table = Table()
print(new_table)
```
### Output
```
++
++
++
```
This is an empty table. It has no data so it only displays this strange thing.

A table that has columns but no rows — a query that came back empty — shows
its headers rather than raising:

```
┌──────┬───────┐
│ name │ value │
╞══════╪═══════╡
└──────┴───────┘
```

It's possible to add data as columns or rows, or even alternating each one. Any untitled column will be named automatically.

### Code Example
```
new_table.add_column('Name', ['Jade', 'John', 'Jane'])
new_table.add_column('Age', [20, 30, 40])
new_table.add_column('Results', [9.651, 3, 245.7])
print(new_table)
```

### Output
```
+----------------------+
| Name   Age   Results |
+======+=====+=========+
| Jade |  20 |   9.651 |
| John |  30 |   3     |
| Jane |  40 | 245.7   |
+------+-----+---------+
```

### Code Example
```
new_table = Table()
new_table.add_column('Name', ['Jade', 'John', 'Jane'])
new_table.add_column('Age', [20, 30, 40])
new_table.add_column('Test\nResults', [9.651, 3, 245.7])
new_table.add_row(['Piotr\nBaltimore', 27, 3.5])
new_table.add_row(['Sam', 21, 0.6519])
print(new_table)
```

### Output
```
+----------------------------+
| Name        Age       Test |
|                    Results |
+===========+=====+==========+
| Jade      |  20 |   9.651  |
| John      |  30 |   3      |
| Jane      |  40 | 245.7    |
| Piotr     |  27 |   3.5    |
| Baltimore |     |          |
| Sam       |  21 |   0.6519 |
+-----------+-----+----------+
```
As it is visible, the table will format automatically new lines and data types, for now without trying to parse strings that could be converted to another type.

The ``Table`` class offers a variety of options that allow things like showing the index of each row, changing the style of the table, hiding the headers, etc.

See style examples [here](https://github.com/Opus-Perpetuus/flexablelib/blob/main/style_examples.md).

### Code Example
```
new_table = Table()
new_table.add_column('Name', ['Jade', 'John'])
new_table.add_column('Age', [20, 30])
new_table.add_column('Test\nResults', [9.651, 3, 245.7])
new_table.add_row(['Piotr\nBaltimore', 27, 3.5])
new_table.add_row(['Sam', 21])
new_table.show_index = True
new_table.style_name = 'pretty_columns'
new_table.missing_value = '?'
print(new_table)
```

### Output
```
╒═══╤═══════════╤═════╤═════════╕
│ i │ Name      │ Age │    Test │
│   │           │     │ Results │
╞═══╪═══════════╪═════╪═════════╡
│ 0 │ Jade      │  20 │   9.651 │
│ 1 │ John      │  30 │   3     │
│ 2 │ ?         │   ? │ 245.7   │
│ 3 │ Piotr     │  27 │   3.5   │
│   │ Baltimore │     │         │
│ 4 │ Sam       │  21 │       ? │
╘═══╧═══════════╧═════╧═════════╛
```
The missing value aligns as if it was of the same type of the other data in the column.

This shows how to get the row and column count. If the index is shown, this count remains unaffected by that column, although, you can get the internal count.

### Code Example
```
new_table.show_index = False
new_table.show_headers = False
print(new_table)
print('row:', new_table.row_count)
print('columns:', new_table.column_count)
new_table.show_index = True
print(new_table)
print('internal_row_count:', new_table.internal_row_count)
print('internal_column_count:', new_table.internal_column_count)
```

### Output
```
╒═══════════╤════╤═════════╕
│ Jade      │ 20 │   9.651 │
│ John      │ 30 │   3     │
│ ?         │  ? │ 245.7   │
│ Piotr     │ 27 │   3.5   │
│ Baltimore │    │         │
│ Sam       │ 21 │       ? │
╘═══════════╧════╧═════════╛
row: 5
columns: 3
╒═══╤═══════════╤════╤═════════╕
│ 0 │ Jade      │ 20 │   9.651 │
│ 1 │ John      │ 30 │   3     │
│ 2 │ ?         │  ? │ 245.7   │
│ 3 │ Piotr     │ 27 │   3.5   │
│   │ Baltimore │    │         │
│ 4 │ Sam       │ 21 │       ? │
╘═══╧═══════════╧════╧═════════╛
internal_row_count: 5
internal_column_count: 4
```

## Colour

Colour the header, the borders, whole columns, whole rows, or individual cells.
Specs accept names, attributes, 256-colour indexes and hex triples.

```python
table.header_color = 'bold cyan'
table.border_color = 'grey'
table.column_colors = {'Service': 'bright_white'}
table.color_rule = lambda value, row, column: (
    'red' if column == 'Delta' and value < 0 else None
)
```

`color_rule` receives the original value, so numeric comparisons work directly.

Colour is emitted only to a terminal by default, and never when `NO_COLOR` is
set. `FORCE_COLOR` or `table.use_colors = True` overrides that. Because
`compose()` returns a string you may send anywhere, the default errs toward not
embedding escape sequences in something bound for a file.

Widths are measured in terminal columns, not characters, so coloured cells and
CJK or emoji data stay aligned.

## Reading and writing

```python
Table.from_csv('sales.csv')          # numeric columns parsed and aligned
Table.from_html(markup)              # standard library parser, no dependency
Table.from_dicts(records)
Table.from_pandas(dataframe)         # pip install flexablelib[pandas]
Table.from_excel('report.xlsx')      # pip install flexablelib[excel]

table.to_csv('out.csv')
table.to_markdown()
table.to_html('report.html', paginate=25)
table.to_excel('report.xlsx')
```

`to_html` writes one self-contained file — the stylesheet and the sorting,
filtering and pagination script are inline — so it works offline and from a
`file://` URL.

Text formats deliver everything as strings, and a column of strings is
left-aligned. `parse_str_numbers` converts numeric-looking text so it aligns as
numbers; the readers turn it on for you:

```python
table.parse_str_numbers = True
```

Values with leading zeros are left alone, so `'007'` stays a string.

## Merging cells

Render a rectangular block as a single cell, across columns, down rows, or
both. Coordinates are inclusive, zero-based, and ignore the index column.

```python
table.merge_cells(0, 0, last_column=2, value='Quarter summary')
table.merge_cells(1, 0, last_row=3)                # keeps the top-left content
table.merge_cells(0, 0, 2, 2, value='Total', align='r')
```

A merge never widens the table -- columns are still sized by their unmerged
content -- so text longer than its span is truncated.

## Notes

- A column named ``"i"`` does not collide with the index column (`utils.IndexColumnTitle`).
- Exponential numbers align on the decimal / exponent axis with the rest of the float column.
- Shrinking a float column drops decimals instead of chopping characters, so decimal alignment survives a terminal fit ([#23](https://github.com/Opus-Perpetuus/flexablelib/issues/23)).

Open work and the issue map: [docs/ISSUES.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/ISSUES.md).

## Project Layout

```
flexablelib/                 # GitHub repository
├── flexablelib/            the Python package (no runtime dependencies)
│   ├── __init__.py          public API: Table, TableComposition, SeparatorLine
│   ├── table.py             the Table class — state and render orchestration
│   ├── columns.py           type inference, alignment, column widths
│   ├── style_compositions.py   the 56 border styles, as data
│   ├── table_strings.py     separator lines and data rows
│   ├── cells.py             cell padding, justification, wrapping
│   ├── options.py           constants and defaults
│   └── utils.py             type predicates and small helpers
├── tests/                   pytest suite — see ARCHITECTURE.md#testing
├── docs/                    issue history and design notes
├── logos/                   brand assets — see logos/README.md
├── ARCHITECTURE.md          how it all fits together
├── style_examples.md        all 56 styles rendered
├── package.json             canonical version number; drives the release
└── setup.py                 reads the version from package.json
```

Run the tests from the repository root:

```
pip install -r requirements-dev.txt
python -m pytest
```

See [**ARCHITECTURE.md**](https://github.com/Opus-Perpetuus/flexablelib/blob/main/ARCHITECTURE.md) for the rendering pipeline, how styles are defined,
and how to add one.
