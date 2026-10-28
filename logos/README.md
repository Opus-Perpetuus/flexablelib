# flexablelib — brand assets

## The mark

The icon is a rounded terminal table: outer frame, solid header, double rule,
three data rows, and a vertical amber axis through the body. The axis is the
decimal point — float columns in flexablelib align on their separator, so
`9.651`, `245.7`, and `12.4325` line up. Teal corner ticks mark flexibility
(console + HTML, styles, merges, widths).

## Files

| File | Use |
| --- | --- |
| `export/logo.svg` | Combination mark (icon + wordmark), 1024×512. README headers, docs. |
| `export/logo-{512,1024,2048}.png` | Raster combination mark, by width. |
| `export/icon.svg` | Icon alone, square. Favicons, avatars, app icons. |
| `export/icon-{16,32,48,64,180,192,512,1024}.png` | Raster icon, by edge length. |
| `export/favicon.ico` | Multi-resolution ICO (48/32/16). |

`logo.svg` keeps the icon in a `<g id="icon">` and the text in a `<g id="wordmark">`.
`icon.svg` is that mark cropped to `viewBox="64 76 360 360"`.

## Palette

| Role | Hex |
| --- | --- |
| Frame, bottom rule | `#312E81` |
| Header / wordmark “lib” | `#4338CA` |
| Data bars (left of axis) | `#818CF8` |
| Data bars (right of axis) | `#6366F1` / `#A5B4FC` |
| **Decimal axis (accent)** | `#F59E0B` |
| Flex corner ticks | `#14B8A6` |
| Wordmark — “flexable” | `#475569` |
| Tagline | `#64748B` |

Backgrounds are transparent. The indigo / amber / teal set holds up on light
and dark surfaces (including GitHub’s `#0d1117`).

## Typography

Wordmark: monospace stack `Menlo, Consolas, 'DejaVu Sans Mono', monospace`,
weight 700, slight negative tracking. Tagline under the name at 22px.

Use exported PNGs where pixel-exact reproduction matters (live SVG text
metrics vary by system font).

## Working files

`concepts/concept-flexablelib.svg` and `iterations/iteration-flexablelib.svg`
mirror the current export. Open `preview.html` for light/dark checks.

## Regenerating the exports

Requires `librsvg` (`rsvg-convert`) and Pillow (or ImageMagick) for the ICO.

```bash
cd logos/export
for w in 512 1024 2048; do rsvg-convert -w $w logo.svg -o logo-${w}.png; done
for s in 16 32 48 64 180 192 512 1024; do rsvg-convert -w $s -h $s icon.svg -o icon-${s}.png; done
python3 - <<'PY'
from PIL import Image
imgs = [Image.open(f"icon-{s}.png").convert("RGBA") for s in (48, 32, 16)]
imgs[0].save("favicon.ico", format="ICO", sizes=[(48,48),(32,32),(16,16)], append_images=imgs[1:])
PY
```
