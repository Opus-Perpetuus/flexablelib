"""
Pictures: :class:`Image` shows an image file, URL, bytes or bitmap with the
best method the terminal has (kitty graphics, iTerm2 inline images, sixel,
Unicode blocks, braille, ASCII art) and falls back to a link that opens it
in a browser -- or, with no browser or display, to a warning with the
reason. :class:`ImageViewer` pages through several images.
"""

import math
import os
import time

from flexablelib import _frames as _fx
from flexablelib import _images as _img
from flexablelib_tui import accessibility as _a11y
from flexablelib_tui import graphics as _g

from .base import _Themed

__all__ = ['Image', 'ImageViewer', 'IMAGE_EXTENSIONS']

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp',
                    '.ppm', '.pgm', '.pbm', '.pnm', '.tif', '.tiff', '.ico',
                    '.svg', '.pdf')
FITS = ('contain', 'cover', 'fill', 'none')
_IDS = {}


def _image_id(key):
    """A stable 24-bit kitty image id for ``key`` (never 0)."""
    ident = _IDS.get(key)
    if ident is None:
        import zlib
        ident = (zlib.crc32(repr(key).encode()) & 0xFFFFFF) or 1
        _IDS[key] = ident
    return ident


class Image(_Themed):
    """
    An image in the terminal.

    ``source``: a path, ``file://`` or ``http(s)://`` URL, bytes, a file
    object, a :class:`flexablelib._images.Bitmap` or a Pillow image.
    ``alt`` is the text alternative read by screen readers and shown in
    linear mode -- always give one (the accessibility audit reports images
    without it). ``width`` / ``height`` cap the size in cells (default: the
    space the layout offers and the image's own proportions); ``fit`` is
    ``'contain'`` (whole image, proportions kept), ``'cover'`` (fills the
    area, cropped), ``'fill'`` (stretched) or ``'none'`` (pixels 1:1,
    cropped). ``method`` forces one of ``'kitty'``, ``'iterm'``,
    ``'sixel'``, ``'half'``, ``'quadrant'``, ``'sextant'``, ``'braille'``,
    ``'ascii'``, ``'link'``, ``'none'`` (default: ``FLEXABLELIB_IMAGE``, then
    what :func:`flexablelib_tui.graphics.detect` finds); ``blocks`` picks the
    Unicode mode used when no pixel protocol is available (``'half'``).
    ``caption=True`` adds the alt text (or file name) below as a link.
    Enter, ``o`` or a click open the image in the browser when there is
    one; ``on_open(image)`` replaces that.
    """

    role = 'img'
    needs_graphics = True

    def __init__(self, source, alt=None, width=None, height=None,
                 fit='contain', method=None, blocks=None, align='center',
                 background=None, upscale=True, animate=False, caption=False,
                 cell_size=None, focusable=False, on_open=None, **kwargs):
        super(Image, self).__init__(**kwargs)
        if fit not in FITS:
            raise ValueError('fit must be one of {0}'.format(FITS))
        self.source = source
        self.alt = alt
        self.width = width
        self.height = height
        self.fit = fit
        self.method = method
        self.blocks = blocks
        self.align = align
        self.background = background
        self.upscale = upscale
        self.animate = animate
        self.caption = caption
        self.cell_size = cell_size
        self.focusable = focusable
        self.on_open = on_open
        self.error = None
        self.used_method = None
        self._frames = None
        self._started = None
        self._cache = {}

    # -- source ---------------------------------------------------------------

    @property
    def name(self):
        src = self.source
        if isinstance(src, (str, os.PathLike)):
            text = os.fspath(src)
            return text.rstrip('/').rsplit('/', 1)[-1] or text
        return getattr(src, 'name', None) or 'imagen'

    @property
    def url(self):
        """What a browser opens: the URL, or ``file://`` for a path."""
        if isinstance(self.source, (str, os.PathLike)):
            return _g.file_url(self.source)
        return None

    def reload(self):
        self._frames = None
        self._cache = {}
        self.error = None

    def _load(self):
        if self._frames is None:
            try:
                if self.animate and not _a11y.settings.reduced_motion:
                    frames = _img.load_frames(self.source)
                else:
                    frames = [_img.load(self.source)]
                self._frames = frames
                self.error = None
            except _img.ImageError as error:
                self._frames = []
                self.error = str(error)
            except (OSError, ValueError) as error:
                self._frames = []
                self.error = str(error)
            self._started = time.monotonic()
        return self._frames

    def bitmap(self):
        """The current frame (the first one unless animating), or None."""
        frames = self._load()
        if not frames:
            return None
        if len(frames) == 1 or _a11y.settings.reduced_motion:
            return frames[0]
        total = sum(max(20, f.delay or 100) for f in frames)
        t = int((time.monotonic() - self._started) * 1000) % total
        for frame in frames:
            t -= max(20, frame.delay or 100)
            if t < 0:
                return frame
        return frames[-1]

    # -- accessibility -------------------------------------------------------

    def a11y_name(self):
        return str(self.a11y_label or self.alt or '')

    def a11y_value(self):
        bm = self.bitmap()
        if bm is None:
            return 'no se puede mostrar: {0}'.format(self.error or '')
        return '{0}×{1} px'.format(bm.width, bm.height)

    # -- geometry ------------------------------------------------------------

    def _info(self):
        return _g.detect()

    def _cell(self, info):
        return tuple(self.cell_size) if self.cell_size else info.cell

    def natural_width(self):
        if self.width:
            return self.width
        bm = self.bitmap()
        if bm is None:
            return min(60, _fx.visible_width(self.name) + 40)
        cw = self._cell(self._info())[0]
        from flexablelib.layout import render_width
        return max(4, min(render_width(None), math.ceil(bm.width / cw)))

    def _box(self, bm, width, height, cell):
        """(cols, rows, crop) for the picture inside width x height cells."""
        cw, ch = cell
        iw, ih = bm.width, bm.height
        max_w = width * cw
        max_h = height * ch if height else None
        crop = None
        if self.fit == 'fill' and max_h:
            return width, height, None
        if self.fit == 'none':
            cols = min(width, math.ceil(iw / cw))
            rows = math.ceil(ih / ch)
            if height:
                rows = min(rows, height)
            crop = (0, 0, min(iw, cols * cw), min(ih, rows * ch))
            return cols, rows, crop
        if self.fit == 'cover' and max_h:
            s = max(max_w / iw, max_h / ih)
            vis_w, vis_h = max_w / s, max_h / s
            crop = (int((iw - vis_w) / 2), int((ih - vis_h) / 2),
                    max(1, int(vis_w)), max(1, int(vis_h)))
            return width, height, crop
        s = max_w / iw
        if max_h:
            s = min(s, max_h / ih)
        if not self.upscale:
            s = min(s, 1.0)
        cols = max(1, min(width, int(round(iw * s / cw))))
        rows = max(1, int(round(ih * s / ch)))
        if height:
            rows = min(rows, height)
        return cols, rows, crop

    # -- drawing -------------------------------------------------------------

    def _fallback(self, width, reason, info=None):
        """The link line, or the warning when nothing can open it."""
        url = self.url
        ok, how = _g.browser_available()
        name = self.name
        if url and ok:
            self.used_method = 'link'
            icon = '->' if _a11y.settings.ascii else '🖼'
            text = '{0} {1}'.format(icon, name)
            hint = ' (Enter: abrir en el navegador)' if self.focusable else \
                ' (abrir en el navegador)'
            line = _g.hyperlink(url, self.paint(text, self.theme.accent +
                                                ' underline'
                                                if self._active() else None))
            lines = [line + self.paint(hint, self.theme.muted)]
            if reason:
                lines.append(self.paint(reason, self.theme.muted))
            return lines + self._focus_line(width)
        self.used_method = 'warning'
        symbol = _a11y.status_symbol('warning')
        why = reason or 'no se puede mostrar'
        if url and not ok:
            why += '; no hay navegador ni pantalla para abrirla ({0})'.format(
                how)
        elif not url:
            why += '; sin archivo ni URL que abrir'
        text = '{0} {1}: {2}'.format(symbol, name, why)
        return [self.paint(line, self.theme.warning)
                for line in _wrap(text, width)]

    def _alt_lines(self, width):
        self.used_method = 'alt'
        text = 'Imagen: {0}'.format(self.alt or self.name)
        if self.alt and self.name not in ('imagen', self.alt):
            text += ' ({0})'.format(self.name)
        if self.bitmap() is None:
            text += ' -- no se puede mostrar: {0}'.format(self.error)
        return _wrap(text, width)

    def _color(self, info):
        if not self._active():
            return 'none'
        level = info.color or 'truecolor'
        return level if level in ('truecolor', '256', '16') else '16'

    def draw(self, width, height):
        info = self._info()
        width = min(width, self.width) if self.width else width
        if self.height:
            height = min(height, self.height) if height else self.height
        caption = []
        if self.caption:
            label = self.alt or self.name
            if self.url:
                label = _g.hyperlink(self.url, label)
            caption = [self.paint(label, self.theme.muted)]
            if height:
                height = max(1, height - 1)
        color = self._color(info)
        method, mode, reason = _g.choose(
            info, force=self.method, blocks=self.blocks,
            color=color if color != 'none' else 'none')
        if method == 'alt':
            return self._alt_lines(width)
        if method == 'none':
            self.used_method = 'none'
            return [self.paint('[{0}]'.format(self.alt or self.name),
                               self.theme.muted)][:1]
        if method == 'link':
            return self._fallback(width, '') + caption
        bm = self.bitmap()
        if bm is None:
            return self._fallback(width, self.error) + caption
        cell = self._cell(info)
        if method == 'text':
            cell_px = _img.CELL_PIXELS[mode]
        cols, rows, crop = self._box(bm, width, height, cell)
        if cols < 2 or rows < 1:
            return self._fallback(width, 'no cabe ({0}×{1})'.format(
                width, height)) + caption
        if crop:
            bm = bm.crop(*crop)
        if method == 'text':
            lines = self._text(bm, cols, rows, mode, color)
        else:
            lines = self._pixels(bm, cols, rows, cell, method, info, color)
        self.used_method = method if method != 'text' else mode
        pad = max(0, width - cols)
        left = pad // 2 if self.align == 'center' else \
            pad if self.align == 'right' else 0
        if left:
            lines = [' ' * left + line for line in lines]
        if caption:
            lines.append(_fx.fit_line(caption[0], width,
                                      'c' if self.align == 'center' else 'l'))
        return lines + self._focus_line(width)

    def _focus_line(self, width):
        if not (self.focusable and self.focused):
            return []
        text = '> Enter: abrir' if _a11y.settings.ascii else '▶ Enter: abrir'
        return [_fx.fit_line(self.paint(text, 'reverse') if self._active()
                             else '[' + text + ']', width,
                             'c' if self.align == 'center' else 'l')]

    def _text(self, bm, cols, rows, mode, color):
        key = ('text', id(bm), cols, rows, mode, color, self.background)
        hit = self._cache.get(key)
        if hit is not None:
            return list(hit)
        pw, ph = _img.CELL_PIXELS[mode]
        src = bm
        if self.background is not None:
            src = src.flatten(_rgb(self.background))
        scaled = _img.scale(src, cols * pw, rows * ph)
        lines = _img.cells(scaled.data, scaled.width, scaled.height, mode,
                           color, 128)
        self._cache = {key: lines}
        return list(lines)

    def _pixels(self, bm, cols, rows, cell, method, info, color):
        cw, ch = cell
        key = (method, id(bm), cols, rows, cell, color, self.background,
               info.kitty_placeholders, info.tmux)
        hit = self._cache.get(key)
        if hit is not None:
            mark_key, lines = hit
            if mark_key in _g._PAYLOADS:
                return list(lines)
        # Exact pixel size inside the cell box, proportions kept.
        if self.fit in ('fill', 'cover'):
            dw, dh = cols * cw, rows * ch
        else:
            s = min(cols * cw / bm.width, rows * ch / bm.height)
            dw = max(1, int(round(bm.width * s)))
            dh = max(1, int(round(bm.height * s)))
        src = bm
        if self.background is not None:
            src = src.flatten(_rgb(self.background))
        if color == 'none':
            src = src.grayscale()
        scaled = _img.scale(src, dw, dh)
        tmux = bool(info.tmux)
        if method == 'kitty':
            ident = _image_id((id(self), self.source if isinstance(
                self.source, str) else id(self.source)))
            png = _img.encode_png(scaled)
            if info.kitty_placeholders or tmux:
                payload = _g.kitty_sequence(png, ident, cols, rows,
                                            placeholder=True, tmux=tmux)
                mark_key = _g.register(payload, cols, rows, 'placeholder',
                                       ident, tmux)
                lines = _g.kitty_placeholder_rows(ident, cols, rows)
                lines[0] = _g.mark(mark_key) + lines[0]
                self._cache = {key: (mark_key, lines)}
                return list(lines)
            payload = _g.kitty_sequence(png, ident)
            kind = 'kitty'
        elif method == 'iterm':
            payload = _g.iterm_sequence(_img.encode_png(scaled), dw, dh,
                                        name=self.name)
            kind = 'iterm'
            ident = None
        else:
            colors = min(255, info.sixel_colors or 255)
            payload = _g.sixel_sequence(scaled, colors)
            if tmux:
                payload = payload       # tmux 3.4 draws sixel itself
            kind = 'sixel'
            ident = None
        mark_key = _g.register(payload, cols, rows, kind, ident, False)
        lines = [' ' * cols for _ in range(rows)]
        lines[-1] = _g.mark(mark_key) + lines[-1]
        self._cache = {key: (mark_key, lines)}
        return list(lines)

    # -- input ---------------------------------------------------------------

    def open(self):
        """Open the image in the browser; warns instead when impossible."""
        if self.on_open is not None:
            return self.on_open(self)
        url = self.url
        if not url:
            self._warn('sin archivo ni URL que abrir')
            return False
        ok, how = _g.open_external(url)
        if ok:
            self._tell('Abriendo {0} en el navegador'.format(self.name),
                       'info')
        else:
            self._warn('no hay navegador ni pantalla para abrir {0} ({1})'
                       .format(self.name, how))
        return ok

    def _tell(self, text, kind):
        if self.app is not None:
            self.app.notify(text, kind)
            self.app.announce(text)

    def _warn(self, text):
        self._tell(_a11y.status_symbol('warning') + ' ' + text, 'warning')

    def on_key(self, key):
        if str(key) in ('enter', 'o'):
            self.open()
            return True
        return False

    def on_mouse(self, event):
        if event.action == 'press' and event.button == 0:
            self.open()
            return True
        return False


class ImageViewer(_Themed):
    """
    Several images, one at a time: Left/Right (or PgUp/PgDn) change image,
    ``f`` cycles the fit (contain, cover, none), Enter or ``o`` opens the
    current one in the browser. ``images`` are sources or ``(source, alt)``
    pairs.
    """

    role = 'img'
    focusable = True
    needs_graphics = True

    def __init__(self, images, index=0, fit='contain', method=None,
                 **kwargs):
        super(ImageViewer, self).__init__(**kwargs)
        self.items = []
        for item in images:
            src, alt = item if isinstance(item, tuple) else (item, None)
            self.items.append(Image(src, alt=alt, fit=fit, method=method))
        self.index = max(0, min(index, len(self.items) - 1))

    @property
    def current(self):
        return self.items[self.index] if self.items else None

    def a11y_name(self):
        return self.a11y_label or 'Visor de imágenes'

    def a11y_value(self):
        cur = self.current
        if cur is None:
            return 'sin imágenes'
        return '{0} de {1}: {2}'.format(self.index + 1, len(self.items),
                                        cur.alt or cur.name)

    def natural_width(self):
        return 60

    def children(self):
        return []

    def draw(self, width, height):
        cur = self.current
        if cur is None:
            return [self.paint('Sin imágenes', self.theme.muted)]
        body_h = (height - 1) if height else None
        cur.app = self.app
        body = cur.render(width, body_h).split('\n')
        arrows = ('< ', ' >') if _a11y.settings.ascii else ('◀ ', ' ▶')
        info = '{0}{1} · {2}/{3} · {4}{5}'.format(
            arrows[0], cur.alt or cur.name, self.index + 1, len(self.items),
            cur.fit, arrows[1])
        spec = self.theme.accent if self.focused else self.theme.muted
        if self.focused and self._marked():
            info = '> ' + info
        self.hot(len(body), self._prev, 0, 2)
        self.hot(len(body), self._next, max(0, width - 2), None)
        return body + [_fx.fit_line(self.paint(info, spec), width, 'c')]

    def _prev(self):
        if self.items:
            self.index = (self.index - 1) % len(self.items)
            self.announce(self.a11y_value())

    def _next(self):
        if self.items:
            self.index = (self.index + 1) % len(self.items)
            self.announce(self.a11y_value())

    def on_key(self, key):
        name = str(key)
        if name in ('left', 'pageup'):
            self._prev()
        elif name in ('right', 'pagedown'):
            self._next()
        elif name == 'f' and self.current is not None:
            order = ('contain', 'cover', 'none')
            cur = self.current
            cur.fit = order[(order.index(cur.fit) + 1) % 3] \
                if cur.fit in order else 'contain'
            cur._cache = {}
        elif name in ('enter', 'o') and self.current is not None:
            self.current.open()
        else:
            return False
        self.refresh()
        return True


def _rgb(color):
    if isinstance(color, (tuple, list)):
        return tuple(int(c) for c in color[:3])
    text = str(color).lstrip('#')
    if len(text) == 3:
        text = ''.join(c * 2 for c in text)
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def _wrap(text, width):
    from flexablelib.text_width import wrap_to_width
    return wrap_to_width(text, max(1, width)) or ['']
