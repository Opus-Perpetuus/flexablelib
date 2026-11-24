"""Regression tests for the 3.7.7 Grid fixes."""
import signal

import pytest

from flexablelib.layout import Grid, GridCell, strip_ansi


@pytest.fixture
def no_hang():
    if not hasattr(signal, 'SIGALRM'):
        yield
        return

    def boom(*_):
        raise AssertionError('Grid.render hung')
    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


@pytest.mark.parametrize('title', ['\u200d', '\u200b', '\u0301',
                                   '\x1b[31m\x1b[0m', '\u200d\u200b'])
def test_zero_width_title_does_not_hang(no_hang, title):
    grid = Grid([GridCell('abc', title=title), 'x'], columns=1,
                border='ascii')
    lines = grid.render(width=20).split('\n')
    assert lines[0] == '+------------------+'
    assert len({len(strip_ansi(line)) for line in lines}) == 1


def test_title_newline_becomes_space_like_card(no_hang):
    grid = Grid([GridCell('abc', title='a\nb'), 'x'], columns=2,
                border='single', use_colors=False)
    top = grid.render(width=24).split('\n')[0]
    assert top.startswith('┌─ a b ─')
    assert '\n' not in top


def test_title_trailing_newline_keeps_frame(no_hang):
    grid = Grid([GridCell('abc', title='ab\r\n')], columns=1,
                border='single', use_colors=False)
    lines = grid.render(width=16).split('\n')
    assert len(lines) == 3
    assert lines[0].startswith('┌─ ab')
    assert lines[0].endswith('┐')


def test_title_with_tab_is_expanded(no_hang):
    grid = Grid([GridCell('abc', title='a\tb')], columns=1,
                border='single', use_colors=False)
    top = grid.render(width=30).split('\n')[0]
    assert '\t' not in top
    assert top.startswith('┌─ a') and top.endswith('┐')
    assert len(top) == 30
