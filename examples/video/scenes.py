#!/usr/bin/env python3
"""
Escenas del video demo de flexablelib: cada una imprime salida real de la
biblioteca, con el código que la produce al lado.

    python examples/video/scenes.py --list
    python examples/video/scenes.py tablas-estilos
    python examples/video/scenes.py titulo 3 "Widgets" "ProgressBar · Sparkline"

Las usa examples/video/demo.py, que las teclea y ejecuta en orden dentro de
una terminal real mientras se graba la pantalla. Requiere
``pip install "flexablelib[all]"`` (Pillow para el título y la imagen).
"""

import datetime as dt
import inspect
import io
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for _p in (ROOT, os.path.join(ROOT, 'examples'),
           os.path.join(ROOT, 'packages', 'tui'),
           os.path.join(ROOT, 'packages', 'components'),
           os.path.join(ROOT, 'packages', 'speedups')):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from flexablelib import (BarChart, Card, Grid, GridCell, KeyHints, Live,  # noqa: E402
                         LogView, ProgressBar, Rule, Screen, Sparkline,
                         StatusBar, Table, Text)
import flexablelib_components as C  # noqa: E402
from flexablelib import _frames  # noqa: E402

CACHE = os.path.join(tempfile.gettempdir(), 'flexablelib-video')
ACCENT = '#7aa2f7'
GOLD = '#e0af68'
SCENES = {}


def scene(name):
    def deco(fn):
        SCENES[name] = fn
        return fn
    return deco


def size():
    s = shutil.get_terminal_size((140, 40))
    return s.columns, s.lines


def out(text=''):
    # render() leaves pictures as zero-width marks; expand_graphics turns
    # them into the terminal's escape sequences, as print(component) does.
    sys.stdout.write(_frames.expand_graphics(text) + '\n')
    sys.stdout.flush()


def clear():
    sys.stdout.write('\x1b[2J\x1b[3J\x1b[H')
    sys.stdout.flush()


def source(fn):
    """The body of a scene function, without its def line and docstring."""
    body = textwrap.dedent('\n'.join(inspect.getsource(fn).split('\n')[1:]))
    if body.lstrip().startswith(('"""', "'''")):
        q = body.lstrip()[:3]
        start = body.index(q)
        body = body[body.index(q, start + 3) + 3:]
    return body.strip('\n')


def side_by_side(fn, output, title='salida'):
    """Code of the scene on the left, its real output on the right."""
    from flexablelib.text_width import visible_width
    w, _ = size()
    code = source(fn)
    need = max(visible_width(l) for l in code.split('\n')) + 9
    ow = max(visible_width(l) for l in output.split('\n')) + 4
    cw = max(min(need, w - ow - 3), w // 3)
    g = Grid([GridCell(C.Code(code, 'python'), title='código'),
              GridCell(Text(output), title=title)],
             column_widths=[cw, '1fr'], border='rounded', border_color='#3b4261',
             title_color='bold ' + GOLD, use_colors=True)
    out(g.render(width=w))


def caption(text):
    w, _ = size()
    out(Text(text, align='c', color='italic #9aa5ce', use_colors=True).render(w))


# ---------------------------------------------------------------- títulos

def _font(size_, bold=False):
    from PIL import ImageFont
    try:
        path = subprocess.run(['fc-match', '-f', '%{file}',
                               'Fira Sans:' + ('bold' if bold else 'regular')],
                              capture_output=True, text=True).stdout
        return ImageFont.truetype(path, size_)
    except Exception:
        return ImageFont.load_default()


def title_png(number, title, subtitle, path):
    from PIL import Image as P, ImageDraw
    W, H = 1600, 560
    im = P.new('RGB', (W, H), (26, 27, 38))
    d = ImageDraw.Draw(im)
    for x in range(W):                       # gradient bar
        t = x / W
        c = (int(122 + (187 - 122) * t), int(162 + (154 - 162) * t), int(247))
        d.line([(x, H - 14), (x, H)], fill=c)
    label = 'flexablelib 3.5.1' + ('' if number in ('', '0') else '  ·  capítulo ' + number)
    d.text((80, 50), label, font=_font(46), fill=(122, 162, 247))
    size_ = 160
    while d.textlength(title, font=_font(size_, True)) > W - 160:
        size_ -= 6
    d.text((74, 110), title, font=_font(size_, True), fill=(192, 202, 245))
    words, lines, cur = subtitle.split(' '), [], ''
    f = _font(50)
    for word in words:
        if d.textlength((cur + ' ' + word).strip(), font=f) > W - 160:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    lines.append(cur)
    for i, line in enumerate(lines[:3]):
        d.text((82, 330 + i * 64), line, font=f, fill=(224, 175, 104))
    im.save(path)


@scene('titulo')
def titulo(number='1', title='Tablas', subtitle=''):
    """Chapter card: a picture drawn with Pillow, shown by flexablelib's Image."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'titulo-{0}.png'.format(number or 0))
    title_png(number, title, subtitle, path)
    w, h = size()
    clear()
    img = C.Image(path, alt=title, width=w - 8, height=h - 6)
    pad = max(0, (h - 2 - img.render(width=w - 8).count('\n') - 1) // 2)
    out('\n' * pad)
    for line in img.render(width=w - 8).split('\n'):
        out('    ' + line)


# ---------------------------------------------------------------- tablas

VENTAS = [
    ['Norte', 'Monterrey', 1281, 18250.5, 99.2],
    ['Norte', 'Saltillo', 1282, 9120.0, 97.8],
    ['Centro', 'CDMX', 1290, 41003.25, 99.9],
    ['Centro', 'Puebla', 1291, 7330.0, 95.1],
    ['Sur', 'Mérida', 1301, 6890.0, 98.6],
    ['Sur', 'Oaxaca 🌮', 1302, 3410.75, 92.4],
]
HEAD = ['Región', 'Tienda', 'Folio', 'Ventas', 'SLA %']


def inicio():
    t = Table(rows=VENTAS, headers=HEAD)
    t.style_name = 'rounded'
    t.header_color = 'bold #7dcfff'
    t.border_color = '#565f89'
    t.float_format = ',.2f'
    t.id_columns = 'auto'                       # Folio sin comas
    t.color_rule = lambda v, r, c: (
        'bold #f7768e' if c == 'SLA %' and v < 96 else None)
    t.title = 'Ventas por tienda'
    t.use_colors = True
    return str(t)


@scene('tablas-inicio')
def s_tablas_inicio():
    side_by_side(inicio, inicio())


@scene('tablas-estilos')
def s_estilos():
    names = ['rounded', 'single_rows', 'double_header', 'double_frame_rows',
             'rounded_double_underline', 'dashed', 'tilde_rows', 'psql',
             'markdown', 'rst', 'lines_single', 'borderless']
    cells = []
    for name in names:
        t = Table(rows=[['Oslo', 7.25], ['Lima', 19.5]], headers=['Ciudad', 'Temp'])
        t.style_name = name
        t.header_color = 'bold #7dcfff'
        t.border_color = '#7aa2f7'
        t.use_colors = True
        cells.append(GridCell(Text(str(t)), title=name))
    w, _ = size()
    out(Grid(cells, columns=4, border='rounded', border_color='#3b4261',
             title_color='bold ' + GOLD, use_colors=True).render(width=w))
    caption('{0} estilos de borde: Table().possible_styles · style_name = ...'.format(
        len(Table().possible_styles)))


def combinadas():
    t = Table(rows=[['T1', 'Norte', 120, 135], ['', 'Sur', 98, 101],
                    ['T2', 'Norte', 140, 152], ['', 'Sur', 110, 99],
                    ['Total', '', 468, 487]],
              headers=['Trimestre', 'Zona', 'Plan', 'Real'])
    t.style_name = 'double_horizontal_rows'
    t.merge_cells(0, 0, last_row=1)
    t.merge_cells(2, 0, last_row=3)
    t.merge_cells(4, 0, last_column=1)
    t.footer_rows = 1
    t.footer_color = 'bold'
    t.header_color = 'bold #bb9af7'
    t.border_color = '#7aa2f7'
    t.border_text(' Producción ', where='top', color='bold #e0af68')
    t.border_text(' 2026 ', where='bottom', align='right', offset=None,
                  color='#7dcfff')
    t.caption = 'celdas combinadas · texto en el borde · pie de tabla'
    t.use_colors = True
    return str(t)


@scene('tablas-combinadas')
def s_combinadas():
    side_by_side(combinadas, combinadas())


@scene('tablas-temas')
def s_temas():
    cells = []
    for name in ('ocean', 'neon', 'forest', 'ember', 'solarized', 'midnight'):
        t = Table(rows=[r[:2] + r[3:4] for r in VENTAS[:4]],
                  headers=['Región', 'Tienda', 'Ventas'])
        t.apply_theme(name)
        t.zebra = ('', 'on #24283b')
        t.float_format = ',.1f'
        t.use_colors = True
        cells.append(GridCell(Text(str(t)), title="apply_theme('{0}')".format(name)))
    w, _ = size()
    out(Grid(cells, columns=3, border='rounded', border_color='#3b4261',
             title_color='bold ' + GOLD, use_colors=True).render(width=w))
    caption('temas · zebra · colores por regla, por fila, por columna y por celda')


def exportar():
    t = Table(rows=VENTAS[:4], headers=HEAD)
    t.id_columns = 'auto'
    csv = t.to_csv()
    md = t.to_markdown()
    t.to_html('ventas.html', title='Ventas 2026')   # página con orden y filtro
    return csv, md


@scene('tablas-exportar')
def s_exportar():
    os.makedirs(CACHE, exist_ok=True)
    os.chdir(CACHE)
    csv, md = exportar()
    html = open('ventas.html', encoding='utf-8').read()
    w, h = size()
    left = Grid([GridCell(C.Code(source(exportar), 'python'), title='código'),
                 GridCell(Text(csv.replace('\r', '').strip()), title='to_csv()'),
                 GridCell(Text(md.strip()), title='to_markdown()')],
                columns=1, border='rounded', border_color='#3b4261',
                title_color='bold ' + GOLD, use_colors=True)
    shot = os.path.join(CACHE, 'ventas.png')
    chrome = shutil.which('google-chrome') or shutil.which('chromium')
    if chrome:
        subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu',
                        '--hide-scrollbars', '--window-size=1100,720',
                        '--screenshot=' + shot, 'file://' + os.path.join(CACHE, 'ventas.html')],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    right = GridCell(C.Image(shot, alt='ventas.html en el navegador') if os.path.exists(shot)
                     else Text(html[:800]),
                     title='to_html() · {0:,} bytes, abierta en Chrome'.format(len(html)))
    g = Grid([GridCell(left), right], column_widths=[66, '1fr'], use_colors=True,
             border='rounded', border_color='#3b4261', title_color='bold ' + GOLD)
    out(g.render(width=w))


def streaming():
    t = Table(headers=['Hora', 'Servicio', 'Latencia ms', 'Estado'])
    t.style_name = 'rounded'
    t.header_color = 'bold #7dcfff'
    t.column_min_width = [8, 12, 11, 10]
    t.use_colors = True
    t.color_rule = lambda v, r, c: ('#9ece6a' if v == '✔ ok' else
                                    '#f7768e' if v == '✖ error' else None)
    for line in t.stream(eventos()):           # una línea por fila
        print(line, flush=True)


def eventos():
    rnd = random.Random(7)
    for i in range(18):
        time.sleep(0.22)
        ms = rnd.choice([12, 18, 25, 40, 95, 310, 640, 820])
        yield ['10:{0:02d}:{1:02d}'.format(i // 6, (i * 7) % 60),
               rnd.choice(['api', 'auth', 'pagos', 'búsqueda']), ms,
               '✖ error' if ms > 500 else '✔ ok']


@scene('tablas-streaming')
def s_streaming():
    w, _ = size()
    code = Grid([GridCell(C.Code(source(streaming), 'python'), title='código · Table.stream()')],
                border='rounded', border_color='#3b4261', title_color='bold ' + GOLD,
                use_colors=True)
    out(code.render(width=min(w, 90)))
    streaming()


@scene('tablas-paginas')
def s_paginas():
    t = Table(headers=['#', 'Cliente', 'Ciudad', 'Total'])
    rnd = random.Random(3)
    names = ['Ana', 'Luis', 'Sofía', 'Diego', 'Lucía', 'Mateo', 'Valeria',
             'Emilio', 'Regina', 'Iker']
    cities = ['Mérida', 'Monterrey', 'CDMX', 'Guadalajara', 'Puebla', 'León']
    for i in range(40):
        t.add_row([1000 + i, rnd.choice(names), rnd.choice(cities),
                   round(rnd.uniform(100, 9000), 2)])
    t.style_name = 'rounded_rows'
    t.header_color = 'bold #bb9af7'
    t.float_format = ',.2f'
    t.id_columns = ['#']
    t.title = 'Clientes'
    t.use_colors = True
    pages = t.paginate(page_length=8, page_label=True)
    w, h = size()
    for i, page in enumerate(pages):
        clear()
        out(C.Code("pages = t.paginate(page_length=8, page_label=True)   # {0} páginas".format(
            len(pages)), 'python', line_numbers=False).render(width=w))
        out()
        out(page)
        out()
        out(C.Pagination(len(pages) * 8, 8, i + 1, use_colors=True).render(width=60))
        time.sleep(1.1)


# ---------------------------------------------------------------- grid

def grid_demo(width):
    g = Grid([
        GridCell(Text('Encabezado que ocupa 3 columnas', align='c'), span=3, title='Top'),
        GridCell(Text('▸ Inicio\n  Ventas\n  Pedidos\n  Clientes'), row_span=2, title='Menú',
                 hide_below=50),
        GridCell(Text('42 pedidos'), title='KPI'),
        GridCell(Text('$71,182')),
        GridCell(Text('ocupa 2 columnas'), span=2, title='Log', title_align='r'),
        GridCell(Text('color de celda'), color='black on #9ece6a', title='color'),
        GridCell(Text('centrado', align='c'), span=2, valign='middle', title='Centro',
                 title_align='c'),
    ], column_widths={0: ['1fr', '1fr', '1fr'], 50: [14, '1fr', '1fr']}, border='rounded',
        border_color='#7aa2f7', title_color='bold ' + GOLD, use_colors=True)
    return g.render(width=width)


@scene('grid')
def s_grid():
    w, h = size()
    out(Text("Grid(column_widths={0: [...], 50: [14, '1fr', '1fr']}, border='rounded') — "
             "bordes compartidos, span, row_span, títulos, breakpoints",
             color='#9aa5ce', use_colors=True).render(w))
    out()
    a, b = 70, 46
    left = grid_demo(a).split('\n')
    right = grid_demo(b).split('\n')
    n = max(len(left), len(right))
    left += [' ' * a] * (n - len(left))
    right += [' ' * b] * (n - len(right))
    out(Text('ancho {0}'.format(a), color='bold #7dcfff', use_colors=True).render(a) + '    ' +
        Text('ancho {0} (el menú se oculta)'.format(b), color='bold #7dcfff', use_colors=True).render(b))
    for l, r in zip(left, right):
        out(l + '    ' + r)
    out()
    t = Table(rows=[r[:2] + r[3:4] for r in VENTAS[:3]], headers=['Región', 'Tienda', 'Ventas'])
    t.float_format = ',.2f'
    cards = Grid(t.to_cards(subtitle_field='Región', border_color='#bb9af7', style_name='rounded',
                            title_color='bold #c0caf5'),
                 columns=3, use_colors=True)
    out(Text('Table.to_cards(): la misma tabla como tarjetas (Card)', color='bold #7dcfff',
             use_colors=True).render(w))
    out(cards.render(width=min(w, 120)))


# ---------------------------------------------------------------- widgets

@scene('widgets')
def s_widgets():
    """ProgressBar, Sparkline, BarChart, StatusBar, LogView and KeyHints in a
    Screen redrawn by Live."""
    rnd = random.Random(5)
    cpu, net = [], []
    log = LogView(level_colors={'NOTICE': 'bold #bb9af7'}, use_colors=True)
    msgs = ['INFO sincronización completa', 'WARN latencia 820 ms', 'INFO 12 pedidos nuevos',
            'ERROR timeout en envíos', 'INFO reintento ok', 'NOTICE respaldo listo',
            'DEBUG caché 94 %', 'INFO usuario ana entró']
    w, h = size()
    with Live(stream=sys.stdout, width=w, height=h, transient=True) as live:
        for tick in range(60):
            cpu.append(40 + 30 * math.sin(tick / 4) + rnd.uniform(-8, 8))
            net.append(abs(50 * math.sin(tick / 6.0)) + rnd.uniform(0, 15))
            if tick % 3 == 0:
                log.append('10:{0:02d} {1}'.format(tick // 3, msgs[(tick // 3) % len(msgs)]))
            bars = Grid([
                ProgressBar(min(100, tick * 2.1), label='Descarga', label_width=9, color='#7aa2f7',
                            use_colors=True),
                ProgressBar(cpu[-1], label='CPU', label_width=9,
                            thresholds={0.7: '#e0af68', 0.9: '#f7768e'}, use_colors=True),
                ProgressBar(412 + tick, 512, label='Disco', label_width=9, value_width=11,
                            value_format='{value:.0f}/{total:.0f} GB', color='#bb9af7',
                            use_colors=True),
            ], columns=1, row_gap=0)
            sparks = Grid([
                Sparkline(cpu[-60:], label='CPU', label_width=6, show_last=True,
                          value_format='{0:.0f}%', color='#9ece6a', use_colors=True),
                Sparkline(net[-60:], label='Red', label_width=6, show_last=True,
                          value_format='{0:.0f} MB/s', color='#7dcfff', use_colors=True),
            ], columns=1, row_gap=0)
            chart = BarChart({'Laptops': 412 + tick * 3, 'Monitores': 268 + tick * 5,
                              'Teclados': 190 + tick, 'Audífonos 🎧': 151 + tick * 2},
                             sort=True, color='#7aa2f7', colors={'Laptops': '#e0af68'},
                             use_colors=True)
            body = Grid([GridCell(bars, title='ProgressBar'), GridCell(sparks, title='Sparkline'),
                         GridCell(chart, title='BarChart'), GridCell(log, title='LogView')],
                        columns=2, border='rounded', border_color='#3b4261',
                        title_color='bold ' + GOLD, row_heights=['auto', '1fr'], use_colors=True)
            screen = Screen(body=body,
                            header=StatusBar('◆ Screen + Live', 'widgets en vivo',
                                             'frame {0}'.format(tick), color='black on #7aa2f7',
                                             use_colors=True),
                            footer=KeyHints({'q': 'Salir', '↑↓': 'Mover', 'F5': 'Refrescar'},
                                            use_colors=True))
            live.update(screen)
            time.sleep(0.12)


# ---------------------------------------------------------------- componentes

T0 = dt.date(2026, 11, 12)


def components():
    k = dict(use_colors=True)
    return [
        ('Entradas', [
            C.TextInput('Nombre', 'Yael', help='Tu nombre', **k),
            C.PasswordInput('Clave', 'secreto', **k),
            C.NumberInput('Cantidad', 5, minimum=0, **k),
            C.MoneyInput('Importe', 1234.5, **k),
            C.MaskedInput('Teléfono', '5512345678', **k),
            C.ExpressionInput('Total', '2*3+1', **k),
            C.Checkbox('Acepto términos', True, **k),
            C.Switch('Activo', True, **k),
            C.RadioGroup('Vista', ['Lista', 'Tabla', 'Tarjetas'], 'Tabla', layout='buttons', **k),
            C.CheckboxGroup('Días', ['Lu', 'Ma', 'Mi', 'Ju'], ['Ma', 'Ju'], **k),
            C.Select('Estado', ['Abierto', 'Cerrado'], 'Cerrado', **k),
            C.Autocomplete('Ciudad', ['Mérida', 'Monterrey', 'México'], 'Mé', **k),
            C.ColorInput('Color', '#7aa2f7', **k),
            C.TextArea('Notas', 'línea 1\nuna segunda línea que se envuelve', rows=3, **k),
            C.Button('Guardar', kind='primary', **k),
        ]),
        ('Fechas y horas', [
            C.Calendar(T0, today=T0, **k), C.DateInput('Fecha', T0, today=T0, **k),
            C.TimeInput('Hora', '09:30', **k),
            C.DateTimeInput('Cita', '2026-11-12T10:00', today=T0, **k),
            C.WeekInput('Semana', T0, today=T0, **k), C.MonthInput('Mes', T0, today=T0, **k),
            C.DateRangeInput('Periodo', (T0, T0 + dt.timedelta(days=6)), today=T0, **k),
            C.Timer(dt.datetime(2026, 11, 12, 9), end=dt.datetime(2026, 11, 12, 10, 2, 3), **k),
        ]),
        ('Visualización', [
            C.Stat('Ventas', '$71,182', '+6.2%', trend=[1, 3, 2, 5, 4, 6], **k),
            C.LineChart({'cpu': [1, 5, 3, 8, 6, 9, 4], 'mem': [2, 2, 3, 3, 4, 4, 5]}, height=5,
                        labels=['09:00', '10:00'], **k),
            C.Alert('Se guardó el pedido', kind='success', title='Listo', **k),
            C.Badge('Nuevo', **k), C.Tag('urgente', kind='error', **k),
            C.StatusBadge('paid', {'paid': ('Pagado', 'success')}, **k),
            C.Timeline([('09:00', 'Creado', 'Pedido recibido', 'info'),
                        ('10:30', 'Pagado', None, 'success')], **k),
            C.Stepper(['Datos', 'Pago', 'Envío'], 1, **k),
            C.Code('def doble(x):\n    return x * 2\n', 'python', **k),
            C.MarkdownView('# Título\n\nTexto **negrita** y `código`.\n\n- uno\n- [x] hecho', **k),
            C.Spinner('Cargando', **k), C.ErrorPanel(404, 'No encontrado', 'La página no existe', **k),
        ]),
        ('Navegación y estructura', [
            C.Tabs({'Clientes': 'contenido', 'Pedidos': 'otro', 'Reportes': 'más'}, **k),
            C.Breadcrumbs(['Inicio', 'Ventas', 'Pedidos', 'Pedido 1281'], **k),
            C.Menu(['Abrir', '-', {'label': 'Guardar', 'shortcut': 'ctrl+s'},
                    {'label': 'Borrar', 'disabled': True}], **k),
            C.Sidebar({'Ventas': ['Resumen', 'Pedidos'], 'Admin': ['Usuarios']}, title='Panel', **k),
            C.Tree({'src': {'app.py': None, 'ui': ['tabla.py', 'menu.py']}, 'README.md': None}, **k),
            C.Accordion([('Sección 1', 'texto 1'), ('Sección 2', 'texto 2')], **k),
            C.Pagination(200, 20, 5, **k),
            C.Wizard([('Datos', 'paso 1'), ('Pago', 'paso 2')], **k),
        ]),
        ('Datos, formularios y diálogos', [
            C.DataTable(['Folio', 'Cliente', {'title': 'Total', 'type': 'money'}],
                        [[1281, 'Ana', 15000.5], [1282, 'Luis', 220.0], [1283, 'Sofía', 3000.0]],
                        selectable=True, **k),
            C.FilterBar(['estado', 'total'], value='estado:pagado total>100', **k),
            C.CatalogGrid([{'title': 'Laptop', 'subtitle': '14"', 'price': 19999, 'badge': 'Nuevo'},
                           {'title': 'Mouse', 'price': 299}], **k),
            C.Form([C.TextInput('Nombre', required=True, **k), 'Contacto',
                    (C.TextInput('Correo', **k), C.TextInput('Tel', **k))], **k),
            C.ConfirmDialog('¿Borrar el pedido 1281?', danger=True, **k),
            C.LoadingOverlay('Procesando', progress=0.4, **k),
        ]),
    ]


@scene('componentes')
def s_componentes():
    w, h = size()
    cols = 3
    cw = (w - 2 * (cols - 1)) // cols
    groups = components()
    total = sum(len(g) for _, g in groups)
    for name, comps in groups:
        rendered = [(type(c).__name__, c.render(width=cw - 4)) for c in comps]
        page, height = [], [0] * cols
        pages = []
        for label, text in rendered:
            hh = text.count('\n') + 3
            col = height.index(min(height))
            if height[col] + hh > h - 5 and page:
                pages.append(page)
                page, height = [], [0] * cols
                col = 0
            page.append((col, label, text))
            height[col] += hh
        pages.append(page)
        for i, page in enumerate(pages):
            clear()
            out(StatusBar('◆ flexablelib_components', '{0}{1}'.format(
                name, '' if len(pages) == 1 else ' ({0}/{1})'.format(i + 1, len(pages))),
                '{0} componentes'.format(total), color='black on #bb9af7', use_colors=True).render(w))
            columns = []
            for c in range(cols):
                cards = [Card(title=label, body=Text(text), border_color='#3b4261',
                              title_color='bold ' + GOLD, width=cw, use_colors=True)
                         for col, label, text in page if col == c]
                columns.append('\n'.join(str(card) for card in cards).split('\n') if cards else [])
            n = max(len(c) for c in columns)
            for r in range(min(n, h - 2)):
                out('  '.join((col[r] if r < len(col) else ' ' * cw) for col in columns))
            time.sleep(float(os.environ.get('SCENE_PAUSE', '3.2')))


# ---------------------------------------------------------------- folios

def folios(id_columns):
    t = Table(rows=[[1281, 'Ana', 15000, 25, 2026, '06700'],
                    [1282, 'Luis', 2200, 3, 2026, '97000'],
                    [10450, 'Sofía', 1250000, 1200, 2025, '64000']],
              headers=['Folio', 'Cliente', 'Total', 'Piezas', 'Año', 'Código postal'])
    t.int_format = ','
    t.id_columns = id_columns          # None: todo con comas · 'auto': detecta
    t.style_name = 'rounded'
    t.header_color = 'bold #7dcfff'
    t.use_colors = True
    return str(t)


@scene('folios')
def s_folios():
    w, h = size()
    out(C.Code(source(folios), 'python').render(width=min(w, 100)))
    out()
    out(Text("id_columns=None  →  1,281 se lee como cantidad ✖", color='bold #f7768e',
             use_colors=True).render(w))
    out(folios(None))
    out()
    out(Text("id_columns='auto'  →  Folio, Año y Código postal tal cual; Total y Piezas con comas ✔",
             color='bold #9ece6a', use_colors=True).render(w))
    out(folios('auto'))
    out()
    from flexablelib import is_id_column
    names = ['Folio', 'cliente_id', 'Código postal', 'SKU', 'RFC', 'Total', 'Piezas', 'Monto']
    out(Text('is_id_column(): ' + '   '.join(
        '{0} {1}'.format(n, '✔' if is_id_column(n) else '·') for n in names),
        color='#c0caf5', use_colors=True).render(w))


# ---------------------------------------------------------------- imágenes

def picture(path):
    """A sunset over the sea, drawn with Pillow (no files needed)."""
    from PIL import Image as P, ImageDraw, ImageFilter
    W, H = 640, 400
    im = P.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H * 0.62)
        if y < H * 0.62:
            c = (int(40 + 215 * t), int(30 + 110 * t ** 1.5), int(90 + 40 * (1 - t)))
        else:
            u = (y - H * 0.62) / (H * 0.38)
            c = (int(70 - 40 * u), int(60 - 30 * u), int(110 - 30 * u))
        d.line([(0, y), (W, y)], fill=c)
    d.ellipse([W * 0.5 - 70, H * 0.62 - 110, W * 0.5 + 70, H * 0.62 + 30], fill=(255, 214, 120))
    rnd = random.Random(4)
    for layer, (col, base) in enumerate([((60, 40, 80), 0.50), ((35, 25, 55), 0.56)]):
        pts = [(0, H * 0.62)]
        x = 0
        while x <= W:
            pts.append((x, H * base + rnd.uniform(-40, 30) * (1 - layer * 0.4)))
            x += rnd.randint(30, 70)
        pts += [(W, H * 0.62)]
        d.polygon(pts, fill=col)
    d.rectangle([0, H * 0.62, W, H], fill=(30, 35, 75))
    for i in range(70):
        y = H * 0.63 + i * 2.1
        half = 90 - i * 1.1 + rnd.uniform(-10, 10)
        d.line([(W / 2 - half, y), (W / 2 + half, y)], fill=(255, 190 - i, 110), width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(path)


def pic():
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'atardecer.png')
    if not os.path.exists(path):
        picture(path)
    return path


@scene('imagen')
def s_imagen(method='auto'):
    """One picture with the method the terminal supports (or the one given)."""
    from flexablelib_tui import graphics
    path = pic()
    w, h = size()
    info = graphics.detect()
    img = C.Image(path, alt='Atardecer en el mar', method=None if method == 'auto' else method,
                  width=min(w - 4, 92), height=h - 9)
    card = Card(title="Image('atardecer.png'{0})".format(
        '' if method == 'auto' else ", method='{0}'".format(method)),
        body=img, border_color='#7aa2f7', title_color='bold ' + GOLD, use_colors=True,
        width=min(w, 96))
    out(str(card))
    out(Text('método usado: {0}{1}   ·   terminal: {2}   ·   kitty={3} sixel={4} celda={5}x{6}px'.format(
        img.used_method, ' (detectado)' if method == 'auto' else '',
        info.version or info.terminal, info.kitty, info.sixel, info.cell[0], info.cell[1]),
        color='#9ece6a', use_colors=True).render(min(w, 120)))


@scene('imagen-bloques')
def s_bloques():
    path = pic()
    w, h = size()
    cw = (w - 6) // 3
    cells = []
    for mode in ('half', 'quadrant', 'sextant', 'braille', 'ascii'):
        img = C.Image(path, alt='Atardecer', method=mode if mode in ('braille', 'ascii') else 'blocks',
                      blocks=mode if mode not in ('braille', 'ascii') else None,
                      width=cw - 4, height=(h - 8) // 2)
        cells.append(GridCell(img, title="method='{0}'".format(mode)))
    note = Text("Sin protocolo gráfico la imagen se dibuja con texto:\n\n"
                "▀ half      1×2 píxeles por celda\n"
                "▚ quadrant  2×2\n"
                "🬗 sextant   2×3\n"
                "⣿ braille   2×4 puntos\n"
                "@ ascii     rampa de luminancia\n\n"
                "truecolor, 256 o 16 colores, o mono con dithering.",
                color='#c0caf5', use_colors=True)
    cells.append(GridCell(note, title='cadena de respaldo'))
    out(Grid(cells, columns=3, border='rounded', border_color='#3b4261',
             title_color='bold ' + GOLD, use_colors=True).render(width=w))


@scene('imagen-respaldo')
def s_respaldo():
    path = pic()
    w, h = size()
    out(Text('Cuando la terminal no puede dibujar la imagen:', color='bold #7dcfff',
             use_colors=True).render(w))
    out()
    link = C.Image(path, alt='Atardecer en el mar', method='link', width=70)
    out(str(Card(title="method='link' · hipervínculo OSC 8 (clic o Enter → navegador)",
             body=link, border_color='#7aa2f7', title_color='bold ' + GOLD,
             use_colors=True, width=90)))
    out()
    env = dict(os.environ)
    for k in ('DISPLAY', 'WAYLAND_DISPLAY', 'BROWSER'):
        env.pop(k, None)
    env['FLEXABLELIB_NO_BROWSER'] = '1'
    code = ("import flexablelib_components as C; from flexablelib import Card; "
            "print(Card(title='sin pantalla ni navegador (SSH, contenedor, CI)', "
            "body=C.Image({0!r}, alt='Atardecer en el mar', method='link', width=70), "
            "border_color='#e0af68', title_color='bold #e0af68', use_colors=True, width=90))").format(path)
    subprocess.run([sys.executable, '-c', code], env=env)


# ---------------------------------------------------------------- accesibilidad

@scene('lector')
def s_lector():
    """What the screen-reader mode writes: linear text, one line per component."""
    from flexablelib_tui.accessibility import describe
    k = dict(use_colors=True)
    comps = [C.TextInput('Nombre', 'Yael', required=True, **k),
             C.PasswordInput('Clave', 'secreto', **k),
             C.Checkbox('Activo', True, **k),
             C.Select('Estado', ['Abierto', 'Cerrado'], 'Cerrado', **k),
             C.Button('Guardar', **k),
             C.DataTable(['Folio', 'Cliente'], [[1281, 'Ana'], [1282, 'Luis']], **k)]
    w, _ = size()
    out(Text('describe(componente.a11y()) — lo que lee un lector de pantalla',
             color='bold #7dcfff', use_colors=True).render(w))
    for i, c in enumerate(comps):
        out(('> ' if i == 0 else '  ') + describe(c.a11y()))


# ---------------------------------------------------------------- aceleración

@scene('backend')
def s_backend():
    import flexablelib.fast as fast
    from flexablelib import _frames, _images
    import flexablelib_speedups
    w, _ = size()
    card = Card(title='¿Qué está activo?', fields={
        'flexablelib.fast.implementation()': fast.implementation(),
        '_frames.BACKEND (marcos, diff)': _frames.BACKEND,
        '_images.BACKEND (imágenes)': _images.BACKEND,
        'flexablelib-speedups': flexablelib_speedups.__version__,
        'forzar Python': 'FLEXABLELIB_FRAMES=python · FLEXABLELIB_IMAGES=python',
    }, border_color='#9ece6a', title_color='bold #9ece6a', use_colors=True, width=min(w, 100))
    out(str(card))


def _time(fn, n):
    t = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t) / n * 1000


@scene('carrera')
def s_carrera():
    """C against pure Python on the same work, measured now."""
    from flexablelib import _frames, _images
    import dashboard
    from PIL import Image as P
    raw = P.open(pic()).convert('RGBA')
    data, iw, ih = raw.tobytes(), raw.width, raw.height
    small = raw.resize((320, 200)).tobytes()
    jobs = [
        ('Frame del dashboard 300×80', lambda: dashboard.build('ocean', 'rounded', True, 1)
         .render(width=300, height=80), 15),
        ('resize 640×400 → 320×200', lambda: _images.resize(data, iw, ih, 320, 200), 3),
        ('quantize 320×200, 255 colores', lambda: _images.quantize(small, 320, 200, 255, 128), 2),
        ('braille 80×24 (mono)', lambda: _images.cells(small, 320, 200, 'braille', 'none', 128), 6),
    ]
    w, h = size()
    results = {}
    with Live(stream=sys.stdout, width=w, height=h, transient=True) as live:
        def draw(status):
            rows = []
            for name, _, _ in jobs:
                py, c = results.get((name, 'python')), results.get((name, 'c'))
                rows.append([name, '{0:.2f} ms'.format(py) if py else '…',
                             '{0:.2f} ms'.format(c) if c else '…',
                             '{0:.0f}×'.format(py / c) if py and c else ''])
            t = Table(rows=rows, headers=['Operación', 'Python', 'C', 'Aceleración'])
            t.style_name = 'rounded'
            t.header_color = 'bold #7dcfff'
            t.color_rule = lambda v, r, col: 'bold #9ece6a' if col == 'Aceleración' else None
            t.use_colors = True
            speed = {name[:24]: results[(name, 'python')] / results[(name, 'c')]
                     for name, _, _ in jobs if (name, 'c') in results}
            parts = [GridCell(Text(str(t)), title='medido ahora, en esta máquina')]
            if speed:
                parts.append(GridCell(BarChart(speed, value_format='{0:,.0f}×', color='#9ece6a',
                                               use_colors=True), title='veces más rápido con C'))
            body = Grid(parts, columns=1, border='rounded', border_color='#3b4261',
                        title_color='bold ' + GOLD, use_colors=True)
            live.update(Screen(body=body, header=StatusBar(
                '◆ Aceleración C', status, 'flexablelib[speed]', color='black on #9ece6a',
                use_colors=True)))
        for name, fn, n in jobs:
            for backend in ('python', 'c'):
                _frames.use(backend)
                _images.use(backend)
                draw('midiendo: {0} ({1})'.format(name, backend))
                fn()
                results[(name, backend)] = _time(fn, n)
                draw('midiendo: {0} ({1})'.format(name, backend))
        _frames.use('auto')
        _images.use('auto')
        draw('listo')
        time.sleep(float(os.environ.get('SCENE_PAUSE', '5')))


# ---------------------------------------------------------------- cierre

@scene('cierre')
def s_cierre():
    w, h = size()
    card = Card(title='flexablelib 3.5.1', subtitle='tablas, layouts y apps de terminal en Python',
                fields={'Instalar': 'pip install "flexablelib[all]"',
                        'Extras': 'tui · components · speed · images',
                        'Python': 'CPython 3.8 – 3.14 · Linux, macOS, Windows',
                        'Wheels C': 'x86_64 y aarch64 (manylinux, musllinux), macOS arm64/Intel, Windows',
                        'Código': 'github.com/Opus-Perpetuus/flexablelib',
                        'PyPI': 'pypi.org/project/flexablelib'},
                border_color='#7aa2f7', title_color='bold #7aa2f7', width=min(w - 10, 96),
                use_colors=True, shadow=True)
    lines = str(card).split('\n')
    out('\n' * max(0, (h - len(lines)) // 2 - 1))
    from flexablelib.text_width import visible_width
    pad = ' ' * max(0, (w - visible_width(lines[0])) // 2)
    for l in lines:
        out(pad + l)
    out()
    out(Text('Gracias por ver ✦', align='c', color='bold ' + GOLD, use_colors=True).render(w))


def main(argv):
    if len(argv) < 2 or argv[1] == '--list':
        out('\n'.join(SCENES))
        return
    SCENES[argv[1]](*argv[2:])


if __name__ == '__main__':
    main(sys.argv)
