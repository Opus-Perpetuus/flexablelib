"""3.5.4: the key parser survives out-of-range code points in kitty
reports, an Escape followed by a bracketed paste keeps the paste intact,
input split anywhere parses like the whole; a click in a MoneyInput puts
the cursor under the click; CoordinatesInput renders at widths 1 and 2;
an empty Table with show_index renders; Key and MouseEvent survive copy
and pickle."""

import copy
import pickle
import random

import pytest

from flexablelib import Table
from flexablelib.text_width import strip_ansi, visible_width

T = pytest.importorskip('flexablelib_tui')

from flexablelib_tui.keys import (Key, KeyParser, MouseEvent,  # noqa: E402
                                  parse_keys)


def names(keys):
    return [(str(k), k.char) for k in keys]


def chunked(data, step):
    parser = KeyParser()
    out = []
    for i in range(0, len(data), step):
        out += parser.feed(data[i:i + step])
    return out + parser.flush()


def sig(keys):
    return [(str(k), k.char, k.event, k.mouse, k.data) for k in keys]


class TestKittyOutOfRange:
    def test_text_code_point_too_large_is_ignored(self):
        assert names(parse_keys('\x1b[97;1;99999999u')) == [('a', 'a')]

    def test_shifted_code_point_too_large_is_ignored(self):
        keys = parse_keys('\x1b[97:9999999999;2u')
        assert len(keys) == 1 and str(keys[0]).lower() == 'a'

    def test_valid_text_still_used(self):
        assert names(parse_keys('\x1b[97;1;241u')) == [('a', 'ñ')]

    def test_following_keys_still_parsed(self):
        keys = parse_keys('\x1b[97;1;99999999ub')
        assert [str(k) for k in keys] == ['a', 'b']

    def test_parser_state_survives(self):
        parser = KeyParser(kitty=True)
        parser.feed('\x1b[97:1114112;2;1114112u')
        assert names(parser.feed('x')) == [('x', 'x')]


class TestEscapeThenPaste:
    def test_paste_text_kept(self):
        keys = parse_keys('\x1b\x1b[200~hola\x1b[201~')
        assert names(keys) == [('escape', ''), ('paste', 'hola')]

    def test_split_feed(self):
        data = '\x1b\x1b[200~hola\x1b[201~'
        for step in range(1, len(data) + 1):
            assert names(chunked(data, step)) == \
                [('escape', ''), ('paste', 'hola')], step

    def test_paste_then_keys(self):
        keys = parse_keys('\x1b\x1b[200~a b\x1b[201~x')
        assert names(keys) == [('escape', ''), ('paste', 'a b'), ('x', 'x')]

    def test_alt_arrow_unchanged(self):
        assert [str(k) for k in parse_keys('\x1b\x1b[A')] == ['alt+up']


class TestSplitInputMatchesWhole:
    def test_escape_escape_waits_for_more(self):
        parser = KeyParser()
        assert parser.feed('\x1b\x1b') == []
        assert parser.pending
        assert [str(k) for k in parser.feed('[A')] == ['alt+up']

    def test_escape_escape_then_flush(self):
        parser = KeyParser()
        parser.feed('\x1b\x1b')
        assert [str(k) for k in parser.flush()] == ['escape', 'escape']

    def test_alt_home_split(self):
        assert [str(k) for k in chunked('\x1b\x1b[~', 1)] == \
            [str(k) for k in parse_keys('\x1b\x1b[~')]

    def test_random_split_points(self):
        pieces = ['\x1b', '[', 'O', '1', ';', '5', 'A', '~', 'u', '<', 'M',
                  'm', '\x1b[200~', '\x1b[201~', 'a', 'ñ', '漢', '\t', ':',
                  '9', '$', '^', '?', '\x07', 'P', '\\']
        rnd = random.Random(354)
        for _ in range(3000):
            data = ''.join(rnd.choice(pieces) for _ in range(rnd.randint(1, 14)))
            whole = sig(parse_keys(data))
            step = rnd.randint(1, 4)
            assert sig(chunked(data, step)) == whole, (data, step)


class TestKeyCopyPickle:
    EVENT = MouseEvent(0, 3, 4, True, 'drag', ('ctrl',))

    @pytest.mark.parametrize('clone', [
        copy.copy, copy.deepcopy, lambda o: pickle.loads(pickle.dumps(o))])
    def test_mouse_event(self, clone):
        got = clone(self.EVENT)
        assert got == self.EVENT
        assert (got.action, got.mods) == ('drag', ('ctrl',))

    @pytest.mark.parametrize('clone', [
        copy.copy, copy.deepcopy, lambda o: pickle.loads(pickle.dumps(o))])
    def test_key(self, clone):
        key = Key('ctrl+a', 'x', mouse=self.EVENT, event='repeat',
                  data=('dsr', '0'), raw='\x01')
        got = clone(key)
        assert isinstance(got, Key) and got == 'ctrl+a'
        assert (got.char, got.mouse, got.event, got.data, got.raw) == \
            ('x', self.EVENT, 'repeat', ('dsr', '0'), '\x01')
        assert got.mouse.action == 'drag'


class TestEmptyTableWithIndex:
    def test_renders_like_without_index(self):
        plain = Table()
        indexed = Table()
        indexed.show_index = True
        assert str(indexed) == str(plain)

    def test_paginate(self):
        table = Table()
        table.show_index = True
        assert list(table.paginate()) == [str(Table())]

    def test_headers_only_keep_index(self):
        table = Table(headers=['a', 'b'])
        table.show_index = True
        assert ' i ' in strip_ansi(str(table))


C = pytest.importorskip('flexablelib_components')

from flexablelib_tui import App  # noqa: E402


def click(app, x, y):
    app.dispatch(Key('mouse', mouse=MouseEvent(0, x, y, True, 'press')))
    app.dispatch(Key('mouse', mouse=MouseEvent(0, x, y, False, 'release')))


class TestMoneyInputClick:
    def setup_method(self):
        self.money = C.MoneyInput(label='Monto', value=1234)
        self.app = App(body=C.Stack([self.money]), mouse=True)
        self.app.run(keys=[], size=(30, 4))
        # '› $1234.00': the marker and a space, then the symbol at x=2.
        assert self.app.origin(self.money) == (0, 0)

    def test_click_on_digit_puts_cursor_before_it(self):
        click(self.app, 3, 1)                 # the '1'
        assert self.money.cursor_pos == 0
        click(self.app, 5, 1)                 # the '3'
        assert self.money.cursor_pos == 2

    def test_click_on_symbol_goes_to_start(self):
        click(self.app, 2, 1)
        assert self.money.cursor_pos == 0

    def test_typing_after_click_inserts_there(self):
        click(self.app, 4, 1)                 # the '2'
        self.app.dispatch(Key('9', '9'))
        assert self.money.text.startswith('192')

    def test_click_past_end_of_empty_input(self):
        money = C.MoneyInput(label='m')
        app = App(body=C.Stack([money]), mouse=True)
        app.run(keys=[], size=(30, 4))
        click(app, 6, 1)
        assert money.cursor_pos == 0
        for name in ('ctrl+left', 'ctrl+right', 'ctrl+w', 'backspace'):
            app.dispatch(Key(name))           # used to raise IndexError
            app.render(30, 4)
        assert money.text == ''


class TestCursorOutOfRange:
    @pytest.mark.parametrize('name', ['ctrl+left', 'ctrl+right', 'ctrl+w',
                                      'alt+b', 'alt+f', 'backspace', 'left',
                                      'delete', 'ctrl+k'])
    def test_cursor_set_past_the_text(self, name):
        field = C.TextInput(value='uno dos')
        field.cursor_pos = 50
        field.handle_key(Key(name))
        assert 0 <= field.cursor_pos <= len(field.text)

    def test_negative_cursor(self):
        field = C.TextInput(value='uno')
        field.cursor_pos = -4
        field.handle_key(Key('x', 'x'))
        assert field.text == 'xuno'


class TestCoordinatesNarrow:
    @pytest.mark.parametrize('width', [1, 2, 3, 4, 10])
    def test_renders_within_width(self, width):
        field = C.CoordinatesInput(label='Ubicación', value=(20.5, -103.2))
        lines = field.render(width).split('\n')
        assert all(visible_width(strip_ansi(l)) <= width for l in lines)

    def test_narrow_stacks_both_fields(self):
        field = C.CoordinatesInput(label='c')
        assert len(field.render(2).split('\n')) > \
            len(field.render(20).split('\n'))
