"""
Optional C acceleration for drawing terminal frames with flexablelib.

Install with ``pip install flexablelib[speed]``. Nothing imports this package
directly: :mod:`flexablelib._frames` picks it up when it is installed and
falls back to identical pure-Python code when it is not.
"""

__version__ = '3.3.1'

from . import _frames  # noqa: F401,E402

__all__ = ['_frames', '__version__']
