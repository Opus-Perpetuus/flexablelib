#!/usr/bin/env python3
"""
Guion del video demo: teclea y ejecuta, en orden, los ejemplos del repo y las
escenas de scenes.py dentro de una terminal kitty real, y maneja teclado y
ratón con xdotool en las partes interactivas. record.sh lo lanza en una
pantalla virtual y graba con ffmpeg; aquí no se inventa ninguna salida.

    python examples/video/demo.py                  # todo (dentro de kitty)
    python examples/video/demo.py --only 5,8       # algunos capítulos
    python examples/video/demo.py --log tiempos.json

Necesita kitty con ``allow_remote_control yes`` y ``--listen-on`` (variable
KITTY_LISTEN_ON), xdotool y, para el capítulo de imágenes, xterm (sixel).
"""

import argparse
import fcntl
import json
import os
import shlex
import struct
import subprocess
import sys
import termios
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from flexablelib.text_width import visible_width  # noqa: E402

PROMPT = '\x1b[38;2;122;162;247m~/flexablelib\x1b[0m \x1b[38;2;187;154;247m❯\x1b[0m '
BASE_FONT = 15.0
SOCKET = os.environ.get('KITTY_LISTEN_ON', 'unix:/tmp/flexablelib-video.sock')
LOG = []
T0 = time.time()


def w(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def clear():
    w('\x1b[2J\x1b[3J\x1b[H')


def kitty(*args):
    t = time.time()
    try:
        r = subprocess.run(['kitty', '@', '--to', SOCKET] + list(args),
                           capture_output=True, text=True, timeout=4)
    except subprocess.TimeoutExpired as e:
        r = subprocess.CompletedProcess(e.cmd, -1, '', 'timeout')
    if os.environ.get('DEMO_DEBUG'):
        with open(os.environ['DEMO_DEBUG'], 'a') as f:
            f.write('{0} {1:.2f}s rc={2} {3!r} {4}\n'.format(
                args[:2], time.time() - t, r.returncode, r.stderr[-200:], winsize()))
    return r.stdout


_FONT = [None]


def font(size):
    """Zoom the terminal; the screen is cleared first so nothing reflows
    on camera, and the scene starts once kitty has resized."""
    if _FONT[0] == size:
        return
    clear()
    before = winsize()[:2]
    for attempt in range(3):
        kitty('set-font-size', str(size))
        for _ in range(20):
            time.sleep(0.1)
            if winsize()[:2] != before:
                break
        else:
            continue
        break
    time.sleep(0.6)
    _FONT[0] = size


def winsize():
    rows, cols, xp, yp = struct.unpack('HHHH', fcntl.ioctl(
        sys.stdout.fileno(), termios.TIOCGWINSZ, b'\0' * 8))
    return rows, cols, xp, yp


def cell_center(row, col):
    rows, cols, xp, yp = winsize()
    cw, ch = xp / cols, yp / rows
    ox, oy = (1920 - xp) / 2, (1080 - yp) / 2
    return int(ox + col * cw + cw / 2), int(oy + row * ch + ch / 2)


def find(text):
    """Row and column of text on the kitty screen, read back from kitty."""
    screen = kitty('get-text', '--extent', 'screen').split('\n')
    for r, line in enumerate(screen):
        i = line.find(text)
        if i >= 0:
            return r, visible_width(line[:i]) + 1
    return None


def xdo(*args):
    subprocess.run(['xdotool'] + list(args))


def act(actions):
    for a in actions:
        kind = a[0]
        if kind == 'sleep':
            time.sleep(a[1])
        elif kind == 'key':
            for k in a[1].split():
                xdo('key', k)
                time.sleep(a[2] if len(a) > 2 else 0.35)
        elif kind == 'type':
            xdo('type', '--delay', '90', a[1])
            time.sleep(0.3)
        elif kind in ('click', 'wheel', 'move'):
            pos = find(a[1])
            if pos is None:
                continue
            x, y = cell_center(*pos)
            xdo('mousemove', str(x), str(y))
            time.sleep(0.35)
            if kind == 'click':
                xdo('click', '1')
            elif kind == 'wheel':
                for _ in range(a[2]):
                    xdo('click', a[3] if len(a) > 3 else '5')
                    time.sleep(0.25)
            time.sleep(0.4)
        elif kind == 'park':
            xdo('mousemove', '1910', '1070')


def type_command(command, speed=0.022):
    w(PROMPT)
    time.sleep(0.25)
    for ch in command:
        w(ch)
        time.sleep(speed)
    time.sleep(0.35)
    w('\n')


def run(command, hold=3.0, size=None, actions=None, env=None, shown=None,
        clear_first=True):
    """Type the command, run it for real, drive it, then hold the result."""
    if size:
        font(size)
    if clear_first:
        clear()
    type_command(shown or command)
    full_env = dict(os.environ)
    full_env.update(env or {})
    for k, v in list(full_env.items()):
        if v is None:
            del full_env[k]
    proc = subprocess.Popen(command, shell=True, cwd=ROOT, env=full_env)
    if actions:
        t = threading.Thread(target=act, args=(actions,), daemon=True)
        t.start()
    proc.wait()
    time.sleep(hold)


def chapter(number, title, subtitle, hold=3.2):
    LOG.append({'t': round(time.time() - T0, 2), 'n': number, 'title': title})
    font(BASE_FONT)
    clear()
    subprocess.run([sys.executable, os.path.join(HERE, 'scenes.py'), 'titulo',
                    str(number), title, subtitle], cwd=ROOT)
    time.sleep(hold)


S = 'python examples/video/scenes.py '


def ch0():
    chapter(0, 'flexablelib — demo completa',
            'tablas, layouts, widgets, componentes y apps de terminal en Python · '
            'todo lo que ves es salida real de la terminal', hold=4.5)


def ch1():
    chapter(1, 'Tablas', 'estilos · bordes · celdas combinadas · colores y temas · '
            'exportar a HTML, CSV y Markdown · streaming · paginación')
    run(S + 'tablas-inicio', hold=4.5, size=22)
    run(S + 'tablas-estilos', hold=5, size=18)
    run(S + 'tablas-combinadas', hold=5, size=21)
    run(S + 'tablas-temas', hold=5, size=18)
    run(S + 'tablas-exportar', hold=6, size=17)
    run(S + 'tablas-streaming', hold=2.5, size=18)
    run(S + 'tablas-paginas', hold=1.5, size=20)


def ch2():
    chapter(2, 'Grid y layout', 'bordes compartidos · span y row_span · títulos por celda · '
            'anchos fijos, fr y % · breakpoints · tarjetas')
    run(S + 'grid', hold=6, size=18)


def ch3():
    chapter(3, 'Widgets', 'ProgressBar · Sparkline · BarChart · StatusBar · LogView · '
            'KeyHints · Screen y Live')
    run(S + 'widgets', hold=0.5, size=17)
    run('python examples/dashboard.py --live 12 --interval 0.5 --theme neon', hold=0.5,
        size=15)


def ch4():
    chapter(4, 'Componentes', 'más de 90 componentes: entradas, fechas, visualización, '
            'navegación, datos, formularios y diálogos')
    run(S + 'componentes', hold=0.3, size=20, env={'SCENE_PAUSE': '2.5'})


def ch5():
    chapter(5, 'App TUI', 'teclado y ratón · foco con Tab · filtros y orden · diálogos · '
            'paleta de comandos · ayuda F1 · formularios')
    run('python examples/admin.py', hold=0.3, size=17, actions=[
        ('sleep', 2.5), ('key', 'Down', 0.6), ('key', 'Return', 1.4),
        ('key', 'Tab', 0.5), ('type', 'estado:pagado'), ('key', 'space'),
        ('type', 'total>5000'), ('key', 'Return', 1.0), ('key', 'Tab', 0.6),
        ('key', '5 5', 0.8), ('key', 'Down Down', 0.5), ('key', 'Return', 2.2),
        ('key', 'Escape', 0.8), ('wheel', 'Folio', 3, '5'), ('sleep', 0.6),
        ('key', 'ctrl+k', 0.8), ('type', 'cli'), ('sleep', 1.4), ('key', 'Escape', 0.6),
        ('click', 'Agenda'), ('sleep', 1.6), ('click', 'Resumen'), ('sleep', 1.0),
        ('key', 'ctrl+n', 0.8), ('type', 'Yael'), ('key', 'Tab'), ('type', 'yael@ejemplo.mx'),
        ('key', 'Tab'), ('type', '5512345678'), ('sleep', 0.8),
        ('key', 'Tab Tab Tab Tab', 0.25), ('key', 'Return', 2.4),
        ('key', 'F1', 2.6), ('key', 'Escape', 0.6), ('key', 'ctrl+b', 1.8),
        ('park',), ('key', 'ctrl+q')])
    run('python examples/keys.py', hold=0.3, size=17, actions=[
        ('sleep', 2.0), ('key', 'ctrl+shift+a alt+x F5 ctrl+Return shift+Tab', 0.7),
        ('type', 'hola'), ('click', 'Botón B'), ('sleep', 0.6), ('click', 'Casilla'),
        ('sleep', 0.6), ('wheel', 'Elemento 03', 4, '5'), ('sleep', 1.4),
        ('park',), ('key', 'ctrl+q')])


def ch6():
    chapter(6, 'Accesibilidad', 'temas de alto contraste y para daltonismo · NO_COLOR · '
            'modo lector de pantalla · ASCII · foco visible sin color')
    run('python examples/admin.py --theme high-contrast', hold=0.3, size=17, actions=[
        ('sleep', 2.0), ('key', 'Down Return', 0.7), ('key', 'Tab Down Down', 0.5),
        ('sleep', 1.2), ('key', 'ctrl+q')])
    run('python examples/admin.py --theme deuteranopia', hold=0.3, size=17, actions=[
        ('sleep', 2.6), ('key', 'ctrl+q')])
    run('NO_COLOR=1 python examples/dashboard.py', hold=3.5, size=15,
        shown='NO_COLOR=1 python examples/dashboard.py')
    run(S + 'lector', hold=3.0, size=24)
    run('python examples/admin.py --screen-reader --announce stdout', hold=0.3, size=17,
        actions=[('sleep', 2.2), ('key', 'Tab', 1.1), ('key', 'Tab', 1.1), ('key', 'Down', 1.1),
                 ('key', 'Return', 1.6), ('key', 'ctrl+q')])
    run('python examples/admin.py --ascii --focus-marker --no-color', hold=0.3, size=17,
        actions=[('sleep', 2.6), ('key', 'ctrl+q')])


def ch7():
    chapter(7, 'Folios', 'identificadores tal cual (1281, 2026, 06700) · '
            'cantidades y dinero con separadores · detección por nombre')
    run(S + 'folios', hold=6, size=18)


def ch8():
    chapter(8, 'Imágenes', 'kitty · iTerm2 · sixel · bloques Unicode · braille · ASCII · '
            'enlace al navegador · aviso sin navegador')
    run(S + 'imagen', hold=5, size=15)
    # sixel: the same scene in a real xterm (VT340 mode) on top of kitty.
    clear()
    type_command("xterm -ti vt340 -e 'python examples/video/scenes.py imagen sixel'")
    env = dict(os.environ)
    env.pop('KITTY_WINDOW_ID', None)
    env['TERM'] = 'xterm-256color'
    x = subprocess.Popen([
        'xterm', '-ti', 'vt340', '-xrm', 'XTerm*decTerminalID: vt340',
        '-xrm', 'XTerm*numColorRegisters: 256', '-xrm', 'XTerm*sixelScrolling: true',
        '-fa', 'DejaVu Sans Mono', '-fs', '12', '-bg', '#16161e', '-fg', '#c0caf5',
        '-bw', '3', '-bd', '#7aa2f7', '-geometry', '104x34+300+150', '-T', 'xterm',
        '-e', 'bash', '-c', 'cd {0} && {1} examples/video/scenes.py imagen sixel; sleep 6'.format(
            shlex.quote(ROOT), shlex.quote(sys.executable))], env=env)
    x.wait()
    run(S + 'imagen-bloques', hold=5.5, size=15)
    run(S + 'imagen-respaldo', hold=5, size=24)


def ch9():
    chapter(9, 'Aceleración C', 'flexablelib[speed]: medición de texto, marcos, diff e '
            'imágenes en C · mismo resultado que Python · benchmark en vivo')
    run(S + 'backend', hold=3.5, size=24)
    run(S + 'carrera', hold=0.3, size=18, env={'SCENE_PAUSE': '4.5'})
    run('python tools/bench_frames.py --frames 30', hold=4, size=26)


def ch10():
    LOG.append({'t': round(time.time() - T0, 2), 'n': 10, 'title': 'Cierre'})
    font(26)
    clear()
    subprocess.run([sys.executable, os.path.join(HERE, 'scenes.py'), 'cierre'], cwd=ROOT)
    time.sleep(10)


CHAPTERS = [ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, ch9, ch10]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default='')
    parser.add_argument('--log', default='')
    args = parser.parse_args()
    only = {int(n) for n in args.only.split(',') if n.strip()}
    w('\x1b[?25l')
    try:
        for i, fn in enumerate(CHAPTERS):
            if not only or i in only:
                fn()
    finally:
        w('\x1b[?25h')
        LOG.append({'t': round(time.time() - T0, 2), 'n': -1, 'title': 'fin'})
        if args.log:
            with open(args.log, 'w') as f:
                json.dump({'start': T0, 'chapters': LOG}, f, indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
