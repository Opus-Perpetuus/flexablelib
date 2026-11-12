"""3.5.0 core: image decoders, resize, quantization, sixel, text cells --
pure Python and C (flexablelib-speedups) give the same results."""

import io
import os
import random
import struct
import zlib

import pytest

from flexablelib import _images as I


def _gradient(w=7, h=5, alpha=False):
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out += bytes([x * 255 // max(1, w - 1), y * 255 // max(1, h - 1),
                          (x * y * 37) & 255,
                          (255 if not alpha else (x + y) * 255 // (w + h))])
    return I.Bitmap(w, h, out)


def _png(width, height, ctype, depth, rows, extra=b'', interlace=0):
    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data +
                struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    ihdr = struct.pack('>IIBBBBB', width, height, depth, ctype, 0, 0,
                       interlace)
    raw = b''.join(b'\x00' + r for r in rows)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + extra +
            chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


@pytest.fixture(params=I.available())
def backend(request):
    old = I.BACKEND
    I.use(request.param)
    yield request.param
    I.use(old)


class TestBitmap:
    def test_basics(self):
        bm = _gradient(4, 3)
        assert bm.size == (4, 3) and not bm.has_alpha()
        assert bm.pixel(3, 0)[:2] == (255, 0)
        assert bm.crop(1, 1, 2, 2).size == (2, 2)
        assert bm.crop(-1, -1, 10, 10).size == (4, 3)
        assert bm.flatten() is bm
        assert 'Bitmap(4x3)' == repr(bm)
        g = bm.grayscale()
        r, gg, b, a = g.pixel(2, 1)
        assert r == gg == b

    def test_alpha_flatten(self):
        bm = I.Bitmap(2, 1, bytes([255, 0, 0, 0, 0, 0, 255, 128]))
        assert bm.has_alpha()
        flat = bm.flatten((0, 255, 0))
        assert flat.pixel(0, 0) == (0, 255, 0, 255)
        assert flat.pixel(1, 0)[3] == 255

    def test_errors(self):
        with pytest.raises(I.ImageError):
            I.Bitmap(0, 1, b'')
        with pytest.raises(I.ImageError):
            I.Bitmap(1, 1, b'\0')

    def test_from_rgb(self):
        bm = I.Bitmap.from_rgb(1, 1, b'\x01\x02\x03')
        assert bm.pixel(0, 0) == (1, 2, 3, 255)


class TestPNG:
    def test_roundtrip(self, backend):
        bm = _gradient(9, 6, alpha=True)
        back = I.decode_png(I.encode_png(bm))
        assert back.data == bm.data

    @pytest.mark.parametrize('depth', [1, 2, 4, 8, 16])
    def test_gray(self, depth):
        maxv = (1 << depth) - 1
        vals = [0, maxv, maxv // 2 if maxv > 1 else 1, 0]
        if depth == 16:
            row = b''.join(struct.pack('>H', v) for v in vals)
        else:
            bits = ''.join(format(v, '0{0}b'.format(depth)) for v in vals)
            bits += '0' * (-len(bits) % 8)
            row = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
        bm = I.decode_png(_png(4, 1, 0, depth, [row]))
        assert bm.pixel(0, 0) == (0, 0, 0, 255)
        assert bm.pixel(1, 0) == (255, 255, 255, 255)

    def test_palette_and_trns(self):
        plte = struct.pack('>I', 6) + b'PLTE' + b'\xff\x00\x00\x00\x00\xff'
        plte += struct.pack('>I', zlib.crc32(b'PLTE\xff\x00\x00\x00\x00\xff'))
        trns = struct.pack('>I', 1) + b'tRNS\x00' + \
            struct.pack('>I', zlib.crc32(b'tRNS\x00'))
        bm = I.decode_png(_png(2, 1, 3, 8, [b'\x00\x01'], plte + trns))
        assert bm.pixel(0, 0) == (255, 0, 0, 0)
        assert bm.pixel(1, 0) == (0, 0, 255, 255)

    def test_gray_alpha_rgb16(self):
        bm = I.decode_png(_png(1, 1, 4, 8, [b'\x80\x40']))
        assert bm.pixel(0, 0) == (128, 128, 128, 64)
        bm = I.decode_png(_png(1, 1, 2, 16, [b'\xff\xff\x00\x00\x80\x00']))
        assert bm.pixel(0, 0) == (255, 0, 128, 255)

    def test_against_pillow(self, tmp_path):
        Image = pytest.importorskip('PIL.Image')
        rnd = random.Random(3)
        for mode in ('L', 'LA', 'RGB', 'RGBA', 'P', '1'):
            im = Image.new('RGBA', (13, 7))
            im.putdata([tuple(rnd.randrange(256) for _ in range(4))
                        for _ in range(13 * 7)])
            im = im.convert(mode)
            for interlace in (0, 1):
                buf = io.BytesIO()
                im.save(buf, 'PNG', interlace=interlace)
                ours = I.decode_png(buf.getvalue())
                ref = Image.open(io.BytesIO(buf.getvalue()))
                ref = ref.convert('RGBA')
                assert ours.data == ref.tobytes(), (mode, interlace)

    def test_errors(self):
        with pytest.raises(I.ImageError):
            I.decode_png(b'\x89PNG\r\n\x1a\nxx')
        with pytest.raises(I.ImageError):
            I.decode_png(b'nope')


class TestOtherFormats:
    def test_pnm(self):
        assert I.decode_pnm(b'P1\n2 1\n0 1').pixel(1, 0)[:3] == (0, 0, 0)
        assert I.decode_pnm(b'P2 # c\n1 1 15\n15').pixel(0, 0)[0] == 255
        assert I.decode_pnm(b'P3\n1 1\n255\n1 2 3').pixel(0, 0) == \
            (1, 2, 3, 255)
        assert I.decode_pnm(b'P4\n2 1\n\x80').pixel(0, 0)[0] == 0
        assert I.decode_pnm(b'P5\n1 1\n255\n\x10').pixel(0, 0)[0] == 16
        assert I.decode_pnm(b'P6\n1 1\n255\n\x01\x02\x03').pixel(0, 0) == \
            (1, 2, 3, 255)
        assert I.decode_pnm(b'P6\n1 1\n65535\n\xff\xff\x00\x00\x80\x00') \
            .pixel(0, 0)[:3] == (255, 0, 128)
        with pytest.raises(I.ImageError):
            I.decode_pnm(b'P9\n1 1\n')

    @pytest.mark.parametrize('mode,fmt', [('RGB', 'BMP'), ('P', 'BMP'),
                                          ('1', 'BMP'), ('RGBA', 'BMP'),
                                          ('L', 'BMP'), ('RGB', 'GIF'),
                                          ('P', 'GIF'), ('RGB', 'PPM'),
                                          ('L', 'PPM')])
    def test_against_pillow(self, mode, fmt):
        Image = pytest.importorskip('PIL.Image')
        rnd = random.Random(5)
        im = Image.new('RGB', (11, 6))
        im.putdata([tuple(rnd.randrange(256) for _ in range(3))
                    for _ in range(66)])
        im = im.convert(mode)
        buf = io.BytesIO()
        im.save(buf, fmt)
        data = buf.getvalue()
        ours = {'BMP': I.decode_bmp, 'GIF': I.decode_gif,
                'PPM': I.decode_pnm}[fmt](data)
        ref = Image.open(io.BytesIO(data)).convert('RGBA')
        if fmt == 'BMP' and mode == 'RGBA':
            ref = Image.open(io.BytesIO(data)).convert('RGBA')
        assert ours.size == ref.size
        assert ours.data == ref.tobytes()

    def test_gif_frames(self):
        Image = pytest.importorskip('PIL.Image')
        frames = [Image.new('RGB', (4, 3), c) for c in
                  ((255, 0, 0), (0, 255, 0), (0, 0, 255))]
        buf = io.BytesIO()
        frames[0].save(buf, 'GIF', save_all=True, append_images=frames[1:],
                       duration=120, loop=0)
        got = I.decode_gif(buf.getvalue(), all_frames=True)
        assert len(got) == 3
        assert got[1].pixel(0, 0)[:3] == (0, 255, 0)
        assert got[2].delay == 120
        assert I.decode_gif(buf.getvalue()).pixel(0, 0)[:3] == (255, 0, 0)

    def test_detect_format(self):
        assert I.detect_format(b'\x89PNG\r\n\x1a\n') == 'png'
        assert I.detect_format(b'\xff\xd8\xff') == 'jpeg'
        assert I.detect_format(b'GIF89a') == 'gif'
        assert I.detect_format(b'BM') == 'bmp'
        assert I.detect_format(b'RIFF\0\0\0\0WEBP') == 'webp'
        assert I.detect_format(b'P6\n1 1') == 'pnm'
        assert I.detect_format(b'<svg xmlns') == 'svg'
        assert I.detect_format(b'%PDF-1.4') == 'pdf'
        assert I.detect_format(b'zzzz') is None


class TestLoading:
    def test_sources(self, tmp_path):
        bm = _gradient(3, 2)
        png = I.encode_png(bm)
        path = tmp_path / 'a.png'
        path.write_bytes(png)
        assert I.load(str(path)).data == bm.data
        assert I.load(path).data == bm.data
        assert I.load(path.as_uri()).data == bm.data
        assert I.load(png).data == bm.data
        assert I.load(io.BytesIO(png)).data == bm.data
        assert I.load(bm) is bm
        assert len(I.load_frames(str(path))) == 1

    def test_no_pillow_paths(self, monkeypatch):
        monkeypatch.setenv('FLEXABLELIB_NO_PILLOW', '1')
        bm = I.decode(I.encode_png(_gradient(2, 2)))
        assert bm.size == (2, 2)
        with pytest.raises(I.ImageError) as err:
            I.decode(b'\xff\xd8\xff\xe0' + b'\0' * 20)
        assert 'flexablelib[images]' in str(err.value)
        with pytest.raises(I.ImageError):
            I.decode(b'not an image at all')

    def test_pillow_formats(self):
        Image = pytest.importorskip('PIL.Image')
        for fmt in ('JPEG', 'WEBP', 'TIFF'):
            buf = io.BytesIO()
            try:
                Image.new('RGB', (5, 4), (200, 10, 10)).save(buf, fmt)
            except (OSError, KeyError):
                continue
            bm = I.decode(buf.getvalue())
            assert bm.size == (5, 4)
            assert bm.pixel(2, 2)[0] > 150
        im = Image.new('RGBA', (2, 2), (1, 2, 3, 4))
        assert I.load(im).pixel(0, 0) == (1, 2, 3, 4)

    def test_missing_file(self, tmp_path):
        with pytest.raises((I.ImageError, OSError)):
            I.load(str(tmp_path / 'nope.png'))

    def test_svg_pdf_need_renderers(self, monkeypatch):
        monkeypatch.setattr(I, '_which', lambda name: None)
        import builtins
        real = builtins.__import__

        def no(name, *a, **k):
            if name in ('cairosvg', 'fitz'):
                raise ImportError(name)
            return real(name, *a, **k)
        monkeypatch.setattr(builtins, '__import__', no)
        with pytest.raises(I.ImageError):
            I.render_svg(b'<svg/>')
        with pytest.raises(I.ImageError):
            I.render_pdf(b'%PDF-1.4')

    def test_svg_pdf_tools(self, monkeypatch):
        png = I.encode_png(_gradient(2, 2))
        import builtins
        real = builtins.__import__

        def no(name, *a, **k):
            if name in ('cairosvg', 'fitz'):
                raise ImportError(name)
            return real(name, *a, **k)
        monkeypatch.setattr(builtins, '__import__', no)
        monkeypatch.setattr(I, '_which', lambda name: '/bin/' + name)
        seen = []
        def run(cmd, data=None, timeout=20):
            seen.append(cmd)
            if cmd[0] == 'pdftoppm':
                with open(cmd[-1] + '.png', 'wb') as handle:
                    handle.write(png)
            return png
        monkeypatch.setattr(I, '_run', run)
        assert I.render_svg(b'<svg/>', 40) == png
        assert I.render_pdf(b'%PDF') == png
        assert seen[0][:3] == ['rsvg-convert', '-f', 'png']
        assert seen[1][0] == 'pdftoppm'
        monkeypatch.setattr(I, '_run', lambda *a, **k: None)
        with pytest.raises(I.ImageError):
            I.render_pdf(b'%PDF')
        with pytest.raises(I.ImageError):
            I.render_svg(b'<svg/>')


class TestColours:
    def test_palettes(self):
        assert I.rgb_to_256(0, 0, 0) == 16
        assert I.rgb_to_256(255, 255, 255) == 231
        assert 232 <= I.rgb_to_256(128, 128, 128) <= 255
        assert I.rgb_to_16(255, 0, 0) in (1, 9)
        assert I.rgb_to_16(0, 0, 0) == 0


class TestPrimitivesParity:
    """C and Python give byte-identical results."""

    def _cases(self, n=25):
        rnd = random.Random(11)
        for _ in range(n):
            w, h = rnd.randint(1, 23), rnd.randint(1, 17)
            data = bytes(rnd.randrange(256) for _ in range(w * h * 4))
            yield rnd, w, h, data

    def test_resize(self):
        if 'c' not in I.available():
            pytest.skip('speedups not built')
        for rnd, w, h, data in self._cases():
            nw, nh = rnd.randint(1, 30), rnd.randint(1, 30)
            assert I._C.resize(data, w, h, nw, nh) == \
                I._py_resize(data, w, h, nw, nh)

    def test_quantize_sixel(self):
        if 'c' not in I.available():
            pytest.skip('speedups not built')
        for rnd, w, h, data in self._cases():
            colors = rnd.choice([2, 16, 255])
            c = I._C.quantize(data, w, h, colors, 128)
            p = I._py_quantize(data, w, h, colors, 128)
            assert c == p
            assert I._C.sixel_encode(p[1], w, h, p[0]) == \
                I._py_sixel_encode(p[1], w, h, p[0])

    def test_cells(self):
        if 'c' not in I.available():
            pytest.skip('speedups not built')
        for rnd, w, h, data in self._cases(15):
            for mode in ('half', 'quadrant', 'sextant', 'braille', 'ascii'):
                for color in ('truecolor', '256', '16', 'none'):
                    assert I._C.cells(data, w, h, mode, color, 128) == \
                        I._py_cells(data, w, h, mode, color, 128), \
                        (mode, color)


class TestPrimitives:
    def test_resize_exact(self, backend):
        bm = I.Bitmap(2, 1, bytes([0, 0, 0, 255, 200, 100, 50, 255]))
        assert I.scale(bm, 1, 1).pixel(0, 0) == (100, 50, 25, 255)
        assert I.scale(bm, 2, 1) is bm
        assert I.scale(bm, 4, 2).size == (4, 2)

    def test_quantize_transparent(self, backend):
        data = bytes([255, 0, 0, 255, 0, 0, 0, 0])
        pal, idx = I.quantize(data, 2, 1, 16, 128)
        assert idx[1] == 255 and idx[0] != 255
        assert pal[idx[0] * 3:idx[0] * 3 + 3] == b'\xff\x00\x00'

    def test_sixel_shape(self, backend):
        bm = _gradient(10, 13)
        pal, idx = I.quantize(bm.data, 10, 13, 8, 128)
        out = I.sixel_encode(idx, 10, 13, pal)
        assert out.startswith('\x1bP0;1;0q"1;1;10;13')
        assert out.endswith('\x1b\\')
        assert out.count('-') >= 2          # three bands of six rows
        assert '#0;2;' in out

    def test_sixel_rle(self, backend):
        bm = I.Bitmap(20, 6, bytes([0, 0, 255, 255]) * 120)
        pal, idx = I.quantize(bm.data, 20, 6, 4, 128)
        assert '!20~' in I.sixel_encode(idx, 20, 6, pal)

    @pytest.mark.parametrize('mode', ['half', 'quadrant', 'sextant',
                                      'braille', 'ascii'])
    def test_cells(self, backend, mode):
        pw, ph = I.CELL_PIXELS[mode]
        bm = I.scale(_gradient(8, 8), 4 * pw, 2 * ph)
        lines = I.cells(bm.data, bm.width, bm.height, mode, 'truecolor', 128)
        assert len(lines) == 2
        from flexablelib.text_width import visible_width
        if mode != 'sextant' or visible_width(I.sextant(1)) == 1:
            assert all(visible_width(line) == 4 for line in lines)
        mono = I.cells(bm.data, bm.width, bm.height, mode, 'none', 128)
        assert all('\x1b' not in line for line in mono)
        for level in ('256', '16'):
            col = I.cells(bm.data, bm.width, bm.height, mode, level, 128)
            assert len(col) == 2

    def test_half_blocks_colours(self, backend):
        bm = I.Bitmap(1, 2, bytes([255, 0, 0, 255, 0, 0, 255, 255]))
        line, = I.cells(bm.data, 1, 2, 'half', 'truecolor', 128)
        assert '38;2;255;0;0' in line and '48;2;0;0;255' in line
        assert '▀' in line

    def test_sextant_table(self):
        assert I.sextant(0) == ' '
        assert I.sextant(63) == '█'
        assert I.sextant(21) == '▌'
        assert len(set(I.sextant(m) for m in range(64))) == 64

    def test_use(self):
        old = I.BACKEND
        try:
            assert I.use('python') == 'python'
            assert I.resize is I._py_resize
            if 'c' not in I.available():
                with pytest.raises(RuntimeError):
                    I.use('c')
        finally:
            I.use(old)


def _bmp(width, height, bits, rows, compression=0, masks=None, header=40,
         palette=b''):
    stride = ((width * bits + 31) // 32) * 4
    pixels = b''.join(r.ljust(stride, b'\0') for r in rows)
    extra = b''
    if masks:
        extra = struct.pack('<' + 'I' * len(masks), *masks)
    info = struct.pack('<IiiHHIIiiII', header, width, height, 1, bits,
                       compression, len(pixels), 2835, 2835,
                       len(palette) // 4, 0)
    info = info.ljust(header, b'\0')
    if masks and header >= 52:
        info = info[:40] + extra + info[40 + len(extra):]
        extra = b''
    offset = 14 + header + len(extra) + len(palette)
    head = b'BM' + struct.pack('<IHHI', offset + len(pixels), 0, 0, offset)
    return head + info + extra + palette + pixels


class TestMoreDecoding:
    def test_python_unfilter_all_filters(self):
        rnd = random.Random(2)
        for bpp in (1, 3, 4, 8):
            stride, rows = bpp * 5, 4
            data = bytearray()
            for r in range(rows):
                data.append(r % 5)
                data += bytes(rnd.randrange(256) for _ in range(stride))
            got = I._py_unfilter(bytes(data), rows, stride, bpp)
            if 'c' in I.available():
                assert I._C.unfilter(bytes(data), rows, stride, bpp) == got
        with pytest.raises(I.ImageError):
            I._py_unfilter(b'\x09' + b'\0' * 4, 1, 4, 1)
        with pytest.raises(I.ImageError):
            I._py_unfilter(b'\x00', 1, 4, 1)

    def test_png_python_backend(self, backend):
        Image = pytest.importorskip('PIL.Image')
        rnd = random.Random(8)
        im = Image.new('RGBA', (9, 9))
        im.putdata([tuple(rnd.randrange(256) for _ in range(4))
                    for _ in range(81)])
        for interlace in (0, 1):
            buf = io.BytesIO()
            im.save(buf, 'PNG', interlace=interlace)
            assert I.decode_png(buf.getvalue()).data == im.tobytes()

    def test_png_transparency_keys(self):
        def chunk(kind, data):
            return (struct.pack('>I', len(data)) + kind + data +
                    struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
        bm = I.decode_png(_png(2, 1, 0, 8, [b'\x05\x09'],
                               chunk(b'tRNS', b'\x00\x05')))
        assert bm.pixel(0, 0)[3] == 0 and bm.pixel(1, 0)[3] == 255
        bm = I.decode_png(_png(1, 1, 0, 16, [b'\x12\x34'],
                               chunk(b'tRNS', b'\x12\x34')))
        assert bm.pixel(0, 0)[3] == 0
        bm = I.decode_png(_png(2, 1, 2, 8, [b'\x01\x02\x03\x04\x05\x06'],
                               chunk(b'tRNS', b'\x00\x01\x00\x02\x00\x03')))
        assert bm.pixel(0, 0)[3] == 0 and bm.pixel(1, 0)[3] == 255
        bm = I.decode_png(_png(1, 1, 2, 16, [b'\x01\x00\x02\x00\x03\x00'],
                               chunk(b'tRNS', b'\x01\x00\x02\x00\x03\x00')))
        assert bm.pixel(0, 0)[3] == 0
        bm = I.decode_png(_png(1, 1, 6, 16, [b'\xff\x00' * 4]))
        assert bm.pixel(0, 0) == (255, 255, 255, 255)
        bm = I.decode_png(_png(1, 1, 4, 16, [b'\x80\x00\xff\xff']))
        assert bm.pixel(0, 0) == (128, 128, 128, 255)

    def test_png_bad_headers(self):
        with pytest.raises(I.ImageError):
            I.decode_png(_png(1, 1, 7, 8, [b'\0']))
        with pytest.raises(I.ImageError):
            I.decode_png(_png(1, 1, 3, 8, [b'\0']))      # no palette
        good = _png(1, 1, 0, 8, [b'\0'])
        with pytest.raises(I.ImageError):
            I.decode_png(good[:40])

    def test_bmp_variants(self):
        bm = I.decode_bmp(_bmp(2, 1, 24, [b'\x01\x02\x03\x04\x05\x06']))
        assert bm.pixel(0, 0) == (3, 2, 1, 255)
        bm = I.decode_bmp(_bmp(1, 2, 24, [b'\x00\x00\xff', b'\xff\x00\x00']))
        assert bm.pixel(0, 0)[:3] == (0, 0, 255)       # bottom-up
        bm = I.decode_bmp(_bmp(1, -2, 24, [b'\x00\x00\xff', b'\xff\x00\x00']))
        assert bm.pixel(0, 0)[:3] == (255, 0, 0)       # top-down
        v = (31 << 10) | (0 << 5) | 31
        bm = I.decode_bmp(_bmp(1, 1, 16, [struct.pack('<H', v)]))
        assert bm.pixel(0, 0)[:3] == (255, 0, 255)
        bm = I.decode_bmp(_bmp(1, 1, 32, [b'\x01\x02\x03\x00']))
        assert bm.pixel(0, 0) == (3, 2, 1, 255)
        masks = (0xF800, 0x07E0, 0x001F)
        bm = I.decode_bmp(_bmp(1, 1, 16, [struct.pack('<H', 0xF800)], 3,
                               masks))
        assert bm.pixel(0, 0) == (255, 0, 0, 255)
        masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        bm = I.decode_bmp(_bmp(1, 1, 32, [b'\x10\x20\x30\x80'], 3, masks,
                               header=108))
        assert bm.pixel(0, 0) == (0x30, 0x20, 0x10, 0x80)
        pal = b'\x00\x00\xff\x00' + b'\xff\x00\x00\x00'
        bm = I.decode_bmp(_bmp(3, 1, 1, [b'\x40'], palette=pal))
        assert bm.pixel(1, 0)[:3] == (0, 0, 255)
        assert bm.pixel(0, 0)[:3] == (255, 0, 0)
        bm = I.decode_bmp(_bmp(2, 1, 4, [b'\x10'], palette=pal))
        assert bm.pixel(0, 0)[:3] == (0, 0, 255)
        bm = I.decode_bmp(_bmp(2, 1, 2, [b'\x40'], palette=pal))
        assert bm.pixel(0, 0)[:3] == (0, 0, 255)

    def test_bmp_errors(self):
        with pytest.raises(I.ImageError):
            I.decode_bmp(b'BM')
        with pytest.raises(I.ImageError):
            I.decode_bmp(_bmp(1, 1, 8, [b'\0'], compression=1,
                              palette=b'\0' * 4))
        data = _bmp(4, 4, 24, [b'\0' * 12] * 4)
        with pytest.raises(I.ImageError):
            I.decode_bmp(data[:-20])

    def test_gif_features(self):
        Image = pytest.importorskip('PIL.Image')
        rnd = random.Random(4)
        im = Image.new('P', (20, 19))
        im.putpalette(bytes(rnd.randrange(256) for _ in range(768)))
        im.putdata([rnd.randrange(256) for _ in range(380)])
        buf = io.BytesIO()
        im.save(buf, 'GIF', interlace=True)
        assert I.decode_gif(buf.getvalue()).data == \
            Image.open(io.BytesIO(buf.getvalue())).convert('RGBA').tobytes()
        frames = [Image.new('RGB', (6, 6), (255, 0, 0)),
                  Image.new('RGB', (6, 6), (0, 0, 255))]
        for disposal in (2, 3):
            buf = io.BytesIO()
            frames[0].save(buf, 'GIF', save_all=True,
                           append_images=frames[1:], disposal=disposal,
                           duration=40, transparency=0)
            got = I.decode_gif(buf.getvalue(), all_frames=True)
            assert len(got) == 2

    def test_gif_errors(self):
        with pytest.raises(I.ImageError):
            I.decode_gif(b'GIF00a')
        head = b'GIF89a' + struct.pack('<HHBBB', 1, 1, 0, 0, 0)
        with pytest.raises(I.ImageError):
            I.decode_gif(head + b'\x3b')
        with pytest.raises(I.ImageError):
            I.decode_gif(head + b'\x99')
        # local colour table, no global one, code beyond the table
        frame = b'\x2c' + struct.pack('<HHHHB', 0, 0, 1, 1, 0x80) + \
            b'\x00\x00\x00\xff\xff\xff' + b'\x02\x02\xff\xff\x00\x3b'
        with pytest.raises(I.ImageError):
            I.decode_gif(head + frame)
        plain_frame = b'\x2c' + struct.pack('<HHHHB', 0, 0, 1, 1, 0) + \
            b'\x02\x02\x44\x01\x00\x3b'
        assert I.decode_gif(head + plain_frame).size == (1, 1)

    def test_read_source_http(self, tmp_path):
        import http.server
        import threading
        png = I.encode_png(_gradient(2, 2))
        (tmp_path / 'a.png').write_bytes(png)

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=str(tmp_path), **k)

            def log_message(self, *a):
                pass
        server = http.server.HTTPServer(('127.0.0.1', 0), Quiet)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            url = 'http://127.0.0.1:{0}/'.format(server.server_port)
            assert I.read_source(url + 'a.png')[0] == png
            with pytest.raises(I.ImageError):
                I.read_source(url + 'a.png', max_bytes=10)
            with pytest.raises(I.ImageError):
                I.read_source(url + 'missing.png')
        finally:
            server.shutdown()

    def test_read_source_errors(self, tmp_path):
        with pytest.raises(I.ImageError):
            I.read_source(str(tmp_path))
        big = tmp_path / 'big.bin'
        big.write_bytes(b'x' * 20)
        with pytest.raises(I.ImageError):
            I.read_source(str(big), max_bytes=10)
        assert I.read_source(io.BytesIO(b'ab'))[0] == b'ab'

    def test_svg_pdf_real_tools(self, tmp_path):
        import shutil
        if shutil.which('rsvg-convert'):
            svg = (b'<svg xmlns="http://www.w3.org/2000/svg" width="8" '
                   b'height="4"><rect width="8" height="4" fill="red"/></svg>')
            bm = I.decode(svg)
            assert bm.size[0] > 0 and bm.pixel(1, 1)[0] > 200
        if shutil.which('pdftoppm'):
            Image = pytest.importorskip('PIL.Image')
            buf = io.BytesIO()
            Image.new('RGB', (40, 20), (0, 0, 255)).save(buf, 'PDF')
            bm = I.decode(buf.getvalue())
            assert bm.size[0] > 10 and bm.pixel(5, 5)[2] > 200

    def test_run_failures(self):
        assert I._run(['/nonexistent/tool']) is None
        assert I._run(['false']) is None if os.name != 'nt' else True


_ADAM7 = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
          (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))


def _adam7_png(bm):
    """An interlaced RGBA PNG of ``bm`` (filter 0 in every pass)."""
    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data +
                struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    raw = bytearray()
    for x0, y0, dx, dy in _ADAM7:
        for y in range(y0, bm.height, dy):
            xs = list(range(x0, bm.width, dx))
            if not xs:
                continue
            raw.append(0)
            for x in xs:
                raw += bytes(bm.pixel(x, y))
    ihdr = struct.pack('>IIBBBBB', bm.width, bm.height, 8, 6, 0, 0, 1)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b''))


class TestEdgeCases:
    def test_adam7(self, backend):
        for w, h in ((1, 1), (3, 2), (9, 11), (17, 5)):
            bm = _gradient(w, h, alpha=True)
            assert I.decode_png(_adam7_png(bm)).data == bm.data

    def test_pnm_errors_and_depths(self):
        for bad in (b'P6\nx y\n255\n', b'P6\n2 2\n255\n\x00',
                    b'P4\n9 2\n\x00', b'P3\n2 1\n255\n1 2 3'):
            with pytest.raises(I.ImageError):
                I.decode_pnm(bad)
        assert I.decode_pnm(b'P2\n1 1\n65535\n65535').pixel(0, 0)[0] == 255
        assert I.decode_pnm(b'P5\n1 1\n15\n\x0f').pixel(0, 0)[0] == 255

    def test_decode_misc(self, monkeypatch):
        monkeypatch.setenv('FLEXABLELIB_NO_PILLOW', '1')
        with pytest.raises(I.ImageError):
            I.decode(b'')
        png = I.encode_png(_gradient(2, 2))
        assert len(I.decode(png, all_frames=True)) == 1
        assert I.detect_format(b'II*\x00') == 'tiff'
        assert I.detect_format(b'\x00\x00\x01\x00') == 'ico'

    def test_flatten_mixed_alpha(self):
        bm = I.Bitmap(2, 1, bytes([10, 20, 30, 255, 200, 200, 200, 0]))
        flat = bm.flatten((1, 2, 3))
        assert flat.pixel(0, 0) == (10, 20, 30, 255)
        assert flat.pixel(1, 0) == (1, 2, 3, 255)

    @pytest.mark.parametrize('mode', ['half', 'quadrant', 'sextant',
                                      'braille', 'ascii'])
    def test_cells_transparency_and_flat(self, backend, mode):
        pw, ph = I.CELL_PIXELS[mode]
        w, h = pw * 3, ph
        clear = bytes(w * h * 4)
        solid = bytes([200, 10, 10, 255]) * (w * h)
        mixed = bytearray(solid)
        for i in range(0, len(mixed), 8):
            mixed[i + 3] = 0
        for data in (clear, solid, bytes(mixed)):
            for color in ('truecolor', 'none', '16'):
                lines = I.cells(data, w, h, mode, color, 128)
                assert len(lines) == 1
        line, = I.cells(clear, w, h, mode, 'none', 128)
        assert line.strip() == ''
