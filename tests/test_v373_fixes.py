"""3.7.3: a bare string where a ``(label, action)`` pair is expected -- a
dialog's buttons, a toolbar, a command palette, a timeline's events -- is
one label, not its first two characters taken as label and "action" (which
then raised TypeError when pressed); plus app behaviour that had no tests:
focus cycling with nothing focused, key releases, terminal focus reports,
mouse capture dropped with its dialog (a press on a signature pad kept
drawing after the dialog closed), the screen-reader text with notifications
and a plain footer, and the too-small screen in ASCII."""

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib_tui import App, Key  # noqa: E402
from flexablelib_tui.keys import MouseEvent  # noqa: E402
from flexablelib.text_width import strip_ansi  # noqa: E402


def _app(body, size=(60, 12)):
    app = App(body=body, use_colors=False)
    app.render(*size)
    return app


def _click(app, x, y, action='press'):
    return app.dispatch(Key('mouse', mouse=MouseEvent(0, x, y, action)))


# -- bare labels --------------------------------------------------------------

def test_modal_bare_labels_are_whole_buttons_that_close():
    modal = C.Modal('¿Seguro?', title='Borrar', buttons=['Sí', 'No'])
    assert [b.label for b in modal.buttons] == ['Sí', 'No']
    app = _app(C.Stack([C.Button('Base')]))
    app.push(modal)
    text = strip_ansi(app.render(60, 12))
    assert 'Sí' in text and 'No' in text
    app.focus(modal.buttons[1])
    assert app.dispatch('enter') is True      # was TypeError: 'str' ...
    assert modal not in app.layers


def test_modal_mixes_bare_labels_pairs_and_buttons():
    ran = []
    modal = C.Modal('x', buttons=['Cerrar', ('Guardar', lambda: ran.append(1)),
                                  ('Quedarse', lambda: False),
                                  C.Button('Propio')])
    assert [b.label for b in modal.buttons] == ['Cerrar', 'Guardar',
                                                'Quedarse', 'Propio']
    app = _app(C.Stack([C.Button('Base')]))
    modal.open(app)
    modal.buttons[2].press()
    assert modal in app.layers                # False keeps it open
    modal.buttons[1].press()
    assert ran == [1] and modal not in app.layers


def test_toolbar_bare_labels_and_one_item_tuples():
    pressed = []
    bar = C.Toolbar(['Guardar', ('Salir',),
                     ('Ayuda', lambda: pressed.append('ayuda'))])
    assert [b.label for b in bar.buttons] == ['Guardar', 'Salir', 'Ayuda']
    assert [b.on_press for b in bar.buttons[:2]] == [None, None]
    app = _app(bar)
    app.focus(bar.buttons[0])
    assert app.dispatch('enter') is True      # no action: nothing breaks
    assert bar.buttons[0].presses == 1
    app.dispatch('right')
    app.dispatch('right')
    app.dispatch('enter')
    assert pressed == ['ayuda']
    assert 'Guardar' in strip_ansi(bar.render(40))


def test_command_palette_bare_labels():
    palette = C.CommandPalette(['Abrir', 'Cerrar', ('Copiar', None)])
    assert [c['label'] for c in palette.commands] == ['Abrir', 'Cerrar',
                                                      'Copiar']
    app = _app(C.Stack([C.Button('Base')]))
    app.push(palette)
    app.render(60, 12)
    for ch in 'cerr':
        app.dispatch(Key(ch, ch))
    app.dispatch('enter')                     # was TypeError
    assert palette.ran == ['Cerrar']
    assert palette not in app.layers


def test_timeline_bare_string_is_the_title():
    tl = C.Timeline(['Pedido creado', ('10:00', 'Pagado'),
                     {'title': 'Enviado', 'kind': 'success'}])
    assert tl.events[0] == ('', 'Pedido creado', None, None)
    assert tl.events[1][:2] == ('10:00', 'Pagado')
    text = strip_ansi(tl.render(40))
    assert 'Pedido creado' in text
    assert 'Pedido creado' in tl.a11y_value()


# -- app behaviour ------------------------------------------------------------

def test_shift_tab_with_nothing_focused_goes_to_the_last():
    a, b, c = C.Button('a'), C.Button('b'), C.Button('c')
    app = _app(C.Stack([a, b, c]))
    app.focus(None)
    app.focus_previous()
    assert app.focused is c
    app.focus(None)
    app.focus_next()
    assert app.focused is a


def test_tab_with_nothing_focusable_is_still_used():
    app = _app(C.Stack([C.Badge('solo texto')]))
    assert app.focus_next() is True and app.focused is None


def test_key_release_and_terminal_focus_reports():
    box = C.Checkbox('x')
    app = _app(C.Stack([box]))
    app.focus(box)
    assert app.dispatch(Key(' ', ' ', event='release')) is False
    assert box.value is False
    assert app.dispatch('focusout') is False
    assert app.terminal_focused is False
    assert app.dispatch('focusin') is False
    assert app.terminal_focused is True


def test_mouse_capture_is_dropped_with_its_dialog():
    sig = C.SignatureInput(label='Firma', columns=10, rows=3)
    app = App(body=C.Stack([C.Button('Base')]), mouse=True, use_colors=False)
    app.render(60, 20)
    modal = C.Modal(sig, title='F')
    app.push(modal)
    app.render(60, 20)
    x0, y0 = app.origin(sig)
    _click(app, x0 + 2, y0 + 2)
    assert app._capture is sig
    app.pop(modal)
    assert app._capture is None
    # The drag and release that follow do not draw on the closed pad.
    ink = list(map(list, sig.value)) if sig.value else sig.value
    app.render(60, 20)
    _click(app, x0 + 5, y0 + 2, 'drag')
    _click(app, x0 + 5, y0 + 2, 'release')
    assert (list(map(list, sig.value)) if sig.value else sig.value) == ink


def test_pop_with_nothing_to_close():
    app = _app(C.Stack([C.Button('Base')]))
    assert app.pop() is None
    assert app.pop(C.Modal('x')) is None


def test_linear_text_lists_notifications_and_a_plain_footer():
    app = App(body=C.Stack([C.Button('Guardar')]), footer='F1 ayuda   q salir',
              header='Clientes', use_colors=False)
    app.render(60, 10)
    app.notify('Guardado', kind='success')
    text = app.linear_text()
    lines = text.split('\n')
    assert lines[0] == 'Clientes'
    assert lines[-1] == 'F1 ayuda q salir'
    assert any('Guardado' in line for line in lines)


def test_too_small_screen_in_ascii():
    app = App(body=C.Stack([C.Button('x')]), min_size=(40, 10), ascii=True,
              use_colors=False)
    lines = app.render(30, 6).split('\n')
    assert len(lines) == 6
    text = '\n'.join(lines)
    # Symbols fold to ASCII (× to x); letters such as ñ stay.
    assert 'Ventana muy pequeña' in text and '30x6' in text
    assert '×' not in text


def test_render_without_height_uses_the_screen_height():
    app = App(body=C.Stack([C.Button('x')]), use_colors=False)
    out = app.render(20)
    assert out.split('\n')[0].startswith('[>x<]')
    assert len(out.split('\n')) > 1
