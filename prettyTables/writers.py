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
from typing import Any, List, Optional, Sequence

from .fast import strip_ansi
from .options import FLT_FILTER, INT_FILTER
from .utils import IndexCounter, ValuePlacer


def _plain(value: Any) -> str:
    """
    Cell text with any colour removed.

    Every writer here targets a format that carries its own styling, so ANSI
    sequences would be literal noise -- and in CSV they would corrupt the
    field outright.
    """
    return strip_ansi(str(value)) if value is not None else ''


def _script_json(payload) -> str:
    """
    JSON safe to embed inside a ``<script>`` element.

    An HTML parser ends a script at the first ``</script``, wherever it
    appears -- quoting means nothing to it, so a cell holding that text closed
    the element early, dropped the rest of the program into the page as
    visible text, and let the remainder of the cell be parsed as real markup.

    Escaping the three characters that can start a tag or an entity avoids it.
    ``\\u003c`` and friends are ordinary JSON escapes, so the value the page
    receives is unchanged.
    """
    return (
        json.dumps(payload)
        .replace('&', '\\u0026')
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
    )


def _table_data(table, include_index: bool):
    """
    (headers, rows) honouring the index setting, with the sentinels resolved.

    Storage keeps two placeholder objects that only the console renderer knew
    how to read: one shared ``IndexCounter`` standing in for the index column,
    and a ``ValuePlacer`` marking an absent cell. Handed to a writer as they
    are, they exported their own repr --
    ``<prettyTables.utils.ValuePlacer object at 0x7f...>`` -- into CSV,
    Markdown, HTML and Excel alike, and in HTML the repr also made a numeric
    column look textual and lose its alignment.

    Resolving them here fixes every writer at once, because they all come
    through this function. The index is computed the same way the renderer
    computes it, from ``index_start`` and ``index_step``.
    """
    if include_index:
        headers = [str(header) for header in table.internal_headers]
        rows = table.internal_rows
    else:
        headers = [str(header) for header in table.headers]
        rows = table.rows

    missing = table.missing_value
    start, step = table.index_start, table.index_step
    numbering = include_index and table.show_index

    resolved = []
    for position, row in enumerate(rows):
        cells = []
        for column, cell in enumerate(row):
            if numbering and column == 0 and isinstance(cell, IndexCounter):
                cells.append(start + position * step)
            elif isinstance(cell, ValuePlacer):
                cells.append(missing)
            else:
                cells.append(cell)
        resolved.append(cells)
    return headers, resolved


def to_records(table, include_index: bool = False) -> List[dict]:
    """The table as a list of dicts, one per row."""
    headers, rows = _table_data(table, include_index)
    return [dict(zip(headers, row)) for row in rows]


def to_simple_html(table, include_index: bool = False) -> str:
    """
    A bare HTML ``<table>`` for notebook ``_repr_html_`` hooks.

    No document chrome, scripts or pagination -- just thead/tbody so Jupyter
    and friends can embed the table in a cell output.
    """
    headers, rows = _table_data(table, include_index)
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
    for row in rows:
        parts.append('<tr>')
        for cell in row:
            parts.append(
                '<td>{0}</td>'.format(_html.escape(_plain(cell)))
            )
        parts.append('</tr>')
    parts.append('</tbody></table>')
    return ''.join(parts)


def to_csv(table, target=None, include_index: bool = False,
           delimiter: str = ',', encoding: str = 'utf-8') -> Optional[str]:
    """
    Write CSV.

    With no target, returns the CSV as a string; otherwise writes to the given
    path or open handle and returns None.
    """
    headers, rows = _table_data(table, include_index)

    def dump(handle):
        writer = _csv.writer(handle, delimiter=delimiter)
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

    headers, rows = _table_data(table, include_index)
    if not headers:
        return ''

    def cell(value):
        return _plain(value).replace('|', '\\|').replace('\n', ' ')

    header_texts = [cell(header) for header in headers]
    row_texts = [[cell(value) for value in row] for row in rows]

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
      var nx = parseFloat(x), ny = parseFloat(y);
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
    """
    headers, rows = _table_data(table, include_index)
    header_texts = [_plain(header) for header in headers]
    row_texts = [[_plain(cell) for cell in row] for row in rows]

    # A column is treated as numeric for sorting and alignment when every
    # non-empty cell in it parses as a number.
    numeric_flags = []
    for index in range(len(header_texts)):
        values = [row[index] for row in row_texts
                  if index < len(row) and row[index].strip()]
        numeric = bool(values)
        for value in values:
            try:
                float(value)
            except ValueError:
                numeric = False
                break
        numeric_flags.append(numeric)

    payload = {
        'headers': header_texts,
        'rows': row_texts,
        'numeric': numeric_flags,
        'perPage': max(0, int(paginate)),
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
var DATA = {_script_json(payload)};
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


def to_excel(table, path, sheet_name: str = 'Sheet1',
             include_index: bool = False, autofit: bool = True,
             freeze_header: bool = True) -> None:
    """
    Write an .xlsx workbook.

    Numbers are written as numbers rather than text, so the spreadsheet can
    compute with them, and are right-aligned to match. The header row is bold
    and frozen, and column widths are fitted to the content.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:  # pragma: no cover - depends on the environment
        raise ImportError(
            'writing Excel requires openpyxl. '
            'Install it with: pip install prettyTables[excel]'
        )

    headers, rows = _table_data(table, include_index)

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

    for row_index, row in enumerate(rows, start=2):
        for column_index, value in enumerate(row, start=1):
            # Keep real numbers numeric so formulas and charts work; anything
            # else goes in as its plain text.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                written = _plain(value)
            else:
                written = value
            cell = worksheet.cell(row=row_index, column=column_index,
                                  value=written)
            if isinstance(written, (int, float)) and not isinstance(written, bool):
                cell.alignment = Alignment(horizontal='right')

    if autofit:
        for column_index, header in enumerate(headers, start=1):
            longest = len(_plain(header))
            for row in rows:
                if column_index - 1 < len(row):
                    longest = max(longest, len(_plain(row[column_index - 1])))
            # A little padding, and a ceiling so one long cell cannot push a
            # column off the screen.
            worksheet.column_dimensions[get_column_letter(column_index)].width = (
                min(60, longest + 2)
            )

    if freeze_header:
        worksheet.freeze_panes = 'A2'

    workbook.save(path)
