"""
Shared pieces of the components: the colour theme, the input base class with
labels, help text and validation, and a few drawing helpers.
"""

from flexablelib import _frames as _fx
from flexablelib.colors import RESET, parse_spec
from flexablelib_tui import Component

__all__ = ['Theme', 'DEFAULT_THEME', 'Input', 'frame', 'join_columns',
           'Box', 'Button']


class Theme(object):
    """
    Colours the components use, as flexablelib colour specs.

    ``accent`` marks focus and selection, ``muted`` secondary text,
    ``selection`` the highlighted row of a list or table, and ``info`` /
    ``success`` / ``warning`` / ``error`` the message kinds, ``field`` the
    background of text fields.
    """

    def __init__(self, accent='cyan', muted='bright_black', text=None,
                 selection='black on cyan', border='bright_black',
                 info='blue', success='green', warning='yellow',
                 error='red', title='bold', field='on #262626'):
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


DEFAULT_THEME = Theme()

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

    def paint(self, text, spec):
        if not text or not spec or not self._active():
            return text
        prefix = _SPEC_CACHE.get(spec)
        if prefix is None:
            prefix = _SPEC_CACHE[spec] = parse_spec(spec)
        if not prefix:
            return text
        return prefix + text.replace(RESET, RESET + prefix) + RESET

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
        return frame(lines, width, self.title, color, self.paint, self.style,
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
        out.extend(self.control(width, height))
        if self.help and not self.error:
            out.append(self.paint(self.help, self.theme.muted))
        if self.error:
            out.append(self.paint('✖ ' + self.error, self.theme.error))
        return out

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
        if not self._active() and self.focused:
            label = '[>' + label[2:-2] + '<]'
        return [self.paint(label, self.style())]

    def on_key(self, key):
        if str(key) in ('enter', 'space'):
            return self.press()
        return False
