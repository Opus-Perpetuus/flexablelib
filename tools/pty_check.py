#!/usr/bin/env python3
"""Real-pty checks for flexablelib 3.4.0: special keys, combinations, kitty,
modifyOtherKeys, paste, focus, injected mouse, App clicks, screen-reader mode."""
import json, os, pty, select, sys, time

OUT = "/tmp/flex_pty_%d.jsonl" % os.getpid()

def child_keys():
    from flexablelib_tui import Terminal
    with open(OUT, 'a') as log:
        with Terminal(mouse=True, focus=True, keyboard='legacy') as term:
            log.write('"READY"\n'); log.flush()
            end = time.time() + 20
            while time.time() < end:
                for k in term.read_keys(timeout=0.2):
                    rec = {'key': str(k), 'char': k.char, 'event': k.event}
                    if k.mouse is not None:
                        m = k.mouse
                        rec['mouse'] = [m.button, m.x, m.y, m.pressed, m.action]
                    log.write(json.dumps(rec) + '\n'); log.flush()
                    if str(k) == 'ctrl+q':
                        return

def child_app():
    import flexablelib_components as C
    from flexablelib_tui import App
    log = open(OUT, 'a')
    def press():
        log.write('"PRESSED"\n'); log.flush()
    box = C.Checkbox('Activo')
    app = App(body=C.Stack([C.Button('Uno', on_press=press), box]), mouse=True,
              bindings={'ctrl+q': lambda: app.exit(box.value)})
    log.write('"READY"\n'); log.flush()
    result = app.run()
    log.write(json.dumps({'checked': result}) + '\n'); log.flush()

def child_reader():
    import flexablelib_components as C
    from flexablelib_tui import App
    app = App(body=C.Stack([C.TextInput(label='Nombre'), C.Checkbox('Activo'),
                            C.Button('Guardar')]), title='Clientes',
              announce='stdout', bindings={'ctrl+q': lambda: app.exit()})
    app.run()

def run(kind, steps, env=None):
    open(OUT, 'w').close()
    pid, fd = pty.fork()
    if pid == 0:
        os.environ.update(env or {})
        import fcntl, struct, termios
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
        try:
            {'keys': child_keys, 'app': child_app, 'reader': child_reader}[kind]()
        except BaseException:
            import traceback
            open(OUT, 'a').write(json.dumps({'error': traceback.format_exc()}) + '\n')
        finally:
            os._exit(0)
    screen = b''
    def drain(t=0.3):
        nonlocal screen
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try:
                    screen += os.read(fd, 65536)
                except OSError:
                    return
    t0 = time.time()
    while kind != 'reader' and '"READY"' not in open(OUT).read() and time.time() - t0 < 10:
        drain(0.1)
    drain(1.0)
    for data in steps:
        os.write(fd, data); drain(0.25)
    drain(1.0)
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    lines = [json.loads(l) for l in open(OUT) if l.strip()]
    return lines, screen.decode('utf-8', 'replace')

E = b'\x1b'
KEYS = [
    (E + b'OP', 'f1'), (E + b'[24~', 'f12'), (E + b'[1;2P', 'shift+f1'),
    (E + b'[15;5~', 'ctrl+f5'), (E + b'[24;8~', 'ctrl+alt+shift+f12'),
    (E + b'[1;5A', 'ctrl+up'), (E + b'[1;3D', 'alt+left'), (E + b'[Z', 'shift+tab'),
    (E + b'[3~', 'delete'), (E + b'[5;5~', 'ctrl+pageup'), (E + b'[H', 'home'),
    (b'\x01', 'ctrl+a'), (E + b'x', 'alt+x'), (E + b'X', 'alt+X'),
    (E + b'[13;5u', 'ctrl+enter'), (E + b'[105;5u', 'ctrl+i'),
    (E + b'[97;6u', 'ctrl+A'), (E + b'[57376u', 'f13'),
    (E + b'[27;5;13~', 'ctrl+enter'), (E + b'[27;6;65~', 'ctrl+A'),
    (E + b'[a', 'shift+up'), (E + b'Oa', 'ctrl+up'), (E + b'[[A', 'f1'),
    ('ñ'.encode(), 'ñ'), ('😀'.encode(), '😀'),
    (E + b'[I', 'focusin'), (E + b'[O', 'focusout'),
    (E + b'[200~hola\nmundo' , None), (E + b'[201~', 'paste'),
    (E + b'[<0;10;5M', 'mouse'), (E + b'[<0;10;5m', 'mouse'),
    (E + b'[<32;12;5M', 'mouse'), (E + b'[<64;3;3M', 'scrollup'),
    (E + b'[<65;3;3M', 'scrolldown'), (E + b'[<20;7;2M', 'mouse'),
    (b'\x11', 'ctrl+q'),
]
report = {}
recs, _ = run('keys', [s for s, _ in KEYS], env={'TERM': 'xterm-256color'})
got = [r for r in recs if isinstance(r, dict)]
want = [w for _, w in KEYS if w]
names = [r['key'] for r in got]
report['keys'] = {'sent': len(want), 'got': names, 'ok': names == want}
paste = [r for r in got if r['key'] == 'paste']
report['paste_text_ok'] = bool(paste) and paste[0]['char'] == 'hola\nmundo'
report['mouse'] = [r.get('mouse') for r in got if 'mouse' in r]

ENV = {'TERM': 'xterm-256color'}
recs, scr = run('app', [E + b'[<0;3;1M', E + b'[<0;3;1m', E + b'[<0;2;2M', E + b'[<0;2;2m', b'\x11'], env=ENV)
report['app_click_button'] = 'PRESSED' in recs
report['app_click_checkbox'] = {'checked': True} in recs
recs2, _ = run('app', [b'\t', b' ', b'\x11'], env=ENV)
report['app_keyboard_tab_space'] = {'checked': True} in recs2
report['app_recs'] = recs

recs, scr = run('reader', [b'\t', b'\t', b'\x11'], env={'TERM': 'dumb'})
report['reader_linear'] = all(s in scr for s in ('Nombre, campo de texto', 'Activo, casilla', 'Guardar, botón'))
report['reader_escapes'] = scr.count('\x1b[')
report["reader_tail"] = scr[-400:]
print(json.dumps(report, ensure_ascii=False, indent=1))
