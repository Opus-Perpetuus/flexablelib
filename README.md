<p align="center">
  <img src="logos/export/logo.svg" alt="prettyTables" width="440">
</p>

<p align="center">
  <em>Format tabular data with pretty styles.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/prettyTables/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/prettyTables?style=flat-square&color=4338CA&logo=pypi&logoColor=white"></a>
  <a href="https://pypi.org/project/prettyTables/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/prettyTables?style=flat-square&color=4338CA&logo=python&logoColor=white"></a>
  <a href="https://pypi.org/project/prettyTables/"><img alt="Downloads per month" src="https://img.shields.io/pypi/dm/prettyTables?style=flat-square&color=F59E0B"></a>
  <a href="https://pypi.org/project/prettyTables/"><img alt="Development status" src="https://img.shields.io/pypi/status/prettyTables?style=flat-square&color=F59E0B"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/prettyTables?style=flat-square&color=64748B"></a>
</p>

---

# **Pretty Tables**

This is a python package that aims to provide a simple and pretty way of printing tables to the console making use of a class.

The idea started as an attempt to reproduce the behavior of the [PM2](https://pm2.keymetrics.io) package when it displays tables to show data. Later, heavy inspiration came
of two other python packages:

- [Jazzband's](https://github.com/jazzband) [prettytable](https://github.com/jazzband/prettytable) (The names are similar by accident). Uses a class too.
- [Astanin's](https://github.com/astanin) [tabulate](https://github.com/astanin/python-tabulate). A very simple to use and efficient package.

A big part of the behavior of this package was replicated from these.

# Installation
``pip install prettyTables`` on Windows.

``pip3 install prettyTables`` on Linux

# Usage
Creating a table is simple.
### Code Example
```
from prettyTables import Table

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

See style examples [here](/style_examples.md).

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

# Colour

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

# Reading and writing

```python
Table.from_csv('sales.csv')          # numeric columns parsed and aligned
Table.from_html(markup)              # standard library parser, no dependency
Table.from_dicts(records)
Table.from_pandas(dataframe)         # pip install prettyTables[pandas]
Table.from_excel('report.xlsx')      # pip install prettyTables[excel]

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

# Merging cells

Render a rectangular block as a single cell, across columns, down rows, or
both. Coordinates are inclusive, zero-based, and ignore the index column.

```python
table.merge_cells(0, 0, last_column=2, value='Quarter summary')
table.merge_cells(1, 0, last_row=3)                # keeps the top-left content
table.merge_cells(0, 0, 2, 2, value='Total', align='r')
```

A merge never widens the table -- columns are still sized by their unmerged
content -- so text longer than its span is truncated.

# Performance

An optional C extension accelerates text measurement, and the render pipeline
avoids the second measuring pass when the table already fits. On identical
data:

| Library | 100x4 | 2000x4 | 10000x6 |
| --- | ---: | ---: | ---: |
| **prettyTables** | **1.0 ms** | **16.9 ms** | **147 ms** |
| prettytable | 1.4 ms | 23.2 ms | 174 ms |
| tabulate | 1.7 ms | 27.5 ms | 193 ms |
| pandas `.to_string()` | 1.7 ms | 22.9 ms | 228 ms |

Reproduce with `python3 tools/benchmark.py`. This measures one job: turning
data already in memory into formatted text. pandas is an analysis engine and
`to_string` is a convenience within it, so this says nothing about groupby or
joins.

The extension is built automatically where a compiler is available and falls
back to pure Python where it is not, so installation never fails for want of a
toolchain.

```python
from prettyTables.fast import implementation
print(implementation())   # 'C extension' or 'pure Python'
```

# Known Issues
- Naming a column ``"i"`` will mess up what columns show if the index column is displaying.
- Exponential numbers only align incorrectly.
- Shrinking a float column to fit the terminal loses its decimal alignment ([#23](https://github.com/Opus-Perpetuus/prettyTables/issues/23)).

# Project Layout

```
prettyTables/
├── prettyTables/            the package itself (no runtime dependencies)
│   ├── __init__.py          public API: Table, TableComposition, SeparatorLine
│   ├── table.py             the Table class — state and render orchestration
│   ├── columns.py           type inference, alignment, column widths
│   ├── style_compositions.py   the 42 border styles, as data
│   ├── table_strings.py     separator lines and data rows
│   ├── cells.py             cell padding, justification, wrapping
│   ├── options.py           constants and defaults
│   └── utils.py             type predicates and small helpers
├── tests/                   pytest suite — see ARCHITECTURE.md#testing
├── logos/                   brand assets — see logos/README.md
├── ARCHITECTURE.md          how it all fits together
├── style_examples.md        all 42 styles rendered
├── package.json             canonical version number; drives the release
└── setup.py                 reads the version from package.json
```

Run the tests from the repository root:

```
pip install -r requirements-dev.txt
python -m pytest
```

See [**ARCHITECTURE.md**](ARCHITECTURE.md) for the rendering pipeline, how styles are defined,
and how to add one.
