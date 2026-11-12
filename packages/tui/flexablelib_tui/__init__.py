"""
Terminal interface toolkit for flexablelib (``pip install flexablelib[tui]``).

Widgets (progress bars, sparklines, bar charts, status bars, key hints, logs,
text, rules), full-screen layout (:class:`Screen`), in-place redraw that
writes only the changed lines (:class:`Live`), keyboard input on Linux, macOS
and Windows (:class:`Terminal`, :class:`KeyParser`), and interactive
applications with focus, key bindings, scrolling, dialogs and resize
(:class:`App`, :class:`Component`, :class:`ScrollView`).

Everything here is also reachable as ``flexablelib.ProgressBar``,
``flexablelib.App`` and so on once installed.
"""

__version__ = '3.3.1'

from .widgets import (ProgressBar, Sparkline, BarChart, StatusBar, KeyHints,
                      LogView, Text, Rule)
from .screen import Screen, Live, render_height
from .keys import Key, KeyParser, WindowsKeyParser, parse_keys
from .terminal import Terminal
from .app import App, Component, ScrollView, overlay

__all__ = ['ProgressBar', 'Sparkline', 'BarChart', 'StatusBar', 'KeyHints',
           'LogView', 'Text', 'Rule', 'Screen', 'Live', 'render_height',
           'Key', 'KeyParser', 'WindowsKeyParser', 'parse_keys', 'Terminal',
           'App', 'Component', 'ScrollView', 'overlay', '__version__']
