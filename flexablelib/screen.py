"""
FULL-SCREEN LAYOUT AND LIVE REFRESH

``Screen``
    A header, a body and a footer laid out to the exact terminal size: the
    header sticks to the top, the footer to the bottom, and the body gets
    every line in between (a :class:`~flexablelib.Grid` body hands them to
    its fraction rows, a :class:`~flexablelib.widgets.LogView` shows that many
    lines). Content taller than the screen is cut, so the footer never scrolls
    away.

``Live``
    Redraws a renderable in place: ``with Live(screen) as live: ...
    live.update()``. On a terminal it uses the alternate screen and hides the
    cursor, restoring both on exit; on a pipe or file it writes each frame
    once, plainly.
"""

import sys
import time

from .layout import _accepts_height, _render_child, _fit_line, render_width
from .utils import get_window_size

__all__ = ['Screen', 'Live', 'render_height']

ALT_SCREEN_ON = '\x1b[?1049h'
ALT_SCREEN_OFF = '\x1b[?1049l'
CURSOR_HIDE = '\x1b[?25l'
CURSOR_SHOW = '\x1b[?25h'
HOME = '\x1b[H'
CLEAR_LINE = '\x1b[K'
CLEAR_BELOW = '\x1b[J'


def render_height(height=None):
    """The height to lay out into: ``height`` if given, else the terminal's."""
    if height is not None:
        height = int(height)
        if height < 1:
            raise ValueError('height must be >= 1, got {0}'.format(height))
        return height
    _, lines = get_window_size()
    return max(1, int(lines))


def _render(child, width, height=None):
    if child is None:
        return []
    if height is not None and _accepts_height(child):
        text = child.render(width=width, height=height)
    else:
        text = _render_child(child, width)
    return text.split('\n') if text != '' else []


class Screen(object):
    """
    A whole terminal screen: ``header`` on top, ``footer`` at the bottom,
    ``body`` filling the rest.

    >>> screen = Screen(body=grid, header=StatusBar('App', right='12:00'),
    ...                 footer=KeyHints({'q': 'Salir'}))
    >>> print(screen.render(width=100, height=30))   # exactly 30 lines

    ``width`` / ``height`` fix the size (default: the terminal's).
    ``height=None`` *and* ``fit_height=False`` let the body take its natural
    height (the footer then follows it instead of sticking to the bottom).
    ``margin`` is blank columns on each side.
    """

    def __init__(self, body=None, header=None, footer=None, width=None,
                 height=None, fit_height=True, margin=0):
        self.body = body
        self.header = header
        self.footer = footer
        self.width = width
        self.height = height
        self.fit_height = bool(fit_height)
        self.margin = max(0, int(margin))

    def natural_width(self):
        from .layout import _natural_width
        return max(_natural_width(self.body), _natural_width(self.header),
                   _natural_width(self.footer)) + 2 * self.margin

    def __str__(self):
        return self.render()

    def render(self, width=None, height=None):
        width = render_width(width if width is not None else self.width)
        if height is None:
            height = self.height
        if height is None and self.fit_height:
            height = render_height(None)
        inner = max(1, width - 2 * self.margin)
        head = _render(self.header, inner)
        foot = _render(self.footer, inner)
        if height is None:
            body = _render(self.body, inner)
        else:
            height = int(height)
            room = height - len(head) - len(foot)
            if room < 0:
                # The footer outranks the header: drop header lines first.
                head = head[:max(0, height - len(foot))]
                foot = foot[-height:] if len(foot) > height else foot
                room = height - len(head) - len(foot)
            body = _render(self.body, inner, room) if room > 0 else []
            body = body[:room] + [''] * (room - len(body[:room]))
        side = ' ' * self.margin
        lines = [side + _fit_line(line, inner) + side
                 for line in head + body + foot]
        return '\n'.join(lines)


class Live(object):
    """
    Redraw a renderable in place.

    >>> with Live(screen) as live:
    ...     for tick in range(10):
    ...         update_data(tick)
    ...         live.update()
    ...         time.sleep(1)

    ``renderable`` is anything with ``render(width, height)`` (or a string);
    ``update(new)`` swaps it. ``screen=True`` uses the alternate screen so the
    shell comes back untouched; ``transient=False`` reprints the last frame
    on the normal screen at exit. ``stream`` defaults to ``sys.stdout``;
    ``force_terminal`` overrides the ``isatty()`` check.
    """

    def __init__(self, renderable=None, stream=None, screen=True,
                 hide_cursor=True, transient=False, force_terminal=None,
                 width=None, height=None):
        self.renderable = renderable
        self.stream = stream if stream is not None else sys.stdout
        self.screen = screen
        self.hide_cursor = hide_cursor
        self.transient = transient
        self.force_terminal = force_terminal
        self.width = width
        self.height = height
        self.frames = 0
        self._last = None
        self._started = False

    @property
    def is_terminal(self):
        if self.force_terminal is not None:
            return bool(self.force_terminal)
        try:
            return bool(self.stream.isatty())
        except (AttributeError, ValueError):
            return False

    def _frame(self):
        r = self.renderable
        if r is None:
            return ''
        width = render_width(self.width)
        height = self.height
        if height is None and self.is_terminal:
            height = render_height(None)
        if isinstance(r, str):
            lines = r.split('\n')
            if height is not None:
                lines = lines[:height]
            return '\n'.join(lines)
        if _accepts_height(r):
            return r.render(width=width, height=height)
        return _render_child(r, width)

    def _write(self, text):
        self.stream.write(text)
        flush = getattr(self.stream, 'flush', None)
        if callable(flush):
            flush()

    def start(self):
        if self._started:
            return self
        self._started = True
        if self.is_terminal:
            codes = (ALT_SCREEN_ON if self.screen else '') + \
                (CURSOR_HIDE if self.hide_cursor else '')
            if codes:
                self._write(codes)
        return self

    def stop(self):
        if not self._started:
            return
        self._started = False
        if self.is_terminal:
            codes = (CURSOR_SHOW if self.hide_cursor else '') + \
                (ALT_SCREEN_OFF if self.screen else '')
            if codes:
                self._write(codes)
            if self.screen and not self.transient and self._last:
                self._write(self._last + '\n')

    def update(self, renderable=None):
        """Swap in ``renderable`` (if given) and redraw; returns the frame."""
        if renderable is not None:
            self.renderable = renderable
        if not self._started:
            self.start()
        frame = self._frame()
        if self.is_terminal:
            body = (CLEAR_LINE + '\n').join(frame.split('\n'))
            self._write(HOME + body + CLEAR_LINE + CLEAR_BELOW)
        else:
            self._write(frame + '\n')
        self._last = frame
        self.frames += 1
        return frame

    refresh = update

    def run(self, step=None, interval=1.0, iterations=None, sleep=time.sleep):
        """
        Redraw every ``interval`` seconds, calling ``step(frame_number)``
        first; stop after ``iterations`` frames, when ``step`` returns
        ``False``, or on Ctrl-C.
        """
        count = 0
        with self:
            try:
                while iterations is None or count < iterations:
                    if step is not None and step(count) is False:
                        break
                    self.update()
                    count += 1
                    if iterations is None or count < iterations:
                        sleep(interval)
            except KeyboardInterrupt:
                pass
        return count

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False
