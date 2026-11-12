"""
WINDOWS CONSOLE INPUT

The Windows console delivers input as ``INPUT_RECORD`` structures read with
``ReadConsoleInputW``: key events (virtual-key code, character, modifier
state), mouse events (position, buttons, wheel), window-size changes and
focus changes. This module turns them into the same :class:`~.keys.Key`
values the escape-sequence parser produces.

- :func:`translate_key` / :class:`ConsoleInputTranslator` are pure Python and
  work on records written as tuples, so they run (and are tested) on every
  platform:

  - ``('key', down, repeat, vk, char, state)``
  - ``('mouse', x, y, buttons, state, flags)``
  - ``('size', columns, lines)``
  - ``('focus', has_focus)``
  - ``('menu', command)``

- :class:`ConsoleInput` reads (and, for tests, writes) real records through
  ``ctypes`` on Windows. With ``vt=True`` it also asks the console for
  virtual-terminal input (``ENABLE_VIRTUAL_TERMINAL_INPUT``): keys then come
  as escape sequences in the record characters and are parsed by
  :class:`~.keys.KeyParser`; consoles without it fall back to records.

:class:`~.terminal.Terminal` uses ``ConsoleInput`` when stdin is a console
and the legacy ``msvcrt.getwch()`` reader otherwise.
"""

import ctypes
import os

from .keys import Key, KeyParser, MouseEvent, compose_key, _control

__all__ = ['ConsoleInput', 'ConsoleInputTranslator', 'translate_key',
           'records_from_text']

# dwControlKeyState
RIGHT_ALT, LEFT_ALT, RIGHT_CTRL, LEFT_CTRL = 0x1, 0x2, 0x4, 0x8
SHIFT, ENHANCED = 0x10, 0x100
# dwEventFlags
MOUSE_MOVED, DOUBLE_CLICK, MOUSE_WHEELED, MOUSE_HWHEELED = 1, 2, 4, 8
# EventType
KEY_EVENT, MOUSE_EVENT, WINDOW_BUFFER_SIZE_EVENT, MENU_EVENT, FOCUS_EVENT = \
    0x1, 0x2, 0x4, 0x8, 0x10
# Console input modes
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_LINE_INPUT = 0x0002
ENABLE_ECHO_INPUT = 0x0004
ENABLE_WINDOW_INPUT = 0x0008
ENABLE_MOUSE_INPUT = 0x0010
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200

_VK = {
    0x08: 'backspace', 0x09: 'tab', 0x0C: 'begin', 0x0D: 'enter',
    0x13: 'pause', 0x1B: 'escape', 0x20: 'space', 0x21: 'pageup',
    0x22: 'pagedown', 0x23: 'end', 0x24: 'home', 0x25: 'left', 0x26: 'up',
    0x27: 'right', 0x28: 'down', 0x2C: 'printscreen', 0x2D: 'insert',
    0x2E: 'delete', 0x5D: 'menu', 0xAD: 'volumemute', 0xAE: 'volumedown',
    0xAF: 'volumeup', 0xB0: 'mediatracknext', 0xB1: 'mediatrackprevious',
    0xB2: 'mediastop', 0xB3: 'mediaplaypause',
}
_VK.update((0x70 + n, 'f{0}'.format(n + 1)) for n in range(24))
# Shift, Ctrl, Alt, Win, Caps/Num/Scroll lock and their left/right forms.
_MODIFIER_VK = frozenset([0x10, 0x11, 0x12, 0x14, 0x5B, 0x5C, 0x90, 0x91,
                          0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5])
_BUTTONS = ((0x1, 0), (0x2, 2), (0x4, 1), (0x8, 7), (0x10, 8))


def _key_mods(state):
    mods = []
    if state & (LEFT_CTRL | RIGHT_CTRL):
        mods.append('ctrl')
    if state & (LEFT_ALT | RIGHT_ALT):
        mods.append('alt')
    if state & SHIFT:
        mods.append('shift')
    return mods


def translate_key(vk, char, state):
    """The :class:`Key` for one key-down record, or ``None`` (modifiers)."""
    if vk in _MODIFIER_VK:
        return None
    char = char or ''
    if char == '\x00':
        char = ''
    # AltGr arrives as Right-Alt + Left-Ctrl and types a character.
    if (char and char >= ' ' and state & RIGHT_ALT and state & LEFT_CTRL):
        state &= ~(RIGHT_ALT | LEFT_CTRL)
    mods = _key_mods(state)
    name = _VK.get(vk)
    if name is not None and not (vk == 0x20 and char and 'ctrl' not in mods
                                 and 'alt' not in mods):
        if name == 'tab' and mods == ['shift']:
            return Key('shift+tab')
        if not mods:
            return Key(name, {'enter': '\n', 'tab': '\t'}.get(name, ''))
        return Key(compose_key(name, mods))
    others = [m for m in mods if m != 'shift']
    if 'ctrl' in mods and 0x41 <= vk <= 0x5A:
        return Key(compose_key(chr(vk).lower(), mods))
    if 'ctrl' in mods and 0x30 <= vk <= 0x39:
        return Key(compose_key(chr(vk), mods))
    if char and char < ' ':
        base = str(_control(char))
        return Key(base) if not others else Key(compose_key(
            base.replace('ctrl+', ''), ['ctrl'] + others))
    if char:
        if not others:
            return Key('space', ' ') if char == ' ' else Key(char, char)
        return Key(compose_key('space' if char == ' ' else char, others))
    if others and 0x41 <= vk <= 0x5A:
        return Key(compose_key(chr(vk).lower(), mods))
    return None


class ConsoleInputTranslator(object):
    """
    Turns console input records into keys, keeping the state that needs:
    pressed mouse buttons (to report releases), split surrogate pairs and
    the escape-sequence parser used for virtual-terminal input.

    ``vt``: the console sends escape sequences (VT input mode); ``origin``:
    the ``(left, top)`` cell of the visible window inside the screen buffer,
    subtracted from mouse positions.
    """

    def __init__(self, vt=False, origin=(0, 0)):
        self.vt = vt
        self.origin = origin
        self.parser = KeyParser()
        self._buttons = 0
        self._surrogate = ''
        self.size = None
        self.focused = None

    @property
    def pending(self):
        return self.parser.pending or bool(self._surrogate)

    def flush(self):
        self._surrogate = ''
        return self.parser.flush()

    def feed(self, records):
        keys = []
        for record in records:
            kind = record[0]
            if kind == 'key':
                keys.extend(self._key(*record[1:]))
            elif kind == 'mouse':
                keys.extend(self._mouse(*record[1:]))
            elif kind == 'size':
                self.size = (record[1], record[2])
                keys.append(Key('resize', data=self.size))
            elif kind == 'focus':
                self.focused = bool(record[1])
                keys.append(Key('focusin' if record[1] else 'focusout'))
        return keys

    def _key(self, down, repeat, vk, char, state):
        if not down:
            return []
        char = char or ''
        if '\ud800' <= char[:1] <= '\udbff':
            self._surrogate = char
            return []
        if self._surrogate and '\udc00' <= char[:1] <= '\udfff':
            char = (self._surrogate + char).encode(
                'utf-16-le', 'surrogatepass').decode('utf-16-le')
            self._surrogate = ''
        keys = []
        if char and (self.vt or self.parser.pending or
                     (vk == 0 and char == '\x1b')):
            text = '\n' if char == '\r' else char
            for _ in range(max(1, repeat)):
                keys.extend(self.parser.feed(text))
            return keys
        if char and len(char) > 1:               # a joined surrogate pair
            return [Key(char, char)] * max(1, repeat)
        key = translate_key(vk, char, state)
        if key is None:
            return []
        return [key] * max(1, repeat)

    def _mouse(self, x, y, buttons, state, flags):
        x -= self.origin[0]
        y -= self.origin[1]
        mods = _key_mods(state)
        if flags & (MOUSE_WHEELED | MOUSE_HWHEELED):
            delta = (buttons >> 16) & 0xFFFF
            if delta >= 0x8000:
                delta -= 0x10000
            if flags & MOUSE_HWHEELED:
                code, name = (67, 'scrollright') if delta > 0 else \
                    (66, 'scrollleft')
            else:
                code, name = (64, 'scrollup') if delta > 0 else \
                    (65, 'scrolldown')
            return [Key(compose_key(name, mods), mouse=MouseEvent(
                code, x, y, True, 'scroll', mods))]
        buttons &= 0xFFFF
        if flags & MOUSE_MOVED:
            held = [b for bit, b in _BUTTONS if buttons & bit]
            self._buttons = buttons
            if held:
                return [Key('mouse', mouse=MouseEvent(
                    held[0], x, y, True, 'drag', mods))]
            return [Key('mouse', mouse=MouseEvent(3, x, y, False, 'move',
                                                  mods))]
        keys = []
        changed = buttons ^ self._buttons
        if flags & DOUBLE_CLICK:
            changed |= buttons
        for bit, button in _BUTTONS:
            if changed & bit:
                pressed = bool(buttons & bit)
                keys.append(Key('mouse', mouse=MouseEvent(
                    button, x, y, pressed, None, mods)))
        self._buttons = buttons
        return keys


def records_from_text(text, state=0):
    """Key-down/up record pairs that type ``text`` (for tests and demos)."""
    out = []
    for ch in text:
        vk = ord(ch.upper()) if ch.isalnum() and ch.isascii() else 0
        out.append(('key', True, 1, vk, ch, state))
        out.append(('key', False, 1, vk, ch, state))
    return out


# -- ctypes structures (defined everywhere; used on Windows) ----------------

class _COORD(ctypes.Structure):
    _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]


class _CHAR(ctypes.Union):
    _fields_ = [('UnicodeChar', ctypes.c_uint16), ('AsciiChar', ctypes.c_char)]


class _KEY_EVENT(ctypes.Structure):
    _fields_ = [('bKeyDown', ctypes.c_int32), ('wRepeatCount', ctypes.c_uint16),
                ('wVirtualKeyCode', ctypes.c_uint16),
                ('wVirtualScanCode', ctypes.c_uint16), ('uChar', _CHAR),
                ('dwControlKeyState', ctypes.c_uint32)]


class _MOUSE_EVENT(ctypes.Structure):
    _fields_ = [('dwMousePosition', _COORD), ('dwButtonState', ctypes.c_uint32),
                ('dwControlKeyState', ctypes.c_uint32),
                ('dwEventFlags', ctypes.c_uint32)]


class _SIZE_EVENT(ctypes.Structure):
    _fields_ = [('dwSize', _COORD)]


class _MENU_EVENT(ctypes.Structure):
    _fields_ = [('dwCommandId', ctypes.c_uint32)]


class _FOCUS_EVENT(ctypes.Structure):
    _fields_ = [('bSetFocus', ctypes.c_int32)]


class _EVENT(ctypes.Union):
    _fields_ = [('KeyEvent', _KEY_EVENT), ('MouseEvent', _MOUSE_EVENT),
                ('WindowBufferSizeEvent', _SIZE_EVENT),
                ('MenuEvent', _MENU_EVENT), ('FocusEvent', _FOCUS_EVENT)]


class INPUT_RECORD(ctypes.Structure):
    _fields_ = [('EventType', ctypes.c_uint16), ('Event', _EVENT)]


def record_to_tuple(rec):
    """An ``INPUT_RECORD`` as the tuple form the translator reads."""
    kind = rec.EventType
    if kind == KEY_EVENT:
        k = rec.Event.KeyEvent
        code = k.uChar.UnicodeChar
        return ('key', bool(k.bKeyDown), k.wRepeatCount, k.wVirtualKeyCode,
                chr(code) if code else '', k.dwControlKeyState)
    if kind == MOUSE_EVENT:
        m = rec.Event.MouseEvent
        return ('mouse', m.dwMousePosition.X, m.dwMousePosition.Y,
                m.dwButtonState, m.dwControlKeyState, m.dwEventFlags)
    if kind == WINDOW_BUFFER_SIZE_EVENT:
        s = rec.Event.WindowBufferSizeEvent.dwSize
        return ('size', s.X, s.Y)
    if kind == FOCUS_EVENT:
        return ('focus', bool(rec.Event.FocusEvent.bSetFocus))
    return ('menu', rec.Event.MenuEvent.dwCommandId)


def tuple_to_record(item):
    """The ``INPUT_RECORD`` for a tuple record (to inject with
    ``WriteConsoleInputW``)."""
    rec = INPUT_RECORD()
    kind = item[0]
    if kind == 'key':
        _, down, repeat, vk, char, state = item
        rec.EventType = KEY_EVENT
        k = rec.Event.KeyEvent
        k.bKeyDown = 1 if down else 0
        k.wRepeatCount = repeat
        k.wVirtualKeyCode = vk
        k.uChar.UnicodeChar = ord(char) if char else 0
        k.dwControlKeyState = state
    elif kind == 'mouse':
        _, x, y, buttons, state, flags = item
        rec.EventType = MOUSE_EVENT
        m = rec.Event.MouseEvent
        m.dwMousePosition.X, m.dwMousePosition.Y = x, y
        m.dwButtonState = buttons & 0xFFFFFFFF
        m.dwControlKeyState = state
        m.dwEventFlags = flags
    elif kind == 'size':
        rec.EventType = WINDOW_BUFFER_SIZE_EVENT
        rec.Event.WindowBufferSizeEvent.dwSize.X = item[1]
        rec.Event.WindowBufferSizeEvent.dwSize.Y = item[2]
    elif kind == 'focus':
        rec.EventType = FOCUS_EVENT
        rec.Event.FocusEvent.bSetFocus = 1 if item[1] else 0
    else:
        rec.EventType = MENU_EVENT
        rec.Event.MenuEvent.dwCommandId = item[1]
    return rec


class ConsoleInput(object):   # pragma: no cover - exercised on Windows CI
    """
    Console input records through the Win32 API (Windows only).

    ``handle`` defaults to the console input of ``stdin`` (``CONIN$``).
    """

    def __init__(self, handle=None, stdin=None):
        self.kernel32 = ctypes.windll.kernel32
        if handle is None:
            handle = self._handle_of(stdin)
        self.handle = handle
        self._saved = None
        self.vt = False

    def _handle_of(self, stdin):
        try:
            import msvcrt
            return msvcrt.get_osfhandle(stdin.fileno())
        except (AttributeError, ValueError, OSError, ImportError):
            return self.kernel32.GetStdHandle(-10)      # STD_INPUT_HANDLE

    def mode(self):
        """The console input mode, or ``None`` when this is no console."""
        value = ctypes.c_uint32()
        if not self.kernel32.GetConsoleMode(ctypes.c_void_p(self.handle),
                                            ctypes.byref(value)):
            return None
        return value.value

    def set_mode(self, value):
        return bool(self.kernel32.SetConsoleMode(
            ctypes.c_void_p(self.handle), ctypes.c_uint32(value)))

    def start(self, mouse=False, vt=True):
        """Raw input mode; returns ``False`` when ``handle`` is no console."""
        old = self.mode()
        if old is None:
            return False
        self._saved = old
        new = old | ENABLE_WINDOW_INPUT | ENABLE_EXTENDED_FLAGS
        new &= ~(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT |
                 ENABLE_PROCESSED_INPUT)
        if mouse:
            new = (new | ENABLE_MOUSE_INPUT) & ~ENABLE_QUICK_EDIT_MODE
        self.vt = False
        if vt and self.set_mode(new | ENABLE_VIRTUAL_TERMINAL_INPUT):
            self.vt = True
            return True
        return self.set_mode(new & ~ENABLE_VIRTUAL_TERMINAL_INPUT)

    def stop(self):
        if self._saved is not None:
            self.set_mode(self._saved)
            self._saved = None

    def pending(self):
        count = ctypes.c_uint32()
        if not self.kernel32.GetNumberOfConsoleInputEvents(
                ctypes.c_void_p(self.handle), ctypes.byref(count)):
            return 0
        return count.value

    def read(self, timeout):
        """Tuple records available within ``timeout`` seconds."""
        ms = max(0, int(timeout * 1000))
        if self.kernel32.WaitForSingleObject(ctypes.c_void_p(self.handle),
                                             ms) != 0:
            return []
        count = self.pending()
        if not count:
            return []
        buf = (INPUT_RECORD * count)()
        read = ctypes.c_uint32()
        if not self.kernel32.ReadConsoleInputW(
                ctypes.c_void_p(self.handle), buf, count, ctypes.byref(read)):
            return []
        return [record_to_tuple(buf[k]) for k in range(read.value)]

    def write(self, records):
        """Inject tuple records into the input queue (tests, automation)."""
        items = [tuple_to_record(r) for r in records]
        buf = (INPUT_RECORD * len(items))(*items)
        written = ctypes.c_uint32()
        self.kernel32.WriteConsoleInputW(ctypes.c_void_p(self.handle), buf,
                                         len(items), ctypes.byref(written))
        return written.value

    def window_origin(self, output=None):
        """``(left, top)`` of the visible window in the screen buffer."""
        class _SMALL_RECT(ctypes.Structure):
            _fields_ = [('Left', ctypes.c_short), ('Top', ctypes.c_short),
                        ('Right', ctypes.c_short), ('Bottom', ctypes.c_short)]

        class _INFO(ctypes.Structure):
            _fields_ = [('dwSize', _COORD), ('dwCursorPosition', _COORD),
                        ('wAttributes', ctypes.c_uint16),
                        ('srWindow', _SMALL_RECT),
                        ('dwMaximumWindowSize', _COORD)]
        info = _INFO()
        handle = output if output is not None else \
            self.kernel32.GetStdHandle(-11)
        if not self.kernel32.GetConsoleScreenBufferInfo(
                ctypes.c_void_p(handle), ctypes.byref(info)):
            return (0, 0)
        return (info.srWindow.Left, info.srWindow.Top)


def available():
    """Whether the Win32 console API can be used here."""
    return os.name == 'nt' and hasattr(ctypes, 'windll')
