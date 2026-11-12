"""
Display components: badges, tags, statuses, alerts, links, breadcrumbs,
empty and error states, spinners and skeletons, code with highlighting,
Markdown and HTML views, detail lists, timelines, steppers, comments,
attachments, KPI stats and line charts.
"""

import html.parser
import math
import re

from flexablelib import _frames as _fx
from flexablelib.text_width import wrap_to_width

from .base import _Themed, frame

__all__ = ['Badge', 'Tag', 'StatusBadge', 'Alert', 'Link', 'Breadcrumbs',
           'EmptyState', 'ErrorPanel', 'Spinner', 'Skeleton', 'Code',
           'highlight', 'MarkdownView', 'HtmlView', 'DetailView', 'Timeline',
           'Stepper', 'CommentList', 'AttachmentList', 'Stat', 'LineChart',
           'human_size']


def _wrap(text, width):
    lines = []
    for paragraph in str(text).split('\n'):
        lines.extend(wrap_to_width(paragraph, max(1, width)) or [''])
    return lines


class Badge(_Themed):
    """A short label on a coloured background: ``kind`` is a theme kind
    (``'info'``, ``'success'``, ``'warning'``, ``'error'``) or ``color``."""

    def __init__(self, text, kind='info', color=None, **kwargs):
        super(Badge, self).__init__(**kwargs)
        self.text = str(text)
        self.kind = kind
        self.color = color

    def natural_width(self):
        return _fx.visible_width(self.text) + 2

    def inline(self):
        if not self._active():
            return '[' + self.text + ']'
        color = self.color or self.theme.kind(self.kind)
        return self.paint(' ' + self.text + ' ', 'bold black on ' + color)

    def draw(self, width, height):
        return [self.inline()]


class Tag(Badge):
    """A tag in a colour; ``(etiqueta)`` without colours."""

    def inline(self):
        color = self.color or self.theme.kind(self.kind)
        if not self._active():
            return '(' + self.text + ')'
        return self.paint('▐', color) + self.paint(self.text,
                                                   'black on ' + color) + \
            self.paint('▌', color)


class StatusBadge(Badge):
    """
    A status from ``options`` -- ``{value: (label, kind_or_colour)}`` -- with
    a coloured dot: ``● Pagado``.
    """

    def __init__(self, value, options=None, **kwargs):
        self.options = options or {}
        self.value = value
        label, kind = self.options.get(value, (str(value), 'info'))
        super(StatusBadge, self).__init__(label, kind=kind, **kwargs)

    def inline(self):
        kind = self.kind
        color = self.color or getattr(self.theme, kind, None) or kind
        dot = self.paint('●', color) if self._active() else '*'
        return dot + ' ' + self.text


class Alert(_Themed):
    """
    A message box: ``kind`` sets the icon and colour; ``title`` is optional.
    ``dismissible=True`` adds a close hint and lets Escape hide it.
    """

    ICONS = {'info': 'ℹ', 'success': '✔', 'warning': '⚠', 'error': '✖'}

    def __init__(self, message, kind='info', title=None, dismissible=False,
                 **kwargs):
        super(Alert, self).__init__(**kwargs)
        self.message = message
        self.kind = kind
        self.title = title
        self.dismissible = bool(dismissible)
        self.focusable = self.dismissible
        self.visible = True

    def natural_width(self):
        return min(80, max(_fx.visible_width(line) for line in
                           str(self.message).split('\n')) + 6)

    def on_key(self, key):
        if self.dismissible and str(key) in ('escape', 'enter', 'x'):
            self.visible = False
            self.refresh()
            return True
        return False

    def draw(self, width, height):
        if not self.visible:
            return []
        color = self.theme.kind(self.kind)
        icon = self.ICONS.get(self.kind, '•')
        inner = max(1, width - 4)
        lines = []
        if self.title:
            lines.append(self.paint(icon + ' ' + self.title, 'bold ' + color))
            lines.extend(_wrap(self.message, inner))
        else:
            body = _wrap(self.message, inner - 2)
            lines.append(self.paint(icon, 'bold ' + color) + ' ' + body[0])
            lines.extend('  ' + line for line in body[1:])
        lines = [' ' + line for line in lines]
        footer = 'esc' if self.dismissible and self.focused else None
        return frame(lines, width, None, color, self.paint, footer=footer)


class Link(_Themed):
    """
    A hyperlink. On terminals that support OSC 8 it is clickable; the URL is
    shown after the text when ``show_url=True`` or colours are off.
    """

    focusable = True

    def __init__(self, text, url=None, show_url=False, on_open=None,
                 **kwargs):
        super(Link, self).__init__(**kwargs)
        self.text = text
        self.url = url or text
        self.show_url = bool(show_url)
        self.on_open = on_open

    def natural_width(self):
        return _fx.visible_width(self.text) + (len(self.url) + 3
                                               if self.show_url else 0)

    def inline(self):
        if not self._active():
            return '{0} <{1}>'.format(self.text, self.url) \
                if self.text != self.url else self.url
        spec = 'underline ' + (self.theme.accent if self.focused else
                               self.theme.info)
        text = '\x1b]8;;{0}\x1b\\{1}\x1b]8;;\x1b\\'.format(
            self.url, self.paint(self.text, spec))
        if self.show_url:
            text += ' ' + self.paint(self.url, self.theme.muted)
        return text

    def on_key(self, key):
        if str(key) == 'enter' and self.on_open is not None:
            self.on_open(self.url)
            return True
        return False

    def draw(self, width, height):
        return [self.inline()]


class Breadcrumbs(_Themed):
    """``Inicio › Ventas › Pedido 1281``: the last item is the current one;
    long trails collapse in the middle to fit."""

    def __init__(self, items, separator=' › ', **kwargs):
        super(Breadcrumbs, self).__init__(**kwargs)
        self.items = [str(i) for i in items]
        self.separator = separator

    def natural_width(self):
        return _fx.visible_width(self.separator.join(self.items))

    def draw(self, width, height):
        items = list(self.items)
        fits = lambda xs: _fx.visible_width(  # noqa: E731
            self.separator.join(xs)) <= width
        if not fits(items) and len(items) > 2:
            # Keep the first and as many of the last as fit, '…' between.
            tail = [items[-1]]
            for item in reversed(items[1:-1]):
                if not fits([items[0], '…', item] + tail):
                    break
                tail.insert(0, item)
            items = [items[0], '…'] + tail
        parts = [self.paint(i, self.theme.muted) for i in items[:-1]]
        if items:
            parts.append(self.paint(items[-1], 'bold'))
        return [self.paint(self.separator, self.theme.muted).join(parts)]


class EmptyState(_Themed):
    """A centred icon, title and hint for a view with nothing to show."""

    expand = True

    def __init__(self, title='Sin datos', message=None, icon='∅',
                 action=None, **kwargs):
        super(EmptyState, self).__init__(**kwargs)
        self.title = title
        self.message = message
        self.icon = icon
        self.action = action

    def natural_width(self):
        return max(_fx.visible_width(self.title),
                   _fx.visible_width(self.message or '')) + 4

    def draw(self, width, height):
        lines = [self.paint(self.icon, self.theme.muted), '',
                 self.paint(self.title, 'bold')]
        if self.message:
            lines.extend(self.paint(line, self.theme.muted)
                         for line in _wrap(self.message, width - 4))
        if self.action:
            lines.extend(['', self.paint(self.action, self.theme.accent)])
        top = max(0, ((height or len(lines)) - len(lines)) // 2)
        return [''] * top + [_fx.fit_line(line, width, 'c') for line in lines]


class ErrorPanel(EmptyState):
    """An error screen: big code, title, message and what to do next."""

    def __init__(self, code=None, title='Algo salió mal', message=None,
                 hint=None, **kwargs):
        super(ErrorPanel, self).__init__(title=title, message=message,
                                         icon='✖', action=hint, **kwargs)
        self.code = code

    def draw(self, width, height):
        lines = super(ErrorPanel, self).draw(width, None)
        lines[0] = _fx.fit_line(self.paint(
            '✖ ' + (str(self.code) if self.code is not None else 'Error'),
            'bold ' + self.theme.error), width, 'c')
        top = max(0, ((height or len(lines)) - len(lines)) // 2)
        return [''] * top + lines


class Spinner(_Themed):
    """
    An animated spinner with a message; each ``render`` (or ``tick()``)
    advances it. ``style`` is ``'dots'``, ``'line'``, ``'arc'`` or
    ``'bounce'``.
    """

    STYLES = {'dots': '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏', 'line': '-\\|/', 'arc': '◜◠◝◞◡◟',
              'bounce': '⠁⠂⠄⠂'}

    def __init__(self, message='', style='dots', **kwargs):
        super(Spinner, self).__init__(**kwargs)
        self.message = message
        self.frames = self.STYLES.get(style, style)
        self.index = 0

    def natural_width(self):
        return _fx.visible_width(self.message) + 2

    def tick(self):
        self.index = (self.index + 1) % len(self.frames)

    def draw(self, width, height):
        glyph = self.frames[self.index % len(self.frames)]
        self.tick()
        return [self.paint(glyph, self.theme.accent) +
                (' ' + self.message if self.message else '')]


class Skeleton(_Themed):
    """Grey placeholder bars while content loads (``lines`` of them)."""

    def __init__(self, lines=3, **kwargs):
        super(Skeleton, self).__init__(**kwargs)
        self.lines = max(1, int(lines))

    def draw(self, width, height):
        out = []
        for i in range(self.lines):
            w = width if i < self.lines - 1 else max(1, width * 3 // 5)
            out.append(self.paint('░' * w, self.theme.muted))
        return out


# +---------------------------------------------------------------------------+
# Code

_KEYWORDS = {
    'python': 'and as assert async await break class continue def del elif '
              'else except False finally for from global if import in is '
              'lambda None nonlocal not or pass raise return True try while '
              'with yield self',
    'javascript': 'async await break case catch class const continue default '
                  'delete do else export extends false finally for function '
                  'if import in instanceof let new null return super switch '
                  'this throw true try typeof undefined var void while yield',
    'sql': 'select from where and or not insert into values update set delete '
           'create table alter drop index join left right inner outer on as '
           'group by order having limit offset null is in like between case '
           'when then else end distinct union all primary key references '
           'returning with',
    'bash': 'if then else elif fi for in do done while case esac function '
            'return export local echo exit',
    'json': 'true false null',
}
_KEYWORDS['typescript'] = _KEYWORDS['javascript'] + ' interface type enum ' \
    'implements private public readonly'
_KEYWORDS['js'] = _KEYWORDS['javascript']
_KEYWORDS['ts'] = _KEYWORDS['typescript']
_KEYWORDS['py'] = _KEYWORDS['python']
_KEYWORDS['sh'] = _KEYWORDS['bash']
_COMMENTS = {'python': '#', 'py': '#', 'bash': '#', 'sh': '#', 'sql': '--',
             'javascript': '//', 'js': '//', 'typescript': '//', 'ts': '//'}
_TOKEN = re.compile(r'''(?P<str>"(?:\\.|[^"\\])*"?|'(?:\\.|[^'\\])*'?|`[^`]*`?)'''
                    r'''|(?P<num>\b\d+(?:\.\d+)?\b)|(?P<word>[A-Za-z_]\w*)''')


def highlight(line, language, painter, theme):
    """One line of code with strings, numbers, keywords and comments
    coloured. Unknown languages come back as they are."""
    lang = (language or '').lower()
    if lang not in _KEYWORDS:
        return line
    keywords = set(_KEYWORDS[lang].split())
    sql = lang == 'sql'
    comment = _COMMENTS.get(lang)
    code, rest = line, ''
    if comment:
        # A comment marker outside strings starts the comment.
        in_str = None
        for i, ch in enumerate(line):
            if in_str:
                if ch == in_str and line[i - 1:i] != '\\':
                    in_str = None
            elif ch in '"\'`':
                in_str = ch
            elif line.startswith(comment, i):
                code, rest = line[:i], line[i:]
                break
    out, pos = [], 0
    for match in _TOKEN.finditer(code):
        out.append(code[pos:match.start()])
        text = match.group(0)
        if match.group('str'):
            out.append(painter(text, theme.success))
        elif match.group('num'):
            out.append(painter(text, theme.warning))
        elif (text.lower() if sql else text) in keywords:
            out.append(painter(text, 'bold ' + theme.accent))
        else:
            out.append(text)
        pos = match.end()
    out.append(code[pos:])
    if rest:
        out.append(painter(rest, theme.muted))
    return ''.join(out)


class Code(_Themed):
    """
    Source code with line numbers and highlighting for ``language``
    (python, javascript/typescript, sql, bash, json). Long lines are cut;
    ``title`` frames it.
    """

    def __init__(self, code, language=None, line_numbers=True, title=None,
                 start=1, **kwargs):
        super(Code, self).__init__(**kwargs)
        self.code = code.rstrip('\n')
        self.language = language
        self.line_numbers = bool(line_numbers)
        self.title = title
        self.start = start

    def natural_width(self):
        lines = self.code.split('\n')
        gutter = len(str(len(lines) + self.start)) + 3 \
            if self.line_numbers else 0
        return max(_fx.visible_width(line) for line in lines) + gutter + \
            (4 if self.title else 0)

    def draw(self, width, height):
        lines = self.code.split('\n')
        digits = len(str(len(lines) + self.start - 1))
        inner = width - 4 if self.title else width
        out = []
        for i, line in enumerate(lines):
            text = highlight(line.expandtabs(4), self.language, self.paint,
                             self.theme)
            if self.line_numbers:
                num = self.paint('{0:>{1}} │ '.format(i + self.start, digits),
                                 self.theme.muted)
                text = num + text
            out.append(_fx.fit_line(text, max(1, inner)))
        if self.title:
            return frame([' ' + line for line in out], width, self.title,
                         self.theme.border, self.paint)
        return out


# +---------------------------------------------------------------------------+
# Markdown and HTML

_INLINE = [
    (re.compile(r'`([^`]+)`'), 'code'),
    (re.compile(r'\*\*(.+?)\*\*|__(.+?)__'), 'bold'),
    (re.compile(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])|'
                r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])'), 'italic'),
    (re.compile(r'~~(.+?)~~'), 'strike'),
    (re.compile(r'\[([^\]]+)\]\(([^)]+)\)'), 'link'),
]


class MarkdownView(_Themed):
    """
    Markdown drawn for the terminal: headings, emphasis, inline and fenced
    code (highlighted), quotes, ordered / unordered / task lists, rules,
    links and pipe tables (as flexablelib tables), wrapped to the width.
    """

    def __init__(self, text, **kwargs):
        super(MarkdownView, self).__init__(**kwargs)
        self.text = text

    def natural_width(self):
        return min(100, max((_fx.visible_width(line) for line in
                             self.text.split('\n')), default=0))

    def inline(self, text):
        # Each piece is rendered and parked behind a placeholder, so the
        # escape sequences it adds (which contain '[') are never matched by
        # the patterns that run after it.
        store = []
        token = re.compile('\x00(\\d+)\x00')

        def restore(value):
            return token.sub(lambda m: store[int(m.group(1))], value)

        def keep(rendered):
            store.append(rendered)
            return '\x00{0}\x00'.format(len(store) - 1)

        def render(kind, match):
            inner = restore(next(g for g in match.groups() if g is not None))
            if kind == 'code':
                return self.paint(inner, self.theme.warning) if \
                    self._active() else '`' + inner + '`'
            if kind == 'bold':
                return self.paint(inner, 'bold')
            if kind == 'italic':
                return self.paint(inner, 'italic')
            if kind == 'strike':
                return self.paint(inner, 'dim')
            url = match.group(2)
            if not self._active():
                return '{0} <{1}>'.format(inner, url)
            return '\x1b]8;;{0}\x1b\\{1}\x1b]8;;\x1b\\'.format(
                url, self.paint(inner, 'underline ' + self.theme.info))
        for pattern, kind in _INLINE:
            text = pattern.sub(lambda m, k=kind: keep(render(k, m)), text)
        return restore(text)

    def _table(self, rows, width):
        from flexablelib import Table
        cells = [[c.strip() for c in row.strip().strip('|').split('|')]
                 for row in rows]
        header, body = cells[0], [r for r in cells[2:]]
        table = Table(headers=header)
        for row in body:
            table.add_row((row + [''] * len(header))[:len(header)])
        table.style_name = 'rounded'
        table.use_colors = self._active()
        table.max_width = width
        return table.compose().split('\n')

    def draw(self, width, height):
        out = []
        lines = self.text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith('```'):
                lang = stripped[3:].strip() or None
                block = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    block.append(lines[i])
                    i += 1
                i += 1
                bar = self.paint('│ ', self.theme.muted)
                out.extend(bar + _fx.fit_line(highlight(
                    b, lang, self.paint, self.theme), max(1, width - 2))
                    for b in block)
                continue
            if stripped.startswith('|') and i + 1 < len(lines) and \
                    re.match(r'^\s*\|?\s*:?-+', lines[i + 1]):
                rows = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    rows.append(lines[i])
                    i += 1
                out.extend(self._table(rows, width))
                continue
            i += 1
            heading = re.match(r'^(#{1,6})\s+(.*)', stripped)
            if heading:
                level = len(heading.group(1))
                text = self.inline(heading.group(2))
                if out and out[-1] != '':
                    out.append('')
                if level == 1:
                    out.append(self.paint(text.upper() if not self._active()
                                          else text, 'bold underline ' +
                                          self.theme.accent))
                elif level == 2:
                    out.append(self.paint(text, 'bold ' + self.theme.accent))
                else:
                    out.append(self.paint(text, 'bold'))
                continue
            if re.match(r'^(-{3,}|\*{3,}|_{3,})$', stripped):
                out.append(self.paint('─' * width, self.theme.muted))
                continue
            if stripped.startswith('>'):
                bar = self.paint('▎ ', self.theme.muted)
                for part in _wrap(self.inline(stripped.lstrip('> ')),
                                  width - 2):
                    out.append(bar + self.paint(part, 'italic'))
                continue
            item = re.match(r'^(\s*)([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?(.*)',
                            line)
            if item:
                indent = len(item.group(1).expandtabs(4)) // 2 * 2
                marker = item.group(2)
                if marker in '-*+':
                    marker = '•' if self._active() else '-'
                task = item.group(3)
                if task:
                    done = task.strip()[1] in 'xX'
                    marker = ('☑' if done else '☐') if self._active() else \
                        ('[x]' if done else '[ ]')
                prefix = ' ' * indent + marker + ' '
                body = _wrap(self.inline(item.group(4)),
                             width - len(prefix))
                out.append(prefix + body[0])
                out.extend(' ' * len(prefix) + b for b in body[1:])
                continue
            if not stripped:
                if out and out[-1] != '':
                    out.append('')
                continue
            out.extend(_wrap(self.inline(stripped), width))
        while out and out[-1] == '':
            out.pop()
        return out


class _HtmlToMarkdown(html.parser.HTMLParser):
    BLOCK = {'p', 'div', 'section', 'article', 'header', 'footer', 'ul',
             'ol', 'table', 'blockquote', 'pre', 'h1', 'h2', 'h3', 'h4',
             'h5', 'h6', 'hr', 'br', 'tr'}

    def __init__(self):
        html.parser.HTMLParser.__init__(self, convert_charrefs=True)
        self.out = []
        self.lists = []
        self.href = None
        self.pre = False
        self.row = None
        self.rows = []
        self.skip = 0

    def emit(self, text):
        self.out.append(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style', 'head'):
            self.skip += 1
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.emit('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag in ('p', 'div', 'section', 'article'):
            self.emit('\n\n')
        elif tag == 'br':
            self.emit('\n')
        elif tag in ('strong', 'b'):
            self.emit('**')
        elif tag in ('em', 'i'):
            self.emit('*')
        elif tag == 'code' and not self.pre:
            self.emit('`')
        elif tag == 'pre':
            self.pre = True
            self.emit('\n```\n')
        elif tag == 'a':
            self.href = attrs.get('href')
            self.emit('[')
        elif tag in ('ul', 'ol'):
            self.lists.append([tag, 0])
            self.emit('\n')
        elif tag == 'li':
            depth = max(0, len(self.lists) - 1)
            kind = self.lists[-1] if self.lists else ['ul', 0]
            kind[1] += 1
            marker = '{0}.'.format(kind[1]) if kind[0] == 'ol' else '-'
            self.emit('\n' + '  ' * depth + marker + ' ')
        elif tag == 'blockquote':
            self.emit('\n\n> ')
        elif tag == 'hr':
            self.emit('\n\n---\n\n')
        elif tag == 'tr':
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.row.append('')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head'):
            self.skip = max(0, self.skip - 1)
        elif tag in ('strong', 'b'):
            self.emit('**')
        elif tag in ('em', 'i'):
            self.emit('*')
        elif tag == 'code' and not self.pre:
            self.emit('`')
        elif tag == 'pre':
            self.pre = False
            self.emit('\n```\n')
        elif tag == 'a':
            self.emit('](' + (self.href or '') + ')')
            self.href = None
        elif tag in ('ul', 'ol') and self.lists:
            self.lists.pop()
            self.emit('\n')
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == 'table' and self.rows:
            width = max(len(r) for r in self.rows)
            rows = [r + [''] * (width - len(r)) for r in self.rows]
            lines = ['| ' + ' | '.join(rows[0]) + ' |',
                     '|' + '---|' * width]
            lines.extend('| ' + ' | '.join(r) + ' |' for r in rows[1:])
            self.emit('\n\n' + '\n'.join(lines) + '\n\n')
            self.rows = []
        elif tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                     'blockquote'):
            self.emit('\n\n')

    def handle_data(self, data):
        if self.skip:
            return
        if self.row is not None and self.row:
            self.row[-1] += data.strip()
            return
        if self.row is not None:
            return
        if not self.pre:
            data = re.sub(r'\s+', ' ', data)
        self.emit(data)


class HtmlView(MarkdownView):
    """HTML drawn like :class:`MarkdownView` (headings, emphasis, links,
    lists, quotes, code, tables); scripts and styles are dropped."""

    def __init__(self, html_text, **kwargs):
        parser = _HtmlToMarkdown()
        parser.feed(html_text)
        parser.close()
        text = re.sub(r'\n{3,}', '\n\n', ''.join(parser.out)).strip()
        text = '\n'.join(line.strip() if not line.startswith(' ') else
                         line.rstrip() for line in text.split('\n'))
        super(HtmlView, self).__init__(text, **kwargs)
        self.html = html_text


# +---------------------------------------------------------------------------+
# Records

class DetailView(_Themed):
    """
    Labelled values in aligned columns -- a record's detail. ``fields`` is a
    mapping or ``(label, value)`` pairs; a label starting with ``#`` is a
    section heading. ``columns=2`` lays the pairs out in two columns.
    """

    def __init__(self, fields, columns=1, label_color=None, **kwargs):
        super(DetailView, self).__init__(**kwargs)
        self.fields = list(fields.items()) if isinstance(fields, dict) \
            else list(fields)
        self.columns = max(1, int(columns))
        self.label_color = label_color

    def natural_width(self):
        widths = [_fx.visible_width(str(k)) + _fx.visible_width(str(v)) + 2
                  for k, v in self.fields]
        return min(100, max(widths or [10]) * self.columns +
                   3 * (self.columns - 1))

    def _block(self, fields, width):
        label_w = min(width // 2, max([_fx.visible_width(str(k))
                                       for k, _ in fields
                                       if not str(k).startswith('#')] or [0]))
        out = []
        for label, value in fields:
            label = str(label)
            if label.startswith('#'):
                if out:
                    out.append('')
                out.append(self.paint(label.lstrip('# '), 'bold ' +
                                      self.theme.accent))
                continue
            body = _wrap('' if value is None else value,
                         max(1, width - label_w - 2))
            head = self.paint(_fx.fit_line(label, label_w),
                              self.label_color or self.theme.muted)
            out.append(head + '  ' + body[0])
            out.extend(' ' * (label_w + 2) + b for b in body[1:])
        return out

    def draw(self, width, height):
        if self.columns == 1:
            return self._block(self.fields, width)
        from .base import join_columns
        per = int(math.ceil(len(self.fields) / float(self.columns)))
        col_w = max(1, (width - 3 * (self.columns - 1)) // self.columns)
        blocks = [self._block(self.fields[i * per:(i + 1) * per], col_w)
                  for i in range(self.columns)]
        return join_columns(blocks, [col_w] * self.columns, gap=3)


class Timeline(_Themed):
    """
    Events down a line: ``(when, title, detail)`` or dicts with ``when``,
    ``title``, ``detail``, ``kind`` / ``status``. Also a status history: give
    ``kind`` per event (``'success'``, ``'error'`` ...).
    """

    def __init__(self, events, **kwargs):
        super(Timeline, self).__init__(**kwargs)
        self.events = [self._event(e) for e in events]

    @staticmethod
    def _event(event):
        if isinstance(event, dict):
            return (str(event.get('when', '')), str(event.get('title', '')),
                    event.get('detail'), event.get('kind',
                                                   event.get('status')))
        event = tuple(event) + (None, None)
        return (str(event[0]), str(event[1]), event[2], event[3])

    def natural_width(self):
        return max([_fx.visible_width(w) + _fx.visible_width(t) + 5
                    for w, t, _, _ in self.events] or [10])

    def draw(self, width, height):
        when_w = max([_fx.visible_width(w) for w, _, _, _ in self.events] or
                     [0])
        out = []
        for i, (when, title, detail, kind) in enumerate(self.events):
            color = self.theme.kind(kind) if kind else self.theme.accent
            dot = self.paint('●', color) if self._active() else 'o'
            line = '│' if i < len(self.events) - 1 else ' '
            stem = self.paint(line, self.theme.muted) if self._active() \
                else ('|' if line != ' ' else ' ')
            out.append(self.paint(_fx.fit_line(when, when_w, 'r'),
                                  self.theme.muted) + ' ' + dot + ' ' +
                       self.paint(title, 'bold'))
            body_w = max(1, width - when_w - 3)
            for part in (_wrap(detail, body_w) if detail else []):
                out.append(' ' * when_w + ' ' + stem + ' ' + part)
            if i < len(self.events) - 1:
                out.append(' ' * when_w + ' ' + stem)
        return out


class Stepper(_Themed):
    """
    Progress through steps: ``✔ Datos ─── ● Pago ─── ○ Envío``. ``current``
    is the active step's index; ``layout='vertical'`` lists them with their
    ``descriptions``.
    """

    def __init__(self, steps, current=0, layout='horizontal',
                 descriptions=None, failed=None, **kwargs):
        super(Stepper, self).__init__(**kwargs)
        self.steps = [str(s) for s in steps]
        self.current = current
        self.layout = layout
        self.descriptions = descriptions or {}
        self.failed = failed

    def natural_width(self):
        return sum(_fx.visible_width(s) + 6 for s in self.steps)

    def _mark(self, i):
        if i == self.failed:
            return self.paint('✖', self.theme.error) if self._active() \
                else 'x', self.theme.error
        if i < self.current:
            return (self.paint('✔', self.theme.success) if self._active()
                    else 'v'), None
        if i == self.current:
            return (self.paint('●', self.theme.accent) if self._active()
                    else '>'), 'bold ' + self.theme.accent
        return (self.paint('○', self.theme.muted) if self._active()
                else 'o'), self.theme.muted

    def draw(self, width, height):
        if self.layout == 'vertical':
            out = []
            for i, step in enumerate(self.steps):
                mark, spec = self._mark(i)
                out.append(mark + ' ' + self.paint(step, spec))
                desc = self.descriptions.get(i) or self.descriptions.get(step)
                if desc:
                    out.extend('│ ' + self.paint(d, self.theme.muted)
                               for d in _wrap(desc, width - 2))
                if i < len(self.steps) - 1:
                    out.append(self.paint('│', self.theme.muted))
            return out
        labels = []
        for i, step in enumerate(self.steps):
            mark, spec = self._mark(i)
            labels.append(mark + ' ' + self.paint(step, spec))
        used = sum(_fx.visible_width(l) for l in labels)
        gaps = len(labels) - 1
        if gaps and used + 3 * gaps <= width:
            seg = max(3, min(8, (width - used) // gaps - 2))
            joiner = ' ' + self.paint('─' * seg, self.theme.muted) + ' '
            return [joiner.join(labels)]
        # Too narrow: only the current step, with its number.
        mark, spec = self._mark(self.current)
        return ['{0}/{1} '.format(self.current + 1, len(self.steps)) + mark +
                ' ' + self.paint(self.steps[self.current], spec)]


class CommentList(_Themed):
    """
    A conversation: dicts with ``author``, ``when``, ``text`` and optional
    ``replies`` (indented below).
    """

    def __init__(self, comments, **kwargs):
        super(CommentList, self).__init__(**kwargs)
        self.comments = list(comments)

    def _one(self, comment, width, depth, out):
        pad = '  ' * depth + ('│ ' if depth else '')
        avail = max(1, width - _fx.visible_width(pad))
        head = self.paint(str(comment.get('author', '')), 'bold ' +
                          self.theme.accent)
        if comment.get('when'):
            head += ' ' + self.paint('· ' + str(comment['when']),
                                     self.theme.muted)
        out.append(pad + head)
        out.extend(pad + line for line in _wrap(comment.get('text', ''),
                                                avail))
        for reply in comment.get('replies', []):
            self._one(reply, width, depth + 1, out)

    def draw(self, width, height):
        out = []
        for i, comment in enumerate(self.comments):
            if i:
                out.append('')
            self._one(comment, width, 0, out)
        return out


def human_size(size):
    """``1536`` -> ``'1.5 KB'``."""
    size = float(size or 0)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024 or unit == 'TB':
            return ('{0:.0f} {1}' if unit == 'B' else '{0:.1f} {1}').format(
                size, unit)
        size /= 1024.0


class AttachmentList(_Themed):
    """Files with an icon by type, name and size: ``(name, size)`` pairs or
    dicts with ``name`` and ``size``."""

    ICONS = {'pdf': '📕', 'xlsx': '📗', 'xls': '📗', 'csv': '📗', 'doc': '📘',
             'docx': '📘', 'png': '🖼', 'jpg': '🖼', 'jpeg': '🖼', 'gif': '🖼',
             'zip': '📦', 'txt': '📄', 'json': '📄', 'md': '📄'}

    def __init__(self, files, **kwargs):
        super(AttachmentList, self).__init__(**kwargs)
        self.files = [(f.get('name'), f.get('size')) if isinstance(f, dict)
                      else tuple(f) for f in files]

    def draw(self, width, height):
        out = []
        for name, size in self.files:
            ext = str(name).rsplit('.', 1)[-1].lower() if '.' in str(name) \
                else ''
            icon = self.ICONS.get(ext, '📎') if self._active() else '-'
            right = human_size(size) if size is not None else ''
            room = max(1, width - _fx.visible_width(icon) - len(right) - 2)
            out.append(icon + ' ' + _fx.fit_line(_fx.truncate(
                str(name), room, '…'), room) + ' ' +
                self.paint(right, self.theme.muted))
        return out


class Stat(_Themed):
    """
    A KPI: label, big value, change against before (``delta``, a number or
    text; positive is green unless ``invert=True``) and an optional trend
    sparkline (``trend`` values).
    """

    def __init__(self, label, value, delta=None, trend=None, invert=False,
                 suffix='', **kwargs):
        super(Stat, self).__init__(**kwargs)
        self.label = label
        self.value = value
        self.delta = delta
        self.trend = list(trend or [])
        self.invert = bool(invert)
        self.suffix = suffix

    def natural_width(self):
        return max(_fx.visible_width(str(self.label)),
                   _fx.visible_width(str(self.value)) + 10, 18)

    def draw(self, width, height):
        out = [self.paint(str(self.label), self.theme.muted)]
        value = self.paint(str(self.value), 'bold')
        if self.delta is not None:
            number = self.delta
            if isinstance(number, str):
                try:
                    number = float(number.strip('%+ '))
                    if self.delta.strip().startswith('-'):
                        number = -abs(number)
                except ValueError:
                    number = 0
            good = (number >= 0) != self.invert
            arrow = '▲' if number > 0 else ('▼' if number < 0 else '■')
            text = self.delta if isinstance(self.delta, str) else \
                '{0:+g}{1}'.format(self.delta, self.suffix)
            value += '  ' + self.paint(arrow + ' ' + text.lstrip('+-')
                                       if number else arrow + ' ' + text,
                                       self.theme.success if good else
                                       self.theme.error)
        out.append(value)
        if self.trend:
            sparks = '▁▂▃▄▅▆▇█'
            data = self.trend[-width:]
            low, high = min(data), max(data)
            span = (high - low) or 1
            out.append(self.paint(''.join(
                sparks[int((v - low) / span * 7)] for v in data),
                self.theme.accent))
        return out


class LineChart(_Themed):
    """
    Lines on a braille canvas (2x4 dots per cell) with a y axis and x
    labels. ``series`` maps names to value lists (or is one list);
    ``height`` is in rows. Each series takes a colour from ``colors``.
    """

    COLORS = ['cyan', 'magenta', 'yellow', 'green', 'blue', 'red']

    def __init__(self, series, height=8, labels=None, colors=None,
                 y_format='{0:g}', legend=True, **kwargs):
        super(LineChart, self).__init__(**kwargs)
        if not isinstance(series, dict):
            series = {'': list(series)}
        self.series = {k: list(v) for k, v in series.items()}
        self.height = max(2, int(height))
        self.labels = labels
        self.colors = list(colors or self.COLORS)
        self.y_format = y_format
        self.legend = bool(legend)

    def natural_width(self):
        return max(30, max(len(v) for v in self.series.values()) + 8)

    def draw(self, width, height):
        rows = self.height if height is None else max(2, min(self.height,
                                                             height - 2))
        values = [v for s in self.series.values() for v in s]
        if not values:
            return ['']
        low, high = min(values), max(values)
        if high == low:
            high = low + 1
        labels = [self.y_format.format(high), self.y_format.format(low)]
        axis_w = max(len(l) for l in labels) + 1
        cols = max(2, width - axis_w - 1)
        dots_w, dots_h = cols * 2, rows * 4
        cells = [[0] * cols for _ in range(rows)]
        owner = [[None] * cols for _ in range(rows)]
        bits = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
        for n, (name, data) in enumerate(self.series.items()):
            if len(data) < 2:
                data = data * 2
            prev = None
            for x in range(dots_w):
                pos = x * (len(data) - 1) / float(max(1, dots_w - 1))
                i = int(pos)
                frac = pos - i
                v = data[i] if i + 1 >= len(data) else \
                    data[i] + (data[i + 1] - data[i]) * frac
                y = int(round((high - v) / (high - low) * (dots_h - 1)))
                span = [y] if prev is None else range(min(prev, y),
                                                      max(prev, y) + 1)
                for yy in span:
                    r, c = yy // 4, x // 2
                    cells[r][c] |= bits[yy % 4][x % 2]
                    owner[r][c] = n
                prev = y
        out = []
        for r in range(rows):
            label = labels[0] if r == 0 else (labels[1] if r == rows - 1
                                              else '')
            line = []
            for c in range(cols):
                bitsum = cells[r][c]
                if not bitsum:
                    line.append(' ')
                    continue
                char = chr(0x2800 + bitsum)
                color = self.colors[owner[r][c] % len(self.colors)]
                line.append(self.paint(char, color))
            out.append(self.paint(_fx.fit_line(label, axis_w - 1, 'r'),
                                  self.theme.muted) + ' ' +
                       self.paint('┤' if label else '│', self.theme.muted) +
                       ''.join(line))
        axis = ' ' * axis_w + self.paint('└' + '─' * cols, self.theme.muted)
        out.append(axis)
        if self.labels:
            first, last = str(self.labels[0]), str(self.labels[-1])
            gap = max(1, cols - len(first) - len(last))
            out.append(' ' * (axis_w + 1) + self.paint(
                first + ' ' * gap + last, self.theme.muted))
        if self.legend and len(self.series) > 1:
            parts = [self.paint('━━', self.colors[n % len(self.colors)]) +
                     ' ' + name for n, name in enumerate(self.series)]
            out.append(' ' * (axis_w + 1) + '   '.join(parts))
        return out


