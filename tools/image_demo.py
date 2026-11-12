"""Show one picture with the method the terminal supports (or the one
given): ``python tools/image_demo.py picture.png [method] [seconds]``.
Prints what was detected under the picture. Used for the screenshots in
docs/img/v35."""

import os
import sys
import time

from flexablelib import Card
from flexablelib_components import Image
from flexablelib_tui import graphics


def main(argv):
    path = argv[1] if len(argv) > 1 else 'picture.png'
    method = argv[2] if len(argv) > 2 and argv[2] != 'auto' else None
    seconds = float(argv[3]) if len(argv) > 3 else 0
    width = int(os.environ.get('DEMO_WIDTH', '44'))
    info = graphics.detect()
    img = Image(path, alt='Imagen de prueba', method=method, width=width - 4)
    card = Card(title='flexablelib · Image', body=img, width=width)
    text = str(card)
    sys.stdout.write(text + '\n')
    used = img.used_method
    sys.stdout.write('método: {0}{1}\n'.format(
        used, '' if method else ' (detectado)'))
    sys.stdout.write('terminal: {0}\n'.format(info.version or info.terminal))
    sys.stdout.write('kitty={0} iterm={1} sixel={2} celda={3}x{4}{5}\n'.format(
        info.kitty, info.iterm, info.sixel, info.cell[0], info.cell[1],
        '' if info.cell_known else '?'))
    sys.stdout.flush()
    if seconds:
        time.sleep(seconds)


if __name__ == '__main__':
    main(sys.argv)
