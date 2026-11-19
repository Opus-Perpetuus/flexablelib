"""3.7.5: hex colours follow FORCE_COLOR and an empty NO_COLOR does not turn
colour off (core; the component side is in test_v375_colours_components)."""

import pytest

from flexablelib import Table
from flexablelib.colors import color_depth, parse_spec, supports_color


class _Tty(object):
    def isatty(self):
        return True


@pytest.mark.parametrize('force, depth', [
    (None, 'truecolor'), ('3', 'truecolor'), ('2', '256'), ('1', '16'),
    ('true', '16'), (' YES ', '16'), ('0', 'truecolor'), ('', 'truecolor'),
])
def test_color_depth(monkeypatch, force, depth):
    if force is not None:
        monkeypatch.setenv('FORCE_COLOR', force)
    assert color_depth() == depth


@pytest.mark.parametrize('force, spec, expected', [
    (None, '#ff8800', '\x1b[38;2;255;136;0m'),
    ('3', 'on #262626', '\x1b[48;2;38;38;38m'),
    ('2', '#ff8800', '\x1b[38;5;208m'),
    ('2', 'on #262626', '\x1b[48;5;235m'),
    ('2', 'grey23', '\x1b[38;5;237m'),
    ('2', 'color:93', '\x1b[38;5;93m'),
    ('1', '#ff0000', '\x1b[91m'),
    ('1', 'bold #000000 on #ffffff', '\x1b[1;30;107m'),
    ('1', 'color:196', '\x1b[91m'),
    ('1', '196', '\x1b[91m'),
    ('1', 'color:4', '\x1b[34m'),
    ('1', 'color:12', '\x1b[94m'),
    ('1', 'on grey0', '\x1b[40m'),
    ('1', 'red on blue', '\x1b[31;44m'),
])
def test_parse_spec_follows_force_color(monkeypatch, force, spec, expected):
    if force is not None:
        monkeypatch.setenv('FORCE_COLOR', force)
    assert parse_spec(spec) == expected


def test_out_of_range_index_still_errors_at_16_colours(monkeypatch):
    monkeypatch.setenv('FORCE_COLOR', '1')
    with pytest.raises(ValueError):
        parse_spec('color:256')


def test_table_hex_colour_downsampled(monkeypatch):
    t = Table([['a']], headers=['h'])
    t.use_colors = True
    t.header_color = '#ff0000'
    monkeypatch.setenv('FORCE_COLOR', '2')
    out = t.compose()
    assert '\x1b[38;5;196m' in out and '38;2;' not in out
    monkeypatch.setenv('FORCE_COLOR', '1')
    out = t.compose()
    assert '\x1b[91m' in out and '38;5;' not in out


def test_empty_no_color_is_ignored(monkeypatch):
    monkeypatch.setenv('TERM', 'xterm')
    monkeypatch.setenv('NO_COLOR', '')
    assert supports_color(_Tty()) is True
    monkeypatch.setenv('NO_COLOR', '0')
    assert supports_color(_Tty()) is False
