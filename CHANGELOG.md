# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [3.0.3] - 2026-11-11

### Fixed
- A leftover `ESC[0m` kept by `strip_by_width` no longer lands in the
  padded text of a coloured merge and closes the fill mid-cell. The
  background now covers the whole interior rectangle, including internal
  separators and padding (theme `dark` and other themes).
- Column-only styles again draw a top and bottom rule around a
  multi-column merge, clamped to the merge width, with `├`/`┤` tees that
  do not bleed into neighbouring cells. A vertical-only merge still
  gets no cap.
- Junctions on a fully absorbed separator (side-by-side merges, or a
  rule that is almost entirely merge interiors) are repaired even when
  the line no longer looks like a rule, so leftover `┼`/`╟`/`╢` become
  `│`/`║`.
- Dotted-row `:` junctions become `.` when a vertical arm is missing;
  markdown header separators stay `|---|---|` so the format remains
  valid; ascii-rounded outer frames are not rewritten.

### Added
- A glyph-topology verifier (`flexablelib.box_topology`) and tests over
  every style, with and without colour, covering horizontal, vertical
  and 2D merges at corners, edges, and next to the header or footer.
  Colour must not change the glyphs, and every interior column of a
  coloured merge must carry that merge's background.

## [3.0.2] - 2026-11-11

### Fixed
- Merge and zebra backgrounds now fill a single rectangle: the interior of
  the cell or merge, including any separators absorbed between its rows.
  The fill no longer stairsteps at the corners, leaks onto neighbouring
  cells, or paints the outline glyphs (`─`, `═`, tees and crossings).
- Horizontal rules keep `border_color` (or the default foreground) and do
  not inherit a cell or zebra background, so a `_rows` style no longer
  loses its border colour or leaves an uncoloured gap on a junction.
- A leftover `ESC[0m` after a merge that already closed its colour is
  dropped, so `column_colors` / zebra next to a coloured merge no longer
  emit a doubled reset.
- Theme `slate` (psql + zebra) and other themes paint a 2D merge as a
  solid rectangle; `border_color` no longer cuts through the label.
- Column-only styles (verticals but no rule between rows) no longer
  insert a synthetic cap around a multi-column merge. That cap blanked
  neighbour cells on a new line and made them look merged. The span is
  shown by dropping the internal vertical; when the merge has a colour,
  the rectangular fill marks it. Existing header and end rules still
  get their tees repaired.

## [3.0.1] - 2026-11-11

### Fixed
- A merged region drawn over a cell with ANSI colour no longer leaves a
  stray `ESC[0m` in the output. The reset is now added only when a colour is
  actually still open where the merge starts.
- Slicing coloured text (`slice_by_width`, and merges that use it) no longer
  appends a second reset after text that already closed its colour.

### Added
- `text_width.sgr_is_open(text)` reports whether text leaves a colour or
  attribute switched on.
- Tests for merge/slice escape handling and for `from_markdown` / `from_html`
  edge cases (prose around a table, corrupt or malformed embedded payloads,
  rowspans in the body and across the header).

## [3.0.0] - 2026-11-10

### Changed (breaking)
- Every border style has a new name that describes how it looks. A name
  reads as the line family (`single`, `rounded`, `double`, `double_frame`,
  `double_horizontal`, `double_header`, `dashed`, `dotted`, `ascii`,
  `tilde`, `lines`, `underlined`, `borderless`, or a text format:
  `markdown`, `org`, `psql`, `rst`), then optional modifiers:
  `_double_underline` (double rule under the header), `_rows` (a rule
  between every row) and `_open_header` / `_open_body` / `_open` (no
  column separators in the header, the body, or both).
- The default style is now called `ascii_double_underline_open_header`
  (formerly `grid_eheader`); it looks the same.
- `presto` was identical to `psql`, and `blocks` to `blank`, so each pair
  now has one name: `psql` and `borderless`. The catalogue has 54 styles.
- `table.possible_styles` lists only the new names.

### Deprecated
- The old names still work: setting one (on `style_name` or in the
  constructor) uses the new style and emits a `DeprecationWarning`. They
  are listed in `flexablelib.style_compositions.DEPRECATED_STYLE_NAMES` and
  will be removed in a future major release.

### Old → new names

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

`rounded`, `markdown`, `psql` and `ascii_rounded` keep their names.

### Documentation
- `style_examples.md` is generated by `tools/style_examples.py` and shows
  all 54 styles grouped by family, with a description of each and the
  old → new table.

## [2.3.1] - 2026-11-10

### Fixed
- ``to_html(paginate=None)`` raised ``TypeError``; ``None`` now means no
  paging, like ``0``.
- ``index_start = None`` / ``index_step = None`` raised ``TypeError``;
  they now fall back to the defaults (``0`` and ``1``), as non-numeric
  strings already did.

### Internal
- Removed unused helpers from ``flexablelib.utils`` (``float_format``,
  ``is_list``/``is_tuple``/``is_dict``/``is_set``/``is_str``/``is_bytes``,
  ``length_of_elements``, ``flatten``, ``delete_repetitions``). None were
  part of the public API or called anywhere in the package.
- Tests for alignment indicators on ``pipes`` and ``sticks``: centred and
  right markers, wide characters, one-character and zero-width columns.
- Behaviour tests for public edge paths: `add_dividers` with one iterable,
  `hrules=True`, invalid `hrules`/`vrules`/`border_text` arguments,
  `clear_border_texts`, non-callable `row_filter`/`color_rule`, and
  out-of-range `hide_columns`.

## [2.3.0] - 2026-11-07

### Changed (visible behaviour)
- Explicit ``None`` now displays ``missing_value`` (blank by default), just
  like a padding gap or ``table.missing``. Previously it printed ``None``.
  Use the string ``"None"`` to retain that literal output. Applies to every
  style, printing/``compose``, pagination, streaming and transposition.
- A numeric column containing ``None`` keeps its numeric type, alignment
  and decimal axis; wrapping no longer splits its numbers as text.
- Derived tables used for pagination/streaming preserve gaps as missing data
  instead of converting the placeholder to text before inferring types.
  ``Table(rows=t.rows)`` preserves the visible cells with matching settings.
  Raw rows and export missing-value semantics are unchanged.

### Tests and documentation
- Regressions across all 56 styles, three missing-value displays and all
  render paths; raw/formatted exports, row round-trips and numeric wrapping.
- The stress matrix now compares None, padding sentinels and row round-trips
  in every style/theme and mode; stream budgets include decimal-axis width
  and a feasible terminal budget (narrow fits are covered outside stream).
- README and ``docs/MISSING_VALUES.md`` explain the visible change.

## [2.2.4] - 2026-11-07

Found by a new stress matrix (``tools/stress_matrix.py``): every style and
theme on a 30x50 table of mixed data (CJK, emoji, multi-line, ``None``),
each feature alone, a pairwise covering set of all feature options, and
"everything at once" combos, checking line widths, border junctions,
visible rows, export order and determinism. A reduced version runs in the
test suite (``tests/test_stress_matrix.py``).

### Fixed
- Fitting a table to the terminal (``max_width``) or capping one column
  (``column_max_width``) left-aligned every other int column and the index,
  even ones that were not shortened. Only a column that really loses
  characters is turned into text now.
- ``add_divider`` / ``divide_every`` in a style without inter-row rules drew
  a run of ASCII ``-`` across the column lines (``│ a │`` / ``-------``). The
  divider now uses the style's glyphs (``├───┼───┤``, ``╞═══╪═══╡``,
  ``+---+``, ``|---|`` for markdown/pipes/orgtbl, edge to edge for
  ``*_ebody`` styles), skipping hidden columns; styles with no column lines
  keep the dashed line.
- Merges in ``tilg_columns``, ``dots``, ``psql``/``presto`` and other
  non-box styles got light box glyphs (``│ ├ ┴``) for their caps. ASCII
  column lines now join with ``+`` and ``dots`` with ``:`` (dividers in
  ``dots`` too).
- ``expand_to_window`` with ``column_max_width`` pulled a column that was
  already wider than its cap (numbers are never cut) back to the cap, so its
  cells overflowed the rules and the frame broke (also on ``paginate`` pages).
- ``stream()``:
  - with ``show_index`` and ``column_min_width`` or ``column_max_width``
    raised ``IndexError``; with ``show_index`` alone nothing was frozen and
    the lines grew as rows arrived. The index width is now reserved for a
    sized input (``len(rows)``), including roman numerals.
  - with ``zebra`` or cell backgrounds lost every row and printed the bottom
    border after the header and after each row.
  - with ``show_headers=False`` on an empty table raised ``ValueError``
    (``column_max_width must be >= 1``), and with ``panel`` / ``shadow`` on a
    borderless style closed the panel after the first row.
- ``title`` and ``caption`` were not centred on a table with no rows.
- ``Table.from_csv`` accepts CSV text, so ``from_csv(table.to_csv())``
  round-trips like ``from_markdown`` and ``from_html`` already did. Paths
  and open handles work as before.

## [2.2.3] - 2026-11-06

### Fixed
- ``Table(headers=..., rows=...)`` with a short first row and a wider later
  row no longer invents a ghost ``column N``. Padding now uses the live
  column count after every row is loaded, so later cells that already fill
  the remaining headers are enough.
- ``add_row`` / ``add_column`` reject bare ``str`` / ``bytes`` data with
  ``TypeError`` instead of expanding them into one cell per character.
  ``Table(rows=...)`` does the same for a string ``rows`` value or string
  row entries. Wrap a single string cell in a list.
- ``show_empty_columns`` coerces with ``bool(...)``, matching
  ``show_empty_rows``.

## [2.2.2] - 2026-11-05

### Fixed
- ``zebra = True`` (and ``row_stripe = True``) raised ``ColourError: unknown
  colour: 'true'`` when ``use_colors`` was on. ``True`` now enables a default
  odd-row ``reverse`` stripe; ``False`` clears it. Other non-spec values raise
  ``TypeError`` at assignment time instead of blowing up later in ``compose()``.
- ``parse_str_numbers = True`` before ``add_column`` / ``add_row`` left digit
  strings unparsed, contrary to the documented "order does not matter". New
  cells are parsed on the way in, matching ``set_cell`` and the re-parse that
  already ran when the flag was turned on after the data was there.

## [2.2.1] - 2026-11-04

### Fixed
- A merge on the first or last drawn row -- often where ``sort_by`` or
  ``row_filter`` puts it -- rewrote the whole border next to it: the top
  border under a ``title`` (with ``show_headers=False``) came out as an inner
  rule (``├───┴───┼───┤``), the bottom border above a ``caption`` lost its
  corners, ``markdown``/``orgtbl`` header separators turned into ``+---+``,
  and ``*_eheader`` header separators kept a junction over the merged span.
  Only the junctions over the merge change now, and each keeps the arms the
  lines around it really have.
- A merge covering a column in ``hide_columns`` (or a hidden empty column)
  that is left with a single drawn column printed ``.``: the column was sized
  without the merge text. It now shrinks to that column and the column fits
  the text, as the exports already did.

### CI
- Wheels: one path to PyPI. Only the ``vX.Y.Z`` tag push builds and
  publishes; publishing the GitHub release no longer starts a second, duplicate
  build that competed for the macOS runner. Publishing waits for all 28 wheels
  (Linux manylinux + musllinux, Windows, macOS arm64; CPython 3.8-3.14) and
  the sdist, checks the count and that the tag matches ``package.json``, and
  is safe to re-run. One run per ref (``concurrency``).
- The real reason the macOS job never started: GitHub's hosted macOS arm64
  runners are short of capacity, and a job no runner picks up is cancelled
  after ~15 minutes. A new ``wheels-retry`` workflow re-runs the failed or
  cancelled jobs of a tag run (up to three more attempts), so publishing
  finishes on its own.
- Actions moved off Node 20: ``checkout@v5``, ``setup-python@v6``,
  ``upload-artifact@v6``, ``download-artifact@v7``.

## [2.2.0] - 2026-11-04

### Changed (breaking)
- Exports now write the table as ``compose()`` shows it. ``to_csv``,
  ``to_markdown``, ``to_html``, ``to_rst``, ``to_asciidoc``, ``to_latex``,
  ``to_excel``, ``to_records`` and ``_repr_html_`` follow ``sort_by``
  (``sort_reverse``, callables) and ``row_filter``, leave out
  ``hide_columns`` (and empty rows/columns when ``show_empty_rows`` /
  ``show_empty_columns`` are off), and number the index by display position.
  Before, they wrote every stored row in insertion order.
- The text exports (CSV, Markdown, HTML, RST, AsciiDoc, LaTeX) hold the
  formatted strings ``compose()`` prints -- ``float_format``,
  ``int_format``, ``leading_zeros``, ``custom_format``, ``strip_cells`` --
  without padding or ANSI codes. Before, they wrote ``str()`` of the raw
  value. Gaps stay empty strings. Reading such an export back gives the
  printed text (``'1,200'`` stays a string).
- ``to_records()`` keeps the stored Python values (numbers stay numbers, gaps
  ``None``) but in display order, filtered, without hidden columns.
- ``to_excel()`` keeps numbers numeric; other cells hold the displayed text.
- Merges keep their display position, as in ``compose()``; a merge split by
  ``show_empty_rows=False`` is dropped and one over hidden columns shrinks.
- ``Table.rows`` is unchanged: the stored data in insertion order.

### Added
- ``to_records(formatted=True)`` returns the displayed strings.
- ``to_excel()`` turns simple ``int_format`` / ``float_format`` /
  ``custom_format`` specs and ``leading_zeros`` into Excel number formats
  (``',d'`` -> ``#,##0``, ``'.2f'`` -> ``0.00``, ``'.1%'`` -> ``0.0%``,
  ``'$ {:,.2f}'`` -> ``"$ "#,##0.00``).
- ``to_html()`` sorts numeric columns on the stored number, so formatted
  values such as ``1,200`` sort correctly in the browser.

## [2.1.1] - 2026-11-04

### Fixed
- ``paginate()`` and ``stream()`` dropped most of the table's settings:
  ``float_format``, ``int_format``, ``custom_format``, ``leading_zeros``,
  ``str_align``/``int_align``/``float_align``/``bool_align``,
  ``column_colors``, ``max_table_width``, ``show_empty_rows`` and border
  texts, among others. They now render like ``compose()``.
- ``paginate()`` and ``stream()`` re-parsed text cells, so ``'1e3'`` printed
  as ``1000.0``. Values are kept as stored.
- ``paginate()`` ignored ``sort_by`` and ``row_filter``, and with
  ``show_empty_rows=False`` a page could lose visible rows. Pages now hold
  the rows in display order, the index keeps counting across pages, and
  ``row_colors``, ``cell_colors``, ``cell_valign``, ``color_rule``,
  ``zebra``, ``footer_rows``, dividers and merges follow their rows (a merge
  split by a page break is dropped).
- ``stream()`` now honours ``row_filter``, ``row_colors``, ``cell_colors``,
  ``color_rule``, dividers and merges. ``sort_by`` is still not applied while
  streaming (documented).
- ``color_rule`` received another row's value after ``sort_by`` or
  ``row_filter`` reordered the body, so it painted the wrong cells.
- Setting ``index_title`` (even to its current value) shifted the column
  alignments and widths by one column.

## [2.1.0] - 2026-11-03

### Changed (breaking)
- ``Table.rows`` returns a copy (new outer list and new row lists) with
  ``None`` in empty or missing cells, the same values ``to_records`` gives;
  editing it no longer changes the table. Code that edited ``t.rows`` in place
  should use ``add_row`` and the new ``set_cell(row, column, value)``.

### Added
- ``Table.set_cell(row, column, value)``: replace one cell by row position and
  column position or header (``table.missing`` empties it). It keeps the row
  and column stores in sync, which editing ``t.rows`` never did.

## [2.0.21] - 2026-11-03

### Fixed
- Text exports (``to_csv``, ``to_markdown``, ``to_rst``, ``to_asciidoc``,
  ``to_latex``, ``to_html``) and ``to_records`` wrote
  ``<flexablelib.utils.ValuePlacer object at ...>`` for gaps -- short rows
  padded by the table, NaN/NULL from the readers, ``table.missing``. Gaps
  now export as empty cells (``None`` in records).
- ``include_index=True`` wrote ``<...IndexCounter object at ...>`` in every
  row, and left the index out when ``show_index`` was off. The index is now
  numbered like the rendered one (``index_start``, ``index_step``,
  ``index_title``, ``roman_index``).
- A float column whose numbers have no decimal point (``1e+20``) rendered
  one character wider than its border.
- ``vrules='none'`` kept the corners of the horizontal rules, which made
  them two columns wider than the rows.
- ``transpose()`` / ``rotate()`` showed gaps blank instead of the missing
  value and exported the sentinel's repr; the missing value is carried over.
- ``merge_cells`` with a non-integer coordinate (a float, or a
  ``(row, column)`` pair) raises a ``TypeError`` naming the argument instead
  of a comparison error.
- ``plain`` style: the blank line under the header was one column shorter
  than the rows (no junction between columns), so ``compose()`` output was
  not rectangular.

### Tests
- Every style renders lines of equal terminal width with CJK / emoji
  headers and ``column_max_width``. Pins that ``*_eheader`` styles draw the
  header row without column separators by design.

## [2.0.20] - 2026-11-02

### Fixed
- ``column_min_width`` and ``column_max_width`` are checked when set. A
  non-integer entry raised a bare ``int()`` error only at print time, and a
  cap of ``0`` or below silently trimmed every cell to ``.``. Both now raise
  ``ValueError`` naming the option; ``None`` still means no bound.
- ``from_html`` with a negative ``index`` past the first table raised a bare
  ``list index out of range``; it now gives the same message as a positive
  index that is out of range.

### Tests
- Reader coverage: CSV without header and ragged rows, dialect plus
  delimiter, numeric-looking text, Markdown from bytes and paths, HTML from
  paths, records with dict rows and generator input.

## [2.0.19] - 2026-11-01

### Fixed
- ``column_max_width`` trims by terminal columns and line by line: CJK text
  is cut to fit, emoji ZWJ sequences are no longer over-trimmed and
  multi-line cells keep their lines instead of collapsing to ``...``.
- A width cap never narrows a column below content that cannot shrink (the
  index column, a float's integer digits, a 2-column glyph in a 1-column
  cap); the frame used to come out narrower than the text.
- ``show_index`` with ``column_max_width`` raised ``IndexError`` or trimmed
  the wrong column.
- Float columns fill wider columns (``column_min_width``, a long header)
  instead of leaving rows short.
- A numeric-looking header (``'0'``, ``'2024'``) over a float column crashed
  with ``valign`` and overflowed without it; it is now right-aligned.
- ``sort_by`` on mixed types or ``None`` raised ``TypeError``. Numbers sort
  before text, other types group by type, and missing values (``None``,
  NaN) always go last, also with ``sort_reverse``.
- ``border_color`` and ``border_text`` emitted ANSI escapes with
  ``use_colors=False``, under ``NO_COLOR`` or into a pipe (regression from
  2.0.11). Coloured themes now leave ``use_colors`` on auto instead of
  forcing it on, so ``apply_theme`` output to a file stays clean; set
  ``use_colors = True`` to force colour.
- Left/right ``border_text`` overwrote cell text on styles without an outer
  border, and started on the title line when a ``title`` was set.
- ``sticks`` alignment indicators overhung columns narrower than 3.
- ``add_divider`` on styles without a body rule (``dashes``,
  ``grid_eheader``) drew a rule too wide after a wrapped row.
- Merged cells follow ``cell_padding`` (0, 2, 3...); ``hrules`` with merges
  on styles whose frame has no horizontal glyph raised ``TypeError``.
- Three or more repeated headers (``['x', 'x', 'x']``) produced a duplicate
  name and ``compose()`` raised ``IndexError``.
- Readers: ``from_markdown`` unescapes ``\|``; ``from_records`` accepts the
  dicts ``to_records`` returns; ``from_html`` reads ``to_html`` pages, lays
  out ``rowspan``/``colspan`` (later cells used to slide left) and restores
  them as merges, and takes the ``<th>`` header from the selected table.
- HTML/XLSX colours: a background-only ``'on red'`` exported as red text,
  and ``greyNN`` / ``color:N`` colours exported nothing.
- ``to_latex`` escapes ``|``, ``<`` and ``>``.

### Tests
- Regression tests for every fix above and behaviour tests for exporters,
  readers and colour helpers (coverage 87% -> 90%).

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
- The test suite passes against an installed package with only ``tests/``,
  ``pytest.ini`` and ``style_examples.md`` copied next to it (the conda-forge
  recipe layout, #26): checks that need a source checkout now skip there.

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
