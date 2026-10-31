"""
Render benchmark against the other table libraries.

The target is the specific job this package does: turning tabular data already
in memory into formatted text. Run from the repository root:

    python3 tools/benchmark.py           # C extension, if built
    python3 tools/benchmark.py --pure    # pure-Python fallback
"""

import random
import sys
import time

if '--pure' in sys.argv:
    # Measure the fallback every install has, compiler or not.
    sys.modules['flexablelib._speedups'] = None

from flexablelib import Table  # noqa: E402
from flexablelib.fast import implementation  # noqa: E402

SHAPES = [(100, 4), (2000, 4), (10000, 6)]
REPEATS = 5


def make_rows(row_count, column_count):
    random.seed(3)
    cities = ['Oslo', 'Lima', 'Tokyo', 'Berlin', 'Cairo']
    rows = []
    for index in range(row_count):
        row = [f'item{index}', random.choice(cities),
               round(random.uniform(0, 1000), 2), index]
        while len(row) < column_count:
            row.append(round(random.uniform(0, 100), 3))
        rows.append(row[:column_count])
    return rows


def headers_for(column_count):
    names = ['name', 'city', 'value', 'n', 'extra1', 'extra2', 'extra3']
    return names[:column_count]


def fastest(callable_, repeats=REPEATS):
    best = float('inf')
    for _ in range(repeats):
        start = time.perf_counter()
        callable_()
        best = min(best, time.perf_counter() - start)
    return best


def contenders(rows, headers):
    """Every library that is installed, as name -> zero-argument callable."""
    entries = {}

    def build_flexablelib():
        table = Table()
        for index, header in enumerate(headers):
            table.add_column(header, [row[index] for row in rows])
        return str(table)

    entries['flexablelib'] = build_flexablelib

    try:
        from tabulate import tabulate
        entries['tabulate'] = lambda: tabulate(rows, headers=headers,
                                               tablefmt='grid')
    except ImportError:
        pass

    try:
        from prettytable import PrettyTable

        def build_prettytable():
            table = PrettyTable()
            table.field_names = headers
            for row in rows:
                table.add_row(row)
            return table.get_string()

        entries['prettytable'] = build_prettytable
    except ImportError:
        pass

    try:
        import io

        from rich.console import Console
        from rich.table import Table as RichTable

        def build_rich():
            table = RichTable()
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*[str(value) for value in row])
            console = Console(file=io.StringIO(), width=200,
                              color_system=None, force_terminal=False)
            console.print(table)
            return console.file.getvalue()

        entries['rich'] = build_rich
    except ImportError:
        pass

    try:
        import pandas

        frame = pandas.DataFrame(rows, columns=headers)
        entries['pandas .to_string()'] = frame.to_string
    except ImportError:
        pass

    return entries


def versions():
    """Installed version of every contender, for the record."""
    from importlib import metadata
    found = []
    for name in ('flexablelib', 'tabulate', 'prettytable', 'rich', 'pandas'):
        try:
            found.append(f'{name} {metadata.version(name)}')
        except metadata.PackageNotFoundError:
            pass
    return ', '.join(found)


def main():
    print(f'backend: {implementation()}')
    print(f'versions: {versions()}\n')
    for row_count, column_count in SHAPES:
        rows = make_rows(row_count, column_count)
        headers = headers_for(column_count)
        results = {name: fastest(fn)
                   for name, fn in contenders(rows, headers).items()}

        baseline = results['flexablelib']
        print(f'{row_count} rows x {column_count} columns')
        for name, seconds in sorted(results.items(), key=lambda kv: kv[1]):
            if name == 'flexablelib':
                marker = '<-- this package'
            else:
                marker = f'{seconds / baseline:.2f}x of flexablelib'
            print(f'  {name:<22} {seconds * 1000:8.1f} ms   {marker}')
        print()


if __name__ == '__main__':
    main()
