"""
Navigation and structure: tabs, menus (also as context menus and menu
buttons), pagination, sidebar, top bar, toolbar, wizard, accordion,
carousel, tree / object inspector, command palette, split panes, stacks and
the application shell that wires them together.
"""

from flexablelib import _frames as _fx
from flexablelib.layout import _accepts_height, _natural_width, _render_child

from flexablelib_tui import Key

from .base import Button, _Themed, frame, join_columns

_Enter = Key('enter')

__all__ = ['Tabs', 'Menu', 'ContextMenu', 'MenuButton', 'Pagination',
           'Sidebar', 'TopBar', 'Toolbar', 'Wizard', 'Accordion',
           'Carousel', 'Tree', 'CommandPalette', 'Split', 'Stack',
           'VStack', 'GridView', 'AppShell', 'SortControl', 'render_into']


def render_into(child, width, height=None):
    """Lines of any renderable at ``width`` (and ``height`` when it takes
    one)."""
    if child is None:
        return []
    if isinstance(child, str):
        lines = child.split('\n')
    elif height is not None and _accepts_height(child):
        lines = child.render(width=width, height=height).split('\n')
    else:
        text = _render_child(child, width)
        lines = text.split('\n') if text else []
    if height is not None:
        lines = lines[:height]
    return lines


class Tabs(_Themed):
    """
    Tabbed panes: ``tabs`` is a mapping (or pairs) of title to content.
    Left/Right (or 1-9) switch while the tab bar has the focus; the content's
    own components follow it in the focus order. ``on_change(index)``.
    """

    focusable = True
    expand = True
    role = 'tablist'

    def a11y_value(self):
        if not self.tabs:
            return ''
        return '{0} ({1} de {2})'.format(self.tabs[self.index][0],
                                         self.index + 1, len(self.tabs))

    def __init__(self, tabs, index=0, on_change=None, **kwargs):
        super(Tabs, self).__init__(**kwargs)
        self.tabs = list(tabs.items()) if isinstance(tabs, dict) \
            else list(tabs)
        self.index = index
        self.on_change = on_change

    @property
    def current(self):
        return self.tabs[self.index][1] if self.tabs else None

    def children(self):
        return [self.current] if self.current is not None else []

    def form_children(self):
        """Every pane, shown or not (the fields a form collects)."""
        return [c for _, c in self.tabs if not isinstance(c, str)]

    def natural_width(self):
        bar = sum(_fx.visible_width(t) + 3 for t, _ in self.tabs)
        return max([bar] + [_natural_width(c) for _, c in self.tabs])

    def select(self, index):
        index = max(0, min(len(self.tabs) - 1, index))
        if index != self.index:
            self.index = index
            if self.on_change is not None:
                self.on_change(index)
        self.refresh()
        return True

    def on_key(self, key):
        k = str(key)
        if k in ('left', 'right'):
            n = len(self.tabs)
            return self.select((self.index + (1 if k == 'right' else -1)) % n)
        if len(k) == 1 and k.isdigit() and 0 < int(k) <= len(self.tabs):
            return self.select(int(k) - 1)
        return False

    def draw(self, width, height):
        parts = []
        for i, (title, _) in enumerate(self.tabs):
            text = ' {0} '.format(title)
            if i == self.index:
                spec = self.theme.selection if self.focused else 'bold reverse'
                if self._marked():
                    text = ('▸{0}◂' if self._active() else '[{0}]').format(
                        title)
                text = self.paint(text, spec) if self._active() else \
                    ('[>{0}<]' if self.focused else '[{0}]').format(title)
            else:
                text = self.paint(text, self.theme.muted)
            parts.append(text)
        self.hot_parts(0, parts, 1, 0, [
            (lambda i=i: self.select(i)) for i in range(len(parts))])
        bar = self.paint('│', self.theme.border).join(parts) if \
            self._active() else ' '.join(parts)
        out = [bar, self.paint('─' * width, self.theme.accent if self.focused
                               else self.theme.border)]
        room = None if height is None else max(0, height - 2)
        out.extend(render_into(self.current, width, room))
        return out


def _window(comp, out, row, height):
    """The rows of ``out`` that fit ``height``, kept around ``row`` (the
    current item) with ``▲ n``/``▼ n`` lines saying how many are hidden
    above and below; clickable spots move with the rows. ``comp.top`` is
    the first row shown (kept between frames)."""
    total = len(out)
    if not height or total <= height:
        comp.top = 0
        return out
    height = max(1, int(height))
    top = max(0, min(getattr(comp, 'top', 0), total - 1))
    for _ in range(3):
        up = 1 if top > 0 and height > 2 else 0
        room = height - up
        down = 1 if top + room < total and height > 2 else 0
        room -= down
        room = max(1, room)
        if row is not None:
            if row < top:
                top = row
            elif row >= top + room:
                top = row - room + 1
        top = max(0, min(top, total - room))
    up = 1 if top > 0 and height > 2 else 0
    room = height - up
    down = 1 if top + room < total and height > 2 else 0
    room = max(1, room - down)
    comp.top = top
    shown = out[top:top + room]
    arrows = ('^', 'v') if not comp._active() else ('▲', '▼')
    lines = []
    if up:
        lines.append(comp.paint(' {0} {1} más'.format(arrows[0], top),
                                comp.theme.muted))
    lines.extend(shown)
    if down:
        lines.append(comp.paint(' {0} {1} más'.format(
            arrows[1], total - top - room), comp.theme.muted))
    if isinstance(comp._hot, list):
        moved = []
        for r, x0, x1, action in comp._hot:
            if top <= r < top + room:
                moved.append((r - top + up, x0, x1, action))
        if up:
            moved.append((0, 0, None, lambda: comp.scroll_items(-room)))
        if down:
            moved.append((len(lines) - 1, 0, None,
                          lambda: comp.scroll_items(room)))
        comp._hot = moved
    return lines


class Menu(_Themed):
    """
    A vertical menu. ``items``: labels, ``(label, action)``, or dicts with
    ``label``, ``action``, ``shortcut``, ``icon``, ``disabled``; ``'-'`` is a
    separator. Up/Down move (skipping separators and disabled items), Enter
    runs the action, a letter jumps to the item starting with it, and an
    item's ``shortcut`` runs it directly. ``on_select(index, item)``.
    With more items than the height it gets (or ``max_visible``) it shows
    a window around the current item with ``▲ n más`` / ``▼ n más`` lines
    (click them to page); PgUp/PgDn move a page and the wheel scrolls.
    """

    focusable = True
    role = 'menu'

    def a11y_value(self):
        if not self.items or not self._enabled(self.index):
            return ''
        item = self.items[self.index]
        n = [i for i in range(len(self.items)) if self._enabled(i)]
        text = '{0} ({1} de {2})'.format(item['label'],
                                         n.index(self.index) + 1, len(n))
        if item.get('shortcut'):
            text += ', atajo ' + item['shortcut']
        return text

    def __init__(self, items, on_select=None, index=0, max_visible=None,
                 **kwargs):
        super(Menu, self).__init__(**kwargs)
        self.items = [self._item(i) for i in items]
        self.on_select = on_select
        self.index = index
        self.max_visible = max_visible
        self.top = 0
        if self.items and not self._enabled(self.index):
            self._step(1)

    @staticmethod
    def _item(item):
        if item == '-' or item is None:
            return {'separator': True, 'label': ''}
        if isinstance(item, dict):
            return dict(item)
        if isinstance(item, (tuple, list)):
            return {'label': str(item[0]), 'action': item[1] if len(item) > 1
                    else None}
        return {'label': str(item)}

    def _enabled(self, i):
        item = self.items[i]
        return not item.get('separator') and not item.get('disabled')

    def _step(self, step):
        n = len(self.items)
        for _ in range(n):
            self.index = (self.index + step) % n
            if self._enabled(self.index):
                break

    def natural_width(self):
        return max([_fx.visible_width(self._text(i)) for i in self.items] or
                   [8]) + 2

    def _text(self, item):
        text = item['label']
        if item.get('icon'):
            text = item['icon'] + ' ' + text
        return text

    def activate(self, i=None):
        i = self.index if i is None else i
        if not self.items or not self._enabled(i):
            return False
        self.index = i
        item = self.items[i]
        if item.get('action') is not None:
            item['action']()
        if self.on_select is not None:
            self.on_select(i, item)
        self.refresh()
        return True

    def on_key(self, key):
        k = str(key)
        if not self.items:
            return False
        if k in ('up', 'k'):
            self._step(-1)
        elif k in ('down', 'j'):
            self._step(1)
        elif k == 'home':
            self.index = len(self.items) - 1
            self._step(1)
        elif k == 'end':
            self.index = 0
            self._step(-1)
        elif k in ('enter', 'space'):
            return self.activate()
        else:
            for i, item in enumerate(self.items):
                if item.get('shortcut') == k and self._enabled(i):
                    return self.activate(i)
            if len(k) == 1:
                order = list(range(self.index + 1, len(self.items))) + \
                    list(range(0, self.index + 1))
                for i in order:
                    if self._enabled(i) and \
                            self.items[i]['label'][:1].lower() == k.lower():
                        self.index = i
                        self.refresh()
                        return True
            return False
        self.refresh()
        return True

    _page = 5

    def scroll_items(self, delta):
        """Move the current item ``delta`` enabled items (a page)."""
        step = 1 if delta > 0 else -1
        for _ in range(abs(int(delta))):
            before = self.index
            self._step(step)
            if (step > 0 and self.index < before) or \
                    (step < 0 and self.index > before):
                self.index = before
                break
        self.refresh()
        return True

    def handle_key(self, key):
        k = str(key)
        if k in ('pageup', 'pagedown', 'scrollup', 'scrolldown') and \
                self.items and k not in self.bindings:
            page = self._page if k.startswith('page') else 3
            return self.scroll_items(page if k.endswith('down') else -page)
        return super(Menu, self).handle_key(key)

    def draw(self, width, height):
        rows = self.max_visible or height or len(self.items)
        self._page = max(1, rows - 2)
        out = []
        for i in range(len(self.items)):
            item = self.items[i]
            if item.get('separator'):
                out.append(self.paint('─' * width, self.theme.border))
                continue
            shortcut = item.get('shortcut') or ''
            if not item.get('disabled'):
                self.hot(len(out), lambda i=i: self.activate(i))
            room = max(1, width - 2 - (len(shortcut) + 1 if shortcut else 0))
            text = ' ' + _fx.fit_line(self._text(item), room) + \
                (' ' + shortcut if shortcut else '') + ' '
            if item.get('disabled'):
                out.append(self.paint(text, 'dim'))
            elif i == self.index and self.focused:
                out.append(self.mark_current(text, self.theme.selection))
            elif i == self.index and not self._active():
                out.append(text)
            elif i == self.index:
                out.append(self.paint(text, 'underline'))
            else:
                if shortcut:
                    text = text[:-len(shortcut) - 1] + self.paint(
                        shortcut, self.theme.muted) + ' '
                out.append(text)
        return _window(self, out, self.index, rows)


class ContextMenu(Menu):
    """A :class:`Menu` in a framed popup: ``open(app, position)`` shows it,
    Escape or choosing an item closes it."""

    def natural_width(self):
        return super(ContextMenu, self).natural_width() + 2

    def open(self, app, position='center'):
        app.push(self, position=position)
        app.focus(self)
        return self

    def close(self):
        if self.app is not None:
            self.app.pop(self)

    def activate(self, i=None):
        done = super(ContextMenu, self).activate(i)
        if done:
            self.close()
        return done

    def on_key(self, key):
        if str(key) == 'escape':
            self.close()
            return True
        super(ContextMenu, self).on_key(key)
        return True

    def draw(self, width, height):
        inner = super(ContextMenu, self).draw(max(1, width - 2), height)
        self._hot = [(r + 1, x0 + 1, None if x1 is None else x1 + 1, a)
                     for r, x0, x1, a in self._hot]
        return frame(inner, width, None, self.theme.accent, self.paint)


class MenuButton(Button):
    """A button that opens a :class:`ContextMenu` of ``items`` below it."""

    def __init__(self, label, items, **kwargs):
        super(MenuButton, self).__init__(label + ' ▾', **kwargs)
        self.menu = ContextMenu(items, theme=self._theme,
                                use_colors=kwargs.get('use_colors'))

    def press(self):
        self.presses += 1
        if self.app is not None:
            self.menu.open(self.app, position='center')
        return True


class Pagination(_Themed):
    """
    ``‹ 1 … 4 [5] 6 … 20 ›`` with the item range: Left/Right (or PgUp/PgDn)
    change page, Home/End jump. ``on_change(page)``; pages count from 1.
    """

    focusable = True
    role = 'navigation'

    def a11y_value(self):
        return 'página {0} de {1}'.format(self.page, self.pages)

    def __init__(self, total, page_size=20, page=1, on_change=None,
                 **kwargs):
        super(Pagination, self).__init__(**kwargs)
        self.total = max(0, int(total))
        self.page_size = max(1, int(page_size))
        self.page = page
        self.on_change = on_change

    @property
    def pages(self):
        return max(1, -(-self.total // self.page_size))

    def go(self, page):
        page = max(1, min(self.pages, page))
        if page != self.page:
            self.page = page
            if self.on_change is not None:
                self.on_change(page)
        self.refresh()
        return True

    def on_key(self, key):
        k = str(key)
        moves = {'left': -1, 'pageup': -1, 'right': 1, 'pagedown': 1}
        if k in moves:
            return self.go(self.page + moves[k])
        if k == 'home':
            return self.go(1)
        if k == 'end':
            return self.go(self.pages)
        return False

    def natural_width(self):
        return 40

    def numbers(self, slots=7):
        pages, page = self.pages, self.page
        if pages <= slots:
            return list(range(1, pages + 1))
        side = (slots - 3) // 2
        if page <= side + 2:
            return list(range(1, slots - 1)) + [None, pages]
        if page >= pages - side - 1:
            return [1, None] + list(range(pages - slots + 3, pages + 1))
        return [1, None] + list(range(page - side + 1, page + side)) + \
            [None, pages]

    def draw(self, width, height):
        start = (self.page - 1) * self.page_size + 1 if self.total else 0
        end = min(self.total, self.page * self.page_size)
        info = '{0}–{1} de {2}'.format(start, end, self.total)
        parts = [self.paint('‹', self.theme.muted if self.page == 1 else None)]
        actions = [lambda: self.go(self.page - 1)]
        for n in self.numbers():
            actions.append(None if n is None else
                           (lambda n=n: self.go(n)))
            if n is None:
                parts.append(self.paint('…', self.theme.muted))
            elif n == self.page and self._marked() and self._active():
                parts.append(self.paint('[{0}]'.format(n), 'bold underline ' +
                                        self.theme.selection
                                        if self.focused else 'reverse'))
            elif n == self.page:
                spec = 'bold underline ' + self.theme.selection \
                    if self.focused else 'reverse'
                parts.append(self.paint(' {0} '.format(n), spec) if
                             self._active() else
                             ('>{0}<' if self.focused else '[{0}]').format(n))
            else:
                parts.append(str(n))
        parts.append(self.paint('›', self.theme.muted if
                                self.page == self.pages else None))
        actions.append(lambda: self.go(self.page + 1))
        line = ' '.join(parts)
        if _fx.visible_width(line) <= width:
            self.hot_parts(0, parts, 1, 0, actions)
        if _fx.visible_width(line) + len(info) + 3 <= width:
            line += '   ' + self.paint(info, self.theme.muted)
        elif _fx.visible_width(line) > width:
            line = '‹ {0}/{1} ›'.format(self.page, self.pages)
        return [line]


class Sidebar(Menu):
    """
    Navigation down the side: ``sections`` maps a heading to items (as in
    :class:`Menu`). ``collapsed=True`` (or Ctrl-B) shows only the icons.
    It keeps to the height it gets: a window around the current item with
    ``▲`` / ``▼`` lines, the title staying on top.
    """

    role = 'navigation'

    expand = True

    def __init__(self, sections, collapsed=False, title=None, **kwargs):
        items = []
        if isinstance(sections, dict):
            for heading, entries in sections.items():
                if heading:
                    items.append({'label': heading, 'heading': True,
                                  'disabled': True})
                items.extend(entries)
        else:
            items = list(sections)
        super(Sidebar, self).__init__(items, **kwargs)
        self.collapsed = bool(collapsed)
        self.title = title
        self.active = self.index

    def natural_width(self):
        if self.collapsed:
            return 4
        return max(super(Sidebar, self).natural_width(),
                   _fx.visible_width(self.title or '') + 2) + 1

    def activate(self, i=None):
        done = super(Sidebar, self).activate(i)
        if done:
            self.active = self.index
        return done

    def on_key(self, key):
        if str(key) == 'ctrl+b':
            self.collapsed = not self.collapsed
            self.refresh()
            return True
        return super(Sidebar, self).on_key(key)

    def draw(self, width, height):
        head = []
        if self.title and not self.collapsed:
            head.append(self.paint(' ' + self.title, 'bold ' +
                                   self.theme.accent))
            head.append('')
        self._hot_base = len(head)
        out = []
        current = None
        for i, item in enumerate(self.items):
            if i == self.index:
                current = len(out)
            if item.get('heading'):
                if not self.collapsed:
                    out.append(self.paint(' ' + item['label'].upper(),
                                          self.theme.muted))
                continue
            if item.get('separator'):
                out.append(self.paint('─' * width, self.theme.border))
                continue
            icon = item.get('icon') or item['label'][:1]
            if not item.get('disabled'):
                self.hot(len(out), lambda i=i: self.activate(i))
            text = ' ' + icon + ' ' if self.collapsed else \
                ' ' + self._text(item)
            text = _fx.fit_line(text, width)
            if i == self.index and self.focused:
                text = self.mark_current(text, self.theme.selection)
            elif i == self.active and self._marked() and self._active():
                text = self.paint('▌', self.theme.accent) + \
                    self.paint('•' + text[1:], 'bold')
            elif i == self.active:
                text = self.paint('▌', self.theme.accent) + \
                    self.paint(text[1:], 'bold') if self._active() else \
                    '*' + text[1:]
            elif item.get('disabled'):
                text = self.paint(text, 'dim')
            out.append(text)
        rows = self.max_visible or (max(1, height - len(head)) if height
                                    else None)
        if rows:
            self._page = max(1, rows - 2)
        if isinstance(self._hot, list):
            # _window works in the item rows' own coordinates.
            self._hot = [(r - len(head), x0, x1, a)
                         for r, x0, x1, a in self._hot]
        lines = _window(self, out, current, rows)
        if isinstance(self._hot, list):
            self._hot = [(r + len(head), x0, x1, a)
                         for r, x0, x1, a in self._hot]
        self._hot_base = 0
        return head + lines


class TopBar(_Themed):
    """
    The bar across the top: ``title`` (and ``breadcrumbs``) on the left,
    ``actions`` -- text or ``(key, label)`` pairs -- and ``status`` on the
    right.
    """

    def __init__(self, title='', breadcrumbs=None, actions=None, status=None,
                 color=None, **kwargs):
        super(TopBar, self).__init__(**kwargs)
        self.title = title
        self.breadcrumbs = breadcrumbs or []
        self.actions = actions or []
        self.status = status
        self.color = color

    role = 'banner'

    def a11y_name(self):
        return self.a11y_label or self.title or ''

    def a11y_value(self):
        parts = [' › '.join(str(b) for b in self.breadcrumbs)]
        if self.status:
            parts.append(str(self.status))
        return ', '.join(p for p in parts if p)

    def natural_width(self):
        return 60

    def draw(self, width, height):
        color = self.color or 'black on ' + self.theme.accent
        left = ' ' + self.paint(self.title, 'bold')
        if self.breadcrumbs:
            left += '  ' + ' › '.join(str(b) for b in self.breadcrumbs)
        right_parts = []
        for action in self.actions:
            if isinstance(action, (tuple, list)):
                right_parts.append('{0} {1}'.format(action[0], action[1]))
            else:
                right_parts.append(str(action))
        if self.status:
            right_parts.append(str(self.status))
        right = '  '.join(right_parts) + ' '
        room = width - _fx.visible_width(right)
        if room < _fx.visible_width(left):
            left = _fx.truncate(left, max(0, room - 1), '…')
        line = _fx.fit_line(left, max(0, room)) + right
        line = _fx.fit_line(line, width)
        return [self.paint(line, color) if self._active() else line]


class Toolbar(_Themed):
    """
    A row of :class:`Button` s (or ``(label, action)`` pairs): Left/Right
    move between them while one has focus; each keeps its own shortcut.
    """

    role = 'toolbar'

    def __init__(self, buttons, gap=1, align='l', **kwargs):
        super(Toolbar, self).__init__(**kwargs)
        self.buttons = [b if isinstance(b, Button) else
                        Button(b[0], b[1], theme=self._theme,
                               use_colors=kwargs.get('use_colors'))
                        for b in buttons]
        self.gap = gap
        self.align = align

    def children(self):
        return list(self.buttons)

    def natural_width(self):
        return sum(b.natural_width() for b in self.buttons) + \
            self.gap * (len(self.buttons) - 1)

    def handle_key(self, key):
        k = str(key)
        if self.app is not None and self.app.focused in self.buttons and \
                k in ('left', 'right'):
            i = self.buttons.index(self.app.focused)
            j = (i + (1 if k == 'right' else -1)) % len(self.buttons)
            self.app.focus(self.buttons[j])
            return True
        for button in self.buttons:
            if button.shortcut and k == button.shortcut and \
                    not button.disabled:
                return button.press()
        return super(Toolbar, self).handle_key(key)

    def draw(self, width, height):
        parts = [b.render(width=b.natural_width()) for b in self.buttons]
        line = (' ' * self.gap).join(parts)
        return [_fx.fit_line(line, width, self.align)]


class Wizard(_Themed):
    """
    Steps with a stepper on top, the current step's content, and Back /
    Next / Finish buttons. ``steps`` are ``(title, content)`` pairs;
    ``validate(index) -> error or None`` guards Next; ``on_finish()``.
    Ctrl-N / Ctrl-P move too.
    """

    expand = True
    role = 'form'

    def a11y_value(self):
        if not self.steps:
            return ''
        return 'paso {0} de {1}: {2}'.format(self.index + 1, len(self.steps),
                                             self.steps[self.index][0])

    def a11y_state(self):
        return ['invalid'] if self.error else []

    def __init__(self, steps, on_finish=None, validate=None, **kwargs):
        super(Wizard, self).__init__(**kwargs)
        self.steps = list(steps)
        self.index = 0
        self.on_finish = on_finish
        self.check = validate
        self.error = None
        self.finished = False
        colors = kwargs.get('use_colors')
        self.back = Button('‹ Atrás', self.previous, theme=self._theme,
                           use_colors=colors)
        self.next = Button('Siguiente ›', self.advance, kind='primary',
                           theme=self._theme, use_colors=colors)

    def children(self):
        content = self.steps[self.index][1] if self.steps else None
        return ([content] if content is not None else []) + \
            [self.back, self.next]

    def form_children(self):
        """Every step's content (the fields a form collects)."""
        return [c for _, c in self.steps
                if c is not None and not isinstance(c, str)]

    def natural_width(self):
        return max([60] + [_natural_width(c) for _, c in self.steps])

    def previous(self):
        if self.index > 0:
            self.index -= 1
            self.error = None
        self.refresh()
        return True

    def advance(self):
        if self.check is not None:
            self.error = self.check(self.index)
            if self.error:
                self.refresh()
                return True
        if self.index + 1 < len(self.steps):
            self.index += 1
        else:
            self.finished = True
            if self.on_finish is not None:
                self.on_finish()
        self.refresh()
        return True

    def handle_key(self, key):
        k = str(key)
        if k == 'ctrl+n':
            return self.advance()
        if k == 'ctrl+p':
            return self.previous()
        return super(Wizard, self).handle_key(key)

    def draw(self, width, height):
        from .display import Stepper
        stepper = Stepper([t for t, _ in self.steps], self.index,
                          theme=self._theme, use_colors=self.use_colors)
        out = render_into(stepper, width) + ['']
        self.back.disabled = self.index == 0
        last = self.index + 1 == len(self.steps)
        self.next.label = 'Finalizar ✔' if last else 'Siguiente ›'
        content = self.steps[self.index][1] if self.steps else ''
        room = None if height is None else max(0, height - len(out) - 3)
        body = render_into(content, width, room)
        if room is not None:
            body += [''] * (room - len(body))
        out.extend(body)
        if self.error:
            out.append(self.paint('✖ ' + self.error, self.theme.error))
        else:
            out.append('')
        buttons = self.back.render(width=self.back.natural_width()) + '  ' + \
            self.next.render(width=self.next.natural_width())
        out.append(_fx.fit_line(buttons, width, 'r'))
        return out


class Accordion(_Themed):
    """
    Collapsible sections: ``sections`` are ``(title, content)`` pairs. Up/Down
    move between headers, Enter/Space toggle; ``multiple=False`` keeps one
    open at a time. A single section works as a collapsible panel.
    """

    focusable = True
    role = 'tree'

    def a11y_value(self):
        if not self.sections:
            return ''
        return '{0} ({1} de {2})'.format(self.sections[self.index][0],
                                         self.index + 1, len(self.sections))

    def a11y_state(self):
        if not self.sections:
            return []
        return ['expanded' if self.index in self.opened else 'collapsed']

    def _click(self, i):
        self.index = i
        return self.toggle(i)

    def __init__(self, sections, open=(0,), multiple=True, **kwargs):
        super(Accordion, self).__init__(**kwargs)
        self.sections = list(sections.items()) if isinstance(sections, dict) \
            else list(sections)
        self.opened = set(open or ())
        self.multiple = bool(multiple)
        self.index = 0

    def children(self):
        return [c for i, (_, c) in enumerate(self.sections)
                if i in self.opened and not isinstance(c, str)]

    def form_children(self):
        """Every section, open or not (the fields a form collects)."""
        return [c for _, c in self.sections if not isinstance(c, str)]

    def natural_width(self):
        return max([_natural_width(c) + 2 for _, c in self.sections] +
                   [_fx.visible_width(t) + 4 for t, _ in self.sections])

    def toggle(self, i=None):
        i = self.index if i is None else i
        if i in self.opened:
            self.opened.discard(i)
        else:
            if not self.multiple:
                self.opened.clear()
            self.opened.add(i)
        self.refresh()
        return True

    def on_key(self, key):
        k = str(key)
        if k in ('up', 'down') and self.sections:
            self.index = (self.index + (1 if k == 'down' else -1)) % \
                len(self.sections)
            self.refresh()
            return True
        if k in ('enter', 'space'):
            return self.toggle()
        if k == 'right' and self.index not in self.opened:
            return self.toggle()
        if k == 'left' and self.index in self.opened:
            return self.toggle()
        return False

    def draw(self, width, height):
        out = []
        for i, (title, content) in enumerate(self.sections):
            is_open = i in self.opened
            arrow = ('▾' if is_open else '▸') if self._active() else \
                ('v' if is_open else '>')
            head = _fx.fit_line(arrow + ' ' + str(title), width)
            self.hot(len(out), lambda i=i: self._click(i))
            if i == self.index and self.focused:
                head = self.paint(head, self.theme.selection) if \
                    self._active() else '*' + head[1:]
                if self._marked() and self._active():
                    head = self.mark_current(_fx.fit_line(
                        ' ' + arrow + ' ' + str(title), width),
                        self.theme.selection)
            elif i == self.index:
                head = self.paint(head, 'bold underline')
            else:
                head = self.paint(head, 'bold')
            out.append(head)
            if is_open:
                out.extend('  ' + line for line in
                           render_into(content, max(1, width - 2)))
        return out


class Carousel(_Themed):
    """Slides one at a time with ``◀ ● ○ ○ ▶``; Left/Right change slide,
    ``autoplay`` (in ticks) advances on :meth:`tick`."""

    focusable = True
    role = 'region'

    def a11y_value(self):
        return 'diapositiva {0} de {1}'.format(self.index + 1,
                                               len(self.slides))

    def __init__(self, slides, index=0, autoplay=None, **kwargs):
        super(Carousel, self).__init__(**kwargs)
        self.slides = list(slides)
        self.index = index
        self.autoplay = autoplay
        self._ticks = 0

    def natural_width(self):
        return max([_natural_width(s) for s in self.slides] + [20])

    def go(self, step):
        if self.slides:
            self.index = (self.index + step) % len(self.slides)
        self.refresh()
        return True

    def tick(self):
        if self.autoplay:
            self._ticks += 1
            if self._ticks >= self.autoplay:
                self._ticks = 0
                self.go(1)

    def on_key(self, key):
        k = str(key)
        if k in ('left', 'right'):
            return self.go(1 if k == 'right' else -1)
        return False

    def draw(self, width, height):
        room = None if height is None else max(0, height - 1)
        body = render_into(self.slides[self.index] if self.slides else '',
                           width, room)
        dots = ' '.join(('●' if i == self.index else '○') if self._active()
                        else ('*' if i == self.index else '.')
                        for i in range(len(self.slides)))
        nav = self.paint('◀', self.theme.accent if self.focused else
                         self.theme.muted) + ' ' + dots + ' ' + \
            self.paint('▶', self.theme.accent if self.focused else
                       self.theme.muted)
        if self.focused:
            nav = self.paint('[', 'bold') + nav + self.paint(']', 'bold')
        if room is not None:
            body += [''] * (room - len(body))
        left = (width - _fx.visible_width(_fx.strip_ansi(nav))) // 2 + \
            (1 if self.focused else 0)
        segments = ['◀'] + dots.split(' ') + ['▶']
        steps = [-1] + [i - self.index for i in range(len(self.slides))] + [1]
        self.hot_parts(len(body), segments, 1, max(0, left),
                       [(lambda s=s: self.go(s)) for s in steps])
        return body + [_fx.fit_line(nav, width, 'c')]


class Tree(_Themed):
    """
    A collapsible tree. ``data`` is nested dicts / lists (an object
    inspector) or ``(label, children)`` nodes. Up/Down move, Right/Enter
    expand, Left collapses or goes to the parent, ``*`` expands everything.
    ``on_select(path, value)`` runs on Enter for a leaf.
    """

    focusable = True
    expand = True
    role = 'tree'

    def a11y_value(self):
        rows = self.rows()
        if not rows:
            return ''
        path, key, value, depth, branch = rows[min(self.index, len(rows) - 1)]
        text = '{0}, nivel {1}'.format(key, depth + 1)
        if not branch and value is not None:
            text += ': ' + str(value)
        return text

    def a11y_state(self):
        rows = self.rows()
        if not rows:
            return []
        path, _, _, _, branch = rows[min(self.index, len(rows) - 1)]
        if not branch:
            return []
        return ['expanded' if path in self.expanded else 'collapsed']

    def _click(self, i):
        if i == self.index:
            return self.on_key(_Enter)
        self.index = i
        return True

    def __init__(self, data, expanded_depth=1, on_select=None,
                 max_value_width=40, **kwargs):
        super(Tree, self).__init__(**kwargs)
        self.data = data
        self.on_select = on_select
        self.max_value_width = max_value_width
        self.expanded = set()
        self.index = 0
        self.top = 0
        self._expand_to(data, (), expanded_depth)

    @staticmethod
    def _kids(value):
        if isinstance(value, dict):
            return list(value.items())
        if isinstance(value, (list, tuple)) and not (
                len(value) == 2 and isinstance(value[0], str) and
                isinstance(value[1], (list, tuple, dict))):
            return [('[{0}]'.format(i), v) for i, v in enumerate(value)]
        if isinstance(value, tuple) and len(value) == 2:
            return [(c[0], c[1]) if isinstance(c, tuple) else (str(c), None)
                    for c in value[1]]
        return None

    def _expand_to(self, value, path, depth):
        kids = self._kids(value)
        if kids is None or depth <= 0:
            return
        self.expanded.add(path)
        for key, child in kids:
            self._expand_to(child, path + (key,), depth - 1)

    def rows(self):
        out = []

        def walk(value, path, depth):
            for key, child in self._kids(value) or []:
                p = path + (key,)
                kids = self._kids(child)
                out.append((p, key, child, depth, kids is not None))
                if kids is not None and p in self.expanded:
                    walk(child, p, depth + 1)
        walk(self.data, (), 0)
        return out

    def natural_width(self):
        return 40

    def on_key(self, key):
        k = str(key)
        rows = self.rows()
        if not rows:
            return False
        self.index = min(self.index, len(rows) - 1)
        path, _, value, depth, branch = rows[self.index]
        if k in ('up', 'k'):
            self.index = max(0, self.index - 1)
        elif k in ('down', 'j'):
            self.index = min(len(rows) - 1, self.index + 1)
        elif k in ('right', 'l') and branch:
            self.expanded.add(path)
        elif k == 'enter':
            if branch:
                self.expanded.symmetric_difference_update([path])
            elif self.on_select is not None:
                self.on_select(path, value)
        elif k in ('left', 'h'):
            if branch and path in self.expanded:
                self.expanded.discard(path)
            elif len(path) > 1:
                parent = path[:-1]
                self.index = next(i for i, r in enumerate(rows)
                                  if r[0] == parent)
        elif k == '*':
            self._expand_to(self.data, (), 99)
        elif k in ('pageup', 'pagedown'):
            step = 10 if k == 'pagedown' else -10
            self.index = max(0, min(len(rows) - 1, self.index + step))
        else:
            return False
        self.refresh()
        return True

    def _value_text(self, value, branch):
        if branch:
            n = len(self._kids(value) or [])
            kind = '{…}' if isinstance(value, dict) else '[…]'
            return self.paint('{0} {1}'.format(kind, n), self.theme.muted)
        if value is None:
            return self.paint('null', self.theme.muted)
        if isinstance(value, bool):
            return self.paint(str(value).lower(), self.theme.accent)
        if isinstance(value, (int, float)):
            return self.paint(str(value), self.theme.warning)
        return self.paint(_fx.truncate('"{0}"'.format(value),
                                       self.max_value_width, '…'),
                          self.theme.success)

    def draw(self, width, height):
        rows = self.rows()
        view = height or len(rows)
        self.index = min(self.index, max(0, len(rows) - 1))
        if self.index < self.top:
            self.top = self.index
        if self.index >= self.top + view:
            self.top = self.index - view + 1
        out = []
        for i in range(self.top, min(len(rows), self.top + view)):
            path, key, value, depth, branch = rows[i]
            if branch:
                arrow = ('▾' if path in self.expanded else '▸') if \
                    self._active() else ('-' if path in self.expanded else '+')
            else:
                arrow = ' '
            label = '  ' * depth + arrow + ' ' + str(key)
            self.hot(len(out), lambda i=i: self._click(i))
            line = _fx.fit_line(label, min(width, _fx.visible_width(label)))
            if i == self.index and self.focused:
                line = self.mark_current(line, self.theme.selection)
            value_text = self._value_text(value, branch) if \
                isinstance(self.data, (dict, list)) or branch else ''
            out.append(line + (': ' if value_text and not branch else '  ') +
                       value_text if value_text else line)
        return out


class CommandPalette(_Themed):
    """
    A search box over commands -- ``(label, action)`` pairs or dicts with
    ``label``, ``action``, ``hint``, ``keywords`` -- matched by fuzzy
    subsequence, best first. Up/Down choose, Enter runs, Escape closes.
    Open it with ``open(app)`` (bind it to ``ctrl+k`` or ``/``).
    """

    focusable = True
    role = 'dialog'

    def a11y_name(self):
        return self.a11y_label or self.title or ''

    def a11y_value(self):
        items = self.matches()
        text = 'búsqueda: ' + (self.query or '(vacía)')
        if items:
            i = min(self.index, len(items) - 1)
            text += ', {0} ({1} de {2})'.format(items[i]['label'], i + 1,
                                                 len(items))
        else:
            text += ', sin resultados'
        return text

    def _run(self, i):
        self.index = i
        self.on_key(_Enter)
        return True

    def __init__(self, commands, placeholder='Buscar…', max_visible=8,
                 title='Comandos', **kwargs):
        super(CommandPalette, self).__init__(**kwargs)
        self.commands = [c if isinstance(c, dict) else
                         {'label': c[0], 'action': c[1] if len(c) > 1
                          else None} for c in commands]
        self.placeholder = placeholder
        self.max_visible = max_visible
        self.title = title
        self.query = ''
        self.index = 0
        self.ran = []

    def natural_width(self):
        return 60

    @staticmethod
    def score(query, text):
        """Lower is better; None when ``query`` is not a subsequence."""
        q, t = query.lower(), text.lower()
        if not q:
            return 0
        if q in t:
            return t.index(q)
        pos, gaps, last = 0, 0, -1
        for ch in q:
            pos = t.find(ch, pos)
            if pos < 0:
                return None
            if last >= 0:
                gaps += pos - last - 1
            last = pos
            pos += 1
        return 100 + gaps

    def matches(self):
        scored = []
        for n, command in enumerate(self.commands):
            text = command['label'] + ' ' + ' '.join(
                command.get('keywords', []))
            s = self.score(self.query, text)
            if s is not None:
                scored.append((s, n, command))
        scored.sort(key=lambda x: (x[0], x[1]))
        return [c for _, _, c in scored]

    def open(self, app):
        self.query = ''
        self.index = 0
        app.push(self, position='top')
        app.focus(self)
        return True

    def close(self):
        if self.app is not None:
            self.app.pop(self)

    def on_key(self, key):
        k = str(key)
        items = self.matches()
        if k == 'escape':
            self.close()
        elif k == 'up':
            self.index = max(0, self.index - 1)
        elif k == 'down':
            self.index = min(max(0, len(items) - 1), self.index + 1)
        elif k == 'enter':
            if items:
                command = items[min(self.index, len(items) - 1)]
                self.ran.append(command['label'])
                self.close()
                if command.get('action') is not None:
                    command['action']()
        elif k == 'backspace':
            self.query = self.query[:-1]
            self.index = 0
        elif k == 'paste' or key.is_printable or k == 'space':
            self.query += key.char or ' '
            self.index = 0
        elif k in ('tab', 'shift+tab'):
            return True
        else:
            return False
        self.refresh()
        return True

    def draw(self, width, height):
        inner = max(1, width - 4)
        query = self.query or self.paint(self.placeholder, self.theme.muted)
        lines = [self.paint('› ', self.theme.accent) + query +
                 ((self.cursor(' ') if self._active() else '_')
                  if self.focused else ''),
                 self.paint('─' * inner, self.theme.border)]
        items = self.matches()
        for i, command in enumerate(items[:self.max_visible]):
            hint = command.get('hint') or ''
            room = max(1, inner - len(hint) - 1)
            text = _fx.fit_line(' ' + command['label'], room) + ' ' + hint
            if i == self.index:
                text = self.mark_current(_fx.fit_line(text, inner),
                                      self.theme.selection)
            elif hint:
                text = text[:-len(hint)] + self.paint(hint, self.theme.muted)
            self.hot(len(lines) + 1, lambda i=i: self._run(i), 2,
                     width - 1)
            lines.append(text)
        if not items:
            lines.append(self.paint(' Sin resultados', self.theme.muted))
        return frame([' ' + l for l in lines], width, self.title,
                     self.theme.accent, self.paint)


class Split(_Themed):
    """
    Two panes side by side (``direction='horizontal'``) or stacked
    (``'vertical'``), divided at ``ratio``; Ctrl-Left/Right (Ctrl-Up/Down)
    move the divider.
    """

    expand = True

    def __init__(self, first, second, ratio=0.5, direction='horizontal',
                 divider=True, minimum=8, **kwargs):
        super(Split, self).__init__(**kwargs)
        self.first = first
        self.second = second
        self.ratio = ratio
        self.direction = direction
        self.divider = bool(divider)
        self.minimum = minimum
        self._geometry = None
        self.dragging = False

    role = 'group'

    def children(self):
        return [self.first, self.second]

    def on_mouse(self, event):
        """Drag the divider with the mouse."""
        if self._geometry is None or event.button != 0:
            return False
        vertical, at, size = self._geometry
        pos = event.y if vertical else event.x
        if event.action == 'press':
            self.dragging = abs(pos - at) <= 1
            return self.dragging
        if event.action == 'drag' and self.dragging:
            self.ratio = max(0.1, min(0.9, float(pos) / max(1, size)))
            self.refresh()
            return True
        if event.action == 'release':
            was, self.dragging = self.dragging, False
            return was
        return False

    def natural_width(self):
        if self.direction == 'vertical':
            return max(_natural_width(self.first),
                       _natural_width(self.second))
        return _natural_width(self.first) + _natural_width(self.second) + 3

    def handle_key(self, key):
        k = str(key)
        grow = {'ctrl+right': 0.05, 'ctrl+left': -0.05, 'ctrl+down': 0.05,
                'ctrl+up': -0.05}
        horizontal = self.direction != 'vertical'
        if k in grow and (('left' in k or 'right' in k) == horizontal):
            self.ratio = max(0.1, min(0.9, self.ratio + grow[k]))
            self.refresh()
            return True
        return super(Split, self).handle_key(key)

    def draw(self, width, height):
        if self.direction == 'vertical':
            total = height or (len(render_into(self.first, width)) +
                               len(render_into(self.second, width)) + 1)
            avail = total - (1 if self.divider else 0)
            top_h = max(1, min(avail - 1, int(round(avail * self.ratio))))
            top = render_into(self.first, width, top_h)
            top += [''] * (top_h - len(top))
            bottom = render_into(self.second, width, avail - top_h)
            divider = '━' if self.dragging else '─'
            mid = [self.paint(divider * width, self.theme.border)] \
                if self.divider else []
            self._geometry = (True, top_h, avail)
            return top + mid + bottom
        gap = 3 if self.divider else 1
        avail = max(2, width - gap)
        left_w = max(min(self.minimum, avail - 1), min(
            avail - self.minimum, int(round(avail * self.ratio))))
        left_w = max(1, min(avail - 1, left_w))
        right_w = avail - left_w
        left = render_into(self.first, left_w, height)
        right = render_into(self.second, right_w, height)
        rows = height or max(len(left), len(right))
        self._geometry = (False, left_w + gap // 2, avail)
        sep = ' ' + self.paint('┃' if self.dragging else '│',
                               self.theme.border) + ' ' if \
            self.divider else ' '
        out = []
        for k in range(rows):
            out.append(_fx.fit_line(left[k] if k < len(left) else '', left_w) +
                       sep + (right[k] if k < len(right) else ''))
        return out


class Stack(_Themed):
    """
    Children one below the other (``direction='vertical'``) or side by side
    (``'horizontal'``, equal widths unless ``widths`` given), with ``gap``.
    A horizontal stack with ``min_width`` wraps onto more rows when its
    children would get narrower than that (four cards become 2 x 2, then a
    column).
    """

    role = 'group'

    def __init__(self, children, direction='vertical', gap=0, widths=None,
                 min_width=None, **kwargs):
        super(Stack, self).__init__(**kwargs)
        self.items = list(children)
        self.direction = direction
        self.gap = max(0, int(gap))
        self.widths = widths
        self.min_width = min_width

    def children(self):
        return list(self.items)

    def natural_width(self):
        widths = [_natural_width(c) for c in self.items] or [0]
        if self.direction == 'horizontal':
            return sum(widths) + self.gap * (len(widths) - 1)
        return max(widths)

    def _row(self, items, slots, width, height):
        if self.widths:
            widths = list(self.widths)
        else:
            each = (width - self.gap * (slots - 1)) // slots
            widths = [each] * slots
            widths[-1] = width - self.gap * (slots - 1) - each * (slots - 1)
        widths = widths[:len(items)]
        blocks = [render_into(c, max(1, w), height)
                  for c, w in zip(items, widths)]
        return join_columns(blocks, widths, self.gap)

    def draw(self, width, height):
        if self.direction == 'horizontal':
            per_row = len(self.items) or 1
            if self.min_width and not self.widths:
                per_row = max(1, min(per_row, (width + self.gap) //
                                     (int(self.min_width) + self.gap)))
                # Balanced rows: 4 cards that fit 3 across become 2 x 2.
                rows = -(-len(self.items) // per_row)
                per_row = -(-len(self.items) // rows)
            if per_row < len(self.items):
                out = []
                for start in range(0, len(self.items), per_row):
                    if start:
                        out.extend([''] * self.gap)
                    out.extend(self._row(self.items[start:start + per_row],
                                         per_row, width, None))
                return out
            return self._row(self.items, per_row, width, height)
        out = []
        for i, child in enumerate(self.items):
            if i and self.gap:
                out.extend([''] * self.gap)
            out.extend(render_into(child, width))
        return out



def _contains(node, target, depth=0):
    """Whether ``target`` is ``node`` or somewhere inside it."""
    if node is target:
        return True
    if depth > 64:
        return False
    from flexablelib_tui.app import _child_nodes
    return any(_contains(c, target, depth + 1) for c in _child_nodes(node))


def _share(room, weights, lows, highs):
    """Split ``room`` rows by ``weights`` on top of ``lows``, each capped
    at ``highs`` (None: no cap); leftover rows go to the largest
    remainders."""
    sizes = list(lows)
    open_ = [i for i, w in enumerate(weights) if w > 0]
    while room > 0 and open_:
        total = float(sum(weights[i] for i in open_))
        shares = {i: room * weights[i] / total for i in open_}
        given = 0
        capped = []
        for i in open_:
            add = int(shares[i])
            if highs[i] is not None and sizes[i] + add >= highs[i]:
                add = max(0, highs[i] - sizes[i])
                capped.append(i)
            sizes[i] += add
            given += add
        room -= given
        if capped:
            open_ = [i for i in open_ if i not in capped]
            continue
        order = sorted(open_, key=lambda i: shares[i] - int(shares[i]),
                       reverse=True)
        for i in order:
            if room <= 0:
                break
            if highs[i] is None or sizes[i] < highs[i]:
                sizes[i] += 1
                room -= 1
        break
    return sizes


class VStack(_Themed):
    """
    Children one below the other that share the height the stack gets.

    ``weights`` (one per child) split the rows left over: a child with
    weight 0 keeps its own height, the others grow in proportion. By
    default (3.7.0) children with ``expand`` -- a ``DataTable(fill=True)``,
    a ``ScrollView``, a ``Sidebar``, ``Tabs`` -- get weight 1, the rest 0. ``min_heights`` / ``max_heights`` (one per child, None for
    no limit) bound each one; ``gap`` puts blank rows between them and
    ``height`` fixes the stack's own height (otherwise it takes its slot's).
    When the children need more rows than there are, the stack scrolls and
    follows the focus: whenever another component inside takes the focus,
    the child holding it is brought into view (Tab reaches the children out
    of view too). The wheel and PgUp/PgDn (when the focused child does not
    use them) scroll it; ``scrollbar=True`` shows a bar on the right while
    it scrolls.
    """

    role = 'group'
    expand = True

    def __init__(self, children, weights=None, min_heights=None,
                 max_heights=None, gap=0, height=None, scrollbar=True,
                 follow_focus=True, step=3, **kwargs):
        super(VStack, self).__init__(**kwargs)
        self.items = list(children)
        n = len(self.items)

        def per_child(values, default, name):
            values = list(values) if values is not None else [default] * n
            if len(values) != n:
                raise ValueError('{0} needs one value per child ({1})'
                                 .format(name, n))
            return values
        if weights is None:
            # Children that fill their slot (expand: tables with fill=True,
            # scroll views, sidebars, tabs) share the rows left over.
            weights = [1 if getattr(c, 'expand', False) else 0
                       for c in self.items]
        self.weights = [max(0.0, float(w or 0))
                        for w in per_child(weights, 0, 'weights')]
        self.min_heights = [max(0, int(v or 0)) for v in
                            per_child(min_heights, 0, 'min_heights')]
        self.max_heights = [None if v is None else max(0, int(v)) for v in
                            per_child(max_heights, None, 'max_heights')]
        self.gap = max(0, int(gap))
        self.height = None if height is None else max(1, int(height))
        self.scrollbar = bool(scrollbar)
        self.follow_focus = bool(follow_focus)
        self.step = max(1, int(step))
        self.offset = 0
        self.total = 0
        self.view_height = 0
        self.heights = []
        self._followed = None
        self._blocks = []

    def children(self):
        return list(self.items)

    def natural_width(self):
        return max([_natural_width(c) for c in self.items] or [0]) + \
            (1 if self.scrollbar else 0)

    @property
    def max_offset(self):
        return max(0, self.total - self.view_height)

    def scroll_to(self, offset):
        self.offset = max(0, min(int(offset), self.max_offset))
        self.refresh()

    def scroll(self, delta):
        self.scroll_to(self.offset + delta)

    def _clamp(self, i, rows):
        rows = max(rows, self.min_heights[i])
        high = self.max_heights[i]
        return rows if high is None else min(rows, high)

    def _layout(self, width, height):
        """The height of every child and their rendered lines."""
        naturals = [len(render_into(c, width)) for c in self.items]
        gaps = self.gap * max(0, len(self.items) - 1)
        if height is None:
            sizes = [self._clamp(i, naturals[i])
                     for i in range(len(self.items))]
        else:
            fixed = [self._clamp(i, naturals[i]) if not self.weights[i]
                     else self.min_heights[i]
                     for i in range(len(self.items))]
            room = height - gaps - sum(fixed)
            sizes = _share(room, self.weights, fixed, self.max_heights)
        blocks = []
        for child, rows in zip(self.items, sizes):
            lines = render_into(child, width, rows) if rows else []
            blocks.append(lines + [''] * (rows - len(lines)))
        return sizes, blocks

    def _holder(self):
        app = self.app
        target = getattr(app, 'focused', None) if app is not None else None
        if target is None:
            return None
        for i, child in enumerate(self.items):
            if _contains(child, target):
                return i
        return None

    def draw(self, width, height):
        h = self.height or height
        sizes, blocks = self._layout(width, h)
        lines = []
        starts = []
        for i, block in enumerate(blocks):
            if i and self.gap:
                lines.extend([''] * self.gap)
            starts.append(len(lines))
            lines.extend(block)
        overflow = h is not None and len(lines) > h
        inner = width
        if overflow and self.scrollbar and width > 1:
            inner = width - 1
            sizes, blocks = self._layout(inner, h)
            lines, starts = [], []
            for i, block in enumerate(blocks):
                if i and self.gap:
                    lines.extend([''] * self.gap)
                starts.append(len(lines))
                lines.extend(block)
        self.heights = sizes
        self.total = len(lines)
        self.view_height = h if h is not None else len(lines)
        if not overflow:
            self.offset = 0
            return lines
        if self.follow_focus:
            target = getattr(self.app, 'focused', None) if self.app else None
            if target is not self._followed:
                self._followed = target
                i = self._holder()
                if i is not None:
                    top, size = starts[i], sizes[i]
                    if top < self.offset or size > h:
                        self.offset = top
                    elif top + size > self.offset + h:
                        self.offset = top + size - h
        self.offset = max(0, min(self.offset, self.max_offset))
        visible = lines[self.offset:self.offset + h]
        if not (self.scrollbar and inner < width):
            return visible
        thumb = max(1, h * h // self.total)
        top = (h - thumb) * self.offset // max(1, self.max_offset)
        bar = []
        for k in range(h):
            on = top <= k < top + thumb
            bar.append(self.paint('┃' if on else '│', self.theme.border)
                       if self._active() and not self._marked() else
                       ('█' if on else '│'))
        return [_fx.fit_line(line, inner) + mark
                for line, mark in zip(visible, bar)]

    def a11y_value(self):
        if self.total <= self.view_height:
            return ''
        return 'líneas {0}-{1} de {2}'.format(
            self.offset + 1, min(self.total, self.offset + self.view_height),
            self.total)

    def on_key(self, key):
        k = str(key)
        moves = {'scrollup': -self.step, 'scrolldown': self.step,
                 'pageup': -max(1, self.view_height),
                 'pagedown': max(1, self.view_height)}
        if k in moves and self.total > self.view_height:
            self.scroll(moves[k])
            return True
        return False

_COMPONENT_KWARGS = ('theme', 'use_colors', 'bindings', 'disabled',
                     'a11y_label', 'description', 'role', 'tab_index')


class GridView(_Themed):
    """
    A :class:`flexablelib.Grid` as a component, with an accessible name and
    role: ``children`` and every other keyword (``columns``, ``min_width``,
    ``gap``, ``border``, ``column_widths``...) are the grid's; ``title``
    (drawn above it, bold) or ``a11y_label`` names it for screen readers,
    and ``role`` is ``'group'`` unless given. Its components keep their
    focus order. :meth:`audit` checks the grid and everything inside it
    (role, label, focus shown without colour) and returns
    :class:`flexablelib_tui.accessibility.AuditIssue` s.
    """

    role = 'group'
    expand = False

    def __init__(self, children, title=None, **kwargs):
        own = dict((k, kwargs.pop(k)) for k in _COMPONENT_KWARGS
                   if k in kwargs)
        super(GridView, self).__init__(**own)
        self.items = list(children)
        self.title = title
        self.options = kwargs

    def a11y_name(self):
        if self.a11y_label:
            return str(self.a11y_label)
        return self.title or ''

    def a11y_value(self):
        return '{0} elementos'.format(len(self.items))

    def children(self):
        from flexablelib.layout import GridCell
        kids = []
        for item in self.items:
            if isinstance(item, GridCell):
                item = item.child
            elif isinstance(item, tuple) and item:
                item = item[0]
            if item is not None and not isinstance(item, str):
                kids.append(item)
        return kids

    def grid(self):
        """The :class:`flexablelib.Grid` drawn."""
        from flexablelib.layout import Grid
        return Grid(self.items, **self.options)

    def natural_width(self):
        return _natural_width(self.grid())

    def draw(self, width, height):
        out = []
        if self.title:
            out.append(self.paint(self.title, 'bold'))
        room = None if height is None else max(1, height - len(out))
        grid = self.grid()
        text = grid.render(width=width, height=room) if room else \
            grid.render(width=width)
        out.extend(text.split('\n') if text else [])
        return out

    def audit(self, width=40, check_focus=True):
        """Accessibility problems of the grid and of every component in
        it (see :func:`flexablelib_tui.accessibility.audit`)."""
        from flexablelib_tui import accessibility as a11y
        from flexablelib_tui.app import Component, _child_nodes
        found = []
        stack = list(reversed(self.children()))
        seen = set()
        while stack:
            node = stack.pop()
            if id(node) in seen:
                continue
            seen.add(id(node))
            if isinstance(node, Component):
                found.append(node)
            stack.extend(reversed(_child_nodes(node)))
        return a11y.audit([self] + found, width=width,
                          check_focus=check_focus)


class SortControl(_Themed):
    """
    Choose the sort field and direction: Left/Right pick the field, Space or
    Enter flips ascending/descending. ``on_change(field, descending)``.
    """

    focusable = True
    role = 'radiogroup'

    def a11y_value(self):
        return '{0}, {1}'.format(self.field, 'descendente' if self.descending
                                 else 'ascendente')

    def _click(self, f):
        if f == self.field:
            self.descending = not self.descending
        else:
            self.field = f
        return self._changed()

    def __init__(self, fields, field=None, descending=False, on_change=None,
                 **kwargs):
        super(SortControl, self).__init__(**kwargs)
        self.fields = list(fields)
        self.field = field if field is not None else (self.fields[0] if
                                                       self.fields else None)
        self.descending = bool(descending)
        self.on_change = on_change

    def natural_width(self):
        return sum(len(str(f)) + 3 for f in self.fields) + 8

    def _changed(self):
        if self.on_change is not None:
            self.on_change(self.field, self.descending)
        self.refresh()
        return True

    def on_key(self, key):
        k = str(key)
        if k in ('left', 'right') and self.fields:
            i = self.fields.index(self.field) if self.field in self.fields \
                else 0
            self.field = self.fields[(i + (1 if k == 'right' else -1)) %
                                     len(self.fields)]
            return self._changed()
        if k in ('space', 'enter'):
            self.descending = not self.descending
            return self._changed()
        return False

    def draw(self, width, height):
        parts = [self.paint('Ordenar:', self.theme.muted)]
        for f in self.fields:
            if f == self.field:
                arrow = '↓' if self.descending else '↑'
                text = '{0} {1}'.format(f, arrow)
                parts.append(self.paint(' ' + text + ' ', 'bold underline ' +
                                        self.theme.selection
                                        if self.focused else 'reverse') if
                             self._active() else
                             ('>{0}<' if self.focused else '[{0}]').format(
                                 text))
            else:
                parts.append(str(f))
        self.hot_parts(0, parts, 1, 0, [None] + [
            (lambda f=f: self._click(f)) for f in self.fields])
        return [' '.join(parts)]


class AppShell(_Themed):
    """
    The frame of an application: ``sidebar`` on the left, ``topbar`` above
    the content, ``content`` the current page. ``pages`` maps sidebar labels
    to content, so choosing an item in the sidebar shows its page. The
    sidebar hides itself below ``sidebar_below`` columns (Ctrl-B shows it).
    """

    expand = True
    role = 'application'

    def a11y_name(self):
        if self.a11y_label:
            return self.a11y_label
        return getattr(self.topbar, 'title', '') or ''

    def __init__(self, content=None, sidebar=None, topbar=None, pages=None,
                 sidebar_below=70, **kwargs):
        super(AppShell, self).__init__(**kwargs)
        self.content = content
        self.sidebar = sidebar
        self.topbar = topbar
        self.pages = dict(pages or {})
        self.sidebar_below = sidebar_below
        self.show_sidebar = True
        self.force_sidebar = False
        self._width = 200
        if sidebar is not None and self.pages:
            previous = sidebar.on_select

            def choose(index, item):
                self.open_page(item['label'])
                if previous is not None:
                    previous(index, item)
            sidebar.on_select = choose
            if content is None:
                first = next((i for i in sidebar.items
                              if i['label'] in self.pages), None)
                if first is not None:
                    self.content = self.pages[first['label']]

    def open_page(self, name):
        if name in self.pages:
            self.content = self.pages[name]
            if isinstance(self.topbar, TopBar):
                self.topbar.breadcrumbs = [name]
        self.refresh()

    def sidebar_visible(self, width=None):
        width = self._width if width is None else width
        return self.sidebar is not None and self.show_sidebar and (
            width >= self.sidebar_below or self.force_sidebar)

    def children(self):
        kids = []
        if self.sidebar_visible():
            kids.append(self.sidebar)
        if self.topbar is not None:
            kids.append(self.topbar)
        if self.content is not None:
            kids.append(self.content)
        return kids

    def natural_width(self):
        return 100

    def handle_key(self, key):
        if str(key) == 'ctrl+b' and self.sidebar is not None:
            if self._width < self.sidebar_below:
                self.force_sidebar = not self.force_sidebar
                self.show_sidebar = True
            else:
                self.show_sidebar = not self.show_sidebar
            self.refresh()
            return True
        return super(AppShell, self).handle_key(key)

    def draw(self, width, height):
        self._width = width
        top = render_into(self.topbar, width) if self.topbar is not None \
            else []
        rows = None if height is None else max(0, height - len(top))
        if self.sidebar_visible(width):
            side_w = min(max(4, _natural_width(self.sidebar)), width // 3)
            side = render_into(self.sidebar, side_w, rows)
            main_w = max(1, width - side_w - 1)
            main = render_into(self.content, main_w, rows)
            n = rows or max(len(side), len(main))
            side += [''] * (n - len(side))
            bar = self.paint('│', self.theme.border)
            body = [_fx.fit_line(side[k], side_w) + bar +
                    (main[k] if k < len(main) else '') for k in range(n)]
        else:
            body = render_into(self.content, width, rows)
        return top + body
