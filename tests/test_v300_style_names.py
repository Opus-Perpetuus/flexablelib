"""
3.0.0 renamed every border style so the name describes the look. The old
names keep working for now, translated with a DeprecationWarning.
"""

import warnings

import pytest

from flexablelib import Table
from flexablelib.options import DEFAULT_STYLE
from flexablelib.style_compositions import DEPRECATED_STYLE_NAMES

ALL_STYLES = Table().possible_styles


def render(style_name):
    table = Table(rows=[['a', 1], ['b', 22]], headers=['n', 'q'])
    table.use_colors = False
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        table.style_name = style_name
    return str(table)


def test_every_old_name_points_at_a_current_style():
    for old, new in DEPRECATED_STYLE_NAMES.items():
        assert new in ALL_STYLES, (old, new)


def test_no_old_name_is_still_a_current_style():
    assert not set(DEPRECATED_STYLE_NAMES) & set(ALL_STYLES)


def test_the_default_style_is_a_current_name():
    assert DEFAULT_STYLE in ALL_STYLES
    assert Table().style_name == 'ascii_double_underline_open_header'


@pytest.mark.parametrize('old, new', sorted(DEPRECATED_STYLE_NAMES.items()))
def test_the_setter_translates_an_old_name_and_warns(old, new):
    table = Table()
    with pytest.warns(DeprecationWarning, match=new):
        table.style_name = old
    assert table.style_name == new


@pytest.mark.parametrize('old, new', sorted(DEPRECATED_STYLE_NAMES.items()))
def test_an_old_name_renders_exactly_like_the_new_one(old, new):
    assert render(old) == render(new)


def test_the_constructor_translates_an_old_name_and_warns():
    with pytest.warns(DeprecationWarning, match="'pretty_grid' was renamed to 'double_horizontal_rows'"):
        table = Table(style_name='pretty_grid')
    assert table.style_name == 'double_horizontal_rows'


def test_the_warning_points_at_the_caller():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        Table().style_name = 'grid'
    assert caught and caught[0].filename == __file__


@pytest.mark.parametrize('name', ['rounded', 'markdown', 'psql', 'single', 'nope', ''])
def test_current_and_unknown_names_do_not_warn(name):
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        Table().style_name = name


def test_unhashable_style_name_falls_back_to_the_default():
    table = Table()
    table.style_name = ['grid']
    assert table.style_name == DEFAULT_STYLE


def test_style_names_are_lowercase_snake_case_words():
    for name in ALL_STYLES:
        assert name == name.lower() and ' ' not in name and '__' not in name
