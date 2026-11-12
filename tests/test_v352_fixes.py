"""3.5.2: dialogs shown with app.push() close with Escape and their buttons;
a form inside a modal closes with Escape; Text with \\r\\n line endings."""

import pytest

from flexablelib import Text, Table, Grid, GridCell
from flexablelib.text_width import visible_width, strip_ansi

C = pytest.importorskip('flexablelib_components')

from flexablelib_tui import App, Key  # noqa: E402


def key(name):
    return Key(name)


def open_app(layer, push):
    app = App(body='x')
    if push:
        app.push(layer)
    else:
        layer.open(app)
    app.render(80, 24)
    return app


@pytest.mark.parametrize('push', [True, False])
class TestModalClose:
    def test_escape_closes(self, push):
        closed = []
        m = C.Modal('hola', on_close=lambda: closed.append(1))
        app = open_app(m, push)
        assert m.is_open
        app.dispatch(key('escape'))
        assert m not in app.layers
        assert not m.is_open
        assert closed == [1]

    def test_button_closes(self, push):
        pressed = []
        m = C.Modal('hola', buttons=[('Cerrar', lambda: pressed.append(1))])
        app = open_app(m, push)
        app.focus(m.buttons[0])
        app.dispatch(key('enter'))
        assert pressed == [1]
        assert m not in app.layers

    def test_close_method(self, push):
        m = C.Modal('hola')
        app = open_app(m, push)
        m.close()
        assert m not in app.layers and not m.is_open

    def test_confirm_dialog(self, push):
        answers = []
        d = C.ConfirmDialog('¿Borrar?', on_cancel=lambda: answers.append(0))
        app = open_app(d, push)
        app.dispatch(key('escape'))
        assert d not in app.layers
        d = C.ConfirmDialog('¿Borrar?', on_cancel=lambda: answers.append(0))
        app = open_app(d, push)
        app.focus(d.buttons[0])
        app.dispatch(key('enter'))
        assert d not in app.layers and answers == [0]

    def test_focus_returns(self, push):
        app = App(body=C.TextInput('Fuera'))
        app.render(80, 24)
        before = app.focused
        m = C.Modal('hola')
        if push:
            app.push(m)
        else:
            m.open(app)
        app.render(80, 24)
        app.dispatch(key('escape'))
        assert app.focused is before

    def test_not_closable_stays(self, push):
        m = C.Modal('hola', closable=False)
        app = open_app(m, push)
        app.dispatch(key('escape'))
        assert m in app.layers and m.is_open


def form(app, on_cancel):
    return C.Form([
        C.TextInput('Nombre', required=True),
        (C.TextInput('Correo'), C.MaskedInput('Teléfono', mask='phone')),
        C.DateInput('Alta'),
        C.Select('Ciudad', ['Mérida', 'CDMX'])],
        on_submit=lambda values: app.pop(),
        on_cancel=(lambda: app.pop()) if on_cancel else None)


@pytest.mark.parametrize('push', [True, False])
@pytest.mark.parametrize('on_cancel', [True, False])
@pytest.mark.parametrize('tabs', [0, 1, 2, 3, 4, 5, 6])
def test_form_in_modal_escape(push, on_cancel, tabs):
    app = App(body='x')
    closed = []
    m = C.Modal(form(app, on_cancel), title='Nuevo cliente', width=64,
                on_close=lambda: closed.append(1))
    if push:
        app.push(m)
    else:
        m.open(app)
    app.render(100, 30)
    for ch in 'Ana':
        app.dispatch(key(ch))
    for _ in range(tabs):
        app.dispatch(key('tab'))
        app.render(100, 30)
    app.dispatch(key('escape'))
    assert m not in app.layers
    # app.pop() from the form's on_cancel keeps the modal's state in step.
    assert not m.is_open
    assert closed == [1]


def test_pop_from_outside_runs_on_close_once():
    closed = []
    app = App(body='x')
    m = C.Modal('hola', on_close=lambda: closed.append(1)).open(app)
    app.pop()
    assert not m.is_open and closed == [1]
    assert app.pop() is None
    assert closed == [1]


def test_popover_state():
    app = App(body='x')
    p = C.Popover('hola').open(app, position='top-right', modal=False)
    assert p.is_open
    app.pop(p)
    assert not p.is_open


@pytest.mark.parametrize('eol', ['\r\n', '\r', '\n'])
def test_text_line_endings(eol):
    lines = Text('x,y{0}a,b{0}'.format(eol)).render(20).split('\n')
    assert not any('\r' in l for l in lines)
    assert [strip_ansi(l).rstrip() for l in lines] == ['x,y', 'a,b', '']
    assert all(visible_width(l) == 20 for l in lines)


def test_text_csv_in_grid():
    csv = Table([['Norte', 1]], headers=['Región', 'Ventas']).to_csv()
    assert '\r\n' in csv
    out = str(Grid([GridCell(Text(csv), title='to_csv()')], width=30, border='rounded'))
    assert '\r' not in out
    rows = out.split('\n')
    assert len(set(visible_width(r) for r in rows if r)) == 1
    assert 'Región,Ventas' in strip_ansi(out)


def test_text_natural_width_ignores_cr():
    assert Text('abc\r\nde\r\n').natural_width() == 3


def test_legacy_text_line_endings():
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        from flexablelib._legacy.widgets import Text as LegacyText
    out = LegacyText('x,y\r\na,b\r\n').render(10)
    assert '\r' not in out
    assert strip_ansi(out).split('\n')[:2] == ['x,y       ', 'a,b       ']
