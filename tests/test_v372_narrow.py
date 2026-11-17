"""3.7.2: ``too_narrow_message`` is also shown when the table comes out wider
than the space for a reason the minimum-width estimate cannot see -- the
digits in front of a decimal point are never cut, so a float column can stay
wider than its share. Before, the overflowing table was returned."""

from flexablelib import Table
from flexablelib.text_width import visible_width

MESSAGE = 'No cabe: {needed} > {available}'


def _floats(max_width, message=MESSAGE, **options):
    table = Table(rows=[[123456789012.5, 'a'], [3.25, 'b']],
                  headers=['monto', 'x'])
    table.max_width = max_width
    table.too_narrow_message = message
    for name, value in options.items():
        setattr(table, name, value)
    return table


def _width(text):
    return max(visible_width(line) for line in text.split('\n'))


def test_message_when_the_integer_digits_do_not_fit():
    out = _floats(15).compose()
    assert out.startswith('No cabe: ')
    needed, available = out[len('No cabe: '):].split(' > ')
    assert int(available) == 15
    assert int(needed) > 15
    # needed is the width the table really takes.
    assert int(needed) == _width(_floats(15, message=None).compose())


def test_without_a_message_the_table_is_drawn_as_before():
    out = _floats(15, message=None).compose()
    assert '123456789012' in out
    assert _width(out) > 15


def test_table_that_fits_is_drawn():
    out = _floats(30).compose()
    assert '123456789012.5' in out
    assert _width(out) <= 30


def test_decimals_dropped_still_fits_and_draws():
    # 18 columns: the decimals go, the integer part stays, it fits.
    out = _floats(20).compose()
    assert 'No cabe' not in out
    assert _width(out) <= 20


def test_panel_and_shadow_are_counted():
    out = _floats(18, panel=True, shadow=True).compose()
    assert out.startswith('No cabe: ') and out.endswith('> 18')


def test_terminal_width_is_the_limit(terminal):
    terminal(15)
    table = _floats(None)
    assert table.compose().startswith('No cabe: ')
    terminal(60)
    assert '123456789012.5' in table.compose()


def test_message_without_placeholders():
    assert _floats(15, message='Ventana muy angosta').compose() == \
        'Ventana muy angosta'
