"""
Regenerate the README feature gallery (docs/img/*.png).

Every image is rendered from the current source tree, so the README never
shows output the library no longer produces. Needs Pillow (dev only):

    pip install pillow
    python3 tools/readme_gallery.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

from flexablelib import Table  # noqa: E402
from text_to_png import render  # noqa: E402

OUT = ROOT / 'docs' / 'img'

SERVICES = [
    ['api-gateway', 'eu-west-1', 99.982, 1240],
    ['auth', 'us-east-1', 99.9, 312],
    ['billing', 'us-east-1', 98.75, 87],
    ['search', 'ap-south-1', 100.0, 4410],
]
HEADERS = ['Service', 'Region', 'Uptime %', 'RPS']


def base(style='rounded'):
    table = Table(rows=[list(r) for r in SERVICES], headers=list(HEADERS))
    table.style_name = style
    table.use_colors = True
    return table


def quickstart():
    table = base('rounded')
    table.header_color = 'bold cyan'
    table.border_color = 'grey'
    table.color_rule = lambda value, row, column: (
        'red' if column == 'Uptime %' and value < 99.5 else None
    )
    return str(table)


def styles():
    out = []
    for name in ('modern', 'rounded', 'pretty_grid', 'psql', 'markdown', 'blocks'):
        table = Table(rows=[['Oslo', 7.25], ['Lima', 19.5]],
                      headers=['City', 'Temp'])
        table.style_name = name
        table.use_colors = True
        if name == 'blocks':
            table.header_color = 'bold white on blue'
            table.zebra = ('', 'on grey23')
        out.append(f'{name}\n{table}')
    return '\n\n'.join(out)


def border_text():
    table = base('modern')
    table.border_color = 'blue'
    table.border_text(' Production ', where='top', color='bold yellow')
    table.border_text(' 4 services ', where='bottom', color='cyan',
                      offset=None, align='right')
    return str(table)


def merges():
    table = Table(
        rows=[['Q1', 'North', 120, 135], ['', 'South', 98, 101],
              ['Q2', 'North', 140, 152], ['', 'South', 110, 99]],
        headers=['Quarter', 'Zone', 'Plan', 'Actual'])
    table.style_name = 'pretty_grid'
    table.use_colors = True
    table.merge_cells(0, 0, last_row=1)
    table.merge_cells(2, 0, last_row=3)
    table.header_color = 'bold'
    return str(table)


def decimals():
    table = Table(rows=[['pi', 3.14159], ['big', 12345.5], ['tiny', 0.0001],
                        ['neg', -42.0], ['sci', 6.02e23]],
                  headers=['Name', 'Value'])
    table.style_name = 'rounded'
    table.use_colors = True
    return str(table)


def themes():
    out = []
    for name in ('dark', 'ocean', 'solarized', 'report'):
        table = base()
        table.apply_theme(name)
        table.use_colors = True
        table.title = f'apply_theme({name!r})'
        out.append(str(table))
    return '\n\n'.join(out)


def zebra_footer():
    rows = [list(r) for r in SERVICES] + [['Total', '4 regions', 99.658, 6049]]
    table = Table(rows=rows, headers=list(HEADERS))
    table.style_name = 'rounded'
    table.use_colors = True
    table.header_color = 'bold'
    table.zebra = ('', 'on grey23')
    table.footer_rows = 1
    table.footer_color = 'bold'
    table.caption = 'source: status page, last 30 days'
    return str(table)


GALLERY = {
    'quickstart': quickstart,
    'styles': styles,
    'border_text': border_text,
    'merges': merges,
    'decimals': decimals,
    'themes': themes,
    'zebra_footer': zebra_footer,
}


def main():
    os.environ.pop('NO_COLOR', None)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, build in GALLERY.items():
        render(build(), OUT / f'{name}.png')


if __name__ == '__main__':
    main()
