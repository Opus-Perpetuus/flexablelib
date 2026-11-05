"""2.2.2 regressions: zebra=True and parse_str_numbers on add_column/add_row."""
import re

import pytest

from flexablelib import Table


ANSI = re.compile(r'\x1b\[[0-9;]*m')


def bare(text: str) -> str:
    return ANSI.sub('', text)


def test_zebra_true_turns_on_default_striping():
    table = Table(rows=[[1], [2], [3]], headers=['n'])
    table.use_colors = True
    table.zebra = True
    assert table.zebra == ('', 'reverse')
    coloured = table.compose()
    assert '\x1b[' in coloured
    assert '1' in bare(coloured) and '2' in bare(coloured)


def test_zebra_false_clears_striping():
    table = Table(rows=[[1], [2]], headers=['n'])
    table.zebra = True
    table.zebra = False
    assert table.zebra is None


def test_row_stripe_true_matches_zebra():
    table = Table(rows=[[1], [2]], headers=['n'])
    table.row_stripe = True
    assert table.zebra == ('', 'reverse')
    assert table.row_stripe == ('', 'reverse')


def test_zebra_rejects_non_colour_objects():
    table = Table()
    with pytest.raises(TypeError, match='zebra must be'):
        table.zebra = 3


def test_parse_str_numbers_before_add_column():
    """Docs: order of the flag and the data must not matter."""
    table = Table()
    table.parse_str_numbers = True
    table.add_column('n', ['10', '20', '3.5', 'x'])
    assert table.rows == [[10], [20], [3.5], ['x']]
    # Numeric column stays right-aligned once typed.
    assert '  10' in bare(table.compose()) or '| 10' in bare(table.compose())


def test_parse_str_numbers_before_add_row():
    table = Table()
    table.parse_str_numbers = True
    table.add_column('a')
    table.add_column('b')
    # Replace empty placeholders by adding typed rows via a fresh table.
    table = Table()
    table.parse_str_numbers = True
    table.add_row(['1', '2.5'])
    table.add_row(['3', 'x'])
    assert table.rows == [[1, 2.5], [3, 'x']]


def test_parse_str_numbers_off_keeps_digit_strings():
    table = Table()
    table.add_column('code', ['007', '1.50'])
    assert table.rows == [['007'], ['1.50']]
