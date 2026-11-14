"""
INTERACTIVE APPLICATIONS

``Component``
    The base of everything that takes keyboard focus: ``draw(width, height)``
    returns its lines, ``on_key(key)`` handles a key (return True when it
    did), ``bindings`` maps keys to callables. Components nest inside any
    :class:`~flexablelib.Grid`, :class:`Screen` or other component, so a
    layout of tables, cards and widgets becomes interactive by placing
    components in it.

``App``
    Runs the loop: draws the screen (only the changed lines reach the
    terminal), reads keys, gives each to the focused component, then to its
    parents, then to the app's own bindings. ``tab`` / ``shift+tab`` move the
    focus between the components on screen, ``ctrl+c`` quits, a resized
    window is redrawn at its new size, and ``push(layer)`` opens a dialog
    over the screen that keeps the focus until ``pop()``.

    ``App.run(keys=[...], size=(80, 24))`` runs without a terminal -- for
    tests, screenshots and scripted demos -- and returns the last frame.

``ScrollView``
    A focusable viewport over content taller than its slot, with a scroll
    bar; arrows, PgUp/PgDn, Home/End and the mouse wheel scroll it.
"""

import io
import time

from flexablelib import _frames as _fx
from flexablelib.colors import RESET, parse_spec, supports_color
from flexablelib.layout import (Card, Grid, GridCell, _render_child,
                                render_width)

from . import accessibility as _a11y
from .keys import Key, MouseEvent, key_label
from .keymap import KeyMap
from .screen import Live, Screen

__all__ = ['Component', 'App', 'ScrollView', 'overlay']

# Frame counter: a component drawn in the latest frame is on screen, and only
# components on screen take focus.
_FRAME = [0]

# Hit testing: while an app tracks the mouse, every component drawn wraps its
# lines in zero-width marks naming it (see flexablelib._frames.extract_marks).
_HIT = {'on': False, 'items': []}


class Component(object):
    """
    Base class for interactive pieces.

    Subclasses implement ``draw(width, height)`` returning a list of lines
    (or one string) and, when they react to keys, ``on_key(key)``. Set
    ``focusable = True`` to take focus; ``self.focused`` says whether they
    have it. ``natural_width()`` is the width a layout should offer.
    ``expand = True`` makes the component fill the height it is given.

    Accessibility: ``role`` (class attribute or argument) and ``a11y_label``
    / ``description`` describe the component to screen readers
    (:meth:`a11y`); ``tab_index`` orders the focus (lower first, ``-1``
    leaves it out of Tab while clicks still focus it). Mouse: ``on_mouse``
    receives :class:`~flexablelib_tui.keys.MouseEvent` values in the
    component's own coordinates; ``hovered`` is true under the pointer when
    the app tracks hover.
    """

    focusable = False
    expand = False
    use_colors = None
    role = 'group'

    def __init__(self, bindings=None, use_colors=None, disabled=False,
                 a11y_label=None, description=None, role=None,
                 tab_index=None):
        self.focused = False
        self.hovered = False
        self.app = None
        self.parent = None
        self.disabled = bool(disabled)
        self.bindings = dict(bindings or {})
        if use_colors is not None:
            self.use_colors = use_colors
        self.a11y_label = a11y_label
        self.description = description
        if role is not None:
            self.role = role
        self.tab_index = tab_index
        self._drawn = -1

    # -- colour -------------------------------------------------------------

    def _active(self):
        if self.use_colors is None:
            return supports_color()
        return bool(self.use_colors)

    def _marked(self):
        """Whether focus and selection are shown with text markers
        (always without colour; with colour when ``focus_marker`` is on)."""
        return not self._active() or _a11y.settings.focus_marker

    def paint(self, text, spec):
        """``text`` in colour ``spec`` (a flexablelib colour spec)."""
        if not text or not spec or not self._active():
            return text
        prefix = parse_spec(spec)
        if not prefix:
            return text
        return prefix + text.replace(RESET, RESET + prefix) + RESET

    # -- accessibility ------------------------------------------------------

    def a11y_name(self):
        """The accessible label: ``a11y_label`` or the component's own
        ``label`` / ``title`` / ``text`` / ``message`` / ``name``."""
        if self.a11y_label:
            return str(self.a11y_label)
        for attr in ('label', 'title', 'text', 'message', 'name'):
            value = getattr(self, attr, None)
            if isinstance(value, str) and value.strip():
                return _fx.strip_ansi(value).strip()
        return ''

    def a11y_value(self):
        """The current value as text ('' when there is none)."""
        return ''

    def a11y_state(self):
        """States beyond focus and disabled: ``checked``, ``expanded`` ..."""
        return []

    def a11y(self):
        """
        What assistive output needs: ``role``, ``label``, ``value``,
        ``state`` (list), ``description``, ``shortcut`` and ``error``.
        """
        state = list(self.a11y_state())
        if self.focused:
            state.insert(0, 'focused')
        if self.disabled:
            state.append('disabled')
        shortcut = getattr(self, 'shortcut', None)
        return {'role': self.role, 'label': self.a11y_name(),
                'value': self.a11y_value(), 'state': state,
                'description': self.description or '',
                'shortcut': key_label(shortcut) if isinstance(shortcut, str)
                and shortcut else '',
                'error': getattr(self, 'error', None) or ''}

    def describe(self):
        """The sentence a screen reader says for this component."""
        return _a11y.describe(self)

    def announce(self, text, priority='polite'):
        """Announce ``text`` through the running app (screen readers)."""
        if self.app is not None:
            self.app.announce(text, priority)

    # -- layout protocol ----------------------------------------------------

    @property
    def can_focus(self):
        return self.focusable and not self.disabled

    @property
    def on_screen(self):
        """Whether the component was drawn in the latest frame."""
        return self._drawn == _FRAME[0]

    def natural_width(self):
        return 20

    def draw(self, width, height):   # pragma: no cover - abstract
        return []

    def render(self, width=None, height=None):
        width = render_width(width)
        self._drawn = _FRAME[0]
        lines = self.draw(width, height)
        if isinstance(lines, str):
            lines = lines.split('\n') if lines else []
        if height is not None:
            lines = lines[:height]
            if self.expand and len(lines) < height:
                lines = lines + [''] * (height - len(lines))
        lines = _fx.fit_lines(lines, width)
        if _a11y.settings.ascii:
            lines = [_fx.ascii_fold(line) for line in lines]
        if _HIT['on']:
            ident = len(_HIT['items'])
            _HIT['items'].append(self)
            start = _fx.mark_open(ident)
            lines = [start + line + _fx.MARK_CLOSE for line in lines]
        return '\n'.join(lines)

    def __str__(self):
        return _fx.expand_graphics(self.render())

    def children(self):
        """Components (or layouts holding components) inside this one."""
        return []

    # -- input --------------------------------------------------------------

    def handle_key(self, key):
        """Bindings first, then ``on_key``; True when the key was used."""
        action = self.bindings.get(str(key))
        if action is not None:
            result = action()
            return result is not False
        return bool(self.on_key(key))

    def on_key(self, key):
        return False

    def on_mouse(self, event):
        """A mouse event in this component's coordinates (``event.x``,
        ``event.y`` from its top-left cell); True when it was used. Clicks
        already focus the component; the wheel falls back to the keys
        ``'scrollup'`` / ``'scrolldown'``, then ``'up'`` / ``'down'``."""
        return False

    def on_focus(self):
        pass

    def on_blur(self):
        pass

    def focus(self):
        """Ask the running app to focus this component."""
        if self.app is not None:
            self.app.focus(self)

    def refresh(self):
        if self.app is not None:
            self.app.refresh()


def overlay(base, top, x, y, width):
    """Lay the lines of ``top`` over ``base`` at column ``x``, row ``y``."""
    out = list(base)
    for k, line in enumerate(top):
        row = y + k
        if row < 0 or row >= len(out):
            continue
        w = _fx.visible_width(line)
        under = out[row]
        left = _fx.slice_columns(under, 0, x) if x > 0 else ''
        right_w = width - x - w
        right = _fx.slice_columns(under, x + w, right_w) if right_w > 0 \
            else ''
        out[row] = left + line + right
    return out


def _child_nodes(node):
    """The direct children of anything a screen can hold."""
    if isinstance(node, Component):
        return list(node.children())
    if isinstance(node, Screen):
        return [n for n in (node.header, node.body, node.footer)
                if n is not None]
    if isinstance(node, Grid):
        return list(node.children)
    if isinstance(node, GridCell):
        return [node.child]
    if isinstance(node, Card):
        body = node.body
        return [body] if body is not None and not isinstance(body, str) \
            else []
    if isinstance(node, App):
        return [node.screen] + list(node.layers)
    return []


class App(object):
    """
    An interactive terminal application.

    >>> app = App(body=grid, header=StatusBar('Panel'), footer=KeyHints(...),
    ...           bindings={'q': app.exit, 'f5': (reload, 'Recargar')})
    >>> app.run()

    ``bindings`` maps keys to callables, or to ``(callable, description)``
    so the help screen (F1) and :meth:`key_hints` list them; ``None`` removes
    a default one. The defaults come from ``keymap`` (a
    :class:`~flexablelib_tui.KeyMap`): ``ctrl+c`` quits, ``tab`` /
    ``shift+tab`` move the focus, ``f1`` shows the shortcuts.
    ``interval`` (seconds) calls ``on_tick(app)`` that often and redraws.

    Mouse: ``mouse=True`` turns on clicks (focus and activate what is under
    the pointer), the wheel (scrolls what is under it) and drags (split
    panes, scroll bars); ``mouse='hover'`` also tracks the pointer.

    Accessibility (see :mod:`flexablelib_tui.accessibility`):
    ``screen_reader=True`` draws the screen as linear text with roles and
    labels and announces changes to ``announce`` (``'stdout'``,
    ``'stderr'``, a path, a stream or a callable); ``reduced_motion``,
    ``ascii`` and ``focus_marker`` override the environment;
    ``min_size=(columns, lines)`` shows a message instead of a squeezed
    screen; ``title`` names the application for screen readers;
    ``theme`` (a name such as ``'high-contrast'`` or ``'deuteranopia'``, or
    a ``Theme``) applies to every component that did not choose one.
    """

    def __init__(self, body=None, header=None, footer=None, bindings=None,
                 interval=None, on_tick=None, mouse=False, stream=None,
                 terminal=None, use_colors=None, keymap=None,
                 screen_reader=None, announce=None, reduced_motion=None,
                 ascii=None, focus_marker=None, min_size=None, title=None,
                 lang=None, theme=None):
        self.use_colors = use_colors
        self.screen = Screen(body=body, header=header, footer=footer)
        self.layers = []
        self.focused = None
        self.running = False
        self.result = None
        self.interval = interval
        self.on_tick = on_tick
        self.mouse = mouse if mouse == 'hover' else bool(mouse)
        self.stream = stream
        self.terminal = terminal
        self.frames = 0
        self.clock = time.monotonic
        self.last_frame = ''
        self.title = title
        self.min_size = tuple(min_size) if min_size else None
        self.keymap = keymap if keymap is not None else KeyMap()
        self.a11y_settings = dict(
            (k, v) for k, v in (('screen_reader', screen_reader),
                                ('reduced_motion', reduced_motion),
                                ('ascii', ascii),
                                ('focus_marker', focus_marker),
                                ('lang', lang), ('theme', theme))
            if v is not None)
        self.announcer = _a11y.Announcer(announce)
        self.hovered = None
        self._dirty = True
        self._focus_stack = []
        self._regions = []
        self._origins = {}
        self._layer_boxes = []
        self._capture = None
        self.descriptions = {}
        self.bindings = {}
        for key in self.keymap.keys_for('quit'):
            self.bindings[key] = self.exit
        for key in self.keymap.keys_for('focus_next'):
            self.bindings[key] = self.focus_next
        for key in self.keymap.keys_for('focus_prev'):
            self.bindings[key] = self.focus_previous
        self.descriptions.update(dict.fromkeys(
            self.keymap.keys_for('focus_next'), 'Siguiente'))
        self.descriptions.update(dict.fromkeys(
            self.keymap.keys_for('focus_prev'), 'Anterior'))
        self.descriptions.update(dict.fromkeys(
            self.keymap.keys_for('quit'), 'Salir'))
        for key, action in (bindings or {}).items():
            if action is None:
                self.bindings.pop(key, None)
                self.descriptions.pop(key, None)
                continue
            if isinstance(action, tuple):
                action, text = action
                self.descriptions[key] = text
            self.bindings[key] = action

    # -- accessibility ------------------------------------------------------

    @property
    def screen_reader(self):
        if 'screen_reader' in self.a11y_settings:
            return bool(self.a11y_settings['screen_reader'])
        return _a11y.settings.screen_reader

    def settings(self):
        """The accessibility settings in force while this app works."""
        return _a11y.configure(**self.a11y_settings)

    def announce(self, text, priority='polite'):
        """Tell screen-reader users ``text`` (see ``announce=``)."""
        return self.announcer.announce(text, priority)

    def key_hints(self):
        """``[(key label, description)]`` of the documented bindings, for a
        :class:`~flexablelib_tui.KeyHints` footer or a help screen."""
        ascii = _a11y.settings.ascii or self.a11y_settings.get('ascii')
        out = []
        seen = set()
        for key, text in self.descriptions.items():
            if key in self.bindings and text and key not in seen:
                seen.add(key)
                out.append((key_label(key, ascii), text))
        return out

    def show_help(self):
        """A dialog listing the shortcuts (F1); any key closes it."""
        self.push(_Help(self.key_hints(), self.keymap))
        self.announce('Ayuda: ' + '; '.join(
            '{0}: {1}'.format(k, d) for k, d in self.key_hints()))
        return True

    def read_screen(self):
        """Announce the whole screen as linear text (Ctrl+R)."""
        for line in self.linear_text().split('\n'):
            self.announcer.announce(line, 'assertive')
        return True

    def linear_text(self):
        """
        The screen as screen readers want it: one line per meaningful
        component, ``role`` and label first, the focused one marked ``>``,
        dialogs and notifications included.
        """
        with self.settings():
            lines = []
            title = self.title or self._plain(self.screen.header)
            if title:
                lines.append(title)
            modal = self._modal()
            if modal is not None:
                lines.append(_a11y.describe(modal))
            root = modal if modal is not None else self.screen
            for node in self.walk(root):
                if node is modal or not isinstance(node, Component):
                    continue
                if not node.on_screen and self.frames:
                    continue
                info = node.a11y()
                if info['role'] in ('group', 'region', 'none') and \
                        not info['label']:
                    continue
                mark = '>' if node is self.focused else ' '
                lines.append(mark + ' ' + _a11y.describe(info))
            for layer in self.layers:
                if isinstance(layer, _Toast):
                    lines.append('  ' + _a11y.describe(layer))
            if modal is None:
                footer = self._plain(self.screen.footer)
                if footer:
                    lines.append(footer)
        return '\n'.join(lines)

    @staticmethod
    def _plain(node):
        if node is None or isinstance(node, Component):
            return ''
        try:
            text = _render_child(node, 200)
        except Exception:   # pragma: no cover - defensive
            return ''
        text = _fx.strip_ansi(text)
        return ' '.join(text.split())

    def _focus_snapshot(self):
        node = self.focused
        if node is None:
            return None, None
        return node, _a11y.describe(node)

    def _announce_changes(self, before):
        node, text = self._focus_snapshot()
        if node is None:
            return
        if node is not before[0]:
            self.announce(_a11y.describe(node))
        elif text != before[1]:
            info = node.a11y()
            parts = [str(info['value'])] if info['value'] not in (None, '') \
                else []
            parts += [_a11y.STATE_NAMES.get(
                _a11y.settings.lang, _a11y.STATE_NAMES['es']).get(s, s)
                for s in info['state'] if s != 'focused']
            if info.get('error'):
                parts.append('Error: ' + info['error'])
            self.announce(', '.join(parts) or text)

    # -- tree ---------------------------------------------------------------

    def walk(self, root=None):
        """Every node under ``root`` (default: the screen and dialogs)."""
        stack = [(root if root is not None else self, None)]
        while stack:
            node, parent = stack.pop()
            if isinstance(node, Component):
                node.app = self
                node.parent = parent
                yield node
            elif node is not self:
                yield node
            for child in reversed(_child_nodes(node)):
                stack.append((child, node if isinstance(node, Component)
                              else parent))

    def components(self):
        return [n for n in self.walk() if isinstance(n, Component)]

    def _modal(self):
        modal = [layer for layer in self.layers
                 if getattr(layer, '_modal', True)]
        return modal[-1] if modal else None

    def focusables(self, tab=False):
        """Components that can take focus now, in focus order: positive
        ``tab_index`` first (ascending), then screen order. With ``tab``,
        the ones ``tab_index=-1`` leaves out of Tab are skipped."""
        root = self._modal() or self.screen
        items = [n for n in self.walk(root)
                 if isinstance(n, Component) and n.can_focus and n.on_screen]
        if tab:
            items = [n for n in items if (n.tab_index or 0) >= 0]
        ordered = sorted((n for n in items if (n.tab_index or 0) > 0),
                         key=lambda n: n.tab_index)
        return ordered + [n for n in items if not (n.tab_index or 0) > 0]

    # -- focus --------------------------------------------------------------

    def focus(self, component):
        if component is self.focused:
            return
        if self.focused is not None:
            self.focused.focused = False
            self.focused.on_blur()
        self.focused = component
        if component is not None:
            component.app = self
            component.focused = True
            component.on_focus()
        self._dirty = True

    def _cycle(self, step):
        items = self.focusables(tab=True)
        if not items:
            return True
        if self.focused in items:
            i = (items.index(self.focused) + step) % len(items)
        else:
            i = 0 if step > 0 else len(items) - 1
        self.focus(items[i])
        return True

    def focus_next(self):
        return self._cycle(1)

    def focus_previous(self):
        return self._cycle(-1)

    # -- dialogs ------------------------------------------------------------

    def push(self, layer, position='center', modal=True):
        """
        Show ``layer`` over the screen. ``position`` is ``'center'``,
        ``'top'``, ``'bottom'``, ``'top-right'``, ``'bottom-right'`` or an
        ``(x, y)`` cell (negative counts from the right / bottom). A modal
        layer keeps the focus (Tab cycles inside it) until popped;
        ``modal=False`` floats over the screen without taking keys
        (notifications, tooltips).
        """
        layer._position = position
        layer._modal = bool(modal)
        self.layers.append(layer)
        pushed = getattr(layer, '_pushed', None)
        if callable(pushed):
            pushed()
        for node in self.walk(layer):
            if isinstance(node, Component):
                node.app = self
        if modal:
            self._focus_stack.append(self.focused)
            self.focus(None)
            if isinstance(layer, Component):
                with self.settings():
                    self.announce(_a11y.describe(layer), 'assertive')
        self._dirty = True
        return layer

    def pop(self, layer=None):
        """Close the top dialog (or ``layer``) and give the focus back."""
        if layer is None:
            layer = self._modal()
        if layer is None or layer not in self.layers:
            return None
        self.layers.remove(layer)
        if getattr(layer, '_modal', True):
            previous = self._focus_stack.pop() if self._focus_stack else None
            self.focus(previous)
        if self._capture is not None and self._capture is layer:
            self._capture = None
        self._dirty = True
        popped = getattr(layer, '_popped', None)
        if callable(popped):
            popped()
        return layer

    def notify(self, message, kind='info', seconds=3.0):
        """A short message in the top-right corner for ``seconds``; screen
        readers hear it with its kind (``'Éxito: Guardado'``)."""
        toast = _Toast(message, kind, self.clock() + seconds)
        toast.use_colors = self.use_colors
        toasts = [l for l in self.layers if isinstance(l, _Toast)]
        self.push(toast, position=(-1, 1 + 3 * len(toasts)), modal=False)
        with self.settings():
            self.announce(_a11y.status_symbol(kind, word=True, ascii=True)
                          .split(' ', 1)[-1] + ': ' + str(message),
                          'assertive' if kind == 'error' else 'polite')
        return toast

    # -- drawing ------------------------------------------------------------

    def refresh(self):
        """Mark the screen for redrawing."""
        self._dirty = True

    def _render_marked(self, node, **kw):
        """Render ``node``; with the mouse on, also where its pieces went."""
        if not self.mouse:
            text = node.render(**kw)
            return (text.split('\n') if text else []), []
        _HIT['on'] = True
        _HIT['items'] = []
        try:
            text = node.render(**kw)
        finally:
            _HIT['on'] = False
        items = _HIT['items']
        _HIT['items'] = []
        lines, regions = _fx.extract_marks(text.split('\n') if text else [])
        return lines, [(items[i], row, x0, x1, depth)
                       for i, row, x0, x1, depth in regions
                       if 0 <= i < len(items)]

    def _compose(self, width, height):
        _FRAME[0] += 1
        for node in self.walk():     # give every component its app
            pass
        now = self.clock()
        expired = [l for l in self.layers
                   if isinstance(l, _Toast) and l.until <= now]
        for layer in expired:
            self.layers.remove(layer)
        lines, base = self._render_marked(self.screen, width=width,
                                          height=height)
        regions = [r + (-1,) for r in base]
        boxes = []
        rows = len(lines)
        for n, layer in enumerate(self.layers):
            want = getattr(layer, 'natural_width', lambda: width - 4)()
            w = max(1, min(width - 2, want))
            fixed = getattr(layer, 'height', None)
            kw = {'width': w} if fixed is None else \
                {'width': w, 'height': min(rows - 2, fixed)}
            top, marks = self._render_marked(layer, **kw)
            top = top[:rows]
            x, y = self._place(getattr(layer, '_position', 'center'), w,
                               len(top), width, rows)
            lines = overlay(lines, top, x, y, width)
            boxes.append((layer, x, y, w, len(top)))
            regions.extend((c, row + y, x0 + x, x1 + x, depth, n)
                           for c, row, x0, x1, depth in marks
                           if row < len(top))
        self._regions = regions
        self._layer_boxes = boxes
        origins = {}
        for comp, row, x0, x1, depth, n in regions:
            seen = origins.get(id(comp))
            if seen is None or (row, x0) < (seen[1], seen[0]):
                origins[id(comp)] = (x0, row)
        self._origins = origins
        return lines

    @staticmethod
    def _place(position, w, h, width, rows):
        if isinstance(position, (tuple, list)):
            x, y = position
            x = width - w + x + 1 if x < 0 else x
            y = rows - h + y + 1 if y < 0 else y
        elif position == 'top':
            x, y = (width - w) // 2, 1
        elif position == 'bottom':
            x, y = (width - w) // 2, rows - h - 1
        elif position == 'top-right':
            x, y = width - w - 1, 1
        elif position == 'bottom-right':
            x, y = width - w - 1, rows - h - 1
        else:
            x, y = (width - w) // 2, (rows - h) // 2
        return max(0, min(x, width - w)), max(0, min(y, rows - h))

    def _too_small(self, width, height):
        need_w, need_h = self.min_size
        msg = ['Ventana muy pequeña',
               '{0}×{1}, se necesitan {2}×{3}'.format(width, height, need_w,
                                                     need_h),
               'Agranda la terminal o reduce la letra']
        if _a11y.settings.ascii:
            msg = [_fx.ascii_fold(m) for m in msg]
        top = max(0, (height - len(msg)) // 2)
        lines = [''] * top + [_fx.fit_line(m, width, 'c') for m in msg]
        lines = lines[:height] + [''] * max(0, height - len(lines))
        return [_fx.fit_line(l, width) for l in lines]

    def render(self, width=None, height=None):
        width = render_width(width)
        if height is None:
            height = self.screen.height
        with self.settings():
            return self._render(width, height)

    def _render(self, width, height):
        if self.use_colors is not None:
            # App(use_colors=...) is the default for every piece on screen
            # (widgets and components alike) that did not choose for itself.
            for node in self.walk():
                if node is not self and \
                        getattr(node, 'use_colors', False) is None:
                    node.use_colors = self.use_colors
        if self.min_size and height is not None and (
                width < self.min_size[0] or height < self.min_size[1]):
            lines = self._too_small(width, height)
            self._regions = []
        else:
            lines = self._compose(width, height)
            candidates = self.focusables(tab=True) or self.focusables()
            if self.focused not in self.focusables():
                # First frame, or the focused component left the screen (a
                # narrower layout hid it, a dialog closed): focus the first.
                self.focus(candidates[0] if candidates else None)
                if self.focused is not None:
                    lines = self._compose(width, height)
        if _a11y.settings.ascii:
            lines = [_fx.ascii_fold(line) for line in lines]
        self.frames += 1
        self._dirty = False
        if self.screen_reader:
            self.last_frame = self.linear_text()
        else:
            self.last_frame = '\n'.join(lines)
        return self.last_frame

    # -- mouse --------------------------------------------------------------

    def hit(self, x, y):
        """The components under cell ``(x, y)``, innermost first (empty
        when a dialog covers the cell or a modal dialog blocks it)."""
        modal = self._modal()
        for n in range(len(self._layer_boxes) - 1, -1, -1):
            layer, lx, ly, lw, lh = self._layer_boxes[n]
            if lx <= x < lx + lw and ly <= y < ly + lh:
                return self._chain(x, y, n)
            if layer is modal:
                return []
        return self._chain(x, y, -1)

    def _chain(self, x, y, layer):
        best = None
        for comp, row, x0, x1, depth, n in self._regions:
            if n == layer and row == y and x0 <= x < x1:
                if best is None or depth >= best[1]:
                    best = (comp, depth)
        if best is None:
            return []
        chain = []
        node = best[0]
        while node is not None and node not in chain:
            if isinstance(node, Component):
                chain.append(node)
            node = getattr(node, 'parent', None)
        return chain

    def origin(self, component):
        """``(x, y)`` of the component's top-left cell in the last frame."""
        return self._origins.get(id(component))

    def _local(self, component, event):
        origin = self.origin(component) or (0, 0)
        return event.moved(origin[0], origin[1])

    def _mouse(self, key):
        event = key.mouse
        action = event.action
        if self._capture is not None and action in ('drag', 'release'):
            target = self._capture
            if action == 'release':
                self._capture = None
            target.on_mouse(self._local(target, event))
            return True
        chain = self.hit(event.x, event.y)
        if action == 'move':
            new = chain[0] if chain else None
            if new is not self.hovered:
                if self.hovered is not None:
                    self.hovered.hovered = False
                if new is not None:
                    new.hovered = True
                self.hovered = new
                self._dirty = True
            for comp in chain:
                if comp.on_mouse(self._local(comp, event)):
                    return True
            return new is not None
        if not chain:
            return self._modal() is not None    # outside a dialog: swallow
        if action == 'press' and event.button in (0, 1, 2):
            # Only what Tab could reach: an inner picker (a calendar inside
            # a date input) leaves the focus on the input that owns it.
            reachable = set(map(id, self.focusables()))
            for comp in chain:
                if id(comp) in reachable:
                    if (comp.tab_index or 0) >= -1:
                        self.focus(comp)
                    break
        for comp in chain:
            if comp.on_mouse(self._local(comp, event)):
                if action == 'press':
                    self._capture = comp
                return True
        if action == 'scroll':
            names = {64: ('scrollup', 'up'), 65: ('scrolldown', 'down'),
                     66: ('scrollleft', 'left'), 67: ('scrollright', 'right')}
            for name in names.get(event.button, ()):
                for comp in chain:
                    if comp.handle_key(Key(name)):
                        return True
        return action == 'press'

    # -- input --------------------------------------------------------------

    def dispatch(self, key):
        """Route one key; returns True when something used it."""
        if not isinstance(key, Key):
            key = Key(str(key), str(key) if len(str(key)) == 1 else '')
        if key.event == 'release' or str(key) == 'response':
            return False
        key = self.keymap.translate(key)
        self._dirty = True
        with self.settings():
            before = self._focus_snapshot()
            used = self._dispatch(key)
            if self.running or self.frames:
                self._announce_changes(before)
        return used

    def _dispatch(self, key):
        name = str(key)
        if key.mouse is not None:
            return self._mouse(key)
        if name in ('focusin', 'focusout'):
            self.terminal_focused = name == 'focusin'
            return False
        quit_keys = self.keymap.keys_for('quit')
        if name in quit_keys and name in self.bindings:
            self.bindings[name]()
            return True
        node = self.focused
        seen = set()
        while node is not None and id(node) not in seen:
            seen.add(id(node))
            if isinstance(node, Component) and node.handle_key(key):
                return True
            node = getattr(node, 'parent', None)
        top = self._modal()
        if top is None and self.focused is None:
            # Nothing has the focus: the screen's own components still get
            # their keys (a shell's shortcuts, a page with no inputs).
            top = self.screen.body
        if isinstance(top, Component) and top is not self.focused and \
                id(top) not in seen and top.handle_key(key):
            return True
        action = self.bindings.get(name)
        if action is not None:
            result = action()
            return result is not False
        named = self.keymap.action_for(key)
        if named == 'help' and not isinstance(self._modal(), _Help):
            return self.show_help()
        if named == 'read_screen' and self.screen_reader:
            return self.read_screen()
        return False

    def exit(self, result=None):
        """Stop the loop; ``run()`` returns ``result``."""
        self.result = result
        self.running = False
        return True

    quit = exit

    # -- loop ---------------------------------------------------------------

    def run(self, keys=None, size=None, max_frames=None):
        """
        Run until ``exit()``. With ``keys`` (an iterable of key names or
        :class:`Key`), run headless: no terminal, the keys fed one by one,
        the frame redrawn after each; returns the last frame. Otherwise
        returns ``result`` passed to ``exit()``.
        """
        if keys is not None:
            return self._run_headless(keys, size)
        return self._run_terminal(size, max_frames)

    def _run_headless(self, keys, size):
        width, height = size or (80, 24)
        stream = self.stream if self.stream is not None else io.StringIO()
        live = Live(self, stream=stream, force_terminal=True, width=width,
                    height=height)
        self.running = True
        with live:
            live.update()
            if self.screen_reader:
                with self.settings():
                    for line in self.linear_text().split('\n'):
                        self.announcer.announce(line, 'assertive')
            for key in keys:
                if not self.running:
                    break
                if str(key) == 'tick':
                    if self.on_tick is not None:
                        self.on_tick(self)
                    self._dirty = True
                else:
                    self.dispatch(key)
                if self._dirty:
                    live.update()
        self.running = False
        self.live = live
        return self.last_frame

    def _make_terminal(self):
        from .terminal import Terminal
        return self.terminal or Terminal(mouse=self.mouse, focus=True)

    def _run_terminal(self, size, max_frames):   # pragma: no cover - needs a tty
        import os as _os
        if _os.environ.get('TERM', '').lower() == 'dumb' and \
                'screen_reader' not in self.a11y_settings:
            # No cursor addressing: linear output works everywhere.
            self.a11y_settings['screen_reader'] = True
        if self.screen_reader:
            return self._run_linear(max_frames)
        terminal = self._make_terminal()
        width, height = size or (None, None)
        live = Live(self, stream=self.stream, width=width, height=height)
        self.running = True
        next_tick = time.monotonic() + (self.interval or 0)
        with terminal:
            if any(getattr(c, 'needs_graphics', False)
                   for c in self.components()):
                from . import graphics as _graphics
                _graphics.probe_terminal(terminal)
            caps = getattr(terminal, 'capabilities', None)
            if 'ascii' not in self.a11y_settings and caps is not None and \
                    caps.unicode is False and not _a11y.settings.ascii:
                self.a11y_settings['ascii'] = True
            with live:
                live.update()
                while self.running:
                    timeout = 0.1
                    if self.interval:
                        timeout = max(0.0, min(timeout,
                                               next_tick - time.monotonic()))
                    for key in terminal.read_keys(timeout=timeout):
                        self.dispatch(key)
                        if not self.running:
                            break
                    if any(isinstance(l, _Toast) and l.until <= self.clock()
                           for l in self.layers):
                        self._dirty = True
                    if self.interval and time.monotonic() >= next_tick:
                        next_tick += self.interval
                        if self.on_tick is not None:
                            self.on_tick(self)
                        self._dirty = True
                    if terminal.resized():
                        live.invalidate()
                        self._dirty = True
                    if self._dirty and self.running:
                        live.update()
                        if max_frames is not None and \
                                self.frames >= max_frames:
                            break
        self.live = live
        return self.result

    def _run_linear(self, max_frames=None):   # pragma: no cover - needs a tty
        """
        Screen-reader mode on a real terminal: no full-screen drawing; the
        screen is printed once as linear text, then every change is
        announced as a new line (what screen readers read best).
        """
        import os as _os
        import sys as _sys
        stream = self.stream if self.stream is not None else _sys.stdout
        if self.announcer.target is None:
            self.announcer.target = stream
        if self.terminal is None and \
                _os.environ.get('TERM', '').lower() == 'dumb':
            # A dumb terminal gets no mode switches at all: the escape
            # sequences would be printed or read aloud.
            from .terminal import Terminal
            terminal = Terminal(paste=False, focus=False, keyboard='legacy')
        else:
            terminal = self._make_terminal()
        self.running = True
        width = render_width(None)
        next_tick = time.monotonic() + (self.interval or 0)
        with terminal:
            self.render(width, self.screen.height)
            self.read_screen()
            while self.running:
                for key in terminal.read_keys(timeout=0.1):
                    self.dispatch(key)
                    if self._dirty:
                        self.render(width, self.screen.height)
                    if not self.running:
                        break
                if self.interval and time.monotonic() >= next_tick:
                    next_tick += self.interval
                    if self.on_tick is not None:
                        self.on_tick(self)
                    self.render(width, self.screen.height)
                if max_frames is not None and self.frames >= max_frames:
                    break
        return self.result


class _Toast(Component):
    """A notification drawn by :meth:`App.notify`; a click dismisses it."""

    COLORS = {'info': 'blue', 'success': 'green', 'warning': 'yellow',
              'error': 'red'}
    ICONS = {'info': 'ℹ', 'success': '✔', 'warning': '⚠', 'error': '✖'}
    role = 'status'

    def __init__(self, message, kind, until):
        super(_Toast, self).__init__()
        self.message = str(message)
        self.kind = kind
        self.until = until

    def a11y_name(self):
        word = _a11y.status_symbol(self.kind, word=True, ascii=True)
        return word.split(' ', 1)[-1] + ': ' + self.message

    def on_mouse(self, event):
        if event.action == 'press' and self.app is not None:
            self.app.pop(self)
            return True
        return False

    def natural_width(self):
        return min(48, _fx.visible_width(self.message) + 6)

    def draw(self, width, height):
        color = self.COLORS.get(self.kind, 'blue')
        inner = max(1, width - 2)
        text = _fx.fit_line(self.ICONS.get(self.kind, '•') + ' ' +
                            self.message, inner)
        if not self._active():
            return ['+' + '-' * inner + '+', '|' + text + '|',
                    '+' + '-' * inner + '+']
        return [self.paint(' ' + text + ' ', 'bold black on ' + color)]


class _Help(Component):
    """The shortcut list :meth:`App.show_help` opens; any key closes it."""

    role = 'dialog'

    def __init__(self, hints, keymap):
        super(_Help, self).__init__(a11y_label='Atajos de teclado')
        self.hints = list(hints)
        self.keymap = keymap
        self.title = 'Atajos de teclado'

    def natural_width(self):
        widths = [_fx.visible_width(k) + 3 + _fx.visible_width(d)
                  for k, d in self.hints] or [20]
        return min(70, max(max(widths), 30) + 4)

    def draw(self, width, height):
        inner = max(1, width - 4)
        keyw = max([_fx.visible_width(k) for k, _ in self.hints] or [4])
        body = [_fx.fit_line(_fx.fit_line(k, keyw) + '   ' + d, inner)
                for k, d in self.hints] or ['(sin atajos)']
        body += ['', _fx.fit_line('Cualquier tecla cierra esta ayuda', inner)]
        title = _fx.truncate(' ' + self.title + ' ', inner, '')
        pad = inner - _fx.visible_width(title)
        lines = ['┌─' + '─' * (pad // 2) + title + '─' * (pad - pad // 2) +
                 '─┐']
        lines += ['│ ' + _fx.fit_line(b, inner) + ' │' for b in body]
        lines.append('└' + '─' * (inner + 2) + '┘')
        return lines

    def handle_key(self, key):
        if self.app is not None:
            self.app.pop(self)
        return True

    def on_mouse(self, event):
        if event.action == 'press' and self.app is not None:
            self.app.pop(self)
            return True
        return False


class ScrollView(Component):
    """
    A scrollable viewport.

    ``content`` is text, a list of lines, or any renderable (drawn at the
    view's width minus the scroll bar). ``height`` fixes the view's height;
    otherwise it takes the height its slot gives it. ``follow=True`` keeps
    the view at the bottom while it is there (for logs).
    ``follow_focus=True`` (the default) scrolls to the component inside
    the content that takes the focus (Tab reaches the ones out of view):
    each time the focus moves to another component inside, its rows are
    brought into view; scrolling by hand afterwards is left alone.
    """

    focusable = True
    expand = True
    role = 'scrollbar'

    def __init__(self, content='', height=None, follow=False, scrollbar=True,
                 color='bright_black', focus_color='cyan', step=3,
                 follow_focus=True, **kwargs):
        super(ScrollView, self).__init__(**kwargs)
        self.follow_focus = bool(follow_focus)
        self._followed = None
        self.content = content
        self.height = None if height is None else max(1, int(height))
        self.follow = bool(follow)
        self.scrollbar = bool(scrollbar)
        self.color = color
        self.focus_color = focus_color
        self.step = max(1, int(step))
        self.offset = 0
        self.view_height = self.height or 1
        self.total = 0

    def natural_width(self):
        from flexablelib.layout import _natural_width
        return _natural_width(self.content) + (1 if self.scrollbar else 0)

    def children(self):
        return [self.content] if not isinstance(self.content, (str, list)) \
            else []

    def _lines(self, width):
        content = self.content
        if isinstance(content, list):
            return [str(line) for line in content]
        if isinstance(content, str):
            return content.split('\n') if content else []
        text = _render_child(content, width)
        return text.split('\n') if text else []

    @property
    def max_offset(self):
        return max(0, self.total - self.view_height)

    def scroll_to(self, offset):
        self.offset = max(0, min(int(offset), self.max_offset))
        self.refresh()

    def scroll(self, delta):
        self.scroll_to(self.offset + delta)

    _last_width = None

    def _focused_inside(self):
        target = self.app.focused if self.app is not None else None
        if target is None or target is self or \
                isinstance(self.content, (str, list)):
            return None
        node, seen = getattr(target, 'parent', None), 0
        while node is not None and seen < 256:
            if node is self:
                return target
            node, seen = getattr(node, 'parent', None), seen + 1
        return None

    def focus_rows(self, width):
        """``(first, last)`` content rows of the focused component inside
        the view, or None."""
        target = self._focused_inside()
        if target is None:
            return None
        saved = _HIT['on'], _HIT['items']
        _HIT['on'], _HIT['items'] = True, []
        try:
            text = _render_child(self.content, width)
            items = _HIT['items']
        finally:
            _HIT['on'], _HIT['items'] = saved
        _lines, regions = _fx.extract_marks(text.split('\n') if text else [])
        rows = [row for i, row, x0, x1, depth in regions
                if 0 <= i < len(items) and items[i] is target]
        return (min(rows), max(rows)) if rows else None

    def _follow(self, inner, h):
        target = self._focused_inside()
        if target is self._followed:
            return
        self._followed = target
        span = self.focus_rows(inner) if target is not None else None
        if span is None:
            return
        first, last = span
        if first < self.offset or last - first + 1 > h:
            self.offset = first
        elif last >= self.offset + h:
            self.offset = last - h + 1

    def draw(self, width, height):
        self._last_width = width
        h = self.height or height or self.view_height
        inner = max(1, width - 1) if self.scrollbar else width
        if self.follow_focus:
            self._follow(inner, max(1, h))
        lines = self._lines(inner)
        at_bottom = self.offset >= self.max_offset
        self.total = len(lines)
        self.view_height = max(1, h)
        if self.follow and at_bottom:
            self.offset = self.max_offset
        self.offset = max(0, min(self.offset, self.max_offset))
        visible = lines[self.offset:self.offset + self.view_height]
        visible += [''] * (self.view_height - len(visible))
        if not self.scrollbar:
            return visible
        bar = self._bar()
        return [_fx.fit_line(line, inner) + mark
                for line, mark in zip(visible, bar)]

    def _bar(self):
        h = self.view_height
        color = self.focus_color if self.focused else self.color
        if self.total <= h:
            return [' '] * h
        thumb = max(1, h * h // self.total)
        top = (h - thumb) * self.offset // max(1, self.max_offset)
        return [self.paint('┃' if top <= k < top + thumb else '│', color)
                if not (self._marked() and self.focused) else
                ('█' if top <= k < top + thumb else '│') for k in range(h)]

    def a11y_name(self):
        return Component.a11y_name(self) or 'Contenido'

    def a11y_value(self):
        if self.total <= self.view_height:
            return ''
        return 'líneas {0}-{1} de {2}'.format(
            self.offset + 1, min(self.total, self.offset + self.view_height),
            self.total)

    def on_mouse(self, event):
        width = self._last_width
        on_bar = self.scrollbar and width and event.x >= width - 1 and \
            self.total > self.view_height
        if event.action == 'press' and event.button == 0 and on_bar:
            self._dragging = True
        if event.action in ('press', 'drag') and getattr(
                self, '_dragging', False):
            span = max(1, self.view_height - 1)
            self.scroll_to(round(max(0, min(event.y, span)) *
                                 self.max_offset / span))
            return True
        if event.action == 'release' and getattr(self, '_dragging', False):
            self._dragging = False
            return True
        return False

    def on_key(self, key):
        k = str(key)
        moves = {'up': -1, 'k': -1, 'down': 1, 'j': 1,
                 'scrollup': -self.step, 'scrolldown': self.step,
                 'pageup': -self.view_height, 'pagedown': self.view_height,
                 'space': self.view_height}
        if k in moves:
            self.scroll(moves[k])
            return True
        if k in ('home', 'g'):
            self.scroll_to(0)
            return True
        if k in ('end', 'G'):
            self.scroll_to(self.max_offset)
            return True
        return False
