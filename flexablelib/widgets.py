"""
Terminal widgets -- compatibility module.

Since 3.3.0 the widgets (``ProgressBar``, ``Sparkline``, ``BarChart``,
``StatusBar``, ``KeyHints``, ``LogView``, ``Text``, ``Rule``) live in the
optional package ``flexablelib-tui``::

    pip install "flexablelib[tui]"

With it installed this module *is* ``flexablelib_tui.widgets``. Without it,
the 3.2.0 widgets bundled here keep working and a DeprecationWarning says how
to install the package; the bundled copy goes away in 4.0.
"""

import sys
import warnings

try:
    from flexablelib_tui import widgets as _impl
except ImportError:
    warnings.warn('flexablelib.widgets now lives in the optional package '
                  'flexablelib-tui; pip install "flexablelib[tui]". The '
                  'bundled 3.2.0 widgets are used for now and will be '
                  'removed in 4.0.', DeprecationWarning, stacklevel=2)
    from ._legacy import widgets as _impl

sys.modules[__name__] = _impl
