"""
ACCESSIBILITY

Settings and tools that make terminal interfaces usable without a mouse,
without colour, without Unicode, with motion turned down and with a screen
reader:

- :data:`settings` -- process-wide switches, read from the environment and
  overridden by :class:`~flexablelib_tui.App` arguments:

  ========================  ==============================  ===============
  setting                   environment                     effect
  ========================  ==============================  ===============
  ``screen_reader``         ``FLEXABLELIB_SCREEN_READER=1``  linear text
                                                            output and
                                                            announcements
  ``reduced_motion``        ``FLEXABLELIB_REDUCED_MOTION=1`` static spinners,
                                                            no animation
  ``ascii``                 ``FLEXABLELIB_ASCII=1``          ASCII symbols
                                                            and borders
  ``focus_marker``          ``FLEXABLELIB_FOCUS_MARKER=1``   focus shown with
                                                            text markers in
                                                            colour too
  ``lang``                  ``FLEXABLELIB_LANG=en``          role names
  ``theme``                 ``FLEXABLELIB_THEME=name``       component theme
                                                            (e.g.
                                                            ``high-contrast``)
  ========================  ==============================  ===============

  ``FLEXABLELIB_A11Y=1`` turns on ``focus_marker`` and ``reduced_motion``.

- :func:`describe` -- the sentence a screen reader says for a component
  (label, role, value, state, description, shortcut), from the component's
  :meth:`~flexablelib_tui.Component.a11y` information;
- :class:`Announcer` -- writes announcements (focus moves, changed values,
  dialogs, notifications) to stdout, stderr, a file or a callback;
- :func:`contrast_ratio`, :func:`simulate_cvd`, :func:`delta_e` -- WCAG
  contrast and colour-vision-deficiency checks for themes;
- :func:`ascii_fold` -- frames redrawn with ASCII stand-ins (C-accelerated);
- :func:`audit` -- automatic checks: every component has a role and a label,
  focus is visible without colour.
"""

import contextlib
import math
import os
import re
import sys

from flexablelib import _frames as _fx

__all__ = ['Settings', 'settings', 'configure', 'describe', 'Announcer',
           'ROLE_NAMES', 'STATE_NAMES', 'contrast_ratio',
           'relative_luminance', 'parse_color', 'spec_colors',
           'simulate_cvd', 'delta_e', 'ascii_fold', 'audit', 'AuditIssue',
           'STATUS_SYMBOLS', 'status_symbol', 'plain_style_signature']

_TRUE = ('1', 'true', 'yes', 'on')


def _flag(env, name):
    value = env.get(name)
    if value is None:
        return None
    return value.strip().lower() in _TRUE


class Settings(object):
    """Accessibility switches (see the module docstring)."""

    FIELDS = ('screen_reader', 'reduced_motion', 'ascii', 'focus_marker',
              'lang', 'theme')
    _AS_IS = ('lang', 'theme')

    def __init__(self, screen_reader=False, reduced_motion=False, ascii=False,
                 focus_marker=False, lang='es', theme=None):
        self.theme = theme
        self.screen_reader = bool(screen_reader)
        self.reduced_motion = bool(reduced_motion)
        self.ascii = bool(ascii)
        self.focus_marker = bool(focus_marker)
        self.lang = lang

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        a11y = bool(_flag(env, 'FLEXABLELIB_A11Y'))
        values = {
            'screen_reader': _flag(env, 'FLEXABLELIB_SCREEN_READER'),
            'reduced_motion': _flag(env, 'FLEXABLELIB_REDUCED_MOTION'),
            'ascii': _flag(env, 'FLEXABLELIB_ASCII'),
            'focus_marker': _flag(env, 'FLEXABLELIB_FOCUS_MARKER'),
        }
        out = cls(lang=(env.get('FLEXABLELIB_LANG') or 'es')[:2].lower(),
                  theme=env.get('FLEXABLELIB_THEME') or None)
        for name, value in values.items():
            if value is None:
                value = a11y and name in ('reduced_motion', 'focus_marker')
            setattr(out, name, bool(value))
        return out

    def as_dict(self):
        return dict((name, getattr(self, name)) for name in self.FIELDS)

    def update(self, **values):
        for name, value in values.items():
            if name not in self.FIELDS:
                raise TypeError('unknown accessibility setting ' + name)
            if value is not None:
                setattr(self, name, value if name in self._AS_IS
                        else bool(value))

    def __repr__(self):
        return 'Settings({0})'.format(', '.join(
            '{0}={1!r}'.format(k, v) for k, v in self.as_dict().items()))


#: The process-wide settings components read.
settings = Settings.from_env()


@contextlib.contextmanager
def configure(**values):
    """Change :data:`settings` inside a ``with`` block (tests, previews)."""
    saved = settings.as_dict()
    settings.update(**values)
    try:
        yield settings
    finally:
        for name, value in saved.items():
            setattr(settings, name, value)


# -- descriptions -------------------------------------------------------------

ROLE_NAMES = {
    'es': {
        'button': 'botón', 'checkbox': 'casilla', 'switch': 'interruptor',
        'radiogroup': 'grupo de opciones', 'radio': 'opción',
        'textbox': 'campo de texto', 'password': 'contraseña',
        'spinbutton': 'campo numérico', 'combobox': 'lista desplegable',
        'listbox': 'lista', 'menu': 'menú', 'menuitem': 'opción de menú',
        'tablist': 'pestañas', 'tab': 'pestaña', 'grid': 'tabla',
        'table': 'tabla', 'tree': 'árbol', 'dialog': 'diálogo',
        'alertdialog': 'diálogo de alerta', 'alert': 'alerta',
        'status': 'estado', 'progressbar': 'barra de progreso',
        'link': 'enlace', 'navigation': 'navegación', 'form': 'formulario',
        'region': 'región', 'group': 'grupo', 'document': 'documento',
        'code': 'código', 'img': 'gráfica', 'list': 'lista',
        'calendar': 'calendario', 'toolbar': 'barra de herramientas',
        'separator': 'separador', 'scrollbar': 'desplazamiento',
        'searchbox': 'búsqueda', 'slider': 'control deslizante',
        'heading': 'encabezado', 'text': 'texto', 'timer': 'temporizador',
        'feed': 'lista de comentarios', 'figure': 'indicador',
        'application': 'aplicación', 'banner': 'barra superior',
        'splitter': 'separador ajustable', 'tooltip': 'información',
    },
    'en': {
        'button': 'button', 'checkbox': 'checkbox', 'switch': 'switch',
        'radiogroup': 'radio group', 'radio': 'radio button',
        'textbox': 'edit text', 'password': 'password',
        'spinbutton': 'spin button', 'combobox': 'combo box',
        'listbox': 'list box', 'menu': 'menu', 'menuitem': 'menu item',
        'tablist': 'tab list', 'tab': 'tab', 'grid': 'table',
        'table': 'table', 'tree': 'tree', 'dialog': 'dialog',
        'alertdialog': 'alert dialog', 'alert': 'alert', 'status': 'status',
        'progressbar': 'progress bar', 'link': 'link',
        'navigation': 'navigation', 'form': 'form', 'region': 'region',
        'group': 'group', 'document': 'document', 'code': 'code',
        'img': 'chart', 'list': 'list', 'calendar': 'calendar',
        'toolbar': 'toolbar', 'separator': 'separator',
        'scrollbar': 'scroll area', 'searchbox': 'search',
        'slider': 'slider', 'heading': 'heading', 'text': 'text',
        'timer': 'timer', 'feed': 'comments', 'figure': 'indicator',
        'application': 'application', 'banner': 'banner',
        'splitter': 'splitter', 'tooltip': 'tooltip',
    },
}

STATE_NAMES = {
    'es': {
        'checked': 'marcada', 'unchecked': 'sin marcar', 'on': 'encendido',
        'off': 'apagado', 'expanded': 'expandido', 'collapsed': 'contraído',
        'selected': 'seleccionado', 'disabled': 'no disponible',
        'required': 'obligatorio', 'invalid': 'con error', 'busy': 'ocupado',
        'readonly': 'solo lectura', 'focused': 'con foco',
        'pressed': 'presionado', 'modal': 'modal', 'mixed': 'parcial',
        'current': 'actual', 'empty': 'vacío', 'hidden': 'oculto',
    },
    'en': {
        'checked': 'checked', 'unchecked': 'not checked', 'on': 'on',
        'off': 'off', 'expanded': 'expanded', 'collapsed': 'collapsed',
        'selected': 'selected', 'disabled': 'unavailable',
        'required': 'required', 'invalid': 'invalid entry', 'busy': 'busy',
        'readonly': 'read only', 'focused': 'focused', 'pressed': 'pressed',
        'modal': 'modal', 'mixed': 'mixed', 'current': 'current',
        'empty': 'empty', 'hidden': 'hidden',
    },
}

_WORDS = {
    'es': {'shortcut': 'atajo', 'error': 'error'},
    'en': {'shortcut': 'shortcut', 'error': 'error'},
}


def describe(info, lang=None, focused_state=False):
    """
    The sentence for one component: ``'Guardar, botón'``,
    ``'Nombre, campo de texto, Yael, obligatorio'``.

    ``info`` is a component (its ``a11y()`` is used) or that dict. The
    ``focused`` state is left out unless ``focused_state``.
    """
    if hasattr(info, 'a11y'):
        info = info.a11y()
    lang = lang or settings.lang
    roles = ROLE_NAMES.get(lang, ROLE_NAMES['es'])
    states = STATE_NAMES.get(lang, STATE_NAMES['es'])
    words = _WORDS.get(lang, _WORDS['es'])
    parts = []
    label = (info.get('label') or '').strip()
    if label:
        parts.append(label)
    role = info.get('role')
    if role:
        parts.append(roles.get(role, role))
    value = info.get('value')
    if value not in (None, ''):
        parts.append(str(value))
    for state in info.get('state') or ():
        if state == 'focused' and not focused_state:
            continue
        parts.append(states.get(state, state))
    text = ', '.join(parts)
    error = info.get('error')
    if error:
        text += '. {0}: {1}'.format(words['error'].capitalize(), error)
    description = (info.get('description') or '').strip()
    if description:
        text += '. ' + description
    shortcut = info.get('shortcut')
    if shortcut:
        text += '. {0}: {1}'.format(words['shortcut'].capitalize(), shortcut)
    return text


class Announcer(object):
    """
    Where announcements go: ``None`` (kept in ``history`` only),
    ``'stdout'``, ``'stderr'``, a file path, an open stream or a callable
    taking the text. Repeating the last announcement is skipped unless
    ``dedupe=False``; ``prefix`` starts every line (``'» '``).
    """

    def __init__(self, target=None, dedupe=True, prefix=''):
        self.target = target
        self.dedupe = dedupe
        self.prefix = prefix
        self.history = []

    def _write(self, line):
        target = self.target
        if target is None:
            return
        if callable(target) and not hasattr(target, 'write'):
            target(line)
            return
        if target == 'stdout':
            stream = sys.stdout
        elif target == 'stderr':
            stream = sys.stderr
        elif isinstance(target, str):
            with open(target, 'a', encoding='utf-8') as handle:
                handle.write(self.prefix + line + '\n')
            return
        else:
            stream = target
        try:
            stream.write(self.prefix + line + '\n')
            stream.flush()
        except (AttributeError, ValueError, OSError):
            pass

    def announce(self, text, priority='polite'):
        """Say ``text``; ``'assertive'`` interrupts (always repeated)."""
        text = ' '.join(_fx.strip_ansi(str(text)).split())
        if not text:
            return False
        if self.dedupe and priority != 'assertive' and self.history and \
                self.history[-1] == text:
            return False
        self.history.append(text)
        self._write(text)
        return True

    __call__ = announce

    def clear(self):
        self.history = []


# -- status symbols -----------------------------------------------------------

#: Message kinds as symbol + word, so meaning never rests on colour alone.
STATUS_SYMBOLS = {
    'info': ('ℹ', 'i', 'Info', 'Info'),
    'success': ('✔', '+', 'Éxito', 'Success'),
    'warning': ('⚠', '!', 'Aviso', 'Warning'),
    'error': ('✖', 'x', 'Error', 'Error'),
    'neutral': ('•', '*', '', ''),
}


def status_symbol(kind, ascii=None, word=False, lang=None):
    """The symbol (and with ``word`` its name) for a message kind."""
    entry = STATUS_SYMBOLS.get(kind, STATUS_SYMBOLS['neutral'])
    use_ascii = settings.ascii if ascii is None else ascii
    symbol = entry[1] if use_ascii else entry[0]
    if not word:
        return symbol
    name = entry[2] if (lang or settings.lang) == 'es' else entry[3]
    return (symbol + ' ' + name).strip()


def ascii_fold(text):
    """``text`` with box drawing and symbols as ASCII (same widths)."""
    return _fx.ascii_fold(text)


# -- colour checks ------------------------------------------------------------

# xterm's default palette for the 16 named colours.
_ANSI_RGB = {
    'black': (0, 0, 0), 'red': (205, 0, 0), 'green': (0, 205, 0),
    'yellow': (205, 205, 0), 'blue': (0, 0, 238), 'magenta': (205, 0, 205),
    'cyan': (0, 205, 205), 'white': (229, 229, 229),
    'bright_black': (127, 127, 127), 'grey': (127, 127, 127),
    'gray': (127, 127, 127), 'bright_red': (255, 0, 0),
    'bright_green': (0, 255, 0), 'bright_yellow': (255, 255, 0),
    'bright_blue': (92, 92, 255), 'bright_magenta': (255, 0, 255),
    'bright_cyan': (0, 255, 255), 'bright_white': (255, 255, 255),
}
_HEX_RE = re.compile(r'^#?([0-9a-f]{6})$|^#([0-9a-f]{3})$')
_DIGITS_RE = re.compile(r'^[0-9]{1,3}$')
_GREY_RE = re.compile(r'^gr[ae]y([0-9]{1,3})$')
# The greys of the xterm 256 palette: black, the 24-step ramp, white.
_GREY_LEVELS = [0] + [8 + 10 * i for i in range(24)] + [255]
_ATTRS = ('bold', 'dim', 'italic', 'underline', 'blink', 'reverse',
          'hidden', 'strike', 'strikethrough', 'normal', 'faint')


def _xterm_rgb(index):
    if index < 16:
        names = ['black', 'red', 'green', 'yellow', 'blue', 'magenta',
                 'cyan', 'white']
        name = names[index % 8]
        return _ANSI_RGB['bright_' + name if index >= 8 else name]
    if index < 232:
        index -= 16
        steps = (0, 95, 135, 175, 215, 255)
        return (steps[index // 36], steps[(index // 6) % 6], steps[index % 6])
    level = 8 + 10 * (index - 232)
    return (level, level, level)


def parse_color(token):
    """``(r, g, b)`` for ``'#rrggbb'``, ``'#rgb'``, ``'rrggbb'``, a colour
    name, ``'color:N'`` / ``'colour:N'`` / ``N`` (256 palette) or
    ``'greyNN'`` (the xterm grey a terminal shows for it); ``None`` if not.

    Every colour :func:`flexablelib.colors.parse_spec` draws is understood,
    so contrast checks see the colour that is really on screen."""
    if token is None:
        return None
    if isinstance(token, tuple):
        return token
    token = str(token).strip().lower()
    hex_match = _HEX_RE.match(token)
    if hex_match:
        digits = hex_match.group(1) or hex_match.group(2)
        if len(digits) == 3:
            digits = ''.join(c * 2 for c in digits)
        return tuple(int(digits[k:k + 2], 16) for k in (0, 2, 4))
    if token.startswith('#'):
        return None
    if token in _ANSI_RGB:
        return _ANSI_RGB[token]
    for prefix in ('color:', 'colour:'):
        if token.startswith(prefix):
            token = token[len(prefix):]
            break
    if _DIGITS_RE.match(token) and int(token) < 256:
        return _xterm_rgb(int(token))
    grey = _GREY_RE.match(token)
    if grey and int(grey.group(1)) <= 100:
        # parse_spec draws the nearest xterm grey, not the exact level.
        target = int(grey.group(1)) * 255 / 100.0
        level = min(_GREY_LEVELS, key=lambda value: abs(value - target))
        return (level, level, level)
    return None


def spec_colors(spec):
    """``(fg, bg, attributes)`` of a colour spec, colours as RGB or None."""
    if not spec:
        return None, None, ()
    text = str(spec).strip().lower()
    if text.startswith('on '):
        fg_part, bg_part = '', text[3:]
    else:
        fg_part, _, bg_part = text.partition(' on ')
    fg = None
    attrs = []
    for token in fg_part.split():
        if token in _ATTRS:
            attrs.append(token)
        elif fg is None:
            fg = parse_color(token)
    bg = None
    for token in bg_part.split():
        bg = parse_color(token)
        if bg is not None:
            break
    return fg, bg, tuple(attrs)


def _linear(channel):
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(color):
    """WCAG relative luminance of an RGB colour (0 black .. 1 white)."""
    r, g, b = (_linear(c) for c in parse_color(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
    """WCAG 2 contrast ratio between two colours (1 .. 21)."""
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    high, low = max(l1, l2), min(l1, l2)
    return (high + 0.05) / (low + 0.05)


# Machado, Oliveira & Fernandes (2009), severity 1.0, in linear RGB.
_CVD = {
    'protanopia': ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
    'deuteranopia': ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
    'tritanopia': ((1.255528, -0.076749, -0.178779),
                   (-0.078411, 0.930809, 0.147602),
                   (0.004733, 0.691367, 0.303900)),
}


def _gamma(c):
    c = max(0.0, min(1.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return int(round(v * 255))


def simulate_cvd(color, kind):
    """How ``color`` looks with ``kind`` colour blindness
    (``'protanopia'``, ``'deuteranopia'``, ``'tritanopia'``)."""
    rgb = [_linear(c) for c in parse_color(color)]
    matrix = _CVD[kind]
    return tuple(_gamma(sum(m * c for m, c in zip(row, rgb)))
                 for row in matrix)


def _lab(color):
    r, g, b = (_linear(c) for c in parse_color(color))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(a, b):
    """CIE76 colour difference (about 2.3 is just noticeable)."""
    la, lb = _lab(a), _lab(b)
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(la, lb)))


# -- audit ----------------------------------------------------------------------

class AuditIssue(object):
    def __init__(self, component, check, message):
        self.component = component
        self.check = check
        self.message = message

    def __repr__(self):
        return 'AuditIssue({0}, {1!r}, {2!r})'.format(
            type(self.component).__name__, self.check, self.message)


_OFF = {21: (1,), 22: (1, 2), 23: (3,), 24: (4,), 25: (5, 6), 27: (7,),
        28: (8,), 29: (9,)}


def plain_style_signature(text):
    """``text`` with colour codes removed but bold / reverse / underline
    kept: what someone who cannot tell colours apart still sees. Only
    changes of those attributes are written, so a coloured span that ends
    with a reset looks the same as plain text."""
    import re
    state = [frozenset()]

    def keep(match):
        attrs = set(state[0])
        params = match.group(1).split(';')
        k = 0
        while k < len(params):
            p = params[k]
            if p in ('38', '48'):
                k += 3 if k + 1 < len(params) and params[k + 1] == '5' \
                    else 5
                continue
            n = int(p) if p.isdigit() else 0
            if n == 0:
                attrs.clear()
            elif n in _OFF:
                attrs.difference_update(_OFF[n])
            elif 1 <= n <= 9:
                attrs.add(n)
            k += 1
        attrs = frozenset(attrs)
        if attrs == state[0]:
            return ''
        state[0] = attrs
        return '\x1b[' + ';'.join(str(a) for a in sorted(attrs)) + 'm'
    return re.sub(r'\x1b\[([0-9;]*)m', keep, text)


def audit(components, width=40, check_focus=True):
    """
    Accessibility problems of ``components`` (instances): a missing role or
    label, and -- for focusable ones -- focus that only colour shows (the
    focused and unfocused renders must differ once colours are removed;
    bold, reverse and underline count). Returns a list of
    :class:`AuditIssue` (empty when everything passes).
    """
    issues = []
    for comp in components:
        info = comp.a11y()
        if not info.get('role'):
            issues.append(AuditIssue(comp, 'role', 'no role'))
        if not (info.get('label') or '').strip():
            issues.append(AuditIssue(comp, 'label', 'no alt text' if info.get(
                'role') == 'img' else 'no label'))
        if check_focus and getattr(comp, 'focusable', False):
            for colors in (False, True):
                saved = comp.use_colors
                comp.use_colors = colors
                was = comp.focused
                try:
                    comp.focused = False
                    off = plain_style_signature(comp.render(width))
                    comp.focused = True
                    on = plain_style_signature(comp.render(width))
                finally:
                    comp.focused = was
                    comp.use_colors = saved
                if off == on:
                    issues.append(AuditIssue(
                        comp, 'focus', 'focus not visible ({0})'.format(
                            'colour' if colors else 'no colour')))
    return issues
