#!/usr/bin/env python3
"""
Miniatura 1280x720 del video: un cuadro real de la captura de fondo,
oscurecido, con el título y un botón de reproducir.

    python examples/video/thumbnail.py cuadro.png thumb.png
"""

import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def font(size, weight='bold'):
    path = subprocess.run(['fc-match', '-f', '%{file}', 'Fira Sans:' + weight],
                          capture_output=True, text=True).stdout
    return ImageFont.truetype(path, size)


def main(frame, out):
    W, H = 1280, 720
    bg = Image.open(frame).convert('RGB').resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(1.2))
    shade = Image.new('RGB', (W, H), (16, 17, 28))
    img = Image.blend(bg, shade, 0.58)
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for y in range(H):                      # darker band behind the title
        a = int(200 * max(0.0, 1 - abs(y - 210) / 250))
        d.line([(0, y), (W, y)], fill=(16, 17, 28, a))
    img = Image.alpha_composite(img.convert('RGBA'), over)
    d = ImageDraw.Draw(img)
    for x in range(W):                      # accent bar
        t = x / W
        d.line([(x, H - 12), (x, H)], fill=(int(122 + 65 * t), int(162 - 8 * t), 247))
    d.text((70, 60), 'flexablelib 3.5.1', font=font(44, 'semibold'), fill=(122, 162, 247))
    title = 'flexablelib — demo completa'
    size = 96
    while d.textlength(title, font=font(size)) > W - 140:
        size -= 4
    d.text((66, 120), title, font=font(size), fill=(236, 240, 255))
    d.text((70, 120 + size + 18),
           'tablas · layouts · widgets · apps TUI · accesibilidad · imágenes · C',
           font=font(36, 'medium'), fill=(224, 175, 104))
    cx, cy, r = W // 2, 500, 92                # play button
    d.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=(0, 0, 0, 90))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(247, 118, 142, 245))
    d.polygon([(cx - 30, cy - 46), (cx - 30, cy + 46), (cx + 50, cy)], fill=(255, 255, 255))
    d.text((W - 300, H - 70), 'salida real de terminal', font=font(28, 'medium'),
           fill=(192, 202, 245))
    img.convert('RGB').save(out, optimize=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
