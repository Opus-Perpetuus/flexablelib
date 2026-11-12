"""
KEYBOARD AND MOUSE INPUT

Terminals report input as text: printable characters as themselves, control
keys as control characters and everything else (arrows, function keys,
modifier combinations, mouse, paste, focus changes and answers to queries) as
escape sequences that differ between terminals. On Windows the legacy
console reports special keys as a ``'\\x00'`` or ``'\\xe0'`` prefix and a scan
code (see :mod:`flexablelib_tui.wincon` for the console input records).

:class:`KeyParser` (escape sequences) and :class:`WindowsKeyParser` (console
scan codes) turn every encoding into :class:`Key` values with one naming
scheme:

- printable characters are themselves: ``'a'``, ``'A'``, ``'ñ'``, ``'?'``;
- named keys: ``'enter'``, ``'tab'``, ``'backspace'``, ``'escape'``,
  ``'space'``, ``'up'``, ``'down'``, ``'left'``, ``'right'``, ``'home'``,
  ``'end'``, ``'pageup'``, ``'pagedown'``, ``'insert'``, ``'delete'``,
  ``'begin'``, ``'f1'`` ... ``'f35'``, ``'menu'``, ``'printscreen'`` ...;
- modifiers always in the order ``ctrl+alt+shift+meta+super+hyper+``:
  ``'ctrl+c'``, ``'alt+x'``, ``'ctrl+shift+up'``, ``'ctrl+alt+delete'``.
  Shift with a letter is folded into the letter: ``'alt+A'``, ``'ctrl+A'``;
- ``'paste'`` (bracketed paste; the text is in ``key.char``);
- ``'mouse'`` for presses, releases, drags and moves (``key.mouse`` is a
  :class:`MouseEvent`, 0-based cells) and ``'scrollup'`` / ``'scrolldown'`` /
  ``'scrollleft'`` / ``'scrollright'`` for the wheel (with modifiers:
  ``'ctrl+scrollup'``);
- ``'focusin'`` / ``'focusout'`` when the terminal window gains or loses
  focus, and ``'response'`` for answers to terminal queries (``key.data``).

Recognised encodings: xterm / VT220 / rxvt / Linux console sequences (CSI and
SS3, with modifier parameters), F1-F20 legacy codes, the kitty keyboard
protocol (``CSI code;mods:event;text u``, press / repeat / release),
xterm ``modifyOtherKeys`` (``CSI 27;mods;code ~``), bracketed paste, focus
reporting, SGR (1006), urxvt (1015) and X10 / UTF-8 (1005) mouse reports,
8-bit CSI and ``ESC`` prefixed (Alt / Meta) keys.

A :class:`Key` is a ``str`` (its name), so ``key == 'ctrl+s'`` works and keys
can be dictionary keys of key bindings.
"""

__all__ = ['Key', 'MouseEvent', 'KeyParser', 'WindowsKeyParser',
           'parse_keys', 'MODIFIERS', 'split_key', 'compose_key',
           'normalize_key', 'key_label']

ESC = '\x1b'

#: Modifier names in the order they appear in key names.
MODIFIERS = ('ctrl', 'alt', 'shift', 'meta', 'super', 'hyper')


class Key(str):
    """
    A key press: the string is its name, ``char`` the text it types.

    ``mouse`` holds a :class:`MouseEvent` for mouse keys, ``event`` is
    ``'press'``, ``'repeat'`` or ``'release'`` (releases only arrive when the
    terminal reports them), ``data`` carries the parsed answer of a
    ``'response'`` key and ``raw`` the input text the key came from.
    """

    __slots__ = ('char', 'mouse', 'event', 'data', 'raw')

    def __new__(cls, name, char='', mouse=None, event='press', data=None,
                raw=''):
        self = str.__new__(cls, name)
        self.char = char
        self.mouse = mouse
        self.event = event
        self.data = data
        self.raw = raw
        return self

    @property
    def name(self):
        return str(self)

    @property
    def base(self):
        """The key without modifiers: ``'up'`` for ``'ctrl+up'``."""
        return split_key(self)[0]

    @property
    def mods(self):
        """The modifiers held, as a tuple in canonical order."""
        return split_key(self)[1]

    @property
    def is_printable(self):
        """Whether the key types text (``char`` is that text)."""
        return bool(self.char) and str(self) not in ('enter', 'tab', 'paste')

    def renamed(self, name):
        """The same key (char, mouse, event ...) under another name."""
        return Key(name, self.char, self.mouse, self.event, self.data,
                   self.raw)

    def __repr__(self):
        return 'Key({0!r})'.format(str(self))


class MouseEvent(tuple):
    """
    A mouse report: a ``(button, x, y, pressed)`` tuple with extras.

    ``button`` is 0 (left), 1 (middle), 2 (right), 3 (none: a move without
    buttons), 64-67 (wheel up, down, left, right) or 7+ (extra buttons);
    ``x`` / ``y`` are 0-based cells. ``action`` is ``'press'``,
    ``'release'``, ``'drag'``, ``'move'`` or ``'scroll'`` and ``mods`` the
    modifiers held.
    """

    def __new__(cls, button, x, y, pressed, action=None, mods=()):
        self = tuple.__new__(cls, (button, x, y, pressed))
        if action is None:
            action = 'press' if pressed else 'release'
        self.action = action
        self.mods = tuple(mods)
        return self

    button = property(lambda self: self[0])
    x = property(lambda self: self[1])
    y = property(lambda self: self[2])
    pressed = property(lambda self: self[3])

    def moved(self, dx, dy):
        """The same event with coordinates shifted by ``-dx, -dy``."""
        return MouseEvent(self[0], self[1] - dx, self[2] - dy, self[3],
                          self.action, self.mods)

    def __repr__(self):
        return 'MouseEvent({0}, {1}, {2}, {3}, {4!r})'.format(
            self[0], self[1], self[2], self[3], self.action)


def split_key(name):
    """``(base, mods)`` of a key name: ``('up', ('ctrl', 'shift'))``."""
    name = str(name)
    mods = set()
    while True:
        cut = name.find('+')
        if cut <= 0 or cut == len(name) - 1 or name[:cut] not in MODIFIERS:
            break
        mods.add(name[:cut])
        name = name[cut + 1:]
    return name, tuple(m for m in MODIFIERS if m in mods)


def compose_key(base, mods=()):
    """A key name from its base and modifiers (any order)."""
    mods = set(mods)
    if len(base) == 1 and 'shift' in mods and base.lower() != base.upper():
        base = base.upper()
        mods.discard('shift')
    return ''.join(m + '+' for m in MODIFIERS if m in mods) + base


_MOD_ALIASES = {
    'control': 'ctrl', 'ctl': 'ctrl', 'c': 'ctrl', 'option': 'alt',
    'opt': 'alt', 'a': 'alt', 'm': 'meta', 's': 'shift', 'cmd': 'super',
    'command': 'super', 'win': 'super', 'windows': 'super', 'logo': 'super',
}
_MOD_ALIASES.update((m, m) for m in MODIFIERS)
_KEY_ALIASES = {
    'esc': 'escape', 'return': 'enter', 'ret': 'enter', 'cr': 'enter',
    'del': 'delete', 'ins': 'insert', 'pgup': 'pageup', 'pgdn': 'pagedown',
    'pgdown': 'pagedown', 'page_up': 'pageup', 'page_down': 'pagedown',
    'bs': 'backspace', 'bksp': 'backspace', ' ': 'space', 'spacebar':
    'space', 'arrowup': 'up', 'arrowdown': 'down', 'arrowleft': 'left',
    'arrowright': 'right', 'plus': '+', 'minus': '-',
}


def normalize_key(name):
    """
    The canonical form of a key name written by hand.

    >>> normalize_key('Ctrl+Shift+A')
    'ctrl+A'
    >>> normalize_key('cmd+Esc')
    'super+escape'

    Modifier and key names are case-insensitive (``'Control'``, ``'Opt'``,
    ``'Cmd'``, ``'Esc'``, ``'PgUp'`` ...). A single character keeps its case
    on its own (``'A'`` is Shift+A); with modifiers the case comes from an
    explicit Shift: ``'Ctrl+J'`` is ``'ctrl+j'``, ``'Alt+Shift+X'`` is
    ``'alt+X'``.
    """
    text = str(name)
    if text != ' ':
        text = text.strip()
    if len(text) <= 1:
        return _KEY_ALIASES.get(text, text)
    parts = text.split('+')
    if text.endswith('++'):
        parts = parts[:-2] + ['+']
    mods = []
    for part in parts[:-1]:
        mod = _MOD_ALIASES.get(part.strip().lower())
        if mod is None:
            raise ValueError('unknown modifier {0!r} in {1!r}'.format(
                part, name))
        mods.append(mod)
    base = parts[-1].strip() or parts[-1]
    if mods and len(base) == 1 and 'shift' not in mods:
        base = base.lower()       # 'Ctrl+J' means Ctrl+J, not Ctrl+Shift+J
    if len(base) > 1:
        base = base.lower()
        base = _KEY_ALIASES.get(base, base)
    return compose_key(base, mods)


_LABELS = {'ctrl': 'Ctrl', 'alt': 'Alt', 'shift': 'Shift', 'meta': 'Meta',
           'super': 'Super', 'hyper': 'Hyper', 'pageup': 'PgUp',
           'pagedown': 'PgDn', 'escape': 'Esc', 'enter': 'Enter',
           'backspace': 'Backspace', 'delete': 'Supr', 'insert': 'Insert',
           'space': 'Espacio', 'tab': 'Tab', 'up': '↑', 'down': '↓',
           'left': '←', 'right': '→', 'home': 'Inicio', 'end': 'Fin'}
_ASCII_LABELS = {'up': 'Arriba', 'down': 'Abajo', 'left': 'Izq',
                 'right': 'Der'}


def key_label(name, ascii=False):
    """How a key is shown to people: ``'Ctrl+S'``, ``'Shift+Tab'``, ``'F5'``."""
    base, mods = split_key(name)
    if ascii and base in _ASCII_LABELS:
        label = _ASCII_LABELS[base]
    elif base in _LABELS:
        label = _LABELS[base]
    elif len(base) == 1:
        label = base.upper() if base.isalpha() and not mods else base
        if mods and base.isalpha():
            label = base if base.isupper() else base.upper()
            if base.isupper() and base.lower() != base:
                mods = mods + ('shift',)
    else:
        label = base[:1].upper() + base[1:]
    names = [_LABELS[m] for m in MODIFIERS if m in mods]
    return '+'.join(names + [label])


_CSI_TILDE = {
    1: 'home', 2: 'insert', 3: 'delete', 4: 'end', 5: 'pageup', 6: 'pagedown',
    7: 'home', 8: 'end', 11: 'f1', 12: 'f2', 13: 'f3', 14: 'f4', 15: 'f5',
    17: 'f6', 18: 'f7', 19: 'f8', 20: 'f9', 21: 'f10', 23: 'f11', 24: 'f12',
    25: 'f13', 26: 'f14', 28: 'f15', 29: 'f16', 31: 'f17', 32: 'f18',
    33: 'f19', 34: 'f20', 42: 'f21', 43: 'f22', 44: 'f23', 45: 'f24',
    57427: 'begin',
}
_CSI_LETTER = {
    'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left', 'H': 'home',
    'F': 'end', 'P': 'f1', 'Q': 'f2', 'R': 'f3', 'S': 'f4', 'E': 'begin',
    'G': 'begin',
}
# rxvt: shift+arrows as CSI a-d, ctrl+arrows as SS3 a-d.
_RXVT_ARROWS = {'a': 'up', 'b': 'down', 'c': 'right', 'd': 'left'}
_SS3 = dict(_CSI_LETTER)
_SS3.update({'M': 'enter', 'j': '*', 'k': '+', 'l': ',', 'm': '-', 'n': '.',
             'o': '/', 'X': '='})
_SS3.update((chr(ord('p') + d), str(d)) for d in range(10))
_LINUX_F = {'A': 'f1', 'B': 'f2', 'C': 'f3', 'D': 'f4', 'E': 'f5'}

# Kitty keyboard protocol: functional keys in the private use area.
_KITTY = {
    9: 'tab', 13: 'enter', 27: 'escape', 127: 'backspace', 8: 'backspace',
    32: 'space', 57358: 'capslock', 57359: 'scrolllock', 57360: 'numlock',
    57361: 'printscreen', 57362: 'pause', 57363: 'menu',
    57409: '.', 57410: '/', 57411: '*', 57412: '-', 57413: '+',
    57414: 'enter', 57415: '=', 57416: ',', 57417: 'left', 57418: 'right',
    57419: 'up', 57420: 'down', 57421: 'pageup', 57422: 'pagedown',
    57423: 'home', 57424: 'end', 57425: 'insert', 57426: 'delete',
    57427: 'begin', 57428: 'mediaplay', 57429: 'mediapause',
    57430: 'mediaplaypause', 57431: 'mediareverse', 57432: 'mediastop',
    57433: 'mediafastforward', 57434: 'mediarewind', 57435: 'mediatracknext',
    57436: 'mediatrackprevious', 57437: 'mediarecord', 57438: 'volumedown',
    57439: 'volumeup', 57440: 'volumemute', 57441: 'leftshift',
    57442: 'leftctrl', 57443: 'leftalt', 57444: 'leftsuper',
    57445: 'lefthyper', 57446: 'leftmeta', 57447: 'rightshift',
    57448: 'rightctrl', 57449: 'rightalt', 57450: 'rightsuper',
    57451: 'righthyper', 57452: 'rightmeta', 57453: 'isolevel3shift',
    57454: 'isolevel5shift',
}
_KITTY.update((57376 + n, 'f{0}'.format(13 + n)) for n in range(23))
_KITTY.update((57399 + d, str(d)) for d in range(10))
_CHARS = {'enter': '\n', 'tab': '\t', 'space': ' '}
_EVENTS = {1: 'press', 2: 'repeat', 3: 'release'}
_STRING_INTRO = {']': 'osc', 'P': 'dcs', '_': 'apc', '^': 'pm', 'X': 'sos'}


def _mods(value, kitty=False):
    """Modifier names of an xterm / kitty parameter (1 + bit field)."""
    bits = max(0, (value or 1) - 1)
    mods = []
    if bits & 4:
        mods.append('ctrl')
    if bits & 2:
        mods.append('alt')
    if bits & 1:
        mods.append('shift')
    if bits & 8:
        mods.append('super' if kitty else 'meta')
    if bits & 16:
        mods.append('hyper')
    if bits & 32:
        mods.append('meta')
    return mods


def _modified(name, code, kitty=False):
    return compose_key(name, _mods(code, kitty))


def _control(ch):
    """The key for one character outside an escape sequence."""
    code = ord(ch)
    if ch in '\r\n':
        return Key('enter', '\n', raw=ch)
    if ch == '\t':
        return Key('tab', '\t', raw=ch)
    if ch in '\x7f\x08':
        return Key('backspace', raw=ch)
    if ch == ' ':
        return Key('space', ' ', raw=ch)
    if code == 0:
        return Key('ctrl+space', raw=ch)
    if code < 27:
        return Key('ctrl+' + chr(code + 96), raw=ch)
    if code < 32:
        return Key('ctrl+' + '\\]^_'[code - 28], raw=ch)
    return Key(ch, ch, raw=ch)


def _char_key(code, mods, shifted=None, text=None):
    """The key for a code point reported with modifiers (CSI u, 27~)."""
    mods = list(mods)
    name = _KITTY.get(code)
    if name is not None:
        plain = not [m for m in mods if m != 'shift']
        if name.isdigit() or len(name) == 1:
            if plain and 'shift' not in mods:
                return Key(name, text or name)
            return Key(compose_key(name, mods))
        if name in ('tab',) and mods == ['shift']:
            return Key('shift+tab')
        key = compose_key(name, mods)
        return Key(key, _CHARS.get(name, '') if key == name else '')
    try:
        ch = chr(code)
    except (ValueError, OverflowError):
        return None
    if 'shift' in mods and shifted:
        ch = chr(shifted)
        mods.remove('shift')
    if code < 32:
        base, extra = split_key(_control(ch))
        return Key(compose_key(base, list(extra) + mods)) if mods else \
            _control(ch)
    key = compose_key(ch, mods)
    if len(key) == 1:
        return Key(key, text or key)
    return Key(key)


def _fields(params):
    """``'97:65;6:1;65'`` -> ``[[97, 65], [6, 1], [65]]`` (``None`` = empty)."""
    out = []
    for field in params.split(';'):
        values = []
        for part in field.split(':'):
            if part == '':
                values.append(None)
            elif part.isdigit():
                values.append(int(part))
            else:
                raise ValueError(params)
        out.append(values)
    return out


def _first(fields, index, default=None):
    if index < len(fields) and fields[index] and fields[index][0] is not None:
        return fields[index][0]
    return default


class KeyParser(object):
    """
    Incremental parser for terminal key input.

    >>> parser = KeyParser()
    >>> parser.feed('\\x1b[A')
    [Key('up')]
    >>> parser.feed('\\x1b')       # could be the start of a sequence ...
    []
    >>> parser.flush()            # ... until no more input comes
    [Key('escape')]

    ``feed`` accepts ``str`` or UTF-8 ``bytes`` (split multi-byte characters
    are held back until complete).

    ``kitty`` tells the parser the kitty keyboard protocol is on (modifier
    bit 8 is then *super*, not *meta*); ``releases`` keeps key-release events
    (dropped by default); ``expect_cpr`` counts cursor position reports the
    caller asked for (otherwise ``CSI 1;5R`` is Ctrl+F3).
    """

    def __init__(self, kitty=False, releases=False):
        self._buffer = ''
        self._bytes = b''
        self._paste = None
        self._mouse_down = 0
        self.kitty = kitty
        self.releases = releases
        self.expect_cpr = 0

    @property
    def pending(self):
        """Whether input is held back waiting for the rest of a sequence."""
        return bool(self._buffer or self._bytes or self._paste is not None)

    def _decode(self, data):
        if isinstance(data, str):
            return data
        data = self._bytes + data
        for cut in range(len(data), max(-1, len(data) - 4), -1):
            try:
                text = data[:cut].decode('utf-8')
            except UnicodeDecodeError:
                continue
            self._bytes = data[cut:]
            return text
        self._bytes = b''
        return data.decode('utf-8', 'replace')

    def feed(self, data):
        """Parse ``data``; returns the complete keys found."""
        text = self._decode(data)
        if '\x9b' in text:                       # 8-bit CSI
            text = text.replace('\x9b', ESC + '[')
        self._buffer += text
        keys = []
        buf = self._buffer
        i = 0
        n = len(buf)
        while i < n:
            if self._paste is not None:
                end = buf.find(ESC + '[201~', i)
                if end < 0:
                    # Keep a possible partial terminator for the next feed.
                    keep = 0
                    for size in range(min(5, n - i), 0, -1):
                        if (ESC + '[201~').startswith(buf[n - size:]):
                            keep = size
                            break
                    self._paste += buf[i:n - keep]
                    i = n - keep
                    break
                self._paste += buf[i:end]
                keys.append(Key('paste', self._paste))
                self._paste = None
                i = end + 6
                continue
            ch = buf[i]
            if ch != ESC:
                keys.append(_control(ch))
                i += 1
                continue
            consumed, key = self._escape(buf, i)
            if consumed == 0:      # incomplete: wait for more input
                break
            if key is not None and self._keep(key):
                key.raw = buf[i:i + consumed]
                keys.append(key)
            i += consumed
        self._buffer = buf[i:]
        return keys

    def _keep(self, key):
        return key.event != 'release' or self.releases

    def flush(self):
        """Resolve held-back input when no more is coming (a lone Escape)."""
        keys = []
        if self._paste is not None:
            keys.append(Key('paste', self._paste + self._buffer))
            self._paste = None
            self._buffer = ''
        buf, self._buffer = self._buffer, ''
        if buf == ESC:
            keys.append(Key('escape', raw=ESC))
        elif buf.startswith(ESC + ESC):
            keys.append(Key('escape', raw=ESC))
            keys.extend(self.feed(buf[1:]))
            keys.extend(self.flush())
        elif buf.startswith(ESC) and len(buf) == 2:
            keys.append(self._alt(buf[1]))
        elif buf.startswith(ESC) and buf[1] in _STRING_INTRO:
            keys.append(self._alt(buf[1]))
            keys.extend(self.feed(buf[2:]))
            keys.extend(self.flush())
        elif buf:
            # A truncated sequence: report its characters as typed.
            keys.append(Key('escape', raw=ESC))
            keys.extend(_control(c) for c in buf[1:])
        return keys

    @staticmethod
    def _alt(ch):
        key = _control(ch)
        if str(key).startswith('ctrl+'):
            return Key('ctrl+alt+' + str(key)[5:], raw=ESC + ch)
        return Key('alt+' + str(key), '', raw=ESC + ch)

    def _escape(self, buf, i):
        """``(consumed, key)``; ``consumed == 0`` means incomplete."""
        n = len(buf)
        if i + 1 >= n:
            return 0, None
        nxt = buf[i + 1]
        if nxt == '[':
            return self._csi(buf, i)
        if nxt == 'O':
            return self._ss3(buf, i)
        if nxt in _STRING_INTRO:
            return self._string(buf, i, _STRING_INTRO[nxt])
        if nxt == ESC:
            # ESC + a sequence is that key with Alt (meta sends escape);
            # otherwise an Escape press followed by whatever comes next.
            if i + 2 < n and buf[i + 2] in '[O':
                consumed, key = self._escape(buf, i + 1)
                if consumed == 0:
                    return 0, None
                if (key is not None and str(key) not in
                        ('paste', 'response', 'focusin', 'focusout')
                        and key.mouse is None and self._paste is None):
                    base, mods = split_key(key)
                    return consumed + 1, Key(compose_key(
                        base, mods + ('alt',)), event=key.event)
            return 1, Key('escape')
        return 2, self._alt(nxt)

    def _ss3(self, buf, i):
        n = len(buf)
        j = i + 2
        while j < n and (buf[j].isdigit() or buf[j] == ';'):
            j += 1
        if j >= n:
            return 0, None
        params = buf[i + 2:j]
        name = _SS3.get(buf[j])
        if buf[j] in _RXVT_ARROWS:
            name = 'ctrl+' + _RXVT_ARROWS[buf[j]]
        consumed = j - i + 1
        if name is None:
            return consumed, None
        mod = params.split(';')[-1]
        if mod.isdigit() and int(mod) > 1:
            return consumed, Key(_modified(name, int(mod), self.kitty))
        if len(name) == 1:
            return consumed, Key(name, name)
        return consumed, Key(name, '\n' if name == 'enter' else '')

    def _string(self, buf, i, kind):
        """OSC / DCS / APC / PM / SOS strings, ended by ST or BEL."""
        j = i + 2
        n = len(buf)
        while j < n:
            ch = buf[j]
            if ch == '\x07':
                return j - i + 1, Key('response', data=(kind, buf[i + 2:j]))
            if ch == ESC:
                if j + 1 >= n:
                    return 0, None
                if buf[j + 1] == '\\':
                    return j - i + 2, Key('response',
                                          data=(kind, buf[i + 2:j]))
                # Not a string after all: Alt + the introducer.
                return 2, self._alt(buf[i + 1])
            j += 1
        return 0, None

    def _csi(self, buf, i):
        n = len(buf)
        j = i + 2
        if j < n and buf[j] == '[':                 # Linux console F1-F5
            if j + 1 >= n:
                return 0, None
            name = _LINUX_F.get(buf[j + 1])
            return 4, (Key(name) if name else None)
        while j < n and '\x30' <= buf[j] <= '\x3f':
            j += 1
        params = buf[i + 2:j]
        if (j < n and buf[j] == '$' and not params.startswith('?')
                and ';' not in params):
            # rxvt: CSI 2$ is Shift+Insert (and so on).
            return j - i + 1, self._tilde(params, '$')
        while j < n and '\x20' <= buf[j] <= '\x2f':
            j += 1
        if j >= n:
            return 0, None
        final = buf[j]
        inter = buf[i + 2 + len(params):j]
        consumed = j - i + 1
        if not '\x40' <= final <= '\x7e':
            return j - i, None                      # aborted sequence
        if final == 'M' and not params and not inter:
            return self._x10(buf, i, j)
        if params.startswith('<') and final in 'Mm':
            return consumed, self._mouse_sgr(params[1:], final == 'M')
        if params[:1] in '?>=' and params:
            return consumed, self._response(params, inter, final)
        if inter == '$' and final == 'y':
            return consumed, Key('response', data=('decrqm', params))
        if final in 'tn':
            return consumed, Key('response', data=(
                'window' if final == 't' else 'dsr', params))
        try:
            fields = _fields(params)
        except ValueError:
            return consumed, None
        if final in '~^@':
            return consumed, self._tilde(params, final, fields)
        if final == 'u':
            return consumed, self._kitty_key(fields)
        if final == 'M' and len(fields) == 3:
            return consumed, self._mouse_urxvt(fields)
        if final == 'R' and self.expect_cpr and len(fields) == 2:
            self.expect_cpr -= 1
            return consumed, Key('response', data=('cpr', params))
        if final == 'I' and not params:
            return consumed, Key('focusin')
        if final == 'O' and not params:
            return consumed, Key('focusout')
        if final == 'Z':
            mods = _mods(_first(fields, 1, 1), self.kitty)
            return consumed, Key(compose_key('tab', ['shift'] + mods)
                                 if mods else 'shift+tab')
        if final in _RXVT_ARROWS and not params:
            return consumed, Key('shift+' + _RXVT_ARROWS[final])
        name = _CSI_LETTER.get(final)
        if name is None:
            return consumed, None
        event = self._event(fields)
        mod = _first(fields, 1, 1)
        return consumed, Key(_modified(name, mod, self.kitty), event=event)

    @staticmethod
    def _event(fields):
        if len(fields) > 1 and len(fields[1]) > 1 and fields[1][1]:
            return _EVENTS.get(fields[1][1], 'press')
        return 'press'

    def _tilde(self, params, final, fields=None):
        if fields is None:
            try:
                fields = _fields(params)
            except ValueError:
                return None
        code = _first(fields, 0, 1)
        if final == '~' and code == 200:
            self._paste = ''
            return None
        if final == '~' and code == 27 and len(fields) >= 3:
            # xterm modifyOtherKeys: CSI 27 ; mods ; code ~
            return _char_key(_first(fields, 2, 0),
                             _mods(_first(fields, 1, 1)))
        name = _CSI_TILDE.get(code)
        if name is None:
            return None
        mods = _mods(_first(fields, 1, 1), self.kitty)
        mods += {'$': ['shift'], '^': ['ctrl'], '@': ['ctrl', 'shift'],
                 '~': []}[final]
        return Key(compose_key(name, mods), event=self._event(fields))

    def _kitty_key(self, fields):
        """``CSI code[:shifted[:base]] ; mods[:event] ; text u``."""
        codes = fields[0]
        code = codes[0] if codes[0] is not None else 1
        shifted = codes[1] if len(codes) > 1 else None
        mods = _mods(_first(fields, 1, 1), kitty=True)
        text = None
        if len(fields) > 2:
            text = ''.join(chr(c) for c in fields[2] if c)
        key = _char_key(code, mods, shifted, text)
        if key is None:
            return None
        key.event = self._event(fields)
        return key

    @staticmethod
    def _response(params, inter, final):
        lead = params[0]
        if final == 'c':
            kind = 'da1' if lead == '?' else 'da2' if lead == '>' else 'da3'
        elif final == 'u' and lead == '?':
            kind = 'kitty'
        elif final == 'y' and inter == '$':
            kind = 'decrqm'
        elif final == 'm' and lead == '>':
            kind = 'modifykeys'
        else:
            kind = 'csi' + lead + inter + final
        return Key('response', data=(kind, params[1:]))

    def _mouse_event(self, cb, x, y, release):
        """The key for a mouse report (``cb`` without the +32 offset)."""
        mods = []
        if cb & 16:
            mods.append('ctrl')
        if cb & 8:
            mods.append('alt')
        if cb & 4:
            mods.append('shift')
        low = cb & 3
        if cb & 64:
            button = 64 + low
            name = ('scrollup', 'scrolldown', 'scrollleft',
                    'scrollright')[low]
            return Key(compose_key(name, mods), mouse=MouseEvent(
                button, x - 1, y - 1, True, 'scroll', mods))
        button = (7 + low) if cb & 128 else low
        if cb & 32:
            action = 'move' if low == 3 else 'drag'
            pressed = action == 'drag'
        elif release:
            action, pressed = 'release', False
            if low == 3:                       # X10 / urxvt release
                button = self._mouse_down
        else:
            action, pressed = 'press', True
            self._mouse_down = button
        return Key('mouse', mouse=MouseEvent(button, x - 1, y - 1, pressed,
                                             action, mods))

    def _mouse_sgr(self, params, pressed):
        try:
            cb, x, y = (int(p) for p in params.split(';'))
        except ValueError:
            return None
        return self._mouse_event(cb, x, y, not pressed)

    def _mouse_urxvt(self, fields):
        cb, x, y = (_first(fields, k, 0) for k in range(3))
        cb -= 32
        return self._mouse_event(cb, x, y, (cb & 3) == 3 and not cb & 96)

    def _x10(self, buf, i, j):
        if j + 3 >= len(buf):
            return 0, None
        cb, x, y = (ord(c) - 32 for c in buf[j + 1:j + 4])
        key = None
        if cb >= 0 and x > 0 and y > 0:
            key = self._mouse_event(cb, x, y, (cb & 3) == 3 and not cb & 96)
        return j - i + 4, key


# Windows console: the scan code after a '\x00' / '\xe0' prefix.
_WIN_SCAN = {
    'H': 'up', 'P': 'down', 'K': 'left', 'M': 'right', 'G': 'home',
    'O': 'end', 'I': 'pageup', 'Q': 'pagedown', 'R': 'insert', 'S': 'delete',
    ';': 'f1', '<': 'f2', '=': 'f3', '>': 'f4', '?': 'f5', '@': 'f6',
    'A': 'f7', 'B': 'f8', 'C': 'f9', 'D': 'f10', '\x85': 'f11',
    '\x86': 'f12', 's': 'ctrl+left', 't': 'ctrl+right', '\x8d': 'ctrl+up',
    '\x91': 'ctrl+down', 'w': 'ctrl+home', 'u': 'ctrl+end',
    '\x84': 'ctrl+pageup', 'v': 'ctrl+pagedown', '\x93': 'ctrl+delete',
    '\x92': 'ctrl+insert', '\x94': 'ctrl+tab',
    'T': 'shift+f1', 'U': 'shift+f2', 'V': 'shift+f3', 'W': 'shift+f4',
    'X': 'shift+f5', 'Y': 'shift+f6', 'Z': 'shift+f7', '[': 'shift+f8',
    '\\': 'shift+f9', ']': 'shift+f10', '^': 'ctrl+f1', '_': 'ctrl+f2',
    '`': 'ctrl+f3', 'a': 'ctrl+f4', 'b': 'ctrl+f5', 'c': 'ctrl+f6',
    'd': 'ctrl+f7', 'e': 'ctrl+f8', 'f': 'ctrl+f9', 'g': 'ctrl+f10',
    'h': 'alt+f1', 'i': 'alt+f2', 'j': 'alt+f3', 'k': 'alt+f4',
    'l': 'alt+f5', 'm': 'alt+f6', 'n': 'alt+f7', 'o': 'alt+f8',
    'p': 'alt+f9', 'q': 'alt+f10', '\x87': 'shift+f11', '\x88': 'shift+f12',
    '\x89': 'ctrl+f11', '\x8a': 'ctrl+f12', '\x8b': 'alt+f11',
    '\x8c': 'alt+f12', '\x97': 'alt+home', '\x98': 'alt+up',
    '\x99': 'alt+pageup', '\x9b': 'alt+left', '\x9d': 'alt+right',
    '\x9f': 'alt+end', '\xa0': 'alt+down', '\xa1': 'alt+pagedown',
    '\xa2': 'alt+insert', '\xa3': 'alt+delete', '\xa5': 'alt+tab',
    '\x95': 'ctrl+/', '\x96': 'ctrl+*', 'L': 'begin',
}


class WindowsKeyParser(object):
    """
    Parser for characters read with ``msvcrt.getwch()``.

    Special keys arrive as ``'\\x00'`` or ``'\\xe0'`` followed by a scan code;
    consoles with virtual-terminal input send escape sequences instead, which
    are handed to a :class:`KeyParser`.
    """

    def __init__(self):
        self._prefix = False
        self._vt = KeyParser()

    @property
    def pending(self):
        return self._prefix or self._vt.pending

    def feed(self, chars):
        keys = []
        for ch in chars:
            if self._prefix:
                self._prefix = False
                name = _WIN_SCAN.get(ch)
                if name is not None:
                    keys.append(Key(name))
                continue
            if ch in '\x00\xe0' and not self._vt.pending:
                self._prefix = True
                continue
            if ch == '\r':
                ch = '\n'
            keys.extend(self._vt.feed(ch))
        return keys

    def flush(self):
        self._prefix = False
        return self._vt.flush()


def parse_keys(data, **options):
    """Every key in ``data`` (a complete input string or bytes)."""
    parser = KeyParser(**options)
    return parser.feed(data) + parser.flush()
