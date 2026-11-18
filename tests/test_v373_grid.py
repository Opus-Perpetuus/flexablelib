"""3.7.3: grids that kept to their width only when everything fit -- a
card in a column too narrow for its frame raised ValueError instead of
the grid stacking, a bordered cell's padding ran past a one- or
two-column track, an int ``columns`` larger than the width can hold
overflowed, and a coloured cell title on a bordered grid raised
IndexError (its escape sequence was laid out one cell per character)."""

import pytest

from flexablelib.layout import Card, Grid, GridCell
from flexablelib.text_width import strip_ansi, visible_width


def _widths(text):
    return [visible_width(line) for line in text.split('\n')]


def test_grid_stacks_cards_that_do_not_fit_their_columns():
    # Three 2-column-wide slots cannot hold a framed card: stack instead of
    # raising "width 2 is too narrow for this card".
    cards = [Card(title='a'), Card(title='b'), Card(title='c')]
    out = Grid(cards, columns=3, gap=1, use_colors=False).render(10)
    assert set(_widths(out)) == {0, 10}     # cards, and the gaps between
    assert [line for line in out.split('\n') if line.startswith('╭')] == \
        ['╭─ a ────╮', '╭─ b ────╮', '╭─ c ────╮']
    one = Grid([Card(title='x')], columns=3, gap=1, use_colors=False)
    assert one.render(10).split('\n')[0] == '╭─ x ────╮'


def test_grid_card_too_narrow_even_stacked_still_raises():
    with pytest.raises(ValueError):
        Grid([Card(title='a')], columns=1, use_colors=False).render(2)


def test_bordered_grid_padding_gives_way_in_narrow_tracks():
    out = Grid(['ab', 'cd', 'ef'], columns=4, gap=0, border='rounded',
               use_colors=False).render(10)
    assert set(_widths(out)) == {10}
    assert out.split('\n')[0] == '╭──┬─┬─┬─╮'
    assert out.split('\n')[1] == '│ab│c│e│ │'


def test_unbordered_grid_padding_gives_way_too():
    out = Grid(['abc', 'def'], columns=2, gap=1, padding=2,
               use_colors=False).render(7)
    assert max(_widths(out)) <= 7


def test_int_columns_never_more_than_fit():
    grid = Grid([''], columns=5, gap=0, border='rounded', use_colors=False)
    assert grid.column_count(10) == 4
    assert set(_widths(grid.render(10))) == {10}
    plain = Grid(list('abcdef'), columns=6, gap=2, use_colors=False)
    assert plain.column_count(10) == 4
    assert max(_widths(plain.render(10))) <= 10
    assert plain.column_count(80) == 6


def test_coloured_cell_title_on_a_bordered_grid():
    title = '\x1b[31mrojo\x1b[0m'
    out = Grid(['aa', GridCell('', title=title)], border='single',
               use_colors=False).render(20)
    lines = out.split('\n')
    assert set(_widths(out)) == {20}       # was IndexError
    assert title in lines[0] and strip_ansi(lines[0]) == \
        '┌─────────┬─ rojo ─┐'
    narrow = Grid(['aa', GridCell('', title=title)], border='single',
                  use_colors=False).render(10)
    assert strip_ansi(narrow.split('\n')[2]) == '├─ rojo ─┤'
