# prettyTables — brand assets

## The mark

The icon is a table reduced to its structure — top border, solid header row, the double rule
that `grid_eheader` draws with `=`, three rows of data, bottom border — with one addition: a
vertical amber axis running through the body, and the data bars snapped to it.

That axis is the decimal point. It is the one thing this logo says that a generic spreadsheet
icon does not: `prettyTables` aligns float columns on their decimal separator, so `9.651`,
`245.7`, and `12.4325` line up. The bars extend different distances on each side of the axis
for exactly that reason.

The axis is deliberately the highest-contrast element in the mark. It carries the concept, so
it has to survive being the only thing you can still make out at 16px.

## Files

| File | Use |
| --- | --- |
| `export/logo.svg` | Combination mark (icon + wordmark), 1024×512. README headers, docs. |
| `export/logo-{512,1024,2048}.png` | Raster combination mark, by width. |
| `export/icon.svg` | Icon alone, square. Favicons, avatars, app icons. |
| `export/icon-{16,32,48,64,180,192,512,1024}.png` | Raster icon, by edge length. |
| `export/favicon.ico` | Multi-resolution ICO (48/32/16). |

`logo.svg` keeps the icon in a `<g id="icon">` and the text in a `<g id="wordmark">`, so the
icon can be lifted out without redrawing it. `icon.svg` is that group cropped to
`viewBox="60 76 360 360"`.

## Palette

| Role | Hex |
| --- | --- |
| Frame, header row, rules | `#4338CA` |
| Data bars, left of axis | `#818CF8` |
| Data bars, right of axis | `#6366F1` |
| **Decimal axis (accent)** | `#F59E0B` |
| Wordmark — "pretty" | `#5A6472` |
| Wordmark — "Tables" | `#4338CA` |

Backgrounds are transparent. The palette was chosen to hold up on both light and dark
backgrounds without a second variant — the mid-tone slate of the wordmark and the amber accent
both clear contrast on white and on GitHub's `#0d1117`.

## Typography

The wordmark is set in a monospace stack — `Menlo, Consolas, 'DejaVu Sans Mono', monospace` —
at weight 700 with `letter-spacing: -3`. Monospace is the point: this is a library whose output
only lines up in a monospaced terminal.

Because the wordmark uses live text rather than outlined paths, it renders with whichever
monospace font the viewer has. Metrics shift slightly between systems. Use the exported PNGs
where exact reproduction matters.

## Working files

`concepts/` holds the four initial directions, `iterations/` the refinements. `iteration-7.svg`
is the final and is what `export/logo.svg` was copied from. Open `preview.html` in a browser to
see everything side by side, with a light/dark toggle and a favicon size check.

## Regenerating the exports

Requires `librsvg` (`rsvg-convert`) and ImageMagick.

```bash
cd logos/export
for w in 512 1024 2048; do rsvg-convert -w $w logo.svg -o logo-${w}.png; done
for s in 16 32 48 64 180 192 512 1024; do rsvg-convert -w $s -h $s icon.svg -o icon-${s}.png; done
magick icon-48.png -define icon:auto-resize=48,32,16 favicon.ico
```
