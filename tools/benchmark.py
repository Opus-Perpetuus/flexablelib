"""
Render benchmark against the other table libraries.

The target is the specific job this package does: turning tabular data already
in memory into formatted text. Run from the repository root:

    python3 tools/benchmark.py
"""

import random
import time

from prettyTables import Table
from prettyTables.fast import implementation

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

    def build_prettytables():
        table = Table()
        for index, header in enumerate(headers):
            table.add_column(header, [row[index] for row in rows])
        return str(table)

    entries['prettyTables'] = build_prettytables

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
        import pandas

        frame = pandas.DataFrame(rows, columns=headers)
        entries['pandas .to_string()'] = frame.to_string
    except ImportError:
        pass

    return entries


def main():
    print(f'backend: {implementation()}\n')
    for row_count, column_count in SHAPES:
        rows = make_rows(row_count, column_count)
        headers = headers_for(column_count)
        results = {name: fastest(fn)
                   for name, fn in contenders(rows, headers).items()}

        baseline = results['prettyTables']
        print(f'{row_count} rows x {column_count} columns')
        for name, seconds in sorted(results.items(), key=lambda kv: kv[1]):
            if name == 'prettyTables':
                marker = '<-- this package'
            else:
                marker = f'{seconds / baseline:.2f}x of prettyTables'
            print(f'  {name:<22} {seconds * 1000:8.1f} ms   {marker}')
        print()


if __name__ == '__main__':
    main()
