# Border styles

54 styles. Set one with `table.style_name = "<name>"`; `table.possible_styles` lists them all.

Names describe the look, read left to right: the line family (`single`, `rounded`, `double_frame`, `ascii`, `lines`...), then `_double_underline` (double rule under the header), `_rows` (a rule between every row), and `_open_header` / `_open_body` / `_open` (no column separators in the header, the body, or both).

## No borders

### `borderless`

Columns separated by spaces, cell margin kept. Use it for background-colour blocks.

```
 City    Temp 
 Oslo    7.25 
 Lima   19.5  
```

### `borderless_compact`

Columns separated by one space, no margin.

```
City  Temp
Oslo  7.25
Lima 19.5 
```

### `borderless_compact_header_gap`

Like `borderless_compact`, with a blank line under the header.

```
City  Temp
          
Oslo  7.25
Lima 19.5 
```

## Single lines

### `single`

Single-line box, single rule under the header.

```
┌──────┬───────┐
│ City │  Temp │
├──────┼───────┤
│ Oslo │  7.25 │
│ Lima │ 19.5  │
└──────┴───────┘
```

### `single_rows`

`single` plus a rule between every row.

```
┌──────┬───────┐
│ City │  Temp │
├──────┼───────┤
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
└──────┴───────┘
```

### `single_double_underline_rows`

Single-line box, double rule under the header, rule between rows.

```
┌──────┬───────┐
│ City │  Temp │
╞══════╪═══════╡
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
└──────┴───────┘
```

### `single_double_underline_rows_open_header`

As above, without column separators in the header.

```
┌──────────────┐
│ City    Temp │
╞══════╤═══════╡
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
└──────┴───────┘
```

### `single_double_underline_open_body`

Double rule under the header, no column separators in the body.

```
┌──────┬───────┐
│ City │  Temp │
╞══════╧═══════╡
│ Oslo    7.25 │
│ Lima   19.5  │
└──────────────┘
```

### `single_double_underline_open`

Double rule under the header, frame only (no column separators).

```
┌──────────────┐
│ City    Temp │
╞══════════════╡
│ Oslo    7.25 │
│ Lima   19.5  │
└──────────────┘
```

## Rounded corners

### `rounded`

Single-line box with rounded corners.

```
╭──────┬───────╮
│ City │  Temp │
├──────┼───────┤
│ Oslo │  7.25 │
│ Lima │ 19.5  │
╰──────┴───────╯
```

### `rounded_rows`

`rounded` plus a rule between every row.

```
╭──────┬───────╮
│ City │  Temp │
├──────┼───────┤
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
╰──────┴───────╯
```

### `rounded_double_underline`

Rounded corners, double rule under the header.

```
╭──────┬───────╮
│ City │  Temp │
╞══════╪═══════╡
│ Oslo │  7.25 │
│ Lima │ 19.5  │
╰──────┴───────╯
```

### `rounded_double_underline_open_header`

As above, without column separators in the header.

```
╭──────────────╮
│ City    Temp │
╞══════╤═══════╡
│ Oslo │  7.25 │
│ Lima │ 19.5  │
╰──────┴───────╯
```

### `rounded_double_underline_open`

As above, frame only (no column separators).

```
╭──────────────╮
│ City    Temp │
╞══════════════╡
│ Oslo    7.25 │
│ Lima   19.5  │
╰──────────────╯
```

## Double lines

### `double_rows`

Everything in double lines, rule between every row.

```
╔══════╦═══════╗
║ City ║  Temp ║
╠══════╬═══════╣
║ Oslo ║  7.25 ║
╠══════╬═══════╣
║ Lima ║ 19.5  ║
╚══════╩═══════╝
```

### `double_frame_rows`

Double outer frame, single inner lines, rule between rows.

```
╔══════╤═══════╗
║ City │  Temp ║
╠══════╪═══════╣
║ Oslo │  7.25 ║
╟──────┼───────╢
║ Lima │ 19.5  ║
╚══════╧═══════╝
```

### `double_frame_rows_open_header`

As above, without column separators in the header.

```
╔══════════════╗
║ City    Temp ║
╠══════╤═══════╣
║ Oslo │  7.25 ║
╟──────┼───────╢
║ Lima │ 19.5  ║
╚══════╧═══════╝
```

### `double_frame_open_body`

Double outer frame, no column separators in the body.

```
╔══════╤═══════╗
║ City │  Temp ║
╠══════╧═══════╣
║ Oslo    7.25 ║
║ Lima   19.5  ║
╚══════════════╝
```

### `double_frame_open`

Double outer frame only (no column separators).

```
╔══════════════╗
║ City    Temp ║
╠══════════════╣
║ Oslo    7.25 ║
║ Lima   19.5  ║
╚══════════════╝
```

### `double_horizontal`

Double horizontal rules, single vertical lines.

```
╒══════╤═══════╕
│ City │  Temp │
╞══════╪═══════╡
│ Oslo │  7.25 │
│ Lima │ 19.5  │
╘══════╧═══════╛
```

### `double_horizontal_rows`

`double_horizontal` plus a rule between every row.

```
╒══════╤═══════╕
│ City │  Temp │
╞══════╪═══════╡
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
╘══════╧═══════╛
```

### `double_header`

Header boxed in double lines, single-line body.

```
╔══════╦═══════╗
║ City ║  Temp ║
╚══════╩═══════╝
│ Oslo │  7.25 │
│ Lima │ 19.5  │
└──────┴───────┘
```

### `double_header_rows`

`double_header` plus a rule between every row.

```
╔══════╦═══════╗
║ City ║  Temp ║
╚══════╩═══════╝
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
└──────┴───────┘
```

### `double_header_open_header`

Double header box without column separators.

```
╔══════════════╗
║ City    Temp ║
╚══════════════╝
│ Oslo │  7.25 │
│ Lima │ 19.5  │
└──────┴───────┘
```

### `double_header_rows_open_header`

As above, plus a rule between every row.

```
╔══════════════╗
║ City    Temp ║
╚══════════════╝
│ Oslo │  7.25 │
├──────┼───────┤
│ Lima │ 19.5  │
└──────┴───────┘
```

### `double_header_open`

Double header box, no column separators anywhere.

```
╔══════════════╗
║ City    Temp ║
╚══════════════╝
│ Oslo    7.25 │
│ Lima   19.5  │
└──────────────┘
```

## Dashed and dotted

### `dashed`

Dashed single lines, heavy dashed rule under the header.

```
┌┄┄┄┄┄┄┬┄┄┄┄┄┄┄┐
┊ City ┊  Temp ┊
┝╍╍╍╍╍╍┿╍╍╍╍╍╍╍┥
┊ Oslo ┊  7.25 ┊
┊ Lima ┊ 19.5  ┊
└┄┄┄┄┄┄┴┄┄┄┄┄┄┄┘
```

### `dotted_rows`

Dots and colons ('.' and ':'), rule between every row.

```
................
: City :  Temp :
:......:.......:
: Oslo :  7.25 :
:......:.......:
: Lima : 19.5  :
:......:.......:
```

## ASCII

### `ascii_rows`

ASCII box (+ - |), rule between every row.

```
+------+-------+
| City |  Temp |
+------+-------+
| Oslo |  7.25 |
+------+-------+
| Lima | 19.5  |
+------+-------+
```

### `ascii_rounded`

ASCII box with '.' and "'" corners, no inner rules.

```
.--------------.
| City |  Temp |
| Oslo |  7.25 |
| Lima | 19.5  |
'--------------'
```

### `ascii_double_underline_rows`

ASCII box, '=' under the header, rule between rows.

```
+------+-------+
| City |  Temp |
+======+=======+
| Oslo |  7.25 |
+------+-------+
| Lima | 19.5  |
+------+-------+
```

### `ascii_double_underline_open_header`

ASCII box, '=' under the header, no column separators in the header. The default style.

```
+--------------+
| City    Temp |
+======+=======+
| Oslo |  7.25 |
| Lima | 19.5  |
+------+-------+
```

### `ascii_double_underline_open_body`

ASCII box, '=' under the header, no column separators in the body.

```
+------+-------+
| City |  Temp |
+======+=======+
| Oslo    7.25 |
| Lima   19.5  |
+--------------+
```

### `ascii_double_underline_open`

ASCII frame, '=' under the header, no column separators.

```
+--------------+
| City    Temp |
+==============+
| Oslo    7.25 |
| Lima   19.5  |
+--------------+
```

### `ascii_align_markers`

ASCII rules that show each column's alignment (~<~, ~^~, ~>~).

```
+ ~<~  +   ~>~ +
| City |  Temp |
+ ~<~  +   ~>~ +
| Oslo |  7.25 |
| Lima | 19.5  |
+ ~<~  +   ~>~ +
```

## Tilde

### `tilde`

ASCII box with '~' and 'O' rules around the header and at the bottom.

```
+------+-------+
| City |  Temp |
O~~~~~~O~~~~~~~O
| Oslo |  7.25 |
| Lima | 19.5  |
O~~~~~~O~~~~~~~O
```

### `tilde_rows`

`tilde` plus a rule between every row.

```
+------+-------+
| City |  Temp |
O~~~~~~O~~~~~~~O
| Oslo |  7.25 |
+------+-------+
| Lima | 19.5  |
O~~~~~~O~~~~~~~O
```

### `tilde_rows_open_header`

As above, without column separators in the header.

```
+--------------+
| City    Temp |
O~~~~~~O~~~~~~~O
| Oslo |  7.25 |
+------+-------+
| Lima | 19.5  |
O~~~~~~O~~~~~~~O
```

### `tilde_open`

Tilde frame only (no column separators).

```
+--------------+
| City    Temp |
O~~~~~~~~~~~~~~O
| Oslo    7.25 |
| Lima   19.5  |
O~~~~~~~~~~~~~~O
```

## Horizontal lines only

### `lines_ascii`

'-' rules above, under the header and at the bottom.

```
--------------
 City    Temp 
--------------
 Oslo    7.25 
 Lima   19.5  
--------------
```

### `lines_ascii_double`

'=' rules above, under the header and at the bottom.

```
==============
 City    Temp 
==============
 Oslo    7.25 
 Lima   19.5  
==============
```

### `lines_ascii_header_only`

Only a '-' rule under the header.

```
 City    Temp 
--------------
 Oslo    7.25 
 Lima   19.5  
```

### `lines_ascii_double_header_only`

Only a '=' rule under the header.

```
 City    Temp 
==============
 Oslo    7.25 
 Lima   19.5  
```

### `lines_single`

Single-line rules above, under the header and at the bottom.

```
──────────────
 City    Temp 
──────────────
 Oslo    7.25 
 Lima   19.5  
──────────────
```

### `lines_double`

Double-line rules above, under the header and at the bottom.

```
══════════════
 City    Temp 
══════════════
 Oslo    7.25 
 Lima   19.5  
══════════════
```

### `lines_single_header_only`

Only a single-line rule under the header.

```
 City    Temp 
──────────────
 Oslo    7.25 
 Lima   19.5  
```

### `lines_double_header_only`

Only a double-line rule under the header.

```
 City    Temp 
══════════════
 Oslo    7.25 
 Lima   19.5  
```

## Underlined columns

### `underlined_ascii`

Each header underlined with '-' (PowerShell look), no margin.

```
City  Temp
---- -----
Oslo  7.25
Lima 19.5 
```

### `underlined_single`

Each header underlined with a single line, closing line at the bottom.

```
City  Temp
──── ─────
Oslo  7.25
Lima 19.5 
──── ─────
```

## Text formats

### `markdown`

GitHub-flavoured Markdown table.

```
| City |  Temp |
|------|-------|
| Oslo |  7.25 |
| Lima | 19.5  |
```

### `markdown_aligned`

Markdown table with alignment colons (:--, :-:, --:).

```
| City |  Temp |
| :--- | ----: |
| Oslo |  7.25 |
| Lima | 19.5  |
```

### `org`

Emacs Org-mode table.

```
| City |  Temp |
|------+-------|
| Oslo |  7.25 |
| Lima | 19.5  |
```

### `psql`

PostgreSQL psql output: inner lines only.

```
 City |  Temp 
------+-------
 Oslo |  7.25 
 Lima | 19.5  
```

### `rst`

reStructuredText simple table.

```
====== =======
 City    Temp 
====== =======
 Oslo    7.25 
 Lima   19.5  
====== =======
```

## Names before 3.0.0

The old names still work but emit a `DeprecationWarning`.

| Old name | New name |
| --- | --- |
| `plain` | `borderless_compact_header_gap` |
| `empty` | `borderless_compact` |
| `blank` | `borderless` |
| `blocks` | `borderless` |
| `sharp` | `single` |
| `modern` | `single_rows` |
| `thin_borderline` | `single_double_underline_rows` |
| `th_bd_eheader` | `single_double_underline_rows_open_header` |
| `th_bd_ebody` | `single_double_underline_open_body` |
| `th_bd_empty` | `single_double_underline_open` |
| `modern_rounded` | `rounded_rows` |
| `round_edges` | `rounded_double_underline` |
| `re_eheader` | `rounded_double_underline_open_header` |
| `re_ebody` | `rounded_double_underline_open` |
| `extended` | `double_rows` |
| `bold_borderline` | `double_frame_rows` |
| `bd_bl_eheader` | `double_frame_rows_open_header` |
| `bd_bl_ebody` | `double_frame_open_body` |
| `bd_bl_empty` | `double_frame_open` |
| `pretty_columns` | `double_horizontal` |
| `pretty_grid` | `double_horizontal_rows` |
| `bheader_columns` | `double_header` |
| `bold_header` | `double_header_rows` |
| `beheader_columns` | `double_header_open_header` |
| `bold_eheader` | `double_header_rows_open_header` |
| `bheader_ebody` | `double_header_open` |
| `dashes` | `dashed` |
| `dots` | `dotted_rows` |
| `ascii` | `ascii_rows` |
| `grid` | `ascii_double_underline_rows` |
| `grid_eheader` | `ascii_double_underline_open_header` |
| `grid_ebody` | `ascii_double_underline_open_body` |
| `grid_empty` | `ascii_double_underline_open` |
| `sticks` | `ascii_align_markers` |
| `tilg_columns` | `tilde` |
| `tilde_grid` | `tilde_rows` |
| `tilg_eheader` | `tilde_rows_open_header` |
| `tilg_empty` | `tilde_open` |
| `simple` | `lines_ascii` |
| `simple_bold` | `lines_ascii_double` |
| `simple_head` | `lines_ascii_header_only` |
| `simple_head_bold` | `lines_ascii_double_header_only` |
| `sim_th_bl` | `lines_single` |
| `sim_bd_bl` | `lines_double` |
| `sim_head_th_bl` | `lines_single_header_only` |
| `sim_head_bd_bl` | `lines_double_header_only` |
| `pwrshll_alike` | `underlined_ascii` |
| `clean` | `underlined_single` |
| `pipes` | `markdown_aligned` |
| `orgtbl` | `org` |
| `presto` | `psql` |
| `re_structured_text` | `rst` |
