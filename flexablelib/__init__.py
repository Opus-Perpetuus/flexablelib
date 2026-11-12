from .table import Table
from .style_compositions import TableComposition, SeparatorLine
from .layout import Card, Grid, GridCell
from .identifiers import ID_COLUMN_NAMES, is_id_column

# Terminal interfaces are optional packages, imported on first use:
#
#   pip install "flexablelib[tui]"         widgets, Screen, Live, App, keys
#   pip install "flexablelib[components]"  inputs, menus, tables, dialogs ...
#   pip install "flexablelib[speed]"       C frame drawing (cut, pad, borders)
#
# The 3.2.0 names (widgets, Screen, Live) still work without the tui package,
# from a bundled copy that warns; the new ones need it.
_COMPAT = {
    'ProgressBar': 'widgets', 'Sparkline': 'widgets', 'BarChart': 'widgets',
    'StatusBar': 'widgets', 'KeyHints': 'widgets', 'LogView': 'widgets',
    'Text': 'widgets', 'Rule': 'widgets', 'Screen': 'screen', 'Live': 'screen',
}
_TUI = ('App', 'Component', 'ScrollView', 'Terminal', 'Key', 'KeyParser',
        'WindowsKeyParser', 'parse_keys', 'overlay', 'MouseEvent', 'KeyMap')

# Names, not the objects themselves: `from flexablelib import *` walks this
# list and raises TypeError on anything that is not a string.
__all__ = ['Table', 'TableComposition', 'SeparatorLine', 'Card', 'Grid',
           'GridCell', 'ProgressBar', 'Sparkline', 'BarChart', 'StatusBar',
           'KeyHints', 'LogView', 'Text', 'Rule', 'Screen', 'Live',
           'is_id_column', 'ID_COLUMN_NAMES']


def _optional(package, extra):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError as error:
        if getattr(error, 'name', None) not in (package, None):
            raise
        raise ImportError('this needs the optional package {0}: pip install '
                          '"flexablelib[{1}]"'.format(
                              package.replace('_', '-'), extra)) from None


def __getattr__(name):
    if name in _COMPAT:
        import importlib
        module = importlib.import_module('.' + _COMPAT[name], __name__)
        return getattr(module, name)
    if name in _TUI:
        return getattr(_optional('flexablelib_tui', 'tui'), name)
    if name[:1].isupper():
        try:
            import flexablelib_components as components
        except ImportError:
            components = None
        if components is not None and name in components.__all__:
            return getattr(components, name)
    raise AttributeError('module {0!r} has no attribute {1!r}'.format(
        __name__, name))


def __dir__():
    return sorted(set(globals()) | set(__all__) | set(_TUI))
