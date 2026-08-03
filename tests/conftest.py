"""
Shared fixtures.

Two things make ``prettyTables`` non-deterministic unless they are pinned:

1. ``utils.get_window_size()`` reads the real console size, and
   ``Table.compose()`` uses it to decide whether the table has to be
   re-wrapped. Every test therefore runs against a fake terminal size, so a
   narrow CI runner cannot change the expected output.

2. The ``style_name`` setter calls ``read_file('style_examples.md')``, a path
   resolved against the *current working directory*. Tests are pinned to the
   repository root so that setter does not explode depending on where pytest
   was invoked from.
"""

import os
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)

# Import the package from the source tree without installing it first, and
# make ``helpers`` importable from the test modules.
for path in (REPO_ROOT, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from helpers import DEFAULT_TERMINAL_COLS, DEFAULT_TERMINAL_LINES  # noqa: E402
from prettyTables import table as table_module  # noqa: E402


@pytest.fixture(autouse=True)
def repo_root_cwd(monkeypatch):
    """
    Pin the CWD to the repository root.

    ``Table.style_name``'s setter reads ``style_examples.md`` relative to the
    CWD, so without this every test that touches that setter would depend on
    where pytest happened to be started.
    """
    monkeypatch.chdir(REPO_ROOT)


@pytest.fixture(autouse=True)
def default_terminal(monkeypatch):
    """
    Give every test a wide, fixed terminal so CI never renders differently
    from a developer's console.
    """
    monkeypatch.setattr(
        table_module,
        'get_window_size',
        lambda: (DEFAULT_TERMINAL_COLS, DEFAULT_TERMINAL_LINES),
    )


@pytest.fixture
def terminal(monkeypatch, default_terminal):
    """
    Override the fake terminal size for a single test.

    Depends on ``default_terminal`` so the order of the two patches is
    guaranteed: this one always wins.

    Usage::

        def test_something(terminal):
            terminal(20)
            ...
    """
    def _set_terminal(cols, lines=DEFAULT_TERMINAL_LINES):
        monkeypatch.setattr(
            table_module,
            'get_window_size',
            lambda: (cols, lines),
        )
        return cols, lines

    return _set_terminal


@pytest.fixture
def terminal_calls(monkeypatch, default_terminal):
    """
    Like ``terminal``, but returns a list that records every read of the
    terminal size.
    """
    calls = []

    def _set_terminal(cols, lines=DEFAULT_TERMINAL_LINES):
        def _fake_get_window_size():
            calls.append((cols, lines))
            return cols, lines

        monkeypatch.setattr(
            table_module,
            'get_window_size',
            _fake_get_window_size,
        )
        return calls

    return _set_terminal
