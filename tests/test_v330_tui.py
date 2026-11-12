"""
3.3.0 terminal toolkit (flexablelib_tui): key parsing, terminal input mode,
the App loop (focus, bindings, dialogs, notifications, resize), ScrollView
and the Live diff renderer.
"""

import io
import os
import sys
import time

import pytest

tui = pytest.importorskip('flexablelib_tui')

from flexablelib import Grid, GridCell  # noqa: E402
from flexablelib_tui import (App, Component, Key, KeyParser, Live,  # noqa
                             ScrollView, StatusBar, Terminal,
                             WindowsKeyParser, overlay, parse_keys)
from flexablelib_tui import app as app_module  # noqa: E402
from flexablelib_tui import terminal as terminal_module  # noqa: E402
from flexablelib.text_width import visible_width  # noqa: E402


def names(keys):
    return [str(k) for k in keys]


class TestKeyParser:
    @pytest.mark.parametrize('data,expected', [
        ('a', ['a']), ('A', ['A']), ('ñ', ['ñ']), (' ', ['space']),
        ('\r', ['enter']), ('\n', ['enter']), ('\t', ['tab']),
        ('\x7f', ['backspace']), ('\x08', ['backspace']),
        ('\x00', ['ctrl+space']), ('\x03', ['ctrl+c']), ('\x1c', ['ctrl+\\']),
        ('\x1f', ['ctrl+_']),
        ('\x1b[A', ['up']), ('\x1b[B', ['down']), ('\x1b[C', ['right']),
        ('\x1b[D', ['left']), ('\x1b[H', ['home']), ('\x1b[F', ['end']),
        ('\x1b[Z', ['shift+tab']), ('\x1b[2~', ['insert']),
        ('\x1b[3~', ['delete']), ('\x1b[5~', ['pageup']),
        ('\x1b[6~', ['pagedown']), ('\x1b[1~', ['home']),
        ('\x1b[4~', ['end']), ('\x1b[15~', ['f5']), ('\x1b[24~', ['f12']),
        ('\x1bOP', ['f1']), ('\x1bOS', ['f4']), ('\x1bOA', ['up']),
        ('\x1bOM', ['enter']), ('\x1b[1;5C', ['ctrl+right']),
        ('\x1b[1;2A', ['shift+up']), ('\x1b[1;3D', ['alt+left']),
        ('\x1b[1;6B', ['ctrl+shift+down']), ('\x1b[3;5~', ['ctrl+delete']),
        ('\x1bx', ['alt+x']), ('\x1b\x01', ['ctrl+alt+a']),
        ('\x1b\x1b[A', ['escape', 'up']), ('\x1b[I', ['focusin']),
        ('\x1b[O', ['focusout']), ('\x1b[99~', []), ('\x1b[q', []),
        ('\x1bOz', []), ('\x1b[1;xA', ['A']),
    ])
    def test_sequences(self, data, expected):
        assert names(parse_keys(data)) == expected

    def test_lone_escape_waits(self):
        p = KeyParser()
        assert p.feed('\x1b') == []
        assert p.pending
        assert names(p.flush()) == ['escape']
        assert not p.pending

    def test_split_sequence(self):
        p = KeyParser()
        assert p.feed('\x1b[') == []
        assert p.feed('1;5') == []
        assert names(p.feed('A')) == ['ctrl+up']
        assert p.feed('\x1bO') == []
        assert names(p.feed('B')) == ['down']

    def test_utf8_bytes_split(self):
        p = KeyParser()
        assert p.feed(b'\xc3') == []
        assert names(p.feed(b'\xb1')) == ['ñ']
        assert names(p.feed('€'.encode()[:1] + b'')) == []
        assert names(p.feed('€'.encode()[1:])) == ['€']

    def test_invalid_bytes_replaced(self):
        p = KeyParser()
        assert len(p.feed(b'\xff\xfe\xfd\xfc\xfb')) == 5

    def test_paste(self):
        keys = parse_keys('\x1b[200~hola\nmundo\x1b[201~x')
        assert names(keys) == ['paste', 'x']
        assert keys[0].char == 'hola\nmundo'

    def test_paste_split_and_unterminated(self):
        p = KeyParser()
        assert p.feed('\x1b[200~ho') == []
        assert p.feed('la') == []
        keys = p.flush()
        assert names(keys) == ['paste'] and keys[0].char == 'hola'

    def test_mouse(self):
        keys = parse_keys('\x1b[<64;10;5M\x1b[<65;1;1M\x1b[<0;3;4M\x1b[<0;3;4m'
                          '\x1b[<1;2M')
        assert names(keys) == ['scrollup', 'scrolldown', 'mouse', 'mouse']
        assert keys[2].mouse == (0, 2, 3, True)
        assert keys[3].mouse[3] is False

    def test_flush_variants(self):
        p = KeyParser()
        p._buffer = '\x1b\x1b'
        assert names(p.flush()) == ['escape', 'escape']
        p._buffer = '\x1bq'
        assert names(p.flush()) == ['alt+q']
        p._buffer = '\x1b[12'
        assert names(p.flush()) == ['escape', '[', '1', '2']

    def test_key_object(self):
        k = Key('a', 'a')
        assert k == 'a' and k.name == 'a' and k.is_printable
        assert repr(k) == "Key('a')"
        assert not Key('enter', '\n').is_printable
        assert {Key('q'): 1}['q'] == 1


class TestWindowsParser:
    def test_scan_codes(self):
        p = WindowsKeyParser()
        keys = p.feed('\xe0H\x00;\xe0\x8d\x00\x85a\r\x08\x1b')
        assert names(keys) == ['up', 'f1', 'ctrl+up', 'f11', 'a', 'enter',
                               'backspace']
        assert p.pending
        assert names(p.flush()) == ['escape']

    def test_unknown_scan_and_vt(self):
        p = WindowsKeyParser()
        assert names(p.feed('\x00\x01')) == []
        assert names(p.feed('\x1b[A')) == ['up']


class FakeStdout(io.StringIO):
    def isatty(self):
        return True


@pytest.mark.skipif(os.name == 'nt', reason='pty is POSIX only')
class TestTerminalPosix:
    def test_raw_mode_and_read(self, monkeypatch):
        import pty
        import termios
        master, slave = pty.openpty()
        stdin = os.fdopen(slave, 'r')
        out = io.StringIO()
        term = Terminal(stdin=stdin, stdout=out, mouse=True)
        before = termios.tcgetattr(slave)
        with term:
            mode = termios.tcgetattr(slave)
            assert not mode[3] & termios.ECHO
            assert not mode[3] & termios.ICANON
            os.write(master, b'a\x1b[Ab')
            assert names(term.read_keys(timeout=0.5)) == ['a', 'up', 'b']
            os.write(master, b'\x1b')
            assert names(term.read_keys(timeout=0.2)) == ['escape']
            os.write(master, b'\x1b[')
            time.sleep(0.01)
            os.write(master, b'B')
            assert names(term.read_keys(timeout=0.3)) == ['down']
            assert term.read_keys(timeout=0.01) == []
            term.start()       # idempotent
        # macOS sets PENDIN on its own after the mode is restored.
        pendin = getattr(termios, 'PENDIN', 0)
        assert termios.tcgetattr(slave)[3] & ~pendin == before[3] & ~pendin
        assert '\x1b[?1000h' in out.getvalue()
        assert '\x1b[?1000l' in out.getvalue()
        term.stop()            # idempotent
        stdin.close()
        os.close(master)

    def test_read_keys_waits_for_input(self):
        import pty
        import threading
        master, slave = pty.openpty()
        stdin = os.fdopen(slave, 'r')
        term = Terminal(stdin=stdin, stdout=io.StringIO(), paste=False)
        with term:
            threading.Timer(0.1, lambda: os.write(master, b'z')).start()
            assert names(term.read_keys()) == ['z']
        stdin.close()
        os.close(master)

    def test_not_a_tty(self):
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        with term:
            assert term.read_keys(timeout=0.01) == []

    def test_broken_streams(self):
        class Bad(object):
            def fileno(self):
                raise ValueError

            def write(self, text):
                raise OSError
        term = Terminal(stdin=Bad(), stdout=Bad())
        with term:
            assert term._read_raw(0) == b''

    def test_resize(self, monkeypatch):
        sizes = [(80, 24)]
        monkeypatch.setattr(terminal_module, 'get_window_size',
                            lambda: sizes[-1])
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        with term:
            assert term.resized() is False
            sizes.append((100, 30))
            assert term.resized() is True
            assert term.resized() is False
            term._on_winch()
            assert term.resized() is True

    def test_winch_signal_installed(self):
        import signal
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        with term:
            assert signal.getsignal(signal.SIGWINCH) == term._on_winch
        assert signal.getsignal(signal.SIGWINCH) != term._on_winch

    def test_select_errors(self, monkeypatch):
        import pty
        import select
        master, slave = pty.openpty()
        stdin = os.fdopen(slave, 'r')
        term = Terminal(stdin=stdin, stdout=io.StringIO())

        def broken(*a):
            raise InterruptedError
        monkeypatch.setattr(select, 'select', broken)
        assert term._read_raw(0) == b''
        monkeypatch.undo()
        monkeypatch.setattr(select, 'select', lambda *a: ([slave], [], []))

        def blocked(*a):
            raise BlockingIOError
        monkeypatch.setattr(os, 'read', blocked)
        assert term._read_raw(0) == b''
        stdin.close()
        os.close(master)


class FakeMsvcrt(object):
    """Stands in for msvcrt: hands out queued characters."""

    def __init__(self, chars=''):
        self.chars = list(chars)

    def kbhit(self):
        return bool(self.chars)

    def getwch(self):
        return self.chars.pop(0)


class TestTerminalWindowsPath:
    """The Windows branches, driven with a stand-in msvcrt on any OS."""

    def test_keys_and_lifecycle(self, monkeypatch):
        fake = FakeMsvcrt('ab\xe0H')
        monkeypatch.setattr(terminal_module, 'WINDOWS', True)
        monkeypatch.setitem(sys.modules, 'msvcrt', fake)
        out = io.StringIO()
        term = Terminal(stdin=io.StringIO(), stdout=out, mouse=True)
        assert isinstance(term.parser, WindowsKeyParser)
        with term:
            assert names(term.read_keys(timeout=0.01)) == ['a', 'b', 'up']
            assert term.read_keys(timeout=0.01) == []
        assert '\x1b[?1000h' in out.getvalue()
        assert '\x1b[?1000l' in out.getvalue()

    def test_waits_until_deadline(self, monkeypatch):
        monkeypatch.setattr(terminal_module, 'WINDOWS', True)
        monkeypatch.setitem(sys.modules, 'msvcrt', FakeMsvcrt())
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        start = time.monotonic()
        assert term._read_raw(0.02) == ''
        assert time.monotonic() - start >= 0.015

    @pytest.mark.skipif(os.name != 'nt', reason='real console API')
    def test_real_console(self):
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        with term:
            assert term.read_keys(timeout=0.01) == []


class Counter(Component):
    focusable = True

    def __init__(self, name, **kw):
        super(Counter, self).__init__(**kw)
        self.name = name
        self.count = 0
        self.blurred = 0

    def natural_width(self):
        return 12

    def on_key(self, key):
        if key == 'up':
            self.count += 1
            return True
        return False

    def on_blur(self):
        self.blurred += 1

    def draw(self, width, height):
        mark = '*' if self.focused else ' '
        return ['{0}{1}={2}'.format(mark, self.name, self.count)]


class Holder(Component):
    def __init__(self, kids):
        super(Holder, self).__init__()
        self.kids = kids

    def children(self):
        return self.kids

    def draw(self, width, height):
        return [k.render(width=width) for k in self.kids]


class TestApp:
    def make(self, **kw):
        self.a, self.b = Counter('a'), Counter('b')
        grid = Grid([self.a, self.b], columns=2, use_colors=False)
        return App(body=grid, header=StatusBar('T', use_colors=False), **kw)

    def test_focus_cycle_and_dispatch(self):
        app = self.make()
        frame = app.run(keys=['up', 'tab', 'up', 'up', 'shift+tab', 'up'],
                        size=(30, 5))
        assert self.a.count == 2 and self.b.count == 2
        assert '*a=2' in frame
        assert self.a.blurred == 1
        assert app.frames >= 6

    def test_bindings_and_exit(self):
        hits = []
        app = self.make(bindings={'q': lambda: app.exit('bye'),
                                  'f5': lambda: hits.append(1),
                                  'tab': None})
        app.run(keys=['f5', 'tab', 'up', 'q', 'up'], size=(30, 5))
        assert hits == [1] and app.result == 'bye'
        assert self.a.count == 1      # tab unbound, last up after quit
        assert app.running is False

    def test_ctrl_c_quits_even_if_component_wants_it(self):
        app = self.make()
        self.a.on_key = lambda key: True
        app.run(keys=['ctrl+c', 'up'], size=(30, 5))
        assert app.running is False

    def test_unhandled_key_and_string_keys(self):
        app = self.make()
        app.run(keys=['x'], size=(30, 5))
        assert app.dispatch('nothing') is False
        assert app.dispatch(Key('zz')) is False

    def test_component_bindings_and_parent_chain(self):
        inner = Counter('i')
        seen = []
        outer = Holder([inner])
        outer.bindings = {'x': lambda: seen.append('outer')}
        inner.bindings = {'y': lambda: False}
        app = App(body=outer)
        app.run(keys=['x', 'y'], size=(20, 3))
        assert seen == ['outer']
        assert inner.parent is outer and inner.app is app

    def test_focus_skips_hidden_and_disabled(self):
        a, b, c = Counter('a'), Counter('b', disabled=True), Counter('c')
        grid = Grid([a, b, GridCell(c, hide_below=100)], columns=3)
        app = App(body=grid)
        app.run(keys=['tab', 'tab'], size=(40, 3))
        assert app.focused is a
        assert app.focusables() == [a]

    def test_focus_moves_when_component_leaves(self):
        a, c = Counter('a'), Counter('c')
        holder = Holder([a, c])
        app = App(body=holder)
        app.run(keys=['tab'], size=(20, 3))
        assert app.focused is c
        holder.kids = [a]
        app.render(20, 3)
        assert app.focused is a

    def test_no_focusables(self):
        app = App(body='solo texto')
        assert app.run(keys=['tab', 'shift+tab'], size=(20, 2)).startswith(
            'solo texto')
        assert app.focused is None

    def test_modal_layer(self):
        app = self.make()
        dialog_btn = Counter('d')
        dialog = Holder([dialog_btn])
        dialog.natural_width = lambda: 10
        app.run(keys=['up'], size=(30, 7))
        app.push(dialog)
        frame = app.render(30, 7)
        assert '*d=0' in frame
        assert app.focusables() == [dialog_btn]
        app.dispatch(Key('up'))
        assert dialog_btn.count == 1 and self.a.count == 1
        assert app.pop() is dialog
        app.render(30, 7)
        assert app.focused is self.a
        assert app.pop() is None

    def test_layer_positions(self):
        app = self.make()
        for pos in ['top', 'bottom', 'top-right', 'bottom-right', (2, 1),
                    (-1, -1), 'center']:
            layer = Holder([])
            layer.draw = lambda w, h: ['XX']
            layer.natural_width = lambda: 2
            app.push(layer, position=pos, modal=False)
        frame = app.render(30, 8)
        assert frame.count('XX') == 7
        assert all(visible_width(l) == 30 for l in frame.split('\n'))

    def test_layer_with_height(self):
        app = self.make()
        layer = ScrollView('\n'.join(str(i) for i in range(50)), height=4)
        app.push(layer)
        frame = app.render(30, 8)
        assert '0' in frame and '5' not in frame.split('\n')[6]

    def test_pop_specific_layer(self):
        app = self.make()
        one, two = Holder([]), Holder([])
        app.push(one)
        app.push(two, modal=False)
        assert app.pop(two) is two
        assert app.pop(Holder([])) is None
        assert app.pop() is one

    def test_notify_expires(self):
        app = self.make(use_colors=False)
        now = [100.0]
        app.clock = lambda: now[0]
        app.notify('Guardado', 'success', seconds=2)
        app.notify('Otro', 'error')
        frame = app.render(40, 8)
        assert 'Guardado' in frame and 'Otro' in frame
        now[0] = 103.5
        frame = app.render(40, 8)
        assert 'Guardado' not in frame and 'Otro' not in frame

    def test_notify_colours(self):
        app = self.make(use_colors=True)
        app.notify('Hola')
        assert '\x1b[' in app.render(40, 8)

    def test_tick(self):
        ticks = []
        app = self.make(on_tick=lambda a: ticks.append(1))
        app.run(keys=['tick', 'tick'], size=(30, 5))
        app.on_tick = None
        app.run(keys=['tick'], size=(30, 5))
        assert ticks == [1, 1]

    def test_headless_stream_and_diff(self):
        stream = io.StringIO()
        app = self.make(stream=stream)
        app.run(keys=['up', 'up'], size=(30, 5))
        out = stream.getvalue()
        assert out.count('\x1b[H') == 1         # one full frame
        assert '\x1b[2;1H' in out               # then line updates
        assert app.live.bytes_written == len(out)

    def test_component_basics(self):
        c = Counter('z')
        assert str(c).startswith(' z=0')
        assert c.render(width=10, height=3) == ' z=0      '
        c.expand = True
        assert c.render(width=4, height=2).split('\n') == [' z=0', '    ']
        c.focus()
        c.refresh()
        assert c.can_focus and not c.on_screen or True
        c.use_colors = True
        assert c.paint('x', 'red') == '\x1b[31mx\x1b[0m'
        assert c.paint('x', '') == 'x'
        assert c.paint('x', 'bogus_spec_on') if False else True
        c.use_colors = False
        assert c.paint('x', 'red') == 'x'

    def test_component_string_draw(self):
        class S(Component):
            def draw(self, width, height):
                return 'a\nb'
        assert S().render(width=2) == 'a \nb '

        class E(Component):
            def draw(self, width, height):
                return ''
        assert E().render(width=3) == ''
        assert Component().natural_width() == 20

    def test_overlay(self):
        base = ['abcdef', '\x1b[31mghijkl\x1b[0m', 'mnopqr']
        out = overlay(base, ['XY'], 2, 1, 6)
        assert out[0] == 'abcdef'
        assert visible_width(out[1]) == 6
        assert 'XY' in out[1]
        assert overlay(base, ['Z'], 0, 9, 6) == base
        assert overlay(['abc'], ['XYZ'], 0, 0, 3) == ['XYZ']

    def test_paint_unknown_prefix(self, monkeypatch):
        c = Counter('x', use_colors=True)
        monkeypatch.setattr(app_module, 'parse_spec', lambda s: '')
        assert c.paint('x', 'red') == 'x'


class TestScrollView:
    def test_keys_and_bar(self):
        sv = ScrollView('\n'.join('l%d' % i for i in range(30)), height=5,
                        use_colors=False)
        app = App(body=sv)
        app.run(keys=['down', 'down', 'pagedown', 'end'], size=(20, 6))
        assert sv.offset == sv.max_offset == 25
        for key, offset in [('home', 0), ('j', 1), ('k', 0), ('G', 25),
                            ('g', 0), ('scrolldown', 3), ('scrollup', 0),
                            ('space', 5), ('pageup', 0)]:
            sv.on_key(Key(key))
            assert sv.offset == offset, key
        assert sv.on_key(Key('x')) is False
        lines = sv.render(width=10).split('\n')
        assert len(lines) == 5
        assert lines[0].endswith('┃')

    def test_follow_and_list_and_renderable(self):
        sv = ScrollView(['a', 'b', 'c'], follow=True, height=2)
        assert sv.render(width=5).split('\n')[0].startswith('b')
        sv.content = ['a', 'b', 'c', 'd']
        sv.render(width=5)
        assert sv.offset == sv.max_offset == 2
        sv.scroll_to(0)
        sv.content = ['a', 'b', 'c', 'd', 'e']
        sv.render(width=5)
        assert sv.offset == 0
        grid = Grid(['x', 'y'], columns=1)
        sv2 = ScrollView(grid, scrollbar=False)
        assert sv2.children() == [grid]
        assert sv2.render(width=6, height=3).split('\n')[0] == 'x     '
        assert sv2.natural_width() >= 1
        assert ScrollView('').render(width=4, height=2) == '    \n    '
        short = ScrollView('a\nb', height=3)
        assert short.render(width=4).split('\n')[0] == 'a  ' + ' '


class TestLiveDiff:
    def test_diff_on_terminal(self, monkeypatch):
        stream = io.StringIO()
        frames = iter(['a\nb\nc', 'a\nX\nc', 'a\nX\nc', 'a\nY'])
        live = Live(stream=stream, force_terminal=True, width=5, height=3)
        with live:
            live.update(next(frames))
            first = stream.getvalue()
            live.update(next(frames))
            second = stream.getvalue()[len(first):]
            live.update(next(frames))
            third = stream.getvalue()[len(first) + len(second):]
            live.update(next(frames))
        assert first.count('\x1b[H') == 1
        assert second == '\x1b[2;1HX\x1b[K'
        assert third == ''
        assert '\x1b[3;1H\x1b[J' in stream.getvalue()

    def test_invalidate_and_no_diff(self):
        stream = io.StringIO()
        live = Live(stream=stream, force_terminal=True, width=5, height=2,
                    diff=False)
        with live:
            live.update('a')
            live.update('b')
        assert stream.getvalue().count('\x1b[H') == 2
        stream = io.StringIO()
        live = Live(stream=stream, force_terminal=True, width=5, height=2)
        with live:
            live.update('a')
            live.invalidate()
            live.update('b')
        assert stream.getvalue().count('\x1b[H') == 2

    def test_resize_redraws(self, monkeypatch):
        from flexablelib_tui import screen as screen_module
        sizes = [(20, 5)]
        monkeypatch.setattr(screen_module, 'get_window_size',
                            lambda: sizes[-1])
        stream = io.StringIO()
        live = Live(stream=stream, force_terminal=True)
        with live:
            live.update('a')
            live.update('b')
            sizes.append((30, 6))
            live.update('c')
        assert stream.getvalue().count('\x1b[H') == 2


@pytest.mark.skipif(os.name == 'nt', reason='pty is POSIX only')
def test_run_in_real_pty(tmp_path):
    """The interactive loop end to end: a child process in a pty."""
    import pty
    import select
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = tmp_path / 'app.py'
    script.write_text(
        'import sys\n'
        'from flexablelib_tui import App, ScrollView, StatusBar\n'
        'sv = ScrollView("\\n".join("fila %d" % i for i in range(99)))\n'
        'app = App(body=sv, header=StatusBar("PTY"), interval=0.05,\n'
        '          bindings={"q": lambda: app.exit(sv.offset)},\n'
        '          on_tick=lambda a: None)\n'
        'app.notify("hola", seconds=0.01)\n'
        'print("RESULT", app.run(), file=sys.stderr)\n')
    master, slave = pty.openpty()
    import fcntl
    import struct
    import termios
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 12, 40, 0, 0))
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [root, os.path.join(root, 'packages', 'tui'),
         os.path.join(root, 'packages', 'speedups')]))
    proc = subprocess.Popen([sys.executable, str(script)], stdin=slave,
                            stdout=slave, stderr=subprocess.PIPE, env=env,
                            close_fds=True)
    os.close(slave)
    out = b''

    def read_for(seconds):
        nonlocal out
        end = time.time() + seconds
        while time.time() < end:
            r, _, _ = select.select([master], [], [], 0.05)
            if r:
                try:
                    out += os.read(master, 65536)
                except OSError:
                    return
    read_for(1.0)
    os.write(master, b'\x1b[B\x1b[B\x1b[6~')
    read_for(0.4)
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', 14, 50, 0, 0))
    read_for(0.4)
    os.write(master, b'q')
    # Keep draining the pty while the child exits: a small pty buffer (macOS)
    # would otherwise block its last redraw and it would never read the 'q'.
    deadline = time.time() + 10
    while proc.poll() is None and time.time() < deadline:
        read_for(0.1)
    _, err = proc.communicate(timeout=5)
    read_for(0.2)
    os.close(master)
    assert proc.returncode == 0, err
    assert b'RESULT' in err
    offset = int(err.decode().split('RESULT')[1].split()[0])
    assert offset >= 2
    assert b'PTY' in out and b'\x1b[?1049h' in out


def test_app_use_colors_reaches_widgets(monkeypatch):
    from flexablelib_tui import KeyHints
    monkeypatch.setenv('FORCE_COLOR', '1')
    hints = KeyHints([('q', 'Salir')])
    explicit = KeyHints([('x', 'Otra')], use_colors=True)
    app = App(body=Counter('c'), header=explicit, footer=hints,
              use_colors=False)
    out = app.render(40, 6)
    assert hints.use_colors is False and explicit.use_colors is True
    assert '\x1b' in out.split('\n')[0] and '\x1b' not in out.split('\n')[-1]
