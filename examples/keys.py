#!/usr/bin/env python3
"""
A live key and mouse detector: shows every key, combination, paste, focus
change and mouse event the terminal sends, with the name flexablelib gives
it, how it is shown to people, the raw bytes and the protocol in use.

    python examples/keys.py                      # interactive (Ctrl-Q quits)
    python examples/keys.py --frame 100x30 --feed '\\x1b[1;5A,\\x1b[<0;12;6M'

Try Ctrl/Alt/Shift combinations, F1-F24, Home/End, the keypad, pasting
text, clicking the buttons, the wheel over the list and switching to
another window and back (focus events). On terminals with the kitty
keyboard protocol (kitty, WezTerm, foot, Ghostty, recent iTerm2) or
xterm's modifyOtherKeys, combinations such as Ctrl+Enter, Ctrl+Shift+A or
Ctrl+I versus Tab are told apart, and releases are shown.
"""

import argparse
import codecs
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (ROOT, os.path.join(ROOT, 'packages', 'tui'),
             os.path.join(ROOT, 'packages', 'components'),
             os.path.join(ROOT, 'packages', 'speedups')):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

import flexablelib_components as C  # noqa: E402
from flexablelib import KeyHints  # noqa: E402
from flexablelib_tui import (App, Component, ScrollView,  # noqa: E402
                             Key, detect_capabilities, key_label,
                             parse_keys)


class KeyLog(Component):
    """The latest keys, newest first, as a small table."""

    role = 'log'
    expand = True

    def __init__(self, rows=12, **kwargs):
        super(KeyLog, self).__init__(**kwargs)
        self.rows = rows
        self.entries = []

    def add(self, key):
        name = str(key)
        if name == 'mouse':
            m = key.mouse
            what = '{0} b{1} ({2},{3}){4}'.format(
                m.action, m.button, m.x, m.y,
                (' + ' + '+'.join(m.mods)) if m.mods else '')
            label = 'Ratón'
        elif name == 'paste':
            what = repr(key.char[:30])
            label = 'Pegar'
        elif name in ('focusin', 'focusout'):
            what = 'ventana'
            label = key_label(name)
        else:
            what = key.event
            label = key_label(name)
        raw = repr(key.raw or key.char or '')[1:-1]
        self.entries.insert(0, (name, label, what, raw))
        del self.entries[200:]
        self.refresh()

    def a11y_value(self):
        if not self.entries:
            return 'sin teclas todavía'
        name, label, what, raw = self.entries[0]
        return 'última: {0} ({1})'.format(label, what)

    def draw(self, width, height):
        rows = (height - 2) if height else self.rows
        name_w, label_w, raw_w = 18, 14, 16
        what_w = max(8, width - name_w - label_w - raw_w - 3)
        fmt = '{0:<%d} {1:<%d} {2:<%d} {3}' % (name_w, label_w, what_w)
        head = fmt.format('nombre', 'se muestra', 'detalle', 'bytes')
        out = [self.paint(head, 'bold') if self._active() else head,
               '─' * width]
        for name, label, what, raw in self.entries[:max(1, rows)]:
            out.append(fmt.format(name[:name_w], label[:label_w],
                                  what[:what_w], raw[:raw_w]))
        if not self.entries:
            out.append('Pulsa cualquier tecla, combinación o haz clic…')
        return out


class Detector(App):
    def __init__(self, **options):
        self.log = KeyLog()
        self.clicks = C.Badge('0 clics', kind='info')
        self.count = 0
        caps = detect_capabilities()
        buttons = C.Stack([C.Toolbar([C.Button('Botón A', self._click),
                                      C.Button('Botón B', self._click)]),
                           C.Checkbox('Casilla')])
        items = ScrollView('\n'.join('Elemento {0:02d}'.format(i)
                                     for i in range(1, 41)), height=6,
                           a11y_label='Lista (rueda del ratón)')
        info = C.DetailView([(k.split(':')[0], k.split(': ', 1)[1])
                             for k in caps.summary()],
                            a11y_label='Capacidades')
        body = C.Split(C.Box(self.log, title='Teclas y ratón'),
                       C.Stack([C.Box(info, title='Terminal'),
                                C.Box(C.Stack([buttons, self.clicks]),
                                      title='Clic aquí'),
                                C.Box(items, title='Rueda aquí')]),
                       ratio=0.62)
        super(Detector, self).__init__(
            body=body, mouse='hover', title='Detector de teclas',
            footer=KeyHints([('Ctrl-Q', 'Salir'), ('F1', 'Ayuda'),
                             ('Tab', 'Foco')]),
            bindings={'ctrl+q': (lambda: self.exit(), 'Salir')}, **options)

    def _click(self):
        self.count += 1
        self.clicks.text = '{0} clic{1}'.format(
            self.count, 's' if self.count != 1 else '')

    def dispatch(self, key):
        if isinstance(key, Key) and str(key) != 'response':
            if str(key) != 'mouse' or key.mouse.action != 'move':
                self.log.add(key)
        return super(Detector, self).dispatch(key)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--frame', metavar='WxH',
                        help='print one frame of this size and exit')
    parser.add_argument('--feed', default='',
                        help='comma-separated raw input (Python escapes) '
                        'parsed before the frame')
    parser.add_argument('--no-color', action='store_true')
    args = parser.parse_args(argv)
    if args.no_color:
        Component.use_colors = False
    app = Detector(use_colors=not args.no_color if args.frame else None)
    if not args.frame:
        app.run()
        return 0
    width, height = (int(n) for n in args.frame.lower().split('x'))
    for chunk in [c for c in args.feed.split(',') if c]:
        app.render(width, height)
        data = codecs.decode(chunk, 'unicode_escape')
        for key in parse_keys(data, kitty=True):
            app.dispatch(key)
    sys.stdout.write(app.render(width, height) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
