<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/logos/export/logo-1024.png" alt="flexablelib" width="440">
</p>

<p align="center">
  <strong>Fast, dependency-free terminal tables — and optional packages for full terminal apps.</strong><br>
  54 border styles · ANSI colours · cell merges · decimal alignment · width fitting · CSV / Markdown / HTML / Excel / LaTeX I/O · grids · 80+ terminal components · C-accelerated frames
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
with an optional C speed-up**, and is covered by **4,500+ tests** on Python
3.8 – 3.14 (Linux, Windows, macOS).

Since 3.3.0 the same library builds **complete interactive terminal
applications**: keyboard focus, key bindings, dialogs, notifications, 80+
ready-made components (inputs, dates, tables, forms, menus, charts, dialogs)
and optional C code that computes each interface frame. All of it is opt-in;
`pip install flexablelib` stays a single dependency-free package.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/quickstart.png" alt="A rounded flexablelib table built in a few lines, with its output" width="620">
</p>

## Install

`pip install flexablelib` — the core: tables, cards, grids, widgets. No dependencies.

| Extra | Brings | For |
| --- | --- | --- |
| `flexablelib[tui]` | `flexablelib-tui` | interactive apps: `App`, keyboard input on Linux, macOS and Windows, focus, key bindings, dialogs, notifications, `Live` diff redraw |
| `flexablelib[components]` | `flexablelib-components` (+ tui) | 80+ terminal components: inputs, dates, tables, forms, navigation, dialogs, charts |
| `flexablelib[speed]` | `flexablelib-speedups` | C code for interface frames: cutting, padding, borders and frame diffs |
| `flexablelib[pandas]`, `[excel]`, `[html]` | pandas, openpyxl, lxml | readers and writers |
| `flexablelib[all]` | everything above | |

Quote the extras in shells that expand brackets: `pip install "flexablelib[tui,components,speed]"`.
Details: [docs/INSTALL.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/INSTALL.md).

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/install.png" alt="Checking which C backends are live" width="520">
</p>

## Terminal applications

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/01_demo_140.png" alt="A complete back-office terminal app: sidebar, KPI cards, line chart, activity timeline and orders table">
</p>

[examples/admin.py](https://github.com/Opus-Perpetuus/flexablelib/blob/main/examples/admin.py) is a complete back-office app
built only with flexablelib: `AppShell` (sidebar, top bar, pages), `Stat`
cards, a braille `LineChart`, a `Timeline`, a `DataTable` bound to a
`FilterBar` (`estado:pagado total>5000`), forms with validation, a command
palette (Ctrl-K), dialogs and notifications. Run it with
`python examples/admin.py`; `--frame 120x36 --keys "tab,down,enter"` prints a
single frame instead (that is how these images are made).

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/app.png" alt="A table and a form side by side in an App, driven by keys" width="620">
</p>

<table>
<tr>
<td width="50%"><b>Keyboard and focus</b> — Tab, arrows, Enter, modal dialogs<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/04_teclado_foco.png" alt="Six frames of keyboard navigation" width="420"></td>
<td width="50%"><b>Forms</b> — required fields, validators, masks, notifications<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/05_formulario.png" alt="A form with validation errors and a success notification" width="420"></td>
</tr>
<tr>
<td><b>Filter and sort</b> — <code>estado:pagado total&gt;5000</code>, keys 1–9 sort<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/02_demo_pedidos.png" alt="Orders filtered and sorted" width="420"></td>
<td><b>Narrow terminals</b> — the sidebar hides, cards reflow<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/03_demo_angosto.png" alt="The same app at 80 and 64 columns" width="420"></td>
</tr>
<tr>
<td><b>Command palette and help</b><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/06_comandos_ayuda.png" alt="Command palette and help dialog" width="420"></td>
<td><b>No colour</b> — zero escape sequences, same layout<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/07_sin_color.png" alt="The app without colour" width="420"></td>
</tr>
</table>

### Components

`flexablelib[components]` adds 80+ components, each rendered at any width,
in colour or plain text: the full list, what each does and its keys is in
[docs/COMPONENTS.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/COMPONENTS.md).

<table>
<tr>
<td width="50%"><b>Inputs</b> — text, password, numbers, money, masks, expressions, JSON, scanners, choices, colours, files<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/08_entradas.png" alt="Input components" width="420"></td>
<td width="50%"><b>Dates and times</b> — calendar, date, time, week, month, ranges, timer<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/09_fechas.png" alt="Date components" width="420"></td>
</tr>
<tr>
<td><b>Display</b> — badges, alerts, code, Markdown, HTML, timelines, steps, stats, charts<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/10_visualizacion.png" alt="Display components" width="420"></td>
<td><b>Navigation</b> — tabs, menus, sidebar, wizard, tree, command palette, app shell<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/11_navegacion.png" alt="Navigation components" width="420"></td>
</tr>
<tr>
<td><b>Data</b> — interactive table, filters, editable table, catalog, forms, login<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/12_datos.png" alt="Data components" width="420"></td>
<td><b>Dialogs</b> — modal, confirm, prompt, loading, popover<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/13_dialogos.png" alt="Dialog components" width="420"></td>
</tr>
<tr>
<td colspan="2"><b>New in 3.6.0</b> — signature pad, stopwatch, a vertical stack that shares its height and follows the focus, focus shown without colour, forms that collect nested fields and editable tables, scanners that keep the code read, catalog cards with pictures, pictures downloaded with an <code>Authorization</code> header, a validation summary from a list of errors<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v36/01_novedades.png" alt="3.6.0 components: SignatureInput, Stopwatch, VStack, focus markers, ScanInput, CatalogGrid with images, ValidationSummary" width="520"></td>
</tr>
<tr>
<td colspan="2"><b>New in 3.7.0</b> — scroll views that follow the focus, menus and sidebars that keep to their height, responsive form columns with spans, tables that fill their slot, an accessible grid with its own audit, a status line for screen readers<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v36/02_novedades_370.png" alt="3.7.0 components: ScrollView following the focus, Menu and Sidebar windows, Form grid, DataTable fill, GridView, StatusLine" width="520"></td>
</tr>
</table>

### Keyboard, mouse and accessibility

Since 3.4.0: [docs/INPUT.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/INPUT.md) · [docs/ACCESSIBILITY.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/ACCESSIBILITY.md) · [docs/FOLIOS.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/FOLIOS.md).

<table>
<tr>
<td width="50%"><b>Every key detected</b> — F1–F24, Ctrl/Alt/Shift/Super, paste, focus, mouse — <code>examples/keys.py</code><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/01_detector_teclas.png" alt="Live key detector" width="420"></td>
<td width="50%"><b>Mouse in every component</b> — click, wheel, drag<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/02_raton.png" alt="Clicks on buttons, tabs, tables and calendars" width="420"></td>
</tr>
<tr>
<td><b>Focus visible without colour</b> — text markers, not colour alone<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/03_foco_visible.png" alt="Focus with and without colour" width="420"></td>
<td><b>High contrast</b> — WCAG AAA text, checked by the tests<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/04_alto_contraste.png" alt="High-contrast theme with contrast ratios" width="420"></td>
</tr>
<tr>
<td><b>Colour-blind themes</b> — deuteranopia, protanopia, tritanopia — simulated<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/05_daltonismo.png" alt="Status colours under colour-blindness simulation" width="420"></td>
<td><b>Screen readers</b> — linear text, roles, labels, announcements<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/06_lector_pantalla.png" alt="Screen-reader linear output" width="420"></td>
</tr>
<tr>
<td><b>ASCII and reduced motion</b> — no Unicode, still spinners<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/07_ascii.png" alt="The app in ASCII mode" width="420"></td>
<td><b>Folios</b> — IDs without thousands separators, money with them<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/08_folios.png" alt="Folio columns versus money columns" width="420"></td>
</tr>
<tr>
<td><b>One name per key</b> — xterm, rxvt, Linux console, kitty, modifyOtherKeys, Windows<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/10_protocolos.png" alt="Key names across protocols" width="420"></td>
<td><b>C acceleration</b> — ASCII fallback and click zones<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v34/09_benchmark.png" alt="C versus Python timings" width="420"></td>
</tr>
</table>

### Pictures in the terminal

Since 3.5.0: [docs/IMAGES.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/IMAGES.md) — kitty, iTerm2, sixel, Unicode blocks, ASCII, then a link to the browser, then a warning. Real terminals under Xvfb.

<table>
<tr>
<td width="50%"><b>kitty graphics protocol</b> — detected, Unicode placeholders<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/01_kitty.png" alt="A picture in kitty" width="420"></td>
<td width="50%"><b>iTerm2 inline images</b> — WezTerm, iTerm2, VS Code, Konsole<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/02_iterm2_wezterm.png" alt="iTerm2 images in WezTerm" width="420"></td>
</tr>
<tr>
<td><b>sixel</b> — xterm, foot, mlterm, Windows Terminal<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/03_sixel_xterm_foot.png" alt="sixel in xterm and foot" width="420"></td>
<td><b>Unicode blocks</b> — half blocks, quadrants, sextants<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/04_bloques_unicode.png" alt="Unicode block pictures" width="420"></td>
</tr>
<tr>
<td><b>Braille and ASCII</b> — mono with NO_COLOR, ASCII without Unicode<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/05_braille_ascii.png" alt="Braille and ASCII pictures" width="420"></td>
<td><b>Inside Grid, Card and App</b> — the frame diff keeps working<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/08_card_grid_app.png" alt="Pictures inside a dashboard" width="420"></td>
</tr>
<tr>
<td><b>Link to the browser</b> — OSC 8, Enter or click opens it<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/06_enlace_osc8.png" alt="Link fallback" width="420"></td>
<td><b>No browser, no display</b> — a warning, nothing opened<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/07_aviso_sin_navegador.png" alt="Warning when no browser is available" width="420"></td>
</tr>
<tr>
<td><b>Redraws in kitty, xterm and WezTerm</b> — ImageViewer in an App<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/09_visor_redibujo.png" alt="ImageViewer switching pictures" width="420"></td>
<td><b>C acceleration</b> — resize, quantize, sixel, blocks<br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v35/10_benchmark.png" alt="C versus Python picture timings" width="420"></td>
</tr>
</table>

### Speed

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/v33/15_benchmark_c_vs_python.png" alt="Milliseconds per frame without C, with the core C measurement and with the C frame code" width="760">
</p>

Every frame of an interface is re-laid out and diffed against the previous one;
only changed lines are written. `flexablelib[speed]` moves the per-line work
(measuring, cutting, padding, border junctions, the diff) to C: a full
back-office screen at 160×48 takes **0.47 ms** (2,100 fps) instead of 6.4 ms
in pure Python. Results are identical with and without C — the test suite
checks both on random input — and `FLEXABLELIB_FRAMES=python` switches the C
code off. Method and numbers: [docs/ACCELERATION.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/ACCELERATION.md).

## 30-second quickstart

The image at the top is the whole program. Numbers align on the decimal
point, colours never break alignment, and the same table exports anywhere:

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/exports.png" alt="Markdown and CSV exports of a table" width="560">
</p>

## Feature gallery

<table>
<tr>
<td width="50%"><b>Styles</b> — 54 presets, from <code>ascii_rows</code> to <code>borderless</code><br><img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/styles.png" alt="Several border styles" width="260"></td>
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

More: [all 54 styles](https://github.com/Opus-Perpetuus/flexablelib/blob/main/style_examples.md) ·
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
| Border style presets | 54 | many `tablefmt` | — (hrules/vrules toggles) | box styles |
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
- **Wheels.** Prebuilt for CPython 3.8 – 3.14 on Linux (manylinux, musllinux),
  Windows x64 and macOS arm64, for both `flexablelib` and `flexablelib-speedups`. Anywhere else it builds from source or falls
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
  (`ascii_rows`, `ascii_double_underline_rows`, `psql`, `markdown`, …) work on any code page.
- **Typed.** Ships `py.typed` (PEP 561).
- **Stability.** flexablelib follows [semantic versioning](https://semver.org):
  within 3.x, public `Table` attributes and methods are not removed or renamed
  without a deprecation period; new features arrive in minor/patch releases
  and every release is listed in the
  [CHANGELOG](https://github.com/Opus-Perpetuus/flexablelib/blob/main/CHANGELOG.md).
- **Support.** Bugs and requests: [issues](https://github.com/Opus-Perpetuus/flexablelib/issues). Security reports:
  [SECURITY.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/SECURITY.md). Contributions:
  [CONTRIBUTING.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/CONTRIBUTING.md).

### Windows console encoding

Box-drawing styles need a UTF-8 console: run `chcp 65001` and set
`PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8=1`). Windows Terminal is usually
UTF-8 already. The terminal packages enable virtual-terminal output on
Windows consoles themselves.

# Guide

## Usage

Creating a table is simple. An empty table has no data, so it only draws its
frame; a table with columns but no rows — a query that came back empty —
shows its headers rather than raising:

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/empty.png" alt="An empty table and a table with headers only" width="560">
</p>

Data can be added as columns or rows, or alternating each one. Any untitled
column is named automatically.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/columns.png" alt="Adding columns" width="460">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/multiline.png" alt="Rows with line breaks" width="460">
</p>

The table formats new lines and data types automatically, without trying to
parse strings that could be converted to another type.

The `Table` class offers options for showing the index of each row, changing
the style, hiding the headers, and more. See all styles
[here](https://github.com/Opus-Perpetuus/flexablelib/blob/main/style_examples.md). The missing value aligns as if it were of
the same type as the other data in the column, and the row and column counts
ignore the index column (the internal counts include it):

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/index_missing.png" alt="Index column, double_horizontal style and missing values" width="560">
</p>

**Changed in 2.3.0:** an explicit `None` is a missing cell, just like a
padding gap or `table.missing`. It displays `missing_value` (blank by default),
not the text `"None"`. Use the string `"None"` if you want that literal text.
This applies to printing, `compose()`, pagination, streaming, and
transposition in every style.

Missing cells do not turn numeric columns into text: numeric alignment and
the decimal axis are preserved, and `overflow='wrap'` does not split floats
because a column contains `None`. Raw `rows` and exports still represent gaps
as `None`; rendering `Table(rows=table.rows)` reproduces the same cells (copy
headers and display settings too if you changed them).

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/none.png" alt="None displayed as a missing cell" width="520">
</p>

See [missing-cell semantics](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/MISSING_VALUES.md) for migration details.

## Colour

Colour the header, the borders, whole columns, whole rows, or individual cells.
Specs accept names, attributes, 256-colour indexes and hex triples.
`color_rule` receives the original value, so numeric comparisons work directly.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/colour.png" alt="Header, border, column and rule-based colours" width="500">
</p>

Colour is emitted only to a terminal by default, and never when `NO_COLOR` is
set. `FORCE_COLOR` or `table.use_colors = True` overrides that. Because
`compose()` returns a string you may send anywhere, the default errs toward not
embedding escape sequences in something bound for a file.

Widths are measured in terminal columns, not characters, so coloured cells and
CJK or emoji data stay aligned.

## Reading and writing

Readers: `Table.from_csv`, `from_html` (standard library parser),
`from_dicts`, `from_markdown`, `from_pandas` (`flexablelib[pandas]`) and
`from_excel` (`flexablelib[excel]`). Writers: `to_csv`, `to_markdown`,
`to_html` (one self-contained file with inline sorting, filtering and
pagination that works offline), `to_rst`, `to_asciidoc`, `to_latex`,
`to_excel` and `to_records`.

Since 2.2.0 every export writes the table as `print(table)` shows it: rows in
`sort_by` order (with `sort_reverse` and callables), `row_filter` applied,
`hide_columns` left out, and the text formats hold the formatted strings —
`float_format`, `int_format`, `leading_zeros`, `custom_format`, `strip_cells` —
without padding or colour. Empty cells are empty strings.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/readwrite.png" alt="Sorted, filtered and formatted Markdown export and records" width="600">
</p>

`to_records()` keeps the stored Python values (numbers stay numbers, gaps are
`None`) in display order; `to_records(formatted=True)` gives the printed
strings. `to_excel()` writes numbers as numbers and turns simple format specs
(`',d'`, `'.2f'`, `'.1%'`, `'{:,.2f}'`…) into the cell's Excel number format.

Text formats deliver everything as strings, and a column of strings is
left-aligned. `table.parse_str_numbers = True` converts numeric-looking text
so it aligns as numbers; the readers turn it on for you. Values with leading
zeros are left alone, so `'007'` stays a string.

`table.rows` is a copy of the stored data, in insertion order and with `None`
in empty cells (sorting, filtering and formats do not touch it), so editing it
does not change the table. Use `add_row` and `set_cell(row, column, value)`
instead (`column` is a position or a header; `table.missing` empties a cell).

## Merging cells

Render a rectangular block as a single cell, across columns, down rows, or
both. Coordinates are inclusive, zero-based, and ignore the index column.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/merges.png" alt="A vertical merge and a horizontal Total merge" width="560">
</p>

A merge never widens the table — columns are still sized by their unmerged
content — so text longer than its span is truncated.

## Cards, grids, responsive tables and terminal layouts

`Card` draws one record in a frame, in any of the table styles. The title goes
into the top border when the style draws one; `field_columns=2` (or `'auto'`)
lays the fields out as tiles and `actions` adds `[ Action ]` chips:

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/card.png" alt="Two cards" width="520">
</p>

Cards take `style_name`, `theme` (the table themes), `border_color`,
`title_color`, `label_color`, `value_colors`, `color` (a background for the
whole card), `zebra`, `panel` and `shadow`.

`table.render(width)` makes a table responsive: the normal table when it fits,
without its low-priority columns next, squeezed and wrapped after that, and
one card per row when nothing else fits. `width` defaults to `max_width`, then
the terminal width; `responsive=True` makes `print(table)` do the same.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/responsive.png" alt="The same table at 64, 46 and 30 columns" width="560">
</p>

`Grid` places cards, tables, text and other grids in columns that reflow with
the width. Since 3.3.0 a cell can be pinned with `row=` and `column=`; empty
slots are closed in bordered grids (`fill_gaps=False` keeps them open), and
`to_cards()` carries merged cells into every card they cover.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/grid_cards.png" alt="A grid of cards and a grid with pinned cells" width="600">
</p>

A grid can size its columns (`12`, `'auto'`, `'2fr'`, `'30%'`, bounds, or one
layout per width), span rows, share one border with proper junctions and a
title per cell, and fill an exact height. Widgets — `ProgressBar`,
`Sparkline`, `BarChart`, `StatusBar`, `KeyHints`, `LogView`, `Text`, `Rule` —
drop into it, `Screen` pins a header and footer to the terminal's edges and
`Live` redraws in place:

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/terminal_grid.png" alt="A bordered terminal layout with a menu, a progress bar, a sparkline and a log" width="560">
</p>

A whole dashboard with a sidebar, KPI cards, a coloured table with merges,
bars, sparklines and a log: [examples/dashboard.py](https://github.com/Opus-Perpetuus/flexablelib/blob/main/examples/dashboard.py)
(`python examples/dashboard.py --live 10`). More in
[docs/LAYOUT.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/LAYOUT.md).

## Notes

- A column named `"i"` does not collide with the index column (`utils.IndexColumnTitle`).
- Exponential numbers align on the decimal / exponent axis with the rest of the float column.
- Shrinking a float column drops decimals instead of chopping characters, so decimal alignment survives a terminal fit ([#23](https://github.com/Opus-Perpetuus/flexablelib/issues/23)).

Open work and the issue map: [docs/ISSUES.md](https://github.com/Opus-Perpetuus/flexablelib/blob/main/docs/ISSUES.md).

## Project layout

- `flexablelib/` — the core package (no runtime dependencies): `table.py` (the Table class), `layout.py` (Card, Grid, GridCell), `_frames.py` (frame primitives, C or Python), `columns.py`, `cells.py`, `table_strings.py`, `style_compositions.py` (the 54 styles, as data), `text_width.py` / `fast.py` (terminal-width measurement, C or Python), readers and writers.
- `packages/tui/` — `flexablelib-tui`: widgets, Screen, Live, App, keyboard and mouse input, accessibility.
- `packages/components/` — `flexablelib-components`: the terminal components.
- `packages/speedups/` — `flexablelib-speedups`: the C frame code.
- `examples/` — `dashboard.py`, `admin.py`, `keys.py` (live key detector).
- `tests/` — the pytest suite; `tools/` — benchmarks and generators; `docs/` — guides and images.
- `ARCHITECTURE.md` — how it all fits together; `style_examples.md` — all 54 styles; `package.json` — the canonical version number.

<p align="center">
  <img src="https://raw.githubusercontent.com/Opus-Perpetuus/flexablelib/main/docs/img/readme/tests.png" alt="Running the test suite" width="560">
</p>

See [**ARCHITECTURE.md**](https://github.com/Opus-Perpetuus/flexablelib/blob/main/ARCHITECTURE.md) for the rendering pipeline, how
styles are defined, and how to add one.
