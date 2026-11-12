"""
Full-screen layout and live refresh -- compatibility module.

Since 3.3.0 ``Screen`` and ``Live`` live in the optional package
``flexablelib-tui`` (``pip install "flexablelib[tui]"``), together with
keyboard input, ``App`` and the components. With it installed this module
*is* ``flexablelib_tui.screen``; without it the bundled 3.2.0 version keeps
working with a DeprecationWarning, until 4.0.
"""

import sys
import warnings

try:
    from flexablelib_tui import screen as _impl
except ImportError:
    warnings.warn('flexablelib.screen now lives in the optional package '
                  'flexablelib-tui; pip install "flexablelib[tui]". The '
                  'bundled 3.2.0 version is used for now and will be '
                  'removed in 4.0.', DeprecationWarning, stacklevel=2)
    from ._legacy import screen as _impl

sys.modules[__name__] = _impl
