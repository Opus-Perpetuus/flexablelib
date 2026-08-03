"""
DATA READERS

Builds tables from external sources. Reached through the Table class
methods rather than called directly::

    Table.from_csv('sales.csv')
    Table.from_pandas(dataframe)
    Table.from_html(markup)
    Table.from_excel('report.xlsx', sheet='Q3')
    Table.from_dicts([{'name': 'Ann', 'age': 30}])

CSV, HTML and dict input need nothing beyond the standard library. Only pandas
and Excel require their respective packages, and only when actually used, so
the base install stays dependency-free.

A note on number parsing. Text formats deliver everything as strings, and a
column of strings is left-aligned, so an unparsed CSV of numbers comes out
looking wrong. The readers therefore convert numeric-looking text by default.
That normalises the representation -- '0.0' is read as the float 0.0 and
renders as '0.0' only because the repr happens to agree, while '1.50' becomes
1.5. Where the exact text matters more than the alignment, pass
``parse_numbers=False`` and everything stays a string. This is the tradeoff
tabulate gets wrong in their #299.
"""

import csv as _csv
import io as _io
import re
from html.parser import HTMLParser
from typing import Any, Dict, Iterable, List, Optional, Sequence

# Numeric text that should become a number. Deliberately strict: no leading
# '+', no whitespace, no thousands separators, and no leading zeros, so
# identifiers survive as text.
#
# Leading zeros are the giveaway that a value is an identifier rather than a
# quantity -- postal codes, product references, zero-padded ids. Converting
# '007' to 7 silently destroys data that cannot be recovered from the table,
# so anything with a redundant leading zero stays a string. '0' and '0.5' are
# of course still numbers.
_INT_TEXT = re.compile(r'^-?(?:0|[1-9]\d*)$')
_FLOAT_TEXT = re.compile(r'^-?(?:(?:0|[1-9]\d*)\.\d*|\.\d+)$')
_EXPONENT_TEXT = re.compile(
    r'^-?(?:(?:0|[1-9]\d*)(?:\.\d*)?|\.\d+)[eE][-+]?\d+$'
)


def parse_value(text: Any, parse_numbers: bool = True) -> Any:
    """
    Convert a string to int or float when it clearly is one.

    Leaves everything else untouched, including empty strings, which stay
    empty rather than becoming a missing value -- that decision belongs to the
    caller, not the parser.
    """
    if not parse_numbers or not isinstance(text, str):
        return text
    stripped = text.strip()
    if not stripped:
        return text
    if _INT_TEXT.match(stripped):
        try:
            return int(stripped)
        except ValueError:
            return text
    if _FLOAT_TEXT.match(stripped) or _EXPONENT_TEXT.match(stripped):
        try:
            return float(stripped)
        except ValueError:
            return text
    return text


def _new_table(table_class, headers: Sequence[str], rows: Iterable[Sequence],
               parse_numbers: bool, **options):
    """
    Assemble a Table from headers and rows. Shared by every reader.

    Built column by column, each with its name and data together. Declaring
    the empty columns first and then adding rows loses every header but the
    first, because appending a row wider than the data seen so far triggers
    the automatic column naming.
    """
    table = table_class(**options)
    rows = [list(row) for row in rows]
    for index, header in enumerate(headers):
        column = [
            parse_value(row[index], parse_numbers) if index < len(row) else ''
            for row in rows
        ]
        table.add_column(str(header), column)
    return table


def from_records(table_class, rows: Iterable[Sequence],
                 headers: Optional[Sequence[str]] = None,
                 parse_numbers: bool = True, **options):
    """
    Build from a sequence of rows.

    With no headers, the first row is used as the header row.
    """
    rows = [list(row) for row in rows]
    if headers is None:
        if not rows:
            return table_class(**options)
        headers, rows = rows[0], rows[1:]
    return _new_table(table_class, headers, rows, parse_numbers, **options)


def from_dicts(table_class, records: Iterable[Dict[str, Any]],
               parse_numbers: bool = False, **options):
    """
    Build from a sequence of mappings, one per row.

    Columns are the union of every key, in the order first encountered, so
    records with differing keys still line up. Missing keys become the table's
    missing value.

    Number parsing is off by default here: a dict already carries typed values,
    so there is nothing to parse and converting would only risk mangling
    strings that happen to look numeric.
    """
    records = list(records)
    headers = []
    for record in records:
        for key in record:
            if key not in headers:
                headers.append(key)
    rows = [[record.get(key, '') for key in headers] for record in records]
    return _new_table(table_class, headers, rows, parse_numbers, **options)


def from_csv(table_class, source, parse_numbers: bool = True,
             has_header: bool = True, delimiter: str = ',',
             encoding: str = 'utf-8', **options):
    """
    Build from a CSV file path, or any open text handle.

    With ``has_header`` false, columns are named automatically.
    """
    if hasattr(source, 'read'):
        reader = _csv.reader(source, delimiter=delimiter)
        rows = [row for row in reader]
    else:
        with open(source, 'r', newline='', encoding=encoding) as handle:
            rows = [row for row in _csv.reader(handle, delimiter=delimiter)]

    if not rows:
        return table_class(**options)
    if has_header:
        return _new_table(table_class, rows[0], rows[1:], parse_numbers,
                          **options)
    width = max(len(row) for row in rows)
    headers = [f'column {i + 1}' for i in range(width)]
    return _new_table(table_class, headers, rows, parse_numbers, **options)


class _TableExtractor(HTMLParser):
    """
    Pulls rows out of HTML <table> elements.

    Written against the standard library rather than lxml so that reading HTML
    needs no dependency. It handles the structure tables actually use -- thead,
    tbody, th, td, nested inline markup -- but it is not a general HTML
    sanitiser and does not evaluate scripts or styles.

    Nested tables are not descended into; the cell keeps the text of the inner
    table flattened, which is almost always what a reader wants.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: List[List[List[str]]] = []
        self._table_depth = 0
        self._current_table = None
        self._current_row = None
        self._current_cell = None
        self._header_flags: List[bool] = []
        self._row_is_header = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self._table_depth += 1
            if self._table_depth == 1:
                self._current_table = []
                self._header_flags = []
            return
        if self._table_depth != 1:
            return
        if tag == 'tr':
            self._current_row = []
            self._row_is_header = False
        elif tag in ('td', 'th'):
            self._current_cell = []
            if tag == 'th':
                self._row_is_header = True

    def handle_endtag(self, tag):
        if tag == 'table':
            if self._table_depth == 1 and self._current_table is not None:
                self.tables.append(self._current_table)
                self._current_table = None
            self._table_depth = max(0, self._table_depth - 1)
            return
        if self._table_depth != 1:
            return
        if tag in ('td', 'th') and self._current_cell is not None:
            text = ''.join(self._current_cell)
            # Collapse whitespace the way a browser would render it.
            cleaned = ' '.join(text.split())
            if self._current_row is not None:
                self._current_row.append(cleaned)
            self._current_cell = None
        elif tag == 'tr' and self._current_row is not None:
            self._current_table.append(self._current_row)
            self._header_flags.append(self._row_is_header)
            self._current_row = None

    def handle_data(self, data):
        if self._current_cell is not None:
            self._current_cell.append(data)

    def header_row_index(self) -> Optional[int]:
        """Index of the first row made of <th> cells, if there is one."""
        for index, is_header in enumerate(self._header_flags):
            if is_header:
                return index
        return None


def from_html(table_class, source, index: int = 0, parse_numbers: bool = True,
              encoding: str = 'utf-8', **options):
    """
    Build from an HTML table.

    ``source`` may be markup, a file path, or an open handle. ``index``
    selects which table in the document to read when there is more than one.

    Uses the standard library's HTML parser, so this needs no dependency.
    A row of <th> cells becomes the header; otherwise the first row does.
    """
    if hasattr(source, 'read'):
        markup = source.read()
    elif isinstance(source, str) and '<' in source:
        markup = source
    else:
        with open(source, 'r', encoding=encoding) as handle:
            markup = handle.read()

    extractor = _TableExtractor()
    extractor.feed(markup)
    extractor.close()

    if not extractor.tables:
        raise ValueError('no <table> element found')
    if index >= len(extractor.tables):
        raise IndexError(
            f'table index {index} out of range; '
            f'the document has {len(extractor.tables)}'
        )

    rows = extractor.tables[index]
    if not rows:
        return table_class(**options)

    header_index = extractor.header_row_index() if index == 0 else None
    if header_index is not None and header_index < len(rows):
        headers = rows[header_index]
        body = rows[:header_index] + rows[header_index + 1:]
    else:
        headers, body = rows[0], rows[1:]

    # Ragged rows are padded so every row reaches the column count.
    width = max([len(headers)] + [len(row) for row in body]) if body else len(headers)
    headers = list(headers) + [f'column {i + 1}' for i in range(len(headers), width)]
    body = [list(row) + [''] * (width - len(row)) for row in body]

    return _new_table(table_class, headers, body, parse_numbers, **options)


def from_pandas(table_class, dataframe, include_index: bool = False, **options):
    """
    Build from a pandas DataFrame or Series.

    Values are taken as they are; pandas has already typed them, so no parsing
    happens. NaN, NaT and None become the table's missing sentinel, so they
    render as ``missing_value`` and leave the column's type alone -- a numeric
    column with gaps stays numeric and stays right-aligned. Letting the float
    NaN through instead would print 'nan' in the cell, which is tabulate #316.
    """
    try:
        import pandas
    except ImportError:  # pragma: no cover - depends on the environment
        raise ImportError(
            'reading a DataFrame requires pandas. '
            'Install it with: pip install prettyTables[pandas]'
        )

    if isinstance(dataframe, pandas.Series):
        dataframe = dataframe.to_frame()

    frame = dataframe.reset_index() if include_index else dataframe

    # Column by column, name and data together. Declaring the columns empty
    # and then adding rows loses every header but the first.
    table = table_class(**options)
    for name in frame.columns:
        # None, not '', for absent values: an empty string is a legitimate
        # string value, so it would make the column textual and left-align
        # the numbers. None is what the table treats as missing.
        table.add_column(str(name), [
            table.missing if _is_missing(value, pandas) else value
            for value in frame[name].tolist()
        ])
    return table


def _is_missing(value, pandas) -> bool:
    """True for any of the several things pandas uses to mean 'no value'."""
    try:
        result = pandas.isna(value)
    except (TypeError, ValueError):
        return False
    # isna on a list-like returns an array rather than a bool. A cell holding
    # a list is not itself missing, so anything non-boolean answers False.
    return result if isinstance(result, bool) else False


def from_excel(table_class, path, sheet=None, has_header: bool = True,
               parse_numbers: bool = False, **options):
    """
    Build from a worksheet in an .xlsx file.

    ``sheet`` takes a name or a zero-based index; the active sheet is used by
    default. Cells arrive already typed from the workbook, so parsing is off.
    """
    try:
        from openpyxl import load_workbook
    except ImportError:  # pragma: no cover - depends on the environment
        raise ImportError(
            'reading Excel requires openpyxl. '
            'Install it with: pip install prettyTables[excel]'
        )

    workbook = load_workbook(filename=path, read_only=True, data_only=True)
    try:
        if sheet is None:
            worksheet = workbook.active
        elif isinstance(sheet, int):
            worksheet = workbook[workbook.sheetnames[sheet]]
        else:
            worksheet = workbook[sheet]

        rows = [
            ['' if cell is None else cell for cell in row]
            for row in worksheet.iter_rows(values_only=True)
        ]
    finally:
        workbook.close()

    if not rows:
        return table_class(**options)
    if has_header:
        return _new_table(table_class, rows[0], rows[1:], parse_numbers,
                          **options)
    width = max(len(row) for row in rows)
    headers = [f'column {i + 1}' for i in range(width)]
    return _new_table(table_class, headers, rows, parse_numbers, **options)
