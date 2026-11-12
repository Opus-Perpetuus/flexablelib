"""
Shared pieces of the components: the colour theme, the input base class with
labels, help text and validation, and a few drawing helpers.
"""

from flexablelib import _frames as _fx
from flexablelib.colors import RESET, parse_spec
from flexablelib_tui import Component

__all__ = ['Theme', 'DEFAULT_THEME', 'THEMES', 'Input', 'frame',
           'join_columns', 'Box', 'Button']


class Theme(object):
    """
    Colours the components use, as flexablelib colour specs.

    ``accent`` marks focus and selection, ``muted`` secondary text,
    ``selection`` the highlighted row of a list or table, and ``info`` /
    ``success`` / ``warning`` / ``error`` the message kinds, ``field`` the
    background of text fields.

    ``background`` / ``foreground`` are the terminal colours the theme is
    meant for (used by contrast checks), ``marker=True`` shows focus and
    selection with text markers in colour too. Ready-made themes:
    ``Theme.preset(name)`` with ``'default'``, ``'high-contrast'``,
    ``'high-contrast-light'``, ``'deuteranopia'``, ``'protanopia'``,
    ``'tritanopia'`` and ``'monochrome'`` (see :data:`THEMES`).
    """

    def __init__(self, accent='cyan', muted='bright_black', text=None,
                 selection='black on cyan', border='bright_black',
                 info='blue', success='green', warning='yellow',
                 error='red', title='bold', field='on #262626',
                 background='#000000', foreground='#e5e5e5', marker=False,
                 name='custom'):
        self.name = name
        self.background = background
        self.foreground = foreground
        self.marker = bool(marker)
        self.field = field
        self.accent = accent
        self.muted = muted
        self.text = text
        self.selection = selection
        self.border = border
        self.info = info
        self.success = success
        self.warning = warning
        self.error = error
        self.title = title

    def kind(self, name):
        """The colour for a message kind ('info', 'success', ...)."""
        return getattr(self, name, None) or self.info

    ROLES = ('accent', 'muted', 'text', 'selection', 'border', 'info',
             'success', 'warning', 'error', 'title', 'field')

    @classmethod
    def preset(cls, name):
        """A copy of one of :data:`THEMES` (``KeyError`` lists the names)."""
        try:
            values = THEMES[name]
        except KeyError:
            raise KeyError('unknown theme {0!r}; choose from {1}'.format(
                name, ', '.join(sorted(THEMES))))
        return cls(name=name, **values)

    def contrast(self):
        """``{role: contrast ratio}`` of each role's text against its
        background (the theme's ``background`` when the role sets none)."""
        from flexablelib_tui.accessibility import spec_colors, contrast_ratio
        out = {}
        for role in self.ROLES:
            spec = getattr(self, role)
            fg, bg, attrs = spec_colors(spec)
            if fg is None and bg is None:
                continue
            if 'reverse' in attrs:
                fg, bg = bg, fg
            fg = fg or self.foreground
            bg = bg or self.background
            out[role] = round(contrast_ratio(fg, bg), 2)
        return out

    def __repr__(self):
        return 'Theme({0!r})'.format(self.name)


#: The ready-made themes (``Theme.preset(name)``). The high-contrast ones
#: reach WCAG AAA (7:1) for text; the colour-blind ones keep every message
#: kind distinct under that deficiency (checked with the Machado 2009
#: simulation) at 7:1 or more on a dark background, and all of them show
#: focus with text markers as well as colour.
THEMES = {
    'default': {},
    'high-contrast': dict(
        accent='#ffff00', muted='#d0d0d0', text='#ffffff',
        selection='black on #ffff00', border='#ffffff', info='#00ffff',
        success='#00ff00', warning='#ffff00', error='#ff6060',
        title='bold #ffffff', field='#ffffff on #1c1c1c',
        background='#000000', foreground='#ffffff', marker=True),
    'high-contrast-light': dict(
        accent='#0000c0', muted='#404040', text='#000000',
        selection='#ffffff on #0000c0', border='#000000', info='#00008b',
        success='#005a00', warning='#6b4000', error='#b00000',
        title='bold #000000', field='#000000 on #ececec',
        background='#ffffff', foreground='#000000', marker=True),
    'deuteranopia': dict(
        accent='#56b4e9', muted='#c0c0c0', text='#ffffff',
        selection='black on #56b4e9', border='#a0a0a0', info='#ffffff',
        success='#56b4e9', warning='#ffb000', error='#ff6e6e',
        title='bold #ffffff', field='#ffffff on #1c1c1c',
        background='#000000', foreground='#ffffff', marker=True),
    'protanopia': dict(
        accent='#4da6ff', muted='#c0c0c0', text='#ffffff',
        selection='black on #4da6ff', border='#a0a0a0', info='#ffffff',
        success='#4da6ff', warning='#f0e442', error='#ff6e6e',
        title='bold #ffffff', field='#ffffff on #1c1c1c',
        background='#000000', foreground='#ffffff', marker=True),
    'tritanopia': dict(
        accent='#00e0ff', muted='#c0c0c0', text='#ffffff',
        selection='black on #00e0ff', border='#a0a0a0', info='#a0a0ff',
        success='#00e0ff', warning='#f0e442', error='#ff6e6e',
        title='bold #ffffff', field='#ffffff on #1c1c1c',
        background='#000000', foreground='#ffffff', marker=True),
    'monochrome': dict(
        accent='bold', muted='dim', text=None, selection='reverse',
        border=None, info='bold', success='bold', warning='bold underline',
        error='bold underline', title='bold', field='underline',
        background='#000000', foreground='#e5e5e5', marker=True),
}

DEFAULT_THEME = Theme(name='default')

_SPEC_CACHE = {}

_BOXES = {
    'rounded': '╭╮╰╯─│',
    'single': '┌┐└┘─│',
    'double': '╔╗╚╝═║',
    'heavy': '┏┓┗┛━┃',
    'ascii': '++++-|',
}


class _Themed(Component):
    """A component with a theme and cached colour specs."""

    def __init__(self, theme=None, **kwargs):
        super(_Themed, self).__init__(**kwargs)
        self.theme = theme or DEFAULT_THEME

    def _marked(self):
        return Component._marked(self) or getattr(self.theme, 'marker', False)

    # -- mouse: clickable spots registered while drawing --------------------

    _hot = ()
    _hot_base = 0

    def render(self, width=None, height=None):
        self._hot = []
        self._hot_base = 0
        return Component.render(self, width, height)

    def hot(self, row, action, x0=0, x1=None):
        """Make columns ``[x0, x1)`` of output row ``row`` clickable: a left
        press there calls ``action()`` (``False`` from it means unused)."""
        if isinstance(self._hot, tuple):
            self._hot = []
        self._hot.append((self._hot_base + row, x0, x1, action))

    def hot_parts(self, row, parts, gap=1, start=0, actions=()):
        """Register ``actions[i]`` for the columns ``parts[i]`` take on
        ``row`` when the parts are joined with ``gap`` columns between them
        (``None`` actions are skipped)."""
        x = start
        for part, action in zip(parts, actions):
            w = _fx.visible_width(_fx.strip_ansi(part))
            if action is not None:
                self.hot(row, action, x, x + w)
            x += w + gap

    def on_mouse(self, event):
        if event.action != 'press' or event.button != 0:
            return False
        for row, x0, x1, action in reversed(self._hot):
            if row == event.y and event.x >= x0 and \
                    (x1 is None or event.x < x1):
                result = action()
                self.refresh()
                return result is not False
        return False

    def paint(self, text, spec):
        if not text or not spec or not self._active():
            return text
        prefix = _SPEC_CACHE.get(spec)
        if prefix is None:
            prefix = _SPEC_CACHE[spec] = parse_spec(spec)
        if not prefix:
            return text
        return prefix + text.replace(RESET, RESET + prefix) + RESET

    def mark_current(self, text, spec=None):
        """A highlighted row (the current item of a list): the selection
        colour, and a ``▸`` marker (``>`` without colour) when focus markers
        are on, so it never depends on colour alone."""
        if self._marked() and text:
            text = ('▸' if self._active() else '>') + \
                _fx.slice_columns(text, 1, max(0, _fx.visible_width(text) - 1))
        if self._active():
            text = self.paint(text, spec or self.theme.selection)
        return text

    def cursor(self, char):
        """``char`` drawn as the text cursor."""
        if not self._active():
            return char
        return self.paint(char or ' ', 'reverse')


def frame(lines, width, title=None, color=None, painter=None, style='rounded',
          title_color=None, footer=None):
    """``lines`` inside a box exactly ``width`` columns wide."""
    tl, tr, bl, br, h, v = _BOXES.get(style, _BOXES['rounded'])
    inner = max(0, width - 2)
    paint = painter or (lambda text, spec: text)

    def edge(left, right, label):
        if not label or inner < 6:
            return paint(left + h * inner + right, color)
        label = _fx.truncate(' ' + label + ' ', inner - 2, '… ')
        rest = inner - 1 - _fx.visible_width(label)
        return (paint(left + h, color) + paint(label, title_color or color) +
                paint(h * rest + right, color))
    out = [edge(tl, tr, title)]
    side = paint(v, color)
    for line in lines:
        out.append(side + _fx.fit_line(line, inner) + side)
    out.append(edge(bl, br, footer))
    return out


def join_columns(blocks, widths, gap=1):
    """Side-by-side blocks of lines, each fitted to its width."""
    height = max((len(b) for b in blocks), default=0)
    out = []
    for k in range(height):
        parts = [_fx.fit_line(b[k] if k < len(b) else '', w)
                 for b, w in zip(blocks, widths)]
        out.append((' ' * gap).join(parts))
    return out


class Box(_Themed):
    """
    A titled frame around a component; the frame takes the accent colour
    while anything inside has the focus. ``children`` keep their own focus.
    """

    expand = True
    role = 'region'

    def __init__(self, child, title=None, style='rounded', padding=1,
                 height=None, footer=None, **kwargs):
        super(Box, self).__init__(**kwargs)
        self.child = child
        self.title = title
        self.style = style
        self.padding = max(0, int(padding))
        self.height = height
        self.footer = footer

    def children(self):
        return [self.child]

    def natural_width(self):
        from flexablelib.layout import _natural_width
        return _natural_width(self.child) + 2 + 2 * self.padding

    def _has_focus(self):
        app = self.app
        node = app.focused if app is not None else None
        while node is not None:
            if node is self:
                return True
            node = getattr(node, 'parent', None)
        return False

    def draw(self, width, height):
        from flexablelib.layout import _accepts_height, _render_child
        height = self.height or height
        inner_w = max(1, width - 2 - 2 * self.padding)
        inner_h = None if height is None else max(0, height - 2)
        child = self.child
        if inner_h is not None and _accepts_height(child):
            text = child.render(width=inner_w, height=inner_h)
        else:
            text = _render_child(child, inner_w)
        lines = text.split('\n') if text else []
        if inner_h is not None:
            lines = lines[:inner_h] + [''] * (inner_h - len(lines))
        pad = ' ' * self.padding
        lines = [pad + _fx.fit_line(line, inner_w) + pad for line in lines]
        focus = self._has_focus()
        color = self.theme.accent if focus else self.theme.border
        style, title = self.style, self.title
        if focus and self._marked():
            # Focus without colour: a heavy (or double) frame and a marker.
            style = 'double' if style == 'heavy' else 'heavy'
            title = '▸ ' + (title or '')
        return frame(lines, width, title, color, self.paint, style,
                     title_color=('bold ' + self.theme.accent) if focus
                     else self.theme.title, footer=self.footer)


class Input(_Themed):
    """
    Base of the form inputs.

    ``label`` is drawn above the control, ``help`` below it (muted), and the
    validation error below that (in the error colour). ``required`` and
    ``validators`` (callables taking the value and returning an error message
    or None) are checked by :meth:`validate`. ``on_change(value)`` runs when
    the value changes, ``on_submit(value)`` on Enter. ``name`` is the key the
    value has in a :class:`~flexablelib_components.Form`.
    """

    focusable = True

    def __init__(self, label=None, value=None, name=None, help=None,
                 required=False, validators=None, on_change=None,
                 on_submit=None, width=None, **kwargs):
        super(Input, self).__init__(**kwargs)
        self.label = label
        self.name = name or (label.lower().replace(' ', '_') if label
                             else None)
        self.help = help
        self.required = bool(required)
        self.validators = list(validators or [])
        self.on_change = on_change
        self.on_submit = on_submit
        self.width = width
        self.error = None
        self._value = None
        self.value = value

    # -- value --------------------------------------------------------------

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new):
        self._value = self.coerce(new)

    def coerce(self, value):
        return value

    def set_value(self, value):
        """Set the value as the user would: runs ``on_change``."""
        old = self.value
        self.value = value
        new = self.value
        if new != old:
            self.error = None
            if self.on_change is not None:
                self.on_change(new)
        self.refresh()

    def is_empty(self):
        return self.value in (None, '', [], {})

    def validate(self):
        """Check the value; returns (and keeps in ``error``) the message."""
        error = None
        if self.required and self.is_empty():
            error = 'Requerido'
        else:
            for check in self.validators:
                error = check(self.value)
                if error:
                    break
        self.error = error or None
        return self.error

    def submit(self):
        self.validate()
        if self.on_submit is not None:
            self.on_submit(self.value)
        return True

    # -- drawing ------------------------------------------------------------

    def natural_width(self):
        return max(self.width or 24, _fx.visible_width(self.label or '') + 2)

    def control(self, width, height):   # pragma: no cover - abstract
        return []

    def draw(self, width, height):
        out = []
        if self.label:
            mark = '*' if self.required else ''
            spec = self.theme.accent if self.focused else self.theme.title
            out.append(self.paint(self.label + mark, spec))
        self._hot_base = len(out)
        out.extend(self.control(width, height))
        self._hot_base = 0
        if self.help and not self.error:
            out.append(self.paint(self.help, self.theme.muted))
        if self.error:
            out.append(self.paint('✖ ' + self.error, self.theme.error))
        return out

    role = 'textbox'

    def a11y_value(self):
        value = self.value
        if value is None:
            return ''
        if isinstance(value, bool):
            return ''
        return str(value)

    def a11y_state(self):
        state = []
        if self.required:
            state.append('required')
        if self.error:
            state.append('invalid')
        if self.is_empty() and not isinstance(self.value, bool):
            state.append('empty')
        return state

    def a11y_name(self):
        if self.a11y_label:
            return str(self.a11y_label)
        for text in (self.label, getattr(self, 'placeholder', None),
                     (self.name or '').replace('_', ' ')):
            if isinstance(text, str) and text.strip():
                return text.strip()
        return ''

    def marker(self):
        """The gutter that shows focus: a bar when focused."""
        if self.focused:
            return self.paint('▌', self.theme.accent) if self._active() \
                else '›'
        return ' '


class Button(_Themed):
    """
    A button: Enter or Space calls ``on_press()``. ``kind`` colours it
    (``'primary'``, ``'danger'``, ``'default'``); ``shortcut`` is a key that
    presses it from anywhere in its parent (shown after the label).
    """

    focusable = True
    role = 'button'

    def __init__(self, label, on_press=None, kind='default', shortcut=None,
                 **kwargs):
        super(Button, self).__init__(**kwargs)
        self.label = label
        self.on_press = on_press
        self.kind = kind
        self.shortcut = shortcut
        self.presses = 0

    def natural_width(self):
        return _fx.visible_width(self.text())

    def text(self):
        hint = ' ' + self.shortcut if self.shortcut else ''
        return '[ {0}{1} ]'.format(self.label, hint) if not self._active() \
            else '  {0}{1}  '.format(self.label, hint)

    def press(self):
        self.presses += 1
        if self.on_press is not None:
            self.on_press()
        self.refresh()
        return True

    def style(self):
        theme = self.theme
        if self.disabled:
            return theme.muted
        base = {'primary': 'black on ' + theme.accent,
                'danger': 'white on ' + theme.error}.get(self.kind)
        if self.focused:
            return 'bold reverse' if base is None else 'bold ' + base
        return base or 'on bright_black'

    def draw(self, width, height):
        label = self.text()
        if self._marked() and self.focused:
            label = ('[>' + label[2:-2] + '<]') if not self._active() else \
                ('▸' + label[1:-1] + '◂')
        style = self.style()
        if self.hovered and self._active() and not self.disabled:
            style += ' underline'
        return [self.paint(label, style)]

    def on_key(self, key):
        if str(key) in ('enter', 'space'):
            return self.press()
        return False

    def on_mouse(self, event):
        if event.action == 'release' and event.button == 0 and \
                not self.disabled and 0 <= event.y < 1 and \
                0 <= event.x < self.natural_width():
            return self.press()
        return event.action == 'press' and event.button == 0
