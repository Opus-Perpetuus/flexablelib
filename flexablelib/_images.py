"""
Image primitives: decode, scale, quantize and turn pictures into terminal
output (sixel bands, Unicode block and braille cells, ASCII art).

Everything here is pure Python and dependency-free. Pillow, when installed,
decodes the formats this module cannot (JPEG, WebP, TIFF ...) and SVG and
PDF use optional renderers (cairosvg / rsvg-convert, PyMuPDF / pdftoppm).
Without Pillow, PNG (every colour type, bit depth and interlacing), GIF
(every frame), BMP and the PPM/PGM/PBM family still load.

With ``flexablelib-speedups`` installed the hot loops -- ``resize``,
``quantize``, ``sixel_encode``, ``cells`` and ``unfilter`` -- run in C.
Both backends give byte-identical results (the test suite checks them on
random images). ``FLEXABLELIB_IMAGES=python`` forces the Python code and
:func:`use` switches at run time.
"""

import io
import os
import struct
import zlib

__all__ = ['Bitmap', 'ImageError', 'load', 'load_frames', 'decode',
           'resize', 'quantize', 'sixel_encode', 'cells', 'unfilter',
           'encode_png', 'rgb_to_256', 'rgb_to_16', 'BACKEND', 'use',
           'available', 'CELL_PIXELS', 'detect_format', 'scale']

# Pixels per cell for each text mode (columns, rows).
CELL_PIXELS = {'half': (1, 2), 'quadrant': (2, 2), 'sextant': (2, 3),
               'braille': (2, 4), 'ascii': (1, 2)}


class ImageError(ValueError):
    """An image that could not be read, with a reason people can read."""


class Bitmap(object):
    """``width`` x ``height`` pixels, ``data`` as RGBA bytes, row by row."""

    __slots__ = ('width', 'height', 'data', 'delay')

    def __init__(self, width, height, data, delay=0):
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise ImageError('imagen vacía ({0}×{1})'.format(width, height))
        if len(data) != width * height * 4:
            raise ImageError('datos de imagen incompletos')
        self.width = width
        self.height = height
        self.data = bytes(data)
        self.delay = delay

    @classmethod
    def from_rgb(cls, width, height, rgb):
        out = bytearray(width * height * 4)
        out[0::4] = rgb[0::3]
        out[1::4] = rgb[1::3]
        out[2::4] = rgb[2::3]
        out[3::4] = b'\xff' * (width * height)
        return cls(width, height, out)

    @property
    def size(self):
        return self.width, self.height

    def has_alpha(self):
        return self.data[3::4].count(255) != self.width * self.height

    def pixel(self, x, y):
        i = (y * self.width + x) * 4
        return tuple(self.data[i:i + 4])

    def crop(self, x, y, w, h):
        x, y = max(0, x), max(0, y)
        w, h = min(w, self.width - x), min(h, self.height - y)
        rows = []
        for row in range(y, y + h):
            start = (row * self.width + x) * 4
            rows.append(self.data[start:start + w * 4])
        return Bitmap(w, h, b''.join(rows))

    def flatten(self, background=(0, 0, 0)):
        """Alpha composited over ``background``; fully opaque result."""
        if not self.has_alpha():
            return self
        br, bg, bb = background
        src = self.data
        out = bytearray(len(src))
        for i in range(0, len(src), 4):
            a = src[i + 3]
            if a == 255:
                out[i:i + 4] = src[i:i + 4]
                continue
            na = 255 - a
            out[i] = (src[i] * a + br * na + 127) // 255
            out[i + 1] = (src[i + 1] * a + bg * na + 127) // 255
            out[i + 2] = (src[i + 2] * a + bb * na + 127) // 255
            out[i + 3] = 255
        return Bitmap(self.width, self.height, out)

    def grayscale(self):
        src = self.data
        out = bytearray(src)
        for i in range(0, len(src), 4):
            lum = (77 * src[i] + 150 * src[i + 1] + 29 * src[i + 2]) >> 8
            out[i] = out[i + 1] = out[i + 2] = lum
        return Bitmap(self.width, self.height, out)

    def __repr__(self):
        return 'Bitmap({0}x{1})'.format(self.width, self.height)


# +---------------------------------------------------------------------------+
# PNG

_PNG_SIG = b'\x89PNG\r\n\x1a\n'
_ADAM7 = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
          (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))


def _py_unfilter(data, rows, stride, bpp):
    """Undo PNG scanline filters: ``rows`` lines of ``stride`` bytes, each
    led by its filter byte. Returns the raw bytes without filter bytes."""
    out = bytearray(rows * stride)
    prev = bytearray(stride)
    pos = 0
    for row in range(rows):
        if pos + 1 + stride > len(data):
            raise ImageError('PNG truncado')
        ftype = data[pos]
        line = bytearray(data[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                if pa <= pb and pa <= pc:
                    pred = a
                elif pb <= pc:
                    pred = b
                else:
                    pred = c
                line[i] = (line[i] + pred) & 255
        elif ftype != 0:
            raise ImageError('PNG con filtro desconocido {0}'.format(ftype))
        out[row * stride:(row + 1) * stride] = line
        prev = line
    return bytes(out)


def _png_samples(raw, width, height, depth, channels):
    """Unpacked samples (one int per channel), 16-bit reduced to 8."""
    if depth == 8:
        return raw
    if depth == 16:
        return raw[0::2]
    per_byte = 8 // depth
    mask = (1 << depth) - 1
    stride = (width * channels * depth + 7) // 8
    out = bytearray(width * height * channels)
    k = 0
    n = width * channels
    for row in range(height):
        base = row * stride
        for i in range(n):
            byte = raw[base + i // per_byte]
            shift = 8 - depth * (i % per_byte + 1)
            out[k] = (byte >> shift) & mask
            k += 1
    return bytes(out)


def _png_to_rgba(samples, width, height, ctype, depth, palette, trns):
    n = width * height
    out = bytearray(n * 4)
    scale_ = 255 // ((1 << depth) - 1) if depth < 8 else 1
    if ctype == 3:
        pal = palette or b''
        alpha = trns or b''
        lut = []
        for i in range(256):
            rgb = pal[i * 3:i * 3 + 3]
            if len(rgb) < 3:
                rgb = b'\x00\x00\x00'
            a = alpha[i] if i < len(alpha) else 255
            lut.append(bytes(rgb) + bytes((a,)))
        return b''.join(lut[s] for s in samples)
    if ctype == 0:
        key = None
        if trns and len(trns) >= 2:
            key = struct.unpack('>H', trns[:2])[0]
            if depth == 16:
                key >>= 8
        g = bytes(min(255, s * scale_) for s in samples) if scale_ != 1 \
            else samples
        out[0::4] = g
        out[1::4] = g
        out[2::4] = g
        if key is None:
            out[3::4] = b'\xff' * n
        else:
            out[3::4] = bytes(0 if s == key else 255 for s in samples)
        return bytes(out)
    if ctype == 4:
        out[0::4] = samples[0::2]
        out[1::4] = samples[0::2]
        out[2::4] = samples[0::2]
        out[3::4] = samples[1::2]
        return bytes(out)
    if ctype == 2:
        out[0::4] = samples[0::3]
        out[1::4] = samples[1::3]
        out[2::4] = samples[2::3]
        out[3::4] = b'\xff' * n
        if trns and len(trns) >= 6:
            key = struct.unpack('>HHH', trns[:6])
            if depth == 16:
                key = tuple(k >> 8 for k in key)
            for i in range(n):
                if (samples[i * 3], samples[i * 3 + 1],
                        samples[i * 3 + 2]) == key:
                    out[i * 4 + 3] = 0
        return bytes(out)
    return bytes(samples)


def decode_png(data):
    if not data.startswith(_PNG_SIG):
        raise ImageError('no es un PNG')
    pos = 8
    header = None
    palette = trns = None
    idat = []
    while pos + 8 <= len(data):
        length, kind = struct.unpack('>I4s', data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', body[:13])
        elif kind == b'PLTE':
            palette = body
        elif kind == b'tRNS':
            trns = body
        elif kind == b'IDAT':
            idat.append(body)
        elif kind == b'IEND':
            break
    if header is None or not idat:
        raise ImageError('PNG sin cabecera o sin datos')
    width, height, depth, ctype, _comp, _filt, interlace = header
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None or depth not in (1, 2, 4, 8, 16):
        raise ImageError('PNG no soportado')
    try:
        raw = zlib.decompress(b''.join(idat))
    except zlib.error:
        raise ImageError('PNG dañado')
    bpp = max(1, channels * depth // 8)
    if not interlace:
        stride = (width * channels * depth + 7) // 8
        pixels = unfilter(raw, height, stride, bpp)
        samples = _png_samples(pixels, width, height, depth, channels)
        return Bitmap(width, height, _png_to_rgba(
            samples, width, height, ctype, depth, palette, trns))
    out = bytearray(width * height * 4)
    pos = 0
    for x0, y0, dx, dy in _ADAM7:
        pw = (width - x0 + dx - 1) // dx
        ph = (height - y0 + dy - 1) // dy
        if pw <= 0 or ph <= 0:
            continue
        stride = (pw * channels * depth + 7) // 8
        size = ph * (stride + 1)
        pixels = unfilter(raw[pos:pos + size], ph, stride, bpp)
        pos += size
        samples = _png_samples(pixels, pw, ph, depth, channels)
        rgba = _png_to_rgba(samples, pw, ph, ctype, depth, palette, trns)
        for j in range(ph):
            for i in range(pw):
                src = (j * pw + i) * 4
                dst = ((y0 + j * dy) * width + x0 + i * dx) * 4
                out[dst:dst + 4] = rgba[src:src + 4]
    return Bitmap(width, height, out)


def encode_png(bitmap, level=6):
    """The bitmap as PNG bytes (RGBA, or RGB when fully opaque)."""
    w, h = bitmap.width, bitmap.height
    src = bitmap.data
    if bitmap.has_alpha():
        stride, ctype, body = w * 4, 6, src
    else:
        rgb = bytearray(w * h * 3)
        rgb[0::3] = src[0::4]
        rgb[1::3] = src[1::4]
        rgb[2::3] = src[2::4]
        stride, ctype, body = w * 3, 2, bytes(rgb)
    raw = b''.join(b'\x00' + body[r * stride:(r + 1) * stride]
                   for r in range(h))

    def chunk(kind, payload):
        return (struct.pack('>I', len(payload)) + kind + payload +
                struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))
    return (_PNG_SIG + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ctype,
                                                  0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, level)) + chunk(b'IEND', b''))


# +---------------------------------------------------------------------------+
# PPM / PGM / PBM

def _pnm_tokens(data, count, pos):
    tokens = []
    n = len(data)
    while len(tokens) < count and pos < n:
        c = data[pos:pos + 1]
        if c == b'#':
            while pos < n and data[pos:pos + 1] not in (b'\n', b'\r'):
                pos += 1
        elif c.isspace():
            pos += 1
        else:
            start = pos
            while pos < n and not data[pos:pos + 1].isspace() and \
                    data[pos:pos + 1] != b'#':
                pos += 1
            tokens.append(int(data[start:pos]))
    return tokens, pos


def decode_pnm(data):
    magic = data[:2]
    if magic not in (b'P1', b'P2', b'P3', b'P4', b'P5', b'P6'):
        raise ImageError('no es PPM/PGM/PBM')
    bitmap = magic in (b'P1', b'P4')
    try:
        head, pos = _pnm_tokens(data, 2 if bitmap else 3, 2)
        width, height = head[0], head[1]
        maxval = 1 if bitmap else head[2]
    except (ValueError, IndexError):
        raise ImageError('cabecera PNM dañada')
    n = width * height
    channels = 3 if magic in (b'P3', b'P6') else 1
    if magic in (b'P4', b'P5', b'P6'):
        pos += 1
        if magic == b'P4':
            stride = (width + 7) // 8
            raw = data[pos:pos + stride * height]
            if len(raw) < stride * height:
                raise ImageError('PNM truncado')
            values = bytearray(n)
            for y in range(height):
                for x in range(width):
                    byte = raw[y * stride + x // 8]
                    values[y * width + x] = \
                        0 if (byte >> (7 - x % 8)) & 1 else 255
        else:
            wide = maxval > 255
            size = n * channels * (2 if wide else 1)
            raw = data[pos:pos + size]
            if len(raw) < size:
                raise ImageError('PNM truncado')
            if wide:
                raw = raw[0::2]
                maxval >>= 8
            values = raw if maxval == 255 else bytes(
                min(255, v * 255 // max(1, maxval)) for v in raw)
    else:
        nums, pos = _pnm_tokens(data, n * channels, pos)
        if len(nums) < n * channels:
            raise ImageError('PNM truncado')
        if bitmap:
            values = bytes(0 if v else 255 for v in nums)
        else:
            values = bytes(min(255, v * 255 // max(1, maxval)) for v in nums)
    if channels == 3:
        return Bitmap.from_rgb(width, height, values)
    out = bytearray(n * 4)
    out[0::4] = values
    out[1::4] = values
    out[2::4] = values
    out[3::4] = b'\xff' * n
    return Bitmap(width, height, out)


# +---------------------------------------------------------------------------+
# BMP

def _mask_shift(mask):
    if not mask:
        return 0, 0
    s = 0
    while not (mask >> s) & 1:
        s += 1
    n = 0
    while (mask >> (s + n)) & 1:
        n += 1
    return s, n


def decode_bmp(data):
    if data[:2] != b'BM' or len(data) < 54:
        raise ImageError('no es BMP')
    offset = struct.unpack('<I', data[10:14])[0]
    header = struct.unpack('<I', data[14:18])[0]
    width, height, _planes, bits, compression = struct.unpack(
        '<iiHHI', data[18:34])
    top_down = height < 0
    height = abs(height)
    colors = struct.unpack('<I', data[46:50])[0] if header >= 40 else 0
    masks = None
    if compression in (3, 6):
        masks = struct.unpack('<III', data[54:66])
        alpha_mask = struct.unpack('<I', data[66:70])[0] if header >= 56 \
            else 0
        masks = masks + (alpha_mask,)
    elif compression != 0:
        raise ImageError('BMP comprimido (RLE) necesita Pillow')
    palette = []
    if bits <= 8:
        count = colors or (1 << bits)
        start = 14 + header
        for i in range(count):
            b, g, r = data[start + i * 4:start + i * 4 + 3]
            palette.append((r, g, b))
    stride = ((width * bits + 31) // 32) * 4
    out = bytearray(width * height * 4)
    shifts = [_mask_shift(m) for m in masks] if masks else None
    for row in range(height):
        src_row = row if top_down else height - 1 - row
        base = offset + src_row * stride
        line = data[base:base + stride]
        if len(line) < stride:
            raise ImageError('BMP truncado')
        for x in range(width):
            a = 255
            if bits in (16, 32) and masks:
                size = bits // 8
                v = int.from_bytes(line[x * size:x * size + size], 'little')
                chans = []
                for (s, n), m in zip(shifts, masks):
                    chans.append(((v & m) >> s) * 255 // ((1 << n) - 1)
                                 if m and n else 255)
                r, g, b, a = chans
            elif bits == 24:
                b, g, r = line[x * 3:x * 3 + 3]
            elif bits == 32:
                b, g, r = line[x * 4:x * 4 + 3]
            elif bits == 16:
                v = line[x * 2] | (line[x * 2 + 1] << 8)
                r = ((v >> 10) & 31) * 255 // 31
                g = ((v >> 5) & 31) * 255 // 31
                b = (v & 31) * 255 // 31
            elif bits in (1, 2, 4, 8):
                per = 8 // bits
                byte = line[x // per]
                idx = (byte >> (8 - bits * (x % per + 1))) & ((1 << bits) - 1)
                r, g, b = palette[idx] if idx < len(palette) else (0, 0, 0)
            else:
                raise ImageError('BMP de {0} bits'.format(bits))
            dst = (row * width + x) * 4
            out[dst:dst + 4] = bytes((r, g, b, a))
    return Bitmap(width, height, out)


# +---------------------------------------------------------------------------+
# GIF

def _lzw(data, min_size, count):
    clear = 1 << min_size
    end = clear + 1
    size = min_size + 1
    table = [bytes((i,)) for i in range(clear)] + [b'', b'']
    out = bytearray()
    prev = None
    bitpos = 0
    nbits = len(data) * 8
    value = int.from_bytes(data, 'little')
    while bitpos + size <= nbits and len(out) < count:
        code = (value >> bitpos) & ((1 << size) - 1)
        bitpos += size
        if code == clear:
            size = min_size + 1
            del table[clear + 2:]
            prev = None
            continue
        if code == end:
            break
        if code < len(table):
            entry = table[code]
            if prev is not None and len(table) < 4096:
                table.append(prev + entry[:1])
        elif prev is not None and code == len(table):
            entry = prev + prev[:1]
            table.append(entry)
        else:
            raise ImageError('GIF dañado')
        out += entry
        prev = entry
        if len(table) == (1 << size) and size < 12:
            size += 1
    return bytes(out[:count])


def decode_gif(data, all_frames=False):
    if data[:6] not in (b'GIF87a', b'GIF89a'):
        raise ImageError('no es GIF')
    width, height, flags = struct.unpack('<HHB', data[6:11])
    pos = 13
    global_table = None
    if flags & 0x80:
        n = 2 << (flags & 7)
        global_table = data[pos:pos + 3 * n]
        pos += 3 * n
    canvas = bytearray(width * height * 4)
    frames = []
    transparent = None
    delay = disposal = 0
    while pos < len(data):
        block = data[pos]
        pos += 1
        if block == 0x3B:
            break
        if block == 0x21:
            label = data[pos]
            pos += 1
            if label == 0xF9 and data[pos] >= 4:
                packed = data[pos + 1]
                delay = struct.unpack('<H', data[pos + 2:pos + 4])[0] * 10
                transparent = data[pos + 4] if packed & 1 else None
                disposal = (packed >> 2) & 7
            while pos < len(data) and data[pos]:
                pos += data[pos] + 1
            pos += 1
            continue
        if block != 0x2C:
            raise ImageError('GIF dañado')
        x0, y0, fw, fh, fflags = struct.unpack('<HHHHB', data[pos:pos + 9])
        pos += 9
        table = global_table
        if fflags & 0x80:
            n = 2 << (fflags & 7)
            table = data[pos:pos + 3 * n]
            pos += 3 * n
        if table is None:
            table = bytes(b for i in range(256) for b in (i, i, i))
        min_size = data[pos]
        pos += 1
        chunks = []
        while pos < len(data) and data[pos]:
            chunks.append(data[pos + 1:pos + 1 + data[pos]])
            pos += data[pos] + 1
        pos += 1
        indices = _lzw(b''.join(chunks), min_size, fw * fh)
        indices += bytes(fw * fh - len(indices))
        rows = list(range(fh))
        if fflags & 0x40:
            rows = (list(range(0, fh, 8)) + list(range(4, fh, 8)) +
                    list(range(2, fh, 4)) + list(range(1, fh, 2)))
        before = bytes(canvas) if disposal == 3 else None
        for k, row in enumerate(rows):
            y = y0 + row
            if y >= height:
                continue
            for i in range(fw):
                x = x0 + i
                if x >= width:
                    continue
                idx = indices[k * fw + i]
                if idx == transparent or idx * 3 + 3 > len(table):
                    continue
                d = (y * width + x) * 4
                canvas[d:d + 3] = table[idx * 3:idx * 3 + 3]
                canvas[d + 3] = 255
        frames.append(Bitmap(width, height, bytes(canvas), delay))
        if not all_frames:
            break
        if disposal == 2:
            for row in range(y0, min(height, y0 + fh)):
                s = (row * width + x0) * 4
                e = (row * width + min(width, x0 + fw)) * 4
                canvas[s:e] = bytes(e - s)
        elif disposal == 3 and before is not None:
            canvas = bytearray(before)
        transparent = None
        delay = disposal = 0
    if not frames:
        raise ImageError('GIF sin imágenes')
    return frames if all_frames else frames[0]


# +---------------------------------------------------------------------------+
# Loading

def detect_format(head):
    """``'png'``, ``'gif'``, ``'jpeg'``, ``'webp'``, ``'bmp'``, ``'pnm'``,
    ``'svg'``, ``'pdf'``, ``'tiff'``, ``'ico'`` or ``None``."""
    if head.startswith(_PNG_SIG):
        return 'png'
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if head[:3] == b'\xff\xd8\xff':
        return 'jpeg'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'webp'
    if head[:2] == b'BM':
        return 'bmp'
    if head[:2] in (b'P1', b'P2', b'P3', b'P4', b'P5', b'P6') and \
            head[2:3].isspace():
        return 'pnm'
    if head[:5] == b'%PDF-':
        return 'pdf'
    if head[:4] in (b'II*\x00', b'MM\x00*'):
        return 'tiff'
    if head[:4] == b'\x00\x00\x01\x00':
        return 'ico'
    if b'<svg' in head[:2048].lower():
        return 'svg'
    return None


_PURE = {'png': decode_png, 'gif': decode_gif, 'bmp': decode_bmp,
         'pnm': decode_pnm}


def _pillow():
    if os.environ.get('FLEXABLELIB_NO_PILLOW'):
        return None
    try:
        from PIL import Image as PILImage
    except ImportError:
        return None
    return PILImage


def _from_pillow(img, all_frames=False):
    count = getattr(img, 'n_frames', 1) if all_frames else 1
    frames = []
    for i in range(count):
        if count > 1:
            img.seek(i)
        frame = img
        if i == 0 and count == 1:
            try:
                from PIL import ImageOps
                frame = ImageOps.exif_transpose(img)
            except Exception:   # pragma: no cover - old Pillow
                frame = img
        frame = frame.convert('RGBA')
        frames.append(Bitmap(frame.width, frame.height, frame.tobytes(),
                             img.info.get('duration', 0) or 0))
    return frames if all_frames else frames[0]


def _run(cmd, data=None, timeout=20):
    import subprocess
    try:
        proc = subprocess.run(cmd, input=data, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 and proc.stdout else None


def _which(name):
    import shutil
    return shutil.which(name)


def render_svg(data, width=None):
    """PNG bytes of an SVG, through cairosvg or ``rsvg-convert``."""
    try:
        import cairosvg
    except (ImportError, OSError):      # OSError: no cairo library
        cairosvg = None
    if cairosvg is not None:
        try:
            kw = {'output_width': width} if width else {}
            return cairosvg.svg2png(bytestring=data, **kw)
        except Exception as error:
            raise ImageError('SVG dañado: {0}'.format(error))
    if _which('rsvg-convert'):
        cmd = ['rsvg-convert', '-f', 'png']
        if width:
            cmd += ['-w', str(width)]
        out = _run(cmd, data)
        if out:
            return out
    raise ImageError('SVG necesita cairosvg o rsvg-convert')


def render_pdf(data, dpi=96):
    """PNG bytes of a PDF's first page, through PyMuPDF or ``pdftoppm``."""
    try:
        import fitz
    except ImportError:
        fitz = None
    if fitz is not None:
        try:
            doc = fitz.open(stream=data, filetype='pdf')
            return doc.load_page(0).get_pixmap(dpi=dpi).tobytes('png')
        except Exception as error:
            raise ImageError('PDF dañado: {0}'.format(error))
    if _which('pdftoppm'):
        out = _run(['pdftoppm', '-png', '-f', '1', '-l', '1', '-r', str(dpi),
                    '-singlefile', '-', '-'], data)
        if out:
            return out
    raise ImageError('PDF necesita PyMuPDF o pdftoppm (poppler)')


def read_source(source, timeout=5.0, max_bytes=64 * 1024 * 1024):
    """``(bytes, name)`` for a path, URL, bytes or file object."""
    if isinstance(source, (bytes, bytearray, memoryview)):
        return bytes(source), None
    if hasattr(source, 'read'):
        return source.read(), getattr(source, 'name', None)
    path = os.fspath(source)
    if path.startswith(('http://', 'https://')):
        from urllib.request import Request, urlopen
        try:
            req = Request(path, headers={'User-Agent': 'flexablelib'})
            with urlopen(req, timeout=timeout) as resp:
                data = resp.read(max_bytes + 1)
        except Exception as error:
            raise ImageError('no se pudo descargar ({0})'.format(error))
        if len(data) > max_bytes:
            raise ImageError('imagen demasiado grande')
        return data, path
    if path.startswith('file://'):
        from urllib.parse import unquote, urlparse
        path = unquote(urlparse(path).path)
        if os.name == 'nt' and path[:1] == '/' and path[2:3] == ':':
            path = path[1:]
    try:
        with open(path, 'rb') as handle:
            data = handle.read(max_bytes + 1)
    except FileNotFoundError:
        raise ImageError('no existe el archivo')
    except IsADirectoryError:
        raise ImageError('es una carpeta')
    except OSError as error:
        raise ImageError(error.strerror or str(error))
    if len(data) > max_bytes:
        raise ImageError('imagen demasiado grande')
    return data, path


def decode(data, all_frames=False):
    """A :class:`Bitmap` (or every frame) from encoded bytes."""
    if not data:
        raise ImageError('archivo vacío')
    kind = detect_format(data[:2048])
    if kind == 'svg':
        data, kind = render_svg(data), 'png'
    elif kind == 'pdf':
        data, kind = render_pdf(data), 'png'
    PILImage = _pillow()
    if PILImage is not None:
        try:
            img = PILImage.open(io.BytesIO(data))
            img.load()
            return _from_pillow(img, all_frames)
        except Exception as error:
            if kind not in _PURE:
                raise ImageError('no se pudo leer la imagen ({0})'.format(
                    error))
    if kind in _PURE:
        if kind == 'gif':
            return decode_gif(data, all_frames)
        bitmap = _PURE[kind](data)
        return [bitmap] if all_frames else bitmap
    if kind is None:
        raise ImageError('formato de imagen desconocido')
    raise ImageError('{0} necesita Pillow (pip install "flexablelib[images]")'
                     .format(kind.upper()))


def load(source, **kw):
    """A :class:`Bitmap` from a path, URL, bytes, file object, ``Bitmap``
    or Pillow image (the first frame of animations)."""
    if isinstance(source, Bitmap):
        return source
    if hasattr(source, 'convert') and hasattr(source, 'tobytes'):
        return _from_pillow(source)
    data, _name = read_source(source, **kw)
    return decode(data)


def load_frames(source, **kw):
    """Every frame (GIF and, with Pillow, animated WebP/PNG)."""
    if isinstance(source, Bitmap):
        return [source]
    data, _name = read_source(source, **kw)
    return decode(data, all_frames=True)


# +---------------------------------------------------------------------------+
# Colour helpers

_CUBE = (0, 95, 135, 175, 215, 255)
ANSI16 = ((0, 0, 0), (205, 0, 0), (0, 205, 0), (205, 205, 0), (0, 0, 238),
          (205, 0, 205), (0, 205, 205), (229, 229, 229), (127, 127, 127),
          (255, 0, 0), (0, 255, 0), (255, 255, 0), (92, 92, 255),
          (255, 0, 255), (0, 255, 255), (255, 255, 255))


def _cube_index(v):
    if v < 48:
        return 0
    if v < 115:
        return 1
    return (v - 35) // 40


def rgb_to_256(r, g, b):
    """The nearest xterm 256-colour index (cube 16-231 or grey 232-255)."""
    ri, gi, bi = _cube_index(r), _cube_index(g), _cube_index(b)
    cr, cg, cb = _CUBE[ri], _CUBE[gi], _CUBE[bi]
    avg = (r + g + b) // 3
    gray = 23 if avg > 238 else max(0, (avg - 3) // 10)
    gv = 8 + 10 * gray
    dc = (cr - r) ** 2 + (cg - g) ** 2 + (cb - b) ** 2
    dg = (gv - r) ** 2 + (gv - g) ** 2 + (gv - b) ** 2
    return 232 + gray if dg < dc else 16 + 36 * ri + 6 * gi + bi


def rgb_to_16(r, g, b):
    """The nearest of the 16 ANSI colours (0-15)."""
    best = 0
    dist = 1 << 30
    for i, (cr, cg, cb) in enumerate(ANSI16):
        d = (cr - r) ** 2 + (cg - g) ** 2 + (cb - b) ** 2
        if d < dist:
            best, dist = i, d
    return best


# +---------------------------------------------------------------------------+
# Pure-Python reference implementations of the accelerated primitives

def _spans(size, new):
    return [(o * size // new, max(o * size // new + 1,
                                   ((o + 1) * size + new - 1) // new))
            for o in range(new)]


def _py_resize(data, width, height, new_w, new_h):
    """Area-average resampling with alpha weighting (exact integers):
    every output pixel averages the source box it covers; when enlarging,
    each box is one source pixel."""
    if new_w <= 0 or new_h <= 0 or width <= 0 or height <= 0:
        raise ValueError('sizes must be positive')
    if len(data) < width * height * 4:
        raise ValueError('data shorter than width * height * 4')
    xs = _spans(width, new_w)
    ys = _spans(height, new_h)
    rows = {}

    def hrow(y):
        line = rows.get(y)
        if line is None:
            base = y * width * 4
            line = []
            for x0, x1 in xs:
                sr = sg = sb = sa = 0
                for i in range(base + x0 * 4, base + x1 * 4, 4):
                    a = data[i + 3]
                    sr += data[i] * a
                    sg += data[i + 1] * a
                    sb += data[i + 2] * a
                    sa += a
                line.append((sr, sg, sb, sa))
            rows[y] = line
        return line
    out = bytearray(new_w * new_h * 4)
    k = 0
    for y0, y1 in ys:
        lines = [hrow(y) for y in range(y0, y1)]
        for ox in range(new_w):
            sr = sg = sb = sa = 0
            for line in lines:
                r, g, b, a = line[ox]
                sr += r
                sg += g
                sb += b
                sa += a
            n = (y1 - y0) * (xs[ox][1] - xs[ox][0])
            if sa:
                out[k] = (sr + sa // 2) // sa
                out[k + 1] = (sg + sa // 2) // sa
                out[k + 2] = (sb + sa // 2) // sa
            out[k + 3] = (sa + n // 2) // n
            k += 4
        for y in range(y0, y1 - 1):
            rows.pop(y, None)
    return bytes(out)


def _box_range(box, shift):
    lo = hi = (box[0] >> shift) & 31
    for k in box:
        v = (k >> shift) & 31
        if v < lo:
            lo = v
        elif v > hi:
            hi = v
    return hi - lo


def _py_quantize(data, width, height, colors, alpha_threshold):
    """
    Median-cut palette of at most ``colors`` (1-255) entries over a 5-bit
    per channel histogram. Returns ``(palette_bytes, indices)``: three bytes
    per entry and one index per pixel; with ``alpha_threshold`` > 0, pixels
    whose alpha is below it get index 255 (transparent).
    """
    colors = max(1, min(255, colors))
    n = width * height
    count = [0] * 32768
    sums = [0] * (32768 * 3)
    keys = [0] * n
    for p in range(n):
        i = p * 4
        if alpha_threshold and data[i + 3] < alpha_threshold:
            keys[p] = -1
            continue
        r, g, b = data[i], data[i + 1], data[i + 2]
        key = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)
        keys[p] = key
        count[key] += 1
        sums[key * 3] += r
        sums[key * 3 + 1] += g
        sums[key * 3 + 2] += b
    used = [k for k in range(32768) if count[k]]
    if not used:
        return b'\x00\x00\x00', bytes([255]) * n
    boxes = [used]
    totals = [sum(count[k] for k in used)]
    while len(boxes) < colors:
        best = -1
        best_range = best_count = -1
        for bi, box in enumerate(boxes):
            if len(box) < 2:
                continue
            rng = max(_box_range(box, 10), _box_range(box, 5),
                      _box_range(box, 0))
            if rng > best_range or (rng == best_range and
                                    totals[bi] > best_count):
                best, best_range, best_count = bi, rng, totals[bi]
        if best < 0:
            break
        box = boxes[best]
        ranges = [_box_range(box, 10), _box_range(box, 5), _box_range(box, 0)]
        shift = (10, 5, 0)[ranges.index(max(ranges))]
        box = sorted(box, key=lambda k: (((k >> shift) & 31) << 15) | k)
        total = totals[best]
        acc = 0
        cut = 1
        for j, k in enumerate(box):
            acc += count[k]
            if acc * 2 >= total:
                cut = j + 1
                break
        cut = max(1, min(len(box) - 1, cut))
        left, right = box[:cut], box[cut:]
        lt = sum(count[k] for k in left)
        boxes[best:best + 1] = [left, right]
        totals[best:best + 1] = [lt, total - lt]
    palette = []
    for box, c in zip(boxes, totals):
        palette.append(tuple(
            (sum(sums[k * 3 + ch] for k in box) + c // 2) // c
            for ch in range(3)))
    lut = {}
    for k in used:
        c = count[k]
        r = (sums[k * 3] + c // 2) // c
        g = (sums[k * 3 + 1] + c // 2) // c
        b = (sums[k * 3 + 2] + c // 2) // c
        best = 0
        dist = 1 << 30
        for pi, (pr, pg, pb) in enumerate(palette):
            d = (pr - r) ** 2 + (pg - g) ** 2 + (pb - b) ** 2
            if d < dist:
                best, dist = pi, d
        lut[k] = best
    lut[-1] = 255
    return (bytes(b for rgb in palette for b in rgb),
            bytes(lut[k] for k in keys))


_SIXEL_PCT = [(v * 100 + 127) // 255 for v in range(256)]


def _py_sixel_encode(indices, width, height, palette):
    """The DCS sixel sequence for an indexed image (255 = transparent)."""
    out = ['\x1bP0;1;0q"1;1;{0};{1}'.format(width, height)]
    ncolors = len(palette) // 3
    for i in range(ncolors):
        out.append('#{0};2;{1};{2};{3}'.format(
            i, _SIXEL_PCT[palette[i * 3]], _SIXEL_PCT[palette[i * 3 + 1]],
            _SIXEL_PCT[palette[i * 3 + 2]]))
    for top in range(0, height, 6):
        band = min(6, height - top)
        present = set()
        for y in range(top, top + band):
            present.update(indices[y * width:(y + 1) * width])
        present.discard(255)
        first = True
        for color in sorted(present):
            if color >= ncolors:
                continue
            bits = [0] * width
            for dy in range(band):
                row = (top + dy) * width
                bit = 1 << dy
                for x in range(width):
                    if indices[row + x] == color:
                        bits[x] |= bit
            last = width
            while last > 0 and not bits[last - 1]:
                last -= 1
            if not first:
                out.append('$')
            first = False
            out.append('#{0}'.format(color))
            x = 0
            while x < last:
                v = bits[x]
                run = 1
                while x + run < last and bits[x + run] == v:
                    run += 1
                ch = chr(63 + v)
                out.append('!{0}{1}'.format(run, ch) if run > 3 else ch * run)
                x += run
        if top + 6 < height:
            out.append('-')
    out.append('\x1b\\')
    return ''.join(out)


QUADRANTS = ' ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█'
ASCII_RAMP = ' .:-=+*#%@'
_BAYER = (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)
# Dot bit for pixel k = dy * 2 + dx in a 2x4 braille cell.
_BRAILLE_BITS = (0x01, 0x08, 0x02, 0x10, 0x04, 0x20, 0x40, 0x80)


def sextant(mask):
    """The character for a 2x3 cell whose set pixels are ``mask`` bits
    (bit k = row k // 2, column k % 2)."""
    if mask == 0:
        return ' '
    if mask == 63:
        return '█'
    if mask == 21:
        return '▌'
    if mask == 42:
        return '▐'
    cp = 0x1FB00 + mask - 1
    if mask > 21:
        cp -= 1
    if mask > 42:
        cp -= 1
    return chr(cp)


def _sgr(fg, bg, color):
    """SGR for a (fg, bg) pair of RGB tuples or None (terminal default)."""
    parts = []
    for rgb, base in ((fg, 38), (bg, 48)):
        if rgb is None:
            parts.append(str(base + 1))
        elif color == 'truecolor':
            parts.append('{0};2;{1};{2};{3}'.format(base, *rgb))
        elif color == '256':
            parts.append('{0};5;{1}'.format(base, rgb_to_256(*rgb)))
        else:
            idx = rgb_to_16(*rgb)
            parts.append(str((base - 8 if idx < 8 else base + 52) +
                             (idx & 7)))
    return '\x1b[' + ';'.join(parts) + 'm'


def _mean(pixels):
    n = len(pixels)
    return ((sum(p[0] for p in pixels) + n // 2) // n,
            (sum(p[1] for p in pixels) + n // 2) // n,
            (sum(p[2] for p in pixels) + n // 2) // n)


def _lum(p):
    return (77 * p[0] + 150 * p[1] + 29 * p[2]) >> 8


def _cell(px, mode, mono, gx, gy, pw):
    """(char, fg, bg) for one cell's pixels (None = transparent)."""
    if mode == 'half':
        top, bottom = px
        if top is None and bottom is None:
            return ' ', None, None
        if bottom is None:
            return '▀', top, None
        if top is None:
            return '▄', bottom, None
        if mono:
            return ' ▄▀█'[(_lum(top) >= 128) * 2 + (_lum(bottom) >= 128)], \
                None, None
        if top == bottom:
            return '█', top, None
        return '▀', top, bottom
    if mode == 'ascii':
        solid = [p for p in px if p is not None]
        if not solid:
            return ' ', None, None
        fg = _mean(solid)
        ch = ASCII_RAMP[_lum(fg) * len(ASCII_RAMP) // 256]
        return ch, (None if ch == ' ' or mono else fg), None
    lums = [None if p is None else _lum(p) for p in px]
    solid = [v for v in lums if v is not None]
    fg = bg = None
    on = [False] * len(px)
    if solid:
        if mono:
            for k, v in enumerate(lums):
                if v is not None and v * 16 > \
                        _BAYER[((gy + k // pw) & 3) * 4 + ((gx + k % pw) & 3)] \
                        * 256 + 128:
                    on[k] = True
        else:
            if len(solid) < len(lums):
                on = [v is not None for v in lums]
            elif mode == 'braille':
                mean = sum(solid) // len(solid)
                on = [v >= mean for v in lums]
            else:
                mean = (sum(solid) + len(solid) // 2) // len(solid)
                on = [v > mean for v in lums]
                if not any(on):
                    on = [True] * len(lums)
            ons = [px[k] for k in range(len(px)) if on[k]]
            offs = [px[k] for k in range(len(px))
                    if not on[k] and px[k] is not None]
            if ons:
                fg = _mean(ons)
            if offs and mode != 'braille':
                bg = _mean(offs)
    mask = 0
    for k, flag in enumerate(on):
        if flag:
            mask |= 1 << k
    if mode == 'braille':
        bits = 0
        for k in range(8):
            if mask & (1 << k):
                bits |= _BRAILLE_BITS[k]
        ch = chr(0x2800 + bits) if bits else ' '
    elif mode == 'quadrant':
        ch = QUADRANTS[mask]
    else:
        ch = sextant(mask)
    if ch == ' ':
        fg = None
    elif ch == '█':
        bg = None
    return ch, fg, bg


def _py_cells(data, width, height, mode, color, threshold):
    """
    Text cells for an image already scaled to the mode's pixel grid
    (:data:`CELL_PIXELS`): ``mode`` is ``'half'``, ``'quadrant'``,
    ``'sextant'``, ``'braille'`` or ``'ascii'``; ``color`` is
    ``'truecolor'``, ``'256'``, ``'16'`` or ``'none'``. Pixels with alpha
    below ``threshold`` are transparent (terminal background). Returns one
    string per text row; colours reset at the end of each row.
    """
    if mode not in CELL_PIXELS:
        raise ValueError('unknown mode {0!r}'.format(mode))
    if color not in ('truecolor', '256', '16', 'none'):
        raise ValueError('unknown colour level {0!r}'.format(color))
    if len(data) < width * height * 4:
        raise ValueError('data shorter than width * height * 4')
    pw, ph = CELL_PIXELS[mode]
    cols = width // pw
    rows = height // ph
    mono = color == 'none'
    lines = []
    for row in range(rows):
        parts = []
        current = (None, None)
        for col in range(cols):
            px = []
            for dy in range(ph):
                base = ((row * ph + dy) * width + col * pw) * 4
                for dx in range(pw):
                    i = base + dx * 4
                    px.append(None if data[i + 3] < threshold else
                              (data[i], data[i + 1], data[i + 2]))
            ch, fg, bg = _cell(px, mode, mono, col * pw, row * ph, pw)
            if not mono and (fg, bg) != current:
                parts.append('\x1b[0m' if fg is None and bg is None
                             else _sgr(fg, bg, color))
                current = (fg, bg)
            parts.append(ch)
        if current != (None, None):
            parts.append('\x1b[0m')
        lines.append(''.join(parts))
    return lines


_PYTHON = {'resize': _py_resize, 'quantize': _py_quantize,
           'sixel_encode': _py_sixel_encode, 'cells': _py_cells,
           'unfilter': _py_unfilter}


def _load_c():
    try:
        from flexablelib_speedups import _images as mod
    except ImportError:
        return None
    return mod


_C = _load_c()
ACCELERATED = _C is not None
BACKEND = 'python'
resize = quantize = sixel_encode = cells = unfilter = None


def available():
    """Backends that can be used: always ``'python'``, ``'c'`` when built."""
    return ['c', 'python'] if _C is not None else ['python']


def use(backend='auto'):
    """Switch backends: ``'c'``, ``'python'`` or ``'auto'``."""
    global BACKEND
    if backend == 'auto':
        backend = 'c' if _C is not None else 'python'
    if backend == 'c' and _C is None:
        raise RuntimeError('flexablelib-speedups is not installed')
    for name in _PYTHON:
        globals()[name] = getattr(_C, name) if backend == 'c' \
            else _PYTHON[name]
    BACKEND = backend
    return backend


use('python' if os.environ.get('FLEXABLELIB_IMAGES', '').lower() == 'python'
    else 'auto')


def scale(bitmap, width, height):
    """A resized :class:`Bitmap`."""
    if (width, height) == (bitmap.width, bitmap.height):
        return bitmap
    return Bitmap(width, height, resize(bitmap.data, bitmap.width,
                                        bitmap.height, width, height))
