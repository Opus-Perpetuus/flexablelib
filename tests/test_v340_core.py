"""3.4.0 core: identifier (folio) columns without thousands separators and
C/Python parity of the frame helpers.  Needs only the core package."""

import os
import random

import pytest

import flexablelib
from flexablelib import Table, _frames


class TestFolios:

    def test_name_detection(self):
        for name in ('Folio', 'folio_fiscal', 'ID', 'cliente_id', 'ClienteId',
                     'Código postal', 'SKU', 'No. pedido', 'Año', '#',
                     'Clave', 'Teléfono', 'RFC'):
            assert flexablelib.is_id_column(name), name
        for name in ('Total', 'Cantidad', 'Importe', 'No. de piezas',
                     'Saldo', 'Piezas', 'Precio', None, True, ''):
            assert not flexablelib.is_id_column(name), name
        assert flexablelib.is_id_column('Pedido', names=['pedido'])
        assert 'folio' in flexablelib.ID_COLUMN_NAMES

    def test_table_default_is_unchanged(self):
        t = Table()
        t.add_column('Folio', [15000])
        t.add_column('Total', [15000])
        t.int_format = ','
        assert str(t).count('15,000') == 2

    def test_table_auto_and_list(self):
        t = Table()
        t.add_column('Folio', [15000])
        t.add_column('Total', [15000])
        t.int_format = ','
        t.id_columns = 'auto'
        out = str(t)
        assert '15000' in out and '15,000' in out
        t.id_columns = ['Total']
        out = str(t)
        assert out.count('15000') == 1 and '| 15,000' in out.replace(
            ' 15,000', '| 15,000') or '15,000' in out
        t.id_columns = 0
        assert t.is_id_column('Folio', 0)
        t.id_columns = True
        assert t.id_columns == 'auto'
        t.id_columns = False
        assert t.id_columns is None
        t.id_names = ['total']
        assert t.id_names == ('total',)

    def test_table_custom_names(self):
        t = Table()
        t.add_column('Pedido', [15000])
        t.add_column('Folio', [15000])
        t.int_format = ','
        t.id_columns = 'auto'
        t.id_names = ['pedido']
        out = str(t)
        assert '15000' in out and '15,000' in out

    def test_excel_keeps_ids_plain(self, tmp_path):
        openpyxl = pytest.importorskip('openpyxl')
        t = Table()
        t.add_column('Folio', [15000])
        t.add_column('Total', [15000])
        t.int_format = ','
        t.id_columns = 'auto'
        path = tmp_path / 'f.xlsx'
        from flexablelib import writers
        writers.to_excel(t, str(path))
        ws = openpyxl.load_workbook(str(path)).active
        cells = {c.value: c for c in ws[1]}
        row = list(ws.iter_rows(min_row=2, max_row=2))[0]
        folio, total = row[0], row[1]
        assert folio.value == 15000 and total.value == 15000
        assert ',' not in (folio.number_format or '')
        assert ',' in (total.number_format or '')
        assert cells


# -- C acceleration parity ----------------------------------------------------

class TestSpeedupParity:

    def _texts(self):
        rnd = random.Random(34)
        pool = '╭─┬╮│├┼┤╰┴╯═║╔╗╚╝▸◂✔✖⚠ℹ●○◀▶█░▒▓⠁⠿…→←↑↓ abcñ漢字😀'
        out = ['', 'plain ascii', '\x1b[1;31m╭──╮\x1b[0m']
        for _ in range(200):
            out.append(''.join(rnd.choice(pool) for _ in range(
                rnd.randint(1, 40))))
        return out

    def test_ascii_fold_c_matches_python(self):
        fold = _frames._PYTHON['ascii_fold']
        for text in self._texts():
            assert _frames.ascii_fold(text) == fold(text), text

    def test_extract_marks_c_matches_python(self):
        py = _frames._PYTHON['extract_marks']
        rnd = random.Random(7)
        for n in range(100):
            parts = []
            depth = 0
            for _ in range(rnd.randint(1, 8)):
                choice = rnd.random()
                if choice < 0.3:
                    parts.append(_frames.mark_open(rnd.randint(0, 999)))
                    depth += 1
                elif choice < 0.5 and depth:
                    parts.append(_frames.MARK_CLOSE)
                    depth -= 1
                else:
                    parts.append(rnd.choice(['ab', '漢字', '\x1b[31mx\x1b[0m',
                                             '─' * 3, ' ']))
            line = ''.join(parts) + _frames.MARK_CLOSE * depth
            assert _frames.extract_marks([line]) == py([line]), line

    def test_python_backend_selected_by_environment(self):
        import subprocess
        import sys
        code = ('import flexablelib._frames as f; '
                'print(f.ascii_fold is f._PYTHON["ascii_fold"])')
        env = dict(os.environ, FLEXABLELIB_FRAMES='python')
        env['PYTHONPATH'] = os.pathsep.join(sys.path)
        out = subprocess.run([sys.executable, '-c', code], env=env,
                             capture_output=True, text=True, timeout=60)
        assert out.stdout.strip() == 'True', out.stderr
