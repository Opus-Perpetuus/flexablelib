"""
Form inputs: text, password, numbers, arithmetic, money, masked text,
multi-line text, JSON, code scanners, checkboxes, switches, radio and
checkbox groups, selects, autocomplete, colours, icons, coordinates and files.

All of them are :class:`~flexablelib_components.base.Input` subclasses: a
``label`` above, ``help`` and validation errors below, ``value`` /
``set_value()``, ``validate()``, ``on_change`` and ``on_submit``.
"""

import ast
import json
import operator
import os
import re
import time

from flexablelib import _frames as _fx

from flexablelib_tui import Key

from .base import Input, _Themed

__all__ = ['TextInput', 'PasswordInput', 'NumberInput', 'ExpressionInput',
           'MoneyInput', 'MaskedInput', 'MASKS', 'TextArea', 'JsonInput',
           'ScanInput', 'Checkbox', 'Switch', 'RadioGroup', 'CheckboxGroup',
           'Select', 'Autocomplete', 'ColorInput', 'IconPicker',
           'CoordinatesInput', 'FileInput', 'normalize_options',
           'evaluate_expression', 'ICONS']

_WORD = re.compile(r'\w', re.UNICODE)


def normalize_options(options):
    """``[(value, label), ...]`` from strings, pairs, dicts or a mapping."""
    if isinstance(options, dict):
        return [(k, str(v)) for k, v in options.items()]
    out = []
    for option in options or []:
        if isinstance(option, dict):
            out.append((option.get('value'), str(option.get(
                'label', option.get('value')))))
        elif isinstance(option, (tuple, list)):
            out.append((option[0], str(option[1] if len(option) > 1
                                       else option[0])))
        else:
            out.append((option, str(option)))
    return out


# +---------------------------------------------------------------------------+
# Single-line text

class TextInput(Input):
    """
    One line of editable text.

    Keys: arrows, Home/End (Ctrl-A/E), Ctrl-arrows by word, Backspace/Delete,
    Ctrl-W (word back), Ctrl-U / Ctrl-K (to start / end), paste, Enter
    submits. ``placeholder`` shows while empty, ``max_length`` caps the
    length, ``allowed`` (a regex character class or callable) filters typed
    characters, ``transform`` is ``'upper'``, ``'lower'`` or a callable.
    """

    def __init__(self, label=None, value='', placeholder='', max_length=None,
                 allowed=None, transform=None, mask_char=None, **kwargs):
        self.text = ''
        self.cursor_pos = 0
        self.scroll_x = 0
        self.placeholder = placeholder
        self.max_length = max_length
        self.allowed = re.compile(allowed) if isinstance(allowed, str) \
            else allowed
        self.transform = transform
        self.mask_char = mask_char
        super(TextInput, self).__init__(label=label, value=value, **kwargs)

    # value <-> text
    def parse(self, text):
        return text

    def format(self, value):
        return '' if value is None else str(value)

    @property
    def value(self):
        try:
            return self.parse(self.text)
        except ValueError:
            return None

    @value.setter
    def value(self, new):
        self.text = self.format(new)
        self.cursor_pos = len(self.text)

    def is_empty(self):
        return self.text.strip() == ''

    def validate(self):
        if self.text.strip():
            try:
                self.parse(self.text)
            except ValueError as error:
                self.error = str(error) or 'Valor inválido'
                return self.error
        return super(TextInput, self).validate()

    # editing
    def _accept(self, char):
        if self.allowed is None:
            return True
        if callable(self.allowed) and not hasattr(self.allowed, 'match'):
            return bool(self.allowed(char))
        return bool(self.allowed.match(char))

    def _apply(self, text):
        if self.transform == 'upper':
            return text.upper()
        if self.transform == 'lower':
            return text.lower()
        if callable(self.transform):
            return self.transform(text)
        return text

    def insert(self, chars):
        chars = ''.join(c for c in chars if c >= ' ' and self._accept(c))
        chars = self._apply(chars)
        if self.max_length is not None:
            chars = chars[:max(0, self.max_length - len(self.text))]
        if not chars:
            return False
        self._edit(self.text[:self.cursor_pos] + chars +
                   self.text[self.cursor_pos:], self.cursor_pos + len(chars))
        return True

    def _edit(self, text, cursor):
        old = self.value
        self.text = text
        self.cursor_pos = max(0, min(cursor, len(text)))
        self.error = None
        new = self.value
        if new != old and self.on_change is not None:
            self.on_change(new)
        self.refresh()

    def _word_left(self):
        i = self.cursor_pos
        while i > 0 and not _WORD.match(self.text[i - 1]):
            i -= 1
        while i > 0 and _WORD.match(self.text[i - 1]):
            i -= 1
        return i

    def _word_right(self):
        i, n = self.cursor_pos, len(self.text)
        while i < n and not _WORD.match(self.text[i]):
            i += 1
        while i < n and _WORD.match(self.text[i]):
            i += 1
        return i

    def on_key(self, key):
        k = str(key)
        pos, text = self.cursor_pos, self.text
        if k == 'paste':
            return self.insert(key.char.replace('\r', '').replace('\n', ' '))
        if key.is_printable or k == 'space':
            return self.insert(key.char or ' ')
        if k == 'backspace':
            if pos > 0:
                self._edit(text[:pos - 1] + text[pos:], pos - 1)
            return True
        if k in ('delete', 'ctrl+d'):
            if pos < len(text):
                self._edit(text[:pos] + text[pos + 1:], pos)
            return True
        if k in ('left', 'ctrl+b'):
            self.cursor_pos = max(0, pos - 1)
        elif k in ('right', 'ctrl+f'):
            self.cursor_pos = min(len(text), pos + 1)
        elif k in ('home', 'ctrl+a'):
            self.cursor_pos = 0
        elif k in ('end', 'ctrl+e'):
            self.cursor_pos = len(text)
        elif k in ('ctrl+left', 'alt+b'):
            self.cursor_pos = self._word_left()
        elif k in ('ctrl+right', 'alt+f'):
            self.cursor_pos = self._word_right()
        elif k in ('ctrl+w', 'alt+backspace', 'ctrl+backspace'):
            start = self._word_left()
            self._edit(text[:start] + text[pos:], start)
        elif k == 'ctrl+u':
            self._edit(text[pos:], 0)
        elif k == 'ctrl+k':
            self._edit(text[:pos], pos)
        elif k == 'enter':
            return self.submit()
        else:
            return False
        self.refresh()
        return True

    def on_mouse(self, event):
        if event.action != 'press' or event.button != 0:
            return False
        if event.y != (1 if self.label else 0):
            return True
        col = max(0, event.x - 2) + self.scroll_x
        acc = pos = 0
        for char in self.shown_text():
            w = _fx.visible_width(char)
            if acc + w > col:
                break
            acc += w
            pos += 1
        self.cursor_pos = pos
        self.refresh()
        return True

    # drawing
    def shown_text(self):
        if self.mask_char:
            return self.mask_char * len(self.text)
        return self.text

    def suffix(self):
        """Muted text drawn at the right end of the control."""
        return ''

    def control(self, width, height):
        marker = self.marker()
        suffix = self.suffix()
        avail = max(1, width - 2 - (_fx.visible_width(suffix) + 1
                                    if suffix else 0))
        shown = self.shown_text()
        if not shown and not self.focused:
            if self.placeholder:
                body = self.paint(_fx.truncate(self.placeholder, avail, '…'),
                                  self.theme.muted)
            else:
                body = '' if self._active() else '_' * min(avail, 24)
        else:
            body = self._viewport(shown, avail)
        body = _fx.fit_line(body, avail)
        if self._active():
            body = self.paint(body, self.theme.field)
        line = marker + ' ' + body
        if suffix:
            line += ' ' + self.paint(suffix, self.theme.muted)
        return [line]

    def _viewport(self, shown, avail):
        widths = [_fx.visible_width(c) for c in shown]
        cursor_col = sum(widths[:self.cursor_pos])
        if cursor_col < self.scroll_x:
            self.scroll_x = cursor_col
        if cursor_col >= self.scroll_x + avail:
            self.scroll_x = cursor_col - avail + 1
        out, col = [], 0
        for i, (char, w) in enumerate(zip(shown, widths)):
            if col >= self.scroll_x and col + w <= self.scroll_x + avail:
                out.append(self.cursor(char) if self.focused and
                           i == self.cursor_pos else char)
            col += w
        if self.focused and self.cursor_pos >= len(shown) and \
                cursor_col - self.scroll_x < avail:
            out.append(self.cursor(' ') if self._active() else '_')
        if not shown and self.placeholder and self.focused:
            out.append(self.paint(self.placeholder, self.theme.muted))
        return ''.join(out)


class PasswordInput(TextInput):
    """Hidden text; Ctrl-R or F2 shows and hides it."""

    def __init__(self, label=None, value='', mask_char='•', **kwargs):
        super(PasswordInput, self).__init__(label=label, value=value,
                                            mask_char=mask_char, **kwargs)
        self._mask = mask_char
        self.revealed = False

    def on_key(self, key):
        if str(key) in ('ctrl+r', 'f2'):
            self.revealed = not self.revealed
            self.mask_char = None if self.revealed else self._mask
            self.refresh()
            return True
        return super(PasswordInput, self).on_key(key)

    def suffix(self):
        return 'ctrl+r' if self.focused else ''

    role = 'password'

    def a11y_value(self):
        if self.revealed:
            return self.text
        n = len(self.text)
        return '' if not n else '{0} carácter{1}'.format(
            n, 'es' if n != 1 else '')


class NumberInput(TextInput):
    """
    A number. Up/Down step it by ``step`` within ``minimum`` / ``maximum``;
    ``decimals`` fixes the decimals shown (``0`` gives an int).
    """

    role = 'spinbutton'

    def a11y_value(self):
        return self.text

    def __init__(self, label=None, value=None, minimum=None, maximum=None,
                 step=1, decimals=None, **kwargs):
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.decimals = decimals
        kwargs.setdefault('allowed', r'[0-9.,\-+eE]')
        super(NumberInput, self).__init__(label=label, value=value, **kwargs)

    def parse(self, text):
        text = text.strip().replace(',', '')
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            raise ValueError('No es un número')
        if self.decimals == 0 or (self.decimals is None and number.is_integer()
                                  and 'e' not in text.lower()
                                  and '.' not in text):
            number = int(round(number))
        if self.minimum is not None and number < self.minimum:
            raise ValueError('Mínimo {0}'.format(self.minimum))
        if self.maximum is not None and number > self.maximum:
            raise ValueError('Máximo {0}'.format(self.maximum))
        return number

    def format(self, value):
        if value is None or value == '':
            return ''
        if self.decimals is not None:
            return '{0:.{1}f}'.format(float(value), self.decimals)
        return str(value)

    def _clamp(self, number):
        if self.minimum is not None:
            number = max(self.minimum, number)
        if self.maximum is not None:
            number = min(self.maximum, number)
        return number

    def on_key(self, key):
        k = str(key)
        if k in ('up', 'down', 'pageup', 'pagedown'):
            factor = {'up': 1, 'down': -1, 'pageup': 10, 'pagedown': -10}[k]
            current = self.value or 0
            number = self._clamp(current + factor * self.step)
            if isinstance(number, float) and self.decimals is None:
                number = round(number, 10)
            self._edit(self.format(number), len(self.format(number)))
            return True
        return super(NumberInput, self).on_key(key)


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.FloorDiv: operator.floordiv}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def evaluate_expression(text):
    """
    The value of an arithmetic expression (``+ - * / // % ** ^``, brackets,
    decimals, ``,`` as thousands separator). Nothing else is evaluated.
    """
    source = text.replace('^', '**').replace(',', '').strip()
    if not source:
        return None
    try:
        tree = ast.parse(source, mode='eval')
    except SyntaxError:
        raise ValueError('Operación inválida')

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and \
                isinstance(node.value, (int, float)) and \
                not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError('Exponente muy grande')
            try:
                return _OPS[type(node.op)](left, right)
            except ZeroDivisionError:
                raise ValueError('División entre cero')
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](walk(node.operand))
        raise ValueError('Operación inválida')
    result = walk(tree)
    if isinstance(result, float) and result.is_integer() and \
            abs(result) < 1e15:
        result = int(result)
    return result


class ExpressionInput(NumberInput):
    """
    A number that also takes arithmetic (``2*3+1``, ``(120-15)/4``): the
    result shows at the right while typing and replaces the expression on
    Enter or when the focus leaves.
    """

    def __init__(self, label=None, value=None, **kwargs):
        kwargs.setdefault('allowed', r'[0-9.,+\-*/%^() eE]')
        super(ExpressionInput, self).__init__(label=label, value=value,
                                              **kwargs)

    def parse(self, text):
        result = evaluate_expression(text)
        if result is None:
            return None
        return super(ExpressionInput, self).parse(repr(result))

    def suffix(self):
        if not re.search(r'[+\-*/%^()]', self.text.lstrip('-')):
            return ''
        value = self.value
        return '' if value is None else '= ' + self.format(value)

    def resolve(self):
        value = self.value
        if value is not None:
            text = self.format(value)
            self.text, self.cursor_pos = text, len(text)

    def on_blur(self):
        self.resolve()

    def submit(self):
        self.resolve()
        return super(ExpressionInput, self).submit()


class MoneyInput(NumberInput):
    """An amount: ``symbol`` before it, thousands separators when not
    editing, ``decimals`` (2) after the point."""

    def __init__(self, label=None, value=None, symbol='$', decimals=2,
                 **kwargs):
        self.symbol = symbol
        super(MoneyInput, self).__init__(label=label, value=value,
                                         decimals=decimals, **kwargs)

    def parse(self, text):
        return super(MoneyInput, self).parse(text.replace(self.symbol, ''))

    def shown_text(self):
        if self.focused:
            return self.symbol + self.text
        value = self.value
        if value is None:
            return ''
        return '{0}{1:,.{2}f}'.format(self.symbol, value, self.decimals or 0)

    def _viewport(self, shown, avail):
        # The symbol is not part of the editable text: shift the cursor.
        saved = self.cursor_pos
        self.cursor_pos = saved + (len(self.symbol) if self.focused else 0)
        try:
            return super(MoneyInput, self)._viewport(shown, avail)
        finally:
            self.cursor_pos = saved


MASKS = {
    'phone': '(###) ###-####',
    'postal_code': '#####',
    'date': '##/##/####',
    'time': '##:##',
    'card': '#### #### #### ####',
    'rfc': 'AAAA######XXX',
    'curp': 'AAAA######AAAAAAXX',
}
_MASK_SLOTS = {'#': str.isdigit, 'A': str.isalpha,
               'X': str.isalnum, '*': lambda c: True}


class MaskedInput(TextInput):
    """
    Text with a fixed pattern: ``#`` a digit, ``A`` a letter, ``X`` either,
    ``*`` anything; other characters are literals filled in automatically.
    ``mask`` may be a name from :data:`MASKS` (``'phone'``, ``'rfc'`` ...).
    ``value`` is the formatted text (``raw=True``: only what was typed).
    """

    def __init__(self, label=None, value='', mask='phone', raw=False,
                 transform='upper', **kwargs):
        self.mask = MASKS.get(mask, mask)
        self.raw = bool(raw)
        self.slots = [i for i, c in enumerate(self.mask) if c in _MASK_SLOTS]
        super(MaskedInput, self).__init__(label=label, value=value,
                                          transform=transform,
                                          max_length=len(self.slots),
                                          **kwargs)

    def _accept(self, char):
        if len(self.text) >= len(self.slots):
            return False
        check = _MASK_SLOTS[self.mask[self.slots[len(self.text)]]]
        return check(char)

    def insert(self, chars):
        done = False
        for char in chars:
            self.cursor_pos = len(self.text)
            if self._accept(char):
                done = super(MaskedInput, self).insert(char) or done
        return done

    def format(self, value):
        if value is None:
            return ''
        typed = [c for c in str(value) if c.isalnum()]
        out = []
        for slot, char in zip(self.slots, typed):
            if _MASK_SLOTS[self.mask[slot]](char):
                out.append(char)
        return self._apply(''.join(out))

    def parse(self, text):
        if self.raw:
            return text
        return self.masked(text, fill=False)

    def masked(self, text, fill=True):
        out = []
        k = 0
        for i, c in enumerate(self.mask):
            if c in _MASK_SLOTS:
                if k < len(text):
                    out.append(text[k])
                    k += 1
                elif fill:
                    out.append('_')
                else:
                    break
            else:
                if k < len(text) or fill:
                    out.append(c)
                else:
                    break
        return ''.join(out)

    def validate(self):
        if self.text and len(self.text) < len(self.slots):
            self.error = 'Formato: ' + self.mask
            return self.error
        return super(MaskedInput, self).validate()

    def shown_text(self):
        return self.masked(self.text)

    def _viewport(self, shown, avail):
        saved = self.cursor_pos
        k = len(self.text)
        self.cursor_pos = self.slots[k] if k < len(self.slots) else len(shown)
        try:
            return super(MaskedInput, self)._viewport(shown, avail)
        finally:
            self.cursor_pos = saved

    def on_key(self, key):
        if str(key) in ('left', 'right', 'home', 'end'):
            return True
        self.cursor_pos = len(self.text)
        return super(MaskedInput, self).on_key(key)


# +---------------------------------------------------------------------------+
# Multi-line text

class TextArea(Input):
    """
    Several lines of text, wrapped to the width. Enter starts a new line;
    ``submit_key`` (``'ctrl+s'``) submits. ``rows`` is the visible height.
    """

    def __init__(self, label=None, value='', rows=5, placeholder='',
                 submit_key='ctrl+s', wrap=True, **kwargs):
        self.lines = ['']
        self.row = 0
        self.col = 0
        self.rows = max(1, int(rows))
        self.scroll_y = 0
        self.placeholder = placeholder
        self.submit_key = submit_key
        self.wrap = bool(wrap)
        super(TextArea, self).__init__(label=label, value=value, **kwargs)
        self.row = self.col = 0

    @property
    def text(self):
        return '\n'.join(self.lines)

    def parse(self, text):
        return text

    def format(self, value):
        return '' if value is None else str(value)

    @property
    def value(self):
        try:
            return self.parse(self.text)
        except ValueError:
            return None

    @value.setter
    def value(self, new):
        self.lines = self.format(new).split('\n') or ['']
        self.row = len(self.lines) - 1
        self.col = len(self.lines[-1])

    def is_empty(self):
        return not self.text.strip()

    def validate(self):
        if self.text.strip():
            try:
                self.parse(self.text)
            except ValueError as error:
                self.error = str(error) or 'Valor inválido'
                return self.error
        return super(TextArea, self).validate()

    def _changed(self):
        self.error = None
        if self.on_change is not None:
            self.on_change(self.value)
        self.refresh()

    def insert(self, text):
        line = self.lines[self.row]
        before, after = line[:self.col], line[self.col:]
        parts = (before + text + after).split('\n')
        last_len = len(parts[-1]) - len(after)
        self.lines[self.row:self.row + 1] = parts
        self.row += len(parts) - 1
        self.col = last_len
        self._changed()
        return True

    def on_key(self, key):
        k = str(key)
        line = self.lines[self.row]
        if k == self.submit_key:
            return self.submit()
        if k == 'paste':
            return self.insert(key.char.replace('\r', ''))
        if k == 'enter':
            return self.insert('\n')
        if key.is_printable or k == 'space':
            return self.insert(key.char or ' ')
        if k == 'backspace':
            if self.col > 0:
                self.lines[self.row] = line[:self.col - 1] + line[self.col:]
                self.col -= 1
            elif self.row > 0:
                prev = self.lines[self.row - 1]
                self.lines[self.row - 1:self.row + 1] = [prev + line]
                self.row -= 1
                self.col = len(prev)
            self._changed()
            return True
        if k == 'delete':
            if self.col < len(line):
                self.lines[self.row] = line[:self.col] + line[self.col + 1:]
            elif self.row + 1 < len(self.lines):
                self.lines[self.row:self.row + 2] = [
                    line + self.lines[self.row + 1]]
            self._changed()
            return True
        if k == 'left':
            if self.col > 0:
                self.col -= 1
            elif self.row > 0:
                self.row -= 1
                self.col = len(self.lines[self.row])
        elif k == 'right':
            if self.col < len(line):
                self.col += 1
            elif self.row + 1 < len(self.lines):
                self.row += 1
                self.col = 0
        elif k == 'up':
            if self.row == 0:
                return False
            self.row -= 1
            self.col = min(self.col, len(self.lines[self.row]))
        elif k == 'down':
            if self.row + 1 >= len(self.lines):
                return False
            self.row += 1
            self.col = min(self.col, len(self.lines[self.row]))
        elif k in ('home', 'ctrl+a'):
            self.col = 0
        elif k in ('end', 'ctrl+e'):
            self.col = len(line)
        elif k == 'ctrl+home':
            self.row = self.col = 0
        elif k == 'ctrl+end':
            self.row = len(self.lines) - 1
            self.col = len(self.lines[-1])
        elif k == 'pageup':
            self.row = max(0, self.row - self.rows)
            self.col = min(self.col, len(self.lines[self.row]))
        elif k == 'pagedown':
            self.row = min(len(self.lines) - 1, self.row + self.rows)
            self.col = min(self.col, len(self.lines[self.row]))
        else:
            return False
        self.refresh()
        return True

    def _segments(self, width):
        """``(row, start, end)`` for every visual line."""
        out = []
        for r, line in enumerate(self.lines):
            if not self.wrap or not line:
                out.append((r, 0, len(line)))
                continue
            start, col = 0, 0
            for i, ch in enumerate(line):
                w = _fx.visible_width(ch)
                if col + w > width:
                    out.append((r, start, i))
                    start, col = i, 0
                col += w
            out.append((r, start, len(line)))
        return out

    def decorate(self, row, text):
        """Hook for syntax colouring of one logical line's segment."""
        return text

    def gutter(self, row, first):
        return ''

    def control(self, width, height):
        marker = self.marker()
        gutter_w = _fx.visible_width(self.gutter(len(self.lines) - 1, True))
        avail = max(1, width - 2 - gutter_w)
        segs = self._segments(avail)
        cur = 0
        for i, (r, s, e) in enumerate(segs):
            if r == self.row and s <= self.col <= e:
                cur = i
                if self.col < e or (i + 1 < len(segs) and segs[i + 1][0] != r) \
                        or i + 1 == len(segs):
                    break
        if cur < self.scroll_y:
            self.scroll_y = cur
        if cur >= self.scroll_y + self.rows:
            self.scroll_y = cur - self.rows + 1
        out = []
        if not self.text and not self.focused and self.placeholder:
            out.append(marker + ' ' + self.paint(self.placeholder,
                                                 self.theme.muted))
        else:
            for i in range(self.scroll_y, min(len(segs), self.scroll_y +
                                              self.rows)):
                r, s, e = segs[i]
                piece = self.lines[r][s:e]
                if self.focused and i == cur:
                    c = self.col - s
                    char = piece[c] if c < len(piece) else ' '
                    shown = self.decorate(r, piece[:c]) + self.cursor(char) + \
                        self.decorate(r, piece[c + 1:])
                else:
                    shown = self.decorate(r, piece)
                g = self.gutter(r, s == 0)
                out.append(marker + ' ' + g + shown)
        while len(out) < self.rows:
            out.append(marker + ' ')
        return out


class JsonInput(TextArea):
    """JSON text; the value is the parsed object. Ctrl-F reformats."""

    def __init__(self, label=None, value=None, indent=2, **kwargs):
        self.indent = indent
        super(JsonInput, self).__init__(label=label, value=value, **kwargs)

    def parse(self, text):
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except ValueError as error:
            raise ValueError('JSON inválido: {0}'.format(
                getattr(error, 'msg', error)))

    def format(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        return json.dumps(value, indent=self.indent, ensure_ascii=False)

    def on_key(self, key):
        if str(key) == 'ctrl+f':
            try:
                self.value = self.parse(self.text)
            except ValueError as error:
                self.error = str(error)
            self.refresh()
            return True
        return super(JsonInput, self).on_key(key)


class ScanInput(TextInput):
    """
    Codes from a keyboard-wedge barcode/QR reader (or typed): each Enter
    accepts one code -- cleaned with ``strip_prefix`` / ``strip_suffix`` /
    ``transform``, checked against ``pattern`` and ``min_length`` /
    ``max_length``, repeated reads within ``duplicate_ms`` dropped,
    ``unique=True`` refusing codes already read -- then calls
    ``on_scan(code)`` and clears for the next one. ``scans`` keeps them.
    """

    def __init__(self, label=None, on_scan=None, pattern=None,
                 min_length=None, max_length=None, strip_prefix='',
                 strip_suffix='', unique=False, duplicate_ms=800,
                 history_size=50, clock=time.monotonic, **kwargs):
        self.on_scan = on_scan
        self.pattern = re.compile(pattern) if pattern else None
        self.min_length = min_length
        self.max_code = max_length
        self.strip_prefix = strip_prefix
        self.strip_suffix = strip_suffix
        self.unique = bool(unique)
        self.duplicate_ms = duplicate_ms
        self.history_size = history_size
        self.clock = clock
        self.scans = []
        self._last = (None, 0.0)
        kwargs.setdefault('placeholder', 'Escanea o escribe un código')
        super(ScanInput, self).__init__(label=label, **kwargs)

    def clean(self, code):
        code = code.strip()
        if self.strip_prefix and code.startswith(self.strip_prefix):
            code = code[len(self.strip_prefix):]
        if self.strip_suffix and code.endswith(self.strip_suffix):
            code = code[:-len(self.strip_suffix)]
        return self._apply(code.replace(' ', '') if self.transform ==
                           'nospace' else code)

    def check(self, code):
        if not code:
            return 'Código vacío'
        if self.min_length and len(code) < self.min_length:
            return 'Mínimo {0} caracteres'.format(self.min_length)
        if self.max_code and len(code) > self.max_code:
            return 'Máximo {0} caracteres'.format(self.max_code)
        if self.pattern and not self.pattern.fullmatch(code):
            return 'Formato no válido'
        if self.unique and code in self.scans:
            return 'Ya leído'
        return None

    def submit(self):
        code = self.clean(self.text)
        now = self.clock()
        last_code, last_time = self._last
        if code == last_code and (now - last_time) * 1000 < self.duplicate_ms:
            self._edit('', 0)
            return True
        self.error = self.check(code)
        if self.error is None:
            self.scans.append(code)
            del self.scans[:-self.history_size]
            self._last = (code, now)
            if self.on_scan is not None:
                self.on_scan(code)
            self.text, self.cursor_pos = '', 0
        self.refresh()
        return True

    def suffix(self):
        return '{0} leídos'.format(len(self.scans)) if self.scans else ''


# +---------------------------------------------------------------------------+
# Choices

class Checkbox(Input):
    """``[x] label``: Space or Enter toggles (or a click)."""

    role = 'checkbox'

    def a11y_state(self):
        state = ['checked' if self._value else 'unchecked']
        if self.required:
            state.append('required')
        if self.error:
            state.append('invalid')
        return state

    def a11y_value(self):
        return ''

    def on_mouse(self, event):
        if event.action == 'press' and event.button == 0 and event.y == 0:
            self.set_value(not self._value)
            return True
        return False

    def __init__(self, label=None, value=False, **kwargs):
        super(Checkbox, self).__init__(label=label, value=value, **kwargs)

    def coerce(self, value):
        return bool(value)

    def is_empty(self):
        return not self._value

    def on_key(self, key):
        if str(key) in ('space', 'enter'):
            self.set_value(not self._value)
            return True
        return False

    def draw(self, width, height):
        box = '[x]' if self._value else '[ ]'
        if self._active():
            box = '☑' if self._value else '☐'
        spec = self.theme.accent if self.focused else None
        line = self.marker() + ' ' + self.paint(box, spec) + ' ' + \
            (self.label or '') + ('*' if self.required else '')
        out = [line]
        if self.error:
            out.append(self.paint('✖ ' + self.error, self.theme.error))
        elif self.help:
            out.append(self.paint('  ' + self.help, self.theme.muted))
        return out


class Switch(Checkbox):
    """An on/off switch; ``labels`` names the two states."""

    role = 'switch'

    def a11y_state(self):
        return ['on' if self._value else 'off']

    def a11y_value(self):
        return self.labels[1] if self._value else self.labels[0]

    def __init__(self, label=None, value=False, labels=('No', 'Sí'),
                 **kwargs):
        self.labels = labels
        super(Switch, self).__init__(label=label, value=value, **kwargs)

    def draw(self, width, height):
        on = self._value
        if self._active():
            track = self.paint(' ━━●', self.theme.success) if on else \
                self.paint('●━━ ', self.theme.muted)
        else:
            track = '[ on]' if on else '[off]'
        state = self.labels[1] if on else self.labels[0]
        label = self.paint(self.label or '', self.theme.accent
                           if self.focused else None)
        return [self.marker() + ' ' + label + ' ' + track + ' ' + state]


class RadioGroup(Input):
    """
    One of ``options``. ``layout='vertical'`` lists them (Up/Down), ``'buttons'``
    draws a segmented row (Left/Right). Moving selects.
    """

    def __init__(self, label=None, options=(), value=None,
                 layout='vertical', **kwargs):
        self.options = normalize_options(options)
        self.layout = layout
        self.index = 0
        super(RadioGroup, self).__init__(label=label, value=value, **kwargs)
        values = [v for v, _ in self.options]
        if self._value in values:
            self.index = values.index(self._value)

    role = 'radiogroup'

    def a11y_value(self):
        for value, label in self.options:
            if value == self._value:
                return '{0} ({1} de {2})'.format(
                    label, self.options.index((value, label)) + 1,
                    len(self.options))
        return ''

    def a11y_state(self):
        return Input.a11y_state(self)

    def _pick(self, i):
        self.index = i
        self.set_value(self.options[i][0])
        return True

    def coerce(self, value):
        return value

    def _move(self, step):
        if not self.options:
            return True
        self.index = (self.index + step) % len(self.options)
        self.set_value(self.options[self.index][0])
        return True

    def on_key(self, key):
        k = str(key)
        horizontal = self.layout == 'buttons'
        back = ('left',) if horizontal else ('up',)
        fwd = ('right',) if horizontal else ('down',)
        if k in back:
            return self._move(-1)
        if k in fwd:
            return self._move(1)
        if k in ('space', 'enter') and self.options:
            self.set_value(self.options[self.index][0])
            return True
        if len(k) == 1:
            for i, (_, label) in enumerate(self.options):
                if label[:1].lower() == k.lower():
                    self.index = i
                    self.set_value(self.options[i][0])
                    return True
        return False

    def control(self, width, height):
        if self.layout == 'buttons':
            parts = []
            for i, (value, label) in enumerate(self.options):
                chosen = value == self._value
                spec = (self.theme.selection if self.focused else
                        'reverse') if chosen else 'on bright_black'
                text = ' {0} '.format(label)
                if not self._active():
                    text = '[{0}]'.format(label) if chosen else \
                        ' {0} '.format(label)
                elif chosen and self._marked():
                    text = '[{0}]'.format(label)
                x0 = 2 + sum(_fx.visible_width(p) for p in
                             (_fx.strip_ansi(q) for q in parts))
                self.hot(0, lambda i=i: self._pick(i), x0,
                         x0 + _fx.visible_width(text))
                parts.append(self.paint(text, spec))
            return [self.marker() + ' ' + ''.join(parts)]
        out = []
        for i, (value, label) in enumerate(self.options):
            dot = '(•)' if value == self._value else '( )'
            if self._active():
                dot = '◉' if value == self._value else '○'
            here = self.focused and i == self.index
            self.hot(len(out), lambda i=i: self._pick(i))
            out.append((self.marker() if here else ' ') + ' ' +
                       self.paint(dot + ' ' + label,
                                  self.theme.accent if here else None))
        return out


class CheckboxGroup(RadioGroup):
    """Several of ``options``: Up/Down move, Space toggles. Value: a list."""

    role = 'group'

    def a11y_value(self):
        chosen = [label for value, label in self.options
                  if value in self._value]
        return '{0} de {1} marcadas{2}'.format(
            len(chosen), len(self.options),
            (': ' + ', '.join(chosen)) if chosen else '')

    def _pick(self, i):
        self.index = i
        value = self.options[i][0]
        chosen = list(self._value)
        if value in chosen:
            chosen.remove(value)
        else:
            chosen.append(value)
        order = [v for v, _ in self.options]
        self.set_value(sorted(chosen, key=order.index))
        return True

    def coerce(self, value):
        return list(value or [])

    def on_key(self, key):
        k = str(key)
        if k == 'up' and self.options:
            self.index = (self.index - 1) % len(self.options)
        elif k == 'down' and self.options:
            self.index = (self.index + 1) % len(self.options)
        elif k in ('space', 'enter') and self.options:
            value = self.options[self.index][0]
            chosen = list(self._value)
            if value in chosen:
                chosen.remove(value)
            else:
                chosen.append(value)
            order = [v for v, _ in self.options]
            self.set_value(sorted(chosen, key=order.index))
        elif k == 'ctrl+a':
            self.set_value([v for v, _ in self.options])
        else:
            return False
        self.refresh()
        return True

    def control(self, width, height):
        out = []
        for i, (value, label) in enumerate(self.options):
            on = value in self._value
            box = ('☑' if on else '☐') if self._active() else \
                ('[x]' if on else '[ ]')
            here = self.focused and i == self.index
            self.hot(len(out), lambda i=i: self._pick(i))
            out.append((self.marker() if here else ' ') + ' ' +
                       self.paint(box + ' ' + label,
                                  self.theme.accent if here else None))
        return out


class Select(Input):
    """
    A drop-down list. Enter or Space opens it; typing filters; Up/Down move;
    Enter picks; Escape closes. ``max_visible`` rows show at once.
    """

    def __init__(self, label=None, options=(), value=None, max_visible=6,
                 placeholder='Selecciona…', **kwargs):
        self.options = normalize_options(options)
        self.max_visible = max(1, int(max_visible))
        self.placeholder = placeholder
        self.open = False
        self.query = ''
        self.index = 0
        self.top = 0
        super(Select, self).__init__(label=label, value=value, **kwargs)

    role = 'combobox'

    def label_of(self, value):
        for v, label in self.options:
            if v == value:
                return label
        return None if value is None else str(value)

    def a11y_value(self):
        if self.open:
            items = self.matches()
            if items:
                i = min(self.index, len(items) - 1)
                return '{0} ({1} de {2})'.format(items[i][1], i + 1,
                                                 len(items))
        return self.label_of(self._value) or ''

    def a11y_state(self):
        return ['expanded' if self.open else 'collapsed'] + \
            Input.a11y_state(self)

    def _toggle(self):
        if self.open:
            self.open = False
        else:
            self.on_key(Key('enter'))
        return True

    def _choose(self, i):
        items = self.matches()
        if i < len(items):
            self.set_value(items[i][0])
        self.open = False
        return True

    def matches(self):
        q = self.query.lower()
        return [o for o in self.options if q in o[1].lower()]

    def on_blur(self):
        self.open = False

    def on_key(self, key):
        k = str(key)
        if not self.open:
            if k in ('enter', 'space', 'down', 'alt+down'):
                self.open = True
                self.query = ''
                values = [v for v, _ in self.options]
                self.index = values.index(self._value) \
                    if self._value in values else 0
                self.refresh()
                return True
            return False
        items = self.matches()
        if k == 'escape':
            self.open = False
        elif k == 'up':
            self.index = max(0, self.index - 1)
        elif k == 'down':
            self.index = min(max(0, len(items) - 1), self.index + 1)
        elif k == 'pageup':
            self.index = max(0, self.index - self.max_visible)
        elif k == 'pagedown':
            self.index = min(max(0, len(items) - 1),
                             self.index + self.max_visible)
        elif k == 'enter':
            if items:
                self.set_value(items[min(self.index, len(items) - 1)][0])
            self.open = False
        elif k == 'backspace':
            self.query = self.query[:-1]
            self.index = 0
        elif key.is_printable:
            self.query += key.char
            self.index = 0
        else:
            return k not in ('tab', 'shift+tab')
        self.refresh()
        return True

    def control(self, width, height):
        shown = self.label_of(self._value)
        arrow = '▴' if self.open else '▾'
        avail = max(1, width - 4)
        if shown is None:
            body = self.paint(self.placeholder, self.theme.muted)
        else:
            body = shown
        line = self.marker() + ' ' + _fx.fit_line(body, avail) + ' ' + \
            self.paint(arrow, self.theme.accent if self.focused else
                       self.theme.muted)
        out = [line]
        self.hot(0, self._toggle)
        if self.open:
            items = self.matches()
            if self.query:
                out.append('  ' + self.paint('/' + self.query,
                                             self.theme.accent))
            if self.index < self.top:
                self.top = self.index
            if self.index >= self.top + self.max_visible:
                self.top = self.index - self.max_visible + 1
            for i in range(self.top, min(len(items), self.top +
                                         self.max_visible)):
                text = _fx.fit_line(' ' + items[i][1], max(1, width - 2))
                if i == self.index:
                    text = self.mark_current(text, self.theme.selection)
                self.hot(len(out), lambda i=i: self._choose(i))
                out.append('  ' + text)
            if not items:
                out.append('  ' + self.paint('Sin resultados',
                                             self.theme.muted))
        return out


class Autocomplete(TextInput):
    """
    Text with suggestions from ``options`` (matching anywhere, case- and
    accent-insensitive). Up/Down choose a suggestion, Enter or Right accepts
    it. ``strict=True`` only accepts an option's label.
    """

    def __init__(self, label=None, options=(), value='', max_suggestions=5,
                 strict=False, **kwargs):
        self.options = normalize_options(options)
        self.max_suggestions = max(1, int(max_suggestions))
        self.strict = bool(strict)
        self.highlight = -1
        super(Autocomplete, self).__init__(label=label, value=value, **kwargs)

    @staticmethod
    def _fold(text):
        import unicodedata
        return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                       if unicodedata.category(c) != 'Mn')

    def suggestions(self):
        q = self._fold(self.text.strip())
        if not q:
            return []
        starts = [o for o in self.options if self._fold(o[1]).startswith(q)]
        inside = [o for o in self.options if q in self._fold(o[1])
                  and o not in starts]
        found = starts + inside
        if len(found) == 1 and found[0][1] == self.text:
            return []
        return found[:self.max_suggestions]

    def parse(self, text):
        for value, label in self.options:
            if label == text:
                return value
        if self.strict and text:
            raise ValueError('Elige una opción de la lista')
        return text

    def format(self, value):
        for v, label in getattr(self, 'options', []):
            if v == value:
                return label
        return super(Autocomplete, self).format(value)

    def on_key(self, key):
        k = str(key)
        items = self.suggestions()
        if items and k in ('up', 'down'):
            step = 1 if k == 'down' else -1
            self.highlight = (self.highlight + step) % len(items)
            self.refresh()
            return True
        if items and k in ('enter', 'right') and (
                self.highlight >= 0 or k == 'enter' or
                self.cursor_pos == len(self.text)):
            pick = items[max(0, self.highlight)]
            self._edit(pick[1], len(pick[1]))
            self.highlight = -1
            if k == 'enter':
                return self.submit()
            return True
        if k == 'escape' and items:
            self.highlight = -1
            self.text_before = self.text
            return True
        self.highlight = -1
        return super(Autocomplete, self).on_key(key)

    role = 'combobox'

    def _accept_suggestion(self, i):
        items = self.suggestions()
        if i < len(items):
            self._edit(items[i][1], len(items[i][1]))
        self.highlight = -1
        return True

    def on_mouse(self, event):
        if _Themed.on_mouse(self, event):
            return True
        return TextInput.on_mouse(self, event)

    def control(self, width, height):
        out = super(Autocomplete, self).control(width, height)
        if self.focused:
            for i, (_, label) in enumerate(self.suggestions()):
                self.hot(len(out), lambda i=i: self._accept_suggestion(i))
                text = _fx.fit_line(' ' + label, max(1, width - 2))
                if i == self.highlight:
                    text = self.mark_current(text, self.theme.selection)
                else:
                    text = self.paint(text, self.theme.muted)
                out.append('  ' + text)
        return out


_PALETTE = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#1abc9c', '#3498db',
            '#9b59b6', '#34495e', '#95a5a6', '#ffffff', '#000000']
_HEX = re.compile(r'^#?([0-9a-fA-F]{6})$')


class ColorInput(TextInput):
    """A ``#rrggbb`` colour with a swatch; Up/Down walk a palette."""

    def __init__(self, label=None, value='', palette=None, **kwargs):
        self.palette = list(palette or _PALETTE)
        kwargs.setdefault('allowed', r'[#0-9a-fA-F]')
        kwargs.setdefault('max_length', 7)
        kwargs.setdefault('transform', 'lower')
        super(ColorInput, self).__init__(label=label, value=value, **kwargs)

    def parse(self, text):
        if not text:
            return None
        match = _HEX.match(text)
        if not match:
            raise ValueError('Color #rrggbb')
        return '#' + match.group(1).lower()

    def suffix(self):
        value = self.value
        if value is None:
            return '  '
        return '██' if not self._active() else ''

    def control(self, width, height):
        line = super(ColorInput, self).control(width - 3, height)[0]
        value = self.value
        swatch = self.paint('██', value) if value and self._active() else \
            '  '
        return [line + ' ' + swatch]

    def on_key(self, key):
        k = str(key)
        if k in ('up', 'down'):
            value = self.value
            i = self.palette.index(value) if value in self.palette else -1
            i = (i + (1 if k == 'down' else -1)) % len(self.palette)
            self._edit(self.palette[i], len(self.palette[i]))
            return True
        return super(ColorInput, self).on_key(key)


ICONS = [
    ('home', '⌂'), ('user', '👤'), ('users', '👥'), ('star', '★'),
    ('heart', '♥'), ('check', '✔'), ('cross', '✖'), ('warning', '⚠'),
    ('info', 'ℹ'), ('question', '?'), ('search', '🔍'), ('gear', '⚙'),
    ('mail', '✉'), ('phone', '☎'), ('calendar', '📅'), ('clock', '🕒'),
    ('lock', '🔒'), ('unlock', '🔓'), ('key', '🔑'), ('bell', '🔔'),
    ('folder', '📁'), ('file', '📄'), ('chart', '📈'), ('cart', '🛒'),
    ('money', '💲'), ('box', '📦'), ('truck', '🚚'), ('tag', '🏷'),
    ('pin', '📌'), ('flag', '⚑'), ('bolt', '⚡'), ('fire', '🔥'),
    ('cloud', '☁'), ('sun', '☀'), ('moon', '☾'), ('globe', '🌐'),
    ('link', '🔗'), ('edit', '✎'), ('trash', '🗑'), ('plus', '＋'),
    ('minus', '－'), ('play', '▶'), ('pause', '⏸'), ('stop', '■'),
    ('refresh', '↻'), ('up', '↑'), ('down', '↓'), ('left', '←'),
    ('right', '→'), ('menu', '☰'), ('dot', '●'), ('circle', '○'),
    ('square', '□'), ('diamond', '◆'), ('triangle', '▲'), ('music', '♪'),
    ('camera', '📷'), ('print', '🖨'), ('save', '💾'), ('database', '🗄'),
    ('server', '🖥'), ('code', '⌨'), ('bug', '🐞'), ('shield', '🛡'),
]


class IconPicker(Input):
    """
    An icon from a grid (``icons``: ``(name, symbol)`` pairs). Typing filters
    by name; arrows move; Enter picks. ``value`` is the name.
    """

    def __init__(self, label=None, value=None, icons=None, columns=8,
                 rows=3, **kwargs):
        self.icons = list(icons or ICONS)
        self.columns = max(1, int(columns))
        self.rows = max(1, int(rows))
        self.query = ''
        self.index = 0
        super(IconPicker, self).__init__(label=label, value=value, **kwargs)

    role = 'listbox'

    def matches(self):
        return [i for i in self.icons if self.query in i[0]]

    def _icon(self, i):
        items = self.matches()
        if self.index == i and i < len(items):
            self.set_value(items[i][0])
        self.index = i
        return True

    def symbol(self):
        for name, sym in self.icons:
            if name == self._value:
                return sym
        return ''

    def on_key(self, key):
        k = str(key)
        items = self.matches()
        moves = {'left': -1, 'right': 1, 'up': -self.columns,
                 'down': self.columns}
        if k in moves and items:
            self.index = max(0, min(len(items) - 1, self.index + moves[k]))
        elif k == 'enter' and items:
            self.set_value(items[min(self.index, len(items) - 1)][0])
        elif k == 'backspace':
            self.query = self.query[:-1]
            self.index = 0
        elif key.is_printable and k != ' ':
            self.query += key.char.lower()
            self.index = 0
        else:
            return False
        self.refresh()
        return True

    def control(self, width, height):
        out = [self.marker() + ' ' + (self.symbol() + ' ' + str(self._value)
                                      if self._value else
                                      self.paint('Sin ícono', self.theme.muted))
               + ('  /' + self.query if self.query else '')]
        if not self.focused:
            return out
        items = self.matches()
        first_row = max(0, self.index // self.columns - self.rows + 1)
        for r in range(first_row, first_row + self.rows):
            cells = []
            for c in range(self.columns):
                i = r * self.columns + c
                if i >= len(items):
                    break
                sym = _fx.fit_line(items[i][1], 2)
                cell = ' ' + sym + ' '
                if i == self.index:
                    cell = self.paint(cell, self.theme.selection) if \
                        self._active() and not self._marked() else \
                        self.paint('[' + sym + ']', self.theme.selection)
                self.hot(len(out), lambda i=i: self._icon(i), 2 + 4 * c,
                         6 + 4 * c)
                cells.append(cell)
            if cells:
                out.append('  ' + ''.join(cells))
        if items:
            out.append('  ' + self.paint(items[min(self.index, len(items) - 1)]
                                         [0], self.theme.muted))
        return out


class CoordinatesInput(Input):
    """Latitude and longitude, side by side. Value: ``{'latitude': ...,
    'longitude': ...}``."""

    focusable = False

    def __init__(self, label=None, value=None, decimals=6, **kwargs):
        theme = kwargs.get('theme')
        colors = kwargs.get('use_colors')
        self.latitude = NumberInput('Latitud', minimum=-90, maximum=90,
                                    decimals=decimals, theme=theme,
                                    use_colors=colors)
        self.longitude = NumberInput('Longitud', minimum=-180, maximum=180,
                                     decimals=decimals, theme=theme,
                                     use_colors=colors)
        super(CoordinatesInput, self).__init__(label=label, value=value,
                                               **kwargs)

    def children(self):
        return [self.latitude, self.longitude]

    @property
    def value(self):
        lat, lon = self.latitude.value, self.longitude.value
        if lat is None and lon is None:
            return None
        return {'latitude': lat, 'longitude': lon}

    @value.setter
    def value(self, new):
        if not new:
            return
        if isinstance(new, dict):
            lat, lon = new.get('latitude'), new.get('longitude')
        else:
            lat, lon = new
        self.latitude.value = lat
        self.longitude.value = lon

    def is_empty(self):
        return self.value is None

    def validate(self):
        errors = [self.latitude.validate(), self.longitude.validate()]
        self.error = next((e for e in errors if e), None)
        if self.error is None:
            return super(CoordinatesInput, self).validate()
        return self.error

    def control(self, width, height):
        half = max(1, (width - 1) // 2)
        left = self.latitude.render(width=half).split('\n')
        right = self.longitude.render(width=width - half - 1).split('\n')
        from .base import join_columns
        return join_columns([left, right], [half, width - half - 1])


class FileInput(Input):
    """
    A path, typed or picked from a browser (Enter opens it): Up/Down move,
    Enter opens a folder or picks a file, Backspace goes up, Escape closes.
    ``extensions`` limits the files listed; ``multiple=True`` picks several
    with Space. ``value`` is the path (a list with ``multiple``).
    """

    def __init__(self, label=None, value=None, directory=None,
                 extensions=None, multiple=False, show_hidden=False,
                 max_visible=8, **kwargs):
        self.directory = os.path.abspath(directory or os.getcwd())
        self.extensions = tuple(e.lower() for e in (extensions or ()))
        self.multiple = bool(multiple)
        self.show_hidden = bool(show_hidden)
        self.max_visible = max(1, int(max_visible))
        self.open = False
        self.index = 0
        self.top = 0
        super(FileInput, self).__init__(label=label, value=value, **kwargs)

    def coerce(self, value):
        if self.multiple:
            return list(value or [])
        return value

    role = 'combobox'

    def a11y_state(self):
        return ['expanded' if self.open else 'collapsed'] + \
            Input.a11y_state(self)

    def a11y_value(self):
        if self.open:
            items = self.entries()
            name, is_dir = items[min(self.index, len(items) - 1)]
            return name + (' (carpeta)' if is_dir else '')
        return Input.a11y_value(self) if not self.multiple else \
            ', '.join(os.path.basename(p) for p in self._value)

    def _entry(self, i):
        if not self.open:
            return self.on_key(Key('enter'))
        if self.index == i:
            return self.on_key(Key('enter'))
        self.index = i
        return True

    def entries(self):
        try:
            names = sorted(os.listdir(self.directory), key=str.lower)
        except OSError:
            return [('..', True)]
        out = [('..', True)]
        for name in names:
            if name.startswith('.') and not self.show_hidden:
                continue
            path = os.path.join(self.directory, name)
            is_dir = os.path.isdir(path)
            if not is_dir and self.extensions and \
                    not name.lower().endswith(self.extensions):
                continue
            out.append((name, is_dir))
        out.sort(key=lambda e: (e[0] != '..', not e[1], e[0].lower()))
        return out

    def on_blur(self):
        self.open = False

    def _pick(self, path):
        if self.multiple:
            chosen = list(self._value)
            if path in chosen:
                chosen.remove(path)
            else:
                chosen.append(path)
            self.set_value(chosen)
        else:
            self.set_value(path)
            self.open = False

    def on_key(self, key):
        k = str(key)
        if not self.open:
            if k in ('enter', 'space'):
                self.open = True
                self.index = self.top = 0
                self.refresh()
                return True
            return False
        items = self.entries()
        if k == 'escape':
            self.open = False
        elif k == 'up':
            self.index = max(0, self.index - 1)
        elif k == 'down':
            self.index = min(len(items) - 1, self.index + 1)
        elif k == 'backspace':
            self.directory = os.path.dirname(self.directory)
            self.index = self.top = 0
        elif k in ('enter', 'space'):
            name, is_dir = items[min(self.index, len(items) - 1)]
            path = os.path.normpath(os.path.join(self.directory, name))
            if is_dir and k == 'enter':
                self.directory = path
                self.index = self.top = 0
            elif not is_dir:
                self._pick(path)
        else:
            return k not in ('tab', 'shift+tab')
        self.refresh()
        return True

    def control(self, width, height):
        if self.multiple:
            shown = ', '.join(os.path.basename(p) for p in self._value)
        else:
            shown = self._value or ''
        body = shown or self.paint('Elige un archivo…', self.theme.muted)
        out = [self.marker() + ' ' + _fx.truncate(body, max(1, width - 4),
                                                 '…')]
        if not self.open:
            self.hot(0, lambda: self.on_key(Key('enter')))
            return out
        out.append('  ' + self.paint(_fx.truncate(self.directory,
                                                  max(1, width - 2), '…'),
                                     self.theme.muted))
        items = self.entries()
        if self.index < self.top:
            self.top = self.index
        if self.index >= self.top + self.max_visible:
            self.top = self.index - self.max_visible + 1
        chosen = self._value if self.multiple else [self._value]
        for i in range(self.top, min(len(items), self.top + self.max_visible)):
            name, is_dir = items[i]
            path = os.path.normpath(os.path.join(self.directory, name))
            mark = '▸ ' if is_dir else ('✔ ' if path in chosen else '  ')
            text = _fx.fit_line(mark + name + ('/' if is_dir and name != '..'
                                               else ''), max(1, width - 2))
            if i == self.index:
                text = self.mark_current(text, self.theme.selection)
            self.hot(len(out), lambda i=i: self._entry(i))
            out.append('  ' + text)
        return out
