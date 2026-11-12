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
from flexablelib.layout import Grid, GridCell, _render_child, render_width

from .keys import Key
from .screen import Live, Screen

__all__ = ['Component', 'App', 'ScrollView', 'overlay']

# Frame counter: a component drawn in the latest frame is on screen, and only
# components on screen take focus.
_FRAME = [0]


class Component(object):
    """
    Base class for interactive pieces.

    Subclasses implement ``draw(width, height)`` returning a list of lines
    (or one string) and, when they react to keys, ``on_key(key)``. Set
    ``focusable = True`` to take focus; ``self.focused`` says whether they
    have it. ``natural_width()`` is the width a layout should offer.
    ``expand = True`` makes the component fill the height it is given.
    """

    focusable = False
    expand = False
    use_colors = None

    def __init__(self, bindings=None, use_colors=None, disabled=False):
        self.focused = False
        self.app = None
        self.parent = None
        self.disabled = bool(disabled)
        self.bindings = dict(bindings or {})
        if use_colors is not None:
            self.use_colors = use_colors
        self._drawn = -1

    # -- colour -------------------------------------------------------------

    def _active(self):
        if self.use_colors is None:
            return supports_color()
        return bool(self.use_colors)

    def paint(self, text, spec):
        """``text`` in colour ``spec`` (a flexablelib colour spec)."""
        if not text or not spec or not self._active():
            return text
        prefix = parse_spec(spec)
        if not prefix:
            return text
        return prefix + text.replace(RESET, RESET + prefix) + RESET

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
        return '\n'.join(_fx.fit_lines(lines, width))

    def __str__(self):
        return self.render()

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
    if isinstance(node, App):
        return [node.screen] + list(node.layers)
    return []


class App(object):
    """
    An interactive terminal application.

    >>> app = App(body=grid, header=StatusBar('Panel'), footer=KeyHints(...),
    ...           bindings={'q': app.exit, 'f5': reload})
    >>> app.run()

    ``bindings`` maps keys to callables (``None`` removes a default one). The
    defaults: ``ctrl+c`` quits, ``tab`` / ``shift+tab`` move the focus.
    ``interval`` (seconds) calls ``on_tick(app)`` that often and redraws, for
    clocks and live data. ``mouse=True`` enables wheel and click reports.
    """

    def __init__(self, body=None, header=None, footer=None, bindings=None,
                 interval=None, on_tick=None, mouse=False, stream=None,
                 terminal=None):
        self.screen = Screen(body=body, header=header, footer=footer)
        self.layers = []
        self.focused = None
        self.running = False
        self.result = None
        self.interval = interval
        self.on_tick = on_tick
        self.mouse = bool(mouse)
        self.stream = stream
        self.terminal = terminal
        self.frames = 0
        self.last_frame = ''
        self._dirty = True
        self._focus_stack = []
        self.bindings = {'ctrl+c': self.exit, 'tab': self.focus_next,
                         'shift+tab': self.focus_previous}
        for key, action in (bindings or {}).items():
            if action is None:
                self.bindings.pop(key, None)
            else:
                self.bindings[key] = action

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

    def focusables(self):
        """Components that can take focus now, in screen order."""
        root = self.layers[-1] if self.layers else self.screen
        return [n for n in self.walk(root)
                if isinstance(n, Component) and n.can_focus and n.on_screen]

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
        items = self.focusables()
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

    def push(self, layer):
        """Show ``layer`` over the screen; it keeps the focus until popped."""
        self._focus_stack.append(self.focused)
        self.layers.append(layer)
        for node in self.walk(layer):
            if isinstance(node, Component):
                node.app = self
        self.focus(None)
        self._dirty = True
        return layer

    def pop(self, layer=None):
        """Close the top dialog (or ``layer``) and give the focus back."""
        if not self.layers:
            return None
        if layer is None or layer is self.layers[-1]:
            removed = self.layers.pop()
        else:
            self.layers.remove(layer)
            removed = layer
        previous = self._focus_stack.pop() if self._focus_stack else None
        self.focus(previous)
        self._dirty = True
        return removed

    # -- drawing ------------------------------------------------------------

    def refresh(self):
        """Mark the screen for redrawing."""
        self._dirty = True

    def _compose(self, width, height):
        _FRAME[0] += 1
        for node in self.walk():     # give every component its app
            pass
        lines = self.screen.render(width=width, height=height).split('\n')
        for layer in self.layers:
            want = getattr(layer, 'natural_width', lambda: width - 4)()
            w = max(1, min(width - 2, want))
            text = layer.render(width=w) if not hasattr(layer, 'height') or \
                getattr(layer, 'height') is None else \
                layer.render(width=w, height=min(height - 2, layer.height))
            top = text.split('\n') if text else []
            top = top[:height]
            x = max(0, (width - w) // 2)
            y = max(0, (height - len(top)) // 2)
            lines = overlay(lines, top, x, y, width)
        return lines

    def render(self, width=None, height=None):
        width = render_width(width)
        if height is None:
            height = self.screen.height
        lines = self._compose(width, height)
        candidates = self.focusables()
        if self.focused not in candidates:
            # First frame, or the focused component left the screen (a
            # narrower layout hid it, a dialog closed): focus the first one.
            self.focus(candidates[0] if candidates else None)
            if self.focused is not None:
                lines = self._compose(width, height)
        self.last_frame = '\n'.join(lines)
        self.frames += 1
        self._dirty = False
        return self.last_frame

    # -- input --------------------------------------------------------------

    def dispatch(self, key):
        """Route one key; returns True when something used it."""
        if not isinstance(key, Key):
            key = Key(str(key), str(key) if len(str(key)) == 1 else '')
        self._dirty = True
        if str(key) == 'ctrl+c' and 'ctrl+c' in self.bindings:
            self.bindings['ctrl+c']()
            return True
        node = self.focused
        seen = set()
        while node is not None and id(node) not in seen:
            seen.add(id(node))
            if isinstance(node, Component) and node.handle_key(key):
                return True
            node = getattr(node, 'parent', None)
        if self.layers:
            top = self.layers[-1]
            if isinstance(top, Component) and top is not self.focused and \
                    id(top) not in seen and top.handle_key(key):
                return True
        action = self.bindings.get(str(key))
        if action is not None:
            result = action()
            return result is not False
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

    def _run_terminal(self, size, max_frames):   # pragma: no cover - needs a tty
        from .terminal import Terminal
        terminal = self.terminal or Terminal(mouse=self.mouse)
        width, height = size or (None, None)
        live = Live(self, stream=self.stream, width=width, height=height)
        self.running = True
        next_tick = time.monotonic() + (self.interval or 0)
        with terminal, live:
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
                    if max_frames is not None and self.frames >= max_frames:
                        break
        self.live = live
        return self.result


class ScrollView(Component):
    """
    A scrollable viewport.

    ``content`` is text, a list of lines, or any renderable (drawn at the
    view's width minus the scroll bar). ``height`` fixes the view's height;
    otherwise it takes the height its slot gives it. ``follow=True`` keeps
    the view at the bottom while it is there (for logs).
    """

    focusable = True
    expand = True

    def __init__(self, content='', height=None, follow=False, scrollbar=True,
                 color='bright_black', focus_color='cyan', step=3, **kwargs):
        super(ScrollView, self).__init__(**kwargs)
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

    def draw(self, width, height):
        h = self.height or height or self.view_height
        inner = max(1, width - 1) if self.scrollbar else width
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
                for k in range(h)]

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
