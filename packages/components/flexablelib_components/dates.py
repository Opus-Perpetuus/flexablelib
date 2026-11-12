"""
Dates and times: a month calendar, date / time / date-time inputs, week,
month, year and weekday pickers, date ranges with presets, and a timer.
"""

import calendar as _calendar
import datetime as _dt
import time

from flexablelib import _frames as _fx

from flexablelib_tui import Key

from .base import Input, _Themed, join_columns

_ENTER = Key('enter')

__all__ = ['Calendar', 'DateInput', 'TimeInput', 'DateTimeInput',
           'WeekInput', 'MonthInput', 'YearInput', 'WeekdayInput',
           'DateRangeInput', 'Timer', 'LOCALES']

LOCALES = {
    'es': {
        'months': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre',
                   'Diciembre'],
        'days': ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'],
        'weekdays': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes',
                     'Sábado', 'Domingo'],
        'today': 'Hoy', 'week': 'Sem',
    },
    'en': {
        'months': ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November',
                   'December'],
        'days': ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
        'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                     'Saturday', 'Sunday'],
        'today': 'Today', 'week': 'Wk',
    },
}


def _add_months(day, months):
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    last = _calendar.monthrange(year, month)[1]
    return day.replace(year=year, month=month, day=min(day.day, last))


def _as_date(value):
    if value is None or value == '':
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return _dt.date.fromisoformat(str(value)[:10])


class Calendar(_Themed):
    """
    A month grid. Arrows move by day and week, PgUp/PgDn by month,
    Ctrl-PgUp/PgDn by year, ``t`` jumps to today, Enter calls
    ``on_select(date)``. ``highlight(date) -> spec`` colours days; ``range``
    ``(start, end)`` shades a span; ``mode='week'`` selects whole weeks.
    """

    focusable = True
    role = 'calendar'
    #: A click on a day chooses it at once (inside a date input); otherwise
    #: the first click moves the cursor there and a second one chooses it.
    single_click = False

    def a11y_value(self):
        day = self.cursor
        text = '{0} {1} de {2} de {3}'.format(
            self.names['weekdays'][day.weekday()], day.day,
            self.names['months'][day.month - 1].lower(), day.year)
        if day == self.today:
            text += ', hoy'
        return text

    def a11y_state(self):
        return ['selected'] if self.selected == self.cursor else []

    def _click(self, day):
        if not self._enabled_day(day):
            return True
        again = day == self.cursor
        self.cursor = day
        if again or self.single_click:
            return self.on_key(_ENTER)
        return True

    def _enabled_day(self, day):
        return not ((self.minimum and day < self.minimum) or
                    (self.maximum and day > self.maximum))

    def __init__(self, value=None, on_select=None, locale='es',
                 minimum=None, maximum=None, mode='day', today=None,
                 **kwargs):
        super(Calendar, self).__init__(**kwargs)
        self.today = today or _dt.date.today()
        self.cursor = _as_date(value) or self.today
        self.selected = _as_date(value)
        self.on_select = on_select
        self.names = LOCALES.get(locale, LOCALES['es'])
        self.minimum = _as_date(minimum)
        self.maximum = _as_date(maximum)
        self.mode = mode
        self.range = None
        self.highlight = None

    def natural_width(self):
        return 22 + (4 if self.mode == 'week' else 0)

    def _clamp(self, day):
        if self.minimum and day < self.minimum:
            return self.minimum
        if self.maximum and day > self.maximum:
            return self.maximum
        return day

    def move(self, days=0, months=0):
        day = self.cursor + _dt.timedelta(days=days)
        if months:
            day = _add_months(day, months)
        self.cursor = self._clamp(day)
        self.refresh()
        return True

    def on_key(self, key):
        k = str(key)
        steps = {'left': -1, 'right': 1, 'up': -7, 'down': 7}
        if k in steps:
            return self.move(days=steps[k])
        months = {'pageup': -1, 'pagedown': 1, 'ctrl+pageup': -12,
                  'ctrl+pagedown': 12}
        if k in months:
            return self.move(months=months[k])
        if k == 'home':
            return self.move(days=1 - self.cursor.day)
        if k == 'end':
            last = _calendar.monthrange(self.cursor.year,
                                        self.cursor.month)[1]
            return self.move(days=last - self.cursor.day)
        if k == 't':
            self.cursor = self._clamp(self.today)
            self.refresh()
            return True
        if k in ('enter', 'space'):
            day = self.cursor
            if self.mode == 'week':
                day = day - _dt.timedelta(days=day.weekday())
            self.selected = day
            if self.on_select is not None:
                self.on_select(day)
            self.refresh()
            return True
        return False

    def _in_range(self, day):
        if self.range and self.range[0]:
            start, end = self.range
            end = end or start
            if start > end:
                start, end = end, start
            return start <= day <= end
        if self.mode == 'week' and self.selected:
            return self.selected <= day < self.selected + \
                _dt.timedelta(days=7)
        return False

    def draw(self, width, height):
        year, month = self.cursor.year, self.cursor.month
        title = '{0} {1}'.format(self.names['months'][month - 1], year)
        week_col = self.mode == 'week'
        grid_w = 20 + (4 if week_col else 0)
        out = [_fx.fit_line(self.paint(title, self.theme.title),
                            grid_w, 'c')]
        head = ' '.join(self.names['days'])
        if week_col:
            head = _fx.fit_line(self.names['week'], 3) + ' ' + head
        out.append(self.paint(head, self.theme.muted))
        cursor_week = self.cursor.isocalendar()[1]
        for week in _calendar.Calendar(0).monthdatescalendar(year, month):
            cells = []
            if week_col:
                num = week[0].isocalendar()[1]
                cells.append(self.paint('{0:>3}'.format(num),
                                        self.theme.accent if num ==
                                        cursor_week and self.focused
                                        else self.theme.muted))
            row = ''
            x = 3 if week_col else 0
            for k, day in enumerate(week):
                text = '{0:>2}'.format(day.day)
                sep = ' ' if k or week_col else ''
                spec = None
                if day.month != month:
                    spec = self.theme.muted
                if self.highlight is not None:
                    spec = self.highlight(day) or spec
                if self._in_range(day):
                    spec = 'reverse' if not self.focused else \
                        self.theme.selection
                if day == self.selected and self.mode == 'day':
                    spec = 'bold ' + (self.theme.accent or '') + ' reverse'
                if day == self.today:
                    spec = (spec or '') + ' underline'
                if day == self.cursor and self.focused:
                    if self._active():
                        spec = self.theme.selection
                        if self._marked():
                            spec += ' bold underline'
                            if k or week_col:
                                sep = '▸'
                    elif k or week_col:
                        sep = '>'
                if (self.minimum and day < self.minimum) or \
                        (self.maximum and day > self.maximum):
                    spec = 'dim'
                self.hot(len(out), lambda day=day: self._click(day), x,
                         x + len(sep) + 2)
                x += len(sep) + 2
                row += sep + self.paint(text, spec.strip() if spec else None)
            out.append(''.join(cells) + row)
        return out


class _Picker(Input):
    """An input that opens an inline picker below its value."""

    role = 'combobox'

    def a11y_value(self):
        if self.open:
            picker = self.picker()
            if picker is not None:
                return picker.a11y_value()
        return self.shown()

    def a11y_state(self):
        return ['expanded' if self.open else 'collapsed'] + \
            Input.a11y_state(self)

    def _toggle(self):
        if self.open:
            self.open = False
        else:
            self.open = True
            self.sync()
        return True

    def __init__(self, label=None, value=None, **kwargs):
        self.open = False
        super(_Picker, self).__init__(label=label, value=value, **kwargs)

    def on_blur(self):
        self.open = False

    def shown(self):   # pragma: no cover - abstract
        return ''

    def picker(self):   # pragma: no cover - abstract
        return None

    def picker_key(self, key):
        return self.picker().handle_key(key)

    def on_key(self, key):
        k = str(key)
        if not self.open:
            if k in ('enter', 'space', 'alt+down'):
                self.open = True
                self.sync()
                self.refresh()
                return True
            if k == 'delete' and not self.required:
                self.set_value(None)
                return True
            return self.closed_key(key)
        if k == 'escape':
            self.open = False
            self.refresh()
            return True
        if k in ('tab', 'shift+tab'):
            return False
        self.picker_key(key)
        self.refresh()
        return True

    def closed_key(self, key):
        return False

    def sync(self):
        pass

    def chosen(self, value):
        self.set_value(value)
        self.open = False

    def control(self, width, height):
        shown = self.shown()
        body = shown if shown else self.paint('—', self.theme.muted)
        icon = self.paint('▾' if not self.open else '▴',
                          self.theme.accent if self.focused else
                          self.theme.muted)
        out = [self.marker() + ' ' + _fx.fit_line(body, max(1, width - 4)) +
               ' ' + icon]
        self.hot(0, self._toggle)
        if self.open:
            picker = self.picker()
            picker.focused = True
            picker.use_colors = self.use_colors
            out.extend('  ' + line for line in
                       picker.render(width=max(1, width - 2)).split('\n'))
        return out


class DateInput(_Picker):
    """
    A date. Enter opens a calendar; with it closed, ``+`` / ``-`` move a day
    and ``t`` sets today. ``format`` is the ``strftime`` pattern shown.
    """

    def __init__(self, label=None, value=None, format='%Y-%m-%d',
                 locale='es', minimum=None, maximum=None, today=None,
                 **kwargs):
        self.format = format
        self.calendar = Calendar(value, locale=locale, minimum=minimum,
                                 maximum=maximum, today=today,
                                 theme=kwargs.get('theme'))
        self.calendar.on_select = self.chosen
        self.calendar.single_click = True
        super(DateInput, self).__init__(label=label, value=value, **kwargs)

    def coerce(self, value):
        return _as_date(value)

    def shown(self):
        return self._value.strftime(self.format) if self._value else ''

    def picker(self):
        return self.calendar

    def sync(self):
        if self._value:
            self.calendar.cursor = self._value
        self.calendar.selected = self._value

    def closed_key(self, key):
        k = str(key)
        if k in ('+', '-'):
            base = self._value or self.calendar.today
            self.set_value(base + _dt.timedelta(days=1 if k == '+' else -1))
            return True
        if k == 't':
            self.set_value(self.calendar.today)
            return True
        return False


class TimeInput(Input):
    """
    ``HH:MM`` (``seconds=True``: ``HH:MM:SS``). Left/Right pick the part,
    Up/Down change it (by ``step`` minutes for minutes), digits type it.
    """

    def __init__(self, label=None, value=None, seconds=False, step=1,
                 **kwargs):
        self.seconds = bool(seconds)
        self.step = max(1, int(step))
        self.part = 0
        self._typed = ''
        super(TimeInput, self).__init__(label=label, value=value, **kwargs)

    def coerce(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, _dt.datetime):
            return value.time().replace(microsecond=0)
        if isinstance(value, _dt.time):
            return value.replace(microsecond=0)
        parts = [int(p) for p in str(value).split(':')]
        while len(parts) < 3:
            parts.append(0)
        return _dt.time(*parts[:3])

    def _parts(self):
        return 3 if self.seconds else 2

    role = 'spinbutton'

    def a11y_value(self):
        t = self._value
        if t is None:
            return ''
        names = ['hora', 'minutos', 'segundos']
        text = t.strftime('%H:%M:%S' if self.seconds else '%H:%M')
        return text + ', editando ' + names[self.part]

    def _pick_part(self, i):
        self.part = i
        self._typed = ''
        return True

    def _change(self, delta, part=None):
        t = self._value or _dt.time(0, 0)
        part = self.part if part is None else part
        h, m, s = t.hour, t.minute, t.second
        if part == 0:
            h = (h + delta) % 24
        elif part == 1:
            m = (m + delta * self.step) % 60
        else:
            s = (s + delta) % 60
        self.set_value(_dt.time(h, m, s))

    def on_key(self, key):
        k = str(key)
        if k in ('left', 'right'):
            self.part = (self.part + (1 if k == 'right' else -1)) % \
                self._parts()
            self._typed = ''
        elif k in ('up', 'down'):
            self._change(1 if k == 'up' else -1)
        elif len(k) == 1 and k.isdigit():
            self._typed = (self._typed + k)[-2:]
            limit = 24 if self.part == 0 else 60
            number = int(self._typed)
            if number >= limit:
                number = int(k)
                self._typed = k
            t = self._value or _dt.time(0, 0)
            values = [t.hour, t.minute, t.second]
            values[self.part] = number
            self.set_value(_dt.time(*values))
            if len(self._typed) == 2 and self.part + 1 < self._parts():
                self.part += 1
                self._typed = ''
        elif k == 'delete' and not self.required:
            self.set_value(None)
        elif k == 'enter':
            return self.submit()
        else:
            return False
        self.refresh()
        return True

    def control(self, width, height):
        t = self._value
        values = ['--', '--', '--'] if t is None else \
            ['{0:02d}'.format(t.hour), '{0:02d}'.format(t.minute),
             '{0:02d}'.format(t.second)]
        parts = []
        for i in range(self._parts()):
            text = values[i]
            if self.focused and i == self.part:
                text = self.paint(text, self.theme.selection + (
                    ' underline' if self._marked() else '')) if \
                    self._active() else '[' + text + ']'
            parts.append(text)
        self.hot_parts(0, parts, 1, 2, [(lambda i=i: self._pick_part(i))
                                        for i in range(len(parts))])
        return [self.marker() + ' ' + ':'.join(parts)]


class DateTimeInput(Input):
    """A date and a time side by side; the value is a ``datetime``."""

    focusable = False
    role = 'group'

    def a11y_value(self):
        value = self.value
        return '' if value is None else value.isoformat(' ')

    def __init__(self, label=None, value=None, seconds=False, locale='es',
                 today=None, **kwargs):
        common = {'theme': kwargs.get('theme'),
                  'use_colors': kwargs.get('use_colors')}
        self.date = DateInput(locale=locale, today=today, **common)
        self.time = TimeInput(seconds=seconds, **common)
        super(DateTimeInput, self).__init__(label=label, value=value,
                                            **kwargs)

    def children(self):
        return [self.date, self.time]

    @property
    def value(self):
        if self.date.value is None:
            return None
        return _dt.datetime.combine(self.date.value,
                                    self.time.value or _dt.time(0, 0))

    @value.setter
    def value(self, new):
        if new is None:
            return
        if isinstance(new, str):
            new = _dt.datetime.fromisoformat(new)
        self.date.value = new
        self.time.value = new if isinstance(new, _dt.datetime) else None

    def is_empty(self):
        return self.date.value is None

    def control(self, width, height):
        left_w = max(14, width // 2)
        left = self.date.render(width=left_w).split('\n')
        right = self.time.render(width=max(1, width - left_w - 1)).split('\n')
        return join_columns([left, right], [left_w, max(1, width - left_w -
                                                         1)])


class WeekInput(_Picker):
    """A week; the value is its Monday. Shown as ``2026-W46 · 09/11–15/11``."""

    def __init__(self, label=None, value=None, locale='es', today=None,
                 **kwargs):
        self.calendar = Calendar(value, locale=locale, mode='week',
                                 today=today, theme=kwargs.get('theme'))
        self.calendar.on_select = self.chosen
        self.calendar.single_click = True
        super(WeekInput, self).__init__(label=label, value=value, **kwargs)

    def coerce(self, value):
        day = _as_date(value)
        return None if day is None else day - _dt.timedelta(
            days=day.weekday())

    def shown(self):
        if not self._value:
            return ''
        year, week, _ = self._value.isocalendar()
        end = self._value + _dt.timedelta(days=6)
        return '{0}-W{1:02d} · {2:%d/%m}–{3:%d/%m}'.format(year, week,
                                                          self._value, end)

    def picker(self):
        return self.calendar

    def sync(self):
        if self._value:
            self.calendar.cursor = self._value
        self.calendar.selected = self._value


class _GridPicker(_Themed):
    """A grid of labelled choices (months, years)."""

    focusable = True
    role = 'grid'

    def a11y_value(self):
        if not self.labels:
            return ''
        return '{0} ({1} de {2})'.format(self.labels[self.index],
                                         self.index + 1, len(self.labels))

    def _click(self, i):
        self.index = i
        if self.on_select:
            self.on_select(i)
        return True

    def __init__(self, labels, columns, index=0, title='', **kwargs):
        super(_GridPicker, self).__init__(**kwargs)
        self.labels = labels
        self.columns = columns
        self.index = index
        self.title = title
        self.on_select = None
        self.on_page = None

    def on_key(self, key):
        k = str(key)
        moves = {'left': -1, 'right': 1, 'up': -self.columns,
                 'down': self.columns}
        if k in moves:
            self.index = max(0, min(len(self.labels) - 1,
                                    self.index + moves[k]))
            return True
        if k in ('pageup', 'pagedown') and self.on_page:
            self.on_page(-1 if k == 'pageup' else 1)
            return True
        if k in ('enter', 'space') and self.on_select:
            self.on_select(self.index)
            return True
        return False

    def draw(self, width, height):
        cell = max(len(label) for label in self.labels) + 2
        out = [self.paint(self.title, self.theme.title)] if self.title else []
        for r in range(0, len(self.labels), self.columns):
            cells = []
            for i in range(r, min(len(self.labels), r + self.columns)):
                text = _fx.fit_line(self.labels[i], cell, 'c')
                self.hot(len(out), lambda i=i: self._click(i),
                         (i - r) * cell, (i - r + 1) * cell)
                if i == self.index and self.focused:
                    if self._marked():
                        text = '[' + text[1:-1] + ']'
                    text = self.paint(text, self.theme.selection) if \
                        self._active() else '[' + text[1:-1] + ']'
                cells.append(text)
            out.append(''.join(cells))
        return out


class MonthInput(_Picker):
    """A month (the value is its first day); PgUp/PgDn change the year."""

    def __init__(self, label=None, value=None, locale='es', today=None,
                 **kwargs):
        self.names = LOCALES.get(locale, LOCALES['es'])
        self.today = today or _dt.date.today()
        self.year = (_as_date(value) or self.today).year
        self.grid = _GridPicker([m[:3] for m in self.names['months']], 4,
                                theme=kwargs.get('theme'))
        self.grid.on_select = lambda i: self.chosen(_dt.date(self.year,
                                                             i + 1, 1))
        self.grid.on_page = self._page
        super(MonthInput, self).__init__(label=label, value=value, **kwargs)

    def _page(self, step):
        self.year += step
        self.grid.title = str(self.year)

    def coerce(self, value):
        day = _as_date(value)
        return None if day is None else day.replace(day=1)

    def shown(self):
        if not self._value:
            return ''
        return '{0} {1}'.format(self.names['months'][self._value.month - 1],
                                self._value.year)

    def sync(self):
        base = self._value or self.today
        self.year = base.year
        self.grid.index = base.month - 1
        self.grid.title = str(self.year)

    def picker(self):
        return self.grid


class YearInput(_Picker):
    """A year (the value is January 1st, or an ``int`` with
    ``as_int=True``); the picker shows twelve years, PgUp/PgDn page."""

    def __init__(self, label=None, value=None, as_int=False, today=None,
                 **kwargs):
        self.as_int = bool(as_int)
        self.today = today or _dt.date.today()
        self.first = self.today.year - 5
        self.grid = _GridPicker([], 4, theme=kwargs.get('theme'))
        self.grid.on_select = lambda i: self.chosen(self.first + i)
        self.grid.on_page = self._page
        super(YearInput, self).__init__(label=label, value=value, **kwargs)
        self._labels()

    def _labels(self):
        self.grid.labels = [str(self.first + i) for i in range(12)]

    def _page(self, step):
        self.first += 12 * step
        self._labels()

    def coerce(self, value):
        if value is None or value == '':
            return None
        year = value if isinstance(value, int) else _as_date(value).year
        return year if self.as_int else _dt.date(year, 1, 1)

    def _year(self):
        if self._value is None:
            return None
        return self._value if self.as_int else self._value.year

    def shown(self):
        year = self._year()
        return '' if year is None else str(year)

    def sync(self):
        year = self._year() or self.today.year
        self.first = year - 5
        self._labels()
        self.grid.index = 5

    def picker(self):
        return self.grid


class WeekdayInput(Input):
    """A day of the week (0 = Monday ... 6 = Sunday) as a row of buttons."""

    def __init__(self, label=None, value=None, locale='es', short=True,
                 **kwargs):
        names = LOCALES.get(locale, LOCALES['es'])
        self.names = names['days'] if short else names['weekdays']
        super(WeekdayInput, self).__init__(label=label, value=value, **kwargs)

    def coerce(self, value):
        return None if value is None else int(value) % 7

    role = 'radiogroup'

    def a11y_value(self):
        return '' if self._value is None else self.names[self._value]

    def on_key(self, key):
        k = str(key)
        if k in ('left', 'right'):
            current = self._value if self._value is not None else -1
            self.set_value((current + (1 if k == 'right' else -1)) % 7)
            return True
        if len(k) == 1 and k in '1234567':
            self.set_value(int(k) - 1)
            return True
        return False

    def control(self, width, height):
        parts = []
        for i, name in enumerate(self.names):
            text = ' {0} '.format(name)
            if i == self._value:
                if self._marked():
                    text = '[' + name + ']'
                text = self.paint(text, self.theme.selection if self.focused
                                  else 'reverse') if self._active() else \
                    '[' + name + ']'
            parts.append(text)
        self.hot_parts(0, parts, 0, 2, [(lambda i=i: self.set_value(i))
                                        for i in range(len(parts))])
        return [self.marker() + ' ' + ''.join(parts)]


class DateRangeInput(_Picker):
    """
    A span of dates: in the picker, Enter marks the start then the end, or
    pick a preset on the left (Up/Down there, Right to the calendar). The
    value is ``(start, end)``.
    """

    PRESETS = ['Hoy', 'Ayer', 'Últimos 7 días', 'Últimos 30 días',
               'Este mes', 'Mes pasado', 'Este año']

    def __init__(self, label=None, value=None, locale='es', today=None,
                 **kwargs):
        self.today = today or _dt.date.today()
        self.calendar = Calendar(locale=locale, today=self.today,
                                 theme=kwargs.get('theme'))
        self.calendar.on_select = self._mark
        self.calendar.single_click = True
        self.calendar.range = (None, None)
        self.preset = 0
        self.in_presets = True
        self._start = None
        super(DateRangeInput, self).__init__(label=label, value=value,
                                             **kwargs)

    def coerce(self, value):
        if not value:
            return None
        start, end = (_as_date(v) for v in value)
        if start and end and start > end:
            start, end = end, start
        return (start, end)

    def preset_range(self, index):
        t = self.today
        if index == 0:
            return (t, t)
        if index == 1:
            y = t - _dt.timedelta(days=1)
            return (y, y)
        if index == 2:
            return (t - _dt.timedelta(days=6), t)
        if index == 3:
            return (t - _dt.timedelta(days=29), t)
        if index == 4:
            return (t.replace(day=1), t)
        if index == 5:
            last = t.replace(day=1) - _dt.timedelta(days=1)
            return (last.replace(day=1), last)
        return (t.replace(month=1, day=1), t)

    def _mark(self, day):
        if self._start is None:
            self._start = day
            self.calendar.range = (day, None)
        else:
            self.chosen((self._start, day))
            self._start = None

    def sync(self):
        self._start = None
        self.calendar.range = self._value or (None, None)
        if self._value:
            self.calendar.cursor = self._value[0]

    def picker(self):
        return self.calendar

    def picker_key(self, key):
        k = str(key)
        if self.in_presets:
            if k in ('up', 'down'):
                self.preset = (self.preset + (1 if k == 'down' else -1)) % \
                    len(self.PRESETS)
            elif k == 'enter':
                self.chosen(self.preset_range(self.preset))
            elif k == 'right':
                self.in_presets = False
            return True
        if k == 'left' and self.calendar.cursor.weekday() == 0:
            self.in_presets = True
            return True
        return self.calendar.handle_key(key)

    def shown(self):
        if not self._value:
            return ''
        start, end = self._value
        return '{0:%Y-%m-%d} → {1:%Y-%m-%d}'.format(start, end)

    def _preset_click(self, i):
        self.preset = i
        self.in_presets = True
        self.chosen(self.preset_range(i))
        return True

    def a11y_value(self):
        if self.open and self.in_presets:
            return self.PRESETS[self.preset]
        return _Picker.a11y_value(self)

    def control(self, width, height):
        out = super(DateRangeInput, self).control(width, height)
        if not self.open:
            return out
        out = out[:1]
        self.calendar.focused = not self.in_presets
        cal = self.calendar.render(width=22).split('\n')
        presets = []
        for i, name in enumerate(self.PRESETS):
            self.hot(1 + i, lambda i=i: self._preset_click(i), 2, 19)
            text = _fx.fit_line(' ' + name, 17)
            if i == self.preset and self.in_presets:
                text = self.mark_current(text, self.theme.selection)
            presets.append(text)
        out.extend('  ' + line for line in
                   join_columns([presets, cal], [17, 22], gap=2))
        if self._start is not None:
            out.append('  ' + self.paint('Inicio: {0:%Y-%m-%d} · elige el fin'
                                         .format(self._start),
                                         self.theme.muted))
        return out


class Timer(_Themed):
    """
    Elapsed time since ``start`` (until ``end``, or now): ``01:23:45``.
    ``interactive=True`` makes it a stopwatch: Space starts and stops, ``r``
    resets. ``clock`` returns seconds (``time.monotonic`` by default) and is
    only used by the stopwatch; ``start`` / ``end`` may be datetimes.
    """

    role = 'timer'

    def a11y_value(self):
        text = self.text()
        if self.interactive:
            text += ', ' + ('en marcha' if self.running else 'detenido')
        return text

    def on_mouse(self, event):
        if self.interactive and event.action == 'press' and \
                event.button == 0:
            return self.toggle()
        return False

    def __init__(self, start=None, end=None, interactive=False, label=None,
                 clock=time.monotonic, now=None, **kwargs):
        super(Timer, self).__init__(**kwargs)
        self.start = start
        self.end = end
        self.interactive = bool(interactive)
        self.focusable = self.interactive
        self.label = label
        self.clock = clock
        self.now = now or _dt.datetime.now
        self._accum = 0.0
        self._since = None

    @property
    def running(self):
        if self.interactive:
            return self._since is not None
        return self.start is not None and self.end is None

    def elapsed(self):
        """Seconds elapsed."""
        if self.interactive:
            extra = self.clock() - self._since if self._since is not None \
                else 0.0
            return self._accum + extra
        if self.start is None:
            return 0.0
        end = self.end or self.now()
        return max(0.0, (end - self.start).total_seconds())

    def toggle(self):
        if self._since is None:
            self._since = self.clock()
        else:
            self._accum += self.clock() - self._since
            self._since = None
        self.refresh()
        return True

    def reset(self):
        self._accum = 0.0
        self._since = self.clock() if self._since is not None else None
        self.refresh()
        return True

    def text(self):
        total = int(self.elapsed())
        hours, rest = divmod(total, 3600)
        minutes, seconds = divmod(rest, 60)
        if hours >= 24:
            days, hours = divmod(hours, 24)
            return '{0}d {1:02d}:{2:02d}:{3:02d}'.format(days, hours, minutes,
                                                        seconds)
        return '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)

    def natural_width(self):
        return len(self.text()) + 2 + len(self.label or '') + 1

    def on_key(self, key):
        if not self.interactive:
            return False
        k = str(key)
        if k in ('space', 'enter'):
            return self.toggle()
        if k == 'r':
            return self.reset()
        return False

    def draw(self, width, height):
        icon = '⏱ ' if self._active() else ''
        spec = self.theme.success if self.running else self.theme.muted
        text = icon + self.paint(self.text(), 'bold ' + spec)
        if self.label:
            text = self.label + ' ' + text
        if self.interactive and self.focused:
            text += self.paint('  espacio: ' + ('pausa' if self.running
                                                 else 'iniciar') + ' · r',
                               self.theme.muted)
        return [text]
