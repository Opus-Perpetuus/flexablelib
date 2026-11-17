"""3.7.2: damaged or hostile image files give ImageError from the built-in
decoders (PNG, GIF, BMP, PNM), on both backends, instead of ValueError,
IndexError or struct.error -- and a header that asks for an enormous picture
is refused before any memory is set aside for it."""

import struct
import time
import zlib

import pytest

from flexablelib import _images as I


def _chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data +
            struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))


def _png(width, height, raw, ctype=2, depth=8, interlace=0, ihdr=None):
    if ihdr is None:
        ihdr = struct.pack('>IIBBBBB', width, height, depth, ctype, 0, 0,
                           interlace)
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr) +
            _chunk(b'IDAT', zlib.compress(raw)) + _chunk(b'IEND', b''))


def _bmp(width, height, bits=24, palette=b'', pixels=None, colors=0,
         header=40, size=None):
    stride = ((width * bits + 31) // 32) * 4
    if pixels is None:
        pixels = bytes(stride * abs(height))
    offset = 14 + header + len(palette)
    dib = struct.pack('<IiiHHIIiiII', header, width, height, 1, bits, 0,
                      len(pixels), 2835, 2835, colors, 0)
    dib += bytes(header - len(dib))
    body = dib + palette + pixels
    return (b'BM' + struct.pack('<IHHI', size or 14 + len(body), 0, 0,
                                offset) + body)


def _gif(width, height, frame=None):
    head = b'GIF89a' + struct.pack('<HHBBB', width, height, 0x80, 0, 0)
    table = b'\x00\x00\x00\xff\xff\xff'
    fw, fh = frame or (width, height)
    desc = b',' + struct.pack('<HHHHB', 0, 0, fw, fh, 0)
    # One clear code, one pixel of index 1, end: 2-bit codes, min size 2.
    data = b'\x02\x02\x4c\x01\x00'
    return head + table + desc + data + b';'


@pytest.fixture(params=I.available())
def backend(request):
    old = I.BACKEND
    I.use(request.param)
    yield request.param
    I.use(old)


@pytest.fixture
def no_pillow(monkeypatch):
    monkeypatch.setattr(I, '_pillow', lambda: None)


def _refused(data, **kw):
    with pytest.raises(I.ImageError):
        I.decode(data, **kw)


class TestDamagedFilesGiveImageError:
    @pytest.mark.parametrize('data', [
        b'P1\n3 2\n0 A 0\n1 0 1\n',
        b'P2 2 2 15 0 15 7M3',
        b'P1\n3 2\n0 1 0\n1 0 \xff\xff',
    ])
    def test_pnm_bad_pixel_tokens(self, backend, no_pillow, data):
        _refused(data)

    def test_png_short_header_chunk(self, backend, no_pillow):
        _refused(_png(0, 0, b'\x00', ihdr=b'\x00\x00\x00\x05\x00\x00'))

    def test_png_unknown_filter_byte(self, backend, no_pillow):
        raw = b'\x07' + bytes(3)
        with pytest.raises(I.ImageError, match='filtro desconocido 7'):
            I.decode(_png(1, 1, raw))

    def test_png_unsupported_interlace(self, backend, no_pillow):
        _refused(_png(1, 1, b'\x00' + bytes(3), interlace=2))

    def test_png_zero_size(self, backend, no_pillow):
        with pytest.raises(I.ImageError, match='sin tamaño'):
            I.decode(_png(0, 3, b'\x00\x00\x00'))

    def test_png_short_pixel_data(self, backend, no_pillow):
        with pytest.raises(I.ImageError, match='truncado'):
            I.decode(_png(4, 4, b'\x00' + bytes(12)))

    def test_bmp_palette_past_the_end(self, backend, no_pillow):
        # 8 bits with a palette count of 226 but almost no bytes after.
        data = _bmp(5, 3, bits=8, colors=226, pixels=b'')[:60]
        _refused(data)

    def test_bmp_unknown_bit_depth(self, backend, no_pillow):
        _refused(_bmp(2, 2, bits=7))

    def test_bmp_negative_width(self, backend, no_pillow):
        _refused(_bmp(-5, 3, pixels=bytes(48)))

    def test_bmp_pixels_missing(self, backend, no_pillow):
        with pytest.raises(I.ImageError, match='BMP truncado'):
            I.decode(_bmp(4, 4, pixels=bytes(10)))

    def test_bmp_bitfields_header_cut(self, backend, no_pillow):
        data = bytearray(_bmp(1, 1, bits=32))
        data[30:34] = struct.pack('<I', 3)      # BI_BITFIELDS
        _refused(bytes(data[:60]))

    @pytest.mark.parametrize('cut', [8, 12, 20, 25])
    def test_gif_cut_short(self, backend, no_pillow, cut):
        _refused(_gif(2, 2)[:cut])

    def test_valid_files_still_read(self, backend, no_pillow):
        assert I.decode(_png(1, 1, b'\x00\x01\x02\x03')).pixel(0, 0) == \
            (1, 2, 3, 255)
        assert I.decode(_bmp(2, 1)).size == (2, 1)
        assert I.decode(_gif(2, 2)).size == (2, 2)
        assert I.decode(b'P1 2 1 0 1').size == (2, 1)


class TestHugeHeaders:
    """A few bytes that claim billions of pixels: refused quickly, with
    ImageError, and without trying to allocate the picture."""

    def _fast(self, data):
        start = time.perf_counter()
        _refused(data)
        assert time.perf_counter() - start < 2

    def test_png(self, backend, no_pillow):
        self._fast(_png(100000, 100000, b'\x00' + bytes(30)))

    def test_png_interlaced(self, backend, no_pillow):
        self._fast(_png(100000, 100000, b'\x00' + bytes(30), interlace=1))

    def test_png_within_limit_but_little_data(self, backend, no_pillow):
        with pytest.raises(I.ImageError, match='truncado'):
            I.decode(_png(5000, 5000, b'\x00' + bytes(30)))

    def test_gif(self, backend, no_pillow):
        self._fast(_gif(65535, 65535))

    def test_gif_huge_frame(self, backend, no_pillow):
        self._fast(_gif(2, 2, frame=(65535, 65535)))

    def test_bmp(self, backend, no_pillow):
        self._fast(_bmp(100000, 100000, pixels=b''))

    def test_pnm(self, backend, no_pillow):
        self._fast(b'P5 100000 100000 255\n' + bytes(10))

    def test_limit_is_public_and_adjustable(self, backend, no_pillow,
                                            monkeypatch):
        data = _png(4, 4, b''.join(b'\x00' + bytes(12) for _ in range(4)))
        assert I.decode(data).size == (4, 4)
        monkeypatch.setattr(I, 'MAX_PIXELS', 15)
        with pytest.raises(I.ImageError, match='demasiado grande'):
            I.decode(data)

    def test_with_pillow_too(self, backend):
        pytest.importorskip('PIL')
        self._fast(_png(100000, 100000, b'\x00' + bytes(30)))


class TestBackendParity:
    def test_unfilter_unknown_filter_is_image_error(self, backend):
        with pytest.raises(I.ImageError, match='filtro desconocido 9'):
            I.unfilter(b'\x09abc', 1, 3, 1)

    def test_unfilter_unknown_filter_on_empty_rows(self, backend):
        # A row of zero bytes still has its filter byte checked.
        with pytest.raises(I.ImageError):
            I.unfilter(b'\x05', 1, 0, 1)
        assert I.unfilter(b'\x00', 1, 0, 1) == b''

    def test_unfilter_truncated(self, backend):
        with pytest.raises(I.ImageError, match='truncado'):
            I.unfilter(b'\x00ab', 1, 3, 1)

    @pytest.mark.parametrize('w,h,data', [(0, 0, b''), (2, 0, b''),
                                          (2, 2, bytes(15))])
    def test_quantize_bad_size(self, backend, w, h, data):
        with pytest.raises(ValueError):
            I.quantize(data, w, h, 16, 128)

    def test_image_error_is_a_value_error(self):
        assert issubclass(I.ImageError, ValueError)


class TestDecoderEdges:
    def test_png_bad_zlib_stream(self, backend, no_pillow):
        data = _png(1, 1, b'\x00' + bytes(3))
        start = data.index(b'IDAT') + 4
        broken = data[:start] + b'\xff\xff\xff' + data[start + 3:]
        with pytest.raises(I.ImageError, match='PNG dañado'):
            I.decode(broken)

    def test_gif_frame_past_the_canvas_is_clipped(self, backend, no_pillow):
        # A 1x1 canvas with a 2x2 frame placed at (0, 0): only the corner
        # pixel lands; the rest is outside and skipped.
        data = _gif(1, 1, frame=(2, 2))
        bitmap = I.decode(data)
        assert bitmap.size == (1, 1)
