"""
KEYBOARD INPUT

Terminals report keys as bytes: printable text as itself, control keys as
control characters, and everything else (arrows, function keys, modifiers,
mouse, paste) as escape sequences that differ between terminals. On Windows
the console reports special keys as a ``'\\x00'`` or ``'\\xe0'`` prefix and a
scan code instead.

:class:`KeyParser` (escape sequences) and :class:`WindowsKeyParser` (console
scan codes) turn either into :class:`Key` values with one naming scheme:

- printable characters are themselves: ``'a'``, ``'A'``, ``'ñ'``, ``'?'``;
- named keys: ``'enter'``, ``'tab'``, ``'shift+tab'``, ``'backspace'``,
  ``'escape'``, ``'space'``, ``'up'``, ``'down'``, ``'left'``, ``'right'``,
  ``'home'``, ``'end'``, ``'pageup'``, ``'pagedown'``, ``'insert'``,
  ``'delete'``, ``'f1'`` ... ``'f12'``;
- modifiers in the order ``ctrl+alt+shift+``: ``'ctrl+c'``, ``'alt+x'``,
  ``'ctrl+up'``, ``'shift+right'``;
- ``'paste'`` (bracketed paste; the text is in ``key.char``) and ``'mouse'``
  (``key.mouse`` is ``(button, x, y, pressed)``, 0-based cells; the wheel is
  reported as the keys ``'scrollup'`` / ``'scrolldown'``).

A :class:`Key` is a ``str`` (its name), so ``key == 'ctrl+s'`` works and keys
can be dictionary keys of key bindings.
"""

__all__ = ['Key', 'KeyParser', 'WindowsKeyParser', 'parse_keys']

ESC = '\x1b'


class Key(str):
    """A key press: the string is its name, ``char`` the text it types."""

    __slots__ = ('char', 'mouse')

    def __new__(cls, name, char='', mouse=None):
        self = str.__new__(cls, name)
        self.char = char
        self.mouse = mouse
        return self

    @property
    def name(self):
        return str(self)

    @property
    def is_printable(self):
        """Whether the key types text (``char`` is that text)."""
        return bool(self.char) and str(self) not in ('enter', 'tab', 'paste')

    def __repr__(self):
        return 'Key({0!r})'.format(str(self))


_CSI_TILDE = {
    1: 'home', 2: 'insert', 3: 'delete', 4: 'end', 5: 'pageup', 6: 'pagedown',
    7: 'home', 8: 'end', 11: 'f1', 12: 'f2', 13: 'f3', 14: 'f4', 15: 'f5',
    17: 'f6', 18: 'f7', 19: 'f8', 20: 'f9', 21: 'f10', 23: 'f11', 24: 'f12',
}
_CSI_LETTER = {
    'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left', 'H': 'home',
    'F': 'end', 'P': 'f1', 'Q': 'f2', 'R': 'f3', 'S': 'f4', 'E': 'begin',
}
_SS3 = dict(_CSI_LETTER)
_SS3.update({'M': 'enter', 'j': '*', 'k': '+', 'm': '-', 'n': '.', 'o': '/'})


def _modified(name, code):
    """Apply an xterm modifier parameter (1 + shift|alt<<1|ctrl<<2)."""
    bits = max(0, code - 1)
    prefix = ''
    if bits & 4:
        prefix += 'ctrl+'
    if bits & 2:
        prefix += 'alt+'
    if bits & 1:
        prefix += 'shift+'
    return prefix + name


def _control(ch):
    """The key for one character outside an escape sequence."""
    code = ord(ch)
    if ch in '\r\n':
        return Key('enter', '\n')
    if ch == '\t':
        return Key('tab', '\t')
    if ch in '\x7f\x08':
        return Key('backspace')
    if ch == ' ':
        return Key('space', ' ')
    if code == 0:
        return Key('ctrl+space')
    if code < 27:
        return Key('ctrl+' + chr(code + 96))
    if code < 32:
        return Key('ctrl+' + '\\]^_'[code - 28])
    return Key(ch, ch)


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
    """

    def __init__(self):
        self._buffer = ''
        self._bytes = b''
        self._paste = None

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
        self._buffer += self._decode(data)
        keys = []
        buf = self._buffer
        i = 0
        n = len(buf)
        while i < n:
            if self._paste is not None:
                end = buf.find(ESC + '[201~', i)
                if end < 0:
                    self._paste += buf[i:]
                    i = n
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
            if key is not None:
                keys.append(key)
            i += consumed
        self._buffer = buf[i:]
        return keys

    def flush(self):
        """Resolve held-back input when no more is coming (a lone Escape)."""
        keys = []
        if self._paste is not None:
            keys.append(Key('paste', self._paste))
            self._paste = None
        buf, self._buffer = self._buffer, ''
        if buf == ESC:
            keys.append(Key('escape'))
        elif buf.startswith(ESC + ESC):
            keys.append(Key('escape'))
            keys.extend(self.feed(buf[1:]))
            keys.extend(self.flush())
        elif buf.startswith(ESC) and len(buf) == 2:
            keys.append(self._alt(buf[1]))
        elif buf:
            # A truncated sequence: report its characters as typed.
            keys.append(Key('escape'))
            keys.extend(_control(c) for c in buf[1:])
        return keys

    @staticmethod
    def _alt(ch):
        key = _control(ch)
        if str(key).startswith('ctrl+'):
            return Key('ctrl+alt+' + str(key)[5:])
        return Key('alt+' + str(key), '')

    def _escape(self, buf, i):
        """``(consumed, key)``; ``consumed == 0`` means incomplete."""
        n = len(buf)
        if i + 1 >= n:
            return 0, None
        nxt = buf[i + 1]
        if nxt == '[':
            return self._csi(buf, i)
        if nxt == 'O':
            if i + 2 >= n:
                return 0, None
            name = _SS3.get(buf[i + 2])
            if name is None:
                return 3, None
            return 3, Key(name, '\n' if name == 'enter' else '')
        if nxt == ESC:
            # ESC ESC: an Escape press followed by whatever comes next.
            return 1, Key('escape')
        return 2, self._alt(nxt)

    def _csi(self, buf, i):
        n = len(buf)
        j = i + 2
        while j < n and '\x30' <= buf[j] <= '\x3f':
            j += 1
        while j < n and '\x20' <= buf[j] <= '\x2f':
            j += 1
        if j >= n:
            return 0, None
        final = buf[j]
        params = buf[i + 2:j]
        consumed = j - i + 1
        if params.startswith('<') and final in 'Mm':
            return consumed, self._mouse(params[1:], final == 'M')
        nums = []
        for part in params.split(';'):
            try:
                nums.append(int(part) if part else 1)
            except ValueError:
                return consumed, None
        if final == '~':
            code = nums[0] if nums else 1
            if code == 200:
                self._paste = ''
                return consumed, None
            name = _CSI_TILDE.get(code)
            if name is None:
                return consumed, None
            if len(nums) > 1:
                name = _modified(name, nums[1])
            return consumed, Key(name)
        if final == 'Z':
            return consumed, Key('shift+tab')
        if final == 'I':
            return consumed, Key('focusin')
        if final == 'O' and not params:
            return consumed, Key('focusout')
        name = _CSI_LETTER.get(final)
        if name is None:
            return consumed, None
        if len(nums) > 1:
            name = _modified(name, nums[1])
        return consumed, Key(name)

    @staticmethod
    def _mouse(params, pressed):
        try:
            button, x, y = (int(p) for p in params.split(';'))
        except ValueError:
            return None
        if button & 64:
            return Key('scrolldown' if button & 1 else 'scrollup',
                       mouse=(button, x - 1, y - 1, pressed))
        return Key('mouse', mouse=(button & 3, x - 1, y - 1, pressed))


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
    '`': 'ctrl+f3', 'a': 'ctrl+f4', 'b': 'ctrl+f5', 'h': 'alt+f1',
    'k': 'alt+f4',
}


class WindowsKeyParser(object):
    """
    Parser for characters read with ``msvcrt.getwch()``.

    Special keys arrive as ``'\\x00'`` or ``'\\xe0'`` followed by a scan code;
    Windows Terminal with virtual-terminal input sends escape sequences
    instead, which are handed to a :class:`KeyParser`.
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


def parse_keys(data):
    """Every key in ``data`` (a complete input string or bytes)."""
    parser = KeyParser()
    return parser.feed(data) + parser.flush()
