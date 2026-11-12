"""
3.3.0 layout and packaging: explicit grid placement, closed gaps in bordered
grids, merged cells in to_cards, the optional-package shims and lazy names.
"""

import importlib
import sys
import warnings

import pytest

import flexablelib
from flexablelib import Grid, GridCell, Table
from flexablelib import layout
from flexablelib.box_topology import check_topology
from flexablelib.text_width import visible_width


def render(grid, width=40):
    return grid.render(width=width).split('\n')


class TestPlacement:
    def test_row_and_column(self):
        g = Grid([GridCell('pin', row=1, column=2), 'a', 'b'], columns=3)
        lines = render(g, 30)
        assert lines[0].startswith('a')
        assert 'b' in lines[0]
        assert 'pin' in lines[-1]
        assert lines[-1].index('pin') >= 20

    def test_row_only_and_column_only(self):
        g = Grid([GridCell('R', row=1), GridCell('C', column=1), 'x'],
                 columns=2)
        lines = render(g, 20)
        assert lines[0].split() == ['x', 'C']
        assert lines[-1].split() == ['R']

    def test_column_only_takes_first_free_row(self):
        g = Grid([GridCell('A', column=0), GridCell('B', column=0)],
                 columns=2)
        lines = render(g, 20)
        assert lines[0].split() == ['A']
        assert lines[-1].split() == ['B']

    def test_overlap_raises(self):
        g = Grid([GridCell('a', row=0, column=0),
                  GridCell('b', row=0, column=0)], columns=2)
        with pytest.raises(ValueError):
            g.render(width=20)

    def test_pin_wider_than_columns_flows(self):
        g = Grid([GridCell('wide', row=0, column=3), 'b'], columns=2)
        lines = render(g, 20)
        assert 'wide' in lines[0]

    def test_spans_respect_pins(self):
        g = Grid([GridCell('pin', row=0, column=1), GridCell('wide', span=2),
                  'c'], columns=3)
        lines = render(g, 30)
        assert 'pin' in lines[0]
        assert 'wide' in ''.join(lines)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            GridCell('x', row=-1)
        with pytest.raises(ValueError):
            GridCell('x', column=-2)


class TestClosedGaps:
    def test_bordered_grid_closes_missing_slot(self):
        g = Grid(['a', 'b', 'c', 'd'], columns=3, border=True,
                 use_colors=False)
        lines = render(g, 32)
        assert check_topology(lines) == []
        assert all(visible_width(l) == 32 for l in lines)
        assert lines[-1].count('┴') == 1
        assert lines[-1].startswith('└') and lines[-1].endswith('┘')

    def test_fill_gaps_off_keeps_open_frame(self):
        g = Grid(['a', 'b', 'c', 'd'], columns=3, border=True,
                 use_colors=False, fill_gaps=False)
        closed = Grid(['a', 'b', 'c', 'd'], columns=3, border=True,
                      use_colors=False)
        assert render(g, 32) != render(closed, 32)

    def test_pinned_hole_in_middle(self):
        g = Grid(['a', GridCell('z', row=1, column=2)], columns=3,
                 border=True, use_colors=False)
        lines = render(g, 31)
        assert check_topology(lines) == []
        assert all(visible_width(l) == 31 for l in lines)

    def test_pinned_title(self):
        g = Grid([GridCell('x', row=1, column=1, title='Pin'), 'a'],
                 columns=2, border=True, use_colors=False)
        lines = render(g, 30)
        assert '┼─ Pin ─' in lines[2]
        assert all(visible_width(l) == 30 for l in lines)


class TestCardsWithMerges:
    def table(self):
        t = Table(headers=['Región', 'Tienda', 'Q1', 'Q2'])
        for row in [['Norte', 'MTY', 1, 2], ['Norte', 'SLT', 3, 4],
                    ['Sur', 'MID', 5, 6]]:
            t.add_row(row)
        t.use_colors = False
        return t

    def test_vertical_merge_repeats_value(self):
        t = self.table()
        t.merge_cells(0, 0, last_row=1)
        cards = t.to_cards()
        assert [c.title for c in cards] == ['Norte', 'Norte', 'Sur']

    def test_horizontal_merge_joins_labels(self):
        t = self.table()
        t.merge_cells(2, 2, last_column=3, value='cerrado')
        text = t.to_cards()[2].render(width=30)
        assert 'Q1 · Q2' in text
        assert 'cerrado' in text
        assert 'Q2 ' not in text.replace('Q1 · Q2', '')

    def test_unmerged_rows_unchanged(self):
        t = self.table()
        t.merge_cells(2, 2, last_column=3, value='cerrado')
        first = t.to_cards()[0].render(width=30)
        assert 'Q1' in first and 'Q2' in first and 'cerrado' not in first

    def test_merge_without_value_uses_top_left(self):
        t = self.table()
        t.merge_cells(0, 2, last_row=1)
        texts = [c.render(width=30) for c in t.to_cards()]
        assert '1' in texts[1].split('Q1')[1].split('\n')[0]


class TestAcceptsHeightCache:
    def test_cached_per_class(self):
        class W(object):
            def render(self, width=None, height=None):
                return ''
        layout._ACCEPTS_HEIGHT.pop(W, None)
        assert layout._accepts_height(W()) is True
        assert layout._ACCEPTS_HEIGHT[W] is True
        assert layout._accepts_height(W()) is True

    def test_instance_override_not_cached(self):
        class W(object):
            def render(self, width=None):
                return ''
        w = W()
        w.render = lambda width=None, height=None: ''
        assert layout._accepts_height(w) is True
        assert W not in layout._ACCEPTS_HEIGHT

    def test_kwargs(self):
        class W(object):
            def render(self, **kw):
                return ''
        assert layout._accepts_height(W()) is True


class TestPackaging:
    def test_lazy_compat_names(self):
        assert flexablelib.ProgressBar.__name__ == 'ProgressBar'
        assert flexablelib.Live.__name__ == 'Live'

    def test_tui_names(self):
        pytest.importorskip('flexablelib_tui')
        assert flexablelib.App.__module__ == 'flexablelib_tui.app'
        assert 'App' in dir(flexablelib)

    def test_component_names(self):
        pytest.importorskip('flexablelib_components')
        assert flexablelib.DataTable.__name__ == 'DataTable'

    def test_unknown_attribute(self):
        with pytest.raises(AttributeError):
            flexablelib.NoSuchThing
        with pytest.raises(AttributeError):
            flexablelib.lowercase_missing

    def test_missing_tui_message(self, monkeypatch):
        monkeypatch.setitem(sys.modules, 'flexablelib_tui', None)
        with pytest.raises(ImportError, match=r'flexablelib\[tui\]'):
            flexablelib.App

    def test_missing_components_is_attribute_error(self, monkeypatch):
        monkeypatch.setitem(sys.modules, 'flexablelib_components', None)
        with pytest.raises(AttributeError):
            flexablelib.DataTable

    def test_inner_import_error_propagates(self, monkeypatch):
        import importlib as il

        def boom(name, *a, **k):
            error = ImportError('inner')
            error.name = 'something_else'
            raise error
        monkeypatch.setattr(il, 'import_module', boom)
        with pytest.raises(ImportError, match='inner'):
            flexablelib._optional('flexablelib_tui', 'tui')

    def test_star_import(self):
        namespace = {}
        exec('from flexablelib import *', namespace)
        assert 'Screen' in namespace and 'Grid' in namespace

    def test_legacy_fallback_warns(self, monkeypatch):
        for name in ('flexablelib.widgets', 'flexablelib.screen'):
            monkeypatch.delitem(sys.modules, name, raising=False)
        monkeypatch.setitem(sys.modules, 'flexablelib_tui', None)
        monkeypatch.delattr(flexablelib, 'widgets', raising=False)
        monkeypatch.delattr(flexablelib, 'screen', raising=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            widgets = importlib.import_module('flexablelib.widgets')
            screen = importlib.import_module('flexablelib.screen')
        assert widgets.__name__ == 'flexablelib._legacy.widgets'
        assert screen.__name__ == 'flexablelib._legacy.screen'
        assert any('flexablelib[tui]' in str(w.message) for w in caught)
        assert widgets.ProgressBar(50, use_colors=False).render(width=20)
        monkeypatch.undo()
        for name in ('flexablelib.widgets', 'flexablelib.screen'):
            sys.modules.pop(name, None)
        importlib.import_module('flexablelib.widgets')
        importlib.import_module('flexablelib.screen')

    def test_shim_is_tui_module(self):
        pytest.importorskip('flexablelib_tui')
        import flexablelib.widgets as w
        import flexablelib_tui.widgets as tw
        assert w is tw

    def test_versions_in_lockstep(self):
        import json
        import os
        import re
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'package.json')) as f:
            version = json.load(f)['version']
        for pkg, mod in (('tui', 'flexablelib_tui'),
                         ('components', 'flexablelib_components'),
                         ('speedups', 'flexablelib_speedups')):
            path = os.path.join(root, 'packages', pkg, mod, '__init__.py')
            with open(path) as f:
                found = re.search(r"__version__ = '([^']+)'", f.read())
            assert found.group(1) == version, pkg

    def test_width_tables_in_sync(self):
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        a = open(os.path.join(root, 'flexablelib', '_width_tables.h')).read()
        b = open(os.path.join(root, 'packages', 'speedups',
                              'flexablelib_speedups',
                              '_width_tables.h')).read()
        assert a == b
