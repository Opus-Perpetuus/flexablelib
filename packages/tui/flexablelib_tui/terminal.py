"""
TERMINAL INPUT MODE

:class:`Terminal` puts the console in the mode an interactive interface
needs -- keys delivered one at a time, not echoed, Ctrl-C delivered as a key --
and restores it on exit, on Linux and macOS (``termios``) and on Windows
(``msvcrt`` plus virtual-terminal output through ``SetConsoleMode``).

>>> with Terminal() as term:
...     for key in term.read_keys(timeout=0.1):
...         print(key)

It also reports size changes: ``term.resized()`` is true once after the window
changed size (``SIGWINCH`` where there is one, polling elsewhere).
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

MOUSE_ON = '\x1b[?1000h\x1b[?1006h'
MOUSE_OFF = '\x1b[?1006l\x1b[?1000l'
PASTE_ON = '\x1b[?2004h'
PASTE_OFF = '\x1b[?2004l'


class Terminal(object):
    """
    Raw keyboard input and resize detection for an interactive session.

    ``stdin`` / ``stdout`` default to the process's. ``mouse=True`` asks the
    terminal for mouse reports (clicks and the wheel), ``paste=True`` (the
    default) for bracketed paste, so pasted text arrives as one ``'paste'``
    key instead of keystrokes.
    """

    def __init__(self, stdin=None, stdout=None, mouse=False, paste=True):
        self.stdin = stdin if stdin is not None else sys.stdin
        self.stdout = stdout if stdout is not None else sys.stdout
        self.mouse = bool(mouse)
        self.paste = bool(paste)
        self.parser = WindowsKeyParser() if WINDOWS else KeyParser()
        self._saved = None
        self._old_winch = None
        self._resized = False
        self._size = None
        self._active = False
        self._win_mode = None

    # -- mode ---------------------------------------------------------------

    def _fileno(self):
        try:
            return self.stdin.fileno()
        except (AttributeError, ValueError, OSError):
            return None

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
        if WINDOWS:   # pragma: no cover - exercised on the Windows CI job
            self._enable_vt()
        else:
            self._enter_cbreak()
            self._install_winch()
        codes = (MOUSE_ON if self.mouse else '') + \
            (PASTE_ON if self.paste else '')
        if codes:
            self._write(codes)
        return self

    def stop(self):
        if not self._active:
            return
        self._active = False
        codes = (MOUSE_OFF if self.mouse else '') + \
            (PASTE_OFF if self.paste else '')
        if codes:
            self._write(codes)
        if WINDOWS:   # pragma: no cover - exercised on the Windows CI job
            self._restore_vt()
        else:
            self._restore_cbreak()
            self._remove_winch()

    def _write(self, text):
        try:
            self.stdout.write(text)
            self.stdout.flush()
        except (AttributeError, ValueError, OSError):
            pass

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
        if WINDOWS:   # pragma: no cover - Windows only
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

    def read_keys(self, timeout=None):
        """
        The keys pressed within ``timeout`` seconds (``None``: wait for one).
        A lone Escape is reported after a short pause with no follow-up.
        """
        keys = []
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
            if keys or timeout is not None or self._resized:
                return keys
