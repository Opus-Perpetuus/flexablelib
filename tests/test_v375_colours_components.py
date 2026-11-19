"""3.7.5: components follow FORCE_COLOR, the TUI ignores an empty NO_COLOR,
and the default theme's message colours reach WCAG AA (4.5:1)."""

import pytest

C = pytest.importorskip('flexablelib_components')
from flexablelib_components.base import THEMES  # noqa: E402
from flexablelib_tui import capabilities  # noqa: E402
from flexablelib_tui.accessibility import contrast_ratio, spec_colors  # noqa: E402


def test_tui_color_level_ignores_empty_no_color():
    assert capabilities.color_level({'NO_COLOR': '', 'TERM': 'xterm'},
                                    tty=True) == '16'
    assert capabilities.color_level({'NO_COLOR': '0'}, tty=True) == 'none'


def test_component_paint_cache_follows_depth(monkeypatch):
    badge = C.Badge('x', use_colors=True)
    monkeypatch.setenv('FORCE_COLOR', '3')
    assert '48;2;38;38;38' in badge.paint('x', 'on #262626')
    monkeypatch.setenv('FORCE_COLOR', '2')
    assert '48;5;235' in badge.paint('x', 'on #262626')
    monkeypatch.setenv('FORCE_COLOR', '1')
    assert '\x1b[40m' in badge.paint('x', 'on #262626')


def test_default_theme_messages_reach_wcag_aa():
    ratios = C.Theme.preset('default').contrast()
    for role in ('info', 'success', 'warning', 'error', 'accent', 'muted'):
        assert ratios[role] >= 4.5, (role, ratios[role])


@pytest.mark.parametrize('name', sorted(THEMES))
def test_danger_button_text_reads_on_error_colour(name):
    theme = C.Theme.preset(name)
    button = C.Button('Borrar', kind='danger', theme=theme)
    fg, bg, _ = spec_colors(button.style())
    if bg is None:
        return
    assert contrast_ratio(fg, bg) >= 4.5
