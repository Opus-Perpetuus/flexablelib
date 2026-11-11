#!/usr/bin/env python3
"""
A complete terminal dashboard built only with flexablelib.

    python examples/dashboard.py                    # one frame, terminal size
    python examples/dashboard.py --width 120 --height 40 --theme neon
    python examples/dashboard.py --live 10          # redraw 10 times, 1 s apart
    python examples/dashboard.py --no-color --border ascii

Pieces: Screen (sticky header and footer), a bordered Grid with column
widths, a row-spanning sidebar and cell titles, KPI cards, a coloured table
with merged cells, progress bars, sparklines, a bar chart and a log.
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))

from flexablelib import (BarChart, Card, Grid, GridCell, KeyHints,  # noqa
                         Live, LogView, ProgressBar, Screen, Sparkline,
                         StatusBar, Table, Text)

THEME_ACCENTS = {
    'ocean': ('#7dc3ff', 'black on #7dc3ff', '#5f87af'),
    'neon': ('#ff5fd7', 'black on #ff5fd7', '#af5fff'),
    'forest': ('#87d787', 'black on #87d787', '#5f875f'),
    'ember': ('#ffaf5f', 'black on #ffaf5f', '#af5f00'),
    'midnight': ('#8787ff', 'white on #303070', '#5f5f87'),
    'dark': ('#d0d0d0', 'black on #d0d0d0', '#6c6c6c'),
    'mono': (None, 'reverse', None),
}


def wave(tick, n, base, amp, phase=0.0):
    return [round(base + amp * math.sin((i + tick) / 2.3 + phase) +
                  amp * 0.4 * math.sin((i + tick) * 1.7 + phase), 1)
            for i in range(n)]


def sales_table(theme, colors):
    t = Table(headers=['Región', 'Tienda', 'Ventas', 'Δ %', 'Estado'])
    rows = [
        ['Norte', 'Monterrey', 18250.5, 12.4, 'OK'],
        ['Norte', 'Saltillo', 9120.0, -3.1, 'Revisar'],
        ['Centro', 'CDMX', 25400.75, 8.9, 'OK'],
        ['Centro', 'Puebla', 7310.2, 1.2, 'OK'],
        ['Sur', 'Mérida', 6890.0, -7.5, 'Alerta'],
        ['Sur', 'Oaxaca', 4210.4, 2.0, 'OK'],
    ]
    for row in rows:
        t.add_row(row)
    t.apply_theme(theme)
    t.style_name = 'single'
    t.use_colors = colors
    t.float_format = ',.1f'
    t.expand_to_window = True
    t.merge_cells(0, 0, last_row=1)
    t.merge_cells(2, 0, last_row=3)
    t.merge_cells(4, 0, last_row=5)
    t.color_rule = lambda value, row, column: (
        ('red' if value < 0 else 'green') if column == 'Δ %' else
        {'OK': 'green', 'Revisar': 'yellow', 'Alerta': 'bold red'}.get(value)
        if column == 'Estado' else None)
    t.column_priority = {'Estado': 2, 'Tienda': 3}
    t.card_options = {'min_width': 24, 'fields': ['Ventas', 'Δ %']}
    return t


def build(theme='ocean', border='rounded', colors=True, tick=0):
    accent, bar_color, border_color = THEME_ACCENTS.get(
        theme, THEME_ACCENTS['ocean'])
    cpu = wave(tick, 40, 55, 25)
    mem = wave(tick, 40, 62, 8, 1.0)
    net = wave(tick, 40, 40, 30, 2.0)

    kpis = [
        Card(title='Ventas hoy', fields={'MXN': '$71,182', 'vs ayer': '+6.2%'},
             field_columns=2, theme=theme, use_colors=colors,
             value_colors={'vs ayer': 'green'}),
        Card(title='Pedidos', fields={'Total': 1284, 'Abiertos': 37},
             field_columns=2, theme=theme, use_colors=colors),
        Card(title='Clientes', fields={'Activos': 942, 'Nuevos': 58},
             field_columns=2, theme=theme, use_colors=colors),
        Card(title='Ticket', fields={'Prom.': '$554', 'Máx.': '$9,870'},
             field_columns=2, theme=theme, use_colors=colors),
    ]
    menu_items = ['Resumen', 'Ventas', 'Inventario', 'Clientes', 'Envíos',
                  'Reportes', 'Ajustes']
    menu = '\n'.join(
        ('\x1b[1m▸ {0}\x1b[0m'.format(item) if i == 0 else '  ' + item)
        for i, item in enumerate(menu_items))
    resources = Grid([
        ProgressBar(cpu[-1], label='CPU', label_width=5, value_width=10,
                    thresholds={0.7: 'yellow', 0.9: 'red'}, use_colors=colors),
        ProgressBar(mem[-1], label='RAM', label_width=5, value_width=10,
                    thresholds={0.7: 'yellow', 0.9: 'red'}, use_colors=colors),
        ProgressBar(412, 512, label='Disco', label_width=5, value_width=10,
                    value_format='{value:.0f}/{total:.0f} GB',
                    thresholds={0.7: 'yellow', 0.9: 'red'}, use_colors=colors),
        Sparkline(cpu, label='CPU', label_width=5, show_last=True, color=accent,
                  use_colors=colors),
        Sparkline(net, label='Red', label_width=5, show_last=True, color='magenta',
                  use_colors=colors),
    ], columns=1, row_gap=0)
    chart = BarChart({'Laptops': 412, 'Monitores': 268, 'Teclados': 190,
                      'Audífonos': 151, 'Cables': 87}, sort=True,
                     color=accent, use_colors=colors)
    log = LogView([
        '09:58:02 INFO  sincronización de inventario completa',
        '09:58:40 OK    pedido #1281 enviado (Mérida)',
        '09:59:13 WARN  latencia de pagos 820 ms',
        '09:59:57 INFO  12 usuarios conectados',
        '10:00:21 ERROR timeout en la API de envíos (reintento 1/3)',
        '10:00:24 OK    API de envíos recuperada',
        '10:01:{0:02d} INFO  tick {1}'.format(tick % 60, tick),
    ], use_colors=colors)

    body = Grid([
        GridCell(Text(menu, use_colors=colors), row_span=3, title='Menú',
                 hide_below=110),
        GridCell(Grid(kpis, min_width=22, row_gap=0, gap=1), span=2,
                 title='Indicadores'),
        GridCell(sales_table(theme, colors), title='Ventas por región'),
        GridCell(resources, title='Recursos', valign='middle'),
        GridCell(chart, title='Top productos'),
        GridCell(log, title='Eventos', stretch=True),
    ],  # Three layouts: one column, two columns, sidebar + two columns.
        column_widths={0: ['1fr'], 76: ['3fr', '2fr'],
                       110: [(16, 14, 18), '3fr', '2fr']},
        row_heights={0: [], 76: ['auto', 'auto', '1fr']},
        border=border, border_color=border_color,
        title_color='bold ' + (accent or ''), use_colors=colors)
    header = StatusBar('◆ flexablelib · Panel de ventas',
                       'Resumen', 'tick {0} · 11/11/2026 10:01'.format(tick),
                       color=bar_color, use_colors=colors)
    footer = KeyHints({'q': 'Salir', '↑↓': 'Mover', 'Enter': 'Abrir',
                       '/': 'Buscar', 'F5': 'Refrescar', '?': 'Ayuda'},
                      key_color=bar_color, use_colors=colors)
    return Screen(body=body, header=header, footer=footer)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[1])
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    parser.add_argument('--theme', default='ocean',
                        choices=sorted(THEME_ACCENTS))
    parser.add_argument('--border', default='rounded',
                        choices=['single', 'rounded', 'double', 'heavy',
                                 'ascii'])
    parser.add_argument('--no-color', action='store_true')
    parser.add_argument('--live', type=int, metavar='N',
                        help='redraw N frames, one per --interval seconds')
    parser.add_argument('--interval', type=float, default=1.0)
    args = parser.parse_args(argv)
    colors = not args.no_color and (args.live is not None or None)
    if colors is None:
        from flexablelib.colors import supports_color
        colors = supports_color()
    if args.live:
        live = Live(build(args.theme, args.border, colors), width=args.width,
                    height=args.height)

        def step(i):
            live.renderable = build(args.theme, args.border, colors, i)
        live.run(step, interval=args.interval, iterations=args.live)
        return 0
    screen = build(args.theme, args.border, colors)
    print(screen.render(width=args.width, height=args.height))
    return 0


if __name__ == '__main__':
    sys.exit(main())
