"""
Data components: an interactive table with sorting, filtering, paging and
selection; a filter bar with a small query language; an editable table; a
catalog of cards; forms with validation (and a login form); file preview.
"""

import datetime as _dt
import math
import os
import re

from flexablelib import _frames as _fx
from flexablelib.identifiers import is_id_column

from .base import Button, Input, _Themed, frame, join_columns
from .inputs import TextInput, PasswordInput, Checkbox

__all__ = ['DataTable', 'FilterBar', 'EditableTable', 'CatalogGrid', 'Form',
           'ValidationSummary', 'LoginForm', 'FilePreview', 'parse_query']


def _cell_text(value, fmt=None):
    if fmt is not None:
        return str(fmt(value))
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Sí' if value else 'No'
    if isinstance(value, float):
        return '{0:,.2f}'.format(value)
    if isinstance(value, int):
        return '{0:,}'.format(value)
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()[:16].replace('T', ' ')
    return str(value)


def _sort_key(value):
    if value is None:
        return (2, '')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (0, value)
    return (1, str(value).lower())


class DataTable(_Themed):
    """
    An interactive table.

    ``columns``: names, or dicts with ``key``, ``title``, ``align``
    (``'l'``/``'r'``/``'c'``), ``width``, ``format(value)`` and
    ``color(value) -> spec`` and ``type``. ``rows``: dicts or sequences.

    Integers get thousands separators (``15,000``) except in identifier
    columns -- folios, IDs, codes, SKUs, years -- which print as typed
    (``1281``): a column with ``'type': 'id'`` (or ``'folio'``, ``'code'``),
    or, with ``id_columns='auto'`` (the default), one whose name says so
    (:func:`flexablelib.is_id_column`; ``id_names`` replaces the word list).
    ``'type': 'number'`` keeps the separators whatever the name;
    ``id_columns=False`` restores the 3.3 behaviour (separators everywhere)
    and a list names the id columns by key, title or position.

    Keys: Up/Down/PgUp/PgDn/Home/End move; ``1``-``9`` sort by that column
    (again: reverse); ``/`` types a quick filter (Enter/Escape end it,
    Escape twice clears it); Space selects (``selectable=True``), Ctrl-A all;
    Left/Right scroll columns that do not fit; Enter calls
    ``on_activate(row)``. ``filters`` are extra predicates (a
    :class:`FilterBar`'s ``predicate``). ``page_size`` pages instead of
    scrolling.
    """

    focusable = True
    expand = True
    role = 'grid'

    def a11y_value(self):
        view = self.view()
        if not view:
            return self.empty
        row = self.current
        n = min(self.cursor_row, len(view) - 1)
        cells = ', '.join('{0} {1}'.format(c['title'], self.text(row, ci))
                          for ci, c in enumerate(self.columns))
        text = 'fila {0} de {1}: {2}'.format(n + 1, len(view), cells)
        if self.sort_key is not None:
            text += '; ordenada por {0} {1}'.format(
                self.columns[self.sort_key]['title'],
                'descendente' if self.sort_desc else 'ascendente')
        return text

    def a11y_state(self):
        view = self.view()
        if self.selectable and view and \
                view[min(self.cursor_row, len(view) - 1)] in self.selected:
            return ['selected']
        return []

    def _click_row(self, n, x):
        view = self.view()
        if n >= len(view):
            return True
        if self.selectable and x < 2:
            i = view[n]
            self.selected.symmetric_difference_update([i])
            if self.on_select is not None:
                self.on_select(self.selected_rows())
            self.cursor_row = n
            return True
        if n == self.cursor_row and self.on_activate is not None:
            self.on_activate(self.current)
        self.cursor_row = n
        return True

    def on_mouse(self, event):
        if event.action == 'scroll' and event.button in (64, 65):
            self._move(-3 if event.button == 64 else 3)
            self.refresh()
            return True
        if event.action == 'press' and event.button == 0:
            for row, x0, x1, action in self._hot:
                if row == event.y and x0 <= event.x < (x1 or 1 << 30):
                    action(event.x) if getattr(action, 'wants_x', False) \
                        else action()
                    self.refresh()
                    return True
        return False

    def __init__(self, columns, rows=(), height=None, selectable=False,
                 on_activate=None, on_select=None, zebra=True,
                 page_size=None, status=True, empty='Sin registros',
                 id_columns='auto', id_names=None, **kwargs):
        super(DataTable, self).__init__(**kwargs)
        self.id_columns = id_columns
        self.id_names = id_names
        self.columns = [self._column(c, i) for i, c in enumerate(columns)]
        self.rows = list(rows)
        self.height = height
        self.selectable = bool(selectable)
        self.on_activate = on_activate
        self.on_select = on_select
        self.zebra = bool(zebra)
        self.page_size = page_size
        self.page = 1
        self.status = bool(status)
        self.empty = empty
        self.cursor_row = 0
        self.top = 0
        self.col_offset = 0
        self.sort_key = None
        self.sort_desc = False
        self.query = ''
        self.typing = False
        self.filters = []
        self.selected = set()
        self._view = None

    @staticmethod
    def _column(column, index):
        if isinstance(column, dict):
            c = dict(column)
            c.setdefault('key', index)
            c.setdefault('title', str(c['key']))
            return c
        return {'key': column if isinstance(column, str) else index,
                'title': str(column)}

    def align(self, ci):
        """A column's alignment: given, or right for numbers."""
        column = self.columns[ci]
        if 'align' not in column:
            for row in self.rows[:50]:
                value = self._get(row, column, ci)
                if value is not None:
                    column['_auto'] = 'r' if isinstance(value, (int, float)) \
                        and not isinstance(value, bool) else 'l'
                    break
            return column.get('_auto', 'l')
        return column['align']

    def _get(self, row, column, index):
        if isinstance(row, dict):
            return row.get(column['key'])
        k = column['key'] if isinstance(column['key'], int) else index
        return row[k] if k < len(row) else None

    _ID_TYPES = ('id', 'folio', 'code', 'codigo', 'código', 'clave', 'key')
    _NUMBER_TYPES = ('number', 'numero', 'número', 'money', 'quantity',
                     'int', 'float', 'amount')

    def is_id_column(self, ci):
        """Whether column ``ci`` holds identifiers (no separators)."""
        column = self.columns[ci]
        kind = str(column.get('type', '')).lower()
        if kind in self._ID_TYPES:
            return True
        if kind in self._NUMBER_TYPES:
            return False
        setting = self.id_columns
        if not setting:
            return False
        if setting == 'auto' or setting is True:
            cached = column.get('_id')
            if cached is None:
                cached = column['_id'] = is_id_column(
                    column.get('title', column['key']), self.id_names) or \
                    (isinstance(column['key'], str) and
                     is_id_column(column['key'], self.id_names))
            return cached
        return column['key'] in setting or column.get('title') in setting \
            or ci in setting

    def text(self, row, ci):
        column = self.columns[ci]
        value = self._get(row, column, ci)
        fmt = column.get('format')
        if fmt is None and isinstance(value, int) and \
                not isinstance(value, bool) and self.is_id_column(ci):
            return str(value)
        return _cell_text(value, fmt)

    def invalidate(self):
        self._view = None
        self.refresh()

    def set_rows(self, rows):
        self.rows = list(rows)
        self.selected.clear()
        self.invalidate()

    def view(self):
        """Indices into ``rows`` after filters and sorting."""
        if self._view is not None:
            return self._view
        idx = list(range(len(self.rows)))
        q = self.query.lower()
        if q:
            idx = [i for i in idx if any(
                q in self.text(self.rows[i], c).lower()
                for c in range(len(self.columns)))]
        for predicate in self.filters:
            idx = [i for i in idx if predicate(self.rows[i])]
        if self.sort_key is not None:
            ci = self.sort_key
            col = self.columns[ci]
            values = {i: self._get(self.rows[i], col, ci) for i in idx}
            # Empty cells stay at the end in both directions.
            filled = [i for i in idx if values[i] is not None]
            empty = [i for i in idx if values[i] is None]
            filled.sort(key=lambda i: _sort_key(values[i]),
                        reverse=self.sort_desc)
            idx = filled + empty
        self._view = idx
        return idx

    @property
    def current(self):
        view = self.view()
        if not view:
            return None
        return self.rows[view[min(self.cursor_row, len(view) - 1)]]

    def selected_rows(self):
        return [self.rows[i] for i in sorted(self.selected)]

    def sort_by(self, ci, descending=None):
        if self.sort_key == ci and descending is None:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_key = ci
            self.sort_desc = bool(descending)
        self.invalidate()
        return True

    def natural_width(self):
        return sum(self._natural(ci) + 2 for ci in range(len(self.columns)))

    def _natural(self, ci):
        column = self.columns[ci]
        if column.get('width'):
            return column['width']
        sample = self.rows[:200]
        w = max([_fx.visible_width(self.text(r, ci)) for r in sample] + [0])
        return max(w, _fx.visible_width(column['title']) + 2)

    def _widths(self, width):
        width -= 2 if self.selectable else 0
        natural = [self._natural(ci) for ci in range(len(self.columns))]
        cols = list(range(self.col_offset, len(self.columns)))
        widths = {ci: natural[ci] for ci in cols}
        total = lambda: sum(widths.values()) + 2 * len(widths)  # noqa: E731
        # Shrink the widest columns first, down to a minimum.
        while total() > width:
            wide = max(widths, key=lambda c: widths[c])
            if widths[wide] <= 6:
                break
            widths[wide] -= 1
        while total() > width and len(widths) > 1:
            widths.pop(max(widths))
        return widths

    def _move(self, step):
        n = len(self.view())
        if n:
            self.cursor_row = max(0, min(n - 1, self.cursor_row + step))
        return True

    def on_key(self, key):
        k = str(key)
        if self.typing:
            if k in ('enter', 'escape'):
                self.typing = False
            elif k == 'backspace':
                self.query = self.query[:-1]
            elif key.is_printable or k == 'space':
                self.query += key.char or ' '
            elif k == 'paste':
                self.query += key.char
            else:
                return k not in ('tab', 'shift+tab')
            self.cursor_row = 0
            self.invalidate()
            return True
        view = self.view()
        page = self.page_size or self._rows_shown
        if k in ('up', 'k'):
            self._move(-1)
        elif k in ('down', 'j'):
            self._move(1)
        elif k == 'pageup':
            self._move(-page)
        elif k == 'pagedown':
            self._move(page)
        elif k in ('home', 'g'):
            self.cursor_row = 0
        elif k in ('end', 'G'):
            self.cursor_row = max(0, len(view) - 1)
        elif k == 'right':
            self.col_offset = min(len(self.columns) - 1, self.col_offset + 1)
        elif k == 'left':
            self.col_offset = max(0, self.col_offset - 1)
        elif len(k) == 1 and k.isdigit() and 0 < int(k) <= len(self.columns):
            return self.sort_by(int(k) - 1)
        elif k == '/':
            self.typing = True
        elif k == 'escape' and self.query:
            self.query = ''
            self.invalidate()
        elif k == 'space' and self.selectable and view:
            i = view[min(self.cursor_row, len(view) - 1)]
            self.selected.symmetric_difference_update([i])
            if self.on_select is not None:
                self.on_select(self.selected_rows())
            self._move(1)
        elif k == 'ctrl+a' and self.selectable:
            if len(self.selected) == len(view):
                self.selected.clear()
            else:
                self.selected = set(view)
            if self.on_select is not None:
                self.on_select(self.selected_rows())
        elif k == 'enter' and view and self.on_activate is not None:
            self.on_activate(self.current)
        else:
            return False
        self.refresh()
        return True

    _rows_shown = 10

    def draw(self, width, height):
        view = self.view()
        widths = self._widths(width)
        order = sorted(widths)
        mark_w = 2 if self.selectable else 0
        head = ' ' * mark_w
        x = mark_w
        for ci in order:
            self.hot(0, lambda ci=ci: self.sort_by(ci), x, x + widths[ci] + 2)
            x += widths[ci] + 2
            col = self.columns[ci]
            title = col['title']
            if ci == self.sort_key:
                title += ' ↓' if self.sort_desc else ' ↑'
            head += ' ' + _fx.fit_line(_fx.truncate(title, widths[ci], '…'),
                                       widths[ci], self.align(ci)) + ' '
        out = [self.paint(_fx.fit_line(head, width), 'bold')]
        out.append(self.paint('─' * width, self.theme.accent if self.focused
                              else self.theme.border))
        extra = (1 if self.status else 0) + (1 if self.typing or self.query
                                             else 0)
        rows_h = self.height or (height - 2 - extra if height else None)
        if self.page_size:
            rows_h = self.page_size
        if rows_h is None:
            rows_h = len(view)
        rows_h = max(1, rows_h)
        self._rows_shown = rows_h
        self.cursor_row = max(0, min(self.cursor_row, len(view) - 1))
        if self.page_size:
            self.page = self.cursor_row // self.page_size + 1
            self.top = (self.page - 1) * self.page_size
        else:
            if self.cursor_row < self.top:
                self.top = self.cursor_row
            if self.cursor_row >= self.top + rows_h:
                self.top = self.cursor_row - rows_h + 1
        shown = view[self.top:self.top + rows_h]
        if not view:
            out.append(self.paint(_fx.fit_line(self.empty, width, 'c'),
                                  self.theme.muted))
        for n, i in enumerate(shown):
            row = self.rows[i]
            pick = (lambda x, n=n: self._click_row(self.top + n, x))
            pick.wants_x = True
            self.hot(len(out), pick)
            line = ''
            if mark_w:
                on = i in self.selected
                line += (('☑ ' if on else '☐ ') if self._active() else
                         ('x ' if on else '  '))
            for ci in order:
                col = self.columns[ci]
                text = _fx.truncate(self.text(row, ci), widths[ci], '…')
                text = _fx.fit_line(text, widths[ci], self.align(ci))
                color = col.get('color')
                if color is not None and self._active():
                    text = self.paint(text, color(self._get(row, col, ci)))
                line += ' ' + text + ' '
            line = _fx.fit_line(line, width)
            here = self.top + n == self.cursor_row
            if here and self.focused:
                line = self.mark_current(_fx.strip_ansi(line),
                                      self.theme.selection)
            elif here:
                line = self.paint(line, 'bold')
            elif self.zebra and n % 2 and self._active():
                line = self.paint(line, 'on #1c1c1c')
            out.append(line)
        if self.typing or self.query:
            cur = self.cursor(' ') if self.typing else ''
            out.append(self.paint('/', self.theme.accent) + self.query + cur)
        if self.status:
            pos = '{0}/{1}'.format(self.cursor_row + 1 if view else 0,
                                   len(view))
            parts = [pos]
            if len(view) != len(self.rows):
                parts.append('de {0}'.format(len(self.rows)))
            if self.page_size:
                pages = max(1, -(-len(view) // self.page_size))
                parts.append('pág. {0}/{1}'.format(self.page, pages))
            if self.selected:
                parts.append('{0} seleccionadas'.format(len(self.selected)))
            hidden = len(self.columns) - len(order)
            if hidden or self.col_offset:
                parts.append('◀▶ {0} columnas más'.format(
                    len(self.columns) - len(order)))
            out.append(self.paint(' · '.join(parts), self.theme.muted))
        return out


_QUERY = re.compile(r'(\S+?)(>=|<=|!=|:|=|>|<)("[^"]*"|\S+)|("[^"]*"|\S+)')


def parse_query(query, fields=None):
    """
    ``[(field, op, value), ...]`` from ``estado:pagado total>1000 mérida``;
    a bare word is ``(None, ':', word)`` (matches any field). ``fields``
    limits the field names recognised.
    """
    out = []
    for match in _QUERY.finditer(query):
        if match.group(1) and (fields is None or match.group(1) in fields):
            value = match.group(3).strip('"')
            out.append((match.group(1), match.group(2), value))
        else:
            word = (match.group(4) or match.group(0)).strip('"')
            out.append((None, ':', word))
    return out


def _compare(cell, op, value):
    if op in ('>', '<', '>=', '<='):
        if cell is None:
            return False
        try:
            a, b = float(cell), float(value)
        except (TypeError, ValueError):
            a, b = str(cell or ''), value
        return {'>': a > b, '<': a < b, '>=': a >= b, '<=': a <= b}[op]
    text = '' if cell is None else str(cell).lower()
    if op == ':':
        return value.lower() in text
    if op == '=':
        return text == value.lower()
    return text != value.lower()


class FilterBar(TextInput):
    """
    Filters typed as a query -- ``estado:pagado total>1000 mérida`` (``:``
    contains, ``=`` / ``!=`` equal, ``>`` ``<`` ``>=`` ``<=`` compare, a
    bare word searches every field) -- shown as chips below. ``predicate``
    is the row filter; ``table`` (a :class:`DataTable`) is refreshed on
    every change.
    """

    role = 'searchbox'

    def __init__(self, fields=None, table=None, label=None, **kwargs):
        self.fields = list(fields) if fields else None
        self.table = table
        kwargs.setdefault('placeholder', 'Filtrar: campo:valor  total>100  '
                          'texto')
        super(FilterBar, self).__init__(label=label, **kwargs)
        user_change = self.on_change

        def changed(value):
            if self.table is not None:
                self.table.cursor_row = 0
                self.table.invalidate()
            if user_change is not None:
                user_change(value)
        self.on_change = changed
        if table is not None:
            table.filters.append(self.predicate)

    def terms(self):
        return parse_query(self.text, self.fields)

    def predicate(self, row):
        for field, op, value in self.terms():
            if field is None:
                cells = row.values() if isinstance(row, dict) else row
                if not any(value.lower() in str(c).lower() for c in cells
                           if c is not None):
                    return False
            else:
                cell = row.get(field) if isinstance(row, dict) else None
                if not _compare(cell, op, value):
                    return False
        return True

    def control(self, width, height):
        out = super(FilterBar, self).control(width, height)
        chips = []
        for field, op, value in self.terms():
            text = value if field is None else '{0}{1}{2}'.format(field, op,
                                                                  value)
            chips.append(self.paint(' ' + text + ' ', 'black on ' +
                                    self.theme.accent) if self._active()
                         else '[' + text + ']')
        if chips:
            out.append('  ' + ' '.join(chips))
        return out


class EditableTable(DataTable):
    """
    A :class:`DataTable` whose cells are edited in place: Left/Right choose
    the cell, Enter edits it (Enter saves, Escape cancels), Ctrl-N adds a
    row, Ctrl-D deletes the current one. Column ``type`` ``'number'`` keeps
    numbers. ``on_edit(row, key, value)`` runs after a change.
    """

    def __init__(self, columns, rows=(), on_edit=None, **kwargs):
        super(EditableTable, self).__init__(columns, rows, **kwargs)
        self.on_edit = on_edit
        self.cursor_col = 0
        self.editor = None

    def children(self):
        return []

    def _set(self, row, ci, value):
        column = self.columns[ci]
        if column.get('type') == 'number':
            try:
                value = float(value) if '.' in str(value) else int(value)
            except ValueError:
                return False
        if isinstance(row, dict):
            row[column['key']] = value
        else:
            k = column['key'] if isinstance(column['key'], int) else ci
            while len(row) <= k:
                row.append(None)
            row[k] = value
        if self.on_edit is not None:
            self.on_edit(row, column['key'], value)
        return True

    def on_key(self, key):
        k = str(key)
        if self.editor is not None:
            if k == 'escape':
                self.editor = None
            elif k == 'enter':
                if self._set(self.current, self.cursor_col, self.editor.text):
                    self.editor = None
                    self.invalidate()
                else:
                    self.editor.error = 'Número inválido'
            else:
                self.editor.on_key(key)
            self.refresh()
            return True
        if k in ('left', 'right'):
            step = 1 if k == 'right' else -1
            self.cursor_col = max(0, min(len(self.columns) - 1,
                                         self.cursor_col + step))
            self.refresh()
            return True
        if k == 'enter' and self.current is not None:
            value = self._get(self.current, self.columns[self.cursor_col],
                              self.cursor_col)
            self.editor = TextInput(value='' if value is None else str(value),
                                    theme=self.theme,
                                    use_colors=self.use_colors)
            self.editor.focused = True
            self.refresh()
            return True
        if k == 'ctrl+n':
            new = {c['key']: None for c in self.columns} if (
                not self.rows or isinstance(self.rows[0], dict)) else \
                [None] * len(self.columns)
            self.rows.append(new)
            self.invalidate()
            self.cursor_row = len(self.view()) - 1
            return True
        if k == 'ctrl+d' and self.current is not None:
            self.rows.remove(self.current)
            self.invalidate()
            return True
        return super(EditableTable, self).on_key(key)

    def _click_row(self, n, x):
        widths = self._widths(self._last_width)
        left = 2 if self.selectable else 0
        for ci in sorted(widths):
            if left <= x < left + widths[ci] + 2:
                self.cursor_col = ci
                break
            left += widths[ci] + 2
        if self.editor is not None:
            return True
        return DataTable._click_row(self, n, x)

    _last_width = 80

    def a11y_value(self):
        text = DataTable.a11y_value(self)
        if self.view() and 0 <= self.cursor_col < len(self.columns):
            text += '; celda {0}'.format(
                self.columns[self.cursor_col]['title'])
            if self.editor is not None:
                text += ' (editando: {0})'.format(self.editor.text)
        return text

    def draw(self, width, height):
        self._last_width = width
        lines = super(EditableTable, self).draw(width, height)
        view = self.view()
        if not view or not self.focused:
            return lines
        widths = self._widths(width)
        order = sorted(widths)
        if self.cursor_col not in widths:
            return lines
        x = sum(widths[c] + 2 for c in order if c < self.cursor_col)
        w = widths[self.cursor_col]
        row = 2 + self.cursor_row - self.top
        if not 2 <= row < len(lines):
            return lines
        plain = _fx.strip_ansi(lines[row])
        if self.editor is not None:
            cell = _fx.fit_line(self.editor._viewport(self.editor.text, w), w)
            cell = self.paint(cell, 'underline') if self._active() else cell
        else:
            cell = _fx.slice_columns(plain, x + 1, w)
            cell = self.paint(cell, 'reverse bold') if self._active() else \
                cell
        left = self.paint(_fx.slice_columns(plain, 0, x + 1),
                          self.theme.selection) if self._active() else \
            _fx.slice_columns(plain, 0, x + 1)
        right_w = width - x - 1 - w
        right = self.paint(_fx.slice_columns(plain, x + 1 + w, right_w),
                           self.theme.selection) if self._active() and \
            right_w > 0 else _fx.slice_columns(plain, x + 1 + w, right_w)
        lines[row] = left + cell + right
        return lines


class CatalogGrid(_Themed):
    """
    Items as cards in a grid that reflows with the width: dicts with
    ``title``, ``subtitle``, ``price``, ``badge`` and ``fields``. Arrows
    move, Enter calls ``on_select(item)``.
    """

    focusable = True
    expand = True
    role = 'listbox'

    def a11y_value(self):
        if not self.items:
            return 'Sin elementos'
        item = self.items[min(self.index, len(self.items) - 1)]
        text = '{0} ({1} de {2})'.format(item.get('title', ''),
                                         self.index + 1, len(self.items))
        if item.get('price') is not None:
            text += ', precio {0}'.format(item['price'])
        return text

    def _click(self, i):
        if i == self.index and self.on_select is not None:
            self.on_select(self.items[i])
        self.index = i
        return True

    def __init__(self, items, min_width=24, on_select=None, card_height=6,
                 **kwargs):
        super(CatalogGrid, self).__init__(**kwargs)
        self.items = list(items)
        self.min_width = min_width
        self.on_select = on_select
        self.card_height = card_height
        self.index = 0
        self.top_row = 0
        self._columns = 1

    def natural_width(self):
        return self.min_width * 3 + 2

    def on_key(self, key):
        k = str(key)
        n = len(self.items)
        moves = {'left': -1, 'right': 1, 'up': -self._columns,
                 'down': self._columns}
        if k in moves and n:
            self.index = max(0, min(n - 1, self.index + moves[k]))
        elif k == 'enter' and n and self.on_select is not None:
            self.on_select(self.items[self.index])
        elif k == 'home':
            self.index = 0
        elif k == 'end':
            self.index = max(0, n - 1)
        else:
            return False
        self.refresh()
        return True

    def _card(self, item, width, selected):
        lines = []
        title = str(item.get('title', ''))
        badge = item.get('badge')
        inner = max(1, width - 4)
        head = self.paint(_fx.truncate(title, inner - (len(str(badge)) + 3
                                                       if badge else 0), '…'),
                          'bold')
        if badge:
            head = _fx.fit_line(head, inner - len(str(badge)) - 2) + \
                self.paint(' ' + str(badge) + ' ', 'black on ' +
                           self.theme.warning) if self._active() else \
                head + ' [' + str(badge) + ']'
        lines.append(head)
        if item.get('subtitle'):
            lines.append(self.paint(_fx.truncate(str(item['subtitle']), inner,
                                                 '…'), self.theme.muted))
        for label, value in (item.get('fields') or {}).items():
            lines.append(_fx.truncate('{0}: {1}'.format(label, value), inner,
                                      '…'))
        if item.get('price') is not None:
            price = item['price']
            text = '${0:,.2f}'.format(price) if isinstance(price, (int, float)) \
                else str(price)
            lines.append(self.paint(text, 'bold ' + self.theme.success))
        rows = self.card_height - 2
        lines = lines[:rows] + [''] * (rows - len(lines))
        color = self.theme.accent if selected else self.theme.border
        return frame([' ' + l for l in lines], width, None, color,
                     self.paint, style='heavy' if selected and
                     (not self._active() or self._marked()) else 'rounded')

    def draw(self, width, height):
        cols = max(1, (width + 1) // (self.min_width + 1))
        self._columns = cols
        card_w = (width - (cols - 1)) // cols
        n_rows = int(math.ceil(len(self.items) / float(cols)))
        visible_rows = n_rows if not height else max(1, height //
                                                     self.card_height)
        row_of = self.index // cols
        if row_of < self.top_row:
            self.top_row = row_of
        if row_of >= self.top_row + visible_rows:
            self.top_row = row_of - visible_rows + 1
        out = []
        for r in range(self.top_row, min(n_rows, self.top_row +
                                         visible_rows)):
            blocks = []
            for c in range(cols):
                i = r * cols + c
                if i >= len(self.items):
                    break
                blocks.append(self._card(self.items[i], card_w,
                                         self.focused and i == self.index))
                for k in range(self.card_height):
                    self.hot(len(out) + k, lambda i=i: self._click(i),
                             c * (card_w + 1), c * (card_w + 1) + card_w)
            out.extend(join_columns(blocks, [card_w] * len(blocks)))
        if not self.items:
            out.append(self.paint('Sin elementos', self.theme.muted))
        return out


class ValidationSummary(_Themed):
    """The list of errors of a form: ``{field: message}``."""

    role = 'alert'

    def a11y_name(self):
        return self.a11y_label or self.title

    def a11y_value(self):
        return '; '.join('{0}: {1}'.format(f, m)
                         for f, m in self.errors.items())

    def __init__(self, errors=None, title='Revisa estos campos', **kwargs):
        super(ValidationSummary, self).__init__(**kwargs)
        self.errors = dict(errors or {})
        self.title = title

    def draw(self, width, height):
        if not self.errors:
            return []
        lines = [self.paint('✖ ' + self.title, 'bold ' + self.theme.error)]
        for field, message in self.errors.items():
            lines.append('  • {0}: {1}'.format(field, message))
        return frame([' ' + l for l in lines], width, None, self.theme.error,
                     self.paint)


class Form(_Themed):
    """
    Fields with labels, help and validation, laid out in ``columns``, with
    submit / cancel buttons. ``fields``: inputs, section titles (strings) or
    tuples of inputs for one row. Enter in a one-line field moves to the
    next; Ctrl-S (or the submit button) validates and calls
    ``on_submit(values)``; Escape calls ``on_cancel()``. ``values()`` is the
    ``{name: value}`` dict; ``errors`` the last validation.
    """

    role = 'form'

    def a11y_name(self):
        return self.a11y_label or self.title or ''

    def a11y_value(self):
        if self.errors:
            return '{0} errores'.format(len(self.errors))
        return ''

    def a11y_state(self):
        return ['invalid'] if self.errors else []

    def __init__(self, fields, on_submit=None, on_cancel=None,
                 submit_label='Guardar', cancel_label='Cancelar', columns=1,
                 title=None, summary=True, **kwargs):
        super(Form, self).__init__(**kwargs)
        self.rows = []
        for item in fields:
            if isinstance(item, (tuple, list)):
                self.rows.append(list(item))
            else:
                self.rows.append([item])
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.columns = max(1, int(columns))
        self.title = title
        self.summary = bool(summary)
        self.errors = {}
        self.submitted = None
        colors = kwargs.get('use_colors')
        self.submit_button = Button(submit_label, self.submit, kind='primary',
                                    shortcut=None, theme=self.theme,
                                    use_colors=colors)
        self.cancel_button = Button(cancel_label, self.cancel,
                                    theme=self.theme, use_colors=colors) \
            if on_cancel is not None or cancel_label else None
        for field in self.fields():
            if isinstance(field, TextInput) and field.on_submit is None:
                field.on_submit = self._next_from(field)

    def _next_from(self, field):
        def advance(value):
            if self.app is not None:
                self.app.focus_next()
        return advance

    def fields(self):
        return [f for row in self.rows for f in row if isinstance(f, Input)]

    def children(self):
        kids = [f for row in self.rows for f in row if not isinstance(f, str)]
        # Same order as drawn: Tab walks the buttons left to right.
        if self.cancel_button is not None:
            kids.append(self.cancel_button)
        kids.append(self.submit_button)
        return kids

    def natural_width(self):
        return 60 if self.columns == 1 else 90

    def values(self):
        return {f.name: f.value for f in self.fields() if f.name}

    def validate(self):
        self.errors = {}
        for f in self.fields():
            error = f.validate()
            if error:
                self.errors[f.label or f.name] = error
        return self.errors

    def submit(self):
        if self.validate():
            bad = next((f for f in self.fields() if f.error), None)
            if bad is not None and self.app is not None:
                self.app.focus(bad)
            self.refresh()
            return True
        self.submitted = self.values()
        if self.on_submit is not None:
            self.on_submit(self.submitted)
        self.refresh()
        return True

    def cancel(self):
        if self.on_cancel is not None:
            self.on_cancel()
        return True

    def handle_key(self, key):
        k = str(key)
        if k == 'ctrl+s':
            return self.submit()
        if k == 'escape' and self.on_cancel is not None:
            return self.cancel()
        return super(Form, self).handle_key(key)

    def draw(self, width, height):
        out = []
        if self.title:
            out.append(self.paint(self.title, 'bold ' + self.theme.accent))
            out.append('')
        if self.summary and self.errors:
            out.extend(ValidationSummary(self.errors, theme=self.theme,
                                         use_colors=self.use_colors)
                       .render(width=width).split('\n'))
        pending = []

        def flush():
            if not pending:
                return
            n = len(pending)
            each = (width - 2 * (n - 1)) // n
            blocks = [p.render(width=each).split('\n') for p in pending]
            out.extend(join_columns(blocks, [each] * n, gap=2))
            out.append('')
            del pending[:]
        for row in self.rows:
            if len(row) == 1 and isinstance(row[0], str):
                flush()
                out.append(self.paint(row[0], 'bold'))
                out.append(self.paint('─' * width, self.theme.border))
                continue
            if len(row) > 1:
                flush()
                pending.extend(row)
                flush()
                continue
            pending.append(row[0])
            if len(pending) >= self.columns:
                flush()
        flush()
        buttons = self.submit_button.render(
            width=self.submit_button.natural_width())
        if self.cancel_button is not None:
            buttons = self.cancel_button.render(
                width=self.cancel_button.natural_width()) + '  ' + buttons
        out.append(_fx.fit_line(buttons, width, 'r'))
        return out


class LoginForm(Form):
    """
    User and password, a "remember me" box and an Enter button.
    ``on_login(user, password, remember)`` returns True, or an error message
    shown above the fields.
    """

    def __init__(self, on_login=None, title='Iniciar sesión',
                 user_label='Usuario', **kwargs):
        colors = kwargs.get('use_colors')
        theme = kwargs.get('theme')
        self.user = TextInput(user_label, name='user', required=True,
                              theme=theme, use_colors=colors)
        self.password = PasswordInput('Contraseña', name='password',
                                      required=True, theme=theme,
                                      use_colors=colors)
        self.remember = Checkbox('Recordarme', name='remember', theme=theme,
                                 use_colors=colors)
        self.on_login = on_login
        self.message = None
        self.logged_in = False
        super(LoginForm, self).__init__(
            [self.user, self.password, self.remember],
            on_submit=self._login, submit_label='Entrar', cancel_label=None,
            title=title, summary=False, **kwargs)
        self.password.on_submit = lambda value: self.submit()

    def _login(self, values):
        result = True
        if self.on_login is not None:
            result = self.on_login(values['user'], values['password'],
                                   values['remember'])
        if result is True:
            self.logged_in = True
            self.message = None
        else:
            self.message = str(result or 'Usuario o contraseña incorrectos')
            self.password.value = ''

    def natural_width(self):
        return 44

    def draw(self, width, height):
        out = super(LoginForm, self).draw(width, height)
        if self.message:
            out.insert(2 if self.title else 0,
                       self.paint('✖ ' + self.message, self.theme.error))
        return out


class FilePreview(_Themed):
    """
    A file's name, size, date and -- for text -- its first lines, with code
    highlighting by extension. Images, PDFs and other binaries show their
    details only (a terminal cannot draw them portably).
    """

    LANGUAGES = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                 '.sql': 'sql', '.sh': 'bash', '.json': 'json'}

    role = 'document'

    def a11y_name(self):
        return self.a11y_label or os.path.basename(self.path)

    def __init__(self, path, max_lines=20, **kwargs):
        super(FilePreview, self).__init__(**kwargs)
        self.path = path
        self.max_lines = max_lines

    def natural_width(self):
        return 70

    def _content(self):
        try:
            with open(self.path, 'rb') as handle:
                head = handle.read(64 * 1024)
        except OSError as error:
            return None, str(error)
        if b'\x00' in head:
            return None, 'Vista previa no disponible (archivo binario)'
        try:
            return head.decode('utf-8'), None
        except UnicodeDecodeError:
            return head.decode('latin-1'), None

    def draw(self, width, height):
        from .display import Code, human_size
        name = os.path.basename(self.path)
        try:
            stat = os.stat(self.path)
            meta = '{0} · {1:%Y-%m-%d %H:%M}'.format(
                human_size(stat.st_size),
                _dt.datetime.fromtimestamp(stat.st_mtime))
        except OSError:
            meta = 'no encontrado'
        out = [self.paint(name, 'bold') + '  ' + self.paint(meta,
                                                            self.theme.muted)]
        text, problem = self._content()
        if problem:
            out.append(self.paint(problem, self.theme.muted))
            return out
        lines = text.split('\n')[:self.max_lines]
        ext = os.path.splitext(name)[1].lower()
        if ext in ('.md', '.markdown'):
            from .display import MarkdownView
            body = MarkdownView('\n'.join(lines), theme=self.theme,
                                use_colors=self.use_colors)
        else:
            body = Code('\n'.join(lines), self.LANGUAGES.get(ext),
                        theme=self.theme, use_colors=self.use_colors)
        out.extend(body.render(width=width).split('\n'))
        return out
