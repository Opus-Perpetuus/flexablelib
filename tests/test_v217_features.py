"""Fixes and packaging guarantees shipped in 2.0.17."""
import os
import re
import subprocess
import sys

import pytest

from flexablelib.colors import ColourError, parse_spec
from flexablelib.table import Table

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bare(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


# --- Rich/X11 percentage greys -------------------------------------------

@pytest.mark.parametrize('spec, code', [
    ('grey0', '38;5;16'),
    ('grey23', '38;5;237'),     # Rich's grey23
    ('gray50', '38;5;244'),     # Rich's grey50
    ('grey100', '38;5;231'),
    ('on grey23', '48;5;237'),
])
def test_percentage_greys_map_to_the_nearest_xterm_grey(spec, code):
    assert parse_spec(spec) == f'\x1b[{code}m'


def test_out_of_range_grey_is_rejected():
    with pytest.raises(ColourError):
        parse_spec('grey101')


def test_zebra_accepts_a_percentage_grey_background():
    table = Table(rows=[['a'], ['b']], headers=['x'])
    table.use_colors = True
    table.zebra = 'on grey23'
    assert '48;5;237' in table.compose()


# --- border_text keeps the frame corners ---------------------------------

def _framed():
    table = Table(rows=[['alpha', 1], ['beta', 2]], headers=['name', 'n'])
    table.style_name = 'modern'
    return table


def test_right_aligned_border_text_keeps_the_closing_corner():
    table = _framed()
    table.border_text('END', where='bottom', offset=None, align='right')
    bottom = bare(table.compose()).splitlines()[-1]
    assert bottom.endswith('END┘')
    assert bottom.startswith('└')


def test_overlong_border_text_is_truncated_before_the_corner():
    table = _framed()
    plain_top = bare(str(_framed())).splitlines()[0]
    table.border_text('X' * 200, where='top', offset=1)
    top = bare(table.compose()).splitlines()[0]
    assert len(top) == len(plain_top)
    assert top[0] == '┌' and top[-1] == '┐'


def test_centered_border_text_sits_inside_the_corners():
    table = _framed()
    table.border_text('mid', where='top', offset=None, align='center')
    top = bare(table.compose()).splitlines()[0]
    assert top[0] == '┌' and top[-1] == '┐' and 'mid' in top


# --- default valign skips per-cell resolution -----------------------------

def test_middle_valign_still_applies_after_the_fast_path():
    table = Table(rows=[['a\nb\nc', 'x']], headers=['tall', 'short'])
    table.style_name = 'ascii'
    table.valign = 'm'
    body = [line for line in bare(table.compose()).splitlines()
            if line.startswith('|')][1:]
    assert ' x ' in body[1]


# --- packaging ------------------------------------------------------------

def test_py_typed_marker_ships_with_the_package():
    import flexablelib
    package_dir = os.path.dirname(os.path.abspath(flexablelib.__file__))
    assert os.path.isfile(os.path.join(package_dir, 'py.typed'))


def _repo_file(name):
    # Downstream packagers (conda-forge) run the suite against an installed
    # package with only tests/ copied over; repo-only checks skip there.
    path = os.path.join(REPO_ROOT, name)
    if not os.path.isfile(path):
        pytest.skip(f'{name} is only present in a source checkout')
    return path


def test_manifest_ships_style_examples_and_tests_in_the_sdist():
    with open(_repo_file('MANIFEST.in')) as handle:
        manifest = handle.read()
    assert 'include style_examples.md' in manifest
    assert 'recursive-include tests *.py' in manifest
    assert 'include flexablelib/py.typed' in manifest


def test_style_name_works_outside_the_repository_root(tmp_path):
    code = (
        'import sys; sys.path.insert(0, {root!r});'
        'from flexablelib import Table;'
        't = Table(rows=[[1]], headers=["a"]); t.style_name = "rounded";'
        'print(t)'
    ).format(root=REPO_ROOT)
    result = subprocess.run([sys.executable, '-c', code], cwd=str(tmp_path),
                            capture_output=True, text=True,
                            encoding='utf-8',
                            env={**os.environ, 'PYTHONUTF8': '1'})
    assert result.returncode == 0, result.stderr
    assert '╭' in result.stdout


# --- README quickstart stays true -----------------------------------------

def test_readme_quickstart_prints_the_output_shown_below_it(capsys):
    """The first python block in README.md is what new users paste."""
    with open(_repo_file('README.md'), encoding='utf-8') as handle:
        readme = handle.read()
    section = readme[readme.index('## 30-second quickstart'):]
    code = re.search(r'```python\n(.*?)```', section, re.S).group(1)
    shown = re.search(r'```\n(╭.*?)```', section, re.S).group(1).strip('\n')
    exec(compile(code, 'README.md', 'exec'), {})
    assert bare(capsys.readouterr().out).strip('\n') == shown


# --- to_html: cell text cannot break out of the inline script --------------

def test_to_html_cell_cannot_close_the_inline_script():
    import json
    payload = '</script><img src=x onerror=alert(1)>'
    table = Table(rows=[[payload, 'a&b']], headers=['<b>h</b>', 'y'])
    page = table.to_html()
    assert '</script><img' not in page
    assert page.count('</script>') == 1           # only the real closing tag
    data = re.search(r'var DATA = (.*);\n', page).group(1)
    assert json.loads(data)['rows'] == [[payload, 'a&b']]
