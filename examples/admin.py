#!/usr/bin/env python3
"""
An interactive back-office application built with flexablelib's optional
terminal packages (``pip install flexablelib[tui,components,speed]``).

    python examples/admin.py                     # interactive (Ctrl-Q quits)
    python examples/admin.py --frame 120x36      # print one frame and exit
    python examples/admin.py --frame 120x36 --keys "tab,down,down,enter"
    python examples/admin.py --frame 80x24 --no-color
    python examples/admin.py --theme high-contrast --screen-reader
    python examples/admin.py --frame 100x30 --keys "click:3:5" --ascii

Keys: Tab / Shift-Tab move the focus, Ctrl-B shows or hides the sidebar,
Ctrl-K opens the command palette, Ctrl-N a new-customer form, F1 the help,
Ctrl-Q quits, Ctrl-R reads the screen aloud (screen-reader mode). In the
orders table: arrows, 1-9 sort, / filter, Space selects, Enter opens the
order. The mouse works too: click to focus and press, wheel to scroll,
drag the scroll bars; ``--theme`` picks a theme (high-contrast,
deuteranopia, protanopia, tritanopia, monochrome ...).

Pieces: AppShell (sidebar, top bar, pages), Stat cards, LineChart,
DataTable bound to a FilterBar, Form with validation, Calendar, Timeline,
Stepper, DetailView, Switch/Select settings, Modal, ConfirmDialog,
CommandPalette and notifications.
"""

import argparse
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Run from a checkout without installing: use the in-tree packages.
for path in (ROOT, os.path.join(ROOT, 'packages', 'tui'),
             os.path.join(ROOT, 'packages', 'components'),
             os.path.join(ROOT, 'packages', 'speedups')):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

import flexablelib_components as C  # noqa: E402
from flexablelib import KeyHints  # noqa: E402
from flexablelib import _frames  # noqa: E402
from flexablelib_tui import App, Component, parse_keys  # noqa: E402

TODAY = dt.date(2026, 11, 11)

ORDERS = [
    {'folio': 1281, 'cliente': 'Ana Torres', 'ciudad': 'Mérida',
     'estado': 'pagado', 'total': 18250.5, 'fecha': '2026-11-11'},
    {'folio': 1280, 'cliente': 'Luis Pérez', 'ciudad': 'Monterrey',
     'estado': 'pendiente', 'total': 9120.0, 'fecha': '2026-11-10'},
    {'folio': 1279, 'cliente': 'Sofía Ruiz', 'ciudad': 'CDMX',
     'estado': 'enviado', 'total': 25400.75, 'fecha': '2026-11-10'},
    {'folio': 1278, 'cliente': 'Eva Núñez', 'ciudad': 'Puebla',
     'estado': 'cancelado', 'total': 7310.2, 'fecha': '2026-11-09'},
    {'folio': 1277, 'cliente': 'Raúl Díaz', 'ciudad': 'Oaxaca',
     'estado': 'pagado', 'total': 4210.4, 'fecha': '2026-11-09'},
    {'folio': 1276, 'cliente': 'Marta Gil', 'ciudad': 'Mérida',
     'estado': 'enviado', 'total': 12999.0, 'fecha': '2026-11-08'},
    {'folio': 1275, 'cliente': 'Iván Soto', 'ciudad': 'Querétaro',
     'estado': 'pendiente', 'total': 3150.0, 'fecha': '2026-11-08'},
    {'folio': 1274, 'cliente': 'Lucía Vega', 'ciudad': 'León',
     'estado': 'pagado', 'total': 8740.9, 'fecha': '2026-11-07'},
    {'folio': 1273, 'cliente': 'Hugo Mora', 'ciudad': 'Tijuana',
     'estado': 'pagado', 'total': 15600.0, 'fecha': '2026-11-07'},
    {'folio': 1272, 'cliente': 'Paula Cruz', 'ciudad': 'Cancún',
     'estado': 'enviado', 'total': 6420.3, 'fecha': '2026-11-06'},
]

STATES = {'pagado': 'green', 'pendiente': 'yellow', 'enviado': 'cyan',
          'cancelado': 'red'}


class Admin(object):
    """Builds the screens and wires the actions."""

    def __init__(self, **app_options):
        self.orders = C.DataTable(
            [{'key': 'folio', 'title': 'Folio', 'align': 'r', 'format': str},
             {'key': 'cliente', 'title': 'Cliente'},
             {'key': 'ciudad', 'title': 'Ciudad'},
             {'key': 'estado', 'title': 'Estado',
              'color': lambda v: STATES.get(v)},
             {'key': 'total', 'title': 'Total', 'align': 'r',
              'format': lambda v: '${0:,.2f}'.format(v)},
             {'key': 'fecha', 'title': 'Fecha'}],
            ORDERS, selectable=True, on_activate=self.open_order)
        self.filters = C.FilterBar(['estado', 'ciudad', 'total'],
                                   table=self.orders)
        self.sidebar = C.Sidebar(
            {'Ventas': ['Resumen', 'Pedidos', 'Agenda'],
             'Administración': ['Clientes', 'Ajustes']}, title='Tienda')
        self.topbar = C.TopBar('Tienda', ['Resumen'],
                               [('Ctrl-K', 'Buscar'), ('F1', 'Ayuda')],
                               status='11 nov 2026 · 10:42')
        self.shell = C.AppShell(sidebar=self.sidebar, topbar=self.topbar,
                                pages=self.pages())
        self.app = App(
            mouse=True, title='Tienda · administración', **app_options,
            body=self.shell,
            footer=KeyHints([('Tab', 'Foco'), ('Ctrl-B', 'Menú'),
                             ('Ctrl-K', 'Comandos'), ('Ctrl-N', 'Nuevo'),
                             ('F1', 'Ayuda'), ('Ctrl-Q', 'Salir')]),
            bindings={'ctrl+q': (lambda: self.app.exit(), 'Salir'),
                      'ctrl+k': (self.palette, 'Paleta de comandos'),
                      'ctrl+n': (self.new_customer, 'Nuevo cliente'),
                      'f1': (self.help, 'Ayuda')})

    # -- pages --------------------------------------------------------------

    def pages(self):
        paid = sum(o['total'] for o in ORDERS if o['estado'] != 'cancelado')
        stats = C.Stack([
            C.Stat('Ventas del mes', '${0:,.0f}'.format(paid), '+6.2%',
                   trend=[42, 48, 45, 52, 58, 55, 63, 71]),
            C.Stat('Pedidos', str(len(ORDERS)), '+3',
                   trend=[6, 7, 7, 8, 9, 8, 10]),
            C.Stat('Cancelaciones', '1', '+1', invert=True,
                   trend=[0, 1, 0, 0, 1, 0, 1]),
            C.Stat('Ticket medio', '${0:,.0f}'.format(paid / 9), '-1.4%',
                   trend=[12, 11, 12, 11, 10, 11, 11])],
            direction='horizontal', gap=1, min_width=22)
        chart = C.Box(C.LineChart(
            {'ventas': [42, 48, 45, 52, 58, 55, 63, 71, 66, 74, 79, 83],
             'meta': [50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72]},
            height=7, labels=['ene', 'jun', 'dic'], y_format='{0:g}k'),
            title='Ventas 2026 (miles)')
        recent = C.Box(C.Timeline([
            ('10:41', 'Pedido 1281 pagado', 'Ana Torres · $18,250.50',
             'success'),
            ('10:12', 'Pedido 1280 creado', 'Luis Pérez', 'info'),
            ('09:55', 'Pedido 1278 cancelado', 'Sin existencias', 'error'),
            ('09:30', 'Inventario actualizado', None, 'warning')]),
            title='Actividad')
        latest = C.Box(C.DataTable(
            [{'key': 'folio', 'title': 'Folio', 'format': str},
             {'key': 'cliente', 'title': 'Cliente'},
             {'key': 'estado', 'title': 'Estado',
              'color': lambda v: STATES.get(v)},
             {'key': 'total', 'title': 'Total', 'align': 'r',
              'format': lambda v: '${0:,.2f}'.format(v)}],
            ORDERS[:4], status=False, zebra=False), title='Últimos pedidos')
        summary = C.Stack([
            stats, C.Split(chart, recent, ratio=0.6, divider=False),
            latest], gap=1)


        orders = C.Stack([self.filters, self.orders], gap=1)

        agenda = C.Split(
            C.Box(C.Calendar(TODAY, today=TODAY), title='Noviembre'),
            C.Box(C.Stack([
                C.Stepper(['Pedido', 'Pago', 'Empaque', 'Envío'], 2),
                C.Timeline([('11:00', 'Entrega Mérida', 'Ruta 3', 'info'),
                            ('13:30', 'Recolección CDMX', None, 'warning'),
                            ('17:00', 'Corte de caja', None, 'success')])],
                gap=1), title='Hoy'), ratio=0.45, divider=False)

        customers = C.Box(C.DetailView({
            '# Cliente': None, 'Nombre': 'Ana Torres',
            'Correo': 'ana@example.com', 'Teléfono': '55 1234 5678',
            'Ciudad': 'Mérida', '# Compras': None, 'Pedidos': '14',
            'Total': '$182,430.00', 'Último': '11 nov 2026'}, columns=2),
            title='Ficha')

        settings = C.Box(C.Form([
            C.Switch('Notificaciones', True),
            C.Switch('Modo compacto', False),
            C.Select('Moneda', ['MXN', 'USD', 'EUR'], 'MXN'),
            C.RadioGroup('Tema', ['Oscuro', 'Claro', 'Sistema'], 'Oscuro',
                         layout='buttons')],
            on_submit=lambda values: self.app.notify(
                'Ajustes guardados', 'success'),
            cancel_label=None), title='Ajustes')
        return {'Resumen': summary, 'Pedidos': orders, 'Agenda': agenda,
                'Clientes': customers, 'Ajustes': settings}

    # -- actions ------------------------------------------------------------

    def open_order(self, row):
        detail = C.DetailView({
            'Folio': row['folio'], 'Cliente': row['cliente'],
            'Ciudad': row['ciudad'], 'Estado': row['estado'],
            'Total': '${0:,.2f}'.format(row['total']),
            'Fecha': row['fecha']})
        modal = C.Modal(detail, title='Pedido {0}'.format(row['folio']),
                        buttons=[('Cerrar', None),
                                 ('Cancelar pedido',
                                  lambda: self.confirm_cancel(row))],
                        width=50)
        modal.open(self.app)

    def confirm_cancel(self, row):
        def cancel():
            row['estado'] = 'cancelado'
            self.app.notify('Pedido {0} cancelado'.format(row['folio']),
                            'warning')
        self.app.pop()
        C.ConfirmDialog(
            '¿Cancelar el pedido {0} de {1}?'.format(row['folio'],
                                                    row['cliente']),
            on_confirm=cancel, confirm_label='Cancelar pedido',
            cancel_label='Volver', danger=True).open(self.app)

    def palette(self):
        def go(page):
            return lambda: self.shell.open_page(page)
        commands = [('Ir a ' + name, go(name)) for name in self.shell.pages]
        commands += [('Nuevo cliente', self.new_customer),
                     ('Ayuda', self.help)]
        self.app.push(C.CommandPalette(commands), position='top')

    def new_customer(self):
        def save(values):
            self.app.pop()
            self.app.notify('Cliente {0} guardado'.format(values['nombre']),
                            'success')
        form = C.Form([
            C.TextInput('Nombre', required=True),
            (C.TextInput('Correo', validators=[
                lambda v: None if not v or '@' in v else 'Correo no válido']),
             C.MaskedInput('Teléfono', mask='phone')),
            C.DateInput('Alta', TODAY, today=TODAY),
            C.Select('Ciudad', ['Mérida', 'Monterrey', 'CDMX', 'Puebla'])],
            on_submit=save, on_cancel=lambda: self.app.pop())
        C.Modal(form, title='Nuevo cliente', width=64).open(self.app)

    def help(self):
        C.Modal(C.MarkdownView(
            '**Tab** cambia el foco · **Ctrl-B** menú · **Ctrl-K** comandos'
            '\n\n- Tabla: flechas, `1`-`9` ordena, `/` filtra, Espacio '
            'selecciona, Enter abre\n- Filtros: `estado:pagado total>5000`'
            '\n- **Esc** cierra los diálogos'), title='Ayuda',
            width=60).open(self.app)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--frame', metavar='WxH',
                        help='print one frame of this size and exit')
    parser.add_argument('--keys', default='',
                        help='comma-separated keys fed before the frame')
    parser.add_argument('--no-color', action='store_true')
    parser.add_argument('--theme', help='high-contrast, deuteranopia, '
                        'protanopia, tritanopia, monochrome ...')
    parser.add_argument('--screen-reader', action='store_true',
                        help='linear text with roles; announcements')
    parser.add_argument('--announce', metavar='TARGET',
                        help='stdout, stderr or a file for announcements')
    parser.add_argument('--ascii', action='store_true')
    parser.add_argument('--focus-marker', action='store_true')
    parser.add_argument('--reduced-motion', action='store_true')
    args = parser.parse_args(argv)
    if args.no_color:
        Component.use_colors = False
    options = dict((k, v) for k, v in (('theme', args.theme),
                                       ('announce', args.announce)) if v)
    for name in ('screen_reader', 'ascii', 'focus_marker', 'reduced_motion'):
        if getattr(args, name):
            options[name] = True
    admin = Admin(**options)
    if not args.frame:
        admin.app.run()
        return 0
    if not args.no_color:
        Component.use_colors = True
        admin.app.use_colors = True
    width, height = (int(n) for n in args.frame.lower().split('x'))
    keys = [k.strip() for k in args.keys.split(',') if k.strip()]
    for key in keys:
        admin.app.render(width, height)
        if key.startswith('click:'):
            # click:X:Y -- a mouse click at that cell (0-based).
            x, y = (int(n) + 1 for n in key.split(':')[1:3])
            for seq in ('\x1b[<0;{0};{1}M', '\x1b[<0;{0};{1}m'):
                for parsed in parse_keys(seq.format(x, y)):
                    admin.app.dispatch(parsed)
            continue
        admin.app.dispatch(key)
    sys.stdout.write(admin.app.render(width, height) + '\n')
    sys.stderr.write('frames backend: {0}\n'.format(_frames.BACKEND))
    return 0


if __name__ == '__main__':
    sys.exit(main())
