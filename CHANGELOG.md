# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [1.5.0](https://github.com/Opus-Perpetuus/prettyTables/compare/v1.4.2...v1.5.0) (2026-08-03)


### Features

* `open_in_browser()` renders the `to_html()` page to a temporary file and
  opens it, which is the quickest way to give a wide table the sideways room,
  the sortable columns and the filter box a terminal cannot. Returns the path
  it wrote; takes `path=` to write somewhere you choose
* merged cells now export. HTML and Excel say it natively -- `rowspan` /
  `colspan`, and real merged ranges -- so the file looks like the table did
* `raw_rows`, `raw_columns`, `raw_internal_rows` and `raw_internal_columns`
  expose the storage view with the sentinels intact, which is what an identity
  comparison against `table.missing` needs


### Bug Fixes

* a merge reached no further than the console. `to_csv()`, `to_markdown()`,
  `to_records()`, `to_html()`, `_repr_html_()` and `to_excel()` all rendered
  the cells of a merged block separately, because merging was applied by
  painting over the assembled console string and no other format could be
  given that treatment
* `rows`, `columns`, `internal_rows` and `internal_columns` handed back the
  table's own storage, so anything printing them got
  `<prettyTables.utils.ValuePlacer object at 0x...>` where a cell was absent,
  and the shared index counter object where the index number should have been.
  They resolve both sentinels now, and return a copy rather than the live
  structure
* both sentinels carry string forms saying what they are, so one that does
  escape reads as `<missing>` rather than an object address wide enough to
  wreck the layout it lands in

## [1.4.2](https://github.com/Opus-Perpetuus/prettyTables/compare/v1.4.1...v1.4.2) (2026-08-03)


### Bug Fixes

* `merge_cells()` with no `value=` now merges. It took its text from the whole
  span rather than the top-left cell, picking up the neighbouring columns and
  the rules between them; that already filled the span exactly, so painting it
  back changed nothing and the merge silently did not happen
* merges survive colour. Layout offsets are terminal columns and were applied
  with a plain string slice, which lands inside an escape sequence and puts
  every later offset out by its length -- one `column_colors` entry rendered
  the merged row wider than the rest of the table
* merges land on the right rows with a `title`, with `add_divider()`, and
  across a hidden empty column
* a float column whose numbers all lack a decimal point (`1e-07`, `1e+16`) no
  longer renders every body row a column wider than its frame
* `column_min_width` and `expand_to_window` widen a float column's cells, not
  just the frame drawn around them
* `show_index = True` no longer raises `IndexError` when the table is narrowed
  by `max_width`, a small terminal, or `column_max_width`
* `add_divider()` draws its rule at the table width when the first displayed
  row wraps to several lines
* every writer (`to_csv`, `to_records`, `to_markdown`, `to_html`,
  `_repr_html_`, `to_excel`) exports the missing value and the index numbers
  instead of `<prettyTables.utils.ValuePlacer object at 0x...>`
* `color_rule` receives the cell it is actually colouring under `sort_by` and
  `row_filter`, is not handed the index column's internal counter, and
  `column_colors` name the right column past a hidden empty one
* `to_html()` no longer lets a cell containing `</script>` close the page's
  script element and have its own markup parsed
* `from prettyTables import *` works; `__all__` held the classes rather than
  their names

## [1.4.1](https://github.com/Opus-Perpetuus/prettyTables/compare/v1.4.0...v1.4.1) (2026-08-03)


### Bug Fixes

* `column_max_width` now wraps or trims cell content to the cap (was only
  changing the measured width number, so long cells still overflowed)

## [1.4.0](https://github.com/Opus-Perpetuus/prettyTables/compare/v1.3.0...v1.4.0) (2026-08-03)


### Features

* cell formatters: `float_format`, `int_format`, `custom_format`, and `leading_zeros`
* per-column `column_min_width` / `column_max_width`
* `header_align` independent of body alignment
* `add_divider()` / `clear_dividers()` for horizontal rules between rows
* table `title` drawn above the frame
* `sort_by` / `sort_reverse` and `row_filter` at render time (storage unchanged)
* Jupyter `_repr_html_()` via a bare HTML table
* `shape` property `(rows, columns)`
* `table_align` and `expand_to_window` wired into render


### Bug Fixes

* float columns keep decimal alignment when the table is shrunk ([#23](https://github.com/Opus-Perpetuus/prettyTables/issues/23))
* alignment options are actually applied; `bool_align` no longer wrote the float slot ([#4](https://github.com/Opus-Perpetuus/prettyTables/issues/4))
* empty rows and columns share one emptiness criterion ([#9](https://github.com/Opus-Perpetuus/prettyTables/issues/9))
* column named `"i"` no longer collides with the index column
* exponential numbers align with the float column
* tabs, emoji VS16, empty header-only tables, markdown alignment colons, and other upstream regressions
* wide-character wrap at width 1 no longer invents a blank line
* header-only tables survive a narrow `max_width` without `IndexError`


### Documentation

* `docs/ISSUES.md` maps every tracker issue to its fix and tests
* README Known Issues and ARCHITECTURE Known gaps brought in line with current behaviour

## [1.3.0](https://github.com/Opus-Perpetuus/prettyTables/compare/v1.2.0...v1.3.0) (2026-08-03)


### Features

* merge cells across columns, down rows, or both, via `merge_cells()` ([39f6e56](https://github.com/Opus-Perpetuus/prettyTables/commit/39f6e56))


### Performance Improvements

* skip the redundant second measuring pass when the table already fits, and cut per-cell helper overhead; 2000x4 renders in 16.9ms against 30.6ms, making this the fastest of prettyTables, prettytable, tabulate and pandas .to_string() on the same data ([88b01f0](https://github.com/Opus-Perpetuus/prettyTables/commit/88b01f0))


### Bug Fixes

* the index column no longer continues counting across renders; it is reset explicitly rather than by a side effect of deep-copying the table ([88b01f0](https://github.com/Opus-Perpetuus/prettyTables/commit/88b01f0))
* `is_some_instance` returned None instead of False when nothing matched ([88b01f0](https://github.com/Opus-Perpetuus/prettyTables/commit/88b01f0))

## [1.2.0](https://github.com/Opus-Perpetuus/prettyTables/compare/v1.1.5...v1.2.0) (2026-08-03)


### Features

* ANSI colour for headers, borders, columns, rows and individual cells, with NO_COLOR and TTY detection ([f7ea1c9](https://github.com/Opus-Perpetuus/prettyTables/commit/f7ea1c9))
* read from CSV, HTML, dicts, pandas and Excel; write CSV, Markdown, self-contained paginated HTML and Excel ([c54fa06](https://github.com/Opus-Perpetuus/prettyTables/commit/c54fa06))
* parse numeric strings via `parse_str_numbers`, absorbing celulartable's type parsing ([ce5362b](https://github.com/Opus-Perpetuus/prettyTables/commit/ce5362b))
* `max_width` and `too_narrow_message` for tables that cannot fit ([f8309b8](https://github.com/Opus-Perpetuus/prettyTables/commit/f8309b8))
* `Table.missing` sentinel for building tables with gaps ([c54fa06](https://github.com/Opus-Perpetuus/prettyTables/commit/c54fa06))


### Bug Fixes

* measure and pad cells by visible width, fixing alignment for CJK, Hangul and emoji ([7a350d2](https://github.com/Opus-Perpetuus/prettyTables/commit/7a350d2))
* exclude hidden rows from column width measurement ([#22](https://github.com/Opus-Perpetuus/prettyTables/issues/22)) ([e480f4e](https://github.com/Opus-Perpetuus/prettyTables/commit/e480f4e))
* shrink the widest column first instead of every column in proportion ([#16](https://github.com/Opus-Perpetuus/prettyTables/issues/16)) ([842f64e](https://github.com/Opus-Perpetuus/prettyTables/commit/842f64e))
* never hand a column a width budget of zero, which raised from textwrap ([#14](https://github.com/Opus-Perpetuus/prettyTables/issues/14)) ([842f64e](https://github.com/Opus-Perpetuus/prettyTables/commit/842f64e))
* with auto_wrap off, the trimmed table now fits the terminal (Known Issue #2) ([842f64e](https://github.com/Opus-Perpetuus/prettyTables/commit/842f64e))


### Performance Improvements

* C extension for text measurement, 17-34x on the hot path, with a pure-Python fallback ([23981d4](https://github.com/Opus-Perpetuus/prettyTables/commit/23981d4))

### [1.1.5](https://github.com/Kyostenas/prettyTables/compare/v1.1.4...v1.1.5) (2022-07-11)


### Bug Fixes

* Wasn't possible to add empty rows. ([7a94a3f](https://github.com/Kyostenas/prettyTables/commit/7a94a3f94438ebdab16d21dd80d4c1bc66be872e))

### [1.1.4](https://github.com/Kyostenas/prettyTables/compare/v1.1.3...v1.1.4) (2022-07-11)


### Bug Fixes

* Accidental import. ([47e798a](https://github.com/Kyostenas/prettyTables/commit/47e798a9019b918b47ace50d5fe5683864e5e886))
* Auto trimming fixed. ([92e3a66](https://github.com/Kyostenas/prettyTables/commit/92e3a668fb931da0225b375d03c72f2ce9e357d0))
* Auto-wrapping fixed. ([4b8d631](https://github.com/Kyostenas/prettyTables/commit/4b8d631dc9f7dbe65053e25b854dc61c7d6fbb64))
* Autwrapping with index shown fixed. ([cbcb70c](https://github.com/Kyostenas/prettyTables/commit/cbcb70c8a08c5572553a3b46cad822cc316d5025))
* Columns not showing wen passing less headers in class args. ([1559fe4](https://github.com/Kyostenas/prettyTables/commit/1559fe41f347130e44f07c67cdd464ca23f0cf68))
* Passing extra headers causes an IndexError. ([e5a3e42](https://github.com/Kyostenas/prettyTables/commit/e5a3e427cf226d6eb4e58fb658d5068be1700edd))
* Using rows and headers arguments gives error. ([0479cd5](https://github.com/Kyostenas/prettyTables/commit/0479cd569396db5a08c9b51be7816b53e0e0f8f9))

### [1.1.3](https://github.com/Kyostenas/prettyTables/compare/v1.1.2...v1.1.3) (2022-05-07)


### Bug Fixes

* more accidental imports ([25e4c88](https://github.com/Kyostenas/prettyTables/commit/25e4c88e0feab8f154547ae159d0d7d8fff0750b))

### [1.1.2](https://github.com/Kyostenas/prettyTables/compare/v1.1.1...v1.1.2) (2022-05-07)


### Bug Fixes

* accidental import. ([736ab4d](https://github.com/Kyostenas/prettyTables/commit/736ab4dc281cb766f9726512e3505a5bb17fc0cc))

### [1.1.1](https://github.com/Kyostenas/prettyTables/compare/v1.1.0...v1.1.1) (2022-05-07)


### Bug Fixes

* adding column of different size causing misplaced missing values. ([66abc50](https://github.com/Kyostenas/prettyTables/commit/66abc5082488c734ffd9329be09f9dc6ea86683b))
* unintended info printing on console. ([560af0a](https://github.com/Kyostenas/prettyTables/commit/560af0aa8016ab71ad11f9f7ce29375543c192a9))

## [1.1.0](https://github.com/Kyostenas/prettyTables/compare/v1.0.0...v1.1.0) (2022-05-07)


### Features

* added auto-wrapping for string columns. ([0cacdef](https://github.com/Kyostenas/prettyTables/commit/0cacdef34c738d0d611440ab393f474f37858ae3))
* added float parsing and alignment ([1a65acd](https://github.com/Kyostenas/prettyTables/commit/1a65acd7a3fc7deb7331de4bed20a9d276d1a87d))
* added show_index option ([8b8d328](https://github.com/Kyostenas/prettyTables/commit/8b8d328af591a7d0edd288d80af029837f300f81))
* auto-wrap depends on the auto_wrap option. ([a1e09e5](https://github.com/Kyostenas/prettyTables/commit/a1e09e50ec913343b5b48b679cf08128ba74a383))
* column data trimming added. ([f53503b](https://github.com/Kyostenas/prettyTables/commit/f53503bc0b1bf3bd342286ba5cb16354ab8ee4ab))
* show_empty_columns, show_empty_rows options ([a7e4288](https://github.com/Kyostenas/prettyTables/commit/a7e428845254d68368e9bce6a7fbb4a59fe4046f))


### Bug Fixes

* add_column omitting columns_with_i ([4cc900d](https://github.com/Kyostenas/prettyTables/commit/4cc900d25c494fbc2dcf4b58a7c7794c42d22b81))
* auto-wrapping doesn't wrap columns "equally". ([9ba68ab](https://github.com/Kyostenas/prettyTables/commit/9ba68aba7c8c7494c33682368921802bc5167436))
* empty column and row hiding working bad ([76979e9](https://github.com/Kyostenas/prettyTables/commit/76979e9b803491e6335cdcca8f7417f99abf8542))
* float columns weren't considering header size ([f8ffce3](https://github.com/Kyostenas/prettyTables/commit/f8ffce38a2b97d409ca7ba37677280d8ff329c68))
* header wrapping wasn't working ([09b5136](https://github.com/Kyostenas/prettyTables/commit/09b513653f89dc61331301c2be5b1506366d0fdc))
* hiding empty r/c when showing i behaving bad ([823776a](https://github.com/Kyostenas/prettyTables/commit/823776ae5b1ca9b9210a8cd8337847a79fd5625f))
* index displays incorrectly when hiding empty rows ([6054dda](https://github.com/Kyostenas/prettyTables/commit/6054ddae743df58907802c1467f8993d937c7df7))
* large missing val. in float col. causes bad alignment ([565d58c](https://github.com/Kyostenas/prettyTables/commit/565d58c9db550d63d634c1f49c972a7c8beb7b8f))
* missing value was a normal value and was affecting alignment ([a01d4fa](https://github.com/Kyostenas/prettyTables/commit/a01d4fa1b7dcc03f3ba78f31b9984ba7a7f4d334))
* read_json not closing json ([6702f53](https://github.com/Kyostenas/prettyTables/commit/6702f5330f11d1f2a70b811e68f9a26447a065f6))
* table with index wasn't auto-wrapping ([23457a5](https://github.com/Kyostenas/prettyTables/commit/23457a542733a40931f875db76f2a62939ffa93e))
* when displaying index and adding rows table data messes up. ([3c0a724](https://github.com/Kyostenas/prettyTables/commit/3c0a7245dd09597ac46028bf31a03d37014c0ccc))
* when showing i table data displays incomplete. ([b33ed42](https://github.com/Kyostenas/prettyTables/commit/b33ed42d064b1875e70357dedc1b2005ba396379))
* wrapping wasn't working ([cf63647](https://github.com/Kyostenas/prettyTables/commit/cf63647a741dec0867cb702d75d16c3b0301d3e1))
