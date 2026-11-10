"""
DATA WRITERS

Renders a table to formats other than the console. Reached through the Table
methods rather than called directly::

    table.to_csv('out.csv')
    table.to_markdown()
    table.to_html('report.html', paginate=25)
    table.to_excel('report.xlsx')

CSV, Markdown and HTML need nothing beyond the standard library. Only Excel
requires openpyxl, and only when used.

The HTML writer emits a single self-contained file. Sorting, filtering and
pagination are done by a small inline script with no external requests, so the
result works offline, from a file:// URL, and inside environments that block
third-party resources.
"""

import csv as _csv
import html as _html
import io as _io
import json
import re
from typing import Any, List, Optional, Sequence

from .fast import strip_ansi
from .colors import background_hex, foreground_hex, spec_to_css
from .options import FLT_FILTER, INT_FILTER
from .utils import to_roman



def _script_safe_json(payload) -> str:
    """
    JSON for embedding inside an inline ``<script>`` element.

    ``json.dumps`` leaves ``<``, ``>`` and ``&`` alone, so a cell containing
    ``</script>`` would close the element and let the rest of the cell run
    as markup -- an XSS hole for any page built from untrusted data. Escaping
    them (and the two line separators JavaScript treats as newlines) as
    ``\\uXXXX`` keeps the value identical once parsed.
    """
    text = json.dumps(payload)
    for char, code in (('<', '\\u003c'), ('>', '\\u003e'), ('&', '\\u0026'),
                       ('\u2028', '\\u2028'), ('\u2029', '\\u2029')):
        text = text.replace(char, code)
    return text

def _plain(value: Any) -> str:
    """
    Cell text with any colour removed.

    Every writer here targets a format that carries its own styling, so ANSI
    sequences would be literal noise -- and in CSV they would corrupt the
    field outright.
    """
    return strip_ansi(str(value)) if value is not None else ''


def _view(table, include_index: bool):
    """
    The rows, columns and cell texts ``compose()`` would show.

    Since 2.2.0 every writer exports the table as it is displayed:
    ``row_filter`` and ``sort_by`` (``sort_reverse``, callables) applied,
    ``hide_columns`` left out, and the configured formats (``int_format``,
    ``float_format``, ``leading_zeros``, ``custom_format``, ``strip_cells``)
    applied to the text. See :meth:`Table._export_view`.
    """
    return table._export_view(include_index)


def _table_data(table, include_index: bool):
    """(headers, raw rows) in display order, ``None`` in the gaps."""
    view = _view(table, include_index)
    return view.headers, view.raw


def _effective_region_color(table, region):
    """Explicit merge colour, else inherit from row/column colour maps."""
    if getattr(region, 'color', None):
        return region.color
    try:
        row_colors = getattr(table, 'row_colors', None) or {}
        if region.first_row in row_colors:
            return row_colors[region.first_row]
        headers = list(getattr(table, 'headers', []) or [])
        if region.first_column < len(headers):
            col_colors = getattr(table, 'column_colors', None) or {}
            return col_colors.get(headers[region.first_column])
    except Exception:
        return None
    return None


def _align_style(align: str) -> str:
    return {'l': 'left', 'r': 'right', 'c': 'center'}.get(align, 'center')


def _html_body_with_merges(table, include_index: bool = False,
                           view=None) -> str:
    """
    Build ``<tr>…</tr>`` rows that honour ``merged_regions`` via rowspan/colspan.

    Covered cells are omitted so the browser paints one merged cell. Merge
    coordinates address data columns; an optional index column shifts them by 1.
    Cells hold the formatted text ``compose()`` shows, in display order.
    """
    if view is None:
        view = _view(table, include_index)
    headers, rows = view.headers, view.text
    col_offset = 1 if include_index else 0
    regions = view.merges

    # Map every covered (row, col-in-output) cell -> owning region (or None for top-left).
    covered = {}
    origin = {}
    for region in regions:
        r0, r1 = region.first_row, region.last_row
        c0, c1 = region.first_column + col_offset, region.last_column + col_offset
        origin[(r0, c0)] = region
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r, c) != (r0, c0):
                    covered[(r, c)] = region

    parts = []
    n_cols = len(headers)
    for r_i, row in enumerate(rows):
        parts.append('<tr>')
        for c_i in range(n_cols):
            if (r_i, c_i) in covered:
                continue
            region = origin.get((r_i, c_i))
            if region is not None:
                rowspan = region.last_row - region.first_row + 1
                colspan = region.last_column - region.first_column + 1
                text = _plain(region.value if region.value is not None else row[c_i])
                attrs = []
                if rowspan > 1:
                    attrs.append(f'rowspan="{rowspan}"')
                if colspan > 1:
                    attrs.append(f'colspan="{colspan}"')
                style_bits = [
                    f'text-align:{_align_style(region.align)}',
                    'vertical-align:middle',
                ]
                color_css = spec_to_css(_effective_region_color(table, region))
                if color_css:
                    style_bits.append(color_css)
                attrs.append(f'style="{";".join(style_bits)}"')
                attr_s = (' ' + ' '.join(attrs)) if attrs else ''
                parts.append(f'<td{attr_s}>{_html.escape(text)}</td>')
            else:
                cell = row[c_i] if c_i < len(row) else ''
                parts.append(f'<td>{_html.escape(_plain(cell))}</td>')
        parts.append('</tr>')
    return ''.join(parts)



def to_records(table, include_index: bool = False,
               formatted: bool = False) -> List[dict]:
    """
    The table as a list of dicts, one per row.

    Rows come in the order ``compose()`` shows them (``sort_by`` and
    ``row_filter`` applied) and ``hide_columns`` are left out. Values stay
    the stored Python objects, so numbers remain numbers; ``formatted=True``
    gives the displayed strings instead. Gaps are ``None`` either way.
    """
    view = _view(table, include_index)
    if not formatted:
        return [dict(zip(view.headers, row)) for row in view.raw]
    return [
        dict(zip(view.headers, [
            None if raw is None else text
            for raw, text in zip(raw_row, text_row)
        ]))
        for raw_row, text_row in zip(view.raw, view.text)
    ]


def to_simple_html(table, include_index: bool = False) -> str:
    """
    A bare HTML ``<table>`` for notebook ``_repr_html_`` hooks.

    No document chrome, scripts or pagination -- just thead/tbody so Jupyter
    and friends can embed the table in a cell output. Merged regions become
    ``rowspan`` / ``colspan`` attributes.
    """
    view = _view(table, include_index)
    headers = view.headers
    parts = ['<table>']
    title = getattr(table, 'title', None)
    if title:
        parts.append(
            '<caption>{0}</caption>'.format(_html.escape(str(title)))
        )
    if headers:
        parts.append('<thead><tr>')
        for header in headers:
            parts.append(
                '<th>{0}</th>'.format(_html.escape(_plain(header)))
            )
        parts.append('</tr></thead>')
    parts.append('<tbody>')
    parts.append(_html_body_with_merges(table, include_index, view))
    parts.append('</tbody></table>')
    return ''.join(parts)


def to_csv(table, target=None, include_index: bool = False,
           delimiter: str = ',', encoding: str = 'utf-8',
           dialect=None, quoting=None, quotechar=None, escapechar=None,
           doublequote=None, lineterminator=None, skipinitialspace=None,
           strict=None) -> Optional[str]:
    """
    Write CSV.

    With no target, returns the CSV as a string; otherwise writes to the given
    path or open handle and returns None.

    Dialect extras (``quoting``, ``quotechar``, ``escapechar``,
    ``doublequote``, ``lineterminator``, ``skipinitialspace``, ``strict``,
    ``dialect``) are forwarded to ``csv.writer``.
    """
    view = _view(table, include_index)
    headers, rows = view.headers, view.text
    from .readers import _csv_reader_kwargs
    writer_kwargs = _csv_reader_kwargs(
        delimiter=delimiter, dialect=dialect, quoting=quoting,
        quotechar=quotechar, escapechar=escapechar,
        doublequote=doublequote, lineterminator=lineterminator,
        skipinitialspace=skipinitialspace, strict=strict,
    )

    def dump(handle):
        writer = _csv.writer(handle, **writer_kwargs)
        writer.writerow([_plain(header) for header in headers])
        for row in rows:
            writer.writerow([_plain(cell) for cell in row])

    if target is None:
        buffer = _io.StringIO()
        dump(buffer)
        return buffer.getvalue()
    if hasattr(target, 'write'):
        dump(target)
        return None
    with open(target, 'w', newline='', encoding=encoding) as handle:
        dump(handle)
    return None


def _markdown_alignment(table, header, column_i, values) -> str:
    """
    Which way a Markdown column should be aligned: ``l``, ``c`` or ``r``.

    An explicit ``col_alignment`` wins. Otherwise a column whose every filled
    cell is a number is right-aligned, as it is in the rendered table.
    Markdown has no decimal alignment, so ``'f'`` becomes ``'r'``.
    """
    requested = getattr(table, 'col_alignment', None)
    chosen = None
    if isinstance(requested, dict):
        chosen = requested.get(header)
    elif isinstance(requested, (list, tuple)):
        if column_i < len(requested):
            chosen = requested[column_i]
    elif requested is not None:
        chosen = requested

    if chosen is None:
        filled = [
            str(value) for value in values
            if value is not None and str(value).strip() != ''
        ]
        numeric = [
            text for text in filled
            if FLT_FILTER(text) is not None or INT_FILTER(text) is not None
        ]
        chosen = 'r' if filled and len(numeric) == len(filled) else 'l'

    if chosen in ('r', 'f'):
        return 'r'
    if chosen == 'c':
        return 'c'
    return 'l'


def _markdown_rule(alignment: str, width: int) -> str:
    """
    The dashes under one column, marked with the colons Markdown reads.

    ``:---`` left, ``---:`` right, ``:--:`` centred. Without them every
    renderer left-aligns, so a column of numbers came out ragged in the
    rendered document even though it was right-aligned in the terminal.
    """
    if alignment == 'r':
        return '-' * (width - 1) + ':'
    if alignment == 'c':
        return ':' + '-' * (width - 2) + ':'
    return ':' + '-' * (width - 1)


def to_markdown(table, include_index: bool = False,
                align: bool = True) -> str:
    """
    Write a GitHub-flavoured Markdown table.

    Pipes inside cells are escaped, since an unescaped one would split the
    cell and shift every column after it.

    With ``align`` the columns are padded to a common width and the rule
    under the header carries the alignment colons, so the rendered document
    lines its numbers up the way the terminal does. Without it the rule is
    plain dashes and nothing is padded.
    """
    from .fast import visible_width, pad_to_width

    view = _view(table, include_index)
    headers, rows = view.headers, view.raw
    if not headers:
        return ''

    def cell(value):
        return _plain(value).replace('|', '\\|').replace('\n', ' ')

    header_texts = [cell(header) for header in headers]
    row_texts = [[cell(value) for value in row] for row in view.text]

    if align:
        widths = [
            max([visible_width(header_texts[i])]
                + [visible_width(row[i]) for row in row_texts if i < len(row)]
                + [3])
            for i in range(len(header_texts))
        ]
        alignments = [
            _markdown_alignment(
                table, header, i,
                [row[i] for row in rows if i < len(row)],
            )
            for i, header in enumerate(headers)
        ]
    else:
        widths = [max(3, visible_width(text)) for text in header_texts]
        alignments = ['l'] * len(header_texts)

    def line(cells):
        padded = [
            pad_to_width(
                text,
                widths[i],
                alignments[i] if align else 'l',
            ) if i < len(widths) else text
            for i, text in enumerate(cells)
        ]
        return '| ' + ' | '.join(padded) + ' |'

    if align:
        rules = [
            _markdown_rule(alignments[i], width)
            for i, width in enumerate(widths)
        ]
    else:
        rules = ['-' * width for width in widths]
    separator = '| ' + ' | '.join(rules) + ' |'
    return '\n'.join([line(header_texts), separator]
                     + [line(row) for row in row_texts])


# The inline stylesheet and script for to_html(). Kept as module constants so
# the generated file stays readable and the Python stays legible.
_HTML_STYLE = """
:root {
  --bg: #ffffff; --fg: #1f2430; --muted: #5a6472; --line: #e3e6ec;
  --head: #4338ca; --head-fg: #ffffff; --stripe: #f7f8fb; --accent: #f59e0b;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117; --fg: #e6edf3; --muted: #9aa4b2; --line: #263041;
    --head: #4338ca; --head-fg: #ffffff; --stripe: #131a24; --accent: #f59e0b;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2rem 1.25rem; background: var(--bg); color: var(--fg);
  font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.wrap { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.25rem; margin: 0 0 1rem; font-weight: 600; }
.controls {
  display: flex; gap: .75rem; flex-wrap: wrap; align-items: center;
  margin-bottom: 1rem;
}
.controls input, .controls select {
  padding: .45rem .6rem; border: 1px solid var(--line); border-radius: 6px;
  background: var(--bg); color: var(--fg); font: inherit; font-size: .9rem;
}
.controls input { flex: 1 1 14rem; min-width: 0; }
.count { color: var(--muted); font-size: .85rem; margin-left: auto; }
.scroll { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
th, td { padding: .5rem .75rem; text-align: left; white-space: nowrap; }
thead th {
  background: var(--head); color: var(--head-fg); font-weight: 600;
  position: sticky; top: 0; cursor: pointer; user-select: none;
}
thead th:hover { filter: brightness(1.15); }
thead th::after { content: ""; opacity: .55; margin-left: .4rem; }
thead th[data-dir="asc"]::after { content: "\\2191"; }
thead th[data-dir="desc"]::after { content: "\\2193"; }
tbody tr:nth-child(even) { background: var(--stripe); }
tbody td { border-top: 1px solid var(--line); }
td.num { text-align: right; }
.pager { display: flex; gap: .4rem; align-items: center; margin-top: 1rem; flex-wrap: wrap; }
.pager button {
  padding: .35rem .7rem; border: 1px solid var(--line); border-radius: 6px;
  background: var(--bg); color: var(--fg); font: inherit; font-size: .85rem;
  cursor: pointer;
}
.pager button:disabled { opacity: .4; cursor: default; }
.pager .page { color: var(--muted); font-size: .85rem; }
.empty { padding: 2rem; text-align: center; color: var(--muted); }
"""

_HTML_SCRIPT = """
(function () {
  var rows = DATA.rows, cols = DATA.headers, numeric = DATA.numeric;
  // Numeric columns sort on the stored number, not the formatted text.
  rows.forEach(function (row, i) { row.keys = (DATA.keys || [])[i] || []; });
  var perPage = DATA.perPage, page = 0, sortCol = -1, sortDir = 0;
  var view = rows.slice();

  var q = document.getElementById('q');
  var body = document.getElementById('body');
  var count = document.getElementById('count');
  var pageLabel = document.getElementById('pageLabel');
  var prev = document.getElementById('prev');
  var next = document.getElementById('next');
  var sizeSelect = document.getElementById('size');

  function compare(a, b) {
    var x = a[sortCol], y = b[sortCol];
    if (numeric[sortCol]) {
      var kx = a.keys[sortCol], ky = b.keys[sortCol];
      var nx = kx === null || kx === undefined ? NaN : kx;
      var ny = ky === null || ky === undefined ? NaN : ky;
      // Blank and non-numeric cells sort last, whichever way the column goes.
      var bx = isNaN(nx), by = isNaN(ny);
      if (bx && by) return 0;
      if (bx) return 1;
      if (by) return -1;
      return (nx - ny) * sortDir;
    }
    return String(x).localeCompare(String(y), undefined, {numeric: true}) * sortDir;
  }

  function apply() {
    var needle = q.value.trim().toLowerCase();
    view = needle
      ? rows.filter(function (row) {
          return row.some(function (cell) {
            return String(cell).toLowerCase().indexOf(needle) !== -1;
          });
        })
      : rows.slice();
    if (sortCol >= 0 && sortDir !== 0) view.sort(compare);
    if (page * perPage >= view.length) page = 0;
    render();
  }

  function render() {
    var start = perPage > 0 ? page * perPage : 0;
    var slice = perPage > 0 ? view.slice(start, start + perPage) : view;
    if (!slice.length) {
      body.innerHTML = '<tr><td class="empty" colspan="' + cols.length +
                       '">No matching rows</td></tr>';
    } else {
      body.innerHTML = slice.map(function (row) {
        return '<tr>' + row.map(function (cell, i) {
          var div = document.createElement('div');
          div.textContent = cell;
          return '<td' + (numeric[i] ? ' class="num"' : '') + '>' +
                 div.innerHTML + '</td>';
        }).join('') + '</tr>';
      }).join('');
    }
    var total = view.length;
    count.textContent = total + (total === 1 ? ' row' : ' rows') +
      (total !== rows.length ? ' of ' + rows.length : '');
    var pages = perPage > 0 ? Math.max(1, Math.ceil(total / perPage)) : 1;
    pageLabel.textContent = 'Page ' + (page + 1) + ' of ' + pages;
    prev.disabled = page === 0;
    next.disabled = page >= pages - 1;
  }

  document.querySelectorAll('thead th').forEach(function (th, i) {
    th.addEventListener('click', function () {
      if (sortCol === i) {
        sortDir = sortDir === 1 ? -1 : sortDir === -1 ? 0 : 1;
      } else {
        sortCol = i; sortDir = 1;
      }
      document.querySelectorAll('thead th').forEach(function (other) {
        other.removeAttribute('data-dir');
      });
      if (sortDir === 1) th.setAttribute('data-dir', 'asc');
      else if (sortDir === -1) th.setAttribute('data-dir', 'desc');
      else sortCol = -1;
      page = 0;
      apply();
    });
  });

  q.addEventListener('input', function () { page = 0; apply(); });
  prev.addEventListener('click', function () { if (page > 0) { page--; render(); } });
  next.addEventListener('click', function () { page++; render(); });
  if (sizeSelect) {
    sizeSelect.addEventListener('change', function () {
      perPage = parseInt(sizeSelect.value, 10) || 0;
      page = 0; apply();
    });
  }
  apply();
})();
"""



def _to_html_merged(table, target, title: str, include_index: bool,
                    encoding: str) -> Optional[str]:
    """Static self-contained HTML page that preserves merged cells."""
    view = _view(table, include_index)
    headers = view.headers
    head_cells = ''.join(
        f'<th>{_html.escape(_plain(h))}</th>' for h in headers
    )
    body = _html_body_with_merges(table, include_index, view)
    markup = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(title)}</title>
<style>{_HTML_STYLE}</style>
</head>
<body>
<div class="wrap">
  <h1>{_html.escape(title)}</h1>
  <p class="count">Merged cells preserved (static view).</p>
  <div class="scroll">
    <table>
      <thead><tr>{head_cells}</tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</div>
</body>
</html>
"""
    if target is None:
        return markup
    if hasattr(target, 'write'):
        target.write(markup)
        return None
    with open(target, 'w', encoding=encoding) as handle:
        handle.write(markup)
    return None


def to_html(table, target=None, title: str = 'Table', paginate: int = 25,
            include_index: bool = False, searchable: bool = True,
            encoding: str = 'utf-8') -> Optional[str]:
    """
    Write a self-contained HTML page.

    The result is one file with no external requests: the stylesheet and the
    script are inline, so it works offline and from a file:// URL. Columns are
    sortable, rows are filterable, and the table is paginated in the browser.

    ``paginate`` is the page size; 0 shows every row on one page. With no
    target the markup is returned as a string.

    Values are passed to the page as JSON data and written into the DOM as
    text, never as markup, so a cell containing HTML is displayed rather than
    interpreted.

    When the table has merged regions, a static ``rowspan``/``colspan`` table
    is written instead of the interactive grid (sort/filter would break merges).
    """
    view = _view(table, include_index)
    if view.merges:
        return _to_html_merged(table, target, title, include_index, encoding)

    header_texts = [_plain(header) for header in view.headers]
    row_texts = [list(row) for row in view.text]

    # A column is treated as numeric for sorting and alignment when every
    # non-empty cell in it is a number -- judged on the stored value, so a
    # formatted '1,234.50' or '12.5 %' still sorts as a number.
    def sort_number(raw, text):
        if isinstance(raw, bool):
            return None
        if isinstance(raw, (int, float)):
            return None if raw != raw else raw
        try:
            return float(text)
        except ValueError:
            return None

    numeric_flags = []
    for index in range(len(header_texts)):
        cells = [
            (raw_row[index], text_row[index])
            for raw_row, text_row in zip(view.raw, row_texts)
            if index < len(text_row) and text_row[index].strip()
        ]
        numeric_flags.append(
            bool(cells)
            and all(sort_number(raw, text) is not None for raw, text in cells)
        )

    keys = [
        [
            sort_number(raw_row[i], text_row[i]) if numeric_flags[i] else None
            for i in range(len(text_row))
        ]
        for raw_row, text_row in zip(view.raw, row_texts)
    ]

    payload = {
        'headers': header_texts,
        'rows': row_texts,
        'keys': keys,
        'numeric': numeric_flags,
        'perPage': max(0, int(paginate or 0)),
    }

    head_cells = ''.join(
        f'<th>{_html.escape(text)}</th>' for text in header_texts
    )
    search_box = (
        '<input id="q" type="search" placeholder="Filter rows...">'
        if searchable else '<input id="q" type="hidden">'
    )
    size_options = ''.join(
        f'<option value="{size}"'
        f'{" selected" if size == payload["perPage"] else ""}>{size} per page</option>'
        for size in (10, 25, 50, 100)
    )
    size_select = (
        f'<select id="size">{size_options}<option value="0"'
        f'{" selected" if payload["perPage"] == 0 else ""}>All rows</option></select>'
        if paginate else ''
    )

    markup = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(title)}</title>
<style>{_HTML_STYLE}</style>
</head>
<body>
<div class="wrap">
  <h1>{_html.escape(title)}</h1>
  <div class="controls">
    {search_box}
    {size_select}
    <span class="count" id="count"></span>
  </div>
  <div class="scroll">
    <table>
      <thead><tr>{head_cells}</tr></thead>
      <tbody id="body"></tbody>
    </table>
  </div>
  <div class="pager">
    <button id="prev" type="button">Previous</button>
    <button id="next" type="button">Next</button>
    <span class="page" id="pageLabel"></span>
  </div>
</div>
<script>
var DATA = {_script_safe_json(payload)};
{_HTML_SCRIPT}
</script>
</body>
</html>
"""

    if target is None:
        return markup
    if hasattr(target, 'write'):
        target.write(markup)
        return None
    with open(target, 'w', encoding=encoding) as handle:
        handle.write(markup)
    return None


_EXCEL_SPEC = re.compile(
    r'^(?P<comma>,)?(?:\.(?P<precision>\d+))?(?P<kind>[dfFeE%n]?)$'
)


def _excel_quote(text: str) -> str:
    return '"{0}"'.format(text.replace('"', '')) if text else ''


def _excel_from_spec(spec: str, is_int: bool) -> Optional[str]:
    """
    An Excel number format for a Python format spec, or None.

    Covers the common shapes -- ``',d'``, ``'.2f'``, ``',.2f'``, ``'.1%'``,
    ``'.3e'``, ``'{:,.2f}'``, ``'$ {:,.0f} MXN'`` -- so the spreadsheet shows
    what the terminal shows while the cell stays a number. Anything else
    (callables, padding, fill characters) leaves Excel's General format.
    """
    prefix = suffix = ''
    if '{' in spec:
        match = re.match(r'^([^{}]*)\{(?:0)?:?([^{}]*)\}([^{}]*)$', spec)
        if not match:
            return None
        prefix, spec, suffix = match.groups()
    match = _EXCEL_SPEC.match(spec)
    if not match:
        return None
    comma = bool(match.group('comma'))
    precision = match.group('precision')
    kind = match.group('kind')
    whole = '#,##0' if comma else '0'
    if kind in ('', 'n'):
        if precision is not None:
            return None
        body = whole if is_int else None
        if body is None and not comma:
            return None
        body = body or '#,##0.##########'
    elif kind == 'd':
        if not is_int:
            return None
        body = whole
    elif kind in ('f', 'F', '%'):
        digits = int(precision) if precision is not None else 6
        body = whole + ('.' + '0' * digits if digits else '')
        if kind == '%':
            body += '%'
    else:  # e / E
        digits = int(precision) if precision is not None else 6
        body = '0' + ('.' + '0' * digits if digits else '') + 'E+00'
    return _excel_quote(prefix) + body + _excel_quote(suffix)


def _excel_number_format(table, value, header, column_i) -> Optional[str]:
    """
    The Excel number format matching how ``compose()`` prints ``value``.

    ``int_format`` / ``float_format`` / ``leading_zeros`` first, then a
    per-column string spec in ``custom_format`` when the type has none.
    """
    is_int = isinstance(value, int)
    spec = table.int_format if is_int else table.float_format
    if spec is None and is_int and getattr(table, 'leading_zeros', None):
        return '0' * int(table.leading_zeros)
    if spec is None:
        custom = getattr(table, 'custom_format', None)
        if isinstance(custom, dict):
            spec = custom.get(header)
            if spec is None:
                spec = custom.get(column_i)
    if not isinstance(spec, str):
        return None
    try:
        return _excel_from_spec(spec, is_int)
    except (TypeError, ValueError):
        return None


def to_excel(table, path, sheet_name: str = 'Sheet1',
             include_index: bool = False, autofit: bool = True,
             freeze_header: bool = True) -> None:
    """
    Write an .xlsx workbook.

    Numbers are written as numbers rather than text, so the spreadsheet can
    compute with them, and are right-aligned to match. Rows follow the
    displayed order (``sort_by``, ``row_filter``), ``hide_columns`` are left
    out, simple ``int_format`` / ``float_format`` / ``custom_format`` specs
    become the cells' Excel number format, and every other cell holds the
    text ``compose()`` shows. The header row is bold
    and frozen, and column widths are fitted to the content.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:  # pragma: no cover - depends on the environment
        raise ImportError(
            'writing Excel requires openpyxl. '
            'Install it with: pip install flexablelib[excel]'
        )

    view = _view(table, include_index)
    headers, rows, texts = view.headers, view.raw, view.text
    data_offset = 1 if include_index else 0
    data_headers = list(table.headers)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='4338CA')
    for column_index, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=1, column=column_index, value=_plain(header))
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='left', vertical='center')

    for row_index, (row, text_row) in enumerate(zip(rows, texts), start=2):
        for column_index, value in enumerate(row, start=1):
            # Keep real numbers numeric so formulas and charts work, with the
            # table's number format carried over when Excel can express it;
            # anything else goes in as the text compose() shows.
            number_format = None
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                written = text_row[column_index - 1]
            else:
                written = value
                header_i = column_index - 1 - data_offset
                if header_i >= 0:
                    number_format = _excel_number_format(
                        table, value,
                        data_headers[header_i] if header_i < len(data_headers)
                        else None,
                        header_i,
                    )
            cell = worksheet.cell(row=row_index, column=column_index,
                                  value=written)
            if isinstance(written, (int, float)) and not isinstance(written, bool):
                cell.alignment = Alignment(horizontal='right')
                if number_format:
                    cell.number_format = number_format

    if autofit:
        for column_index, header in enumerate(headers, start=1):
            longest = len(_plain(header))
            for row in texts:
                if column_index - 1 < len(row):
                    longest = max(longest, len(row[column_index - 1]))
            # A little padding, and a ceiling so one long cell cannot push a
            # column off the screen.
            worksheet.column_dimensions[get_column_letter(column_index)].width = (
                min(60, longest + 2)
            )

    if freeze_header:
        worksheet.freeze_panes = 'A2'

    # Mirror flexablelib merged regions as Excel merged cells. Table coordinates
    # ignore the optional index column and the header row lives on Excel row 1.
    col_offset = 2 if include_index else 1
    for region in view.merges:
        start_row = region.first_row + 2
        end_row = region.last_row + 2
        start_col = region.first_column + col_offset
        end_col = region.last_column + col_offset
        top_left = worksheet.cell(row=start_row, column=start_col)
        if region.value is not None:
            top_left.value = _plain(region.value)
        top_left.alignment = Alignment(
            horizontal={'l': 'left', 'r': 'right', 'c': 'center'}.get(
                region.align, 'center'),
            vertical='center',
            wrap_text=True,
        )
        worksheet.merge_cells(
            start_row=start_row, start_column=start_col,
            end_row=end_row, end_column=end_col,
        )
        spec = _effective_region_color(table, region)
        if spec:
            from openpyxl.styles import Font as _Font
            bg = background_hex(spec)
            fg = foreground_hex(spec)
            if bg:
                fill = PatternFill('solid', fgColor=bg)
                for r in range(start_row, end_row + 1):
                    for c in range(start_col, end_col + 1):
                        worksheet.cell(row=r, column=c).fill = fill
            if fg:
                top_left.font = _Font(color=fg, bold='bold' in str(spec).lower())

    workbook.save(path)


def to_rst(table, include_index: bool = False) -> str:
    """
    Write a reStructuredText grid table.

    Uses ``+---+`` / ``|`` grid syntax so column alignment survives docutils.
    Newlines inside cells become spaces (RST grid cells are single-line).
    """
    from .fast import visible_width, pad_to_width

    view = _view(table, include_index)
    headers = view.headers
    if not headers:
        return ''

    def cell(value):
        return _plain(value).replace('\n', ' ')

    header_texts = [cell(h) for h in headers]
    row_texts = [[cell(v) for v in row] for row in view.text]
    widths = [
        max(
            [visible_width(header_texts[i])]
            + [visible_width(row[i]) for row in row_texts if i < len(row)]
            + [1]
        )
        for i in range(len(header_texts))
    ]

    def rule(char='-'):
        return '+' + '+'.join(char * (w + 2) for w in widths) + '+'

    def line(cells):
        parts = [
            ' ' + pad_to_width(text, widths[i], 'l') + ' '
            for i, text in enumerate(cells)
        ]
        return '|' + '|'.join(parts) + '|'

    out = [rule('-'), line(header_texts), rule('=')]
    for row in row_texts:
        out.append(line(row))
        out.append(rule('-'))
    return '\n'.join(out)


def to_asciidoc(table, include_index: bool = False) -> str:
    """
    Write an AsciiDoc table (``|===`` delimited).

    Column widths are left to the AsciiDoc processor; cells with newlines are
    flattened to spaces so a single logical row stays one source line.
    """
    view = _view(table, include_index)
    headers = view.headers
    if not headers:
        return ''

    def cell(value):
        return _plain(value).replace('|', '\\|').replace('\n', ' ')

    lines = ['|===', '| ' + ' | '.join(cell(h) for h in headers)]
    for row in view.text:
        lines.append('| ' + ' | '.join(cell(v) for v in row))
    lines.append('|===')
    return '\n'.join(lines)


def to_latex(table, include_index: bool = False) -> str:
    """
    Write a LaTeX ``tabular`` environment.

    Alignment letters follow the table's column alignments when available
    (``l`` / ``c`` / ``r``); otherwise every column is left-aligned. Special
    TeX characters in cells are escaped.
    """
    view = _view(table, include_index)
    headers, rows = view.headers, view.raw
    if not headers:
        return ''

    def escape_tex(value):
        text = _plain(value).replace('\n', ' ')
        out = []
        for ch in text:
            if ch == '\\':
                out.append(r'\textbackslash{}')
            elif ch == '&':
                out.append(r'\&')
            elif ch == '%':
                out.append(r'\%')
            elif ch == '$':
                out.append(r'\$')
            elif ch == '#':
                out.append(r'\#')
            elif ch == '_':
                out.append(r'\_')
            elif ch == '{':
                out.append(r'\{')
            elif ch == '}':
                out.append(r'\}')
            elif ch == '~':
                out.append(r'\textasciitilde{}')
            elif ch == '^':
                out.append(r'\textasciicircum{}')
            elif ch == '|':
                # Under the default OT1 font encoding these three print as
                # an em dash and inverted punctuation.
                out.append(r'\textbar{}')
            elif ch == '<':
                out.append(r'\textless{}')
            elif ch == '>':
                out.append(r'\textgreater{}')
            else:
                out.append(ch)
        return ''.join(out)

    aligns = []
    for i, header in enumerate(headers):
        code = 'l'
        try:
            values = [row[i] for row in rows if i < len(row)]
            code = _markdown_alignment(table, header, i, values)
        except Exception:
            code = 'l'
        if code not in ('l', 'c', 'r'):
            code = 'l'
        aligns.append(code)

    colspec = ''.join(aligns)
    lines = [
        r'\begin{tabular}{' + colspec + '}',
        r'\hline',
        ' & '.join(escape_tex(h) for h in headers) + r' \\',
        r'\hline',
    ]
    for row in view.text:
        lines.append(' & '.join(escape_tex(v) for v in row) + r' \\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    return '\n'.join(lines)
