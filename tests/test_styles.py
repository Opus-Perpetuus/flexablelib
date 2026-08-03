"""
The style catalogue (``style_compositions.py``).

Styles are data, not code: 42 ``TableComposition`` namedtuples. Nothing in the
package validates them, so a malformed entry only shows up when a table is
rendered with it. The smoke test below renders the same table in every style
and checks the data survived.
"""

import os

import pytest

from helpers import REPO_ROOT
from prettyTables import Table
from prettyTables.options import DEFAULT_STYLE
from prettyTables.style_compositions import SeparatorLine, TableComposition

ALL_STYLES = Table().possible_styles

CELL_VALUES = ('Jade', 'John', '20', '30', '9.651', '245.7')


def build_table(style_name):
    table = Table(style_name=style_name)
    table.add_column('Name', ['Jade', 'John'])
    table.add_column('Age', [20, 30])
    table.add_column('Results', [9.651, 245.7])
    return table


# +-------------------------------------------------------------------------+
# The catalogue itself
# +-------------------------------------------------------------------------+

def test_the_catalogue_holds_42_styles():
    # A canary: adding a style is meant to be purely additive, and the README,
    # ARCHITECTURE.md and style_examples.md all quote this number.
    assert len(ALL_STYLES) == 42


def test_style_names_are_unique():
    assert len(set(ALL_STYLES)) == len(ALL_STYLES)


def test_the_default_style_is_in_the_catalogue():
    assert DEFAULT_STYLE in ALL_STYLES


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_declares_the_fields_the_renderer_dereferences(style_name):
    """
    Two fields are read unconditionally on every render:
    ``__get_string_table_width`` dereferences ``vertical_table_body_lines``'s
    four characters, and both the width sum and the cell padding multiply by
    ``margin``. A style missing either crashes rather than rendering badly.
    """
    composition = Table(style_name=style_name).style_composition

    assert isinstance(composition, TableComposition)
    assert isinstance(composition.margin, int)
    assert isinstance(composition.vertical_table_body_lines, SeparatorLine)
    assert isinstance(composition.vertical_header_lines, SeparatorLine)


# +-------------------------------------------------------------------------+
# Rendering smoke test
# +-------------------------------------------------------------------------+

@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_renders_without_raising(style_name):
    rendered = str(build_table(style_name))

    assert isinstance(rendered, str)
    assert rendered != ''


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_keeps_all_the_data(style_name):
    # The terminal is wide (conftest default), so nothing is wrapped or
    # trimmed and every cell must appear verbatim.
    rendered = str(build_table(style_name))

    for value in CELL_VALUES:
        assert value in rendered, f'{value!r} missing from style {style_name!r}'


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_keeps_the_headers(style_name):
    rendered = str(build_table(style_name))

    for header in ('Name', 'Age', 'Results'):
        assert header in rendered


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_aligns_the_float_column_on_the_decimal_point(style_name):
    rendered = str(build_table(style_name))
    lines_with_points = [
        line for line in rendered.splitlines()
        if '9.651' in line or '245.7' in line
    ]

    assert len(lines_with_points) == 2
    assert lines_with_points[0].index('.') == lines_with_points[1].index('.')


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_renders_with_the_headers_hidden(style_name):
    # Hiding the headers swaps in superior_header_line_no_header, a separate
    # field that the header-on path never touches.
    table = build_table(style_name)
    table.show_headers = False

    rendered = str(table)

    assert 'Results' not in rendered
    assert '9.651' in rendered


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_renders_with_the_index_column(style_name):
    table = build_table(style_name)
    table.show_index = True

    rendered = str(table)

    assert '9.651' in rendered


@pytest.mark.parametrize('style_name', ALL_STYLES)
def test_every_style_renders_a_wrapped_cell(style_name):
    table = Table(style_name=style_name)
    table.add_column('Name', ['Piotr\nBaltimore', 'Sam'])
    table.add_column('Age', [27, 21])

    rendered = str(table)

    assert 'Piotr' in rendered
    assert 'Baltimore' in rendered
    # The wrapped cell occupies its own printed line.
    assert not any('Piotr' in line and 'Baltimore' in line
                   for line in rendered.splitlines())


# +-------------------------------------------------------------------------+
# Style selection
# +-------------------------------------------------------------------------+

def test_an_unknown_style_name_falls_back_to_the_default():
    table = Table(style_name='not_a_real_style')

    assert table.style_name == DEFAULT_STYLE


def test_no_style_name_falls_back_to_the_default():
    assert Table().style_name == DEFAULT_STYLE


def test_the_style_name_setter_accepts_a_catalogue_name():
    table = build_table('grid')
    table.style_name = 'thin_borderline'

    assert table.style_name == 'thin_borderline'
    assert '┌' in str(table)


def test_the_style_name_setter_reads_style_examples_from_the_cwd(monkeypatch, tmp_path):
    """
    ``style_name``'s setter calls ``read_file('style_examples.md')``, a path
    resolved against the current working directory rather than the package.
    Setting a style from anywhere but the repository root raises.

    Pinned as-is: the suite works around it with the ``repo_root_cwd`` fixture,
    but the coupling is real and this is what would change if it were fixed.
    """
    table = Table()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError):
        table.style_name = 'thin_borderline'


def test_style_examples_is_present_at_the_repository_root():
    # Guards the fixture that makes the setter above usable in the suite.
    assert os.path.isfile(os.path.join(REPO_ROOT, 'style_examples.md'))
