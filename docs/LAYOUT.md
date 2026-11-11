# Cards, grids, responsive tables and terminal interfaces

Cards, grids and responsive tables were added in 3.1.0; grid tracks, shared
borders, sized grids, widgets, `Screen` and `Live` in 3.2.0. Everything here measures visible terminal columns: ANSI
escapes count zero, emoji and CJK count two.

Every renderable has `render(width=None)`. `width=None` means the terminal
width (`COLUMNS`, then the console size, then 80).

## Card

```python
from flexablelib import Card

Card(
    title='Ana', subtitle='Norte',
    fields={'Edad': 28, 'Ciudad': 'Guadalajara'},   # or [(label, value), ...]
    footer='actualizado hoy',
    body=None,            # any renderable: Table, Grid, Card, or text
    actions=['Ver'],      # drawn as [ Ver ] on the last line, right-aligned
    style_name='rounded', # any of the 54 table styles (old names work too)
    theme=None,           # a table theme: dark, ocean, neon, forest...
)
```

| Option | Meaning |
| --- | --- |
| `title_position` | `'auto'` (default): in the top border when the style draws one, else the first line. `'border'` or `'inside'` to force. |
| `title_align`, `align`, `label_align` | `'l'`, `'c'`, `'r'` for the title, the values and the labels. |
| `field_columns` | `1` (label, value per line), `2`+ (a grid of tiles, label above value) or `'auto'` (as many tiles as fit). |
| `field_layout` | `'auto'`, `'inline'` or `'stacked'`. |
| `field_rules` | Rule between field rows. `None` follows the style (`*_rows` styles draw them). |
| `width`, `min_width`, `max_width` | Fixed width, or bounds for the natural width. `render(width)` wins. |
| `height` | Stretch the card (blank lines before the footer). Grids use it to line cards up. |
| `padding` | Spaces between frame and content (default: the style margin). |
| `title_color`, `subtitle_color`, `label_color`, `value_color`, `footer_color` | Colour specs. Defaults: bold title, dim subtitle, labels and footer. |
| `value_colors` | `{label: spec}`. |
| `border_color` | The frame colour. |
| `color` | Background for the whole interior, frame to frame, e.g. `'white on #1e293b'`. |
| `zebra` | Alternate field rows: a spec for odd rows or `(even, odd)`. |
| `panel`, `shadow`, `panel_color`, `shadow_color` | The same outer panel and shadow as `Table`. |
| `use_colors` | `None` (terminal only, honours `NO_COLOR` / `FORCE_COLOR`), `True`, `False`. |

`card.apply_theme(name)` takes the theme's style, border colour, header colour
(as the title colour) and zebra.

## Table titles

| Attribute | Meaning |
| --- | --- |
| `title` | Drawn above the table. |
| `subtitle` | A second line under the title (dim when colour is on). |
| `title_position` | `'above'` (default) or `'border'`: `╭─ Title ───╮`. |
| `caption_position` | `'below'` (default) or `'border'` (bottom rule). |
| `title_align` | `'l'`, `'c'` (default) or `'r'`, for title, subtitle and caption. |
| `title_color` | Colour spec for the title. |

A border title only replaces plain rule glyphs. It never covers a corner or a
column junction (`┬`), so every column still meets the frame. When there is no
long enough stretch of rule, or the style draws no top rule, the title is
drawn above instead. With `'l'` the title takes the first stretch from the
left that is long enough, with `'r'` the first from the right, with `'c'` the
one nearest the middle.

## Responsive tables

`table.render(width=None)` picks the first of these that fits `width`
(default: `max_width`, else the terminal):

1. `'table'`: the table as it is.
2. `'hidden'`: columns with a priority above 1 hidden, highest number first
   (`column_priority = {'Correo': 3, 'Grupo': 2}`), until it fits.
3. `'compact'` (or `'hidden'` when columns had to go too): columns squeezed
   and wrapped, none narrower than `breakpoints['min_column']` (default 8, or
   the column's natural width), hiding as few columns as possible.
4. `'cards'`: one card per row, in a grid of as many columns as fit.

`table.render_mode(width)` tells which one it would use. `breakpoints={'cards':
60}` (or `breakpoints=60`) forces cards below 60 columns. `responsive=True`
(also `Table(..., responsive=True)`) makes `str(table)` and `print(table)` call
`render()`.

`table.to_cards(title_field=None, subtitle_field=None, fields=None,
footer_field=None, **card_options)` builds the cards: the title from the first
column unless told otherwise, the other columns as fields, values formatted as
the table shows them (`sort_by`, `row_filter`, `hide_columns` apply). Cards
inherit the style, `border_color`, `header_color` (title), `zebra`,
`column_colors` (as value colours), `panel` and `shadow`.

`table.card_options` sets the same keys once, plus the grid's `min_width`,
`columns`, `gap` and `row_gap` for the cards view.

## Grid

```python
from flexablelib import Grid, GridCell

Grid(children, columns='auto', gap=2, row_gap=1, min_width=None,
     max_width=None, width=None, equal_height=True, align='l')
```

* `children`: cards, tables, text, grids, or `GridCell(child, span=n)` /
  `(child, n)` for an item spanning `n` columns.
* `columns='auto'` fits as many columns of `min_width` as the width allows
  (default `min_width`: the widest child). An int is the most columns to use;
  with `min_width` it still drops to fewer when they would be too narrow.
* Children are rendered at their cell's width: tables respond (and may turn
  into cards), cards fill the cell, text wraps.
* `equal_height` stretches the cards of one row to the same height.
* `grid.column_count(width)` tells how many columns it would use.

### Column widths (3.2.0)

`column_widths` gives one size per column and sets how many there are:

| Size | Meaning |
| --- | --- |
| `12` | Fixed: 12 columns. |
| `'auto'` | The natural width of the widest one-column child in that column. |
| `'2fr'`, `2.0`, `'2*'` | A share of what is left after the fixed, `%` and `auto` columns. |
| `'30%'` | A share of the grid's width (minus borders and gaps). |
| `(size, min, max)` | Any of the above, bounded: `('1fr', 20, None)`. |

`auto` and `%` columns shrink (down to their minimum) before fractions lose
their minimum. When even the minimums do not fit, the grid stacks every child
in one column. A dict picks a layout per width, like CSS breakpoints -- the
largest key the width reaches wins, and below the smallest key the grid
stacks:

```python
Grid(cells, column_widths={0: ['1fr'],
                           76: ['3fr', '2fr'],
                           110: [(16, 14, 18), '3fr', '2fr']})
```

`collapse_below=N` stacks below `N` columns whatever the layout.

### Cells

```python
GridCell(child, span=1, row_span=1, align='l', valign=None, title=None,
         title_align='l', color=None, stretch=None, padding=None,
         hide_below=None)
```

* `row_span` makes a cell cover several rows (a sidebar). Placement follows
  CSS "sparse" auto-placement: left to right, skipping slots a spanning cell
  above already holds.
* `valign` (`'top'`, `'middle'`, `'bottom'`) places a shorter child in its
  slot; `Grid(valign=...)` sets the default.
* `title` is set into the cell's top border (bordered grids only). It never
  covers a junction; too long, it is cut with `…`; with no room it is left
  out.
* `color` paints the cell's background, padding included.
* `stretch=True` renders the child at the slot's full height. Cards stretch in
  an `equal_height` row; in a grid with a `height` or `row_heights`, every
  child that takes a height (grids, `LogView`, widgets) fills its slot unless
  the cell sets `valign`.
* `hide_below=N` hides the cell when the grid is narrower than `N`.
* `grid.add(child, span, **cell_options)` takes the same options.

### Shared borders

`border='single'` (also `'rounded'`, `'double'`, `'heavy'`, `'ascii'`, `True`)
draws one frame around and between all the cells, with the right junction
(`┬ ┼ ┴ ├ ┤`) wherever cells meet, spans and row spans included. The border
replaces `gap` and `row_gap`. `padding` (default 1) is the space inside each
cell; `border_color` and `title_color` colour the frame and the titles;
`use_colors` works as on cards.

```python
from flexablelib import (Grid, GridCell, LogView, ProgressBar, Sparkline,
                         Text)

Grid([
    GridCell(Text('▸ Resumen\n  Ventas\n  Ajustes'), row_span=2, title='Menú'),
    GridCell(ProgressBar(72, label='CPU', thresholds={0.7: 'yellow'}),
             title='Recursos'),
    GridCell(Sparkline([3, 5, 2, 8, 6, 9, 4, 7], label='rps', show_last=True),
             title='Tráfico'),
    GridCell(LogView(['10:00 INFO arranque', '10:01 WARN lento']), span=2,
             title='Eventos'),
], column_widths=[14, '1fr', '1fr'], border='rounded').render(width=64)
```

```
╭─ Menú ───────┬─ Recursos ────────────┬─ Tráfico ─────────────╮
│ ▸ Resumen    │ CPU ████████▋░░░  72% │ rps ▂▄▁▇▅█▃▆ 7        │
│   Ventas     ├─ Eventos ─────────────┴───────────────────────┤
│   Ajustes    │ 10:00 INFO arranque                           │
│              │ 10:01 WARN lento                              │
╰──────────────┴───────────────────────────────────────────────╯
```

### Height

`grid.render(width, height)` (or `Grid(height=...)`) makes the grid exactly
`height` lines. `row_heights` sizes rows like `column_widths` sizes columns
(`int`, `'auto'`, `'Nfr'`, bounds, or a dict per width): fraction rows share
the spare lines by weight, each keeping at least its content; without
fraction rows the last row takes them. When the content is taller, fraction
rows give up lines first, then the others from the bottom up, so the frame
stays closed.

## Widgets (3.2.0)

All in `flexablelib` (and `flexablelib.widgets`). Each has `render(width=None,
height=None)`, `natural_width()` and `str()`, so they drop into grids, cards
and screens.

| Widget | What it draws | Main options |
| --- | --- | --- |
| `ProgressBar(value, total=100)` | `CPU ███████▋░░░ 64%`, partial cells in eighths | `label`, `label_width`, `value_format` (`'{value}/{total} GB'`, `{percent}`), `value_width`, `thresholds={0.7: 'yellow', 0.9: 'red'}`, `color`, `empty_color`, `fill_char`, `empty_char` |
| `Sparkline(values)` | `▁▂▄▆█▇▅▃`, newest values when longer than the width | `low`, `high`, `label`, `label_width`, `show_last`, `value_format`, `chars`, `color` |
| `BarChart(data)` | one labelled bar per value | `sort`, `max`, `show_values`, `value_format`, `color`, `colors={label: spec}` |
| `StatusBar(left, center, right)` | a full-width bar on a background | `color` (default `'black on cyan'`), `padding`. Narrow: the centre goes first, then the left side is cut with `…`. |
| `KeyHints({'q': 'Salir'})` | key chips, wrapping onto more lines | `key_color`, `label_color`, `separator`, `align` |
| `LogView(lines)` | the newest lines that fit, levels coloured (`ERROR`, `WARN`, `INFO`, `DEBUG`, `OK`) | `height`, `tail`, `wrap`, `level_colors`, `color_lines`, `max_lines`, `append(line)` |
| `Text(text)` | wrapped (or cut) text | `align`, `color`, `wrap` |
| `Rule(title)` | `──── Ventas ────` | `char`, `align`, `color`, `title_color` |

## Screen and Live (3.2.0)

```python
from flexablelib import Live, Screen, StatusBar, KeyHints

screen = Screen(body=grid, header=StatusBar('App', right='10:01'),
                footer=KeyHints({'q': 'Salir', 'F5': 'Refrescar'}))
print(screen.render())                 # exactly the terminal's size
screen.render(width=100, height=30)    # or a given one
```

`Screen` sticks the header to the top and the footer to the bottom and gives
the body every line in between (a grid hands them to its fraction rows, a
`LogView` shows that many lines). Taller content is cut so the footer never
scrolls away; on a tiny terminal header lines go first. `fit_height=False`
lets the body take its natural height; `margin` adds side columns.

`Live` redraws in place:

```python
with Live(screen) as live:
    for tick in range(60):
        update_data(tick)
        live.update()          # or live.update(new_renderable)
        time.sleep(1)

Live(screen).run(step, interval=1.0, iterations=None)   # step(i) -> False stops
```

On a terminal it switches to the alternate screen, hides the cursor and
repaints from the top-left; on exit it restores both and prints the last
frame (`transient=True` leaves nothing). On a pipe or file each frame is
written once, plainly. `screen=False`, `hide_cursor=False`, `force_terminal`
and `stream` adjust that.

`examples/dashboard.py` puts it all together: `python examples/dashboard.py
--theme neon --live 10`.

A whole screen:

```python
screen = Grid([
    GridCell('Ventas de noviembre', span=3),
    GridCell(sales_table, span=2),
    Grid([total_card, pending_card], columns=1, row_gap=0),
    GridCell(Card(title='Notas', body='Texto libre que se ajusta.'), span=3),
], columns=3)
print(screen.render())
```

## Panel and shadow

`flexablelib.layout.wrap_panel(text, panel=True, color=None)` and
`add_shadow(text, shadow=True, color=None)` are the helpers tables and cards
share, so `panel='double'` or `shadow='▒'` look the same on both.

## Limitations

* Merged cells are not carried into cards: each card shows the row's own
  values.
* Without `column_widths`, grid columns are equal width (a bordered grid
  hands out the leftover columns; an open one leaves them at the right, as
  before).
* Placement is automatic only: there is no explicit `row=`/`column=` for a
  cell, and an unfilled slot leaves a gap in a bordered grid's frame.
* `Live` redraws; it does not read the keyboard. Key handling (and so
  scrolling or focus) is up to the application.
* A border title cannot sit over a column junction: on a table whose columns
  are all narrower than the title it falls back to a line above, and with
  `'l'` / `'r'` it may sit over the first column wide enough rather than the
  outermost one.
