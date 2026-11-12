"""
3.4.0 input: the full key parser (xterm / VT220 / rxvt / Linux console,
F1-F35, modifier combinations, kitty keyboard protocol, modifyOtherKeys,
mouse encodings, terminal responses), key names and the key map, terminal
capability detection and probing, keyboard protocol negotiation and the
Windows console input records.
"""

import io
import json
import os
import sys
import time

import pytest

tui = pytest.importorskip('flexablelib_tui')

from flexablelib_tui import (Key, KeyMap, KeyParser, MouseEvent,  # noqa: E402
                             Terminal, key_label, normalize_key, parse_keys)
from flexablelib_tui import capabilities as caps_module  # noqa: E402
from flexablelib_tui import terminal as terminal_module  # noqa: E402
from flexablelib_tui import wincon  # noqa: E402
from flexablelib_tui.keys import compose_key, split_key  # noqa: E402


def names(keys):
    return [str(k) for k in keys]


class TestSequences:
    @pytest.mark.parametrize('data,expected', [
        # Function keys F1-F24 in every encoding.
        ('\x1bOP', 'f1'), ('\x1b[11~', 'f1'), ('\x1b[[A', 'f1'),
        ('\x1b[[E', 'f5'), ('\x1b[12~', 'f2'), ('\x1b[13~', 'f3'),
        ('\x1b[14~', 'f4'), ('\x1b[17~', 'f6'), ('\x1b[18~', 'f7'),
        ('\x1b[19~', 'f8'), ('\x1b[20~', 'f9'), ('\x1b[21~', 'f10'),
        ('\x1b[23~', 'f11'), ('\x1b[24~', 'f12'), ('\x1b[25~', 'f13'),
        ('\x1b[26~', 'f14'), ('\x1b[28~', 'f15'), ('\x1b[29~', 'f16'),
        ('\x1b[31~', 'f17'), ('\x1b[32~', 'f18'), ('\x1b[33~', 'f19'),
        ('\x1b[34~', 'f20'), ('\x1b[42~', 'f21'), ('\x1b[45~', 'f24'),
        ('\x1b[57376u', 'f13'), ('\x1b[57387u', 'f24'),
        ('\x1b[57398u', 'f35'),
        # Modifier parameters: shift 1, alt 2, ctrl 4, meta 8 (+1).
        ('\x1b[1;2P', 'shift+f1'), ('\x1b[1;5P', 'ctrl+f1'),
        ('\x1b[15;3~', 'alt+f5'), ('\x1b[24;8~', 'ctrl+alt+shift+f12'),
        ('\x1b[1;9A', 'meta+up'), ('\x1b[1;16B', 'ctrl+alt+shift+meta+down'),
        ('\x1bO5P', 'ctrl+f1'), ('\x1bO2Q', 'shift+f2'),
        ('\x1b[1;7H', 'ctrl+alt+home'), ('\x1b[5;5~', 'ctrl+pageup'),
        ('\x1b[1;5Z', 'ctrl+shift+tab'), ('\x1b[E', 'begin'),
        # rxvt.
        ('\x1b[a', 'shift+up'), ('\x1b[d', 'shift+left'),
        ('\x1bOa', 'ctrl+up'), ('\x1bOc', 'ctrl+right'),
        ('\x1b[2$', 'shift+insert'), ('\x1b[3^', 'ctrl+delete'),
        ('\x1b[5@', 'ctrl+shift+pageup'), ('\x1b[11^', 'ctrl+f1'),
        # Keypad in application mode.
        ('\x1bOp', '0'), ('\x1bOy', '9'), ('\x1bOk', '+'), ('\x1bOX', '='),
        ('\x1bOl', ','),
        # Alt via ESC prefix, 8-bit CSI.
        ('\x1b\x1b[A', 'alt+up'), ('\x1b\x1bOP', 'alt+f1'),
        ('\x1b\x1b[1;5C', 'ctrl+alt+right'), ('\x9bB', 'down'),
        ('\x1bA', 'alt+A'), ('\x1b ', 'alt+space'),
    ])
    def test_named(self, data, expected):
        assert names(parse_keys(data)) == [expected]

    def test_raw_recorded(self):
        keys = parse_keys('a\x1b[1;5A\x1bx')
        assert [k.raw for k in keys] == ['a', '\x1b[1;5A', '\x1bx']

    def test_8bit_csi_mid_text(self):
        assert names(parse_keys('x\x9b1;2Cy')) == ['x', 'shift+right', 'y']

    def test_escape_escape_then_text(self):
        assert names(parse_keys('\x1b\x1bx')) == ['escape', 'alt+x']
        assert names(parse_keys('\x1b\x1b[200~hi\x1b[201~')) == [
            'escape', 'paste']

    def test_alt_prefix_on_mouse_is_not_alt(self):
        keys = parse_keys('\x1b\x1b[<0;1;1M')
        assert names(keys) == ['escape', 'mouse']

    def test_incomplete_alt_sequence_waits(self):
        p = KeyParser()
        assert p.feed('\x1b\x1b[') == []
        assert names(p.feed('B')) == ['alt+down']

    def test_unknown_sequences_are_dropped(self):
        assert parse_keys('\x1b[999~') == []
        assert parse_keys('\x1b[1;5q') == []
        assert parse_keys('\x1b[[Z') == []
        assert parse_keys('\x1b[1;=5~') == []
        assert parse_keys('\x1b[=5$') == []

    def test_aborted_sequence(self):
        # A control character inside a CSI ends it; the rest is parsed.
        assert names(parse_keys('\x1b[1\x01')) == ['ctrl+a']

    def test_linux_console_incomplete(self):
        p = KeyParser()
        assert p.feed('\x1b[[') == []
        assert names(p.feed('B')) == ['f2']


class TestKitty:
    @pytest.mark.parametrize('data,expected,char', [
        ('\x1b[97u', 'a', 'a'), ('\x1b[97;2u', 'A', 'A'),
        ('\x1b[97:65;2u', 'A', 'A'), ('\x1b[49:33;2u', '!', '!'),
        ('\x1b[49;2u', 'shift+1', ''), ('\x1b[97;5u', 'ctrl+a', ''),
        ('\x1b[97;6u', 'ctrl+A', ''), ('\x1b[97;3u', 'alt+a', ''),
        ('\x1b[97;9u', 'super+a', ''), ('\x1b[97;17u', 'hyper+a', ''),
        ('\x1b[97;33u', 'meta+a', ''), ('\x1b[97;69u', 'ctrl+a', ''),
        ('\x1b[13u', 'enter', '\n'), ('\x1b[13;2u', 'shift+enter', ''),
        ('\x1b[13;5u', 'ctrl+enter', ''), ('\x1b[9;2u', 'shift+tab', ''),
        ('\x1b[9;5u', 'ctrl+tab', ''), ('\x1b[27u', 'escape', ''),
        ('\x1b[127;3u', 'alt+backspace', ''), ('\x1b[32;5u', 'ctrl+space', ''),
        ('\x1b[32u', 'space', ' '), ('\x1b[57399u', '0', '0'),
        ('\x1b[57401;5u', 'ctrl+2', ''), ('\x1b[57413u', '+', '+'),
        ('\x1b[57414u', 'enter', '\n'), ('\x1b[57417u', 'left', ''),
        ('\x1b[57363u', 'menu', ''), ('\x1b[57441;2u', 'shift+leftshift', ''),
        ('\x1b[1;5:1A', 'ctrl+up', ''), ('\x1b[3;5~', 'ctrl+delete', ''),
        ('\x1b[241u', 'ñ', 'ñ'), ('\x1b[97;1;97u', 'a', 'a'),
        ('\x1b[97;2;65u', 'A', 'A'), ('\x1b[3u', 'ctrl+c', ''),
        ('\x1b[3;3u', 'ctrl+alt+c', ''),
    ])
    def test_keys(self, data, expected, char):
        keys = parse_keys(data)
        assert names(keys) == [expected]
        assert keys[0].char == char

    def test_events(self):
        p = KeyParser()
        keys = p.feed('\x1b[97;1:1u\x1b[97;1:2u\x1b[97;1:3u\x1b[1;1:3A')
        assert [(str(k), k.event) for k in keys] == [('a', 'press'),
                                                    ('a', 'repeat')]
        p = KeyParser(releases=True)
        keys = p.feed('\x1b[97;1:3u\x1b[1;1:3A\x1b[3;1:3~')
        assert [(str(k), k.event) for k in keys] == [
            ('a', 'release'), ('up', 'release'), ('delete', 'release')]

    def test_super_bit_depends_on_protocol(self):
        assert names(parse_keys('\x1b[1;9A')) == ['meta+up']
        assert names(parse_keys('\x1b[1;9A', kitty=True)) == ['super+up']

    def test_invalid_code_point(self):
        assert parse_keys('\x1b[99999999u') == []


class TestModifyOtherKeys:
    @pytest.mark.parametrize('data,expected', [
        ('\x1b[27;5;105~', 'ctrl+i'), ('\x1b[27;5;109~', 'ctrl+m'),
        ('\x1b[27;2;13~', 'shift+enter'), ('\x1b[27;5;13~', 'ctrl+enter'),
        ('\x1b[27;6;65~', 'ctrl+A'), ('\x1b[27;3;97~', 'alt+a'),
        ('\x1b[27;5;9~', 'ctrl+tab'), ('\x1b[27;2;9~', 'shift+tab'),
        ('\x1b[27;5;49~', 'ctrl+1'), ('\x1b[27;5;32~', 'ctrl+space'),
        ('\x1b[27;1;97~', 'a'),
    ])
    def test_keys(self, data, expected):
        assert names(parse_keys(data)) == [expected]


class TestMouse:
    def test_sgr_actions(self):
        keys = parse_keys('\x1b[<0;5;6M\x1b[<32;6;6M\x1b[<0;6;6m'
                          '\x1b[<35;7;7M\x1b[<2;1;1M\x1b[<1;1;1M')
        events = [k.mouse for k in keys]
        assert [e.action for e in events] == ['press', 'drag', 'release',
                                              'move', 'press', 'press']
        assert events[0] == (0, 4, 5, True)
        assert (events[0].button, events[0].x, events[0].y,
                events[0].pressed) == (0, 4, 5, True)
        assert events[3].button == 3 and not events[3].pressed
        assert events[4].button == 2 and events[5].button == 1

    def test_sgr_modifiers_and_wheel(self):
        keys = parse_keys('\x1b[<20;1;1M\x1b[<80;1;1M\x1b[<65;3;3M'
                          '\x1b[<66;1;1M\x1b[<67;1;1M\x1b[<72;1;1M')
        assert names(keys) == ['mouse', 'ctrl+scrollup', 'scrolldown',
                               'scrollleft', 'scrollright', 'alt+scrollup']
        assert keys[0].mouse.mods == ('ctrl', 'shift')
        assert keys[2].mouse == (65, 2, 2, True)
        assert keys[2].mouse.action == 'scroll'

    def test_extra_buttons(self):
        keys = parse_keys('\x1b[<128;1;1M\x1b[<129;1;1M')
        assert [k.mouse.button for k in keys] == [7, 8]

    def test_x10_and_utf8(self):
        keys = parse_keys('\x1b[M !!\x1b[M#!!\x1b[M`""\x1b[M@##')
        assert [(k.mouse.action, k.mouse.button, k.mouse.x) for k in keys
                if k.mouse] == [('press', 0, 0), ('release', 0, 0),
                                ('scroll', 64, 1), ('drag', 0, 2)]
        far = parse_keys('\x1b[M ' + chr(32 + 300) + chr(32 + 2))
        assert far[0].mouse[1:3] == (299, 1)

    def test_x10_split_and_invalid(self):
        p = KeyParser()
        assert p.feed('\x1b[M ') == []
        assert names(p.feed('!!')) == ['mouse']
        assert parse_keys('\x1b[M\x1f!!') == []

    def test_urxvt(self):
        keys = parse_keys('\x1b[32;10;5M\x1b[35;10;5M\x1b[96;1;1M'
                          '\x1b[64;2;2M')
        assert [(k.mouse.action, k.mouse.button) for k in keys] == [
            ('press', 0), ('release', 0), ('scroll', 64), ('drag', 0)]
        assert keys[0].mouse[1:3] == (9, 4)

    def test_release_reports_last_button(self):
        keys = parse_keys('\x1b[M"!!\x1b[M#!!')
        assert [k.mouse.button for k in keys] == [2, 2]

    def test_malformed(self):
        assert parse_keys('\x1b[<1;2M') == []
        assert parse_keys('\x1b[<1;2;3;4M') == []

    def test_mouse_event_helpers(self):
        ev = MouseEvent(0, 10, 5, True, mods=('ctrl',))
        assert ev.action == 'press' and ev.mods == ('ctrl',)
        moved = ev.moved(4, 2)
        assert moved == (0, 6, 3, True) and moved.mods == ('ctrl',)
        assert repr(ev) == "MouseEvent(0, 10, 5, True, 'press')"
        assert MouseEvent(0, 0, 0, False).action == 'release'


class TestResponses:
    @pytest.mark.parametrize('data,kind,body', [
        ('\x1b[?1u', 'kitty', '1'), ('\x1b[?62;22c', 'da1', '62;22'),
        ('\x1b[>41;380;0c', 'da2', '41;380;0'), ('\x1b[=0c', 'da3', '0'),
        ('\x1b[?2004;2$y', 'decrqm', '2004;2'),
        ('\x1b[2004;1$y', 'decrqm', '2004;1'),
        ('\x1b[>4;2m', 'modifykeys', '4;2'), ('\x1b[?6n', 'csi?n', '6'),
        ('\x1b[8;24;80t', 'window', '8;24;80'), ('\x1b[0n', 'dsr', '0'),
        ('\x1bP>|kitty(0.36)\x1b\\', 'dcs', '>|kitty(0.36)'),
        ('\x1b]11;rgb:0000/0000/0000\x07', 'osc', '11;rgb:0000/0000/0000'),
        ('\x1b_Gi=1;OK\x1b\\', 'apc', 'Gi=1;OK'),
    ])
    def test_kinds(self, data, kind, body):
        keys = parse_keys(data)
        assert names(keys) == ['response']
        assert keys[0].data == (kind, body)

    def test_cpr_only_when_expected(self):
        assert names(parse_keys('\x1b[1;5R')) == ['ctrl+f3']
        p = KeyParser()
        p.expect_cpr = 1
        keys = p.feed('\x1b[12;40R\x1b[1;5R')
        assert names(keys) == ['response', 'ctrl+f3']
        assert keys[0].data == ('cpr', '12;40')

    def test_string_split_and_flush(self):
        p = KeyParser()
        assert p.feed('\x1b]11;rgb') == []
        assert p.feed(':0/0/0\x1b') == []
        assert names(p.feed('\\')) == ['response']
        p = KeyParser()
        assert p.feed('\x1b]ab') == []
        assert names(p.flush()) == ['alt+]', 'a', 'b']

    def test_string_interrupted_is_alt(self):
        assert names(parse_keys('\x1b]x\x1b[A')) == ['alt+]', 'x', 'up']


class TestPasteAndSplits:
    def test_paste_terminator_split(self):
        p = KeyParser()
        assert p.feed('\x1b[200~hola\x1b[20') == []
        keys = p.feed('1~z')
        assert names(keys) == ['paste', 'z'] and keys[0].char == 'hola'

    def test_paste_keeps_escapes_and_newlines(self):
        keys = parse_keys('\x1b[200~a\x1b[Ab\r\nc\x1b[201~')
        assert keys[0].char == 'a\x1b[Ab\r\nc'

    def test_unterminated_paste_with_partial_end(self):
        p = KeyParser()
        p.feed('\x1b[200~xy\x1b[2')
        keys = p.flush()
        assert keys[0].char == 'xy\x1b[2'

    def test_every_split_point(self):
        data = ('a\x1b[1;5A\x1b[<0;3;4M\x1b[97;6u\x1b[27;5;105~'
                '\x1b[200~p\x1b[201~\x1bOP\x1b[15;2~é')
        whole = names(parse_keys(data))
        for cut in range(1, len(data)):
            p = KeyParser()
            got = p.feed(data[:cut]) + p.feed(data[cut:]) + p.flush()
            assert names(got) == whole, cut

    def test_byte_by_byte(self):
        data = 'ñ\x1b[1;3D€\x1b[<64;1;1M'.encode('utf-8')
        p = KeyParser()
        got = []
        for b in data:
            got.extend(p.feed(bytes([b])))
        assert names(got + p.flush()) == ['ñ', 'alt+left', '€', 'scrollup']


class TestKeyNames:
    def test_split_compose(self):
        assert split_key('ctrl+alt+up') == ('up', ('ctrl', 'alt'))
        assert split_key('ctrl++') == ('+', ('ctrl',))
        assert split_key('+') == ('+', ())
        assert split_key('shift+') == ('shift+', ())
        assert compose_key('a', ['shift', 'alt']) == 'alt+A'
        assert compose_key('1', ['shift']) == 'shift+1'
        assert compose_key('up', ['shift', 'ctrl', 'meta', 'super',
                                  'hyper', 'alt']) == \
            'ctrl+alt+shift+meta+super+hyper+up'

    def test_key_properties(self):
        k = Key('ctrl+shift+up')
        assert k.base == 'up' and k.mods == ('ctrl', 'shift')
        r = Key('a', 'a', raw='a').renamed('b')
        assert r == 'b' and r.char == 'a' and r.raw == 'a'
        assert Key('x').event == 'press'

    @pytest.mark.parametrize('text,expected', [
        ('Ctrl+Shift+A', 'ctrl+A'), ('control+a', 'ctrl+a'),
        ('Opt+shift+X', 'alt+X'), ('cmd+Esc', 'super+escape'),
        ('Win+e', 'super+e'), ('Ctrl+J', 'ctrl+j'), ('Alt+X', 'alt+x'),
        ('alt+shift+x', 'alt+X'), ('PgUp', 'pageup'), ('Shift+Tab', 'shift+tab'),
        ('ctrl++', 'ctrl++'), ('+', '+'), (' ', 'space'), ('F5', 'f5'),
        ('Return', 'enter'), ('ctrl+Del', 'ctrl+delete'), ('A', 'A'),
        ('alt+Space', 'alt+space'), ('Meta+Up', 'meta+up'),
    ])
    def test_normalize(self, text, expected):
        assert normalize_key(text) == expected

    def test_normalize_rejects_unknown_modifier(self):
        with pytest.raises(ValueError):
            normalize_key('foo+a')

    @pytest.mark.parametrize('name,ascii,label', [
        ('ctrl+s', False, 'Ctrl+S'), ('ctrl+A', False, 'Ctrl+Shift+A'),
        ('shift+tab', False, 'Shift+Tab'), ('f5', False, 'F5'),
        ('up', False, '↑'), ('up', True, 'Arriba'), ('alt+left', True,
                                                     'Alt+Izq'),
        ('q', False, 'Q'), ('?', False, '?'), ('ctrl+1', False, 'Ctrl+1'),
        ('pageup', False, 'PgUp'), ('escape', False, 'Esc'),
    ])
    def test_labels(self, name, ascii, label):
        assert key_label(name, ascii) == label


class TestKeyMap:
    def test_defaults_and_actions(self):
        km = KeyMap()
        assert km.action_for('tab') == 'focus_next'
        assert km.action_for('shift+tab') == 'focus_prev'
        assert km.matches(Key('ctrl+c'), 'quit')
        assert km.action_for('x') is None
        assert KeyMap(defaults=False).action_for('tab') is None

    def test_remap_and_bind(self):
        km = KeyMap(remap={'Ctrl+J': 'Down', 'ctrl+t': 'x'},
                    actions={'save': ['ctrl+s', 'F2'], 'quit': 'ctrl+x'})
        k = km.translate(Key('ctrl+j', raw='\n'))
        assert k == 'down' and k.raw == '\n'
        assert km.translate(Key('ctrl+t')).char == 'x'
        assert km.translate('ctrl+t') == 'x'
        assert km.translate(Key('q')) == 'q'
        assert km.keys_for('quit') == ['ctrl+x']
        assert km.describe('save') == 'Ctrl+S / F2'
        km.bind('save', 'ctrl+s', 'f3')
        assert km.keys_for('save') == ['ctrl+s', 'f2', 'f3']
        km.unbind('save', 'F2')
        assert km.keys_for('save') == ['ctrl+s', 'f3']
        km.unbind('save')
        assert km.keys_for('save') == []

    def test_conflicts_and_persistence(self, tmp_path):
        km = KeyMap(actions={'go': ['enter']})
        assert km.conflicts() == {'enter': ['activate', 'go']}
        path = str(tmp_path / 'keys.json')
        km.save(path)
        data = json.load(open(path, encoding='utf-8'))
        assert data['actions']['go'] == ['enter']
        again = KeyMap.load(path)
        assert again.to_dict() == km.to_dict()
        assert KeyMap.from_dict({'actions': {'a': ['x']}},
                                defaults=False).to_dict() == {
            'remap': {}, 'actions': {'a': ['x']}}


class TestCapabilities:
    @pytest.mark.parametrize('env,tty,level', [
        ({'NO_COLOR': '1', 'TERM': 'xterm-256color'}, True, 'none'),
        ({'NO_COLOR': '', 'TERM': 'xterm-256color'}, True, 'none'),
        ({'FORCE_COLOR': '0'}, True, 'none'),
        ({'FORCE_COLOR': 'false'}, True, 'none'),
        ({'FORCE_COLOR': '1'}, False, '16'),
        ({'FORCE_COLOR': ''}, False, '16'),
        ({'FORCE_COLOR': '2'}, False, '256'),
        ({'FORCE_COLOR': '3'}, False, 'truecolor'),
        ({'FORCE_COLOR': 'x'}, False, '16'),
        ({'FORCE_COLOR': '1', 'COLORTERM': 'truecolor'}, False,
         'truecolor'),
        ({'FORCE_COLOR': '1', 'TERM': 'dumb'}, False, '16'),
        ({'TERM': 'dumb'}, True, 'none'),
        ({'TERM': 'xterm'}, False, 'none'),
        ({'TERM': 'xterm'}, True, '16'),
        ({'TERM': 'xterm-256color'}, True, '256'),
        ({'TERM': 'xterm', 'COLORTERM': '24bit'}, True, 'truecolor'),
        ({'TERM_PROGRAM': 'WezTerm'}, True, 'truecolor'),
        ({'WT_SESSION': 'x'}, True, 'truecolor'),
        ({'TERM': 'xterm-kitty'}, True, 'truecolor'),
        ({'TERM_PROGRAM': 'Apple_Terminal'}, True, '256'),
    ])
    def test_color_level(self, env, tty, level):
        assert caps_module.color_level(env, tty) == level

    def test_color_level_defaults_to_process(self, monkeypatch):
        monkeypatch.setattr(sys, 'stdout', io.StringIO())
        assert caps_module.color_level({'TERM': 'xterm'}) == 'none'

    @pytest.mark.parametrize('env,encoding,ok', [
        ({'LANG': 'es_MX.UTF-8'}, None, True),
        ({'LC_ALL': 'en_US.utf8', 'LANG': 'C'}, None, True),
        ({'LANG': 'es_MX.ISO-8859-1'}, 'utf-8', False),
        ({'LANG': 'C'}, 'utf-8', True), ({'LANG': 'C'}, 'ascii', False),
        ({}, None, False), ({'WT_SESSION': '1'}, None, True),
        ({'TERM': 'dumb', 'LANG': 'x.UTF-8'}, None, False),
        ({'FLEXABLELIB_ASCII': '1', 'LANG': 'x.UTF-8'}, None, False),
        ({'FLEXABLELIB_ASCII': '0'}, None, True),
    ])
    def test_unicode(self, env, encoding, ok):
        assert caps_module.unicode_ok(env, encoding) is ok

    def test_detect(self):
        caps = caps_module.detect({'TERM': 'xterm-kitty', 'LANG': 'C.UTF-8',
                                   'CI': '1'}, tty=True, size=(100, 30),
                                  platform='posix')
        assert caps.color == 'truecolor' and caps.unicode
        assert caps.kitty_keyboard and caps.keyboard == 'kitty'
        assert caps.size == (100, 30) and caps.ci and not caps.windows
        lin = caps_module.detect({'TERM': 'linux'}, tty=True, size=(80, 25))
        assert lin.mouse_sgr is False and lin.focus_events is False
        assert lin.keyboard == 'legacy'
        dumb = caps_module.detect({'TERM': 'dumb'}, tty=True,
                                  platform='nt')
        assert dumb.dumb and dumb.windows and dumb.color == 'none'
        assert dumb.bracketed_paste is False
        assert 'Colores: none' in dumb.summary()
        assert 'dumb' in repr(dumb)
        mod = caps_module.Capabilities(modify_other_keys=True)
        assert mod.keyboard == 'modify'
        assert 'Tamaño: 80×25' in lin.summary()

    def test_detect_defaults(self):
        caps = caps_module.detect()
        assert caps.color in ('none', '16', '256', 'truecolor')
        assert len(caps.size) == 2

    def test_apply_responses(self):
        caps = caps_module.Capabilities()
        done = caps_module.apply_responses(caps, parse_keys(
            '\x1b[?3u\x1b[?2026;2$y\x1b[?1006;1$y\x1b[?9999;1$y'
            '\x1b[?2004;0$y\x1b[?x$y\x1bP>|WezTerm 2024\x1b\\'
            '\x1b]10;x\x07') + [Key('a')])
        assert not done
        assert caps.kitty_keyboard and caps.kitty_flags == 3
        assert caps.sync_output is True and caps.mouse_sgr is True
        assert caps.bracketed_paste is False
        assert caps.version == 'WezTerm 2024'
        assert caps_module.apply_responses(caps, parse_keys('\x1b[?62c'))
        assert caps.device_attributes == '62'
        caps2 = caps_module.Capabilities()
        caps_module.apply_responses(caps2, parse_keys('\x1b[?u'))
        assert caps2.kitty_flags == 0


def _pty_terminal(answer=None, **kw):
    """A Terminal on a pty whose far end answers queries with ``answer``."""
    import pty
    master, slave = pty.openpty()
    stdin = os.fdopen(slave, 'r')

    class Out(io.StringIO):
        def write(self, text):
            if answer is not None and '\x1b[c' in text:
                os.write(master, answer.encode())
            return io.StringIO.write(self, text)
    term = Terminal(stdin=stdin, stdout=Out(), **kw)
    return term, master, stdin


@pytest.mark.skipif(os.name == 'nt', reason='pty is POSIX only')
class TestProtocolNegotiation:
    def test_kitty_answered(self, monkeypatch):
        monkeypatch.setenv('TERM', 'xterm-kitty')
        term, master, stdin = _pty_terminal(
            'z\x1b[?1u\x1b[?2004;2$y\x1b[?62;22c')
        with term:
            assert term.protocol == 'kitty' and term.parser.kitty
            assert term.capabilities.kitty_keyboard
            assert term.capabilities.probed
            assert term.capabilities.bracketed_paste is True
            assert term.capabilities.sync_output is False
            assert names(term.read_keys(timeout=0.05)) == ['z']
            os.write(master, b'\x1b[97;5u')
            assert names(term.read_keys(timeout=0.3)) == ['ctrl+a']
        out = term.stdout.getvalue()
        assert '\x1b[>1u' in out and out.endswith('\x1b[?2004l')
        assert '\x1b[<u' in out
        stdin.close()
        os.close(master)

    def test_modify_other_keys(self, monkeypatch):
        monkeypatch.setenv('TERM', 'xterm-256color')
        term, master, stdin = _pty_terminal('\x1b[?64;1c')
        with term:
            assert term.protocol == 'modify'
            os.write(master, b'\x1b[27;5;105~')
            assert names(term.read_keys(timeout=0.3)) == ['ctrl+i']
        out = term.stdout.getvalue()
        assert '\x1b[>4;2m' in out and '\x1b[>4;0m' in out
        stdin.close()
        os.close(master)

    def test_no_answer_is_legacy(self, monkeypatch):
        monkeypatch.setenv('TERM', 'xterm')
        term, master, stdin = _pty_terminal(None)
        start = time.monotonic()
        with term:
            assert term.protocol == 'legacy'
            assert not term.capabilities.probed
        assert time.monotonic() - start < 1.0
        stdin.close()
        os.close(master)

    def test_forced_protocols(self):
        for choice, code in (('kitty', '\x1b[>3u'), ('modify', '\x1b[>4;2m')):
            term, master, stdin = _pty_terminal(None, keyboard=choice,
                                                releases=True)
            with term:
                assert term.protocol == choice
            assert code in term.stdout.getvalue()
            stdin.close()
            os.close(master)
        term, master, stdin = _pty_terminal(None, keyboard='legacy')
        with term:
            assert term.protocol == 'legacy'
        assert term.stdout.getvalue() == '\x1b[?2004h\x1b[?2004l'
        stdin.close()
        os.close(master)

    def test_modes_written(self):
        term, master, stdin = _pty_terminal(None, keyboard='legacy',
                                            mouse='hover', focus=True,
                                            paste=False)
        with term:
            pass
        out = term.stdout.getvalue()
        for code in ('\x1b[?1000h', '\x1b[?1002h', '\x1b[?1003h',
                     '\x1b[?1006h', '\x1b[?1015h', '\x1b[?1004h',
                     '\x1b[?1003l', '\x1b[?1004l', '\x1b[?1000l'):
            assert code in out
        assert '2004' not in out
        stdin.close()
        os.close(master)

    def test_invalid_keyboard(self):
        with pytest.raises(ValueError):
            Terminal(keyboard='nope')

    def test_responses_filtered_and_replay(self):
        term, master, stdin = _pty_terminal(None, keyboard='legacy')
        with term:
            os.write(master, b'\x1b[?62c')
            assert term.read_keys(timeout=0.2) == []
            os.write(master, b'\x1b[?62cq')
            assert names(term.read_keys(timeout=0.2,
                                        responses=True)) == ['response', 'q']
            term.replay([Key('x')])
            assert names(term.read_keys(timeout=0.01)) == ['x']
            assert term.is_tty()
        stdin.close()
        os.close(master)

    def test_probe_skips_non_tty(self):
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        caps = caps_module.probe(term)
        assert caps.probed is False
        assert term.stdout.getvalue() == ''


class TestWindowsTranslation:
    CTRL = wincon.LEFT_CTRL
    ALT = wincon.LEFT_ALT
    SHIFT = wincon.SHIFT

    @pytest.mark.parametrize('vk,char,state,expected', [
        (0x41, 'a', 0, 'a'), (0x41, 'A', 0x10, 'A'), (0x41, '\x01', 0x8,
                                                     'ctrl+a'),
        (0x41, '\x01', 0x18, 'ctrl+A'), (0x41, 'a', 0x2, 'alt+a'),
        (0x41, '\x01', 0xA, 'ctrl+alt+a'), (0x31, '1', 0x8, 'ctrl+1'),
        (0x26, '', 0, 'up'), (0x26, '', 0x18, 'ctrl+shift+up'),
        (0x70, '', 0, 'f1'), (0x7B, '', 0x10, 'shift+f12'),
        (0x7C, '', 0, 'f13'), (0x87, '', 0, 'f24'), (0x09, '\t', 0, 'tab'),
        (0x09, '\t', 0x10, 'shift+tab'), (0x0D, '\r', 0, 'enter'),
        (0x0D, '\r', 0x8, 'ctrl+enter'), (0x1B, '\x1b', 0, 'escape'),
        (0x08, '\x08', 0, 'backspace'), (0x2E, '', 0x2, 'alt+delete'),
        (0x20, ' ', 0, 'space'), (0x20, ' ', 0x8, 'ctrl+space'),
        (0x20, ' ', 0x2, 'alt+space'), (0xDB, '\x1b', 0x8, 'ctrl+_'),
        (0xBF, '?', 0x10, '?'), (0x45, '€', 0x9, '€'),
        (0x45, '', 0x2, 'alt+e'), (0x00, 'ñ', 0, 'ñ'),
        (0xDD, '\x1d', 0x8, 'ctrl+]'), (0x60, '0', 0x20, '0'),
        (0x00, '\x1c', 0xA, 'ctrl+alt+\\'), (0xBA, ';', 0x2, 'alt+;'),
    ])
    def test_keys(self, vk, char, state, expected):
        key = wincon.translate_key(vk, char, state)
        assert str(key) == expected

    def test_ignored(self):
        assert wincon.translate_key(0x10, '', 0x10) is None
        assert wincon.translate_key(0xA2, '', 0x8) is None
        assert wincon.translate_key(0xFF, '', 0) is None
        assert wincon.translate_key(0x07, '\x00', 0) is None

    def test_translator_records(self):
        t = wincon.ConsoleInputTranslator(origin=(0, 10))
        keys = t.feed([
            ('key', True, 1, 0x48, 'h', 0), ('key', False, 1, 0x48, 'h', 0),
            ('key', True, 3, 0x28, '', 0),
            ('key', True, 1, 0x10, '', 0x10),
            ('key', True, 1, 0, '\ud83d', 0), ('key', True, 1, 0, '\ude00', 0),
            ('mouse', 5, 12, 1, 0, 0), ('mouse', 6, 12, 1, 0,
                                        wincon.MOUSE_MOVED),
            ('mouse', 6, 12, 0, 0, 0), ('mouse', 7, 13, 0, 0,
                                        wincon.MOUSE_MOVED),
            ('mouse', 1, 11, 120 << 16, 0x8, wincon.MOUSE_WHEELED),
            ('mouse', 1, 11, (0x10000 - 120) << 16, 0, wincon.MOUSE_WHEELED),
            ('mouse', 1, 11, 120 << 16, 0, wincon.MOUSE_HWHEELED),
            ('mouse', 1, 11, (0x10000 - 120) << 16, 0,
             wincon.MOUSE_HWHEELED),
            ('mouse', 2, 10, 2, 0x10, 0), ('mouse', 2, 10, 6, 0, 0),
            ('mouse', 2, 10, 0, 0, 0), ('mouse', 2, 10, 1, 0,
                                        wincon.DOUBLE_CLICK),
            ('size', 120, 40), ('focus', True), ('focus', False),
            ('menu', 7),
        ])
        assert names(keys) == (['h', 'down', 'down', 'down', '\U0001f600']
                               + ['mouse'] * 4 +
                               ['ctrl+scrollup', 'scrolldown', 'scrollright',
                                'scrollleft'] + ['mouse'] * 5 +
                               ['resize', 'focusin', 'focusout'])
        mice = [k.mouse for k in keys if k.mouse]
        assert mice[0] == (0, 5, 2, True) and mice[0].action == 'press'
        assert mice[1].action == 'drag' and mice[2].action == 'release'
        assert mice[3].action == 'move'
        assert mice[4].mods == ('ctrl',)
        assert [(m.button, m.action) for m in mice[8:]] == [
            (2, 'press'), (1, 'press'), (2, 'release'), (1, 'release'),
            (0, 'press')]
        assert mice[8].mods == ('shift',)
        assert t.size == (120, 40) and t.focused is False

    def test_translator_vt(self):
        t = wincon.ConsoleInputTranslator(vt=True)
        seq = '\x1b[1;5A\x1b[<0;3;4M\r'
        keys = t.feed([('key', True, 1, 0, c, 0) for c in seq])
        assert names(keys) == ['ctrl+up', 'mouse', 'enter']
        keys = t.feed([('key', True, 1, 0x1B, '\x1b', 0)])
        assert keys == [] and t.pending
        assert names(t.flush()) == ['escape']
        t = wincon.ConsoleInputTranslator(vt=True)
        assert names(t.feed([('key', True, 1, 0x26, '', 0)])) == ['up']

    def test_translator_injected_escape_sequence(self):
        t = wincon.ConsoleInputTranslator()
        keys = t.feed([('key', True, 1, 0, c, 0) for c in '\x1b[B'])
        assert names(keys) == ['down']

    def test_records_from_text_and_structs(self):
        recs = wincon.records_from_text('Hi!')
        assert recs[0] == ('key', True, 1, ord('H'), 'H', 0)
        assert recs[4][3] == 0
        t = wincon.ConsoleInputTranslator()
        assert names(t.feed(recs)) == ['H', 'i', '!']
        items = [('key', True, 2, 0x41, 'a', 0x10),
                 ('key', False, 1, 0x26, '', 0),
                 ('mouse', 3, 4, 120 << 16, 0x8, 4), ('size', 80, 25),
                 ('focus', True), ('focus', False), ('menu', 9)]
        for item in items:
            assert wincon.record_to_tuple(wincon.tuple_to_record(item)) == \
                item

    def test_available(self):
        assert wincon.available() == (os.name == 'nt')


class FakeConsole(object):
    """Stands in for wincon.ConsoleInput: hands out queued records."""

    def __init__(self, stdin=None, vt=True, ok=True):
        self.records = []
        self.vt_supported = vt
        self.ok = ok
        self.started = None
        self.stopped = False
        self.vt = False

    def start(self, mouse=False, vt=True):
        self.started = (mouse, vt)
        self.vt = vt and self.vt_supported
        return self.ok

    def stop(self):
        self.stopped = True

    def read(self, timeout):
        out, self.records = self.records, []
        return out

    def window_origin(self):
        return (0, 0)


class TestTerminalConsolePath:
    def _setup(self, monkeypatch, **fake):
        consoles = []

        def make(stdin=None):
            c = FakeConsole(stdin, **fake)
            consoles.append(c)
            return c
        monkeypatch.setattr(terminal_module, 'WINDOWS', True)
        monkeypatch.setattr(wincon, 'available', lambda: True)
        monkeypatch.setattr(wincon, 'ConsoleInput', make)
        return consoles

    def test_records_mode(self, monkeypatch):
        consoles = self._setup(monkeypatch, vt=False)
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO(),
                        mouse=True, windows='records')
        with term:
            console = consoles[0]
            assert console.started == (True, False)
            assert term.protocol == 'windows-console' and term.is_tty()
            console.records = [('key', True, 1, 0x26, '', 0x8),
                               ('size', 90, 30),
                               ('mouse', 1, 1, 1, 0, 0)]
            assert names(term.read_keys(timeout=0.01)) == ['ctrl+up',
                                                           'mouse']
            assert term.resized() is True
        assert console.stopped and term.console is None

    def test_vt_mode(self, monkeypatch):
        consoles = self._setup(monkeypatch, vt=True)
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        with term:
            assert term.protocol == 'windows-vt'
            consoles[0].records = [('key', True, 1, 0, c, 0)
                                   for c in '\x1b[1;2B\x1b']
            assert names(term.read_keys(timeout=0.01)) == ['shift+down',
                                                           'escape']

    def test_not_a_console_falls_back_to_msvcrt(self, monkeypatch):
        from tests.test_v330_tui import FakeMsvcrt
        self._setup(monkeypatch, ok=False)
        monkeypatch.setitem(sys.modules, 'msvcrt', FakeMsvcrt('x'))
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO())
        with term:
            assert term.console is None
            assert names(term.read_keys(timeout=0.01)) == ['x']

    def test_forced_msvcrt(self, monkeypatch):
        consoles = self._setup(monkeypatch)
        term = Terminal(stdin=io.StringIO(), stdout=io.StringIO(),
                        windows='msvcrt')
        monkeypatch.setitem(sys.modules, 'msvcrt',
                            __import__('tests.test_v330_tui', fromlist=['x'])
                            .FakeMsvcrt(''))
        with term:
            assert consoles == [] and term.console is None


@pytest.mark.skipif(os.name != 'nt', reason='real Windows console API')
class TestRealWindowsConsole:
    """Injects input records into a real console and reads them back."""

    def test_records_round_trip(self, tmp_path):
        import subprocess
        out = tmp_path / 'keys.json'
        child = os.path.join(os.path.dirname(__file__), 'wincon_child.py')
        env = dict(os.environ)
        env['PYTHONPATH'] = os.pathsep.join(sys.path)
        proc = subprocess.run(
            [sys.executable, child, str(out)], env=env, timeout=60,
            creationflags=subprocess.CREATE_NEW_CONSOLE)
        assert proc.returncode == 0, out.read_text() if out.exists() else ''
        result = json.loads(out.read_text(encoding='utf-8'))
        assert result['records'] == result['expected_records'], result
        assert result['vt_keys'] == result['expected_vt'], result
        detail = json.dumps({k: result.get(k) for k in (
            'terminal_protocol', 'terminal', 'terminal_mouse',
            'terminal_raw', 'records_terminal')})
        assert result['terminal'] == result['expected_terminal'], detail
        assert result['records_protocol'] == 'windows-console', result
        assert result['records_terminal'] == \
            result['expected_records_terminal'], result
