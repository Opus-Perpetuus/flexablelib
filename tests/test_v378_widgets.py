"""Regression tests for the 3.7.8 widget fixes."""
import pytest

import flexablelib_components as C
from flexablelib.layout import strip_ansi


def _cursor_drawn(widget, width):
    calls = []
    original = widget.cursor

    def spy(char):
        calls.append(char)
        return original(char)
    widget.cursor = spy
    widget.render(width)
    return calls


@pytest.mark.parametrize('text', ['aaaaaaa中b', 'aaaaaaa👍b', 'a中中中中b'])
def test_wide_char_under_cursor_stays_in_view(text):
    field = C.TextInput(value=text)
    field.focused = True
    for pos in range(len(text)):
        field.cursor_pos = pos
        field.scroll_x = 0
        calls = _cursor_drawn(field, 9)
        expected = text[pos]
        assert calls == [expected], (pos, calls)


def test_wide_char_under_cursor_is_shown_whole():
    field = C.TextInput(value='aaaaaaa中b')
    field.focused = True
    field.cursor_pos = 7
    line = strip_ansi(field.render(9))
    assert line.endswith('中')
    assert len(line) == 8  # '› ' + 5 narrow + one wide


@pytest.mark.parametrize('key', ['left', 'right'])
def test_empty_tabs_ignore_arrows(key):
    from flexablelib_tui.keys import Key
    tabs = C.Tabs([])
    assert tabs.handle_key(Key(key)) is False
    assert tabs.index == 0
    tabs.render(20)
