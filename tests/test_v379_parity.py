"""3.7.9: the Python picture primitives refuse the sizes the C ones refuse.

``sixel_encode`` with fewer indices than ``width * height`` raised
``IndexError`` (or quietly drew a short picture) in Python and
``ValueError`` in C; ``cells`` with a negative width or height returned
empty rows in Python and raised ``ValueError`` in C.
"""

import pytest

from flexablelib import _images as I

BACKENDS = [I._PYTHON] + ([I._C.__dict__] if I._C is not None else [])


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('indices, width, height', [
    (b'\x00' * 8, 1, 9),          # one index short of 1 x 9
    (b'\xff' * 9 + b'\x00', 2, 6),  # ten indices for 2 x 6
    (b'\x00' * 4, 0, 4),
    (b'\x00' * 4, 4, 0),
    (b'\x00' * 4, -1, 4),
])
def test_sixel_encode_refuses_bad_sizes(backend, indices, width, height):
    with pytest.raises(ValueError):
        backend['sixel_encode'](indices, width, height, b'\x10\x20\x30')


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('width, height', [(-1, 6), (6, -1), (-2, -2)])
def test_cells_refuses_negative_sizes(backend, width, height):
    with pytest.raises(ValueError):
        backend['cells'](b'\xff' * 64, width, height, 'half', 'truecolor',
                         128)


@pytest.mark.parametrize('backend', BACKENDS)
def test_good_sizes_still_draw(backend):
    assert backend['sixel_encode'](b'\x00\x00', 1, 2, b'\x10\x20\x30') \
        == I._py_sixel_encode(b'\x00\x00', 1, 2, b'\x10\x20\x30')
    assert backend['cells'](b'', 0, 0, 'half', 'none', 128) == []
