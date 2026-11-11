# Cards, grids and responsive tables

Added in 3.1.0. Everything here measures visible terminal columns: ANSI
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
long enough stretch of rule (with `'l'`, the first column; with `'r'`, the
last; with `'c'`, the one nearest the middle), or the style draws no top rule,
the title is drawn above instead.

## Responsive tables

`table.render(width=None)` picks the first of these that fits `width`
(default: `max_width`, else the terminal):

1. `'table'`: the table as it is.
2. `'compact'`: columns squeezed and wrapped, none narrower than
   `breakpoints['min_column']` (default 8, or the column's natural width).
3. `'hidden'`: columns with a priority above 1 hidden, highest number first
   (`column_priority = {'Correo': 3, 'Grupo': 2}`), then squeezed.
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
* Grid columns are equal width; spans cover several of them.
* A border title cannot sit over a column junction, so on tables with narrow
  columns it often falls back to a line above.
