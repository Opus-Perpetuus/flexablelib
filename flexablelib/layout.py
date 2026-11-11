"""
CARDS, GRIDS AND RESPONSIVE LAYOUT

Terminal building blocks that sit next to :class:`~flexablelib.Table`:

``Card``
    One record in a frame: a title (set into the top border when the style
    draws one), an optional subtitle, ``label  value`` fields (optionally laid
    out in a grid of 2+ columns), an optional body (any renderable) and a
    footer. Cards use the same 54 border styles, the same themes and the same
    ``panel`` / ``shadow`` as tables.

``Grid``
    Places renderables (cards, tables, strings, other grids) in columns that
    reflow with the available width -- a grid of cards or the layout of a
    whole terminal screen. Children may span several columns.

Every renderable here has ``render(width=None)``; ``width=None`` means the
current terminal width. ``Table.render(width)`` follows the same protocol, so
tables drop into grids and cards unchanged.

Widths are always visible columns: ANSI escapes count zero, emoji and CJK
count two.
"""

import inspect
import re

from .colors import RESET, parse_spec, supports_color
from .style_compositions import (
    __style_compositions as _STYLE_CATALOGUE,
    DEPRECATED_STYLE_NAMES,
)
from .text_width import (
    pad_to_width,
    strip_ansi,
    tokenize,
    measured_clusters,
    truncate_to_width,
    visible_width,
    wrap_to_width,
)
from .utils import get_window_size

__all__ = ['Card', 'Grid', 'GridCell', 'render_width', 'wrap_panel',
           'add_shadow', 'inset_label']

_ALIGNS = {'l': 'l', 'left': 'l', 'c': 'c', 'center': 'c', 'centre': 'c',
           'r': 'r', 'right': 'r'}

PANEL_PRESETS = {
    'rounded': ('╭', '─', '╮', '│', '╰', '╯'),
    'sharp':   ('┌', '─', '┐', '│', '└', '┘'),
    'ascii':   ('+', '-', '+', '|', '+', '+'),
    'double':  ('╔', '═', '╗', '║', '╚', '╝'),
    'heavy':   ('┏', '━', '┓', '┃', '┗', '┛'),
}


def _align(value, default='l'):
    if value is None:
        return default
    try:
        return _ALIGNS[str(value).lower()]
    except KeyError:
        raise ValueError(
            "align must be 'l', 'c' or 'r' (or left/center/right), "
            'got {0!r}'.format(value)
        )


def render_width(width=None):
    """The width to lay out into: ``width`` if given, else the terminal's."""
    if width is not None:
        width = int(width)
        if width < 1:
            raise ValueError('width must be >= 1, got {0}'.format(width))
        return width
    columns, _ = get_window_size()
    return max(1, int(columns))


def _block_width(text):
    return max((visible_width(line) for line in text.split('\n')), default=0)


# +---------------------------------------------------------------------------+
# Panel and shadow (shared with Table so both draw exactly the same chrome)

def _panel_name(panel):
    if isinstance(panel, str) and panel not in ('True', 'true', '1'):
        return panel.lower()
    return 'rounded'


def _paint(text, prefix):
    """Wrap ``text`` in an SGR prefix (no-op when the prefix is empty)."""
    if not prefix or not text:
        return text
    return prefix + text + RESET


def wrap_panel(text, panel=True, color=None):
    """
    Frame a block of text in an outer panel.

    ``panel`` is ``True`` (rounded) or one of ``rounded``, ``sharp``,
    ``ascii``, ``double``, ``heavy``. ``color`` is a colour spec for the
    frame.
    """
    tl, hz, tr, vt, bl, br = PANEL_PRESETS.get(
        _panel_name(panel), PANEL_PRESETS['rounded'])
    prefix = parse_spec(color) if color else ''
    lines = text.splitlines()
    width = max((visible_width(line) for line in lines), default=0)
    out = [_paint(tl + hz * width + tr, prefix)]
    for line in lines:
        pad = width - visible_width(line)
        out.append(_paint(vt, prefix) + line + ' ' * pad + _paint(vt, prefix))
    out.append(_paint(bl + hz * width + br, prefix))
    return '\n'.join(out)


def add_shadow(text, shadow=True, color=None):
    """
    Drop a one-column shadow to the right and one row below a block.

    ``shadow`` is ``True`` (``░``) or the glyph to use.
    """
    glyph = '░'
    if isinstance(shadow, str) and shadow not in ('True', 'true', '1'):
        glyph = shadow[:1] or '░'
    prefix = parse_spec(color) if color else ''
    lines = text.splitlines()
    width = max((visible_width(line) for line in lines), default=0)
    out = []
    for i, line in enumerate(lines):
        body = line + ' ' * (width - visible_width(line))
        out.append(body + (' ' if i == 0 else _paint(glyph, prefix)))
    out.append(' ' + _paint(glyph * width, prefix))
    return '\n'.join(out)


def _panel_overhead(panel, shadow):
    return (2 if panel else 0) + (1 if shadow else 0)


# +---------------------------------------------------------------------------+
# Labels set into a border line

def _rule_runs(plain, glyph):
    """Maximal runs ``[start, end)`` of ``glyph`` in a plain border line."""
    runs = []
    start = None
    for i, char in enumerate(plain + '\0'):
        if char == glyph:
            if start is None:
                start = i
        elif start is not None:
            runs.append((start, i))
            start = None
    return runs


def _splice(line, start, end, replacement):
    """Replace visible columns ``[start, end)``; keep any escapes inside."""
    before, inside, after = [], [], []
    column = 0
    for kind, value in tokenize(line):
        if kind == 'ansi':
            (before if column < start else inside if column < end
             else after).append(value)
            continue
        for cluster, width in measured_clusters(value):
            (before if column < start else inside if column < end
             else after).append(cluster)
            column += width
    kept = ''.join(token for token in inside if token.startswith('\x1b'))
    return ''.join(before) + replacement + kept + ''.join(after)


def inset_label(line, label, align='c', glyph=None, label_prefix='',
                border_prefix=''):
    """
    Set ``label`` into a horizontal border line: ``╭─ Label ─────╮``.

    The label only goes over a run of plain rule glyphs, never over a corner
    or a column junction (``┬`` ``┴`` ``┼``), so the columns below still meet
    the frame. Returns the new line, or ``None`` when no run is long enough
    (the caller then draws the label outside the frame instead).

    ``label_prefix`` colours the label; ``border_prefix`` is the SGR the
    border was drawn with, reopened after the label.
    """
    plain = strip_ansi(line)
    if not plain.strip():
        return None
    if glyph is None:
        # The rule glyph is the most common non-space character.
        counts = {}
        for char in plain:
            if not char.isspace():
                counts[char] = counts.get(char, 0) + 1
        if not counts:
            return None
        glyph = max(counts, key=counts.get)
    text = ' ' + label + ' '
    need = visible_width(text)
    align = _align(align, 'c')
    # Keep at least one rule glyph either side of the label.
    runs = [(s, e) for s, e in _rule_runs(plain, glyph) if e - s >= need + 2]
    if not runs:
        return None
    total = len(plain)
    # Left: the first stretch of rule (from the left) long enough; right:
    # the first from the right; centre: the one nearest the middle.
    if align == 'l':
        start, end = runs[0]
        pos = start + 1
    elif align == 'r':
        start, end = runs[-1]
        pos = end - 1 - need
    else:
        centre = total // 2
        best = None
        for s, e in runs:
            pos = min(max(centre - need // 2, s + 1), e - 1 - need)
            distance = abs(pos + need // 2 - centre)
            if best is None or distance < best[0]:
                best = (distance, pos)
        pos = best[1]
    if label_prefix or border_prefix:
        replacement = (RESET if border_prefix else '') + \
            _paint(text, label_prefix) + border_prefix
    else:
        replacement = text
    # A plain line is one cluster per character, so string index == column
    # only when every glyph is one column wide; box glyphs are.
    return _splice(line, pos, pos + need, replacement)


# +---------------------------------------------------------------------------+
# Style frames

def _style(name):
    name = DEPRECATED_STYLE_NAMES.get(name, name)
    try:
        return getattr(_STYLE_CATALOGUE, name), name
    except (AttributeError, TypeError):
        raise ValueError('unknown style {0!r}'.format(name))


def _rule(sep):
    """A usable horizontal SeparatorLine, or None when it draws nothing."""
    if sep is None or not sep.middle or not sep.middle.strip():
        return None
    return sep


class _Frame(object):
    """The glyphs a card borrows from a table style."""

    def __init__(self, composition):
        c = composition
        self.top = _rule(c.superior_header_line_no_header) or _rule(
            c.superior_header_line)
        self.title_top = _rule(c.superior_header_line) or self.top
        self.divider = _rule(c.inferior_header_line)
        self.row_rule = _rule(c.table_body_line)
        self.bottom = _rule(c.table_end_line)
        body = c.vertical_table_body_lines
        head = c.vertical_header_lines
        self.body_sides = (self._side(body.left), self._side(body.right))
        self.head_sides = (self._side(head.left), self._side(head.right))
        sides = [s for s in self.body_sides + self.head_sides]
        self.left_w = max(visible_width(self.body_sides[0]),
                          visible_width(self.head_sides[0]))
        self.right_w = max(visible_width(self.body_sides[1]),
                           visible_width(self.head_sides[1]))
        self.margin = max(0, int(c.margin or 0))
        del sides
        self.foot_divider = self._foot_divider()

    _TEES = {'│': ('├', '─', '┤'), '║': ('╟', '─', '╢'),
             '┃': ('┣', '━', '┫'), '|': ('+', '-', '+')}

    def _foot_divider(self):
        """Rule between body and footer that joins the body's sides."""
        from .style_compositions import SeparatorLine
        if self.row_rule is not None:
            return self.row_rule
        if self.divider is not None and self.head_sides == self.body_sides:
            return self.divider
        left = self.body_sides[0]
        if left in self._TEES:
            tl, mid, tr = self._TEES[left]
            return SeparatorLine(tl, mid, None, tr)
        return self.divider

    @staticmethod
    def _side(glyph):
        if glyph is None or not glyph.strip():
            return ''
        return glyph

    def sides(self, head=False):
        left, right = self.head_sides if head else self.body_sides
        return (pad_to_width(left, self.left_w, 'r'),
                pad_to_width(right, self.right_w))

    def line(self, sep, inner):
        """Draw one horizontal rule spanning the frame."""
        if sep is None:
            return None
        left = sep.left if (sep.left and self.left_w) else (
            sep.middle * self.left_w)
        right = sep.right if (sep.right and self.right_w) else (
            sep.middle * self.right_w)
        return (pad_to_width(left, self.left_w, fill=sep.middle[:1]) +
                sep.middle * inner +
                pad_to_width(right, self.right_w, fill=sep.middle[:1]))


def _theme_settings(name):
    from .table import Table
    if name not in Table.THEMES:
        raise ValueError('unknown theme {0!r}; choose from {1}'.format(
            name, ', '.join(sorted(Table.THEMES))))
    return Table.THEMES[name]


def _zebra_specs(zebra):
    if zebra is None or zebra is False:
        return ('', '')
    if zebra is True:
        return ('', 'reverse')
    if isinstance(zebra, (list, tuple)):
        even = zebra[0] if len(zebra) > 0 else ''
        odd = zebra[1] if len(zebra) > 1 else ''
        return (even or '', odd or '')
    return ('', zebra)


def _render_child(child, width):
    """Render any supported child into at most ``width`` columns."""
    if child is None:
        return ''
    render = getattr(child, 'render', None)
    if callable(render):
        try:
            return render(width=width)
        except TypeError:
            return str(render())
    text = str(child)
    lines = []
    for line in text.split('\n'):
        lines.extend(wrap_to_width(line, width) if line else [''])
    return '\n'.join(lines)


def _natural_width(child):
    if child is None:
        return 0
    measure = getattr(child, 'natural_width', None)
    if callable(measure):
        return measure()
    return _block_width(str(child))


def _fit_line(text, width, align='l'):
    """Exactly ``width`` visible columns: pad, or cut what overflows."""
    if visible_width(text) > width:
        text = truncate_to_width(text, width, suffix='')
    return pad_to_width(text, width, align)


class _Painter(object):
    """Colour helper that honours ``use_colors`` and avoids stray resets."""

    def __init__(self, active):
        self.active = active

    def prefix(self, spec):
        if not self.active or not spec:
            return ''
        return parse_spec(spec)

    def segment(self, text, spec, fill=''):
        """Colour ``text`` so it ends back on the ``fill`` background."""
        prefix = self.prefix(spec)
        if not self.active:
            return strip_ansi(text) if text else text
        if not prefix:
            if fill and RESET in text:
                text = text.replace(RESET, RESET + fill)
            return text
        if text.endswith(RESET):
            text = text[:-len(RESET)]
        text = text.replace(RESET, RESET + fill + prefix)
        return prefix + text + RESET + fill

    def fill_line(self, segments_text, fill):
        """Open ``fill`` across a whole interior line."""
        if not fill:
            return segments_text
        body = segments_text
        if body.endswith(RESET + fill):
            body = body[:-len(fill)]
            return fill + body
        return fill + body + RESET


# +---------------------------------------------------------------------------+
# Card

class Card(object):
    """
    One record drawn as a framed card.

    >>> card = Card(title='Ana', subtitle='Norte',
    ...             fields={'Edad': 28, 'Ciudad': 'Guadalajara'},
    ...             style_name='rounded')
    >>> print(card.render(width=26))
    ╭─ Ana ──────────────────╮
    │ Norte                  │
    ├────────────────────────┤
    │ Edad     28            │
    │ Ciudad   Guadalajara   │
    ╰────────────────────────╯

    Parameters
    ----------
    title, subtitle, footer : str, optional
        The title is set into the top border when the style draws one
        (``title_position='border'``), otherwise it opens the card.
    fields : dict or list of (label, value) pairs
        Shown as ``label  value`` rows. ``field_columns=2`` (or more) lays
        them out as a grid of tiles, label above value.
    body : renderable, optional
        Anything with ``render(width)`` (Table, Grid, Card) or plain text,
        drawn after the fields.
    actions : list of str, optional
        Drawn as ``[ Action ]`` chips on the last line.
    style_name : str
        Any table style; deprecated names are accepted.
    theme : str, optional
        A table theme name (``dark``, ``ocean``, ``neon``...).
    width, max_width, min_width : int, optional
        Fixed width, or bounds for the natural width.
    padding : int, optional
        Spaces between the frame and the content (default: the style margin,
        at least 1 when the style draws side borders).
    """

    def __init__(self, title=None, subtitle=None, fields=None, footer=None,
                 body=None, actions=None, style_name='rounded', theme=None,
                 title_align='l', title_position='auto', align='l',
                 label_align='l', field_columns=1, field_layout='auto',
                 field_gap=2, field_rules=None, width=None, max_width=None,
                 min_width=None, padding=None, height=None, use_colors=None,
                 title_color='bold', subtitle_color='dim', label_color='dim',
                 value_color=None, value_colors=None, footer_color='dim',
                 border_color=None, color=None, zebra=None,
                 panel=False, shadow=False, panel_color=None,
                 shadow_color=None):
        self.title = None if title is None else str(title)
        self.subtitle = None if subtitle is None else str(subtitle)
        self.footer = None if footer is None else str(footer)
        self.fields = fields
        self.body = body
        self.actions = list(actions) if actions else []
        self.style_name = style_name
        self.title_align = title_align
        self.title_position = title_position
        self.align = align
        self.label_align = label_align
        self.field_columns = field_columns
        self.field_layout = field_layout
        self.field_gap = field_gap
        self.field_rules = field_rules
        self.width = width
        self.max_width = max_width
        self.min_width = min_width
        self.padding = padding
        self.height = height
        self.use_colors = use_colors
        self.title_color = title_color
        self.subtitle_color = subtitle_color
        self.label_color = label_color
        self.value_color = value_color
        self.value_colors = value_colors
        self.footer_color = footer_color
        self.border_color = border_color
        self.color = color
        self.zebra = zebra
        self.panel = panel
        self.shadow = shadow
        self.panel_color = panel_color
        self.shadow_color = shadow_color
        if theme is not None:
            self.apply_theme(theme)

    # -- properties with validation --------------------------------------

    @property
    def fields(self):
        """The ``(label, value)`` pairs, in order."""
        return list(self.__fields)

    @fields.setter
    def fields(self, value):
        if value is None:
            self.__fields = []
        elif isinstance(value, dict):
            self.__fields = [(str(k), v) for k, v in value.items()]
        else:
            pairs = []
            for item in value:
                try:
                    label, val = item
                except (TypeError, ValueError):
                    raise TypeError(
                        'fields must be a dict or (label, value) pairs')
                pairs.append((str(label), val))
            self.__fields = pairs

    @property
    def style_name(self):
        return self.__style_name

    @style_name.setter
    def style_name(self, value):
        composition, name = _style(value)
        self.__style_name = name
        self.__frame = _Frame(composition)

    @property
    def field_columns(self):
        return self.__field_columns

    @field_columns.setter
    def field_columns(self, value):
        if value == 'auto':
            self.__field_columns = 'auto'
            return
        value = int(value)
        if value < 1:
            raise ValueError('field_columns must be >= 1')
        self.__field_columns = value

    @property
    def title_position(self):
        return self.__title_position

    @title_position.setter
    def title_position(self, value):
        value = 'auto' if value is None else str(value).lower()
        if value not in ('auto', 'border', 'inside'):
            raise ValueError(
                "title_position must be 'auto', 'border' or 'inside'")
        self.__title_position = value

    def add_field(self, label, value):
        """Append one ``label: value`` pair; returns ``self``."""
        self.__fields.append((str(label), value))
        return self

    def apply_theme(self, name):
        """
        Take a table theme's style and colours.

        The theme's header colour becomes the title colour and its zebra
        stripes alternate the field rows. Returns ``self``.
        """
        settings = _theme_settings(name)
        self.style_name = settings.get('style_name', self.style_name)
        if settings.get('use_colors') is False:
            self.use_colors = False
            self.title_color = None
            self.subtitle_color = None
            self.label_color = None
            self.footer_color = None
        header = settings.get('header_color')
        if header:
            self.title_color = header
        self.border_color = settings.get('border_color')
        self.zebra = settings.get('zebra')
        return self

    # -- measurement -------------------------------------------------------

    def _padding(self):
        frame = self.__frame
        if self.padding is not None:
            return max(0, int(self.padding))
        if frame.left_w or frame.right_w:
            return max(1, frame.margin)
        return frame.margin

    def _chrome(self):
        """Columns used by frame, padding, panel and shadow."""
        frame = self.__frame
        return (frame.left_w + frame.right_w + 2 * self._padding() +
                _panel_overhead(self.panel, self.shadow))

    def _label_width(self):
        return max((visible_width(strip_ansi(l)) for l, _ in self.__fields),
                   default=0)

    def _value_text(self, value):
        if value is None:
            return ''
        return str(value)

    def natural_width(self):
        """Width the card takes when nothing constrains it."""
        if self.width is not None:
            return int(self.width)
        frame = self.__frame
        inner = 0
        if self.title:
            extra = 4 if self._title_in_border() else 0
            inner = max(inner, visible_width(self.title) + extra -
                        2 * self._padding() * (1 if extra else 0))
        for text in (self.subtitle, self.footer):
            if text:
                inner = max(inner, max(visible_width(line)
                                       for line in text.split('\n')))
        if self.actions:
            inner = max(inner, visible_width(self._actions_text()))
        if self.__fields:
            label_w = self._label_width()
            cols = self.field_columns
            if cols == 'auto':
                cols = len(self.__fields)
            gap = int(self.field_gap)
            if cols == 1 and self._layout_for(cols) == 'inline':
                value_w = max(_block_width(self._value_text(v))
                              for _, v in self.__fields)
                inner = max(inner, label_w + gap + value_w)
            else:
                tile = max(max(visible_width(l), _block_width(
                    self._value_text(v))) for l, v in self.__fields)
                inner = max(inner, cols * tile + (cols - 1) * gap)
        if self.body is not None:
            inner = max(inner, _natural_width(self.body))
        width = inner + self._chrome()
        if self.max_width is not None:
            width = min(width, int(self.max_width))
        if self.min_width is not None:
            width = max(width, int(self.min_width))
        del frame
        return max(width, self._chrome() + 2)

    def _title_in_border(self):
        if not self.title:
            return False
        if self.title_position == 'inside':
            return False
        return self.__frame.title_top is not None

    def _layout_for(self, cols):
        layout = (self.field_layout or 'auto').lower()
        if layout not in ('auto', 'inline', 'stacked'):
            raise ValueError(
                "field_layout must be 'auto', 'inline' or 'stacked'")
        if layout != 'auto':
            return layout
        return 'inline' if cols == 1 else 'stacked'

    def _actions_text(self):
        return ' '.join('[ {0} ]'.format(a) for a in self.actions)

    # -- rendering ---------------------------------------------------------

    def __str__(self):
        return self.render()

    def render(self, width=None, height=None):
        """
        Draw the card.

        ``width`` is the total width including frame, panel and shadow;
        ``None`` uses the card's own ``width`` or its natural width capped at
        the terminal width. ``height`` stretches the card (blank lines before
        the footer) so cards in one grid row line up.
        """
        frame = self.__frame
        if width is None:
            width = self.width
        if width is None:
            width = min(self.natural_width(), render_width(None))
        width = int(width)
        if height is None:
            height = self.height
        painter = _Painter(supports_color() if self.use_colors is None
                           else bool(self.use_colors))
        pad = self._padding()
        overhead = _panel_overhead(self.panel, self.shadow)
        inner = width - overhead - frame.left_w - frame.right_w
        content_w = inner - 2 * pad
        if content_w < 2:
            # Too narrow for a frame: shed padding first, then refuse.
            pad = max(0, (inner - 2) // 2)
            content_w = inner - 2 * pad
            if content_w < 1:
                raise ValueError(
                    'width {0} is too narrow for this card (needs at least '
                    '{1})'.format(width, width - content_w + 1))

        border = painter.prefix(self.border_color)
        fill = painter.prefix(self.color)
        sections = []   # list of (kind, [interior lines])

        title_in_border = self._title_in_border()
        head = []
        if self.title and not title_in_border:
            for line in wrap_to_width(self.title, content_w):
                head.append(self._content(painter, line, self.title_color,
                                          content_w, pad, fill,
                                          _align(self.title_align)))
        if self.subtitle:
            for raw in self.subtitle.split('\n'):
                for line in wrap_to_width(raw, content_w):
                    head.append(self._content(painter, line,
                                              self.subtitle_color,
                                              content_w, pad, fill,
                                              _align(self.title_align)))
        if head:
            sections.append(('head', head))

        body = self._field_lines(painter, content_w, pad, fill)
        if self.body is not None:
            rendered = _render_child(self.body, content_w)
            for line in rendered.split('\n'):
                body.append(self._content(painter, line, None, content_w,
                                          pad, fill, 'l', rows=False))
        if body:
            sections.append(('body', body))

        foot = []
        if self.footer:
            for raw in self.footer.split('\n'):
                for line in wrap_to_width(raw, content_w):
                    foot.append(self._content(painter, line,
                                              self.footer_color, content_w,
                                              pad, fill, _align(self.align)))
        if self.actions:
            for line in wrap_to_width(self._actions_text(), content_w):
                foot.append(self._content(painter, line, 'bold', content_w,
                                          pad, fill, 'r'))
        if foot:
            sections.append(('foot', foot))

        if not sections:
            sections.append(('body', [self._content(
                painter, '', None, content_w, pad, fill, 'l')]))

        lines = self._assemble(painter, sections, inner, border,
                               title_in_border, height, overhead,
                               content_w, pad, fill)
        out = '\n'.join(lines)
        if self.panel:
            out = wrap_panel(out, self.panel,
                             self.panel_color if painter.active else None)
        if self.shadow:
            out = add_shadow(out, self.shadow,
                             self.shadow_color if painter.active else None)
        return out

    def _content(self, painter, text, spec, content_w, pad, fill, align,
                 rows=True, row_fill=None):
        """One interior line (without side borders): padding + content."""
        line_fill = row_fill if row_fill is not None else fill
        text = _fit_line(text, content_w, align)
        # Pad outside the coloured text so a coloured value does not paint
        # its alignment spaces; the line fill covers everything.
        stripped = text.strip(' ')
        if stripped and spec:
            lead = len(text) - len(text.lstrip(' '))
            trail = len(text) - len(text.rstrip(' '))
            core = text[lead:len(text) - trail] if trail else text[lead:]
            text = (' ' * lead + painter.segment(core, spec, line_fill) +
                    ' ' * trail)
        elif line_fill and RESET in text:
            text = text.replace(RESET, RESET + line_fill)
        if not painter.active:
            text = strip_ansi(text)
        line = ' ' * pad + text + ' ' * pad
        return painter.fill_line(line, line_fill) if painter.active else line

    def _field_lines(self, painter, content_w, pad, fill):
        fields = self.__fields
        if not fields:
            return []
        gap = max(0, int(self.field_gap))
        cols = self.field_columns
        if cols == 'auto':
            # As many tiles per row as fit at their natural width.
            tile = max(max(visible_width(l), _block_width(
                self._value_text(v))) for l, v in fields)
            cols = max(1, (content_w + gap) // (tile + gap))
        cols = min(cols, len(fields))
        layout = self._layout_for(cols)
        label_w = self._label_width()
        even, odd = _zebra_specs(self.zebra)
        values = self.value_colors or {}
        rules = self.field_rules
        if rules is None:
            rules = self.__frame.row_rule is not None
        out = []

        def value_spec(label):
            return values.get(label, self.value_color)

        def row_fill(index):
            spec = odd if index % 2 else even
            prefix = painter.prefix(spec)
            return (fill + prefix) if prefix else fill

        if cols == 1:
            inline_label = min(label_w, max(1, content_w // 2))
            value_w = content_w - inline_label - gap
            use_inline = layout == 'inline' and value_w >= 4
            for index, (label, value) in enumerate(fields):
                rfill = row_fill(index)
                text = self._value_text(value)
                if rules and index:
                    out.append(('rule', None))
                if use_inline:
                    label_lines = wrap_to_width(label, inline_label)
                    value_lines = []
                    for raw in text.split('\n'):
                        value_lines.extend(wrap_to_width(raw, value_w))
                    for k in range(max(len(label_lines), len(value_lines))):
                        lab = label_lines[k] if k < len(label_lines) else ''
                        val = value_lines[k] if k < len(value_lines) else ''
                        out.append(self._pair(
                            painter, lab, val, inline_label, value_w, gap,
                            label, content_w, pad, rfill, value_spec(label)))
                else:
                    for line in wrap_to_width(label, content_w):
                        out.append(self._content(
                            painter, line, self.label_color, content_w, pad,
                            fill, _align(self.label_align), row_fill=rfill))
                    for raw in text.split('\n'):
                        for line in wrap_to_width(raw, content_w):
                            out.append(self._content(
                                painter, line, value_spec(label), content_w,
                                pad, fill, _align(self.align),
                                row_fill=rfill))
            return out

        # Grid of tiles: label above value, ``cols`` per row.
        tile_w = (content_w - gap * (cols - 1)) // cols
        if tile_w < 2:
            cols, tile_w = 1, content_w
        spare = content_w - (tile_w * cols + gap * (cols - 1))
        for row_i, start in enumerate(range(0, len(fields), cols)):
            chunk = fields[start:start + cols]
            rfill = row_fill(row_i)
            if rules and row_i:
                out.append(('rule', None))
            tiles = []
            for label, value in chunk:
                if layout == 'inline':
                    lw = min(visible_width(label), tile_w // 2)
                    vw = max(1, tile_w - lw - 1)
                    lines = []
                    for raw in self._value_text(value).split('\n'):
                        lines.extend(wrap_to_width(raw, vw))
                    labels = wrap_to_width(label, lw) if lw else []
                    tile = []
                    for k in range(max(len(lines), len(labels))):
                        lab = labels[k] if k < len(labels) else ''
                        val = lines[k] if k < len(lines) else ''
                        tile.append([(lab, lw, self.label_color, 'l'),
                                     (' ', 1, None, 'l'),
                                     (val, vw, value_spec(label),
                                      _align(self.align))])
                else:
                    tile = [[(line, tile_w, self.label_color,
                              _align(self.label_align))]
                            for line in wrap_to_width(label, tile_w)]
                    for raw in self._value_text(value).split('\n'):
                        for line in wrap_to_width(raw, tile_w):
                            tile.append([(line, tile_w, value_spec(label),
                                          _align(self.align))])
                tiles.append(tile)
            depth = max(len(t) for t in tiles)
            for k in range(depth):
                parts = []
                for t_i in range(cols):
                    if t_i:
                        parts.append(' ' * gap)
                    if t_i < len(tiles) and k < len(tiles[t_i]):
                        for text, w, spec, al in tiles[t_i][k]:
                            cell = _fit_line(text, w, al)
                            parts.append(self._colour_cell(
                                painter, cell, spec, rfill))
                    else:
                        parts.append(' ' * tile_w)
                parts.append(' ' * spare)
                line = ' ' * pad + ''.join(parts) + ' ' * pad
                out.append(painter.fill_line(line, rfill)
                           if painter.active else strip_ansi(line))
        return out

    def _colour_cell(self, painter, cell, spec, fill):
        if not painter.active:
            return strip_ansi(cell)
        if not spec or not cell.strip(' '):
            return cell.replace(RESET, RESET + fill) if fill else cell
        lead = len(cell) - len(cell.lstrip(' '))
        trail = len(cell) - len(cell.rstrip(' '))
        core = cell[lead:len(cell) - trail] if trail else cell[lead:]
        return ' ' * lead + painter.segment(core, spec, fill) + ' ' * trail

    def _pair(self, painter, label, value, label_w, value_w, gap, key,
              content_w, pad, fill, spec):
        lab = self._colour_cell(painter, _fit_line(label, label_w,
                                                   _align(self.label_align)),
                                self.label_color, fill)
        val = self._colour_cell(painter, _fit_line(value, value_w,
                                                   _align(self.align)),
                                spec, fill)
        line = ' ' * pad + lab + ' ' * gap + val + ' ' * pad
        return painter.fill_line(line, fill) if painter.active else line

    def _assemble(self, painter, sections, inner, border, title_in_border,
                  height, overhead, content_w, pad, fill):
        frame = self.__frame

        def paint(text):
            return _paint(text, border) if text else text

        def wrap_sides(interior, head=False):
            left, right = frame.sides(head)
            return paint(left) + interior + paint(right)

        lines = []
        top_sep = frame.title_top if (sections[0][0] == 'head' or
                                      title_in_border) else frame.top
        top = frame.line(top_sep, inner)
        if top is not None:
            drawn = paint(top)
            if title_in_border:
                label = self.title
                room = inner - 4
                if visible_width(label) > room:
                    label = truncate_to_width(label, max(1, room), '…')
                set_in = inset_label(
                    drawn, label, self.title_align, glyph=top_sep.middle,
                    label_prefix=painter.prefix(self.title_color),
                    border_prefix=border)
                if set_in is None:
                    # Not even a short label fits: draw it as a first line.
                    sections.insert(0, ('head', [self._content(
                        painter, self.title, self.title_color, content_w,
                        pad, fill, _align(self.title_align))]))
                else:
                    drawn = set_in
            lines.append(drawn)

        if height is not None:
            used = sum(len(s[1]) for s in sections) + (1 if top else 0)
            used += sum(1 for i in range(1, len(sections))
                        if ((frame.divider or frame.row_rule)
                            if sections[i - 1][0] == 'head'
                            else frame.foot_divider))
            used -= sum(1 for _, interior in sections for item in interior
                        if isinstance(item, tuple) and not frame.row_rule)
            used += 1 if frame.bottom else 0
            used += overhead and ((2 if self.panel else 0) +
                                  (1 if self.shadow else 0))
            extra = int(height) - used
            if extra > 0:
                blank = self._content(painter, '', None, content_w, pad,
                                      fill, 'l')
                target = None
                for i, (kind, _) in enumerate(sections):
                    if kind == 'body':
                        target = i
                if target is None:
                    target = 0 if sections[0][0] != 'head' or \
                        len(sections) == 1 else len(sections) - 1
                    if sections[target][0] == 'foot' and target > 0:
                        target -= 1
                sections[target][1].extend([blank] * extra)

        for s_i, (kind, interior) in enumerate(sections):
            if s_i:
                if sections[s_i - 1][0] == 'head':
                    sep = frame.divider or frame.row_rule
                else:
                    sep = frame.foot_divider
                if sep is not None:
                    lines.append(paint(frame.line(sep, inner)))
            for item in interior:
                if isinstance(item, tuple):
                    sep = frame.row_rule
                    if sep is not None:
                        lines.append(paint(frame.line(sep, inner)))
                    continue
                lines.append(wrap_sides(item, head=(kind == 'head')))
        bottom = frame.line(frame.bottom, inner)
        if bottom is not None:
            lines.append(paint(bottom))
        return lines


# +---------------------------------------------------------------------------+
# Grid

_VALIGNS = {'t': 't', 'top': 't', 'm': 'm', 'middle': 'm', 'center': 'm',
            'centre': 'm', 'c': 'm', 'b': 'b', 'bottom': 'b'}


def _valign(value, default='t'):
    if value is None:
        return default
    try:
        return _VALIGNS[str(value).lower()]
    except KeyError:
        raise ValueError(
            "valign must be 'top', 'middle' or 'bottom', got {0!r}".format(
                value))


# Glyphs for collapsed grid borders, indexed by which of (up, down, left,
# right) meet at a point.
_BORDER_SETS = {
    'single':  dict(h='─', v='│', tl='┌', tr='┐', bl='└', br='┘', lt='├',
                    rt='┤', tt='┬', bt='┴', x='┼'),
    'rounded': dict(h='─', v='│', tl='╭', tr='╮', bl='╰', br='╯', lt='├',
                    rt='┤', tt='┬', bt='┴', x='┼'),
    'double':  dict(h='═', v='║', tl='╔', tr='╗', bl='╚', br='╝', lt='╠',
                    rt='╣', tt='╦', bt='╩', x='╬'),
    'heavy':   dict(h='━', v='┃', tl='┏', tr='┓', bl='┗', br='┛', lt='┣',
                    rt='┫', tt='┳', bt='┻', x='╋'),
    'ascii':   dict(h='-', v='|', tl='+', tr='+', bl='+', br='+', lt='+',
                    rt='+', tt='+', bt='+', x='+'),
}
_BORDER_ALIASES = {'true': 'single', '1': 'single', 'sharp': 'single',
                   'bold': 'heavy', 'thick': 'heavy'}


def _border_set(border):
    if border is None or border is False:
        return None
    if border is True:
        return _BORDER_SETS['single']
    name = str(border).lower()
    name = _BORDER_ALIASES.get(name, name)
    try:
        return _BORDER_SETS[name]
    except KeyError:
        raise ValueError('border must be one of {0}, got {1!r}'.format(
            ', '.join(sorted(_BORDER_SETS)), border))


def _junction(glyphs, up, down, left, right):
    """The glyph where the given border arms meet."""
    key = (up, down, left, right)
    table = {
        (1, 1, 1, 1): 'x', (0, 1, 1, 1): 'tt', (1, 0, 1, 1): 'bt',
        (1, 1, 0, 1): 'lt', (1, 1, 1, 0): 'rt', (0, 1, 0, 1): 'tl',
        (0, 1, 1, 0): 'tr', (1, 0, 0, 1): 'bl', (1, 0, 1, 0): 'br',
        (1, 1, 0, 0): 'v', (0, 0, 1, 1): 'h', (1, 0, 0, 0): 'v',
        (0, 1, 0, 0): 'v', (0, 0, 1, 0): 'h', (0, 0, 0, 1): 'h',
    }
    name = table.get(tuple(int(bool(k)) for k in key))
    return glyphs[name] if name else ' '


_TRACK_RE = re.compile(r'^\s*(\d+(?:\.\d+)?)\s*(fr|%|\*)?\s*$')


class _Track(object):
    """One column (or row) size: fixed, fraction, percentage or auto."""

    def __init__(self, spec):
        low = high = None
        if isinstance(spec, (tuple, list)):
            if len(spec) != 3:
                raise ValueError(
                    'a track bound is (size, min, max), got {0!r}'.format(
                        spec))
            spec, low, high = spec
        self.low = None if low is None else max(0, int(low))
        self.high = None if high is None else max(1, int(high))
        if self.low is not None and self.high is not None and \
                self.low > self.high:
            raise ValueError('track min {0} is above its max {1}'.format(
                self.low, self.high))
        self.kind, self.value = self._parse(spec)

    @staticmethod
    def _parse(spec):
        if spec is None or (isinstance(spec, str) and
                            spec.strip().lower() == 'auto'):
            return 'auto', 0
        if isinstance(spec, bool):
            raise ValueError('a track size cannot be a bool')
        if isinstance(spec, int):
            if spec < 1:
                raise ValueError('a fixed track must be >= 1, got {0}'.format(
                    spec))
            return 'fixed', spec
        if isinstance(spec, float):
            if spec <= 0:
                raise ValueError('a fraction must be > 0, got {0}'.format(
                    spec))
            return 'fr', spec
        match = _TRACK_RE.match(str(spec).lower())
        if not match:
            raise ValueError(
                "track size must be an int, 'auto', 'Nfr', 'N%' or a float, "
                'got {0!r}'.format(spec))
        number, unit = float(match.group(1)), match.group(2)
        if unit in ('fr', '*'):
            if number <= 0:
                raise ValueError('a fraction must be > 0')
            return 'fr', number
        if unit == '%':
            return 'pct', number
        if number < 1 or number != int(number):
            raise ValueError('a fixed track must be a whole number >= 1')
        return 'fixed', int(number)

    def clamp(self, size):
        if self.low is not None:
            size = max(size, self.low)
        if self.high is not None:
            size = min(size, self.high)
        return size

    @property
    def minimum(self):
        if self.kind == 'fixed':
            return self.clamp(self.value)
        return self.low if self.low is not None else 1


def _distribute(total, weights):
    """Split ``total`` integer units by ``weights`` (largest remainder)."""
    if total <= 0 or not weights:
        return [0] * len(weights)
    whole = float(sum(weights))
    exact = [total * w / whole for w in weights]
    sizes = [int(e) for e in exact]
    order = sorted(range(len(weights)), key=lambda i: exact[i] - sizes[i],
                   reverse=True)
    for i in order[:total - sum(sizes)]:
        sizes[i] += 1
    return sizes


def solve_tracks(tracks, available, natural=None):
    """
    Sizes for ``tracks`` sharing ``available`` columns (or lines).

    Fixed and percentage tracks take their size, ``auto`` tracks their
    ``natural`` size, then fraction tracks share what is left by weight. Every
    track honours its ``(size, min, max)`` bounds. Returns the sizes, or
    ``None`` when even the minimums do not fit.
    """
    natural = natural or [0] * len(tracks)
    if sum(t.minimum for t in tracks) > available:
        return None
    sizes = [0] * len(tracks)
    for i, t in enumerate(tracks):
        if t.kind == 'fixed':
            sizes[i] = t.clamp(t.value)
        elif t.kind == 'pct':
            sizes[i] = t.clamp(max(1, int(available * t.value / 100.0)))
        elif t.kind == 'auto':
            sizes[i] = t.clamp(max(1, natural[i]))
    flexible = [i for i, t in enumerate(tracks) if t.kind == 'fr']
    # Auto and percentage tracks give way first when they overflow.
    over = sum(sizes) + sum(tracks[i].minimum for i in flexible) - available
    if over > 0:
        shrinkable = [i for i, t in enumerate(tracks)
                      if t.kind in ('auto', 'pct')]
        while over > 0 and shrinkable:
            room = [sizes[i] - tracks[i].minimum for i in shrinkable]
            if sum(room) <= 0:
                break
            cut = _distribute(min(over, sum(room)), room)
            for i, c in zip(shrinkable, cut):
                sizes[i] -= c
            over -= sum(cut)
    if not flexible:
        return sizes if sum(sizes) <= available else None
    fixed = set(range(len(tracks))) - set(flexible)
    pinned = {}
    while True:
        free = [i for i in flexible if i not in pinned]
        left = available - sum(sizes[i] for i in fixed) - sum(pinned.values())
        shares = _distribute(max(0, left), [tracks[i].value for i in free])
        clash = False
        for i, share in zip(free, shares):
            bounded = tracks[i].clamp(max(1, share))
            if bounded != share:
                pinned[i] = bounded
                clash = True
                break
        if not clash:
            for i, share in zip(free, shares):
                sizes[i] = share
            break
        if len(pinned) == len(flexible):
            break
    for i, size in pinned.items():
        sizes[i] = size
    if sum(sizes) > available:
        return None
    return sizes


def _track_sets(value, name, allow_empty=False):
    """
    ``[(min_width, [tracks])]`` from a list of sizes or a responsive dict
    ``{min_width: [sizes]}``, sorted by ``min_width``.
    """
    if value is None:
        return []
    if isinstance(value, dict):
        items = []
        for key, sizes in value.items():
            key = int(key)
            if key < 0:
                raise ValueError('{0} breakpoints must be >= 0'.format(name))
            if isinstance(sizes, dict):
                raise TypeError('{0} breakpoints cannot nest'.format(name))
            items.append((key, _track_sets(sizes, name, allow_empty)[0][1]))
        if not items:
            raise ValueError('{0} needs at least one layout'.format(name))
        return sorted(items, key=lambda kv: kv[0])
    if isinstance(value, (str, int, float)):
        raise TypeError('{0} must be a list of sizes or a dict of '
                        'lists'.format(name))
    sizes = list(value)
    if not sizes and not allow_empty:
        raise ValueError('{0} needs at least one size'.format(name))
    return [(0, [_Track(spec) for spec in sizes])]


def _pick(track_sets, width):
    """The tracks for the widest breakpoint ``width`` reaches, or None."""
    chosen = None
    for minimum, tracks in track_sets:
        if width >= minimum:
            chosen = tracks
    return chosen


def _accepts_height(child):
    render = getattr(child, 'render', None)
    if not callable(render):
        return False
    try:
        params = inspect.signature(render).parameters
    except (TypeError, ValueError):  # pragma: no cover - C callables
        return False
    return 'height' in params or any(
        p.kind == p.VAR_KEYWORD for p in params.values())


class GridCell(object):
    """
    A grid child with placement options.

    ``span`` columns and ``row_span`` rows; ``align`` / ``valign`` place the
    child inside its slot when it is narrower or shorter; ``title`` is set
    into the cell's top border when the grid draws borders; ``color`` paints
    the cell's background; ``stretch=True`` renders the child at the slot's
    full height (cards always stretch in an ``equal_height`` grid);
    ``hide_below`` hides the cell when the grid is narrower than that.
    """

    def __init__(self, child, span=1, align='l', row_span=1, valign=None,
                 title=None, title_align='l', color=None, stretch=None,
                 padding=None, hide_below=None):
        self.child = child
        self.span = max(1, int(span))
        self.row_span = max(1, int(row_span))
        self.align = _align(align)
        self.valign = None if valign is None else _valign(valign)
        self.title = None if title is None else str(title)
        self.title_align = _align(title_align)
        self.color = color
        self.stretch = stretch
        self.padding = None if padding is None else max(0, int(padding))
        self.hide_below = None if hide_below is None else int(hide_below)


class Grid(object):
    """
    Lay renderables out in columns that reflow with the width.

    >>> grid = Grid([card_a, card_b, card_c], columns='auto', min_width=24)
    >>> print(grid.render(width=80))   # 3 columns
    >>> print(grid.render(width=50))   # 2 columns
    >>> print(grid.render(width=30))   # 1 column

    Parameters
    ----------
    children : list
        Cards, tables, strings, grids, widgets, or ``GridCell(child, span=n,
        row_span=m)`` / ``(child, span)``.
    columns : 'auto' or int
        ``'auto'`` fits as many columns of ``min_width`` as the width allows.
        An int is the most columns to use; with ``min_width`` the grid still
        drops to fewer when they would be narrower than that.
    column_widths : list, optional
        One size per column: an int (fixed), ``'auto'`` (widest child),
        ``'2fr'`` / ``2.0`` (a share of what is left), ``'30%'``, or
        ``(size, min, max)``. Sets the number of columns. Default: equal
        columns.
    row_heights : list, optional
        One size per row (``int``, ``'auto'``, ``'Nfr'``); fraction rows
        share the lines left when the grid is given a ``height``.
    gap, row_gap : int
        Spaces between columns, blank lines between rows (ignored between
        cells when ``border`` is set: the border separates them).
    min_width : int, optional
        Narrowest a column may be. Default for ``'auto'``: the widest
        child's natural width.
    width, height : int, optional
        Fixed total size (default width: the terminal; default height: as
        tall as the content).
    equal_height : bool
        Stretch cards in one row to the same height.
    border : str or bool, optional
        Draw one shared frame around and between the cells -- ``'single'``,
        ``'rounded'``, ``'double'``, ``'heavy'``, ``'ascii'`` or ``True`` --
        with proper junctions (``┬ ┼ ┴``) wherever cells meet.
    padding : int, optional
        Spaces inside each bordered cell (default 1 with a border, else 0).
    collapse_below : int, optional
        Below this width stack every child in one column.
    valign : str
        ``'top'`` (default), ``'middle'`` or ``'bottom'`` for children
        shorter than their row.
    """

    def __init__(self, children=None, columns='auto', gap=2, row_gap=1,
                 min_width=None, max_width=None, width=None,
                 equal_height=True, align='l', column_widths=None,
                 row_heights=None, height=None, border=None,
                 border_color=None, title_color='bold', padding=None,
                 collapse_below=None, valign='top', use_colors=None):
        self.children = []
        for child in children or []:
            self.add(child)
        self.columns = columns
        self.gap = max(0, int(gap))
        self.row_gap = max(0, int(row_gap))
        self.min_width = min_width
        self.max_width = max_width
        self.width = width
        self.height = height
        self.equal_height = bool(equal_height)
        self.align = _align(align)
        self.column_widths = column_widths
        self.row_heights = row_heights
        self.border = border
        self.border_color = border_color
        self.title_color = title_color
        self.padding = padding
        self.collapse_below = collapse_below
        self.valign = _valign(valign)
        self.use_colors = use_colors

    @property
    def columns(self):
        return self.__columns

    @columns.setter
    def columns(self, value):
        if value is None or value == 'auto':
            self.__columns = 'auto'
            return
        value = int(value)
        if value < 1:
            raise ValueError("columns must be 'auto' or >= 1")
        self.__columns = value

    @property
    def column_widths(self):
        return self.__column_widths

    @column_widths.setter
    def column_widths(self, value):
        self.__track_sets = _track_sets(value, 'column_widths')
        self.__column_widths = value

    @property
    def row_heights(self):
        return self.__row_heights

    @row_heights.setter
    def row_heights(self, value):
        self.__row_sets = _track_sets(value, 'row_heights', allow_empty=True)
        self.__row_heights = value

    @property
    def border(self):
        return self.__border

    @border.setter
    def border(self, value):
        self.__glyphs = _border_set(value)
        self.__border = value

    def add(self, child, span=1, **options):
        """
        Append a child; returns ``self``.

        ``options`` are :class:`GridCell` options (``row_span``, ``title``,
        ``valign``, ``color``...).
        """
        if isinstance(child, GridCell):
            self.children.append(child)
        elif isinstance(child, tuple) and len(child) == 2 and \
                isinstance(child[1], int):
            self.children.append(GridCell(child[0], child[1], **options))
        else:
            self.children.append(GridCell(child, span, **options))
        return self

    # -- measurement -------------------------------------------------------

    def _bordered(self):
        return self.__glyphs is not None

    def _cell_padding(self, cell):
        if cell.padding is not None:
            return cell.padding
        if self.padding is not None:
            return max(0, int(self.padding))
        return 1 if self._bordered() else 0

    def _separator(self):
        """Columns between two tracks."""
        return 1 if self._bordered() else self.gap

    def _frame_columns(self, n):
        return (n + 1) if self._bordered() else self.gap * (n - 1)

    def natural_width(self):
        if self.width is not None:
            return int(self.width)
        if self.__track_sets:
            tracks = self.__track_sets[-1][1]
            n = len(tracks)
            natural = self._natural_tracks(n, None)
            total = 0
            for t, nat in zip(tracks, natural):
                if t.kind == 'fixed':
                    total += t.clamp(t.value)
                else:
                    total += t.clamp(max(1, nat))
            total += self._frame_columns(n)
        else:
            widths = [_natural_width(c.child) + 2 * self._cell_padding(c)
                      for c in self.children] or [0]
            if self.columns == 'auto':
                n = len(self.children) or 1
            else:
                n = min(self.columns, max(1, len(self.children)))
            col = max(widths)
            if self.min_width is not None:
                col = max(col, int(self.min_width))
            total = n * col + self._frame_columns(n)
        if self.max_width is not None:
            total = min(total, int(self.max_width))
        return total

    def _resolve_width(self, width):
        width = render_width(width if width is not None else self.width)
        if self.max_width is not None:
            width = min(width, int(self.max_width))
        return width

    def _natural_tracks(self, n, placed, children=None):
        """Natural width of each column from its single-column children."""
        natural = [0] * n
        if placed is None:
            placed = self._place(n, children)
        for cell, _, c, _, cs in placed:
            if cs == 1:
                natural[c] = max(natural[c], _natural_width(cell.child) +
                                 2 * self._cell_padding(cell))
        return natural

    def visible_children(self, width=None):
        """The children shown at ``width`` (``hide_below`` applied)."""
        width = self._resolve_width(width)
        return [c for c in self.children
                if c.hide_below is None or width >= c.hide_below]

    def _layout(self, width, children=None):
        """``(columns, track widths, stacked)`` for ``width``."""
        stacked = (self.collapse_below is not None and
                   width < int(self.collapse_below))
        if not stacked and self.__track_sets:
            tracks = _pick(self.__track_sets, width)
            if tracks is not None:
                n = len(tracks)
                avail = width - self._frame_columns(n)
                if avail >= n:
                    sizes = solve_tracks(tracks, avail, self._natural_tracks(
                        n, None, children))
                    if sizes is not None:
                        return n, sizes, False
            stacked = True
        if stacked:
            return 1, [max(1, width - self._frame_columns(1))], True
        n = self.column_count(width)
        avail = width - self._frame_columns(n)
        if self._bordered() and avail >= n:
            # A frame should reach the full width: hand out the remainder.
            return n, _distribute(avail, [1] * n), False
        col_w = max(1, avail // n)
        return n, [col_w] * n, False

    def column_count(self, width=None):
        """How many columns the grid uses at ``width``."""
        width = self._resolve_width(width)
        if self.collapse_below is not None and \
                width < int(self.collapse_below):
            return 1
        children = self.visible_children(width)
        if self.__track_sets:
            return self._layout(width, children)[0]
        spans = sum(c.span for c in children) or 1
        if self.min_width is not None:
            min_w = int(self.min_width)
        else:
            min_w = max([min(_natural_width(c.child) +
                             2 * self._cell_padding(c), width)
                         for c in children if c.span == 1] or [1])
        min_w = max(1, min_w)
        sep = self._separator()
        room = width - (2 if self._bordered() else 0) + (
            0 if self._bordered() else sep)
        fit = max(1, (room + (sep if self._bordered() else 0)) //
                  (min_w + sep))
        if self.columns == 'auto':
            return max(1, min(fit, spans))
        if self.min_width is not None:
            return max(1, min(self.columns, fit))
        return self.columns

    def _place(self, n, children=None):
        """
        Auto-place the children on an ``n``-column grid.

        Returns ``(cell, row, column, row_span, column_span)`` tuples. The
        cursor only moves forward (CSS "sparse" placement), skipping slots a
        row-spanning cell above already holds.
        """
        taken = set()
        placed = []
        row, col = 0, 0
        for cell in (self.children if children is None else children):
            span = min(cell.span, n)
            rows = cell.row_span
            while True:
                if col + span > n:
                    row, col = row + 1, 0
                    continue
                if any((row + dr, col + dc) in taken
                       for dr in range(rows) for dc in range(span)):
                    col += 1
                    continue
                break
            for dr in range(rows):
                for dc in range(span):
                    taken.add((row + dr, col + dc))
            placed.append((cell, row, col, rows, span))
            col += span
        return placed

    # -- rendering -----------------------------------------------------------

    def __str__(self):
        return self.render()

    def render(self, width=None, height=None):
        """
        Draw the grid into ``width`` columns (default: terminal width).

        ``height`` (or the grid's own ``height``) makes the grid exactly that
        many lines: fraction rows (``row_heights``) take the spare lines,
        otherwise the last row does. When the content is taller, rows give
        up lines from the bottom up (fraction rows first) so a bordered grid
        keeps its frame closed.
        """
        width = self._resolve_width(width)
        if height is None:
            height = self.height
        children = self.visible_children(width)
        if not children:
            if height:
                return '\n'.join([''] * int(height))
            return ''
        n, tracks, stacked = self._layout(width, children)
        if stacked:
            placed = [(cell, i, 0, 1, 1)
                      for i, cell in enumerate(children)]
        else:
            placed = self._place(n, children)
        bordered = self._bordered()
        sep = self._separator()
        painter = _Painter(supports_color() if self.use_colors is None
                           else bool(self.use_colors))

        def span_width(c, cs):
            return sum(tracks[c:c + cs]) + sep * (cs - 1)

        # Natural render of every child at its slot width.
        blocks = []
        for cell, r, c, rs, cs in placed:
            pad = self._cell_padding(cell)
            inner = max(1, span_width(c, cs) - 2 * pad)
            text = _render_child(cell.child, inner)
            blocks.append([cell, r, c, rs, cs, inner, text])

        n_rows = max(r + rs for _, r, _, rs, _, _, _ in blocks)
        row_sep = 1 if bordered else self.row_gap
        heights = [0] * n_rows
        for cell, r, c, rs, cs, inner, text in blocks:
            if rs == 1:
                heights[r] = max(heights[r], text.count('\n') + 1)
        for cell, r, c, rs, cs, inner, text in blocks:
            if rs > 1:
                need = text.count('\n') + 1
                have = sum(heights[r:r + rs]) + row_sep * (rs - 1)
                if need > have:
                    heights[r + rs - 1] += need - have

        row_tracks = None if stacked else _pick(self.__row_sets, width)
        fractions = {}
        if row_tracks:
            for i in range(n_rows):
                if i >= len(row_tracks):
                    break
                t = row_tracks[i]
                if t.kind == 'fixed':
                    heights[i] = t.clamp(t.value)
                elif t.kind == 'fr':
                    fractions[i] = t.value
                    heights[i] = t.clamp(heights[i]) if t.low or t.high \
                        else heights[i]
                else:
                    heights[i] = t.clamp(heights[i])
        frame_lines = (n_rows + 1) if bordered else row_sep * (n_rows - 1)
        if height is not None:
            target = int(height) - frame_lines
            spare = target - sum(heights)
            if spare > 0:
                if not fractions:
                    fractions = {n_rows - 1: 1.0}
                # Fraction rows split everything the other rows leave, by
                # weight; a row whose content needs more keeps its content
                # height and the rest is split again.
                pool = target - sum(h for i, h in enumerate(heights)
                                    if i not in fractions)
                free = dict(fractions)
                while free:
                    rows_ = sorted(free)
                    shares = _distribute(pool, [free[i] for i in rows_])
                    short = [i for i, share in zip(rows_, shares)
                             if share < heights[i]]
                    if not short:
                        for i, share in zip(rows_, shares):
                            heights[i] = share
                        break
                    for i in short:
                        pool -= heights[i]
                        del free[i]
            elif spare < 0:
                # Too tall: fraction rows give up lines first, then the
                # others from the bottom up, each down to one line.
                order = sorted(fractions, reverse=True) + [
                    i for i in range(n_rows - 1, -1, -1)
                    if i not in fractions]
                for i in order:
                    cut = min(-spare, heights[i] - 1)
                    if cut > 0:
                        heights[i] -= cut
                        spare += cut
                    if spare >= 0:
                        break

        def slot_height(r, rs):
            return sum(heights[r:r + rs]) + row_sep * (rs - 1)

        sized = height is not None or bool(row_tracks)
        for b in blocks:
            cell, r, c, rs, cs, inner, text = b
            slot = slot_height(r, rs)
            lines = text.count('\n') + 1
            stretch = cell.stretch
            if stretch is None:
                # Cards line up in an equal-height row; other renderables
                # that take a height fill a sized grid's slot unless the cell
                # asks to be aligned inside it instead.
                stretch = (isinstance(cell.child, Card) and
                           self.equal_height) or (
                               sized and cell.valign is None and
                               not isinstance(cell.child, Card) and
                               _accepts_height(cell.child))
            if stretch and lines != slot and _accepts_height(cell.child):
                if isinstance(cell.child, Card) and lines > slot:
                    continue
                b[6] = cell.child.render(width=inner, height=slot)

        if bordered:
            out = self._draw_bordered(blocks, tracks, heights, painter)
        else:
            out = self._draw_open(blocks, tracks, heights, painter, sep)
        if height is not None:
            out = out[:int(height)]
            out.extend([''] * (int(height) - len(out)))
        return '\n'.join(out)

    def _slot_lines(self, cell, text, inner, slot, painter):
        """The child's lines aligned inside its slot, ``inner`` wide."""
        lines = text.split('\n')[:slot]
        free = slot - len(lines)
        valign = cell.valign or self.valign
        top = 0 if valign == 't' else (free if valign == 'b' else free // 2)
        blank = [''] * free
        lines = blank[:top] + lines + blank[top:]
        fill = painter.prefix(cell.color)
        out = []
        for line in lines:
            fitted = _fit_line(line, inner, cell.align)
            if fill:
                fitted = fill + fitted.replace(RESET, RESET + fill) + RESET
            out.append(fitted)
        return out

    def _draw_open(self, blocks, tracks, heights, painter, gap):
        n_rows = len(heights)
        row_top = []
        y = 0
        for i, h in enumerate(heights):
            row_top.append(y)
            y += h + (self.row_gap if i < n_rows - 1 else 0)
        # line -> {column: (x, text, width)}; a row-spanning cell keeps
        # feeding lines into the rows below it.
        canvas = [dict() for _ in range(y)]
        x_of = [0]
        for w in tracks:
            x_of.append(x_of[-1] + w + gap)
        for cell, r, c, rs, cs, inner, text in blocks:
            pad = self._cell_padding(cell)
            slot = sum(heights[r:r + rs]) + self.row_gap * (rs - 1)
            lines = self._slot_lines(cell, text, inner, slot, painter)
            for k, line in enumerate(lines):
                canvas[row_top[r] + k][c] = (
                    x_of[c], ' ' * pad + line + ' ' * pad,
                    sum(tracks[c:c + cs]) + gap * (cs - 1))
        out = []
        for entries in canvas:
            parts, x = [], 0
            for col in sorted(entries):
                start, text, w = entries[col]
                if start > x:
                    parts.append(' ' * (start - x))
                parts.append(text)
                x = start + w
            out.append(''.join(parts).rstrip(' '))
        return out

    def _title_position(self, segment, label, align):
        """Start column of `` label `` inside a plain border ``segment``."""
        need = visible_width(label) + 2
        runs = [(s, e) for s, e in _rule_runs(segment, self.__glyphs['h'])
                if e - s >= need + 2]
        if not runs:
            return None
        if align == 'l':
            return runs[0][0] + 1
        if align == 'r':
            return runs[-1][1] - 1 - need
        centre = len(segment) // 2
        best = None
        for s, e in runs:
            pos = min(max(centre - need // 2, s + 1), e - 1 - need)
            distance = abs(pos + need // 2 - centre)
            if best is None or distance < best[0]:
                best = (distance, pos)
        return best[1]

    def _draw_bordered(self, blocks, tracks, heights, painter):
        g = self.__glyphs
        xs = [0]
        for w in tracks:
            xs.append(xs[-1] + w + 1)
        ys = [0]
        for h in heights:
            ys.append(ys[-1] + h + 1)
        W, H = xs[-1] + 1, ys[-1] + 1
        horiz, vert = set(), set()     # unit edges starting at (x, y)
        for cell, r, c, rs, cs, inner, text in blocks:
            x0, x1, y0, y1 = xs[c], xs[c + cs], ys[r], ys[r + rs]
            for x in range(x0, x1):
                horiz.add((x, y0))
                horiz.add((x, y1))
            for y in range(y0, y1):
                vert.add((x0, y))
                vert.add((x1, y))
        grid = [[' '] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                left = (x - 1, y) in horiz
                right = (x, y) in horiz
                up = (x, y - 1) in vert
                down = (x, y) in vert
                if left or right or up or down:
                    grid[y][x] = _junction(g, up, down, left, right)
        # Titles go over each cell's own stretch of top border, never over a
        # junction, so the cells above still meet the ones below.
        titled = {}     # y -> list of [start, end)
        for cell, r, c, rs, cs, inner, text in blocks:
            if not cell.title:
                continue
            y, x0, x1 = ys[r], xs[c], xs[c + cs]
            segment = ''.join(grid[y][x0:x1 + 1])
            room = len(segment) - 6
            if room < 1:
                continue
            label = cell.title
            if visible_width(label) > room:
                label = truncate_to_width(label, room, '…')
            pos = self._title_position(segment, label, cell.title_align)
            if pos is None:
                continue
            x = x0 + pos
            start = x
            for cluster, w in measured_clusters(' ' + label + ' '):
                grid[y][x] = cluster
                for k in range(1, w):
                    grid[y][x + k] = ''
                x += w
            titled.setdefault(y, []).append((start + 1, x - 1))
        border = painter.prefix(self.border_color)
        title_prefix = painter.prefix(self.title_color)
        content = {}
        for cell, r, c, rs, cs, inner, text in blocks:
            pad = self._cell_padding(cell)
            slot_w = xs[c + cs] - xs[c] - 1
            slot_h = ys[r + rs] - ys[r] - 1
            inner_w = max(0, slot_w - 2 * pad)
            lines = self._slot_lines(cell, text, inner_w, slot_h, painter)
            fill = painter.prefix(cell.color)
            edge = _paint(' ' * pad, fill) if fill else ' ' * pad
            for k, line in enumerate(lines):
                content[(ys[r] + 1 + k, xs[c] + 1)] = (edge + line + edge,
                                                       slot_w)
        out = []
        for y in range(H):
            spans = titled.get(y, [])
            parts, x, run = [], 0, []

            def flush():
                if run:
                    parts.append(_paint(''.join(run), border))
                    del run[:]
            while x < W:
                if (y, x) in content:
                    flush()
                    text, w = content[(y, x)]
                    parts.append(text)
                    x += w
                    continue
                span = next((s for s in spans if s[0] == x), None)
                if span is not None:
                    flush()
                    parts.append(_paint(''.join(grid[y][span[0]:span[1]]),
                                        title_prefix))
                    x = span[1]
                    continue
                run.append(grid[y][x])
                x += 1
            flush()
            out.append(''.join(parts))
        return out
