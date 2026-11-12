"""
TERMINAL CAPABILITIES

What the terminal in front of the program can do: colours, Unicode, size,
keyboard protocols (kitty, modifyOtherKeys), mouse encodings, bracketed
paste, focus reporting and synchronized output.

:func:`detect` reads the environment only (no output, works anywhere):
``NO_COLOR``, ``FORCE_COLOR``, ``TERM``, ``COLORTERM``, ``TERM_PROGRAM``,
``KITTY_WINDOW_ID``, ``WT_SESSION``, the locale and whether the streams are
terminals. :func:`probe` asks the terminal itself (kitty keyboard query,
``DECRQM`` for modes, ``XTVERSION``, primary device attributes as the
sentinel every terminal answers) and fills in what it confirms.

>>> caps = detect({'TERM': 'xterm-256color', 'LANG': 'es_MX.UTF-8'},
...               tty=True)
>>> caps.color, caps.unicode
('256', True)
"""

import os
import sys
import time

__all__ = ['Capabilities', 'detect', 'probe', 'color_level', 'unicode_ok',
           'PROBE_QUERY']

_TRUE = ('1', 'true', 'yes', 'on')
_FALSE = ('0', 'false', 'no', 'off')
_TRUECOLOR_PROGRAMS = ('iterm.app', 'wezterm', 'vscode', 'ghostty',
                       'hyper', 'tabby', 'rio', 'warpterminal')
_KITTY_PROGRAMS = ('wezterm', 'ghostty', 'rio')
# Modes asked with DECRQM: bracketed paste, focus, SGR mouse, sync output.
_MODES = {2004: 'bracketed_paste', 1004: 'focus_events', 1006: 'mouse_sgr',
          2026: 'sync_output'}
PROBE_QUERY = ('\x1b[?u' + ''.join('\x1b[?{0}$p'.format(m) for m in _MODES)
               + '\x1b[>0q' + '\x1b[c')


def color_level(env=None, tty=None):
    """``'none'``, ``'16'``, ``'256'`` or ``'truecolor'`` for this terminal.

    ``NO_COLOR`` (any value, as in :func:`flexablelib.colors.supports_color`)
    turns colour off; ``FORCE_COLOR`` forces it
    (``0``/``false`` off, ``1``/empty 16 colours, ``2`` 256, ``3`` true
    colour); ``TERM=dumb`` and output that is no terminal have none.
    """
    env = os.environ if env is None else env
    if 'NO_COLOR' in env:
        return 'none'
    force = env.get('FORCE_COLOR')
    if force is not None:
        force = force.strip().lower()
        if force in _FALSE:
            return 'none'
        if force == '2':
            return '256'
        if force == '3':
            return 'truecolor'
        if force not in ('', '1', 'true', 'yes', 'on'):
            return '16'
        return _guess_level(env) if _guess_level(env) != 'none' else '16'
    term = env.get('TERM', '').lower()
    if term == 'dumb':
        return 'none'
    if tty is None:
        tty = _isatty(sys.stdout)
    if not tty:
        return 'none'
    return _guess_level(env)


def _guess_level(env):
    term = env.get('TERM', '').lower()
    colorterm = env.get('COLORTERM', '').lower()
    program = env.get('TERM_PROGRAM', '').lower()
    if term == 'dumb':
        return 'none'
    if colorterm in ('truecolor', '24bit') or program in _TRUECOLOR_PROGRAMS \
            or env.get('WT_SESSION') or env.get('KITTY_WINDOW_ID') \
            or 'kitty' in term or 'direct' in term:
        return 'truecolor'
    if '256' in term or program == 'apple_terminal':
        return '256'
    return '16'


def unicode_ok(env=None, encoding=None):
    """Whether box drawing and symbols can be printed (else use ASCII)."""
    env = os.environ if env is None else env
    flag = env.get('FLEXABLELIB_ASCII', '').strip().lower()
    if flag in _TRUE:
        return False
    if flag in _FALSE and flag:
        return True
    if env.get('TERM', '').lower() == 'dumb':
        return False
    for name in ('LC_ALL', 'LC_CTYPE', 'LANG'):
        value = env.get(name)
        if value:
            value = value.lower().replace('-', '')
            if 'utf8' in value:
                return True
            if value not in ('c', 'posix'):
                return False
            break
    if env.get('WT_SESSION') or env.get('TERM_PROGRAM'):
        return True
    if encoding:
        return 'utf' in encoding.lower().replace('-', '')
    return False


def _isatty(stream):
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError, OSError):
        return False


class Capabilities(object):
    """What the terminal supports. ``None`` means not known yet."""

    FIELDS = ('color', 'unicode', 'size', 'tty', 'term', 'program', 'dumb',
              'windows', 'kitty_keyboard', 'kitty_flags', 'modify_other_keys',
              'mouse_sgr', 'bracketed_paste', 'focus_events', 'sync_output',
              'version', 'device_attributes', 'probed', 'ci')

    def __init__(self, **values):
        for name in self.FIELDS:
            setattr(self, name, values.get(name))

    @property
    def keyboard(self):
        """The best keyboard protocol: ``'kitty'``, ``'modify'``, ``'legacy'``."""
        if self.kitty_keyboard:
            return 'kitty'
        if self.modify_other_keys:
            return 'modify'
        return 'legacy'

    def as_dict(self):
        return dict((name, getattr(self, name)) for name in self.FIELDS)

    def summary(self):
        """One line per capability, for diagnostics screens."""
        def show(value):
            if value is None:
                return '?'
            if value is True:
                return 'sí'
            if value is False:
                return 'no'
            if isinstance(value, tuple):
                return '×'.join(str(v) for v in value)
            return str(value)
        rows = [('Terminal', self.version or self.program or self.term),
                ('Colores', self.color), ('Unicode', self.unicode),
                ('Tamaño', self.size), ('Teclado', self.keyboard),
                ('Kitty keyboard', self.kitty_keyboard),
                ('Mouse SGR 1006', self.mouse_sgr),
                ('Pegado con corchetes', self.bracketed_paste),
                ('Foco de la ventana', self.focus_events),
                ('Salida sincronizada', self.sync_output)]
        return ['{0}: {1}'.format(k, show(v)) for k, v in rows]

    def __repr__(self):
        return 'Capabilities({0})'.format(', '.join(
            '{0}={1!r}'.format(k, v) for k, v in self.as_dict().items()
            if v is not None))


def detect(env=None, tty=None, stream=None, size=None, platform=None):
    """Capabilities from the environment alone (see the module docstring)."""
    env = dict(os.environ) if env is None else env
    stream = sys.stdout if stream is None else stream
    if tty is None:
        tty = _isatty(stream)
    platform = os.name if platform is None else platform
    term = env.get('TERM', '')
    program = env.get('TERM_PROGRAM', '')
    if size is None:
        try:
            from flexablelib.utils import get_window_size
            size = tuple(get_window_size())
        except Exception:   # pragma: no cover - defensive
            size = (80, 24)
    dumb = term.lower() == 'dumb'
    lowered = term.lower()
    kitty = None
    if 'kitty' in lowered or env.get('KITTY_WINDOW_ID') or \
            program.lower() in _KITTY_PROGRAMS or lowered.startswith('foot'):
        kitty = True
    linux = lowered == 'linux'
    return Capabilities(
        color=color_level(env, tty),
        unicode=unicode_ok(env, getattr(stream, 'encoding', None)),
        size=size, tty=tty, term=term, program=program, dumb=dumb,
        windows=platform == 'nt', kitty_keyboard=kitty,
        modify_other_keys=None,
        mouse_sgr=False if (dumb or linux) else None,
        bracketed_paste=False if dumb else None,
        focus_events=False if (dumb or linux) else None,
        sync_output=None, version=None, device_attributes=None,
        probed=False, ci=bool(env.get('CI')))


def apply_responses(caps, keys):
    """Update ``caps`` from parsed ``'response'`` keys; True once DA1 seen."""
    done = False
    for key in keys:
        if str(key) != 'response' or not key.data:
            continue
        kind, body = key.data[0], key.data[1]
        if kind == 'kitty':
            caps.kitty_keyboard = True
            caps.kitty_flags = int(body) if body.isdigit() else 0
        elif kind == 'decrqm':
            parts = body.split(';')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                field = _MODES.get(int(parts[0]))
                if field:
                    setattr(caps, field, parts[1] in ('1', '2', '3', '4'))
        elif kind == 'dcs' and body.startswith('>|'):
            caps.version = body[2:]
        elif kind == 'da1':
            caps.device_attributes = body
            done = True
    return done


def probe(terminal, timeout=0.2, caps=None):
    """
    Ask ``terminal`` (a started :class:`~.terminal.Terminal`) what it
    supports. Keys typed meanwhile are kept for the terminal's next
    ``read_keys``. Returns the updated :class:`Capabilities`.
    """
    caps = caps if caps is not None else detect(
        stream=terminal.stdout, tty=terminal.is_tty())
    if not terminal.is_tty() or caps.dumb:
        return caps
    terminal.write(PROBE_QUERY)
    deadline = time.monotonic() + timeout
    seen_da = False
    typed = []
    while time.monotonic() < deadline and not seen_da:
        keys = terminal.read_keys(timeout=max(0.0, deadline -
                                              time.monotonic()),
                                  responses=True)
        responses = [k for k in keys if str(k) == 'response']
        typed.extend(k for k in keys if str(k) != 'response')
        seen_da = apply_responses(caps, responses)
    terminal.replay(typed)
    caps.probed = seen_da
    if seen_da:
        for field in _MODES.values():
            if getattr(caps, field) is None:
                setattr(caps, field, False)
        caps.kitty_keyboard = caps.kitty_flags is not None
        caps.modify_other_keys = not caps.kitty_keyboard and \
            caps.term.lower().startswith(('xterm', 'tmux'))
    return caps
