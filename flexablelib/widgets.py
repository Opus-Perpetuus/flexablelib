"""
TERMINAL WIDGETS

Small renderables for dashboards, built to sit in a :class:`~flexablelib.Grid`
or a :class:`~flexablelib.Card` next to tables:

``ProgressBar``  ``Ventas  ███████████▍░░░░░░  64%``
``Sparkline``    ``▁▂▄▆█▇▅▃``
``BarChart``     one labelled horizontal bar per value
``StatusBar``    a full-width bar with left / centre / right text
``KeyHints``     ``q Salir  F1 Ayuda`` key chips
``LogView``      the tail of a log, levels coloured
``Text``         aligned, wrapped, coloured text
``Rule``         a horizontal rule with an optional title

Every widget has ``render(width=None, height=None)`` (``None`` width: the
terminal's), ``natural_width()`` and ``str(widget)``. Widths count visible
columns: ANSI escapes are zero wide, emoji and CJK two. Colour follows
``use_colors``: ``None`` means only on a terminal, honouring ``NO_COLOR`` and
``FORCE_COLOR``.
"""

import builtins
import re

from .colors import RESET, parse_spec, supports_color
from .layout import _align, _fit_line, render_width
from .text_width import (
    pad_to_width,
    strip_ansi,
    truncate_to_width,
    visible_width,
    wrap_to_width,
)

__all__ = ['ProgressBar', 'Sparkline', 'BarChart', 'StatusBar', 'KeyHints',
           'LogView', 'Text', 'Rule']

_EIGHTHS = ' ▏▎▍▌▋▊▉'
_SPARKS = '▁▂▃▄▅▆▇█'


class _Widget(object):
    """Shared colour handling and the render protocol."""

    use_colors = None

    def _active(self):
        if self.use_colors is None:
            return supports_color()
        return bool(self.use_colors)

    def _paint(self, text, spec):
        if not text or not spec or not self._active():
            return text
        prefix = parse_spec(spec)
        if not prefix:
            return text
        return prefix + text.replace(RESET, RESET + prefix) + RESET

    def _width(self, width):
        if width is None:
            width = getattr(self, 'width', None)
        if width is None:
            return min(self.natural_width(), render_width(None))
        return render_width(width)

    def _finish(self, lines, width, height):
        """Clip or pad to ``height`` lines; strip colour when it is off."""
        if height is not None:
            height = max(0, int(height))
            lines = lines[:height] + [' ' * width] * (height - len(lines))
        text = '\n'.join(lines)
        if not self._active():
            text = strip_ansi(text)
        return text

    def __str__(self):
        return self.render()


def _check_number(name, value):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise TypeError('{0} must be a number, got {1!r}'.format(name, value))


def _threshold_color(fraction, color, thresholds):
    """The colour for ``fraction``: the last threshold it reaches."""
    if not thresholds:
        return color
    pairs = sorted(thresholds.items() if isinstance(thresholds, dict)
                   else thresholds)
    chosen = color
    for limit, spec in pairs:
        if fraction >= float(limit):
            chosen = spec
    return chosen


class ProgressBar(_Widget):
    """
    A horizontal bar for a value out of a total.

    >>> print(ProgressBar(64, label='Ventas', use_colors=False).render(30))
    Ventas ██████████████▏░░░░░░░░ 64%

    ``thresholds`` changes the colour as the bar fills: ``{0.7: 'yellow',
    0.9: 'red'}``. With the default ``█`` fill the end of the bar is drawn in
    eighths (``▏▎▍▌▋▊▉``) so small changes show. ``value_format`` replaces the
    percentage, e.g. ``'{value:.0f}/{total:.0f} GB'``. ``label_width`` and
    ``value_width`` pad both ends so a stack of bars lines up.
    """

    def __init__(self, value, total=100, label=None, width=None,
                 show_percent=True, value_format=None, color='green',
                 empty_color='bright_black', label_color=None,
                 thresholds=None, fill_char='█', empty_char='░',
                 label_width=None, value_width=None, use_colors=None):
        self.value = _check_number('value', value)
        self.total = _check_number('total', total)
        if self.total <= 0:
            raise ValueError('total must be > 0')
        self.label = label
        self.width = width
        self.show_percent = show_percent
        self.value_format = value_format
        self.color = color
        self.empty_color = empty_color
        self.label_color = label_color
        self.thresholds = thresholds
        if not fill_char or not empty_char:
            raise ValueError('fill_char and empty_char cannot be empty')
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.label_width = label_width
        self.value_width = value_width
        self.use_colors = use_colors

    @property
    def fraction(self):
        """The filled share, clamped to ``0..1``."""
        return max(0.0, min(1.0, self.value / self.total))

    def _suffix(self):
        if self.value_format:
            text = self.value_format.format(
                value=self.value, total=self.total,
                percent=self.fraction * 100)
        elif self.show_percent:
            text = '{0:>3.0f}%'.format(self.fraction * 100)
        else:
            text = ''
        if self.value_width is not None:
            text = pad_to_width(text, int(self.value_width), 'r')
        return text

    def _label(self):
        if self.label is None:
            return ''
        if self.label_width is not None:
            return _fit_line(str(self.label), int(self.label_width))
        return str(self.label)

    def natural_width(self):
        label, suffix = self._label(), self._suffix()
        return (visible_width(label) + (1 if label else 0) + 20 +
                (1 + visible_width(suffix) if suffix else 0))

    def bar(self, width):
        """Just the bar, ``width`` columns, coloured."""
        width = max(0, int(width))
        cells = self.fraction * width
        full = int(cells)
        rest = cells - full
        partial = ''
        if self.fill_char == '█' and full < width:
            eighth = int(round(rest * 8))
            if eighth == 8:
                full += 1
            elif eighth:
                partial = _EIGHTHS[eighth]
        filled = self.fill_char * full + partial
        empty = self.empty_char * (width - full - (1 if partial else 0))
        color = _threshold_color(self.fraction, self.color, self.thresholds)
        return self._paint(filled, color) + self._paint(empty,
                                                        self.empty_color)

    def render(self, width=None, height=None):
        width = self._width(width)
        label, suffix = self._label(), self._suffix()
        head = (self._paint(label, self.label_color) + ' ') if label else ''
        tail = (' ' + suffix) if suffix else ''
        room = width - visible_width(head) - visible_width(tail)
        if room < 1:
            # Too narrow for label and value: keep the bar.
            head, tail, room = '', '', width
        line = head + self.bar(room) + tail
        return self._finish([line], width, height)


class Sparkline(_Widget):
    """
    A one-line chart of a series: ``▁▂▄▆█▇▅▃``.

    When the series is longer than the width the most recent values are
    shown. ``low`` / ``high`` fix the scale (default: the data's range).
    ``label`` goes in front and ``show_last`` appends the latest value.
    """

    def __init__(self, values, width=None, color=None, low=None, high=None,
                 label=None, show_last=False, value_format='{0:g}',
                 chars=_SPARKS, label_color=None, label_width=None,
                 use_colors=None):
        self.values = [_check_number('values', v) for v in values]
        self.width = width
        self.color = color
        self.low = low
        self.high = high
        self.label = label
        self.show_last = show_last
        self.value_format = value_format
        if not chars:
            raise ValueError('chars cannot be empty')
        self.chars = chars
        self.label_color = label_color
        self.label_width = label_width
        self.use_colors = use_colors

    def _parts(self):
        label = '' if self.label is None else str(self.label)
        if label and self.label_width is not None:
            label = _fit_line(label, int(self.label_width))
        head = (label + ' ') if label else ''
        tail = ''
        if self.show_last and self.values:
            tail = ' ' + self.value_format.format(self.values[-1])
        return head, tail

    def natural_width(self):
        head, tail = self._parts()
        return visible_width(head) + max(1, len(self.values)) + \
            visible_width(tail)

    def line(self, width):
        """Just the chart, at most ``width`` columns."""
        values = self.values[-width:] if width > 0 else []
        if not values:
            return ''
        low = min(values) if self.low is None else float(self.low)
        high = max(values) if self.high is None else float(self.high)
        steps = len(self.chars) - 1
        out = []
        for v in values:
            if high == low:
                index = steps // 2 if high else 0
            else:
                index = int(round((min(max(v, low), high) - low) /
                                  (high - low) * steps))
            out.append(self.chars[index])
        return self._paint(''.join(out), self.color)

    def render(self, width=None, height=None):
        width = self._width(width)
        head, tail = self._parts()
        room = width - visible_width(head) - visible_width(tail)
        if room < 1:
            head, tail, room = '', '', width
        line = self._paint(head, self.label_color) + self.line(room) + tail
        return self._finish([line], width, height)


class BarChart(_Widget):
    """
    Labelled horizontal bars, one per value.

    >>> print(BarChart({'Norte': 120, 'Sur': 80}, use_colors=False).render(30))
    Norte ███████████████████ 120
    Sur   ████████████▋        80

    ``colors`` is one spec or ``{label: spec}``; ``sort=True`` puts the
    largest first; ``max`` fixes the scale.
    """

    def __init__(self, data, width=None, color='cyan', colors=None,
                 show_values=True, value_format='{0:,.0f}', sort=False,
                 max=None, label_color=None, fill_char='█', use_colors=None):
        if isinstance(data, dict):
            pairs = list(data.items())
        else:
            pairs = [tuple(item) for item in data]
        self.data = [(str(k), _check_number('value', v)) for k, v in pairs]
        if any(v < 0 for _, v in self.data):
            raise ValueError('BarChart values must be >= 0')
        self.width = width
        self.color = color
        self.colors = colors or {}
        self.show_values = show_values
        self.value_format = value_format
        self.sort = sort
        self.max = max
        self.label_color = label_color
        self.fill_char = fill_char
        self.use_colors = use_colors

    def _rows(self):
        rows = list(self.data)
        if self.sort:
            rows.sort(key=lambda kv: kv[1], reverse=True)
        return rows

    def natural_width(self):
        rows = self._rows()
        if not rows:
            return 1
        label_w = max(visible_width(k) for k, _ in rows)
        value_w = max(visible_width(self.value_format.format(v))
                      for _, v in rows) if self.show_values else 0
        return label_w + 1 + 24 + (1 + value_w if value_w else 0)

    def render(self, width=None, height=None):
        width = self._width(width)
        rows = self._rows()
        if not rows:
            return self._finish([''], width, height)
        label_w = min(max(visible_width(k) for k, _ in rows),
                      max(1, width // 3))
        values = [self.value_format.format(v) for _, v in rows]
        value_w = max(visible_width(v) for v in values) \
            if self.show_values else 0
        bar_w = width - label_w - 1 - (value_w + 1 if value_w else 0)
        if bar_w < 1:
            bar_w, value_w = max(1, width - label_w - 1), 0
        top = float(self.max) if self.max is not None else \
            builtins.max(v for _, v in rows)
        lines = []
        for (label, value), shown in zip(rows, values):
            spec = self.colors.get(label, self.color) \
                if isinstance(self.colors, dict) else self.colors
            bar = ProgressBar(min(value, top) if top else 0, top or 1,
                              show_percent=False, color=spec,
                              fill_char=self.fill_char, empty_char=' ',
                              empty_color=None, use_colors=self._active())
            line = (self._paint(_fit_line(label, label_w), self.label_color) +
                    ' ' + bar.bar(bar_w))
            if value_w:
                line += ' ' + pad_to_width(shown, value_w, 'r')
            lines.append(line)
        return self._finish(lines, width, height)


class StatusBar(_Widget):
    """
    One full-width line with ``left``, ``center`` and ``right`` text on a
    background, like an editor's status line.

    When the parts do not fit, the centre goes first, then the left part is
    cut with ``…``.
    """

    def __init__(self, left='', center='', right='', color='black on cyan',
                 width=None, padding=1, use_colors=None):
        self.left = str(left or '')
        self.center = str(center or '')
        self.right = str(right or '')
        self.color = color
        self.width = width
        self.padding = max(0, int(padding))
        self.use_colors = use_colors

    def natural_width(self):
        parts = [p for p in (self.left, self.center, self.right) if p]
        return sum(visible_width(p) for p in parts) + \
            2 * max(0, len(parts) - 1) + 2 * self.padding

    def render(self, width=None, height=None):
        width = self._width(width)
        pad = ' ' * min(self.padding, max(0, (width - 1) // 2))
        inner = width - 2 * len(pad)
        left, center, right = self.left, self.center, self.right
        lw, cw, rw = (visible_width(left), visible_width(center),
                      visible_width(right))
        if lw + cw + rw + (2 if center else 0) + (2 if left and right else 0)\
                > inner:
            center, cw = '', 0
        if lw + rw + (1 if left and right else 0) > inner:
            rw = min(rw, inner)
            right = truncate_to_width(right, rw, '…') if rw < \
                visible_width(right) else right
            lw = max(0, inner - rw - (1 if rw else 0))
            left = truncate_to_width(left, lw, '…') if lw else ''
            lw = visible_width(left)
        body = left
        if center:
            start = max(lw + 1, (inner - cw) // 2)
            start = min(start, inner - rw - 1 - cw) if rw else start
            body = body + ' ' * (start - lw) + center
        used = visible_width(body)
        body = body + ' ' * max(0, inner - used - rw) + right
        body = _fit_line(body, inner)
        text = pad + body + pad
        return self._finish([self._paint(text, self.color)], width, height)


class KeyHints(_Widget):
    """
    Keyboard shortcuts as chips: ``q Salir  F1 Ayuda  / Buscar``.

    ``keys`` is a dict or ``(key, action)`` pairs. Hints wrap onto more lines
    when they do not fit.
    """

    def __init__(self, keys, key_color='black on white', label_color=None,
                 separator='  ', width=None, align='l', use_colors=None):
        pairs = list(keys.items()) if isinstance(keys, dict) else \
            [tuple(k) for k in keys]
        self.keys = [(str(k), str(v)) for k, v in pairs]
        self.key_color = key_color
        self.label_color = label_color
        self.separator = separator
        self.width = width
        self.align = _align(align)
        self.use_colors = use_colors

    def _chips(self):
        return [(' {0} '.format(k), ' ' + v) for k, v in self.keys]

    def natural_width(self):
        chips = self._chips()
        return sum(visible_width(k) + visible_width(v) for k, v in chips) + \
            visible_width(self.separator) * max(0, len(chips) - 1)

    def render(self, width=None, height=None):
        width = self._width(width)
        lines, current, used = [], [], 0
        sep_w = visible_width(self.separator)
        for key, label in self._chips():
            chip_w = visible_width(key) + visible_width(label)
            if chip_w > width:
                key = truncate_to_width(key, width, '')
                label = truncate_to_width(label, max(0, width -
                                                     visible_width(key)), '…')
                chip_w = visible_width(key) + visible_width(label)
            extra = chip_w + (sep_w if current else 0)
            if current and used + extra > width:
                lines.append((current, used))
                current, used = [], 0
                extra = chip_w
            current.append(self._paint(key, self.key_color) +
                           self._paint(label, self.label_color))
            used += extra
        if current:
            lines.append((current, used))
        out = []
        for chips, used in lines:
            out.append(pad_to_width(self.separator.join(chips), width,
                                    self.align))
        return self._finish(out, width, height)


_LEVELS = (
    (re.compile(r'\b(CRITICAL|FATAL|ERROR|ERR)\b'), 'bold red'),
    (re.compile(r'\b(WARNING|WARN)\b'), 'yellow'),
    (re.compile(r'\b(INFO)\b'), 'cyan'),
    (re.compile(r'\b(DEBUG|TRACE)\b'), 'bright_black'),
    (re.compile(r'\b(OK|SUCCESS|DONE)\b'), 'green'),
)


class LogView(_Widget):
    """
    The last lines of a log, sized to its slot.

    Level words (``ERROR``, ``WARN``, ``INFO``, ``DEBUG``, ``OK``) are
    coloured; ``level_colors`` overrides them as ``{word: spec}``. Long lines
    are cut with ``…`` unless ``wrap=True``. ``height`` (or the slot's height
    in a grid with a height) is how many lines to show -- the newest ones,
    unless ``tail=False``.
    """

    def __init__(self, lines=None, height=None, width=None, wrap=False,
                 tail=True, level_colors=None, color_lines=False,
                 max_lines=1000, use_colors=None):
        self.max_lines = max(1, int(max_lines))
        self.lines = []
        for line in lines or []:
            self.append(line)
        self.height = height
        self.width = width
        self.wrap = wrap
        self.tail = tail
        self.level_colors = level_colors
        self.color_lines = color_lines
        self.use_colors = use_colors

    def append(self, line):
        """Add one line (or several, split on newlines); returns ``self``."""
        for part in str(line).split('\n'):
            self.lines.append(part)
        del self.lines[:-self.max_lines]
        return self

    def natural_width(self):
        return max([visible_width(l) for l in self.lines] or [1])

    def _spec_for(self, word):
        word = word.upper()
        if self.level_colors:
            for key, spec in self.level_colors.items():
                if key.upper() == word:
                    return spec
        for pattern, spec in _LEVELS:
            if pattern.fullmatch(word):
                return spec
        return None

    def _colour(self, line):
        if not self._active() or '\x1b' in line:
            return line
        words = [p.pattern for p, _ in _LEVELS]
        if self.level_colors:
            words.insert(0, r'(?i:\b(' + '|'.join(
                re.escape(k) for k in self.level_colors) + r')\b)')
        pattern = re.compile('|'.join(words))
        match = pattern.search(line)
        if not match:
            return line
        spec = self._spec_for(match.group(0))
        if self.color_lines:
            return self._paint(line, spec)
        return (line[:match.start()] + self._paint(match.group(0), spec) +
                line[match.end():])

    def render(self, width=None, height=None):
        width = self._width(width)
        if height is None:
            height = self.height
        rows = []
        for line in self.lines:
            if self.wrap:
                rows.extend(wrap_to_width(line, width) or [''])
            elif visible_width(line) > width:
                rows.append(truncate_to_width(line, width, '…'))
            else:
                rows.append(line)
        if height is not None:
            height = int(height)
            rows = rows[-height:] if self.tail else rows[:height]
            if height == 0:
                rows = []
        out = [pad_to_width(self._colour(r), width) for r in rows] or \
            [' ' * width]
        return self._finish(out, width, height)


class Text(_Widget):
    """Text that wraps (or is cut with ``…``), aligned and coloured."""

    def __init__(self, text, align='l', color=None, wrap=True, width=None,
                 use_colors=None):
        self.text = str(text)
        self.align = _align(align)
        self.color = color
        self.wrap = wrap
        self.width = width
        self.use_colors = use_colors

    def natural_width(self):
        return max([visible_width(l) for l in self.text.split('\n')] or [0])

    def render(self, width=None, height=None):
        width = self._width(width)
        out = []
        for raw in self.text.split('\n'):
            if self.wrap:
                pieces = wrap_to_width(raw, width) if raw else ['']
            elif visible_width(raw) > width:
                pieces = [truncate_to_width(raw, width, '…')]
            else:
                pieces = [raw]
            for piece in pieces:
                out.append(pad_to_width(self._paint(piece, self.color), width,
                                        self.align))
        return self._finish(out, width, height)


class Rule(_Widget):
    """A full-width horizontal rule, optionally titled: ``── Ventas ──``."""

    def __init__(self, title=None, char='─', align='c', color='bright_black',
                 title_color='bold', width=None, use_colors=None):
        if not char:
            raise ValueError('char cannot be empty')
        self.title = None if title is None else str(title)
        self.char = char
        self.align = _align(align, 'c')
        self.color = color
        self.title_color = title_color
        self.width = width
        self.use_colors = use_colors

    def natural_width(self):
        return (visible_width(self.title) + 6) if self.title else 1

    def render(self, width=None, height=None):
        if width is None and self.width is None:
            width = render_width(None)
        width = self._width(width)
        if not self.title or visible_width(self.title) + 4 > width:
            line = self._paint((self.char * width)[:width], self.color)
            return self._finish([line], width, height)
        label = ' ' + self.title + ' '
        free = width - visible_width(label)
        if self.align == 'l':
            left = 2
        elif self.align == 'r':
            left = free - 2
        else:
            left = free // 2
        line = (self._paint(self.char * left, self.color) +
                self._paint(label, self.title_color) +
                self._paint(self.char * (free - left), self.color))
        return self._finish([line], width, height)
