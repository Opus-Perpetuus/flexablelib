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

__version__ = '3.5.2'

from .widgets import (ProgressBar, Sparkline, BarChart, StatusBar, KeyHints,
                      LogView, Text, Rule)
from .screen import Screen, Live, render_height
from .keys import (Key, MouseEvent, KeyParser, WindowsKeyParser, parse_keys,
                   normalize_key, key_label)
from .keymap import KeyMap
from .capabilities import Capabilities, detect as detect_capabilities
from .terminal import Terminal
from .app import App, Component, ScrollView, overlay
from . import graphics
from .graphics import GraphicsInfo, detect as detect_graphics

__all__ = ['ProgressBar', 'Sparkline', 'BarChart', 'StatusBar', 'KeyHints',
           'LogView', 'Text', 'Rule', 'Screen', 'Live', 'render_height',
           'Key', 'MouseEvent', 'KeyParser', 'WindowsKeyParser', 'parse_keys',
           'normalize_key', 'key_label', 'KeyMap', 'Capabilities',
           'detect_capabilities', 'Terminal',
           'App', 'Component', 'ScrollView', 'overlay', 'graphics',
           'GraphicsInfo', 'detect_graphics', '__version__']
