"""
TERMINAL INPUT MODE

:class:`Terminal` puts the console in the mode an interactive interface
needs -- keys delivered one at a time, not echoed, Ctrl-C delivered as a key --
turns on the reporting the application asked for (mouse, bracketed paste,
focus changes, a richer keyboard protocol) and restores everything on exit:

- Linux and macOS: ``termios`` raw mode and escape-sequence input
  (:class:`~.keys.KeyParser`);
- Windows: console input records through the Win32 API
  (:mod:`~.wincon`, with virtual-terminal input when the console has it) and
  the legacy ``msvcrt`` reader when stdin is no console; virtual-terminal
  output through ``SetConsoleMode``.

>>> with Terminal(mouse=True) as term:
...     for key in term.read_keys(timeout=0.1):
...         print(key)

It also reports size changes: ``term.resized()`` is true once after the window
changed size (``SIGWINCH``, console resize records, polling elsewhere).

Keyboard protocols (``keyboard=``):

- ``'auto'`` (default): ask the terminal; use the kitty keyboard protocol
  when it answers, xterm ``modifyOtherKeys`` on other xterm-compatible
  terminals, plain sequences otherwise;
- ``'kitty'``, ``'modify'``, ``'legacy'`` force one.
"""

import os
import sys
import time

from flexablelib.utils import get_window_size

from .keys import KeyParser, WindowsKeyParser

__all__ = ['Terminal', 'WINDOWS']

WINDOWS = os.name == 'nt'

# How long a lone Escape waits for the rest of a possible sequence.
ESCAPE_DELAY = 0.025

# Mouse: button presses (1000), drags (1002), every move (1003, hover),
# SGR encoding (1006) with urxvt (1015) as the fallback encoding.
MOUSE_ON = '\x1b[?1000h\x1b[?1002h\x1b[?1015h\x1b[?1006h'
MOUSE_OFF = '\x1b[?1006l\x1b[?1015l\x1b[?1002l\x1b[?1000l'
HOVER_ON = '\x1b[?1003h'
HOVER_OFF = '\x1b[?1003l'
PASTE_ON = '\x1b[?2004h'
PASTE_OFF = '\x1b[?2004l'
FOCUS_ON = '\x1b[?1004h'
FOCUS_OFF = '\x1b[?1004l'
# Kitty keyboard protocol: push flags (1 disambiguate, 2 report events,
# 8 all keys as escape codes, 16 associated text) and pop them on exit.
KITTY_PUSH = '\x1b[>{0}u'
KITTY_POP = '\x1b[<u'
MODIFY_ON = '\x1b[>4;2m'
MODIFY_OFF = '\x1b[>4;0m'


class Terminal(object):
    """
    Raw keyboard input, mouse reports and resize detection.

    ``stdin`` / ``stdout`` default to the process's. ``mouse=True`` asks for
    clicks, drags and the wheel (``'hover'`` adds plain moves),
    ``paste=True`` (the default) for bracketed paste, so pasted text arrives
    as one ``'paste'`` key, ``focus=True`` for ``'focusin'`` /
    ``'focusout'`` keys when the window gains or loses focus. ``keyboard``
    picks the keyboard protocol (see the module docstring); ``releases``
    keeps key-release events where the protocol reports them.
    ``windows='msvcrt'`` forces the legacy Windows reader.
    """

    def __init__(self, stdin=None, stdout=None, mouse=False, paste=True,
                 focus=False, keyboard='auto', releases=False,
                 windows='auto'):
        self.stdin = stdin if stdin is not None else sys.stdin
        self.stdout = stdout if stdout is not None else sys.stdout
        self.mouse = mouse if mouse in ('hover',) else bool(mouse)
        self.paste = bool(paste)
        self.focus = bool(focus)
        if keyboard not in ('auto', 'kitty', 'modify', 'legacy'):
            raise ValueError('keyboard must be auto, kitty, modify or '
                             'legacy, not {0!r}'.format(keyboard))
        self.keyboard = keyboard
        self.releases = bool(releases)
        self.windows = windows
        self.parser = WindowsKeyParser() if WINDOWS else \
            KeyParser(releases=self.releases)
        self.protocol = 'legacy'
        self.capabilities = None
        self.console = None
        self._saved = None
        self._old_winch = None
        self._resized = False
        self._size = None
        self._active = False
        self._win_mode = None
        self._replay = []

    # -- mode ---------------------------------------------------------------

    def _fileno(self):
        try:
            return self.stdin.fileno()
        except (AttributeError, ValueError, OSError):
            return None

    def is_tty(self):
        """Whether stdin is an interactive terminal (or Windows console)."""
        if self.console is not None:
            return True
        fd = self._fileno()
        try:
            return fd is not None and os.isatty(fd)
        except (OSError, ValueError):   # pragma: no cover - defensive
            return False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
        return False

    def start(self):
        if self._active:
            return self
        self._active = True
        self._size = self.size()
        if WINDOWS:
            self._enable_vt()
            self._start_console()
        else:
            self._enter_cbreak()
            self._install_winch()
        self.write(self._modes(True))
        self._start_keyboard()
        return self

    def stop(self):
        if not self._active:
            return
        self._active = False
        codes = self._modes(False)
        if self.protocol == 'kitty':
            codes = KITTY_POP + codes
        elif self.protocol == 'modify':
            codes = MODIFY_OFF + codes
        self.protocol = 'legacy'
        self.write(codes)
        if WINDOWS:
            self._stop_console()
            self._restore_vt()
        else:
            self._restore_cbreak()
            self._remove_winch()

    def _modes(self, on):
        codes = ''
        if self.mouse:
            codes += MOUSE_ON if on else MOUSE_OFF
            if self.mouse == 'hover':
                codes = codes + HOVER_ON if on else HOVER_OFF + codes
        if self.paste:
            codes += PASTE_ON if on else PASTE_OFF
        if self.focus:
            codes += FOCUS_ON if on else FOCUS_OFF
        return codes

    def _start_keyboard(self):
        """Turn on the keyboard protocol ``keyboard`` asks for."""
        choice = self.keyboard
        if choice == 'legacy' or not self.is_tty() or self.console is not None:
            return
        if choice == 'auto':
            from .capabilities import probe
            self.capabilities = probe(self, timeout=0.15)
            choice = self.capabilities.keyboard
        if choice == 'kitty':
            self.write(KITTY_PUSH.format(3 if self.releases else 1))
        elif choice == 'modify':
            self.write(MODIFY_ON)
        self.protocol = choice
        if isinstance(self.parser, KeyParser):
            self.parser.kitty = choice == 'kitty'

    def write(self, text):
        """Write control codes to the terminal (errors ignored)."""
        if not text:
            return
        try:
            self.stdout.write(text)
            self.stdout.flush()
        except (AttributeError, ValueError, OSError):
            pass

    _write = write

    def _enter_cbreak(self):
        fd = self._fileno()
        if fd is None or not os.isatty(fd):
            return
        import termios
        self._saved = termios.tcgetattr(fd)
        mode = termios.tcgetattr(fd)
        # Keys one at a time, no echo, Ctrl-C/Z/S/Q delivered as keys, CR not
        # turned into LF. Output processing stays on so '\n' still returns
        # the carriage.
        mode[0] &= ~(termios.IXON | termios.ICRNL | termios.BRKINT |
                     termios.INPCK | termios.ISTRIP)
        mode[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG |
                     termios.IEXTEN)
        mode[6][termios.VMIN] = 0
        mode[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, mode)

    def _restore_cbreak(self):
        if self._saved is None:
            return
        import termios
        termios.tcsetattr(self._fileno(), termios.TCSADRAIN, self._saved)
        self._saved = None

    def _install_winch(self):
        import signal
        if not hasattr(signal, 'SIGWINCH'):   # pragma: no cover
            return
        try:
            self._old_winch = signal.signal(signal.SIGWINCH, self._on_winch)
        except ValueError:   # not the main thread
            self._old_winch = None

    def _remove_winch(self):
        import signal
        if self._old_winch is not None:
            signal.signal(signal.SIGWINCH, self._old_winch)
            self._old_winch = None

    def _on_winch(self, *args):
        self._resized = True

    def _start_console(self):
        """Console input records when stdin is a Windows console."""
        from . import wincon
        if self.windows == 'msvcrt' or not wincon.available():
            return
        try:
            console = wincon.ConsoleInput(stdin=self.stdin)
            ok = console.start(mouse=bool(self.mouse),
                               vt=self.windows != 'records')
        except (AttributeError, OSError, ValueError):   # pragma: no cover
            return
        if not ok:                                      # pragma: no cover
            return
        self.console = console
        self.parser = wincon.ConsoleInputTranslator(
            vt=console.vt, origin=console.window_origin())
        self.protocol = 'windows-vt' if console.vt else 'windows-console'

    def _stop_console(self):
        if self.console is not None:
            self.console.stop()
            self.console = None
            self.parser = WindowsKeyParser()

    def _enable_vt(self):   # pragma: no cover - Windows only
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)      # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                self._win_mode = (handle, mode.value)
                # ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(handle, mode.value | 0x0001 | 0x0004)
        except (AttributeError, OSError):
            self._win_mode = None

    def _restore_vt(self):   # pragma: no cover - Windows only
        if self._win_mode is None:
            return
        import ctypes
        handle, mode = self._win_mode
        ctypes.windll.kernel32.SetConsoleMode(handle, mode)
        self._win_mode = None

    # -- size ---------------------------------------------------------------

    def size(self):
        """``(columns, lines)`` of the terminal."""
        return get_window_size()

    def resized(self):
        """True once after the window changed size."""
        size = self.size()
        changed = self._resized or size != self._size
        self._resized = False
        self._size = size
        return changed

    # -- input --------------------------------------------------------------

    def _read_raw(self, timeout):
        """Whatever input is available within ``timeout`` seconds."""
        if self.console is not None:
            return self.console.read(timeout)
        if WINDOWS:
            import msvcrt
            deadline = time.monotonic() + max(0.0, timeout)
            chars = []
            while True:
                while msvcrt.kbhit():
                    chars.append(msvcrt.getwch())
                if chars or time.monotonic() >= deadline:
                    return ''.join(chars)
                time.sleep(0.005)
        fd = self._fileno()
        if fd is None:
            time.sleep(max(0.0, timeout))
            return b''
        import select
        try:
            ready, _, _ = select.select([fd], [], [], max(0.0, timeout))
        except (InterruptedError, OSError, ValueError):
            return b''
        if not ready:
            return b''
        try:
            return os.read(fd, 4096)
        except (BlockingIOError, InterruptedError):
            return b''

    def replay(self, keys):
        """Hand ``keys`` back: the next ``read_keys`` returns them first."""
        self._replay.extend(keys)

    def _filter(self, keys, responses):
        out = []
        for key in keys:
            name = str(key)
            if name == 'resize':
                self._resized = True
            elif name == 'response' and not responses:
                continue
            else:
                out.append(key)
        return out

    def read_keys(self, timeout=None, responses=False):
        """
        The keys pressed within ``timeout`` seconds (``None``: wait for one).
        A lone Escape is reported after a short pause with no follow-up.
        Answers to terminal queries are dropped unless ``responses``.
        """
        keys, self._replay = self._replay, []
        if keys:
            return keys
        while True:
            data = self._read_raw(0.05 if timeout is None else timeout)
            if data:
                keys.extend(self.parser.feed(data))
            if self.parser.pending:
                more = self._read_raw(ESCAPE_DELAY)
                if more:
                    keys.extend(self.parser.feed(more))
                    continue
                keys.extend(self.parser.flush())
            keys = self._filter(keys, responses)
            if keys or timeout is not None or self._resized:
                return keys
