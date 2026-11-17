"""3.7.2: a title, subtitle or caption longer than the width the table has to
fit into (``max_width``, or the terminal) wraps at spaces instead of running
past it; one that fits stays on one line as before."""

import pytest

from flexablelib import Table
from flexablelib.text_width import strip_ansi, visible_width

LONG_TITLE = 'Ventas por sucursal del primer trimestre'
LONG_CAPTION = 'Fuente: sistema de caja, cifras sin IVA'


def _table(**options):
    table = Table(rows=[['Centro', 12], ['Norte', 7]],
                  headers=['Sucursal', 'n'])
    for name, value in options.items():
        setattr(table, name, value)
    return table


def _widths(text):
    return [visible_width(line) for line in strip_ansi(text).split('\n')]


class TestWrapToMaxWidth:
    @pytest.mark.parametrize('max_width', [18, 20, 25, 30])
    def test_every_line_fits(self, max_width):
        table = _table(max_width=max_width, title=LONG_TITLE,
                       subtitle='Datos preliminares de todas las tiendas',
                       caption=LONG_CAPTION)
        out = table.compose()
        assert max(_widths(out)) <= max_width
        words = ' '.join(line.strip() for line in out.split('\n'))
        for text in (LONG_TITLE, LONG_CAPTION):
            assert text in words

    def test_breaks_at_spaces(self):
        lines = _table(max_width=20, title=LONG_TITLE).compose().split('\n')
        title = [line.strip() for line in lines[:2]]
        assert title == ['Ventas por sucursal', 'del primer trimestre']

    def test_title_alignment_kept(self):
        for align, check in (('l', lambda l: not l.startswith(' ')),
                             ('r', lambda l: len(l) == 18)):
            table = _table(max_width=18, title=LONG_TITLE, title_align=align)
            body_width = max(_widths(table.compose()))
            first = table.compose().split('\n')[0]
            assert visible_width(first) <= 18 and body_width <= 18
            if align == 'l':
                assert check(first)

    def test_panel_and_shadow_count(self):
        table = _table(max_width=22, title=LONG_TITLE, caption=LONG_CAPTION,
                       panel=True, shadow=True)
        assert max(_widths(table.compose())) <= 22

    def test_border_title_that_does_not_fit_wraps_above(self):
        table = _table(max_width=20, title=LONG_TITLE,
                       title_position='border', caption=LONG_CAPTION,
                       caption_position='border')
        assert max(_widths(table.compose())) <= 20

    def test_multiline_title_wraps_each_line(self):
        table = _table(max_width=20, title=LONG_TITLE + '\nCorte')
        lines = [line.strip() for line in table.compose().split('\n')]
        assert lines[:3] == ['Ventas por sucursal', 'del primer trimestre',
                             'Corte']

    def test_colour_survives_the_break(self, monkeypatch):
        monkeypatch.setenv('FORCE_COLOR', '1')
        table = _table(max_width=20, title=LONG_TITLE, title_color='red')
        lines = table.compose().split('\n')
        assert '\x1b[31m' in lines[0] and '\x1b[31m' in lines[1]
        assert max(_widths(table.compose())) <= 20

    def test_tabs_counted(self):
        table = _table(max_width=20, caption='a\tb\tc\td\te')
        assert max(_widths(table.compose())) <= 20


class TestUnchangedWhenItFits:
    def test_title_wider_than_table_but_within_max_width(self):
        table = _table(max_width=60, title=LONG_TITLE)
        first = table.compose().split('\n')[0]
        assert first.strip() == LONG_TITLE

    def test_no_max_width_uses_the_terminal(self, terminal):
        terminal(200)
        table = _table(title=LONG_TITLE * 3)
        assert table.compose().split('\n')[0].strip() == LONG_TITLE * 3

    def test_short_terminal_wraps(self, terminal):
        terminal(24)
        table = _table(title=LONG_TITLE)
        assert max(_widths(table.compose())) <= 24

    def test_never_narrower_than_the_table(self):
        # Too narrow to fit, rendered anyway: the labels keep to the table's
        # width rather than being squeezed below it.
        headers = ['c%d' % i for i in range(6)]
        table = Table(rows=[['a' * 5] * 6], headers=headers)
        table.max_width = 10
        table.title = 'x ' * 40
        out = table.compose().split('\n')
        width = max(_widths('\n'.join(out[1:])))
        assert max(_widths('\n'.join(out))) == width


class TestCards:
    def test_cards_labels_keep_to_the_width(self, terminal):
        terminal(200)
        table = _table(title=LONG_TITLE, caption=LONG_CAPTION,
                       responsive=True, breakpoints={'cards': 40})
        assert table.render_mode(18) == 'cards'
        out = table.render(width=18)
        assert max(_widths(out)) <= 18
        assert 'Sucursal' in out or 'Centro' in out
