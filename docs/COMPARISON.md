# Table-library comparison survey

Background for the "How it compares" table in the README. Feature notes come from each project's primary README or docs at survey time (October 2026); a library missing a feature here means it was not found in its docs, not that it cannot do it. Corrections are welcome via an issue or PR.

Research for **flexablelib** feature mining (post-2.0.12). The "Already?" and "Candidate?" columns describe 2.0.12; most candidates shipped in 2.0.13 – 2.0.16 (see CHANGELOG.md).
Compiled 2026-10-28 (America/Mexico_City). **89 entries** across languages/registries.

Sources: primary GitHub READMEs (gh api / raw), docs.rs, crates.io, npm, PyPI, RubyGems, Hex, Packagist; secondary comparison pages only as pointers.

Columns: **Already?** = covered by flexablelib 2.0.12 in spirit; **Candidate?** = worth integrating as a terminal-native non-breaking feature.

| # | Lang | Library | URL | Distinctive features (3–8) | Already? | Candidate? |
|---|------|---------|-----|----------------------------|----------|------------|
| 1 | Python | `rich` | https://github.com/Textualize/rich | unicode box tables; row_styles/zebra; caption; footer; nested renderables; overflow wrap/ellipsis; column justify; header_style | styles,title,colors,max_width,wrap partial | yes |
| 2 | Python | `tabulate` | https://github.com/astanin/python-tabulate | many tablefmt presets; decimal align; headers firstrow/keys; showindex; HTML/LaTeX/MD/RST/org/jira exports; floatfmt; disable_numparse | many styles, decimal align, MD/HTML, index | partial |
| 3 | Python | `prettytable` | https://github.com/jazzband/prettytable | align per column; sortby; paginate; HTML/CSV/JSON/LaTeX; border/hrules/vrules toggles; padding_width; from_csv/db/html; max_width/min_width | align,sort,IO,borders via styles | yes |
| 4 | Python | `texttable` | https://github.com/foutaise/texttable | max_width wrap; cols_align/valign; set_deco flags; datatype cols; header_align; CJK wrap via cjkwrap | max_width, align, wrap | yes |
| 5 | Python | `terminaltables` | https://github.com/Robpol86/terminaltables | Ascii/Unicode/Porcelain tables; nested list API; multiline cells | styles, multiline | no |
| 6 | Python | `terminaltables3` | https://github.com/matthewdeanmartin/terminaltables3 | maintained fork of terminaltables; Python 3.8+ | styles | no |
| 7 | Python | `beautifultable` | https://github.com/pri22296/beautifultable | ANSI colors; custom styles; row/col build; streaming append; Unicode; wcwidth | colors, styles, unicode width | partial |
| 8 | Python | `wcwidth` | https://github.com/jquast/wcwidth | East Asian Width; emoji/ZWJ sequences; versioned Unicode tables | text_width/C speedups | no |
| 9 | Python | `pandas Styler` | https://pandas.pydata.org/docs/user_guide/style.html | conditional CSS; gradient/bar charts; to_html/latex/excel; highlight_max/null; format | to_html/excel, color_rule partial | partial |
| 10 | Python | `great_tables` | https://github.com/posit-dev/great-tables | publication tables; spanners; footnotes; nanoplots; HTML/LaTeX; fmt_* helpers | title/HTML | no |
| 11 | Python | `plotext` | https://github.com/piccolomo/plotext | terminal plots; simple show_table; braille/marker charts | none for plots | no |
| 12 | Python | `termtables` | https://github.com/nschloe/termtables | minimal pretty tables; padding; alignment | core | no |
| 13 | Python | `tableprint` | https://github.com/nirum/tableprint | banner/hrules; numpy friendly; style dict | styles | no |
| 14 | Python | `pytablewriter` | https://github.com/thombashi/pytablewriter | many writers AsciiDoc/CSV/HTML/MD/Excel/RST/LaTeX; style themes; type hints | CSV/MD/HTML/Excel | yes |
| 15 | Python | `pytablereader` | https://github.com/thombashi/pytablereader | read CSV/MD/HTML/Excel/Google Sheets; load into table writer | from_csv/html/excel/pandas | yes |
| 16 | Python | `tablib` | https://github.com/jazzband/tablib | format-agnostic Dataset; import/export many formats; headers | IO partial | partial |
| 17 | Python | `columnize` | https://github.com/rocky/pycolumnize | list into balanced columns; ls-like | none | no |
| 18 | Python | `blessed` | https://github.com/jquast/blessed | terminal capabilities; colors/attrs; location | colors/dim/reverse | no |
| 19 | Python | `textual` | https://github.com/Textualize/textual | DataTable widget; reactive TUI; sort/filter UI | none interactive | no |
| 20 | Python | `csvkit` | https://github.com/wireservice/csvkit | csvlook ASCII tables; CLI CSV toolkit | to_csv | partial |
| 21 | Python | `petl` | https://github.com/petl-developers/petl | ETL tables; look() pretty print; transforms | from_records | no |
| 22 | Python | `flexablelib (self)` | https://github.com/Opus-Perpetuus/flexablelib | 56 styles; merges; border_text; border_color; blocks; decimal align; colors; IO | baseline 2.0.12 | — |
| 23 | Rust | `tabled` | https://github.com/zhiburt/tabled | derive macros; Style presets; LineText borders; span; panel; color; width/height control; rotate | styles,border_text,border_color,merges | yes |
| 24 | Rust | `comfy-table` | https://github.com/Nukesor/comfy-table | dynamic width arrange; constraints; presets+modifiers; padding; ANSI attrs; content wrapping | max_width,padding partial,colors | yes |
| 25 | Rust | `cli-table` | https://github.com/cli-table/cli-table | derive; CSV feature; simple Style | styles,CSV | no |
| 26 | Rust | `prettytable-rs` | https://github.com/phsym/prettytable-rs | classic PrettyTable port; format; CSV | core | no |
| 27 | Rust | `tabular` | https://docs.rs/tabular | plain aligned text tables; row format strings | align | no |
| 28 | Rust | `cols` | https://rustutils.gitlab.io/cols/ | adaptive widths; tree render; stream; JSON/CSV/MD export; filters | CSV/MD | partial |
| 29 | Rust | `termimad` | https://github.com/Canop/termimad | MD in terminal; tables inside MD | to_markdown | partial |
| 30 | Go | `tablewriter` | https://github.com/olekukonko/tablewriter | ASCII/Unicode; color; merge cells; caption; footer; bulk append; HTML/MD/CSV; wrap | merges,colors,title,MD/CSV | yes |
| 31 | Go | `go-pretty` | https://github.com/jedib0t/go-pretty | Style many; row/column config; sort; filter; CSV/HTML/MD; paging; suppress empty | styles,sort,filter,IO | yes |
| 32 | Go | `lipgloss` | https://github.com/charmbracelet/lipgloss | layout/style DSL; borders; padding; AdaptiveColor | colors,padding | partial |
| 33 | Go | `bubbles Table` | https://github.com/charmbracelet/bubbles | interactive TUI table; keymap | none | no |
| 34 | Go | `bubble-table` | https://github.com/evertras/bubble-table | interactive columns; filter/sort UI; footer | footer candidate | no |
| 35 | Go | `termenv` | https://github.com/muesli/termenv | color profile detect; styles | supports_color | no |
| 36 | JS | `cli-table3` | https://github.com/cli-table/cli-table3 | unicode; colSpan/rowSpan; colors; wordWrap; style padding; head | merges,colors,wrap | yes |
| 37 | JS | `cli-table (Automattic)` | https://github.com/Automattic/cli-table | original unicode CLI tables; chars customize | styles | no |
| 38 | TS | `gajus/table` | https://github.com/gajus/table | config-driven; border templates; columnUserConfig; spanning | styles,merges | partial |
| 39 | JS | `console-table-printer` | https://github.com/console-table-printer | colored rows; sort; filter; maxLen | colors,sort | partial |
| 40 | JS | `ascii-table3` | https://www.npmjs.com/package/ascii-table3 | ASCII renderer; align; title | title,align | no |
| 41 | JS | `as-table` | https://www.npmjs.com/package/as-table | objects→table; ANSI-aware; emoji width | unicode width | no |
| 42 | JS | `@visulima/tabular` | https://www.npmjs.com/package/@visulima/tabular | borders/padding/align; Unicode; grids | core | partial |
| 43 | JS | `cmd-table` | https://www.npmjs.com/package/cmd-table | interactive TUI; streaming; CSV/JSON/HTML; pivot | IO | no |
| 44 | JS | `ink-table / ink` | https://github.com/vadimdemedes/ink | React CLI; table components community | none | no |
| 45 | Ruby | `terminal-table` | https://github.com/tj/terminal-table | style; alignment; separator rows; title; headings | title,dividers,align | yes |
| 46 | Ruby | `tty-table` | https://github.com/piotrmurach/tty-table | orientations; padding; multiline; resize; styles; filter/transform | padding candidate,wrap | yes |
| 47 | Ruby | `tabulo` | https://github.com/matt-harvey/tabulo | column-based API; truncation; wrapping; border | wrap/truncate | yes |
| 48 | Ruby | `table_tennis` | https://github.com/gurgeous/table_tennis | stylish terminal tables | styles | no |
| 49 | C# | `Spectre.Console Table` | https://github.com/spectreconsole/spectre.console | Rich-like markup; borders; columns expand; footers; alignment; nested panels | colors,styles,title | yes |
| 50 | C# | `ConsoleTables` | https://github.com/khalidabuhakmeh/ConsoleTables | simple ASCII; Write/WriteMarkDown; NumberAlignment | MD | no |
| 51 | C# | `CsConsoleFormat` | https://github.com/Athari/CsConsoleFormat | XAML-like console documents; grids/tables | none | no |
| 52 | Java | `tablesaw` | https://github.com/jtablesaw/tablesaw | dataframe; print() ascii; types; filters | from_records | no |
| 53 | Kotlin | `Picnic` | https://github.com/JakeWharton/picnic | DSL tables; span; border style; padding; ASCII/Unicode | merges,styles | yes |
| 54 | Java | `iarkn/clitable` | https://github.com/iarkn/clitable | simple console tables | core | no |
| 55 | Elixir | `TableRex` | https://github.com/djm/table_rex | title/headers; align; ANSI colors; padding; MD framing; multiline; sort | title,colors,align,MD | yes |
| 56 | Elixir | `scribe` | https://github.com/nucleardraw/scribe | pretty-print structs/maps as tables | from_dicts | no |
| 57 | Elixir | `zweifisch/table` | https://github.com/zweifisch/table | ascii CLI tables | core | no |
| 58 | Elixir | `tablet` | https://hex.pm/packages/tablet | tiny tabular renderer | core | no |
| 59 | Erlang | `stdout_formatter` | https://hex.pm/packages/stdout_formatter | paragraphs/lists/tables plain text | core | no |
| 60 | PHP | `phplucidframe/console-table` | https://github.com/phplucidframe/console-table | setPadding; bordered; headers/rows | padding candidate | yes |
| 61 | PHP | `pear/Console_Table` | https://github.com/pear/Console_Table | classic PEAR console tables; align; border | core | no |
| 62 | PHP | `dekor/php-array-table` | https://github.com/dekor/php-array-table | assoc arrays as mysql-like tables | core | no |
| 63 | PHP | `marcin-orlowski/text-table` | https://github.com/MarcinOrlowski/TextTable | fast flexible text tables | core | partial |
| 64 | PHP | `mmarica/display-table` | https://packagist.org/packages/mmarica/display-table | text format display tables | core | no |
| 65 | PHP | `lucinda/console` | https://packagist.org/packages/lucinda/console | draw tables UNIX/Windows | core | no |
| 66 | Nim | `nim-asciitables / nim-terminaltables` | https://github.com/xmonader/nim-asciitables | setHeaders/addRow; tableWidth; separateRows; custom edges | styles | no |
| 67 | Crystal | `tallboy` | https://github.com/epoch/tallboy | DSL; span; unicode/ascii/md; multiline header; column width/align | merges,align,MD | yes |
| 68 | Crystal | `terminal_table.cr` | https://github.com/benoist/terminal_table.cr | ASCII table generator | core | no |
| 69 | Zig | `prettytable-zig` | https://github.com/dying-will-bullet/prettytable-zig | PrettyTable-like ASCII | core | no |
| 70 | Zig | `firstrow/zig-ascii-table` | https://github.com/firstrow/zig-ascii-table | generate ascii tables | core | no |
| 71 | Zig | `zig-toolbelt/cli-table` | https://github.com/zig-toolbelt/cli-table | cli table helpers | core | no |
| 72 | F# | `FsPrettyTable` | https://github.com/tormaroe/FsPrettyTable | PrettyTable-like ASCII | core | no |
| 73 | Clojure | `cldwalker/table` | https://github.com/cldwalker/table | ascii tables from data structures | from_records | no |
| 74 | OCaml | `printbox` | https://github.com/c-cube/printbox | nested boxes/lists/arrays/tables; multiple backends | nested candidate | partial |
| 75 | Haskell | `boxes` | https://hackage.haskell.org/package/boxes | 2D box combinators for pretty layout | none | no |
| 76 | Scala | `scala-ascii (community)` | https://github.com/mdr/ascii-graphs | parse ascii diagrams; not data tables | none | no |
| 77 | Swift | `SwiftyTextTable` | https://github.com/scottrhoyt/SwiftyTextTable | simple terminal tables; alignment | core | no |
| 78 | Dart | `text_table` | https://github.com/desktop-dart/text_table | stylable flex ascii tables | core | partial |
| 79 | Dart | `tabular_dart` | https://github.com/rtmigo/tabular_dart | ASCII tabular display | core | no |
| 80 | Dart | `ascii_tables` | https://github.com/lord-otori/ascii_tables | tables from collections | core | no |
| 81 | R | `rlistings` | https://github.com/pharmaverse/rlistings | ASCII listings/tables for pharma; formatting | none | no |
| 82 | R | `formattable / knitr kable` | https://cran.r-project.org | kable HTML/MD/LaTeX; formattable colors | to_html/md | no |
| 83 | Julia | `PrettyTables.jl` | https://github.com/ronisbr/PrettyTables.jl | highly configurable; HTML/LaTeX/MD/text; highlighters; formatters; cropping | colors,IO,format | yes |
| 84 | Perl | `Text::Table` | https://metacpan.org/pod/Text::Table | flexible load; column specs | core | no |
| 85 | Perl | `Text::ASCIITable` | https://metacpan.org/pod/Text::ASCIITable | ASCII tables; align; options | core | no |
| 86 | C++ | `FTXUI table` | https://github.com/ArthurSonzogni/FTXUI | TUI table element; flexible layout | none | no |
| 87 | Go | `miller` | https://github.com/johnkerl/miller | name-indexed tabular data; pretty print; many formats | CSV | no |
| 88 | Rust | `xsv` | https://github.com/BurntSushi/xsv | CSV toolkit; table view | CSV | no |
| 89 | Rust | `csview` | https://github.com/wfxr/csview | CSV viewer CJK/emoji | unicode | no |

## Language coverage summary
Python: 22, Rust: 9, JS: 8, Go: 7, PHP: 6, Elixir: 4, Ruby: 4, C#: 3, Dart: 3, Zig: 3, Crystal: 2, Java: 2, Perl: 2, R: 2, C++: 1, Clojure: 1, Erlang: 1, F#: 1, Haskell: 1, Julia: 1, Kotlin: 1, Nim: 1, OCaml: 1, Scala: 1, Swift: 1, TS: 1

## Notes
- Excluded pure ASCII-art / image-to-ascii / asciinema / asciidoctor toolchains unless they ship a data-table renderer.
- TUI-interactive tables (bubbles, textual DataTable, ink) listed for completeness; not integration targets for a string-compose library.
- Nearby CLIs (miller, xsv, csview, csvkit) listed for export/pretty-print adjacency.