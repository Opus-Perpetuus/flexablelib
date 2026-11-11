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
    all_runs = _rule_runs(plain, glyph)
    runs = [(s, e) for s, e in all_runs if e - s >= need + 2]
    if not runs:
        return None
    total = len(plain)
    # Left and right labels belong in the first / last stretch of rule; a
    # label that only fits further in is drawn outside the frame instead of
    # floating over some middle column.
    if align == 'l':
        if all_runs[0] != runs[0]:
            return None
        start, end = runs[0]
        pos = start + 1
    elif align == 'r':
        if all_runs[-1] != runs[-1]:
            return None
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
        cols = min(self.field_columns, len(fields))
        gap = max(0, int(self.field_gap))
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

class GridCell(object):
    """A grid child that spans ``span`` columns."""

    def __init__(self, child, span=1, align='l'):
        self.child = child
        self.span = max(1, int(span))
        self.align = _align(align)


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
        Cards, tables, strings, grids, or ``GridCell(child, span=n)`` /
        ``(child, span)`` for an item that spans ``n`` columns.
    columns : 'auto' or int
        ``'auto'`` fits as many columns of ``min_width`` as the width allows.
        An int is the most columns to use; with ``min_width`` the grid still
        drops to fewer when they would be narrower than that.
    gap, row_gap : int
        Spaces between columns, blank lines between rows.
    min_width : int, optional
        Narrowest a column may be. Default for ``'auto'``: the widest
        child's natural width.
    width : int, optional
        Fixed total width (default: the terminal width).
    equal_height : bool
        Stretch cards in one row to the same height.
    """

    def __init__(self, children=None, columns='auto', gap=2, row_gap=1,
                 min_width=None, max_width=None, width=None,
                 equal_height=True, align='l'):
        self.children = []
        for child in children or []:
            self.add(child)
        self.columns = columns
        self.gap = max(0, int(gap))
        self.row_gap = max(0, int(row_gap))
        self.min_width = min_width
        self.max_width = max_width
        self.width = width
        self.equal_height = bool(equal_height)
        self.align = _align(align)

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

    def add(self, child, span=1):
        """Append a child (optionally spanning columns); returns ``self``."""
        if isinstance(child, GridCell):
            self.children.append(child)
        elif isinstance(child, tuple) and len(child) == 2 and \
                isinstance(child[1], int):
            self.children.append(GridCell(child[0], child[1]))
        else:
            self.children.append(GridCell(child, span))
        return self

    def natural_width(self):
        if self.width is not None:
            return int(self.width)
        widths = [_natural_width(c.child) for c in self.children] or [0]
        if self.columns == 'auto':
            n = len(self.children) or 1
        else:
            n = min(self.columns, max(1, len(self.children)))
        col = max(widths)
        if self.min_width is not None:
            col = max(col, int(self.min_width))
        total = n * col + self.gap * (n - 1)
        if self.max_width is not None:
            total = min(total, int(self.max_width))
        return total

    def column_count(self, width=None):
        """How many columns the grid uses at ``width``."""
        width = render_width(width if width is not None else self.width)
        if self.max_width is not None:
            width = min(width, int(self.max_width))
        spans = sum(c.span for c in self.children) or 1
        if self.min_width is not None:
            min_w = int(self.min_width)
        else:
            min_w = max([min(_natural_width(c.child), width)
                         for c in self.children if c.span == 1] or [1])
        min_w = max(1, min_w)
        fit = max(1, (width + self.gap) // (min_w + self.gap))
        if self.columns == 'auto':
            return max(1, min(fit, spans))
        if self.min_width is not None:
            return max(1, min(self.columns, fit))
        return self.columns

    def __str__(self):
        return self.render()

    def render(self, width=None):
        """Draw the grid into ``width`` columns (default: terminal width)."""
        width = render_width(width if width is not None else self.width)
        if self.max_width is not None:
            width = min(width, int(self.max_width))
        if not self.children:
            return ''
        n = self.column_count(width)
        gap = self.gap
        col_w = max(1, (width - gap * (n - 1)) // n)

        # Flow the children into rows.
        rows, row, used = [], [], 0
        for cell in self.children:
            span = min(cell.span, n)
            if used + span > n:
                rows.append(row)
                row, used = [], 0
            row.append((cell, span))
            used += span
        if row:
            rows.append(row)

        out = []
        for r_i, row in enumerate(rows):
            blocks = []
            for cell, span in row:
                cell_w = col_w * span + gap * (span - 1)
                blocks.append([cell, span, cell_w,
                               _render_child(cell.child, cell_w)])
            if self.equal_height:
                tallest = max(b[3].count('\n') + 1 for b in blocks)
                for b in blocks:
                    child = b[0].child
                    if isinstance(child, Card) and \
                            b[3].count('\n') + 1 < tallest:
                        b[3] = child.render(width=b[2], height=tallest)
            height = max(b[3].count('\n') + 1 for b in blocks)
            for k in range(height):
                parts = []
                for b_i, (cell, span, cell_w, text) in enumerate(blocks):
                    lines = text.split('\n')
                    line = lines[k] if k < len(lines) else ''
                    parts.append(_fit_line(line, cell_w, cell.align))
                out.append((' ' * gap).join(parts).rstrip(' '))
            if r_i < len(rows) - 1:
                out.extend([''] * self.row_gap)
        return '\n'.join(out)
