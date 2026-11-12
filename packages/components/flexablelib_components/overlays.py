"""
Dialogs and overlays: a modal with buttons, confirm and prompt dialogs, a
loading overlay, a popover, and the help line that shows the focused
component's hint (the terminal's tooltip).
"""

from flexablelib import _frames as _fx

from .base import Button, _Themed, frame
from .display import Spinner
from .inputs import TextInput
from .navigation import render_into

__all__ = ['Modal', 'ConfirmDialog', 'PromptDialog', 'LoadingOverlay',
           'Popover', 'HelpLine']


class Modal(_Themed):
    """
    A framed dialog over the screen: ``content`` and a row of ``buttons``
    (``(label, action)`` pairs or :class:`Button` s; an action returning
    anything but False closes the dialog). ``open(app)`` shows it; Escape
    closes it when ``closable``. ``width`` caps its width.
    """

    role = 'dialog'

    def a11y_name(self):
        return self.a11y_label or self.title or ''

    def a11y_value(self):
        return self.content if isinstance(self.content, str) else ''

    def __init__(self, content, title=None, buttons=(), width=60,
                 closable=True, on_close=None, **kwargs):
        super(Modal, self).__init__(**kwargs)
        self.content = content
        self.title = title
        self.width = width
        self.closable = bool(closable)
        self.on_close = on_close
        self.buttons = []
        colors = kwargs.get('use_colors')
        for b in buttons:
            if not isinstance(b, Button):
                label, action = b[0], b[1] if len(b) > 1 else None
                kind = b[2] if len(b) > 2 else 'default'
                b = Button(label, None, kind=kind, theme=self.theme,
                           use_colors=colors)
                b.on_press = self._wrap(action)
            self.buttons.append(b)
        self.is_open = False

    def _wrap(self, action):
        def run():
            result = action() if action is not None else None
            if result is not False:
                self.close()
        return run

    def children(self):
        kids = [] if isinstance(self.content, str) else [self.content]
        return kids + self.buttons

    def natural_width(self):
        return self.width

    def open(self, app):
        app.push(self)
        self.is_open = True
        return self

    def close(self):
        if self.app is not None and self.is_open:
            self.app.pop(self)
        self.is_open = False
        if self.on_close is not None:
            self.on_close()

    def handle_key(self, key):
        k = str(key)
        if k == 'escape' and self.closable:
            self.close()
            return True
        if k in ('left', 'right') and self.app is not None and \
                self.app.focused in self.buttons:
            i = self.buttons.index(self.app.focused)
            step = 1 if k == 'right' else -1
            self.app.focus(self.buttons[(i + step) % len(self.buttons)])
            return True
        return super(Modal, self).handle_key(key)

    def draw(self, width, height):
        inner = max(1, width - 4)
        body = render_into(self.content, inner) if not \
            isinstance(self.content, str) else []
        if isinstance(self.content, str):
            from flexablelib.text_width import wrap_to_width
            for paragraph in self.content.split('\n'):
                body.extend(wrap_to_width(paragraph, inner) or [''])
        lines = [''] + body + ['']
        if self.buttons:
            row = '  '.join(b.render(width=b.natural_width())
                            for b in self.buttons)
            lines.append(_fx.fit_line(row, inner, 'r'))
        footer = 'esc' if self.closable else None
        return frame([' ' + l for l in lines], width, self.title,
                     self.theme.accent, self.paint,
                     title_color='bold ' + self.theme.accent, footer=footer)


class ConfirmDialog(Modal):
    """Yes / no: ``on_confirm()`` or ``on_cancel()``; ``danger=True``
    colours the confirm button as destructive."""

    role = 'alertdialog'

    def __init__(self, message, on_confirm=None, on_cancel=None,
                 title='Confirmar', confirm_label='Aceptar',
                 cancel_label='Cancelar', danger=False, **kwargs):
        self.result = None

        def yes():
            self.result = True
            if on_confirm is not None:
                on_confirm()

        def no():
            self.result = False
            if on_cancel is not None:
                on_cancel()
        super(ConfirmDialog, self).__init__(
            message, title=title, width=kwargs.pop('width', 50),
            buttons=[(cancel_label, no),
                     (confirm_label, yes, 'danger' if danger else 'primary')],
            **kwargs)


class PromptDialog(Modal):
    """Asks for one value: ``on_submit(value)`` on Enter or Aceptar."""

    def __init__(self, label, on_submit=None, value='', title=None,
                 validators=None, **kwargs):
        colors = kwargs.get('use_colors')
        self.input = TextInput(label, value=value, validators=validators,
                               theme=kwargs.get('theme'), use_colors=colors)
        self.value = None
        self._callback = on_submit

        def accept():
            if self.input.validate():
                return False
            self.value = self.input.value
            if self._callback is not None:
                self._callback(self.value)
        self.input.on_submit = lambda v: self._accept_and_close(accept)
        super(PromptDialog, self).__init__(
            self.input, title=title, width=kwargs.pop('width', 50),
            buttons=[('Cancelar', None), ('Aceptar', accept, 'primary')],
            **kwargs)

    def _accept_and_close(self, accept):
        if accept() is not False:
            self.close()


class LoadingOverlay(Modal):
    """
    A spinner and message over the screen that holds the focus while work
    runs: ``show(app)`` / ``hide()``; ``progress`` (0-1) adds a bar.
    """

    def __init__(self, message='Cargando…', progress=None, **kwargs):
        self.spinner = Spinner(message, theme=kwargs.get('theme'),
                               use_colors=kwargs.get('use_colors'))
        self.progress = progress
        super(LoadingOverlay, self).__init__(self.spinner, closable=False,
                                             width=kwargs.pop('width', 40),
                                             **kwargs)

    role = 'progressbar'

    def a11y_name(self):
        return self.a11y_label or self.spinner.message or 'Cargando'

    def a11y_value(self):
        if self.progress is None:
            return 'ocupado'
        return '{0:.0f}%'.format(max(0.0, min(1.0, self.progress)) * 100)

    def a11y_state(self):
        return ['busy']

    def children(self):
        return []

    def show(self, app):
        return self.open(app)

    def hide(self):
        self.close()

    def handle_key(self, key):
        return True

    def draw(self, width, height):
        lines = self.spinner.render(width=max(1, width - 4)).split('\n')
        if self.progress is not None:
            inner = max(1, width - 10)
            fraction = max(0.0, min(1.0, self.progress))
            done = int(round(inner * fraction))
            lines.append(self.paint('█' * done, self.theme.accent) +
                         self.paint('░' * (inner - done), self.theme.muted) +
                         ' {0:>3.0f}%'.format(fraction * 100))
        return frame([' ' + l for l in [''] + lines + ['']], width, None,
                     self.theme.accent, self.paint)


class Popover(Modal):
    """Floating content at a position (``'top-right'``, ``(x, y)``...);
    ``modal=False`` leaves the focus where it was."""

    def __init__(self, content, title=None, width=40, **kwargs):
        super(Popover, self).__init__(content, title=title, width=width,
                                      **kwargs)

    def open(self, app, position='center', modal=True):
        app.push(self, position=position, modal=modal)
        self.is_open = True
        return self


class HelpLine(_Themed):
    """
    One line with the hint of whatever has the focus: its ``help``,
    ``tooltip`` or ``hint`` attribute. Put it above the footer; it is the
    terminal version of a tooltip.
    """

    role = 'status'

    def a11y_name(self):
        return self.a11y_label or 'ayuda'

    def __init__(self, default='', **kwargs):
        super(HelpLine, self).__init__(**kwargs)
        self.default = default

    def natural_width(self):
        return 40

    def draw(self, width, height):
        node = self.app.focused if self.app is not None else None
        text = ''
        while node is not None and not text:
            text = getattr(node, 'tooltip', None) or \
                getattr(node, 'hint', None) or getattr(node, 'help', None) \
                or ''
            node = getattr(node, 'parent', None)
        text = text or self.default
        return [self.paint(_fx.truncate('ⓘ ' + text if text else '', width,
                                        '…'), self.theme.muted)]
