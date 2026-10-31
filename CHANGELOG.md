# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [2.0.18] - 2026-10-31

### Fixed
- ``border_text(..., align='right' | 'center')`` now works with the default
  offset; you no longer have to pass ``offset=None``. The ``offset`` default
  is now ``None`` (automatic: a one-cell margin inside the frame corners).
  An explicit ``offset`` is a margin from the aligned edge: the start column
  for ``left`` (unchanged), the gap before the right edge for ``right``, and
  the margin on both sides for ``center``. Default (left) placement is
  unchanged.
- ``border_text`` on ``where='left' | 'right'`` honours ``align`` too
  (``left`` = top, ``center``, ``right`` = bottom) and, by default, no longer
  overwrites the top corner.
- ``border_text`` rejects a negative or non-integer ``offset`` with a clear
  error.

### Packaging
- CPython **3.14** wheels (Linux manylinux/musllinux, Windows, macOS) via
  cibuildwheel 3.4.1.
- Removed the unused npm toolchain (commitlint, husky, standard-version…) and
  ``package-lock.json``. ``package.json`` only carries the version number now,
  which clears all 35 Dependabot alerts; none of them ever reached PyPI users.

## [2.0.17] - 2026-10-31

### Security
- ``to_html`` (interactive page): cell or header text containing
  ``</script>`` could close the inline script and inject markup. The embedded
  JSON now escapes ``<``, ``>`` and ``&`` as ``\uXXXX``; values are unchanged
  once parsed.

### Fixed
- ``border_text(..., offset=None, align='right' | 'center')`` and overlong
  labels no longer overwrite the frame's closing corner.
- Rich/X11 percentage greys (``grey0`` … ``grey100``, ``gray`` too) are valid
  colour names, e.g. ``table.zebra = 'on grey23'``; they map to the nearest
  xterm-256 grey.

### Performance
- Rendering skips the per-cell vertical-alignment lookup when every cell is
  top-aligned (the default): 10,000 × 6 renders in ~157 ms instead of ~187 ms.
  ``tools/benchmark.py`` now includes rich and a ``--pure`` mode; numbers in
  ``docs/BENCHMARKS.md``.

### Packaging
- ``py.typed`` marker (PEP 561); ``Typing :: Typed`` classifier.
- Development status **5 - Production/Stable**; richer keywords, classifiers
  and ``project_urls`` (Source, Issues, Changelog, Documentation).
- The sdist now ships ``style_examples.md``, ``pytest.ini`` and ``tests/`` so
  the suite runs from it (useful for distro / conda-forge packaging, #26).
- ``setup.cfg``: ``description_file`` (the hyphenated key is deprecated).

### Docs
- README rewritten for adoption: quickstart, feature gallery (PNG renders
  from ``tools/readme_gallery.py``), comparison with tabulate / prettytable /
  rich, production notes, stability policy. Images and links use absolute
  URLs so they render on PyPI.
- ``CONTRIBUTING.md``, ``SECURITY.md``, issue and PR templates,
  ``docs/COMPARISON.md`` (89-library survey), ``docs/BENCHMARKS.md``.

## [2.0.16] - 2026-10-28

### Added
- ``Table.index_title``: rename the ``show_index`` column header (default ``i``).
- ``Table.roman_index``: render index values as Roman numerals.
- ``Table.number_columns``: display data headers as ``1``, ``2``, … (stored names kept).
- ``Table.strip_cells``: strip whitespace from string cells on display.
- ``Table.hrules`` / ``Table.vrules``: PrettyTable-style rule toggles
  (``all`` / ``frame`` / ``header`` / ``none`` for hrules; ``all`` / ``frame`` /
  ``none`` for vrules).
- ``Table.add_dividers(*indexes)`` and ``Table.divide_every(n, start=0)``.
- ``Table.fit_terminal(margin=0)``: pin ``max_width`` to the live terminal.
- Aliases ``max_table_width`` (``max_width``) and ``justify`` (``table_align``).
- ``Table.suppress_empty``: hide empty rows and columns together.
- CSV dialect extras on ``from_csv`` / ``to_csv``: ``dialect``, ``quoting``,
  ``quotechar``, ``escapechar``, ``doublequote``, ``lineterminator``,
  ``skipinitialspace``, ``strict``.
- Themes: ``solarized``, ``neon``, ``mono``, ``autumn``, ``contrast``,
  ``forest``, ``ember``, ``slate``.
- ``paginate(..., freeze_header=True, page_label=False)``: opt-out of repeating
  headers after page 1; optional ``page k/n`` title labels.

### Notes
- ``from_html`` was already present (2.0.x); no API change this release.

## [2.0.15] - 2026-10-28

### Added
- ``Table.stream(rows, append=False)``: beautifultable-style incremental
  print — yields composed lines as rows arrive with widths frozen from
  headers / seed rows / ``column_min_width`` (F13).
- ``Table.hide_columns``: omit columns by name or index at display time
  (go-pretty / prettytable suppress); stored data unchanged.
- ``Table.apply_theme(name)`` + ``Table.THEMES``: named style+colour
  bundles (``plain``, ``dark``, ``midnight``, ``matrix``, ``report``,
  ``markdown``, ``ocean``).
- ``sort_by`` accepts a callable ``key(row)`` in addition to header/index.

### Notes
- Streaming pins column widths; set ``column_min_width`` when later rows
  are wider than the seed content.

## [2.0.14] - 2026-10-28

### Added
- ``Table.valign`` / ``col_valign`` / ``cell_valign``: vertical cell alignment
  ``t`` / ``m`` / ``b`` inside multi-line rows (texttable-style).
- ``Table.panel`` + ``Table.shadow``: outer frame (rounded/sharp/ascii/double/heavy)
  and optional drop-shadow (tabled Panel / Spectre style).
- Export writers: ``to_rst()``, ``to_asciidoc()``, ``to_latex()``.
- ``Table.transpose()`` / ``rotate()``: swap rows and columns for display.
- ``Table.paginate(page_length=...)``: list of composed page strings with
  headers repeated (PrettyTable / go-pretty).
- Nested subtables: a cell whose value is a ``Table`` is composed into a
  multiline cell (minimal useful nesting).

### Notes
- Column percent-width constraints (F10) remain covered by existing
  ``column_min_width`` / ``column_max_width``; no API change.
- Streaming / incremental print (F13) shipped in 2.0.15.

## [2.0.13] - 2026-10-28

### Added
- Research inventory of 89 terminal/pretty-print table libraries across languages
  (see delivery demos / research notes); feature backlog mined into this release.
- ``Table.zebra`` / ``row_stripe``: alternating body-row colours
  (``None``, odd-only spec, or ``(even, odd)``).
- ``Table.caption``: centred text below the table (``title`` stays above).
- ``Table.footer_rows`` + ``Table.footer_color``: style a trailing totals band.
- ``Table.cell_colors``: per-cell ``{(row, col): spec}`` highlights.
- ``Table.cell_padding``: override style cell margin; ``show_margin=False`` now
  forces margin 0 (was stored but unused).
- ``Table.overflow``: ``'wrap'`` / ``'truncate'`` / ``'ellipsis'`` (keeps
  ``auto_wrap`` in sync).
- ``Table.from_markdown``: import GFM pipe tables (alignment row → col_alignment).
- Colour specs may be background-only: ``on #rrggbb`` / ``on white``.

## [2.0.12] - 2026-10-28

### Removed
- ``flush`` style (colour-fill experiments). Use ``blocks`` for borderless
  fills, or any bordered style with ``border_color`` / cell colours.

### Added
- tabled-compatible style names: ``ascii``, ``modern``, ``sharp``, ``rounded``,
  ``modern_rounded``, ``extended``, ``psql``, ``markdown``, ``re_structured_text``,
  ``dots``, ``ascii_rounded``, ``blank``, ``empty`` (glyphs aligned with
  [tabled](https://github.com/zhiburt/tabled) Style presets).
- ``Table.border_text(text, where=..., color=..., offset=..., align=...)`` —
  overlay coloured text on horizontal or vertical borders (tabled LineText).
  ``clear_border_texts()`` resets overlays.
- ``border_color`` documents FG paint of border/rule/junction glyphs on any
  style (including the new tabled names).

## [2.0.11] - 2026-10-28

### Added
- Horizontal rule cell backgrounds: dash runs on H-separators inherit the cell-above fill so coloured cells meet ─/═ without a dark band (generic; recommended with `flush`).
- `paint_rule_cell_backgrounds` helper; ANSI-aware junction glyph detection for painted rules.

## [2.0.10] - 2026-10-28

### Added
- ``flush`` style: full unicode grid whose cell backgrounds meet the border
  glyphs with no interior gap and never paint over them (pad-then-paint
  contract; recommended for coloured cells and coloured merges).
- ``merge_cells(..., color=...)`` paints the whole merge span (ANSI + HTML +
  Excel). When omitted, merges inherit the top-left cell's row/column/cell
  colour so existing colour APIs fill merges instead of leaving dark holes.

## [2.0.9] - 2026-10-28

### Added
- New ``blocks`` style: background-colour cells only — no outer/inner borders
  and no junctions. Column gaps are a single space spacer; cell margin kept so
  ANSI / Excel fills read as solid blocks.

## [2.0.8] - 2026-10-28

### Fixed
- Synthetic caps for multi-column merges clamp their horizontal run to the
  merge's column span (no H bleeding into neighbour columns). Covers
  column-only styles such as `grid_eheader` / `round_edges` / `pretty_columns`.
- Junction repair skips invisible/spacer vertical glyphs, so styles like
  `simple` no longer pick up stray `┴`/`┼` on header and end rules.

## [2.0.7] - 2026-10-28

### Fixed
- Generic merge junction algorithm: rule detection no longer treats a lone
  hyphen inside cell text (e.g. `Beta-1`) as a separator line, so column-only
  styles still get synthetic caps around multi-column merges.
- Pure-horizontal junctions keep the rule's own dash glyph (`┄`/`═`/`─`/`-`)
  instead of substituting a foreign `─`.
- Synthetic caps blank through taller vertical/2D merges that cross the gap
  (no ghost `┼` inside a continuing merge).
- Synthetic caps use the table's outer horizontal style so they match top/bottom.
- Round-edge end corners (`╰`/`╯`) survive last-row horizontal merge repair.

## [2.0.4](https://github.com/Opus-Perpetuus/flexablelib/compare/v2.0.3...v2.0.4) (2026-10-28)

### Bug Fixes

* repair merge junctions on both axes (vertical + horizontal) from surviving arms
* use middle-vertical tees (├/┤) instead of border glyphs (╟/╢) inside the grid
* insert synthetic row rules for column-only styles around multi-column merges

## [2.0.3](https://github.com/Opus-Perpetuus/flexablelib/compare/v2.0.2...v2.0.3) (2026-10-28)

### Features

* ``to_excel`` / ``from_excel`` preserve merged cell ranges (openpyxl)

## [2.0.2](https://github.com/Opus-Perpetuus/flexablelib/compare/v2.0.1...v2.0.2) (2026-10-28)

### Bug Fixes

* redraw vertical-merge vertices as edges/tees instead of leftover corners

## [2.0.1](https://github.com/Opus-Perpetuus/flexablelib/compare/v2.0.0...v2.0.1) (2026-10-28)


### Bug Fixes

* `missing_val` is now an alias of `missing_value` (docs and constructor kwarg name no longer silently no-op)

## [2.0.0](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.4.1...v2.0.0) (2026-10-28)


### ⚠ BREAKING CHANGES

* package renamed from `prettyTables` to `flexablelib` (`from flexablelib import Table`)


### Features

* Flexible Table Library identity: PyPI name `flexablelib`, C extension `flexablelib._speedups`


### Bug Fixes

* colour merge tests pin `use_colors=True` so CI without a TTY still asserts ANSI codes

## [1.4.1](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.4.0...v1.4.1) (2026-08-03)


### Bug Fixes

* `column_max_width` now wraps or trims cell content to the cap (was only
  changing the measured width number, so long cells still overflowed)

## [1.4.0](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.3.0...v1.4.0) (2026-08-03)


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

* float columns keep decimal alignment when the table is shrunk ([#23](https://github.com/Opus-Perpetuus/flexablelib/issues/23))
* alignment options are actually applied; `bool_align` no longer wrote the float slot ([#4](https://github.com/Opus-Perpetuus/flexablelib/issues/4))
* empty rows and columns share one emptiness criterion ([#9](https://github.com/Opus-Perpetuus/flexablelib/issues/9))
* column named `"i"` no longer collides with the index column
* exponential numbers align with the float column
* tabs, emoji VS16, empty header-only tables, markdown alignment colons, and other upstream regressions
* wide-character wrap at width 1 no longer invents a blank line
* header-only tables survive a narrow `max_width` without `IndexError`


### Documentation

* `docs/ISSUES.md` maps every tracker issue to its fix and tests
* README Known Issues and ARCHITECTURE Known gaps brought in line with current behaviour

## [1.3.0](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.2.0...v1.3.0) (2026-08-03)


### Features

* merge cells across columns, down rows, or both, via `merge_cells()` ([39f6e56](https://github.com/Opus-Perpetuus/flexablelib/commit/39f6e56))


### Performance Improvements

* skip the redundant second measuring pass when the table already fits, and cut per-cell helper overhead; 2000x4 renders in 16.9ms against 30.6ms, making this the fastest of flexablelib, prettytable, tabulate and pandas .to_string() on the same data ([88b01f0](https://github.com/Opus-Perpetuus/flexablelib/commit/88b01f0))


### Bug Fixes

* the index column no longer continues counting across renders; it is reset explicitly rather than by a side effect of deep-copying the table ([88b01f0](https://github.com/Opus-Perpetuus/flexablelib/commit/88b01f0))
* `is_some_instance` returned None instead of False when nothing matched ([88b01f0](https://github.com/Opus-Perpetuus/flexablelib/commit/88b01f0))

## [1.2.0](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.1.5...v1.2.0) (2026-08-03)


### Features

* ANSI colour for headers, borders, columns, rows and individual cells, with NO_COLOR and TTY detection ([f7ea1c9](https://github.com/Opus-Perpetuus/flexablelib/commit/f7ea1c9))
* read from CSV, HTML, dicts, pandas and Excel; write CSV, Markdown, self-contained paginated HTML and Excel ([c54fa06](https://github.com/Opus-Perpetuus/flexablelib/commit/c54fa06))
* parse numeric strings via `parse_str_numbers`, absorbing celulartable's type parsing ([ce5362b](https://github.com/Opus-Perpetuus/flexablelib/commit/ce5362b))
* `max_width` and `too_narrow_message` for tables that cannot fit ([f8309b8](https://github.com/Opus-Perpetuus/flexablelib/commit/f8309b8))
* `Table.missing` sentinel for building tables with gaps ([c54fa06](https://github.com/Opus-Perpetuus/flexablelib/commit/c54fa06))


### Bug Fixes

* measure and pad cells by visible width, fixing alignment for CJK, Hangul and emoji ([7a350d2](https://github.com/Opus-Perpetuus/flexablelib/commit/7a350d2))
* exclude hidden rows from column width measurement ([#22](https://github.com/Opus-Perpetuus/flexablelib/issues/22)) ([e480f4e](https://github.com/Opus-Perpetuus/flexablelib/commit/e480f4e))
* shrink the widest column first instead of every column in proportion ([#16](https://github.com/Opus-Perpetuus/flexablelib/issues/16)) ([842f64e](https://github.com/Opus-Perpetuus/flexablelib/commit/842f64e))
* never hand a column a width budget of zero, which raised from textwrap ([#14](https://github.com/Opus-Perpetuus/flexablelib/issues/14)) ([842f64e](https://github.com/Opus-Perpetuus/flexablelib/commit/842f64e))
* with auto_wrap off, the trimmed table now fits the terminal (Known Issue #2) ([842f64e](https://github.com/Opus-Perpetuus/flexablelib/commit/842f64e))


### Performance Improvements

* C extension for text measurement, 17-34x on the hot path, with a pure-Python fallback ([23981d4](https://github.com/Opus-Perpetuus/flexablelib/commit/23981d4))

### [1.1.5](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.1.4...v1.1.5) (2022-07-11)


### Bug Fixes

* Wasn't possible to add empty rows. ([7a94a3f](https://github.com/Opus-Perpetuus/flexablelib/commit/7a94a3f94438ebdab16d21dd80d4c1bc66be872e))

### [1.1.4](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.1.3...v1.1.4) (2022-07-11)


### Bug Fixes

* Accidental import. ([47e798a](https://github.com/Opus-Perpetuus/flexablelib/commit/47e798a9019b918b47ace50d5fe5683864e5e886))
* Auto trimming fixed. ([92e3a66](https://github.com/Opus-Perpetuus/flexablelib/commit/92e3a668fb931da0225b375d03c72f2ce9e357d0))
* Auto-wrapping fixed. ([4b8d631](https://github.com/Opus-Perpetuus/flexablelib/commit/4b8d631dc9f7dbe65053e25b854dc61c7d6fbb64))
* Autwrapping with index shown fixed. ([cbcb70c](https://github.com/Opus-Perpetuus/flexablelib/commit/cbcb70c8a08c5572553a3b46cad822cc316d5025))
* Columns not showing wen passing less headers in class args. ([1559fe4](https://github.com/Opus-Perpetuus/flexablelib/commit/1559fe41f347130e44f07c67cdd464ca23f0cf68))
* Passing extra headers causes an IndexError. ([e5a3e42](https://github.com/Opus-Perpetuus/flexablelib/commit/e5a3e427cf226d6eb4e58fb658d5068be1700edd))
* Using rows and headers arguments gives error. ([0479cd5](https://github.com/Opus-Perpetuus/flexablelib/commit/0479cd569396db5a08c9b51be7816b53e0e0f8f9))

### [1.1.3](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.1.2...v1.1.3) (2022-05-07)


### Bug Fixes

* more accidental imports ([25e4c88](https://github.com/Opus-Perpetuus/flexablelib/commit/25e4c88e0feab8f154547ae159d0d7d8fff0750b))

### [1.1.2](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.1.1...v1.1.2) (2022-05-07)


### Bug Fixes

* accidental import. ([736ab4d](https://github.com/Opus-Perpetuus/flexablelib/commit/736ab4dc281cb766f9726512e3505a5bb17fc0cc))

### [1.1.1](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.1.0...v1.1.1) (2022-05-07)


### Bug Fixes

* adding column of different size causing misplaced missing values. ([66abc50](https://github.com/Opus-Perpetuus/flexablelib/commit/66abc5082488c734ffd9329be09f9dc6ea86683b))
* unintended info printing on console. ([560af0a](https://github.com/Opus-Perpetuus/flexablelib/commit/560af0aa8016ab71ad11f9f7ce29375543c192a9))

## [1.1.0](https://github.com/Opus-Perpetuus/flexablelib/compare/v1.0.0...v1.1.0) (2022-05-07)


### Features

* added auto-wrapping for string columns. ([0cacdef](https://github.com/Opus-Perpetuus/flexablelib/commit/0cacdef34c738d0d611440ab393f474f37858ae3))
* added float parsing and alignment ([1a65acd](https://github.com/Opus-Perpetuus/flexablelib/commit/1a65acd7a3fc7deb7331de4bed20a9d276d1a87d))
* added show_index option ([8b8d328](https://github.com/Opus-Perpetuus/flexablelib/commit/8b8d328af591a7d0edd288d80af029837f300f81))
* auto-wrap depends on the auto_wrap option. ([a1e09e5](https://github.com/Opus-Perpetuus/flexablelib/commit/a1e09e50ec913343b5b48b679cf08128ba74a383))
* column data trimming added. ([f53503b](https://github.com/Opus-Perpetuus/flexablelib/commit/f53503bc0b1bf3bd342286ba5cb16354ab8ee4ab))
* show_empty_columns, show_empty_rows options ([a7e4288](https://github.com/Opus-Perpetuus/flexablelib/commit/a7e428845254d68368e9bce6a7fbb4a59fe4046f))


### Bug Fixes

* add_column omitting columns_with_i ([4cc900d](https://github.com/Opus-Perpetuus/flexablelib/commit/4cc900d25c494fbc2dcf4b58a7c7794c42d22b81))
* auto-wrapping doesn't wrap columns "equally". ([9ba68ab](https://github.com/Opus-Perpetuus/flexablelib/commit/9ba68aba7c8c7494c33682368921802bc5167436))
* empty column and row hiding working bad ([76979e9](https://github.com/Opus-Perpetuus/flexablelib/commit/76979e9b803491e6335cdcca8f7417f99abf8542))
* float columns weren't considering header size ([f8ffce3](https://github.com/Opus-Perpetuus/flexablelib/commit/f8ffce38a2b97d409ca7ba37677280d8ff329c68))
* header wrapping wasn't working ([09b5136](https://github.com/Opus-Perpetuus/flexablelib/commit/09b513653f89dc61331301c2be5b1506366d0fdc))
* hiding empty r/c when showing i behaving bad ([823776a](https://github.com/Opus-Perpetuus/flexablelib/commit/823776ae5b1ca9b9210a8cd8337847a79fd5625f))
* index displays incorrectly when hiding empty rows ([6054dda](https://github.com/Opus-Perpetuus/flexablelib/commit/6054ddae743df58907802c1467f8993d937c7df7))
* large missing val. in float col. causes bad alignment ([565d58c](https://github.com/Opus-Perpetuus/flexablelib/commit/565d58c9db550d63d634c1f49c972a7c8beb7b8f))
* missing value was a normal value and was affecting alignment ([a01d4fa](https://github.com/Opus-Perpetuus/flexablelib/commit/a01d4fa1b7dcc03f3ba78f31b9984ba7a7f4d334))
* read_json not closing json ([6702f53](https://github.com/Opus-Perpetuus/flexablelib/commit/6702f5330f11d1f2a70b811e68f9a26447a065f6))
* table with index wasn't auto-wrapping ([23457a5](https://github.com/Opus-Perpetuus/flexablelib/commit/23457a542733a40931f875db76f2a62939ffa93e))
* when displaying index and adding rows table data messes up. ([3c0a724](https://github.com/Opus-Perpetuus/flexablelib/commit/3c0a7245dd09597ac46028bf31a03d37014c0ccc))
* when showing i table data displays incomplete. ([b33ed42](https://github.com/Opus-Perpetuus/flexablelib/commit/b33ed42d064b1875e70357dedc1b2005ba396379))
* wrapping wasn't working ([cf63647](https://github.com/Opus-Perpetuus/flexablelib/commit/cf63647a741dec0867cb702d75d16c3b0301d3e1))
