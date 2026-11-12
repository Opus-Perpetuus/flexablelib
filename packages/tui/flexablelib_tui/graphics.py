"""
Pictures in the terminal.

Detects what the terminal can show and turns pictures into escape
sequences, best method first:

* **kitty graphics protocol** -- kitty, Ghostty, WezTerm, Warp; with
  Unicode placeholders (kitty 0.28+, Ghostty) the picture is ordinary text
  that layouts, scrolling and tmux (``allow-passthrough on``) handle.
* **iTerm2 inline images** (OSC 1337) -- iTerm2, WezTerm, VS Code, Konsole,
  mintty, rio.
* **sixel** -- xterm (``-ti vt340``), foot, mlterm, contour, Windows
  Terminal 1.22+, Konsole, tmux 3.4+ built with sixel.
* Text: Unicode half blocks, quadrants, sextants or braille in truecolor,
  256 or 16 colours (or mono), then ASCII art.
* A link (OSC 8) that opens the picture in the browser, and with no
  browser or display a warning instead.

Detection: environment variables first (:func:`guess`), then -- when both
standard streams are terminals -- one short query (:func:`query`,
:func:`probe_terminal`): kitty graphics query, cell size in pixels
(``CSI 16 t`` / ``CSI 14 t`` and ``TIOCGWINSZ``), sixel colour registers
(XTSMGRAPHICS), XTVERSION and DA1 (attribute 4 = sixel). The result is
cached. ``FLEXABLELIB_IMAGE=kitty|iterm|sixel|blocks|half|quadrant|sextant|
braille|ascii|link|none`` forces a method.

Frames never carry the (large, width-less) picture sequences: a picture is
blank cells plus a zero-width mark (``ESC ] 8971 ; id BEL``) that
:func:`expand` replaces when the frame is written, so widths, layouts and
frame diffs keep working; :func:`render_diff` redraws a picture whenever a
line it covers changes and deletes kitty images that left the screen.
"""

import base64
import os
import re
import sys
import time
import zlib
from collections import OrderedDict

from flexablelib import _frames as _fx
from flexablelib import _images as _img

__all__ = ['GraphicsInfo', 'METHODS', 'TEXT_MODES', 'guess', 'query',
           'probe_terminal', 'detect', 'reset_cache', 'choose',
           'apply_responses', 'cell_size', 'kitty_sequence', 'kitty_delete',
           'kitty_placeholder_rows', 'iterm_sequence', 'sixel_sequence',
           'tmux_wrap', 'register', 'mark', 'expand', 'marks_in', 'cleanup',
           'render_diff', 'file_url', 'hyperlink', 'browser_available',
           'open_external', 'GRAPHICS_QUERY', 'DIACRITICS', 'PLACEHOLDER']

METHODS = ('kitty', 'iterm', 'sixel', 'half', 'quadrant', 'sextant',
           'braille', 'ascii', 'link', 'none')
TEXT_MODES = ('half', 'quadrant', 'sextant', 'braille', 'ascii')
MARK = _fx.GRAPHICS_MARK
_MARK_RE = re.compile(re.escape(MARK) + r'([0-9a-f]+)\x07')
#: kitty graphics query, cell size, window size, sixel colour registers.
GRAPHICS_QUERY = ('\x1b_Gi=31,s=1,v=1,a=q,t=d,f=24;AAAA\x1b\\'
                  '\x1b[16t\x1b[14t\x1b[?1;1;0S')
DEFAULT_CELL = (10, 20)
_TRUE = ('1', 'true', 'yes', 'on')

# Row/column diacritics of the kitty Unicode placeholder (U+10EEEE).
_DIACRITIC_RANGES = (
    (0x305, 0x305), (0x30D, 0x30E), (0x310, 0x310), (0x312, 0x312),
    (0x33D, 0x33F), (0x346, 0x346), (0x34A, 0x34C), (0x350, 0x352),
    (0x357, 0x357), (0x35B, 0x35B), (0x363, 0x36F), (0x483, 0x487),
    (0x592, 0x595), (0x597, 0x599), (0x59C, 0x5A1), (0x5A8, 0x5A9),
    (0x5AB, 0x5AC), (0x5AF, 0x5AF), (0x5C4, 0x5C4), (0x610, 0x617),
    (0x657, 0x65B), (0x65D, 0x65E), (0x6D6, 0x6DC), (0x6DF, 0x6E2),
    (0x6E4, 0x6E4), (0x6E7, 0x6E8), (0x6EB, 0x6EC), (0x730, 0x730),
    (0x732, 0x733), (0x735, 0x736), (0x73A, 0x73A), (0x73D, 0x73D),
    (0x73F, 0x741), (0x743, 0x743), (0x745, 0x745), (0x747, 0x747),
    (0x749, 0x74A), (0x7EB, 0x7F1), (0x7F3, 0x7F3), (0x816, 0x819),
    (0x81B, 0x823), (0x825, 0x827), (0x829, 0x82D), (0x951, 0x951),
    (0x953, 0x954), (0xF82, 0xF83), (0xF86, 0xF87), (0x135D, 0x135F),
    (0x17DD, 0x17DD), (0x193A, 0x193A), (0x1A17, 0x1A17), (0x1A75, 0x1A7C),
    (0x1B6B, 0x1B6B), (0x1B6D, 0x1B73), (0x1CD0, 0x1CD2), (0x1CDA, 0x1CDB),
    (0x1CE0, 0x1CE0), (0x1DC0, 0x1DC1), (0x1DC3, 0x1DC9), (0x1DCB, 0x1DCC),
    (0x1DD1, 0x1DE6), (0x1DFE, 0x1DFE), (0x20D0, 0x20D1), (0x20D4, 0x20D7),
    (0x20DB, 0x20DC), (0x20E1, 0x20E1), (0x20E7, 0x20E7), (0x20E9, 0x20E9),
    (0x20F0, 0x20F0), (0x2CEF, 0x2CF1), (0x2DE0, 0x2DFF), (0xA66F, 0xA66F),
    (0xA67C, 0xA67D), (0xA6F0, 0xA6F1), (0xA8E0, 0xA8F1), (0xAAB0, 0xAAB0),
    (0xAAB2, 0xAAB3), (0xAAB7, 0xAAB8), (0xAABE, 0xAABF), (0xAAC1, 0xAAC1),
    (0xFE20, 0xFE26), (0x10A0F, 0x10A0F), (0x10A38, 0x10A38),
    (0x1D185, 0x1D189), (0x1D1AA, 0x1D1AD), (0x1D242, 0x1D244),)


def _diacritics():
    out = []
    for start, end in _DIACRITIC_RANGES:
        out.extend(chr(c) for c in range(start, end + 1))
    return out


DIACRITICS = _diacritics()
PLACEHOLDER = chr(0x10EEEE)


# +---------------------------------------------------------------------------+
# Capabilities

class GraphicsInfo(object):
    """What the terminal can show. ``order`` lists the pixel protocols to
    try, best first; ``reasons`` explains each decision."""

    FIELDS = ('kitty', 'kitty_placeholders', 'iterm', 'sixel',
              'sixel_colors', 'cell', 'cell_known', 'color', 'unicode',
              'terminal', 'version', 'tmux', 'passthrough', 'probed', 'tty',
              'dumb', 'order', 'reasons')

    def __init__(self, **values):
        for name in self.FIELDS:
            setattr(self, name, values.get(name))
        if self.order is None:
            self.order = []
        if self.reasons is None:
            self.reasons = []
        if self.cell is None:
            self.cell = DEFAULT_CELL

    @property
    def pixel_methods(self):
        """The pixel protocols this terminal accepts, best first."""
        found = [m for m in self.order if getattr(self, m)]
        for m in ('kitty', 'iterm', 'sixel'):
            if getattr(self, m) and m not in found:
                found.append(m)
        return found

    def best(self):
        """The method :func:`choose` would pick without overrides."""
        return choose(self)[0]

    def as_dict(self):
        return dict((k, getattr(self, k)) for k in self.FIELDS)

    def summary(self):
        def show(v):
            return '?' if v is None else 'sí' if v is True else \
                'no' if v is False else str(v)
        rows = [('Terminal', self.version or self.terminal),
                ('kitty graphics', self.kitty),
                ('  marcadores Unicode', self.kitty_placeholders),
                ('iTerm2 inline', self.iterm), ('sixel', self.sixel),
                ('Celda (px)', '{0}×{1}{2}'.format(
                    self.cell[0], self.cell[1],
                    '' if self.cell_known else ' (supuesto)')),
                ('Colores', self.color), ('Unicode', self.unicode),
                ('tmux', self.tmux), ('Método', self.best())]
        return ['{0}: {1}'.format(k, show(v)) for k, v in rows]

    def __repr__(self):
        return 'GraphicsInfo({0})'.format(', '.join(
            '{0}={1!r}'.format(k, v) for k, v in self.as_dict().items()
            if v not in (None, [], ())))


def _version_tuple(text):
    nums = re.findall(r'\d+', text or '')
    return tuple(int(n) for n in nums[:3])


def _tmux_client(env):
    """(termname, features, passthrough) of the tmux client, or None."""
    if not env.get('TMUX'):
        return None
    import shutil
    import subprocess
    if not shutil.which('tmux'):
        return ('', '', False)
    try:
        out = subprocess.run(
            ['tmux', 'display-message', '-p',
             '#{client_termname}|#{client_termfeatures}|#{version}'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=1,
            universal_newlines=True).stdout.strip()
        passthrough = subprocess.run(
            ['tmux', 'show', '-gv', 'allow-passthrough'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=1,
            universal_newlines=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ('', '', False)
    parts = (out.split('|') + ['', '', ''])[:3]
    return (parts[0], parts[1] + ' tmux=' + parts[2],
            passthrough in ('on', 'all'))


def guess(env=None, platform=None, tmux=None):
    """:class:`GraphicsInfo` from the environment alone (no output)."""
    from . import capabilities
    env = dict(os.environ) if env is None else env
    platform = os.name if platform is None else platform
    term = env.get('TERM', '').lower()
    program = env.get('TERM_PROGRAM', '').lower()
    info = GraphicsInfo(color=capabilities.color_level(env, True),
                        unicode=capabilities.unicode_ok(env, 'utf-8'),
                        terminal=env.get('TERM_PROGRAM') or env.get('TERM'),
                        dumb=term == 'dumb', probed=False)
    why = info.reasons
    if info.dumb or term == 'linux':
        info.kitty = info.iterm = info.sixel = False
        why.append('TERM={0}: sin gráficos'.format(term))
        return info
    if 'kitty' in term or env.get('KITTY_WINDOW_ID'):
        info.kitty = info.kitty_placeholders = True
        info.terminal = 'kitty'
        why.append('kitty (TERM / KITTY_WINDOW_ID)')
    if program == 'ghostty' or 'ghostty' in term or \
            env.get('GHOSTTY_RESOURCES_DIR'):
        info.kitty = info.kitty_placeholders = True
        info.terminal = 'ghostty'
        why.append('Ghostty')
    if program == 'wezterm' or env.get('WEZTERM_EXECUTABLE') or \
            env.get('WEZTERM_PANE'):
        info.iterm = True
        info.kitty = True
        info.sixel = True
        info.order = ['iterm', 'kitty', 'sixel']
        info.terminal = 'WezTerm'
        why.append('WezTerm: iTerm2, kitty y sixel')
    if program == 'iterm.app':
        info.iterm = True
        info.sixel = True
        info.order = ['iterm', 'sixel']
        info.terminal = 'iTerm2'
        why.append('iTerm2')
    if program == 'vscode':
        info.iterm = True
        info.sixel = True
        info.order = ['iterm', 'sixel']
        info.terminal = 'VS Code'
        why.append('VS Code (con terminal.integrated.enableImages)')
    if program == 'mintty' or env.get('MINTTY_SHORTCUT'):
        info.iterm = info.sixel = True
        info.order = ['iterm', 'sixel']
        info.terminal = 'mintty'
        why.append('mintty')
    if env.get('KONSOLE_VERSION'):
        version = _version_tuple(env.get('KONSOLE_VERSION'))
        ok = not version or version[0] >= 220400 or version[0] >= 22
        info.iterm = info.sixel = ok
        info.order = ['iterm', 'sixel']
        info.terminal = 'Konsole'
        why.append('Konsole {0}'.format(env.get('KONSOLE_VERSION')))
    if program == 'warpterminal':
        info.kitty = True
        info.terminal = 'Warp'
        why.append('Warp (kitty)')
    if program == 'rio':
        info.iterm = info.sixel = True
        info.order = ['iterm', 'sixel']
        info.terminal = 'rio'
    if term.startswith(('foot', 'mlterm', 'contour', 'yaft')) or \
            program in ('contour',):
        info.sixel = True
        why.append('{0}: sixel'.format(term or program))
    if program == 'apple_terminal':
        info.kitty = info.iterm = info.sixel = False
        info.terminal = 'Terminal.app'
        why.append('Terminal.app: sin protocolos de imagen')
    if env.get('WT_SESSION') and info.sixel is None:
        why.append('Windows Terminal: sixel solo si DA1 lo anuncia (1.22+)')
    if platform == 'nt' and info.kitty:
        info.kitty = False
        why.append('Windows: ConPTY no deja pasar APC (kitty)')
    if term.startswith('screen') or env.get('STY'):
        info.kitty = info.iterm = info.sixel = False
        why.append('GNU screen: sin gráficos')
    client = _tmux_client(env) if tmux is None else tmux
    if client is not None:
        name, features, passthrough = client
        info.tmux = name or True
        info.passthrough = passthrough
        info.iterm = False
        inner_kitty = 'kitty' in name or 'ghostty' in name
        info.kitty = bool(inner_kitty and passthrough)
        info.kitty_placeholders = info.kitty
        info.sixel = 'sixel' in features
        info.order = ['kitty', 'sixel']
        why.append('tmux (cliente {0!r}{1})'.format(
            name, ', passthrough' if passthrough else ''))
    if not info.order:
        info.order = ['kitty', 'iterm', 'sixel']
    return info


def apply_responses(info, keys):
    """Update ``info`` from parsed ``'response'`` keys; True once DA1 seen."""
    done = False
    for key in keys:
        if str(key) != 'response' or not key.data:
            continue
        kind, body = key.data[0], key.data[1]
        if kind == 'apc' and body.startswith('Gi=31'):
            info.kitty = body.endswith('OK')
            info.reasons.append('consulta kitty: {0}'.format(
                'OK' if info.kitty else body))
        elif kind == 'window':
            parts = body.split(';')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                code, h, w = (int(p) for p in parts)
                if code == 6 and w > 0 and h > 0:
                    info.cell = (w, h)
                    info.cell_known = True
                elif code == 4 and w > 0 and h > 0 and not info.cell_known:
                    info._window_px = (w, h)
        elif kind == 'csi?S':
            parts = body.split(';')
            if len(parts) >= 3 and parts[0] == '1' and parts[1] == '0' \
                    and parts[2].isdigit():
                info.sixel_colors = int(parts[2])
        elif kind == 'dcs' and body.startswith('>|'):
            info.version = body[2:]
            low = info.version.lower()
            if low.startswith('kitty'):
                info.kitty_placeholders = _version_tuple(low) >= (0, 28)
            elif 'ghostty' in low:
                info.kitty_placeholders = True
            elif 'wezterm' in low:
                info.iterm = True
            elif 'iterm2' in low:
                info.iterm = True
        elif kind == 'da1':
            attrs = body.split(';')
            if info.sixel is None or '4' in attrs:
                info.sixel = '4' in attrs
            if '4' in attrs:
                info.reasons.append('DA1 anuncia sixel')
            done = True
    return done


def cell_size(stream=None):
    """``(width, height)`` of a cell in pixels from ``TIOCGWINSZ``, or
    ``None`` when the terminal does not report pixels."""
    try:
        import fcntl
        import struct
        import termios
        fd = (stream or sys.stdout).fileno()
        rows, cols, xpix, ypix = struct.unpack('HHHH', fcntl.ioctl(
            fd, termios.TIOCGWINSZ, b'\0' * 8))
    except Exception:
        return None
    if xpix and ypix and cols and rows:
        return max(1, xpix // cols), max(1, ypix // rows)
    return None


def _finish(info):
    if not info.cell_known:
        win = getattr(info, '_window_px', None)
        if win:
            try:
                from flexablelib.utils import get_window_size
                cols, rows = get_window_size()
                info.cell = (max(1, win[0] // cols), max(1, win[1] // rows))
                info.cell_known = True
            except Exception:   # pragma: no cover - defensive
                pass
    if info.kitty is False:
        info.kitty_placeholders = False
    return info


def _query_text(info):
    """The query sent to the terminal: kitty graphics, cell and window
    size, sixel colour registers (not asked of kitty, which has no sixel),
    XTVERSION and DA1 last (every terminal answers DA1)."""
    text = GRAPHICS_QUERY
    if info.terminal == 'kitty':
        text = text.replace('\x1b[?1;1;0S', '')
    return text + '\x1b[>0q\x1b[c'


def _query_wanted(info, env):
    if info.dumb or info.tmux:
        return False
    if (env.get('TERM_PROGRAM') or '').lower() == 'apple_terminal':
        return False       # prints APC queries as text
    if (env.get('TERM') or '').lower() in ('linux', 'dumb'):
        return False
    return True


def query(info=None, env=None, timeout=0.3, tty_path='/dev/tty'):
    """
    Ask the controlling terminal directly (POSIX, both standard streams on
    a terminal): writes :data:`GRAPHICS_QUERY` plus ``XTVERSION`` and DA1 to
    ``/dev/tty`` in raw mode and reads the answers until DA1 or
    ``timeout``. Returns the updated :class:`GraphicsInfo`.
    """
    env = dict(os.environ) if env is None else env
    info = info if info is not None else guess(env)
    if os.name == 'nt' or not _query_wanted(info, env):
        return info
    try:
        import select
        import termios
        import tty
        fd = os.open(tty_path, os.O_RDWR | os.O_NOCTTY)
    except Exception:
        return info
    from .keys import KeyParser
    try:
        old = termios.tcgetattr(fd)
    except Exception:
        os.close(fd)
        return info
    parser = KeyParser()
    keys = []
    try:
        tty.setraw(fd)
        os.write(fd, _query_text(info).encode())
        deadline = time.monotonic() + timeout
        done = False
        while not done and time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [],
                                        max(0, deadline - time.monotonic()))
            if not ready:
                break
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            new = parser.feed(chunk)
            keys.extend(new)
            done = apply_responses(info, new)
        info.probed = done
    except Exception:   # pragma: no cover - defensive
        pass
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        finally:
            os.close(fd)
    return _finish(info)


def probe_terminal(terminal, timeout=0.3, env=None):
    """Ask a started :class:`~flexablelib_tui.Terminal` (used by ``App``);
    keys typed meanwhile are replayed. Stores the result for :func:`detect`."""
    global _CACHE
    env = dict(os.environ) if env is None else env
    info = guess(env)
    if terminal.is_tty() and _query_wanted(info, env):
        terminal.write(_query_text(info))
        deadline = time.monotonic() + timeout
        typed = []
        done = False
        while time.monotonic() < deadline and not done:
            keys = terminal.read_keys(timeout=max(
                0.0, deadline - time.monotonic()), responses=True)
            typed.extend(k for k in keys if str(k) != 'response')
            done = apply_responses(info, [k for k in keys
                                          if str(k) == 'response'])
        terminal.replay(typed)
        info.probed = done
    px = cell_size(getattr(terminal, 'stdout', None))
    if px and not info.cell_known:
        info.cell, info.cell_known = px, True
    _CACHE = (_env_key(env), _finish(info))
    return info


_CACHE = None


def _env_key(env):
    return tuple(env.get(k) for k in (
        'TERM', 'TERM_PROGRAM', 'KITTY_WINDOW_ID', 'WEZTERM_PANE', 'TMUX',
        'KONSOLE_VERSION', 'WT_SESSION', 'NO_COLOR', 'FORCE_COLOR',
        'COLORTERM', 'LANG', 'LC_ALL', 'FLEXABLELIB_ASCII'))


def reset_cache():
    global _CACHE
    _CACHE = None


def detect(env=None, probe=None, refresh=False):
    """
    The cached :class:`GraphicsInfo` for this process. ``probe`` (default:
    when both standard streams are terminals) asks the terminal once.
    """
    global _CACHE
    env = dict(os.environ) if env is None else env
    key = _env_key(env)
    if not refresh and _CACHE is not None and _CACHE[0] == key:
        return _CACHE[1]
    info = guess(env)
    info.tty = _isatty(sys.stdout) and _isatty(sys.stdin)
    if probe is None:
        probe = info.tty
    if probe:
        info = query(info, env)
    px = cell_size()
    if px and not info.cell_known:
        info.cell, info.cell_known = px, True
    _CACHE = (key, _finish(info))
    return info


def _isatty(stream):
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def choose(info, force=None, env=None, screen_reader=None, ascii=None,
           color=None, blocks=None):
    """
    ``(method, text_mode, reason)`` for showing a picture. ``method`` is
    one of ``'kitty'``, ``'iterm'``, ``'sixel'``, ``'text'`` (blocks or
    ASCII, with ``text_mode``), ``'link'``, ``'alt'`` (screen readers,
    ``TERM=dumb``) or ``'none'``.
    """
    from . import accessibility as _a11y
    env = os.environ if env is None else env
    force = (force or env.get('FLEXABLELIB_IMAGE') or '').strip().lower()
    if force in ('auto',):
        force = ''
    reader = _a11y.settings.screen_reader if screen_reader is None \
        else screen_reader
    use_ascii = _a11y.settings.ascii if ascii is None else ascii
    if color is None:
        color = info.color or 'truecolor'
    unicode_ok = info.unicode is not False and not use_ascii
    if reader or info.dumb:
        return 'alt', None, 'lector de pantalla o TERM=dumb: texto alternativo'
    if force == 'none':
        return 'none', None, 'FLEXABLELIB_IMAGE=none'
    if force == 'link':
        return 'link', None, 'enlace pedido'
    if force in ('kitty', 'iterm', 'sixel'):
        return force, None, 'método pedido'
    if force in TEXT_MODES or force == 'blocks':
        mode = (blocks or 'half') if force == 'blocks' else force
        if not unicode_ok and mode != 'ascii':
            mode = 'ascii'
        return 'text', mode, 'método pedido'
    if not use_ascii:
        for method in info.pixel_methods:
            return method, None, info.reasons[-1] if info.reasons else method
    if not unicode_ok:
        return 'text', 'ascii', 'sin Unicode: ASCII'
    if color == 'none':
        return 'text', 'braille', 'sin color: braille'
    return 'text', blocks or 'half', 'bloques Unicode'


# +---------------------------------------------------------------------------+
# Escape sequences

def tmux_wrap(seq):
    """``seq`` inside a tmux passthrough (``allow-passthrough on``)."""
    return '\x1bPtmux;' + seq.replace('\x1b', '\x1b\x1b') + '\x1b\\'


def kitty_sequence(png, image_id, cols=None, rows=None, placeholder=False,
                   tmux=False, chunk=4096):
    """Transmit-and-show APC sequence(s) for PNG bytes. With
    ``placeholder`` the image becomes a virtual placement shown wherever
    :func:`kitty_placeholder_rows` text is drawn."""
    data = base64.standard_b64encode(png).decode('ascii')
    keys = ['a=T', 'f=100', 'i={0}'.format(image_id), 'q=2']
    if placeholder:
        keys.append('U=1')
    else:
        keys += ['p=1', 'C=1']
    if cols:
        keys.append('c={0}'.format(cols))
    if rows:
        keys.append('r={0}'.format(rows))
    out = []
    parts = [data[i:i + chunk] for i in range(0, len(data), chunk)] or ['']
    for n, part in enumerate(parts):
        more = 1 if n < len(parts) - 1 else 0
        head = ','.join(keys) + ',' if n == 0 else ''
        seq = '\x1b_G{0}m={1};{2}\x1b\\'.format(head, more, part)
        out.append(tmux_wrap(seq) if tmux else seq)
    return ''.join(out)


def kitty_delete(image_id, tmux=False):
    seq = '\x1b_Ga=d,d=I,i={0},q=2\x1b\\'.format(image_id)
    return tmux_wrap(seq) if tmux else seq


def kitty_placeholder_rows(image_id, cols, rows):
    """The text that shows a placeholder image: one string per row."""
    fg = '\x1b[38;2;{0};{1};{2}m'.format((image_id >> 16) & 255,
                                         (image_id >> 8) & 255,
                                         image_id & 255)
    lines = []
    for r in range(rows):
        cells = ''.join(PLACEHOLDER + DIACRITICS[r] + DIACRITICS[c]
                        for c in range(cols))
        lines.append(fg + cells + '\x1b[39m')
    return lines


def iterm_sequence(data, width_px=None, height_px=None, name=None,
                   cols=None, rows=None):
    """OSC 1337 inline image for encoded image bytes (PNG, JPEG, GIF)."""
    args = ['inline=1', 'size={0}'.format(len(data))]
    if name:
        args.append('name=' + base64.b64encode(name.encode()).decode())
    if width_px:
        args.append('width={0}px'.format(width_px))
    elif cols:
        args.append('width={0}'.format(cols))
    if height_px:
        args.append('height={0}px'.format(height_px))
    elif rows:
        args.append('height={0}'.format(rows))
    args.append('preserveAspectRatio=1')
    return '\x1b]1337;File={0}:{1}\x07'.format(
        ';'.join(args), base64.b64encode(data).decode('ascii'))


def sixel_sequence(bitmap, colors=255):
    """DCS sixel for a :class:`~flexablelib._images.Bitmap` (transparent
    where alpha < 128)."""
    palette, indices = _img.quantize(bitmap.data, bitmap.width,
                                     bitmap.height, colors, 128)
    return _img.sixel_encode(indices, bitmap.width, bitmap.height, palette)


# +---------------------------------------------------------------------------+
# Marks: pictures inside plain-text frames

_PAYLOADS = OrderedDict()
_MAX_PAYLOADS = 64


def register(payload, cols, rows, kind, image_id=None, tmux=False):
    """Store a picture's escape sequence; returns its mark id (hex)."""
    key = '{0:x}'.format(zlib.crc32(payload.encode('utf-8', 'replace')) ^
                         (cols << 20) ^ (rows << 8) ^
                         zlib.crc32(kind.encode()))
    _PAYLOADS[key] = (payload, cols, rows, kind, image_id, tmux)
    _PAYLOADS.move_to_end(key)
    while len(_PAYLOADS) > _MAX_PAYLOADS:
        _PAYLOADS.popitem(last=False)
    return key


def mark(key):
    """The zero-width mark that stands for registered picture ``key``."""
    return MARK + key + '\x07'


def _skip_columns(text, start, cols):
    """Index in ``text`` after ``cols`` visible columns from ``start``,
    keeping escape sequences out of the count; plus the escapes skipped."""
    i = start
    kept = []
    n = len(text)
    while i < n and cols > 0:
        if text[i] == '\x1b':
            m = _fx_seq(text, i)
            if m:
                kept.append(text[i:i + m])
                i += m
                continue
        w = _fx.visible_width(text[i])
        cols -= w
        i += 1
    return i, ''.join(kept)


def _fx_seq(text, i):
    from flexablelib.text_width import _ANSI_RE
    m = _ANSI_RE.match(text, i)
    return m.end() - i if m else 0


def _payload_for(key):
    return _PAYLOADS.get(key)


def expand(text):
    """``text`` with every picture mark replaced by its escape sequence:
    kitty placeholders get their image transmitted; cursor-placed pictures
    (kitty, iTerm2, sixel) are drawn from the top-left cell of their area
    with the cursor saved and restored, and the blank cells under the
    mark are skipped (cursor forward) instead of written over the
    picture. Unknown marks are dropped."""
    if MARK not in text:
        return text
    out = []
    pos = 0
    for m in _MARK_RE.finditer(text):
        if m.start() < pos:
            continue
        out.append(text[pos:m.start()])
        entry = _payload_for(m.group(1))
        pos = m.end()
        if entry is None:
            continue
        payload, cols, rows, kind = entry[:4]
        if kind == 'placeholder':
            out.append(payload)
            continue
        up = '\x1b[{0}A'.format(rows - 1) if rows > 1 else ''
        end, escapes = _skip_columns(text, pos, cols)
        out.append('\x1b7' + up + payload + '\x1b8' + escapes +
                   '\x1b[{0}C'.format(cols))
        pos = end
    out.append(text[pos:])
    return ''.join(out)


def marks_in(lines):
    """``[(row, key, rows, kind)]`` for the picture marks in ``lines``."""
    found = []
    for i, line in enumerate(lines):
        if MARK in line:
            for m in _MARK_RE.finditer(line):
                entry = _PAYLOADS.get(m.group(1))
                rows = entry[2] if entry else 1
                kind = entry[3] if entry else ''
                found.append((i, m.group(1), rows, kind))
    return found


def cleanup(old_lines, new_lines):
    """Escape sequences that delete kitty images no longer on screen."""
    old = set(k for _, k, _, kind in marks_in(old_lines or [])
              if kind in ('placeholder', 'kitty'))
    new = set(k for _, k, _, _ in marks_in(new_lines))
    out = []
    for key in sorted(old - new):
        entry = _PAYLOADS.get(key)
        if entry and entry[4]:
            out.append(kitty_delete(entry[4], entry[5]))
    return ''.join(out)


def render_diff(old, new):
    """Like :func:`flexablelib._frames.render_diff`, picture-aware: a
    picture is redrawn whenever any line it covers is rewritten, and marks
    are expanded."""
    changed = set(_fx.changed_lines(old, new))
    for row, _key, rows, kind in marks_in(new):
        if kind != 'placeholder' and any(
                r in changed for r in range(max(0, row - rows + 1), row + 1)):
            changed.add(row)
    parts = [cleanup(old, new)]
    for i in sorted(changed):
        parts.append('\x1b[{0};1H{1}\x1b[K'.format(i + 1, expand(new[i])))
    if len(new) < len(old):
        parts.append('\x1b[{0};1H\x1b[J'.format(len(new) + 1))
    return ''.join(parts)


_fx.set_graphics_expander(expand)


# +---------------------------------------------------------------------------+
# Browsers

def file_url(path):
    """``file://`` URL for a local path (or the URL itself)."""
    text = os.fspath(path)
    if '://' in text:
        return text
    from pathlib import Path
    return Path(os.path.abspath(text)).as_uri()


def hyperlink(url, text):
    """OSC 8 hyperlink."""
    return '\x1b]8;;{0}\x1b\\{1}\x1b]8;;\x1b\\'.format(url, text)


def _wsl(env):
    if env.get('WSL_DISTRO_NAME'):
        return True
    try:
        with open('/proc/version') as handle:
            return 'microsoft' in handle.read().lower()
    except OSError:
        return False


def browser_available(env=None, platform=None, which=None):
    """
    ``(available, how_or_reason)``: whether a graphical browser can open a
    link here. ``BROWSER`` is trusted; Windows always can; macOS needs
    ``open`` and no bare SSH session; Linux and the BSDs need a display
    (``DISPLAY`` / ``WAYLAND_DISPLAY``) and ``xdg-open``, ``gio`` or a
    browser; WSL uses ``wslview`` / ``explorer.exe``.
    ``FLEXABLELIB_NO_BROWSER=1`` says no.
    """
    import shutil
    env = os.environ if env is None else env
    which = which or shutil.which
    platform = sys.platform if platform is None else platform
    if (env.get('FLEXABLELIB_NO_BROWSER') or '').lower() in _TRUE:
        return False, 'FLEXABLELIB_NO_BROWSER'
    if env.get('BROWSER'):
        return True, 'BROWSER'
    if platform.startswith('win'):
        return True, 'start'
    if platform == 'darwin':
        if (env.get('SSH_CONNECTION') or env.get('SSH_TTY')) and \
                not env.get('DISPLAY'):
            return False, 'sesión SSH sin pantalla'
        return (True, 'open') if which('open') else (False, 'sin open')
    if _wsl(env):
        for tool in ('wslview', 'explorer.exe'):
            if which(tool):
                return True, tool
    if not (env.get('DISPLAY') or env.get('WAYLAND_DISPLAY')):
        return False, 'sin pantalla (DISPLAY/WAYLAND_DISPLAY) ni BROWSER'
    for tool in ('xdg-open', 'gio', 'firefox', 'chromium', 'google-chrome',
                 'chromium-browser', 'brave-browser', 'epiphany'):
        if which(tool):
            return True, tool
    return False, 'no hay navegador instalado'


def open_external(target, env=None, platform=None, which=None, runner=None):
    """
    Open ``target`` (path or URL) in the browser, without blocking.
    Returns ``(opened, reason)``; when :func:`browser_available` says no,
    nothing is started.
    """
    import shutil
    import subprocess
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    ok, how = browser_available(env, platform, which)
    if not ok:
        return False, how
    url = file_url(target)
    custom = runner is not None
    runner = runner or (lambda cmd: subprocess.Popen(
        cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, start_new_session=True))
    try:
        if how == 'BROWSER':
            cmd = env['BROWSER'].split(os.pathsep)[0]
            parts = cmd.split()
            if '%s' in cmd:
                parts = [p.replace('%s', url) for p in parts]
            else:
                parts.append(url)
            runner(parts)
        elif how == 'start':
            if custom or not hasattr(os, 'startfile'):
                runner(['cmd', '/c', 'start', '', url])
            else:   # pragma: no cover - Windows only
                os.startfile(url)
        elif how == 'gio':
            runner(['gio', 'open', url])
        else:
            runner([shutil.which(how) or how, url])
    except Exception as error:
        return False, str(error)
    return True, how
