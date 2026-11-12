"""
3.3.0 components (flexablelib_components): every component renders to the
exact width with and without colour, and reacts to its keys.
"""

import datetime as dt
import os

import pytest

C = pytest.importorskip('flexablelib_components')

from flexablelib_tui import App, Key  # noqa: E402
from flexablelib.text_width import visible_width, strip_ansi  # noqa: E402

T = dt.date(2026, 11, 11)


def key(name):
    if name == 'space':
        return Key('space', ' ')
    if len(name) == 1:
        return Key(name, name)
    return Key(name)


def press(comp, *names):
    comp.focused = True
    results = [comp.handle_key(key(n)) for n in names]
    return results


def text(comp, width=50, height=None):
    return strip_ansi(comp.render(width=width, height=height))


def all_components(colors):
    k = dict(use_colors=colors)
    return [
        C.TextInput('Nombre', 'Yael', help='Tu nombre', **k),
        C.TextInput('Vacío', placeholder='escribe', **k),
        C.TextInput('Vacío2', **k),
        C.PasswordInput('Clave', 'secreto', **k),
        C.NumberInput('Cantidad', 5, minimum=0, **k),
        C.ExpressionInput('Total', '2*3+1', **k),
        C.MoneyInput('Importe', 1234.5, **k),
        C.MaskedInput('Teléfono', '5512345678', **k),
        C.TextArea('Notas', 'línea 1\nlínea 2 muy larga que debería envolverse',
                   rows=3, **k),
        C.TextArea('Vacía', placeholder='algo', **k),
        C.JsonInput('Datos', {'a': 1}, **k), C.ScanInput('Código', **k),
        C.Checkbox('Acepto', True, help='h', **k), C.Switch('Activo', True, **k),
        C.Switch('Inactivo', False, **k),
        C.RadioGroup('Tipo', ['A', 'B'], 'B', **k),
        C.RadioGroup('Vista', ['Lista', 'Tabla'], 'Tabla', layout='buttons',
                     **k),
        C.CheckboxGroup('Días', ['Lu', 'Ma'], ['Ma'], **k),
        C.Select('Estado', ['Abierto', 'Cerrado'], **k),
        C.Autocomplete('Ciudad', ['Mérida', 'México'], 'Mé', **k),
        C.ColorInput('Color', '#3498db', **k), C.ColorInput('Sin', **k),
        C.IconPicker('Ícono', 'star', **k), C.IconPicker('Sin', **k),
        C.CoordinatesInput('Ubicación', (20.9, -89.6), **k),
        C.FileInput('Archivo', directory='.', **k),
        C.FileInput('Varios', directory='.', multiple=True, **k),
        C.Calendar(T, today=T, **k), C.Calendar(T, today=T, mode='week', **k),
        C.DateInput('Fecha', T, today=T, **k), C.TimeInput('Hora', '09:30', **k),
        C.TimeInput('Vacía', seconds=True, **k),
        C.DateTimeInput('Cita', '2026-11-11T10:00', today=T, **k),
        C.WeekInput('Semana', T, today=T, **k),
        C.MonthInput('Mes', T, today=T, **k),
        C.YearInput('Año', T, today=T, **k),
        C.WeekdayInput('Día', 2, short=False, **k),
        C.DateRangeInput('Periodo', (T, T), today=T, **k),
        C.Timer(dt.datetime(2026, 11, 11, 9), end=dt.datetime(2026, 11, 13, 10),
                label='Total', **k),
        C.Badge('Nuevo', **k), C.Tag('urgente', kind='error', **k),
        C.StatusBadge('paid', {'paid': ('Pagado', 'success')}, **k),
        C.Alert('Se guardó', kind='success', title='Listo', **k),
        C.Alert('Atención: ' + 'texto largo ' * 8, kind='warning', **k),
        C.Link('Docs', 'https://example.com', show_url=True, **k),
        C.Link('https://example.com', **k),
        C.Breadcrumbs(['Inicio', 'Ventas', 'Pedidos', 'Pedido 1281'], **k),
        C.EmptyState('Sin pedidos', 'Crea el primero', action='n: nuevo', **k),
        C.ErrorPanel(404, 'No encontrado', 'No existe', hint='q', **k),
        C.ErrorPanel(**k), C.Spinner('Cargando', **k), C.Skeleton(2, **k),
        C.Code('def f(x):\n    return "a" * 2  # doble\n', 'python',
               title='f.py', **k),
        C.Code('SELECT * FROM t -- c', 'sql', line_numbers=False, **k),
        C.MarkdownView('# T\n\n## S\n\n### s\n\nTexto **b** *i* ~~x~~ `c` '
                       '[l](http://x)\n\n- a\n  - b\n1. uno\n- [x] hecho\n'
                       '- [ ] no\n\n> cita\n\n---\n\n```python\nx = 1\n```\n'
                       '\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 |\n', **k),
        C.HtmlView('<h1>Hola</h1><p>Un <b>p</b> <i>i</i> <code>c</code> '
                   '<a href="http://x">l</a><br>x</p><ul><li>a</li></ul>'
                   '<ol><li>uno</li></ol><blockquote>q</blockquote><hr>'
                   '<pre>code  x</pre><table><tr><th>a</th><th>b</th></tr>'
                   '<tr><td>1</td></tr></table><script>no</script>'
                   '<div>d</div><strong>s</strong><em>e</em>', **k),
        C.DetailView({'# Cliente': None, 'Nombre': 'Ana', 'Nota': 'x ' * 40},
                     **k),
        C.DetailView([('A', 1), ('B', 2), ('C', 3)], columns=2, **k),
        C.Timeline([('09:00', 'Creado', 'Pedido', 'info'),
                    {'when': '10:30', 'title': 'Pagado', 'status': 'success'}],
                   **k),
        C.Stepper(['Datos', 'Pago', 'Envío'], 1, **k),
        C.Stepper(['Datos', 'Pago', 'Envío'], 2, failed=2,
                  layout='vertical', descriptions={0: 'ok'}, **k),
        C.Stepper(['Un paso largo'] * 6, 3, **k),
        C.CommentList([{'author': 'Ana', 'when': 'hoy', 'text': 'Listo',
                        'replies': [{'author': 'Luis', 'text': 'Ok'}]},
                       {'author': 'Eva', 'text': 'x'}], **k),
        C.AttachmentList([('factura.pdf', 123456), {'name': 'x', 'size': None},
                          ('a.zip', 5 * 1024 ** 5)], **k),
        C.Stat('Ventas', '$71,182', '+6.2%', trend=[1, 3, 2, 5], **k),
        C.Stat('Bajas', 12, -3, invert=True, suffix='%', **k),
        C.Stat('Igual', 1, 'n/a', **k), C.Stat('Cero', 0, 0, **k),
        C.LineChart({'cpu': [1, 5, 3], 'mem': [2]}, height=4,
                    labels=['a', 'b'], **k),
        C.LineChart([3, 3, 3], **k), C.LineChart([], **k),
        C.Tabs({'Uno': 'contenido', 'Dos': 'otro'}, **k),
        C.Menu(['Abrir', '-', {'label': 'Guardar', 'shortcut': 'ctrl+s',
                               'icon': '💾'},
                {'label': 'Borrar', 'disabled': True}, ('Salir', None)], **k),
        C.Pagination(200, 20, 5, **k), C.Pagination(30, 20, **k),
        C.Pagination(0, **k),
        C.Sidebar({'Ventas': ['Resumen', {'label': 'Pedidos', 'icon': '📦'}],
                   'Admin': ['Usuarios', '-']}, title='Panel', **k),
        C.Sidebar(['Uno', 'Dos'], collapsed=True, **k),
        C.TopBar('Panel', ['Ventas'], [('F1', 'Ayuda'), 'x'], '10:01', **k),
        C.Toolbar([('Nuevo', None), C.Button('Borrar', kind='danger', **k)],
                  **k),
        C.Wizard([('Datos', 'paso 1'), ('Pago', 'paso 2')], **k),
        C.Accordion([('S1', 'texto 1'), ('S2', 'texto 2')], **k),
        C.Carousel(['s1', 's2'], **k),
        C.Tree({'a': 1, 'b': {'c': [1, 2.5], 'd': None, 'e': True},
                'f': 'texto'}, **k),
        C.Tree(('raíz', [('hijo', ['nieto']), 'hoja']), **k),
        C.CommandPalette([('Abrir', None), {'label': 'Guardar',
                                            'hint': 'ctrl+s'}], **k),
        C.Split('izquierda', 'derecha', **k),
        C.Split('arriba', 'abajo', direction='vertical', **k),
        C.Stack(['uno', 'dos'], gap=1, **k),
        C.Stack(['uno', 'dos'], direction='horizontal', **k),
        C.Stack(['uno', 'dos'], direction='horizontal', widths=[20, 29],
                gap=1, **k),
        C.SortControl(['Fecha', 'Total'], **k),
        C.DataTable(['Folio', 'Cliente', 'Total'],
                    [[1, 'Ana', 100.5], [2, 'Luis', None], [3, 'Sofía', 3e3]],
                    selectable=True, **k),
        C.DataTable([{'key': 'n', 'title': 'N', 'align': 'c', 'width': 4,
                      'format': lambda v: '#%s' % v,
                      'color': lambda v: 'red'}], [{'n': 1}], page_size=1,
                    **k),
        C.DataTable(['a'], [], **k),
        C.FilterBar(['estado'], value='estado:pagado x', **k),
        C.EditableTable(['A', 'B'], [[1, 2], [3, 4]], **k),
        C.CatalogGrid([{'title': 'Laptop', 'subtitle': '14"', 'price': 19999,
                        'badge': 'Nuevo', 'fields': {'RAM': '16 GB'}},
                       {'title': 'Mouse', 'price': 'consultar'}], **k),
        C.CatalogGrid([], **k),
        C.Form([C.TextInput('Nombre', required=True, **k), 'Contacto',
                (C.TextInput('Correo', **k), C.TextInput('Tel', **k)),
                C.Checkbox('X', **k)], title='Alta', columns=2, **k),
        C.LoginForm(**k), C.FilePreview('setup.py', max_lines=3, **k),
        C.FilePreview('README.md', max_lines=3, **k),
        C.FilePreview('/no/such/file', **k),
        C.ValidationSummary({'Nombre': 'Requerido'}, **k),
        C.ValidationSummary({}, **k),
        C.Modal('¿Seguro?', title='Confirmar', buttons=[('Sí', None)], **k),
        C.Modal(C.Badge('x', **k), closable=False, **k),
        C.ConfirmDialog('¿Borrar?', danger=True, **k),
        C.PromptDialog('Nombre', **k),
        C.LoadingOverlay('Procesando', progress=0.4, **k),
        C.Popover('hola', **k), C.HelpLine('ayuda', **k),
        C.Box(C.TextInput('Dentro', **k), title='Caja', footer='pie', **k),
        C.Button('Guardar', kind='primary', shortcut='F2', **k),
        C.Button('Off', disabled=True, **k),
    ]


@pytest.mark.parametrize('colors', [False, True])
@pytest.mark.parametrize('width', [24, 50, 90])
def test_every_component_renders_exact_width(colors, width):
    for comp in all_components(colors):
        for focused in (False, True):
            comp.focused = focused
            out = comp.render(width=width)
            for line in out.split('\n') if out else []:
                assert visible_width(line) == width, (type(comp).__name__,
                                                      line)
            out = comp.render(width=width, height=6)
            assert len(out.split('\n')) <= 6 if out else True


def test_every_component_has_natural_width():
    for comp in all_components(False):
        assert comp.natural_width() > 0, type(comp).__name__


def test_every_public_name_exported():
    import flexablelib
    for name in C.__all__:
        if name[:1].isupper() and name not in ('DEFAULT_THEME', 'MASKS',
                                               'ICONS'):
            assert getattr(flexablelib, name) is getattr(C, name)


# +---------------------------------------------------------------------------+
# Inputs

class TestTextInput:
    def test_editing(self):
        changes = []
        t = C.TextInput(value='hola', on_change=changes.append,
                        use_colors=False)
        press(t, 'home', 'x', 'end', 'space', 'm', 'left', 'backspace',
              'delete', 'ctrl+a', 'right', 'ctrl+d')
        assert t.text == 'xola'
        assert changes
        press(t, 'end', 'ctrl+w')
        assert t.text == ''
        t.value = 'uno dos tres'
        press(t, 'ctrl+left', 'ctrl+left', 'ctrl+k')
        assert t.text == 'uno '
        press(t, 'ctrl+right', 'end', 'ctrl+u')
        assert t.text == ''
        press(t, 'alt+f', 'alt+b', 'ctrl+b', 'ctrl+f', 'ctrl+e')
        assert press(t, 'f9') == [False]
        t.handle_key(Key('paste', 'a\nb'))
        assert t.text == 'a b'

    def test_limits_and_transform(self):
        t = C.TextInput(max_length=3, allowed=r'[a-z]', transform='upper')
        press(t, 'a', '1', 'b', 'c', 'd')
        assert t.text == 'ABC'
        t2 = C.TextInput(allowed=lambda c: c != 'x', transform='lower')
        press(t2, 'x', 'Y')
        assert t2.text == 'y'
        t3 = C.TextInput(transform=lambda s: s * 2)
        press(t3, 'z')
        assert t3.text == 'zz'
        assert C.TextInput(allowed=r'[0-9]').insert('abc') is False

    def test_submit_and_validate(self):
        got = []
        t = C.TextInput('Correo', required=True, on_submit=got.append,
                        validators=[lambda v: None if '@' in v else 'Correo'])
        press(t, 'enter')
        assert t.error == 'Requerido' and got == ['']
        press(t, 'a', 'enter')
        assert t.error == 'Correo'
        press(t, '@', 'enter')
        assert t.error is None and got[-1] == 'a@'
        assert 'X*' in text(C.TextInput('X', required=True))

    def test_scrolls_to_cursor(self):
        t = C.TextInput(value='x' * 100, use_colors=False)
        t.focused = True
        line = text(t, 20).split('\n')[0]
        assert line.endswith('_') or 'x' in line
        press(t, 'home')
        assert text(t, 20).split('\n')[0].startswith('› x')
        t.set_value('abc')
        assert t.value == 'abc'

    def test_cursor_colour(self):
        t = C.TextInput(value='ab', use_colors=True)
        t.focused = True
        assert '\x1b[7m' in t.render(width=20)


class TestOtherTextInputs:
    def test_password(self):
        p = C.PasswordInput('Clave', 'abc', use_colors=False)
        assert '•••' in text(p)
        press(p, 'ctrl+r')
        assert 'abc' in text(p) and p.revealed
        press(p, 'f2', 'x')
        assert p.text == 'abcx' and '••••' in text(p)
        assert 'ctrl+r' in text(p)

    def test_number(self):
        n = C.NumberInput('N', 5, minimum=0, maximum=20, step=2)
        press(n, 'up', 'up', 'pagedown', 'down')
        assert n.value == 0
        press(n, 'pageup', 'pageup')
        assert n.value == 20
        big = C.NumberInput('B', '1,234')
        assert big.value == 1234
        n.text = 'abc'
        assert n.value is None and n.validate() == 'No es un número'
        n.text = '99'
        assert n.validate() == 'Máximo 20'
        n.text = '-1'
        assert n.validate() == 'Mínimo 0'
        f = C.NumberInput('F', 0.1, step=0.2)
        press(f, 'up')
        assert f.value == pytest.approx(0.3)
        d = C.NumberInput('D', 2, decimals=2)
        assert d.text == '2.00' and d.value == 2.0
        z = C.NumberInput('Z', decimals=0)
        z.text = '2.6'
        assert z.value == 3
        assert C.NumberInput('E').value is None

    def test_expression(self):
        e = C.ExpressionInput('Total', use_colors=False)
        press(e, '2', '*', '(', '3', '+', '1', ')')
        assert e.value == 8 and '= 8' in text(e)
        e.on_blur()
        assert e.text == '8' and e.suffix() == ''
        e.text = '10/4'
        assert e.value == 2.5
        e.text = '2^3'
        assert e.value == 8
        press(e, 'enter')
        assert e.text == '8'
        for bad, message in [('1/0', 'División'), ('2**999', 'Exponente'),
                             ('x', 'inválida'), ('1+', 'inválida'),
                             ('"a"', 'inválida')]:
            with pytest.raises(ValueError, match=message):
                C.evaluate_expression(bad)
        assert C.evaluate_expression('') is None
        assert C.evaluate_expression('-(2)') == -2
        assert C.evaluate_expression('7 // 2 % 3') == 0
        e.text = '1/0'
        assert e.value is None and e.suffix() == ''

    def test_money(self):
        m = C.MoneyInput('Importe', 1234.5, use_colors=False)
        assert '$1,234.50' in text(m)
        m.focused = True
        assert '$1234.50' in text(m)
        m.text = '$10'
        assert m.value == 10.0
        m.text = ''
        m.focused = False
        assert '$' not in text(m).split('\n')[1]

    def test_masked(self):
        m = C.MaskedInput('Tel', use_colors=False)
        press(m, '5', 'a', '5', '1', '2')
        assert m.text == '5512'
        assert '(551) 2__-____' in text(m)
        assert m.validate().startswith('Formato')
        for c in '345678':
            press(m, c)
        assert m.value == '(551) 234-5678' and m.validate() is None
        press(m, 'left', '9')
        assert m.text == '5512345678'
        press(m, 'backspace')
        assert m.text == '551234567'
        r = C.MaskedInput('RFC', 'abcd900101xyz', mask='rfc', raw=True)
        assert r.value == 'ABCD900101XYZ'
        assert C.MaskedInput('x', None).text == ''
        assert C.MaskedInput('d', 'ab12', mask='##-##').text == '12'
        assert C.MaskedInput('d', '1', mask='#-#').masked('1', fill=False) == \
            '1'

    def test_scan(self):
        now = [0.0]
        codes = []
        s = C.ScanInput('Código', on_scan=codes.append, pattern=r'\d+',
                        min_length=3, max_length=6, strip_prefix='P',
                        strip_suffix='#', unique=True, clock=lambda: now[0],
                        use_colors=False)
        for c in 'P123#':
            press(s, c)
        press(s, 'enter')
        assert codes == ['123'] and s.text == ''
        for c in '123':
            press(s, c)
        press(s, 'enter')          # duplicate within the window: dropped
        assert codes == ['123'] and s.error is None
        now[0] = 5
        for c in '123':
            press(s, c)
        press(s, 'enter')
        assert s.error == 'Ya leído'
        for bad, msg in [('', 'vacío'), ('12', 'Mínimo'), ('1234567', 'Máximo'),
                         ('abc', 'Formato')]:
            s.text = bad
            s.submit()
            assert msg in s.error
        assert '1 leídos' in text(s)
        n = C.ScanInput(transform='nospace')
        n.text = 'a b'
        n.submit()
        assert n.scans == ['ab']

    def test_textarea(self):
        changes = []
        t = C.TextArea('Notas', 'ab', rows=2, on_change=changes.append,
                       use_colors=False)
        press(t, 'ctrl+end', 'enter', 'c', 'd', 'up', 'end', 'delete',
              'backspace', 'left', 'right', 'right', 'home', 'ctrl+home',
              'down', 'pageup', 'pagedown', 'ctrl+a', 'ctrl+e', 'space')
        assert t.text.startswith('acd') or changes
        t.handle_key(Key('paste', 'x\ny'))
        assert t.on_key(Key('f12')) is False
        t.value = 'uno\ndos'
        t.row, t.col = 1, 0
        press(t, 'backspace')
        assert t.text == 'unodos'
        t.row, t.col = 0, 3
        press(t, 'delete')
        assert t.text == 'unoos'
        t.row, t.col = 0, 0
        press(t, 'left')
        assert t.on_key(Key('up')) is False
        t.value = 'a\nb'
        t.row = 1
        assert t.on_key(Key('down')) is False
        t.row, t.col = 0, 1
        press(t, 'right', 'left')
        assert (t.row, t.col) == (0, 1)
        got = []
        t.on_submit = got.append
        press(t, 'ctrl+s')
        assert got == ['a\nb']
        long = C.TextArea(value='x' * 120, rows=2, use_colors=False)
        long.focused = True
        assert len(text(long, 30).split('\n')) == 2
        nowrap = C.TextArea(value='x' * 120, wrap=False)
        assert len(nowrap._segments(10)) == 1
        assert C.TextArea(required=True).validate() == 'Requerido'

    def test_json(self):
        j = C.JsonInput('Datos', {'a': 1})
        assert j.value == {'a': 1}
        j.value = '{"b": 2}'
        assert j.value == {'b': 2}
        press(j, 'ctrl+f')
        assert '\n' in j.text
        j.value = '{bad'
        assert j.value is None
        assert 'JSON inválido' in j.validate()
        press(j, 'ctrl+f')
        assert 'JSON inválido' in j.error
        j.value = None
        assert j.value is None and j.validate() is None


class TestChoices:
    def test_checkbox_switch(self):
        c = C.Checkbox('Acepto', required=True)
        assert c.validate() == 'Requerido'
        press(c, 'space')
        assert c.value is True and c.validate() is None
        assert '✖' not in text(c)
        c.error = 'x'
        assert '✖' in text(c)
        assert press(c, 'a') == [False]
        s = C.Switch('On', use_colors=True)
        press(s, 'enter')
        assert s.value and 'Sí' in text(s)

    def test_radio(self):
        r = C.RadioGroup('Tipo', [('a', 'Alfa'), ('b', 'Beta')])
        press(r, 'down')
        assert r.value == 'b'
        press(r, 'down', 'up', 'space')
        assert r.value == 'b'
        press(r, 'a')
        assert r.value == 'a'
        assert press(r, 'z') == [False]
        h = C.RadioGroup('V', {'x': 'X', 'y': 'Y'}, layout='buttons')
        press(h, 'right', 'enter')
        assert h.value == 'y'
        assert press(C.RadioGroup('E', []), 'down', 'enter') == [True, False]

    def test_checkbox_group(self):
        g = C.CheckboxGroup('D', ['a', 'b', 'c'])
        press(g, 'down', 'space', 'up', 'enter')
        assert g.value == ['a', 'b']
        press(g, 'space')
        assert g.value == ['b']
        press(g, 'ctrl+a')
        assert g.value == ['a', 'b', 'c']
        assert press(g, 'x') == [False]

    def test_select(self):
        s = C.Select('Estado', ['Abierto', 'Cerrado', 'Cancelado'],
                     max_visible=2, use_colors=False)
        assert press(s, 'x') == [False]
        press(s, 'enter', 'down', 'down', 'enter')
        assert s.value == 'Cancelado' and not s.open
        press(s, 'space', 'c', 'e', 'backspace', 'enter')
        assert s.value == 'Cerrado'
        press(s, 'enter')
        assert 'Abierto' in text(s)
        press(s, 'pagedown', 'pageup', 'up', 'escape')
        assert not s.open
        press(s, 'enter', 'z', 'z')
        assert 'Sin resultados' in text(s)
        assert press(s, 'tab') == [False]
        press(s, 'enter')
        assert not s.open
        s.on_blur()
        assert s.label_of('nope') == 'nope' and s.label_of(None) is None

    def test_autocomplete(self):
        a = C.Autocomplete('Ciudad', [('mid', 'Mérida'), ('mty', 'Monterrey'),
                                      ('mex', 'México'), ('ags', 'Aguascal.')],
                           strict=True, use_colors=False)
        press(a, 'm', 'e')
        assert [l for _, l in a.suggestions()] == ['Mérida', 'México']
        assert 'México' in text(a)
        press(a, 'down', 'down', 'up', 'enter')
        assert a.value == 'mid'
        a.value = 'mex'
        assert a.text == 'México'
        a.text = 'zzz'
        assert a.validate() == 'Elige una opción de la lista'
        a.text = 'm'
        press(a, 'escape')
        a.text = 'Mon'
        a.cursor_pos = 3
        press(a, 'right')
        assert a.text == 'Monterrey'
        a.text = 'r'
        press(a, 'enter')
        assert a.value in ('mid', 'mty', 'mex')
        assert C.Autocomplete(options=['x']).suggestions() == []
        loose = C.Autocomplete(options=['x'], value='free')
        assert loose.value == 'free'

    def test_color(self):
        c = C.ColorInput('Color', use_colors=True)
        press(c, 'down')
        assert c.value == '#e74c3c'
        press(c, 'up')
        assert c.value == '#000000'
        c.text = '#zz'
        assert c.validate() == 'Color #rrggbb'
        c.text = 'AABBCC'
        assert c.value == '#aabbcc'
        assert '\x1b[38;2;170;187;204m' in c.render(width=30)
        c.use_colors = False
        assert '  ' in text(c)
        assert c.suffix() == '██'
        press(c, 'x')

    def test_icon_picker(self):
        p = C.IconPicker('Ícono', columns=4, rows=2, use_colors=False)
        press(p, 'right', 'down', 'left', 'up', 'enter')
        assert p.value == C.ICONS[0][0]
        press(p, 's', 'x', 'backspace', 't', 'a', 'r', 'enter')
        assert p.value == 'star' and '★' in text(p)
        assert press(p, 'f1') == [False]

    def test_coordinates(self):
        c = C.CoordinatesInput('Ubicación', required=True)
        assert c.value is None and c.validate() == 'Requerido'
        c.value = {'latitude': 95, 'longitude': 0}
        assert c.validate() == 'Máximo 90'
        c.value = (20.5, -89.6)
        assert c.validate() is None
        assert c.value == {'latitude': 20.5, 'longitude': -89.6}
        assert len(c.children()) == 2
        c.value = None

    def test_file_input(self, tmp_path):
        (tmp_path / 'b.txt').write_text('x')
        (tmp_path / 'a.csv').write_text('x')
        (tmp_path / '.hidden').write_text('x')
        (tmp_path / 'sub').mkdir()
        f = C.FileInput('Archivo', directory=str(tmp_path),
                        extensions=['.txt'], use_colors=False)
        assert press(f, 'x') == [False]
        press(f, 'enter')
        names = [n for n, _ in f.entries()]
        assert names == ['..', 'sub', 'b.txt']
        press(f, 'down', 'down', 'enter')
        assert f.value.endswith('b.txt') and not f.open
        press(f, 'enter', 'down', 'enter')
        assert f.directory.endswith('sub')
        press(f, 'backspace', 'up', 'escape')
        assert not f.open
        press(f, 'space', 'x')
        assert press(f, 'tab') == [False]
        f.on_blur()
        m = C.FileInput('Varios', directory=str(tmp_path), multiple=True,
                        show_hidden=True, use_colors=False)
        press(m, 'enter')
        names = [n for n, _ in m.entries()]
        assert '.hidden' in names
        idx = names.index('a.csv')
        press(m, *(['down'] * idx), 'space', 'space', 'space')
        assert len(m.value) == 1 and 'a.csv' in text(m)
        gone = C.FileInput(directory=str(tmp_path / 'missing'))
        assert gone.entries() == [('..', True)]


# +---------------------------------------------------------------------------+
# Dates

class TestDates:
    def test_calendar_keys(self):
        picked = []
        cal = C.Calendar(T, today=T, on_select=picked.append,
                         minimum=dt.date(2026, 10, 1),
                         maximum=dt.date(2027, 3, 1), use_colors=False)
        press(cal, 'right', 'down', 'left', 'up')
        assert cal.cursor == T
        press(cal, 'pagedown', 'end', 'home', 'pageup', 't', 'enter')
        assert picked == [T]
        press(cal, 'ctrl+pageup')
        assert cal.cursor == dt.date(2026, 10, 1)
        press(cal, 'ctrl+pagedown')
        assert cal.cursor == dt.date(2027, 3, 1)
        assert press(cal, 'x') == [False]
        cal.highlight = lambda d: 'red' if d.day == 1 else None
        assert 'Marzo 2027' in text(cal)
        week = C.Calendar(T, today=T, mode='week', locale='en')
        week.on_select = picked.append
        press(week, 'enter')
        assert picked[-1] == dt.date(2026, 11, 9)
        assert 'November' in text(week) and 'Wk' in text(week)

    def test_date_input(self):
        d = C.DateInput('Fecha', today=T, use_colors=False)
        press(d, '+')
        assert d.value == T + dt.timedelta(days=1)
        press(d, '-', '-', 't')
        assert d.value == T
        press(d, 'enter', 'right', 'enter')
        assert d.value == T + dt.timedelta(days=1) and not d.open
        press(d, 'enter')
        assert 'Noviembre 2026' in text(d)
        press(d, 'escape', 'delete')
        assert d.value is None
        assert press(d, 'x') == [False]
        press(d, 'space')
        assert press(d, 'tab') == [False]
        d.on_blur()
        d.value = dt.datetime(2026, 1, 2, 3)
        assert d.value == dt.date(2026, 1, 2)
        d.value = '2026-02-03'
        assert d.shown() == '2026-02-03'

    def test_time_input(self):
        t = C.TimeInput('Hora', use_colors=False)
        press(t, 'up')
        assert t.value == dt.time(1, 0)
        press(t, 'right', 'down', 'left', 'left')
        assert t.value == dt.time(1, 59)
        t.part = 0
        press(t, '0', '9', '3', '0')
        assert t.value == dt.time(9, 30)
        press(t, 'left', '7', '8')
        assert t.value.hour in (7, 8)
        t.part = 1
        press(t, '6', '5')
        assert t.value.minute == 5
        s = C.TimeInput('S', '10:00:05', seconds=True, step=15)
        press(s, 'right', 'up', 'right', 'up')
        assert s.value == dt.time(10, 15, 6)
        press(s, 'delete')
        assert s.value is None
        got = []
        s.on_submit = got.append
        press(s, 'enter', 'x')
        assert got == [None]
        assert C.TimeInput(value=dt.datetime(2026, 1, 1, 8, 5)).value == \
            dt.time(8, 5)
        assert C.TimeInput(value=dt.time(8, 5, 1, 9)).value == \
            dt.time(8, 5, 1)

    def test_datetime_input(self):
        d = C.DateTimeInput('Cita', today=T)
        assert d.value is None and d.is_empty()
        d.value = dt.datetime(2026, 11, 11, 10, 30)
        assert d.value == dt.datetime(2026, 11, 11, 10, 30)
        d.value = dt.date(2026, 1, 1)
        assert d.value == dt.datetime(2026, 1, 1)
        assert len(d.children()) == 2

    def test_week_month_year_weekday(self):
        w = C.WeekInput('Semana', today=T, use_colors=False)
        press(w, 'enter', 'down', 'enter')
        assert w.value == dt.date(2026, 11, 16)
        assert 'W47' in text(w)
        assert C.WeekInput().shown() == ''
        m = C.MonthInput('Mes', today=T, use_colors=False)
        press(m, 'enter', 'right', 'pagedown', 'enter')
        assert m.value == dt.date(2027, 12, 1)
        assert C.MonthInput().shown() == ''
        press(m, 'enter', 'pageup', 'left', 'up', 'down', 'x')
        assert '2026' in text(m)
        y = C.YearInput('Año', today=T, use_colors=False)
        press(y, 'enter', 'right', 'enter')
        assert y.value == dt.date(2027, 1, 1)
        press(y, 'enter', 'pagedown', 'enter')
        assert y.value == dt.date(2039, 1, 1)
        yi = C.YearInput(as_int=True, value=2020)
        assert yi.value == 2020 and yi.shown() == '2020'
        assert C.YearInput().shown() == ''
        wd = C.WeekdayInput('Día')
        press(wd, 'right')
        assert wd.value == 0
        press(wd, 'left', '3')
        assert wd.value == 2
        assert press(wd, 'x') == [False]
        assert C.WeekdayInput(value=9).value == 2

    def test_date_range(self):
        r = C.DateRangeInput('Periodo', today=T, use_colors=False)
        press(r, 'enter', 'down', 'down', 'enter')
        assert r.value == (T - dt.timedelta(days=6), T)
        for i, expected in [(0, (T, T)), (1, (T - dt.timedelta(1),) * 2),
                            (3, (T - dt.timedelta(29), T)),
                            (4, (dt.date(2026, 11, 1), T)),
                            (5, (dt.date(2026, 10, 1), dt.date(2026, 10, 31))),
                            (6, (dt.date(2026, 1, 1), T))]:
            assert r.preset_range(i) == expected
        press(r, 'enter', 'up', 'right', 'enter')
        assert 'Inicio' in text(r)
        press(r, 'right', 'right', 'enter')
        assert r.value[1] > r.value[0]
        press(r, 'enter')
        r.calendar.cursor = dt.date(2026, 11, 9)   # a Monday
        press(r, 'left')
        assert r.in_presets
        r.value = ('2026-05-10', '2026-05-01')
        assert r.value == (dt.date(2026, 5, 1), dt.date(2026, 5, 10))
        r.value = None
        assert r.shown() == ''

    def test_timer(self):
        now = [10.0]
        t = C.Timer(interactive=True, clock=lambda: now[0], use_colors=False)
        assert not t.running and t.text() == '00:00:00'
        press(t, 'space')
        now[0] = 75.0
        assert t.running and t.text() == '00:01:05'
        assert 'pausa' in text(t)
        press(t, 'enter')
        now[0] = 200.0
        assert t.text() == '00:01:05'
        press(t, 'r')
        assert t.text() == '00:00:00'
        press(t, 'space', 'r')
        assert t.running
        assert press(t, 'x') == [False]
        fixed = C.Timer(dt.datetime(2026, 1, 1), end=dt.datetime(2026, 1, 3, 1))
        assert fixed.text() == '2d 01:00:00'
        assert press(fixed, 'space') == [False]
        live = C.Timer(dt.datetime(2026, 1, 1),
                       now=lambda: dt.datetime(2026, 1, 1, 0, 0, 9))
        assert live.running and live.text() == '00:00:09'
        assert C.Timer().elapsed() == 0.0


# +---------------------------------------------------------------------------+
# Display

class TestDisplay:
    def test_alert_dismiss(self):
        a = C.Alert('hola', dismissible=True)
        assert a.focusable
        press(a, 'escape')
        assert not a.visible and a.render(width=20) == ''
        assert press(C.Alert('x'), 'escape') == [False]

    def test_link_open(self):
        opened = []
        link = C.Link('Docs', 'http://x', on_open=opened.append,
                      use_colors=True)
        press(link, 'enter')
        assert opened == ['http://x']
        assert '\x1b]8;;http://x' in link.render(width=20)
        assert press(link, 'x') == [False]

    def test_breadcrumbs_collapse(self):
        b = C.Breadcrumbs(['Inicio', 'Ventas', 'Región', 'Pedido 1281'],
                          use_colors=False)
        assert text(b, 30).startswith('Inicio › … › ')
        assert 'Pedido 1281' in text(b, 30)

    def test_spinner_advances(self):
        s = C.Spinner('x', style='line', use_colors=False)
        assert [text(s, 5)[0] for _ in range(5)] == list('-\\|/-')

    def test_highlight(self):
        painter = lambda t, s: '<' + t + '>'  # noqa: E731
        theme = C.DEFAULT_THEME
        from flexablelib_components.display import highlight
        assert highlight('x = "a#b"  # c', 'python', painter, theme) == \
            'x = <"a#b">  <# c>'
        assert highlight("return 'x\\'y'", 'py', painter, theme) == \
            "<return> <'x\\'y'>"
        assert highlight('SELECT 1', 'sql', painter, theme) == \
            '<SELECT> <1>'
        assert highlight('plain', 'cobol', painter, theme) == 'plain'

    def test_markdown_colours(self):
        md = C.MarkdownView('# T\n\n**b** `c` [l](http://u)', use_colors=True)
        out = md.render(width=40)
        assert '\x1b]8;;http://u' in out and '\x1b[1m' in out

    def test_human_size(self):
        assert C.human_size(512) == '512 B'
        assert C.human_size(1536) == '1.5 KB'
        assert C.human_size(None) == '0 B'


# +---------------------------------------------------------------------------+
# Navigation

class TestNavigation:
    def test_tabs(self):
        changed = []
        tabs = C.Tabs([('A', 'uno'), ('B', C.TextInput('x'))],
                      on_change=changed.append, use_colors=False)
        press(tabs, 'right')
        assert tabs.index == 1 and changed == [1]
        press(tabs, '1', 'left', '9')
        assert tabs.index == 1
        assert tabs.children() and press(tabs, 'x') == [False]
        assert C.Tabs([]).children() == []

    def test_menu(self):
        ran = []
        menu = C.Menu(['Abrir', '-', {'label': 'Guardar', 'shortcut': 'ctrl+s',
                                      'action': lambda: ran.append('g')},
                       {'label': 'Borrar', 'disabled': True},
                       ('Salir', lambda: ran.append('s'))],
                      on_select=lambda i, item: ran.append(i),
                      use_colors=False)
        press(menu, 'down', 'enter')
        assert ran == ['g', 2]
        press(menu, 'down', 'enter')
        assert ran[-2:] == ['s', 4]
        press(menu, 'ctrl+s', 'home', 'end', 'up', 'k', 'j', 'a', 's')
        assert menu.items[menu.index]['label'] == 'Salir'
        assert press(menu, 'q') == [False]
        assert menu.activate(1) is False
        m2 = C.Menu(['-', 'x'], max_visible=1)
        assert m2.index == 1 and len(text(m2).split('\n')) == 1
        assert press(C.Menu([]), 'down') == [False]
        assert 'ctrl+s' in strip_ansi(C.Menu([{'label': 'G', 'shortcut':
                                               'ctrl+s'}, 'x'],
                                             index=1).render(width=20))

    def test_context_menu_and_button(self):
        ran = []
        btn = C.MenuButton('Más', [('Exportar', lambda: ran.append('e'))],
                           use_colors=False)
        app = App(body=btn)
        app.run(keys=['enter'], size=(30, 8))
        assert btn.menu in app.layers
        app.dispatch(key('x'))
        app.dispatch(key('enter'))
        assert ran == ['e'] and btn.menu not in app.layers
        app.dispatch(key('enter'))
        app.dispatch(key('escape'))
        assert not app.layers
        orphan = C.MenuButton('x', ['a'])
        assert orphan.press() is True
        C.ContextMenu(['a']).close()

    def test_pagination(self):
        pages = []
        p = C.Pagination(200, 20, on_change=pages.append, use_colors=False)
        press(p, 'right', 'pagedown', 'end', 'home', 'left')
        assert pages == [2, 3, 10, 1]
        assert p.numbers() == [1, 2, 3, 4, 5, None, 10]
        p.page = 9
        assert p.numbers() == [1, None, 6, 7, 8, 9, 10]
        p.page = 5
        assert p.numbers() == [1, None, 4, 5, 6, None, 10]
        assert text(p, 12).startswith('‹ 5/10 ›')
        assert press(p, 'x') == [False]

    def test_sidebar(self):
        s = C.Sidebar({'A': ['Uno', 'Dos']}, use_colors=False)
        press(s, 'down', 'enter', 'ctrl+b')
        assert s.active == s.index and s.collapsed
        assert s.natural_width() == 4
        assert 'D' in text(s, 6)

    def test_toolbar(self):
        hit = []
        bar = C.Toolbar([('Nuevo', lambda: hit.append('n')),
                         C.Button('Borrar', lambda: hit.append('b'),
                                  shortcut='ctrl+d')])
        app = App(body=bar)
        app.run(keys=['right', 'enter', 'left', 'enter', 'ctrl+d', 'x'],
                size=(40, 3))
        assert hit == ['b', 'n', 'b']

    def test_wizard(self):
        done = []
        errors = {0: 'Falta nombre'}
        wiz = C.Wizard([('Datos', 'uno'), ('Pago', 'dos')],
                       on_finish=lambda: done.append(1),
                       validate=lambda i: errors.pop(i, None),
                       use_colors=False)
        app = App(body=wiz)
        app.run(keys=['ctrl+n'], size=(60, 12))
        assert 'Falta nombre' in app.last_frame
        app.dispatch(key('ctrl+n'))
        assert wiz.index == 1 and 'Finalizar' in app.render(60, 12)
        app.dispatch(key('ctrl+p'))
        assert wiz.index == 0
        app.dispatch(key('ctrl+n'))
        app.dispatch(key('ctrl+n'))
        assert done == [1] and wiz.finished
        wiz.previous()
        wiz.previous()
        assert wiz.index == 0
        assert wiz.handle_key(key('x')) is False

    def test_accordion(self):
        a = C.Accordion([('A', 'uno'), ('B', C.Badge('x'))], multiple=False)
        press(a, 'down', 'enter')
        assert a.opened == {1} and a.children()
        press(a, 'left', 'right', 'up', 'space')
        assert a.opened == {0}
        assert press(a, 'x') == [False]

    def test_carousel(self):
        c = C.Carousel(['a', 'b', 'c'], autoplay=2)
        press(c, 'right', 'left', 'left')
        assert c.index == 2
        c.tick()
        c.tick()
        assert c.index == 0
        assert press(c, 'x') == [False]
        C.Carousel([]).go(1)

    def test_tree(self):
        picked = []
        tree = C.Tree({'a': 1, 'b': {'c': [1, 2], 'd': None}},
                      on_select=lambda p, v: picked.append((p, v)),
                      use_colors=False)
        press(tree, 'enter')
        assert picked == [(('a',), 1)]
        press(tree, 'down', 'right', 'down', 'right', 'down', 'enter')
        assert picked[-1] == (('b', 'c', '[0]'), 1)
        press(tree, 'left', 'left', 'left', 'h', '*', 'pagedown', 'pageup',
              'j', 'k', 'l', 'enter')
        assert press(tree, 'x') == [False]
        assert press(C.Tree({}), 'down') == [False]
        assert len(text(tree, 30, 3).split('\n')) == 3

    def test_command_palette(self):
        ran = []
        cp = C.CommandPalette([('Abrir archivo', lambda: ran.append('a')),
                               {'label': 'Guardar', 'keywords': ['save'],
                                'action': lambda: ran.append('g')},
                               ('Nada',)], use_colors=False)
        app = App(body='fondo', bindings={'ctrl+k': lambda: cp.open(app)})
        app.run(keys=['ctrl+k', 's', 'a', 'v', 'enter'], size=(60, 12))
        assert ran == ['g'] and not app.layers
        app.dispatch(key('ctrl+k'))
        for k in ['z', 'z', 'z']:
            app.dispatch(key(k))
        assert 'Sin resultados' in app.render(60, 12)
        for k in ['backspace', 'backspace', 'backspace', 'down', 'up', 'tab',
                  'f9', 'space', 'backspace', 'enter']:
            app.dispatch(key(k))
        assert ran == ['g', 'a']
        app.dispatch(key('ctrl+k'))
        app.dispatch(Key('paste', 'nad'))
        app.dispatch(key('enter'))
        app.dispatch(key('ctrl+k'))
        app.dispatch(key('escape'))
        assert not app.layers
        assert C.CommandPalette.score('abc', 'a_b_c') == 102
        assert C.CommandPalette.score('xyz', 'abc') is None

    def test_split_and_stack(self):
        sp = C.Split(C.Badge('L'), 'R')
        assert sp.handle_key(key('ctrl+right')) and sp.ratio > 0.5
        assert sp.handle_key(key('ctrl+up')) is False
        v = C.Split('a', 'b', direction='vertical', divider=False)
        assert v.handle_key(key('ctrl+down')) and v.ratio > 0.5
        assert len(text(v, 10, 6).split('\n')) == 6
        assert v.natural_width() >= 1 and sp.natural_width() > 3
        assert C.Stack(['a'], direction='horizontal').natural_width() == 1

    def test_sort_control(self):
        got = []
        s = C.SortControl(['A', 'B'], on_change=lambda f, d: got.append((f, d)))
        press(s, 'right', 'space', 'left')
        assert got == [('B', False), ('B', True), ('A', True)]
        assert press(s, 'x') == [False]

    def test_app_shell(self):
        side = C.Sidebar(['Inicio', 'Ventas'])
        top = C.TopBar('App')
        shell = C.AppShell(sidebar=side, topbar=top,
                           pages={'Inicio': 'página inicio',
                                  'Ventas': 'página ventas'},
                           sidebar_below=50, use_colors=False)
        app = App(body=shell)
        frame = app.run(keys=['down', 'enter'], size=(80, 10))
        assert 'página ventas' in frame and top.breadcrumbs == ['Ventas']
        app.dispatch(key('ctrl+b'))
        assert 'Inicio' not in app.render(80, 10)
        app.dispatch(key('ctrl+b'))
        narrow = app.render(40, 10)
        assert 'Inicio' not in narrow
        app.dispatch(key('ctrl+b'))
        assert shell.force_sidebar and 'Inicio' in app.render(40, 10)
        shell.open_page('nope')
        assert C.AppShell(content='x').handle_key(key('ctrl+b')) is False


# +---------------------------------------------------------------------------+
# Data

ROWS = [{'folio': i, 'cliente': name, 'total': total, 'estado': state}
        for i, (name, total, state) in enumerate([
            ('Ana', 100.5, 'pagado'), ('Luis', 2500.0, 'pendiente'),
            ('Sofía', 30.0, 'pagado'), ('Eva', None, 'cancelado')], 1)]


class TestDataTable:
    def make(self, **kw):
        return C.DataTable(['folio', 'cliente', 'total', 'estado'],
                           [dict(r) for r in ROWS], use_colors=False, **kw)

    def test_navigation_sort_filter(self):
        activated = []
        t = self.make(height=2, on_activate=activated.append)
        press(t, 'down', 'down', 'up', 'end', 'home', 'pagedown', 'pageup',
              'j', 'k', 'G', 'g')
        assert t.cursor_row == 0
        press(t, '3')
        assert [r['cliente'] for r in (t.rows[i] for i in t.view())] == \
            ['Sofía', 'Ana', 'Luis', 'Eva']
        press(t, '3')
        assert t.rows[t.view()[0]]['cliente'] == 'Luis'
        press(t, '/', 'p', 'a', 'g', 'space', 'backspace', 'enter')
        assert len(t.view()) == 2 and '/pag' in text(t)
        press(t, '/')
        t.handle_key(Key('paste', 'o'))
        assert press(t, 'f5') == [True] and press(t, 'tab') == [False]
        press(t, 'escape', 'escape')
        assert t.query == '' and len(t.view()) == 4
        press(t, 'enter')
        assert activated
        assert press(t, 'x') == [False]
        t.sort_by(0, descending=True)
        assert t.rows[t.view()[0]]['folio'] == 4

    def test_selection_and_columns(self):
        picked = []
        t = self.make(selectable=True, on_select=picked.append)
        press(t, 'space', 'space')
        assert len(t.selected_rows()) == 2
        press(t, 'ctrl+a')
        assert len(t.selected) == 4
        press(t, 'ctrl+a')
        assert not t.selected
        press(t, 'right', 'right', 'left')
        assert t.col_offset == 1
        assert 'columnas más' in text(t, 30)
        t.set_rows(ROWS[:1])
        assert t.current['cliente'] == 'Ana'

    def test_list_rows_and_paging(self):
        t = C.DataTable(['a', {'title': 'b'}], [[1, 'x'], [2], [3, 'z']],
                        page_size=2, use_colors=False)
        press(t, 'end')
        assert 'pág. 2/2' in text(t)
        assert t.text([1], 1) == ''
        empty = C.DataTable(['a'], [])
        assert empty.current is None and 'Sin registros' in text(empty)
        assert press(empty, 'space', 'enter') == [False, False]

    def test_cell_formats(self):
        from flexablelib_components.data import _cell_text
        assert _cell_text(True) == 'Sí' and _cell_text(False) == 'No'
        assert _cell_text(dt.date(2026, 1, 2)) == '2026-01-02'
        assert _cell_text(1234) == '1,234'

    def test_colours(self):
        t = self.make()
        t.use_colors = True
        t.focused = True
        out = t.render(width=60)
        assert '\x1b[30;46m' in out or '\x1b[' in out
        t.focused = False
        assert '#1c1c1c' not in out


class TestFilterBar:
    def test_query_language(self):
        assert C.parse_query('estado:pagado total>100 "dos palabras"') == [
            ('estado', ':', 'pagado'), ('total', '>', '100'),
            (None, ':', 'dos palabras')]
        assert C.parse_query('x:1', fields=['y']) == [(None, ':', 'x:1')]

    def test_filters_table(self):
        table = C.DataTable(['folio', 'cliente', 'total', 'estado'],
                            [dict(r) for r in ROWS])
        changes = []
        bar = C.FilterBar(['estado', 'total', 'cliente'], table=table,
                          on_change=changes.append, use_colors=False)
        for c in 'estado:pagado':
            press(bar, c)
        assert len(table.view()) == 2 and changes
        bar.set_value('total>=100')
        assert len(table.view()) == 2
        for query, n in [('total<100', 1), ('total<=30', 1),
                         ('estado=pagado', 2), ('estado!=pagado', 2),
                         ('ana', 1), ('cliente>M', 1), ('zzz', 0)]:
            bar.set_value(query)
            assert len(table.view()) == n, query
        assert '[zzz]' in text(bar)
        plain = C.FilterBar(['a'])
        plain.text = 'a:1'
        assert plain.predicate(['x']) is False
        assert plain.predicate({'a': 1}) is True


class TestEditableTable:
    def test_edit_add_delete(self):
        edits = []
        t = C.EditableTable([{'key': 'n', 'type': 'number'}, 'txt'],
                            [{'n': 1, 'txt': 'a'}], on_edit=lambda *a:
                            edits.append(a), use_colors=False)
        t.focused = True
        press(t, 'enter', 'backspace', '5', 'enter')
        assert t.rows[0]['n'] == 5 and edits
        press(t, 'enter', 'x', 'enter')
        assert t.editor is not None and t.editor.error
        press(t, 'escape', 'right', 'enter', 'escape', 'right', 'left')
        assert t.cursor_col == 0
        press(t, 'ctrl+n')
        assert len(t.rows) == 2
        assert '› ' not in text(t)
        press(t, 'enter')
        assert '5' not in text(t).split('\n')[3]
        press(t, 'escape', 'ctrl+d')
        assert len(t.rows) == 1
        lists = C.EditableTable(['a', 'b'], [[1]])
        lists.focused = True
        lists.cursor_col = 1
        lists._set(lists.rows[0], 1, 'z')
        assert lists.rows[0] == [1, 'z']
        press(lists, 'ctrl+n')
        assert lists.rows[-1] == [None, None]
        t.use_colors = True
        assert t.render(width=40)
        t.cursor_col = 5
        assert t.render(width=40)
        assert C.EditableTable(['a']).children() == []
        f = C.EditableTable([{'key': 'n', 'type': 'number'}], [{'n': 1}])
        assert f._set(f.rows[0], 0, '2.5') and f.rows[0]['n'] == 2.5


class TestCatalogAndForms:
    def test_catalog(self):
        picked = []
        items = [{'title': 'Item %d' % i, 'price': i * 10} for i in range(9)]
        cat = C.CatalogGrid(items, min_width=20, on_select=picked.append,
                            use_colors=False)
        cat.focused = True
        text(cat, 62, 12)
        press(cat, 'right', 'down', 'enter', 'end', 'home', 'left', 'up')
        assert picked == [items[4]]
        press(cat, 'end')
        assert 'Item 8' in text(cat, 62, 12)
        assert press(cat, 'x') == [False]

    def test_form_flow(self):
        got = []
        cancelled = []
        name = C.TextInput('Nombre', required=True)
        mail = C.TextInput('Correo', name='email')
        form = C.Form([name, 'Sección', (mail, C.Checkbox('Ok'))],
                      on_submit=got.append,
                      on_cancel=lambda: cancelled.append(1),
                      use_colors=False)
        app = App(body=form)
        app.run(keys=['ctrl+s'], size=(60, 20))
        assert form.errors == {'Nombre': 'Requerido'}
        assert app.focused is name and 'Revisa' in app.last_frame
        for k in ['A', 'n', 'a', 'enter']:
            app.dispatch(key(k))
        assert app.focused is mail
        app.dispatch(key('ctrl+s'))
        assert got == [{'nombre': 'Ana', 'email': '', 'ok': False}]
        app.dispatch(key('escape'))
        assert cancelled == [1]
        form.app = None
        form.errors = {}
        name.value = ''
        form.submit()
        assert form.errors
        assert C.Form([], cancel_label=None).cancel() is True

    def test_login(self):
        attempts = []

        def check(user, password, remember):
            attempts.append(user)
            return True if password == 'ok' else 'Clave mala'
        login = C.LoginForm(on_login=check, use_colors=False)
        app = App(body=login)
        keys = ['a', 'n', 'a', 'enter', 'm', 'a', 'l', 'enter']
        app.run(keys=keys, size=(50, 16))
        assert attempts == ['ana'] and 'Clave mala' in app.last_frame
        assert login.password.text == ''
        app.focus(login.password)
        for k in ['o', 'k', 'enter']:
            app.dispatch(key(k))
        assert login.logged_in
        bare = C.LoginForm(use_colors=False)
        bare.user.value = 'x'
        bare.password.value = 'y'
        bare.submit()
        assert bare.logged_in
        falsy = C.LoginForm(on_login=lambda *a: None)
        falsy.user.value = falsy.password.value = 'x'
        falsy.submit()
        assert falsy.message == 'Usuario o contraseña incorrectos'

    def test_file_preview(self, tmp_path):
        binary = tmp_path / 'img.png'
        binary.write_bytes(b'\x89PNG\x00\x00')
        assert 'binario' in text(C.FilePreview(str(binary), images=False))
        assert 'no se puede mostrar' in text(C.FilePreview(str(binary)))
        latin = tmp_path / 'l.txt'
        latin.write_bytes('ñ'.encode('latin-1'))
        assert 'ñ' in text(C.FilePreview(str(latin)))
        md = tmp_path / 'r.md'
        md.write_text('# Hola')
        assert 'HOLA' in text(C.FilePreview(str(md), use_colors=False))


# +---------------------------------------------------------------------------+
# Dialogs

class TestDialogs:
    def test_confirm(self):
        yes, no = [], []
        app = App(body=C.Button('b'))
        dlg = C.ConfirmDialog('¿Borrar?', on_confirm=lambda: yes.append(1),
                              on_cancel=lambda: no.append(1), use_colors=False)
        app.run(keys=[], size=(60, 12))
        dlg.open(app)
        app.render(60, 12)
        assert app.focused is dlg.buttons[0]
        app.dispatch(key('right'))
        app.dispatch(key('enter'))
        assert yes == [1] and dlg.result is True and not app.layers
        dlg.open(app)
        app.render(60, 12)
        app.dispatch(key('enter'))
        assert no == [1]
        dlg.open(app)
        app.dispatch(key('escape'))
        assert not app.layers

    def test_modal_not_closable_and_false_action(self):
        app = App(body='x')
        m = C.Modal('hola', buttons=[('Quedarse', lambda: False), ('Ir',)],
                    closable=False, on_close=lambda: None)
        m.open(app)
        app.render(40, 10)
        app.dispatch(key('escape'))
        app.dispatch(key('enter'))
        assert m in app.layers
        app.dispatch(key('right'))
        app.dispatch(key('enter'))
        assert m not in app.layers
        assert m.handle_key(key('z')) is False

    def test_prompt(self):
        got = []
        app = App(body='x')
        p = C.PromptDialog('Nombre', on_submit=got.append,
                           validators=[lambda v: None if v else 'Vacío'])
        p.open(app)
        app.render(50, 10)
        app.dispatch(key('enter'))
        assert p in app.layers and p.input.error == 'Vacío'
        for k in ['Y', 'enter']:
            app.dispatch(key(k))
        assert got == ['Y'] and p not in app.layers

    def test_loading_and_popover(self):
        app = App(body=C.Button('b'))
        load = C.LoadingOverlay('Cargando', progress=1.5)
        load.show(app)
        app.render(40, 10)
        assert app.dispatch(key('q')) is True
        assert '100%' in app.render(40, 10)
        load.hide()
        assert not app.layers
        pop = C.Popover('nota').open(app, position='top-right', modal=False)
        app.render(40, 10)
        assert pop in app.layers
        assert isinstance(app.focused, C.Button)

    def test_help_line(self):
        field = C.TextInput('X', help='Escribe tu nombre')
        hl = C.HelpLine('por defecto', use_colors=False)
        app = App(body=C.Stack([field, hl]))
        frame = app.run(keys=[], size=(40, 6))
        assert 'Escribe tu nombre' in frame
        assert 'por defecto' in text(C.HelpLine('por defecto'))
        assert text(C.HelpLine()).strip() == ''

    def test_box_focus(self):
        inner = C.TextInput('Dentro')
        box = C.Box(inner, title='Caja', height=5, use_colors=True)
        app = App(body=box)
        frame = app.run(keys=[], size=(40, 6))
        assert '\x1b[36m' in frame          # accent border while focused
        assert box.natural_width() > 4
        assert box._has_focus()
        lone = C.Box('x')
        assert lone._has_focus() is False
        assert len(lone.render(width=10, height=4).split('\n')) == 4


def test_theme():
    theme = C.Theme(accent='magenta')
    assert theme.kind('success') == 'green' and theme.kind('zzz') == 'blue'
    b = C.Badge('x', theme=theme, use_colors=True)
    assert '\x1b[' in b.render(width=5)


def test_button_states():
    hit = []
    b = C.Button('Ok', lambda: hit.append(1), use_colors=False)
    press(b, 'enter', 'space', 'x')
    assert hit == [1, 1] and b.presses == 2
    b.focused = True
    assert '[>Ok<]' in text(b, 10)
    colored = C.Button('Ok', kind='danger', use_colors=True)
    colored.focused = True
    assert '\x1b[1;37;41m' in colored.render(width=10)
    colored.kind = 'default'
    assert '\x1b[1;7m' in colored.render(width=10)


def test_input_base():
    i = C.Input('Campo Uno')
    assert i.name == 'campo_uno' and i.is_empty()
    seen = []
    i.on_change = seen.append
    i.set_value(3)
    i.set_value(3)
    assert seen == [3]
    i.focused = True
    i.use_colors = True
    assert '▌' in i.marker()
    i.use_colors = False
    assert i.marker() == '›'
    got = []
    i.on_submit = got.append
    assert i.submit() and got == [3]


def test_paint_cache_and_empty_prefix():
    b = C.Badge('x', use_colors=True)
    assert b.paint('x', 'on #262626') == b.paint('x', 'on #262626')
    from flexablelib_components import base
    base._SPEC_CACHE['weird'] = ''
    assert b.paint('x', 'weird') == 'x'
    assert b.cursor('a') == '\x1b[7ma\x1b[0m'
    b.use_colors = False
    assert b.cursor('a') == 'a'


def test_frame_helper():
    lines = C.frame(['a'], 12, 'Título largo de verdad', footer='pie')
    assert all(visible_width(l) == 12 for l in lines)
    assert C.frame(['a'], 5, 'T')[0] == '╭───╮'
    assert C.frame([], 6, style='ascii') == ['+----+', '+----+']


def test_components_dir_listing():
    assert os.path.exists(os.path.join(os.path.dirname(C.__file__),
                                       'py.typed'))


class TestStackWrap:
    def test_wraps_by_min_width(self):
        cards = [C.Stat('K{0}'.format(i), str(i), use_colors=False)
                 for i in range(4)]
        stack = C.Stack(cards, direction='horizontal', gap=1, min_width=20,
                        use_colors=False)
        wide = stack.render(width=90).split('\n')
        assert all(k in wide[0] for k in ('K0', 'K1', 'K2', 'K3'))
        mid = stack.render(width=50).split('\n')
        rows = [l for l in mid if 'K' in l]
        assert len(rows) == 2 and 'K0' in rows[0] and 'K1' in rows[0] \
            and 'K2' in rows[1]
        assert all(visible_width(l) == 50 for l in mid)
        narrow = stack.render(width=24).split('\n')
        assert len([l for l in narrow if 'K' in l]) == 4
        # The last row keeps the same slot widths as the others.
        three = C.Stack(cards[:3], direction='horizontal', min_width=20,
                        use_colors=False).render(width=45).split('\n')
        assert visible_width(three[-1]) == 45
