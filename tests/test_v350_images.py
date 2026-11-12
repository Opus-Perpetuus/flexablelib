"""3.5.0: pictures in the terminal -- detection per terminal, the escape
sequences of each method, the fallback chain down to the link and the
no-browser warning, marks inside layouts and Live, and the Image /
ImageViewer components."""

import io
import os

import pytest

g = pytest.importorskip('flexablelib_tui.graphics')
fc = pytest.importorskip('flexablelib_components')

from flexablelib import Card, Grid, _frames as _fx, _images as I
from flexablelib.text_width import visible_width
from flexablelib_tui import App, Live, accessibility as a11y
from flexablelib_tui.keys import Key, KeyParser, MouseEvent

CLEAN = ('FLEXABLELIB_IMAGE', 'FLEXABLELIB_NO_BROWSER', 'BROWSER', 'DISPLAY',
         'WAYLAND_DISPLAY', 'TMUX', 'NO_COLOR', 'SSH_CONNECTION', 'SSH_TTY',
         'WSL_DISTRO_NAME')


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in CLEAN:
        monkeypatch.delenv(name, raising=False)
    g.reset_cache()
    with a11y.configure(screen_reader=False, ascii=False,
                        reduced_motion=False):
        yield
    g.reset_cache()


@pytest.fixture
def picture(tmp_path):
    out = bytearray()
    for y in range(40):
        for x in range(60):
            out += bytes([x * 4, y * 6, 120, 255])
    path = tmp_path / 'foto.png'
    path.write_bytes(I.encode_png(I.Bitmap(60, 40, out)))
    return str(path)


def info(**kw):
    base = dict(color='truecolor', unicode=True, cell=(10, 20),
                cell_known=True, order=['kitty', 'iterm', 'sixel'])
    base.update(kw)
    return g.GraphicsInfo(**base)


def use(monkeypatch, gi):
    monkeypatch.setattr(g, 'detect', lambda *a, **k: gi)


def responses(text):
    return [k for k in KeyParser().feed(text) if str(k) == 'response']


# -- detection ------------------------------------------------------------------

class TestGuess:
    T = {'TERM': 'xterm-256color', 'LANG': 'C.UTF-8'}

    def env(self, **kw):
        env = dict(self.T)
        env.update(kw)
        return env

    @pytest.mark.parametrize('env,want', [
        ({'TERM': 'xterm-kitty'}, 'kitty'),
        ({'KITTY_WINDOW_ID': '1'}, 'kitty'),
        ({'TERM_PROGRAM': 'ghostty'}, 'kitty'),
        ({'TERM_PROGRAM': 'WezTerm'}, 'iterm'),
        ({'TERM_PROGRAM': 'iTerm.app'}, 'iterm'),
        ({'TERM_PROGRAM': 'vscode'}, 'iterm'),
        ({'TERM_PROGRAM': 'mintty'}, 'iterm'),
        ({'KONSOLE_VERSION': '230804'}, 'iterm'),
        ({'TERM_PROGRAM': 'WarpTerminal'}, 'kitty'),
        ({'TERM_PROGRAM': 'rio'}, 'iterm'),
        ({'TERM': 'foot'}, 'sixel'),
        ({'TERM': 'mlterm'}, 'sixel'),
        ({'TERM_PROGRAM': 'contour'}, 'sixel'),
        ({'TERM_PROGRAM': 'Apple_Terminal'}, 'text'),
        ({'TERM': 'screen-256color', 'STY': '1.x'}, 'text'),
        ({'WT_SESSION': 'x'}, 'text'),
        ({}, 'text'),
    ])
    def test_terminals(self, env, want):
        gi = g.guess(self.env(**env), platform='posix', tmux=None)
        assert gi.best() == want, gi.reasons

    def test_dumb_and_linux(self):
        assert g.guess({'TERM': 'dumb'}, 'posix').best() == 'alt'
        gi = g.guess({'TERM': 'linux'}, 'posix')
        assert gi.pixel_methods == []

    def test_windows_has_no_kitty(self):
        gi = g.guess(self.env(TERM='xterm-kitty'), platform='nt')
        assert not gi.kitty
        assert any('ConPTY' in r for r in gi.reasons)

    def test_tmux(self):
        env = self.env(TMUX='/tmp/x,1,0')
        gi = g.guess(env, 'posix', tmux=('xterm-kitty', 'RGB', True))
        assert gi.kitty and gi.kitty_placeholders and not gi.iterm
        gi = g.guess(env, 'posix', tmux=('xterm-kitty', 'RGB', False))
        assert not gi.kitty
        gi = g.guess(env, 'posix', tmux=('foot', 'RGB,sixel', False))
        assert gi.best() == 'sixel'

    def test_tmux_client(self, monkeypatch):
        assert g._tmux_client({}) is None
        import shutil
        monkeypatch.setattr(shutil, 'which', lambda n: None)
        assert g._tmux_client({'TMUX': '1'}) == ('', '', False)
        monkeypatch.setattr(shutil, 'which', lambda n: '/usr/bin/tmux')
        import subprocess

        class R:
            def __init__(self, out):
                self.stdout = out
        outs = iter(['xterm-kitty|RGB,sixel|3.4\n', 'on\n'])
        monkeypatch.setattr(subprocess, 'run', lambda *a, **k: R(next(outs)))
        name, feats, passthrough = g._tmux_client({'TMUX': '1'})
        assert name == 'xterm-kitty' and 'sixel' in feats and passthrough

        def boom(*a, **k):
            raise OSError('x')
        monkeypatch.setattr(subprocess, 'run', boom)
        assert g._tmux_client({'TMUX': '1'}) == ('', '', False)

    def test_summary_and_repr(self):
        gi = g.guess(self.env(TERM='xterm-kitty'), 'posix')
        text = '\n'.join(gi.summary())
        assert 'kitty graphics: sí' in text and 'Método: kitty' in text
        assert 'kitty=True' in repr(gi)
        assert gi.as_dict()['kitty'] is True


class TestResponses:
    def test_kitty_ok_and_cell(self):
        gi = info(kitty=None, cell_known=False)
        done = g.apply_responses(gi, responses(
            '\x1b_Gi=31;OK\x1b\\\x1b[6;18;9t\x1b[?1;0;1024S'
            '\x1bP>|kitty(0.32.1)\x1b\\\x1b[?62;4;22c'))
        assert done and gi.kitty and gi.sixel and gi.kitty_placeholders
        assert gi.cell == (9, 18) and gi.cell_known
        assert gi.sixel_colors == 1024
        assert gi.version.startswith('kitty')

    def test_old_kitty_and_errors(self):
        gi = info()
        g.apply_responses(gi, responses('\x1bP>|kitty(0.26.0)\x1b\\'))
        assert gi.kitty_placeholders is False
        gi = info(kitty=None)
        g.apply_responses(gi, responses('\x1b_Gi=31;ENOTSUPPORTED\x1b\\'))
        assert gi.kitty is False

    def test_other_versions(self):
        for name, attr in (('ghostty 1.0', 'kitty_placeholders'),
                           ('WezTerm 2024', 'iterm'), ('iTerm2 3.5', 'iterm')):
            gi = info(kitty_placeholders=None, iterm=None)
            g.apply_responses(gi, responses('\x1bP>|' + name + '\x1b\\'))
            assert getattr(gi, attr) is True

    def test_window_pixels(self, monkeypatch):
        gi = info(cell_known=False)
        g.apply_responses(gi, responses('\x1b[4;480;800t\x1b[?62;22c'))
        assert gi.sixel is False
        import flexablelib.utils as u
        monkeypatch.setattr(u, 'get_window_size', lambda: (80, 24))
        g._finish(gi)
        assert gi.cell == (10, 20) and gi.cell_known

    def test_ignores_other_keys(self):
        gi = info()
        assert not g.apply_responses(gi, [Key('a'), Key('response')])


class FakeTerminal:
    def __init__(self, answer, tty=True):
        self.answer = answer
        self.tty = tty
        self.written = []
        self.replayed = None
        self.stdout = io.StringIO()

    def is_tty(self):
        return self.tty

    def write(self, text):
        self.written.append(text)

    def read_keys(self, timeout=0, responses=False):
        keys, self.answer = KeyParser().feed(self.answer), ''
        return keys

    def replay(self, keys):
        self.replayed = list(keys)


class TestProbe:
    ENV = {'TERM': 'xterm-256color', 'LANG': 'C.UTF-8'}

    def test_probe_terminal(self):
        term = FakeTerminal('x\x1b_Gi=31;OK\x1b\\\x1b[6;16;8t\x1b[?62;4c')
        gi = g.probe_terminal(term, env=self.ENV)
        assert g.GRAPHICS_QUERY in term.written[0]
        assert '\x1b[>0q' in term.written[0] and '\x1b[c' in term.written[0]
        assert gi.kitty and gi.sixel and gi.probed
        assert gi.cell == (8, 16)
        assert [str(k) for k in term.replayed] == ['x']
        assert g.detect(env=self.ENV) is gi        # cached

    def test_no_probe_for_dumb_tmux_apple(self):
        for env in ({'TERM': 'dumb'}, {'TERM': 'xterm', 'TMUX': '1'},
                    {'TERM': 'xterm', 'TERM_PROGRAM': 'Apple_Terminal'},
                    {'TERM': 'linux'}):
            term = FakeTerminal('')
            if env.get('TMUX'):
                g.probe_terminal.__globals__['_tmux_client']  # exists
            gi = g.guess(env, 'posix', tmux=('', '', False)
                         if 'TMUX' in env else None)
            assert not g._query_wanted(gi, env)

    def test_detect_without_tty(self, monkeypatch):
        gi = g.detect(env=self.ENV, probe=False, refresh=True)
        assert gi.probed is False
        monkeypatch.setattr(g, 'cell_size', lambda stream=None: (7, 14))
        gi = g.detect(env=self.ENV, probe=False, refresh=True)
        assert gi.cell == (7, 14)

    def test_query_real_pty(self):
        pty = pytest.importorskip('pty')
        import threading
        import select
        master, slave = pty.openpty()
        name = os.ttyname(slave)
        answers = ('\x1b_Gi=31;OK\x1b\\\x1b[6;20;10t\x1b[4;480;800t'
                   '\x1b[?1;0;256S\x1bP>|kitty(0.35.2)\x1b\\\x1b[?62;4;22c')
        seen = []

        def terminal():
            buf = b''
            while b'\x1b[c' not in buf:
                r, _, _ = select.select([master], [], [], 2)
                if not r:
                    return
                buf += os.read(master, 4096)
            seen.append(buf)
            os.write(master, answers.encode())
        t = threading.Thread(target=terminal)
        t.start()
        try:
            gi = g.query(g.guess(self.ENV, 'posix'), self.ENV, timeout=2,
                         tty_path=name)
        finally:
            t.join(3)
            os.close(master)
            os.close(slave)
        assert seen and b'\x1b_Gi=31' in seen[0]
        assert gi.probed and gi.kitty and gi.sixel and gi.cell == (10, 20)
        assert gi.version == 'kitty(0.35.2)' and gi.kitty_placeholders

    def test_query_timeout_and_errors(self, tmp_path):
        gi = g.query(g.guess(self.ENV, 'posix'), self.ENV, timeout=0.05,
                     tty_path=str(tmp_path / 'none'))
        assert not gi.probed
        assert g.query(None, {'TERM': 'dumb'}).dumb
        regular = tmp_path / 'file'
        regular.write_text('')
        gi = g.query(g.guess(self.ENV, 'posix'), self.ENV, timeout=0.05,
                     tty_path=str(regular))
        assert not gi.probed

    def test_cell_size(self):
        assert g.cell_size(io.StringIO()) is None
        pty = pytest.importorskip('pty')
        import fcntl
        import struct
        import termios
        master, slave = pty.openpty()
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ,
                        struct.pack('HHHH', 24, 80, 800, 480))
            with os.fdopen(os.dup(slave), 'w') as stream:
                assert g.cell_size(stream) == (10, 20)
            fcntl.ioctl(slave, termios.TIOCSWINSZ,
                        struct.pack('HHHH', 24, 80, 0, 0))
            with os.fdopen(os.dup(slave), 'w') as stream:
                assert g.cell_size(stream) is None
        finally:
            os.close(master)
            os.close(slave)


class TestChoose:
    def test_chain(self):
        assert g.choose(info(kitty=True), env={})[0] == 'kitty'
        assert g.choose(info(iterm=True), env={})[0] == 'iterm'
        assert g.choose(info(sixel=True), env={})[0] == 'sixel'
        assert g.choose(info(), env={})[:2] == ('text', 'half')
        assert g.choose(info(), env={}, color='none')[:2] == \
            ('text', 'braille')
        assert g.choose(info(unicode=False), env={})[:2] == ('text', 'ascii')
        assert g.choose(info(kitty=True), env={}, ascii=True)[:2] == \
            ('text', 'ascii')
        assert g.choose(info(kitty=True), env={}, blocks='sextant')[0] == \
            'kitty'
        assert g.choose(info(), env={}, blocks='sextant')[1] == 'sextant'

    def test_reader_and_dumb_mean_alt(self):
        assert g.choose(info(kitty=True), env={}, screen_reader=True)[0] == \
            'alt'
        assert g.choose(info(dumb=True), force='kitty', env={})[0] == 'alt'

    @pytest.mark.parametrize('force,want', [
        ('kitty', ('kitty', None)), ('iterm', ('iterm', None)),
        ('sixel', ('sixel', None)), ('blocks', ('text', 'half')),
        ('braille', ('text', 'braille')), ('ascii', ('text', 'ascii')),
        ('link', ('link', None)), ('none', ('none', None)),
        ('auto', ('text', 'half'))])
    def test_force(self, force, want):
        assert g.choose(info(), env={'FLEXABLELIB_IMAGE': force})[:2] == want
        assert g.choose(info(), force=force, env={})[:2] == want

    def test_forced_blocks_without_unicode(self):
        assert g.choose(info(unicode=False), force='quadrant',
                        env={})[1] == 'ascii'


# -- escape sequences -----------------------------------------------------------

class TestSequences:
    def test_kitty(self):
        seq = g.kitty_sequence(b'\x89PNG' * 2000, 42, 10, 5, chunk=4096)
        first = seq.split('\x1b\\')[0]
        assert first.startswith('\x1b_Ga=T,f=100,i=42,q=2,p=1,C=1,c=10,r=5,')
        assert 'm=1;' in first
        assert seq.count('\x1b_G') == 3 and seq.endswith('\x1b\\')
        assert 'm=0;' in seq.split('\x1b_G')[-1]
        ph = g.kitty_sequence(b'x', 7, 3, 2, placeholder=True)
        assert 'U=1' in ph and 'p=1' not in ph
        assert g.kitty_delete(7) == '\x1b_Ga=d,d=I,i=7,q=2\x1b\\'

    def test_tmux_wrap(self):
        w = g.kitty_sequence(b'x', 7, placeholder=True, tmux=True)
        assert w.startswith('\x1bPtmux;\x1b\x1b_G') and w.endswith('\x1b\\')
        assert g.kitty_delete(7, tmux=True).startswith('\x1bPtmux;')

    def test_placeholders(self):
        rows = g.kitty_placeholder_rows(0x010203, 4, 2)
        assert rows[0].startswith('\x1b[38;2;1;2;3m')
        assert rows[1].count(g.PLACEHOLDER) == 4
        assert g.DIACRITICS[1] in rows[1]
        assert all(visible_width(r) == 4 for r in rows)
        assert len(g.DIACRITICS) == 297

    def test_iterm(self):
        seq = g.iterm_sequence(b'abc', 100, 50, name='a.png')
        assert seq.startswith('\x1b]1337;File=inline=1;size=3;name=YS5wbmc=;'
                              'width=100px;height=50px;preserveAspectRatio=1:')
        assert seq.endswith('YWJj\x07')
        assert 'width=4;height=2' in g.iterm_sequence(b'a', cols=4, rows=2)

    def test_sixel(self):
        bm = I.Bitmap(4, 6, bytes([255, 0, 0, 255]) * 24)
        seq = g.sixel_sequence(bm, 16)
        assert seq.startswith('\x1bP0;1;0q"1;1;4;6#0;2;100;0;0')
        assert seq.endswith('\x1b\\')

    def test_hyperlink_and_url(self, tmp_path):
        assert g.hyperlink('http://x', 'y') == \
            '\x1b]8;;http://x\x1b\\y\x1b]8;;\x1b\\'
        assert g.file_url('http://a/b.png') == 'http://a/b.png'
        assert g.file_url(str(tmp_path / 'a b.png')).startswith('file:///')
        assert '%20' in g.file_url(str(tmp_path / 'a b.png'))


# -- marks ------------------------------------------------------------------------

class TestMarks:
    def test_expand_cursor_picture(self):
        key = g.register('PIX', 3, 2, 'sixel')
        line = 'ab' + g.mark(key) + '\x1b[1m   \x1b[0mcd'
        assert visible_width(line) == 7
        out = g.expand(line)
        assert out == 'ab\x1b7\x1b[1APIX\x1b8\x1b[1m\x1b[3C\x1b[0mcd'
        assert _fx.expand_graphics(line) == out
        assert g.expand('plain') == 'plain'

    def test_expand_placeholder_and_unknown(self):
        key = g.register('APC', 2, 1, 'placeholder', 9)
        assert g.expand(g.mark(key) + 'xx') == 'APCxx'
        assert g.expand(g.mark('deadbeef') + 'x') == 'x'
        one = g.register('ONE', 2, 1, 'iterm')
        assert '\x1b[1A' not in g.expand(g.mark(one) + '  ')

    def test_register_is_stable_and_bounded(self):
        a = g.register('same', 1, 1, 'sixel')
        assert g.register('same', 1, 1, 'sixel') == a
        for n in range(g._MAX_PAYLOADS + 5):
            g.register('p{0}'.format(n), 1, 1, 'sixel')
        assert len(g._PAYLOADS) == g._MAX_PAYLOADS

    def test_render_diff_redraws_covered_picture(self):
        key = g.register('PIC', 2, 2, 'sixel')
        old = ['  x', g.mark(key) + '  y', 'zz']
        new = ['  X', g.mark(key) + '  y', 'zz']
        out = g.render_diff(old, new)
        assert '\x1b[1;1H  X' in out and 'PIC' in out
        assert g.render_diff(new, new) == ''
        out = g.render_diff(new, ['  X'])
        assert '\x1b[2;1H\x1b[J' in out

    def test_cleanup_deletes_kitty_images(self):
        key = g.register('K', 2, 1, 'kitty', 77)
        out = g.cleanup([g.mark(key) + '  '], ['nothing'])
        assert out == g.kitty_delete(77)
        assert g.cleanup(None, ['x']) == ''
        assert g.marks_in(['a', g.mark(key)]) == [(1, key, 1, 'kitty')]

    def test_layout_without_colour_keeps_marks(self):
        key = g.register('S', 3, 1, 'sixel')
        card = Card('t', body=g.mark(key) + '   ', use_colors=False)
        assert g.mark(key) in card.render(width=20)
        assert 'S' in str(card)


# -- browsers ---------------------------------------------------------------------

def which_from(*names):
    return lambda name: '/usr/bin/' + name if name in names else None


class TestBrowser:
    def test_no_display_no_browser(self):
        ok, why = g.browser_available({}, 'linux', which_from('xdg-open'))
        assert not ok and 'DISPLAY' in why

    def test_variants(self):
        assert g.browser_available({'BROWSER': 'w3m'}, 'linux',
                                   which_from()) == (True, 'BROWSER')
        assert g.browser_available({'DISPLAY': ':0'}, 'linux',
                                   which_from('xdg-open')) == \
            (True, 'xdg-open')
        assert g.browser_available({'WAYLAND_DISPLAY': 'w'}, 'linux',
                                   which_from('gio')) == (True, 'gio')
        assert g.browser_available({'DISPLAY': ':0'}, 'linux',
                                   which_from())[0] is False
        assert g.browser_available({}, 'win32', which_from()) == \
            (True, 'start')
        assert g.browser_available({}, 'darwin', which_from('open')) == \
            (True, 'open')
        assert not g.browser_available({}, 'darwin', which_from())[0]
        assert not g.browser_available({'SSH_TTY': '/dev/pts/1'}, 'darwin',
                                       which_from('open'))[0]
        assert g.browser_available({'WSL_DISTRO_NAME': 'U'}, 'linux',
                                   which_from('wslview')) == (True, 'wslview')
        assert g.browser_available({'FLEXABLELIB_NO_BROWSER': '1',
                                    'BROWSER': 'x'}, 'linux',
                                   which_from()) == \
            (False, 'FLEXABLELIB_NO_BROWSER')

    def test_wsl_detection(self, monkeypatch):
        import builtins

        def fake_open(*a, **k):
            raise OSError('no proc')
        monkeypatch.setattr(builtins, 'open', fake_open)
        assert g._wsl({}) is False
        assert g._wsl({'WSL_DISTRO_NAME': 'x'}) is True

    def test_open_never_runs_without_browser(self):
        calls = []
        ok, why = g.open_external('/tmp/a.png', env={}, platform='linux',
                                  which=which_from('xdg-open'),
                                  runner=calls.append)
        assert not ok and calls == []

    def test_open_commands(self):
        calls = []
        assert g.open_external('/tmp/a.png', {'DISPLAY': ':0'}, 'linux',
                               which_from('xdg-open'), calls.append)[0]
        assert calls[-1][1].startswith('file:///')
        assert calls[-1][1].endswith('/tmp/a.png')
        g.open_external('/tmp/a.png', {'DISPLAY': ':0'}, 'linux',
                        which_from('gio'), calls.append)
        assert calls[-1][:2] == ['gio', 'open']
        g.open_external('http://x/y', {'BROWSER': 'firefox --new %s'},
                        'linux', which_from(), calls.append)
        assert calls[-1] == ['firefox', '--new', 'http://x/y']
        g.open_external('http://x/y', {'BROWSER': 'lynx'}, 'linux',
                        which_from(), calls.append)
        assert calls[-1] == ['lynx', 'http://x/y']
        g.open_external('http://x/y', {}, 'win32', which_from(),
                        calls.append)
        assert calls[-1][:3] == ['cmd', '/c', 'start']

        def boom(cmd):
            raise OSError('cannot')
        assert g.open_external('http://x', {'BROWSER': 'b'}, 'linux',
                               which_from(), boom) == (False, 'cannot')


# -- components -------------------------------------------------------------------

def plain(text):
    return _fx.strip_ansi(text)


class TestImage:
    def test_text_modes(self, monkeypatch, picture):
        use(monkeypatch, info())
        for mode in ('half', 'quadrant', 'sextant', 'braille', 'ascii'):
            img = fc.Image(picture, alt='Degradado', method=mode, width=12,
                           use_colors=True)
            lines = img.render(20).split('\n')
            assert img.used_method == mode
            assert all(visible_width(l) == 20 for l in lines)
            # 60x40 px into 12 columns of 10x20 px cells -> 4 rows
            assert len(lines) == 4

    def test_auto_picks_pixels(self, monkeypatch, picture):
        use(monkeypatch, info(kitty=True, kitty_placeholders=True))
        img = fc.Image(picture, alt='x', width=6, use_colors=True)
        out = img.render(6)
        assert img.used_method == 'kitty'
        assert g.PLACEHOLDER in out and g.MARK in out
        printed = str(img)
        assert '\x1b_Ga=T,f=100' in printed and 'U=1' in printed
        assert g.MARK not in printed

    def test_kitty_direct_iterm_sixel(self, monkeypatch, picture):
        for gi, method, needle in (
                (info(kitty=True, kitty_placeholders=False), 'kitty',
                 'p=1,C=1'),
                (info(iterm=True), 'iterm', '\x1b]1337;File=inline=1'),
                (info(sixel=True, sixel_colors=16), 'sixel', '\x1bP0;1;0q')):
            use(monkeypatch, gi)
            img = fc.Image(picture, alt='x', width=8, use_colors=True)
            frame = img.render(10)
            assert img.used_method == method
            assert all(visible_width(l) == 10 for l in frame.split('\n'))
            out = str(img)
            assert needle in out and '\x1b7' in out and '\x1b8' in out
            assert img.render(10) == frame        # cached

    def test_fits(self, monkeypatch, picture):
        use(monkeypatch, info())
        sizes = {}
        for fit in ('contain', 'cover', 'fill', 'none'):
            img = fc.Image(picture, alt='x', fit=fit, method='half',
                           height=3, use_colors=True)
            sizes[fit] = img.render(20, 3).split('\n')
        assert len(sizes['contain']) == 3
        assert len(sizes['cover']) == 3 and len(sizes['fill']) == 3
        img = fc.Image(picture, fit='none', method='half', use_colors=True)
        assert len(img.render(80).split('\n')) == 2   # 40 px / 20 px
        with pytest.raises(ValueError):
            fc.Image(picture, fit='zoom')

    def test_no_upscale_and_align(self, monkeypatch, picture):
        use(monkeypatch, info())
        img = fc.Image(picture, method='half', upscale=False, align='right')
        lines = img.render(30).split('\n')
        assert lines[0].startswith(' ' * 24)        # 6 columns at the right
        img = fc.Image(picture, method='half', align='left')
        assert img.render(30)

    def test_too_small_falls_back(self, monkeypatch, picture):
        use(monkeypatch, info())
        monkeypatch.setattr(g, 'browser_available',
                            lambda *a, **k: (False, 'sin pantalla'))
        img = fc.Image(picture, method='half')
        out = plain(img.render(1))
        assert img.used_method == 'warning'
        assert out.startswith('⚠') or out.startswith('!')

    def test_link_when_browser(self, monkeypatch, picture):
        use(monkeypatch, info())
        monkeypatch.setattr(g, 'browser_available',
                            lambda *a, **k: (True, 'xdg-open'))
        img = fc.Image(picture, alt='x', method='link', use_colors=True)
        out = img.render(60)
        assert img.used_method == 'link'
        assert '\x1b]8;;file://' in out and 'foto.png' in out

    def test_warning_without_browser_never_opens(self, monkeypatch, picture):
        use(monkeypatch, info())
        monkeypatch.delenv('DISPLAY', raising=False)
        monkeypatch.delenv('BROWSER', raising=False)
        monkeypatch.setenv('FLEXABLELIB_IMAGE', 'link')
        real = g.browser_available
        monkeypatch.setattr(        # a Linux box without a display
            g, 'browser_available',
            lambda env=None, platform=None, which=None: real(env, 'linux',
                                                             which))
        monkeypatch.setattr(g, '_wsl', lambda env: False)
        import webbrowser
        import subprocess
        opened = []
        monkeypatch.setattr(webbrowser, 'open',
                            lambda *a, **k: opened.append(a))
        monkeypatch.setattr(subprocess, 'Popen',
                            lambda *a, **k: opened.append(a))
        img = fc.Image(picture, alt='x', focusable=True)
        out = plain(img.render(70))
        assert img.used_method == 'warning'
        assert 'foto.png' in out and 'navegador' in out
        assert '⚠' in out
        assert img.handle_key(Key('enter'))
        assert img.on_mouse(MouseEvent(0, 1, 1, True))
        assert not img.on_mouse(MouseEvent(0, 1, 1, False))
        assert opened == []
        with a11y.configure(ascii=True):
            assert plain(img.render(70)).startswith('!')

    def test_open_with_browser(self, monkeypatch, picture):
        calls = []
        monkeypatch.setattr(g, 'open_external',
                            lambda url: calls.append(url) or (True, 'x'))
        img = fc.Image(picture, alt='x', focusable=True)
        assert img.open() and calls[0].startswith('file://')
        hook = []
        img.on_open = hook.append
        img.open()
        assert hook == [img]
        assert fc.Image(b'\x89PNG').open() is False
        assert not img.on_key(Key('x'))

    def test_broken_image(self, monkeypatch, tmp_path):
        use(monkeypatch, info())
        monkeypatch.setattr(g, 'browser_available',
                            lambda *a, **k: (False, 'sin pantalla'))
        bad = tmp_path / 'bad.png'
        bad.write_bytes(b'\x89PNG\r\n\x1a\nxxxx')
        img = fc.Image(str(bad), alt='Roto', method='half')
        out = plain(img.render(80))
        assert img.used_method == 'warning' and 'bad.png' in out
        assert 'no se puede mostrar' in img.a11y_value()
        img = fc.Image(str(tmp_path / 'missing.png'), method='half')
        img.render(80)
        assert img.error
        img.reload()
        assert img.error is None

    def test_bytes_source_has_no_url(self, monkeypatch, picture):
        use(monkeypatch, info())
        data = open(picture, 'rb').read()
        img = fc.Image(data, alt='x', method='link')
        assert img.url is None and img.name == 'imagen'
        out = plain(img.render(80))
        assert 'sin archivo ni URL' in out

    def test_reader_and_dumb_show_alt(self, monkeypatch, picture):
        use(monkeypatch, info(kitty=True))
        img = fc.Image(picture, alt='Logo de la empresa')
        with a11y.configure(screen_reader=True):
            assert plain(img.render(60)).startswith(
                'Imagen: Logo de la empresa (foto.png)')
        use(monkeypatch, info(dumb=True))
        assert 'Logo' in img.render(60) and img.used_method == 'alt'
        assert img.describe()

    def test_no_color_is_mono(self, monkeypatch, picture):
        use(monkeypatch, info())
        img = fc.Image(picture, alt='x', use_colors=False)
        out = img.render(20)
        assert img.used_method == 'braille' and '\x1b[' not in out
        use(monkeypatch, info(sixel=True))
        img = fc.Image(picture, alt='x', use_colors=False, width=6)
        img.render(6)
        assert img.used_method == 'sixel'       # pixels, in grey

    def test_none_method_and_caption(self, monkeypatch, picture):
        use(monkeypatch, info())
        img = fc.Image(picture, alt='Gráfica', method='none')
        assert plain(img.render(20)).strip() == '[Gráfica]'
        img = fc.Image(picture, alt='Gráfica', method='half', caption=True,
                       height=4, use_colors=True)
        lines = img.render(20, 4).split('\n')
        assert 'Gráfica' in plain(lines[-1])
        assert '\x1b]8;;file://' in lines[-1]

    def test_focus_is_visible(self, monkeypatch, picture):
        use(monkeypatch, info())
        img = fc.Image(picture, alt='x', method='half', focusable=True)
        assert not a11y.audit([img], width=20)
        assert [i.message for i in a11y.audit([fc.Image(picture)])] == \
            ['no alt text']

    def test_background_and_animation(self, monkeypatch, tmp_path):
        Image = pytest.importorskip('PIL.Image')
        use(monkeypatch, info())
        frames = [Image.new('RGBA', (8, 8), c) for c in
                  ((255, 0, 0, 128), (0, 255, 0, 255))]
        path = tmp_path / 'a.gif'
        frames[0].save(path, save_all=True, append_images=frames[1:],
                       duration=50, loop=0)
        img = fc.Image(str(path), alt='x', animate=True, method='half',
                       background='#fff', use_colors=True)
        img.render(4)
        assert len(img._frames) == 2
        assert img.bitmap() is not None
        with a11y.configure(reduced_motion=True):
            assert img.bitmap() is img._frames[0]
        img = fc.Image(str(path), alt='x', method='sixel',
                       background=(0, 0, 0), use_colors=True, width=4)
        use(monkeypatch, info(sixel=True))
        assert '\x1bP' in str(img)

    def test_natural_width(self, monkeypatch, picture):
        use(monkeypatch, info())
        assert fc.Image(picture).natural_width() == 6
        assert fc.Image(picture, width=9).natural_width() == 9
        assert fc.Image(b'x').natural_width() > 10
        assert fc.Image(picture, cell_size=(5, 10)).natural_width() == 12


class TestInsideLayouts:
    def test_card_grid_app(self, monkeypatch, picture):
        use(monkeypatch, info(sixel=True))
        img = fc.Image(picture, alt='Foto', width=10)
        card = Card('Foto', body=img)
        text = card.render(width=30)
        assert g.MARK in text
        assert all(visible_width(l) == 30 for l in text.split('\n'))
        assert '\x1bP0;1;0q' in str(card)
        grid = Grid([Card('a', body=fc.Image(picture, alt='a', width=8,
                                             method='half')),
                     Card('b', body=img)], columns=2)
        out = grid.render(width=50)
        assert all(visible_width(l) <= 50 for l in out.split('\n'))
        assert '\x1bP' in str(grid)
        app = App(body=fc.Stack([img, fc.Button('ok')]))
        stream = io.StringIO()
        app.stream = stream
        app.run(keys=['tab'], size=(40, 12))
        assert '\x1bP0;1;0q' in stream.getvalue()
        assert g.MARK not in stream.getvalue()

    def test_live_diff_and_cleanup(self, monkeypatch, picture):
        use(monkeypatch, info(kitty=True, kitty_placeholders=False))
        img = fc.Image(picture, alt='x', width=8)
        stream = io.StringIO()
        live = Live(stream=stream, force_terminal=True, width=30, height=10)
        live.start()
        live.update(Card('A', body=img))
        first = stream.getvalue()
        assert '\x1b_Ga=T' in first
        n = len(first)
        live.update(Card('B', body=img))          # title row only changed
        second = stream.getvalue()[n:]
        assert '\x1b_G' not in second
        n = len(stream.getvalue())
        live.update(Card('B', body='texto'))     # picture gone: deleted
        assert '\x1b_Ga=d,d=I' in stream.getvalue()[n:]
        live.update(Card('C', body=img))
        live.invalidate()
        live.update(Card('C', body=img))
        live.stop()
        assert stream.getvalue().count('\x1b_Ga=d') >= 2
        plain_live = Live(stream=io.StringIO(), force_terminal=False)
        plain_live.update(Card('x', body=img))
        assert '\x1b_Ga=T' in plain_live.stream.getvalue()


class TestViewerAndPreview:
    def test_viewer(self, monkeypatch, picture, tmp_path):
        use(monkeypatch, info())
        calls = []
        monkeypatch.setattr(g, 'open_external',
                            lambda url: calls.append(url) or (True, 'x'))
        v = fc.ImageViewer([(picture, 'Uno'), picture], use_colors=True)
        assert v.a11y_value() == '1 de 2: Uno'
        out = plain(v.render(40, 8))
        assert 'Uno' in out and '1/2' in out
        assert v.handle_key(Key('right')) and v.index == 1
        assert v.handle_key(Key('left')) and v.index == 0
        assert v.handle_key(Key('f')) and v.current.fit == 'cover'
        assert v.handle_key(Key('enter')) and calls
        assert not v.handle_key(Key('x'))
        v.focused = True
        assert '>' in plain(v.render(40, 8)) or '◀' in plain(v.render(40, 8))
        assert plain(fc.ImageViewer([]).render(20)).strip() == 'Sin imágenes'
        assert fc.ImageViewer([]).a11y_value() == 'sin imágenes'
        assert v.natural_width() == 60 and v.children() == []

    def test_file_preview(self, monkeypatch, picture):
        use(monkeypatch, info())
        p = fc.FilePreview(picture, max_lines=4, use_colors=True)
        assert p.needs_graphics
        lines = p.render(30).split('\n')
        assert 'foto.png' in plain(lines[0])
        assert len(lines) == 5                # header + 4 picture rows
        assert p.image() is p.image()
        q = fc.FilePreview(picture, images=False)
        assert not q.needs_graphics and q.image() is None
