/*
 * flexablelib_speedups._images -- C versions of the image primitives in
 * flexablelib/_images.py: PNG unfiltering, area-average resizing, median-cut
 * quantization, the sixel encoder and the Unicode/ASCII cell renderer.
 *
 * Every function gives exactly the result of its Python reference (integer
 * arithmetic only, same tie-breaking); tests/test_v350_images.py compares
 * both on random images.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <string.h>

typedef long long i64;

/* ------------------------------------------------------------------ */
/* growable byte buffer                                                */

typedef struct { char *p; Py_ssize_t n, cap; } Buf;

static int buf_grow(Buf *b, Py_ssize_t extra)
{
    if (b->n + extra <= b->cap) return 0;
    Py_ssize_t cap = b->cap ? b->cap : 256;
    while (cap < b->n + extra) cap *= 2;
    char *p = (char *)realloc(b->p, (size_t)cap);
    if (!p) { PyErr_NoMemory(); return -1; }
    b->p = p; b->cap = cap;
    return 0;
}

static int buf_put(Buf *b, const char *s, Py_ssize_t len)
{
    if (buf_grow(b, len) < 0) return -1;
    memcpy(b->p + b->n, s, (size_t)len);
    b->n += len;
    return 0;
}

static int buf_str(Buf *b, const char *s) { return buf_put(b, s, (Py_ssize_t)strlen(s)); }

static int buf_cp(Buf *b, unsigned int cp)
{
    char t[4]; int n;
    if (cp < 0x80) { t[0] = (char)cp; n = 1; }
    else if (cp < 0x800) { t[0] = (char)(0xC0 | (cp >> 6)); t[1] = (char)(0x80 | (cp & 63)); n = 2; }
    else if (cp < 0x10000) { t[0] = (char)(0xE0 | (cp >> 12)); t[1] = (char)(0x80 | ((cp >> 6) & 63));
        t[2] = (char)(0x80 | (cp & 63)); n = 3; }
    else { t[0] = (char)(0xF0 | (cp >> 18)); t[1] = (char)(0x80 | ((cp >> 12) & 63));
        t[2] = (char)(0x80 | ((cp >> 6) & 63)); t[3] = (char)(0x80 | (cp & 63)); n = 4; }
    return buf_put(b, t, n);
}

static int buf_int(Buf *b, long v)
{
    char t[32];
    int n = snprintf(t, sizeof t, "%ld", v);
    return buf_put(b, t, n);
}

/* ------------------------------------------------------------------ */
/* unfilter                                                            */

static PyObject *
img_unfilter(PyObject *self, PyObject *args)
{
    Py_buffer in;
    Py_ssize_t rows, stride, bpp;
    if (!PyArg_ParseTuple(args, "y*nnn", &in, &rows, &stride, &bpp)) return NULL;
    if (rows < 0 || stride < 0 || bpp < 1) {
        PyBuffer_Release(&in);
        PyErr_SetString(PyExc_ValueError, "bad sizes");
        return NULL;
    }
    const unsigned char *src = (const unsigned char *)in.buf;
    PyObject *res = PyBytes_FromStringAndSize(NULL, rows * stride);
    if (!res) { PyBuffer_Release(&in); return NULL; }
    unsigned char *out = (unsigned char *)PyBytes_AS_STRING(res);
    Py_ssize_t pos = 0;
    for (Py_ssize_t r = 0; r < rows; r++) {
        if (pos + 1 + stride > in.len) goto truncated;
        int ft = src[pos];
        const unsigned char *line = src + pos + 1;
        unsigned char *o = out + r * stride;
        const unsigned char *prev = r ? out + (r - 1) * stride : NULL;
        pos += 1 + stride;
        for (Py_ssize_t i = 0; i < stride; i++) {
            int a = i >= bpp ? o[i - bpp] : 0;
            int b = prev ? prev[i] : 0;
            int c = (prev && i >= bpp) ? prev[i - bpp] : 0;
            int pred;
            switch (ft) {
            case 0: pred = 0; break;
            case 1: pred = a; break;
            case 2: pred = b; break;
            case 3: pred = (a + b) >> 1; break;
            case 4: {
                int p = a + b - c;
                int pa = abs(p - a), pb = abs(p - b), pc = abs(p - c);
                pred = (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
                break; }
            default:
                Py_DECREF(res); PyBuffer_Release(&in);
                PyErr_Format(PyExc_ValueError, "PNG con filtro desconocido %d", ft);
                return NULL;
            }
            o[i] = (unsigned char)((line[i] + pred) & 255);
        }
    }
    PyBuffer_Release(&in);
    return res;
truncated:
    Py_DECREF(res);
    PyBuffer_Release(&in);
    {
        PyObject *mod = PyImport_ImportModule("flexablelib._images");
        PyObject *cls = mod ? PyObject_GetAttrString(mod, "ImageError") : NULL;
        Py_XDECREF(mod);
        if (cls) { PyErr_SetString(cls, "PNG truncado"); Py_DECREF(cls); }
    }
    return NULL;
}

/* ------------------------------------------------------------------ */
/* resize                                                              */

static void spans(Py_ssize_t size, Py_ssize_t n, Py_ssize_t *lo, Py_ssize_t *hi)
{
    for (Py_ssize_t o = 0; o < n; o++) {
        Py_ssize_t a = o * size / n;
        Py_ssize_t b = ((o + 1) * size + n - 1) / n;
        lo[o] = a;
        hi[o] = b > a + 1 ? b : a + 1;
    }
}

static PyObject *
img_resize(PyObject *self, PyObject *args)
{
    Py_buffer in;
    Py_ssize_t w, h, nw, nh;
    if (!PyArg_ParseTuple(args, "y*nnnn", &in, &w, &h, &nw, &nh)) return NULL;
    if (nw <= 0 || nh <= 0 || w <= 0 || h <= 0) {
        PyBuffer_Release(&in);
        PyErr_SetString(PyExc_ValueError, "sizes must be positive");
        return NULL;
    }
    if (in.len < w * h * 4) {
        PyBuffer_Release(&in);
        PyErr_SetString(PyExc_ValueError, "data shorter than width * height * 4");
        return NULL;
    }
    const unsigned char *src = (const unsigned char *)in.buf;
    Py_ssize_t *xl = PyMem_Malloc(sizeof(Py_ssize_t) * (size_t)(2 * nw + 2 * nh));
    i64 *acc = PyMem_Malloc(sizeof(i64) * 4 * (size_t)nw);
    if (!xl || !acc) { PyMem_Free(xl); PyMem_Free(acc); PyBuffer_Release(&in); return PyErr_NoMemory(); }
    Py_ssize_t *xh = xl + nw, *yl = xh + nw, *yh = yl + nh;
    spans(w, nw, xl, xh);
    spans(h, nh, yl, yh);
    PyObject *res = PyBytes_FromStringAndSize(NULL, nw * nh * 4);
    if (!res) { PyMem_Free(xl); PyMem_Free(acc); PyBuffer_Release(&in); return NULL; }
    unsigned char *out = (unsigned char *)PyBytes_AS_STRING(res);
    Py_BEGIN_ALLOW_THREADS
    for (Py_ssize_t oy = 0; oy < nh; oy++) {
        memset(acc, 0, sizeof(i64) * 4 * (size_t)nw);
        for (Py_ssize_t y = yl[oy]; y < yh[oy]; y++) {
            const unsigned char *row = src + y * w * 4;
            for (Py_ssize_t ox = 0; ox < nw; ox++) {
                i64 *s = acc + ox * 4;
                for (Py_ssize_t x = xl[ox]; x < xh[ox]; x++) {
                    const unsigned char *p = row + x * 4;
                    i64 a = p[3];
                    s[0] += p[0] * a; s[1] += p[1] * a; s[2] += p[2] * a; s[3] += a;
                }
            }
        }
        unsigned char *o = out + oy * nw * 4;
        for (Py_ssize_t ox = 0; ox < nw; ox++) {
            i64 *s = acc + ox * 4;
            i64 n = (i64)(yh[oy] - yl[oy]) * (xh[ox] - xl[ox]);
            i64 sa = s[3];
            if (sa) {
                o[ox * 4] = (unsigned char)((s[0] + sa / 2) / sa);
                o[ox * 4 + 1] = (unsigned char)((s[1] + sa / 2) / sa);
                o[ox * 4 + 2] = (unsigned char)((s[2] + sa / 2) / sa);
            } else {
                o[ox * 4] = o[ox * 4 + 1] = o[ox * 4 + 2] = 0;
            }
            o[ox * 4 + 3] = (unsigned char)((sa + n / 2) / n);
        }
    }
    Py_END_ALLOW_THREADS
    PyMem_Free(xl);
    PyMem_Free(acc);
    PyBuffer_Release(&in);
    return res;
}

/* ------------------------------------------------------------------ */
/* quantize                                                            */

static int sort_shift;
static int cmp_keys(const void *a, const void *b)
{
    int ka = *(const int *)a, kb = *(const int *)b;
    long va = ((long)((ka >> sort_shift) & 31) << 15) | ka;
    long vb = ((long)((kb >> sort_shift) & 31) << 15) | kb;
    return va < vb ? -1 : va > vb;
}

static int box_range(const int *keys, Py_ssize_t n, int shift)
{
    int lo = (keys[0] >> shift) & 31, hi = lo;
    for (Py_ssize_t i = 1; i < n; i++) {
        int v = (keys[i] >> shift) & 31;
        if (v < lo) lo = v; else if (v > hi) hi = v;
    }
    return hi - lo;
}

static PyObject *
img_quantize(PyObject *self, PyObject *args)
{
    Py_buffer in;
    Py_ssize_t w, h;
    int colors, thr;
    if (!PyArg_ParseTuple(args, "y*nnii", &in, &w, &h, &colors, &thr)) return NULL;
    if (colors < 1) colors = 1;
    if (colors > 255) colors = 255;
    Py_ssize_t n = w * h;
    if (w <= 0 || h <= 0 || in.len < n * 4) {
        PyBuffer_Release(&in);
        PyErr_SetString(PyExc_ValueError, "bad image size");
        return NULL;
    }
    const unsigned char *src = (const unsigned char *)in.buf;
    i64 *count = PyMem_Calloc(32768, sizeof(i64));
    i64 *sums = PyMem_Calloc(32768 * 3, sizeof(i64));
    int *pk = PyMem_Malloc(sizeof(int) * (size_t)n);
    int *keys = PyMem_Malloc(sizeof(int) * 32768);
    Py_ssize_t *bstart = PyMem_Malloc(sizeof(Py_ssize_t) * 256);
    Py_ssize_t *blen = PyMem_Malloc(sizeof(Py_ssize_t) * 256);
    i64 *btot = PyMem_Malloc(sizeof(i64) * 256);
    unsigned char *lut = PyMem_Malloc(32768);
    PyObject *pal = NULL, *idx = NULL, *res = NULL;
    if (!count || !sums || !pk || !keys || !bstart || !blen || !btot || !lut) {
        PyErr_NoMemory();
        goto done;
    }
    for (Py_ssize_t p = 0; p < n; p++) {
        const unsigned char *px = src + p * 4;
        if (thr && px[3] < thr) { pk[p] = -1; continue; }
        int key = ((px[0] >> 3) << 10) | ((px[1] >> 3) << 5) | (px[2] >> 3);
        pk[p] = key;
        count[key]++;
        sums[key * 3] += px[0]; sums[key * 3 + 1] += px[1]; sums[key * 3 + 2] += px[2];
    }
    Py_ssize_t used = 0;
    i64 total = 0;
    for (int k = 0; k < 32768; k++) if (count[k]) { keys[used++] = k; total += count[k]; }
    if (!used) {
        pal = PyBytes_FromStringAndSize("\0\0\0", 3);
        idx = PyBytes_FromStringAndSize(NULL, n);
        if (pal && idx) memset(PyBytes_AS_STRING(idx), 255, (size_t)n);
        goto pack;
    }
    int nb = 1;
    bstart[0] = 0; blen[0] = used; btot[0] = total;
    while (nb < colors) {
        int best = -1, best_range = -1;
        i64 best_count = -1;
        for (int bi = 0; bi < nb; bi++) {
            if (blen[bi] < 2) continue;
            const int *bk = keys + bstart[bi];
            int r = box_range(bk, blen[bi], 10), g = box_range(bk, blen[bi], 5), b = box_range(bk, blen[bi], 0);
            int rng = r > g ? r : g; if (b > rng) rng = b;
            if (rng > best_range || (rng == best_range && btot[bi] > best_count)) {
                best = bi; best_range = rng; best_count = btot[bi];
            }
        }
        if (best < 0) break;
        int *bk = keys + bstart[best];
        Py_ssize_t bn = blen[best];
        int r = box_range(bk, bn, 10), g = box_range(bk, bn, 5), b = box_range(bk, bn, 0);
        int mx = r; sort_shift = 10;
        if (g > mx) { mx = g; sort_shift = 5; }
        if (b > mx) { mx = b; sort_shift = 0; }
        qsort(bk, (size_t)bn, sizeof(int), cmp_keys);
        i64 tot = btot[best], acc = 0;
        Py_ssize_t cut = 1;
        for (Py_ssize_t j = 0; j < bn; j++) {
            acc += count[bk[j]];
            if (acc * 2 >= tot) { cut = j + 1; break; }
        }
        if (cut > bn - 1) cut = bn - 1;
        if (cut < 1) cut = 1;
        i64 lt = 0;
        for (Py_ssize_t j = 0; j < cut; j++) lt += count[bk[j]];
        for (int m = nb; m > best + 1; m--) {
            bstart[m] = bstart[m - 1]; blen[m] = blen[m - 1]; btot[m] = btot[m - 1];
        }
        bstart[best + 1] = bstart[best] + cut; blen[best + 1] = bn - cut; btot[best + 1] = tot - lt;
        blen[best] = cut; btot[best] = lt;
        nb++;
    }
    pal = PyBytes_FromStringAndSize(NULL, nb * 3);
    if (!pal) goto done;
    unsigned char *pp = (unsigned char *)PyBytes_AS_STRING(pal);
    for (int bi = 0; bi < nb; bi++) {
        i64 s[3] = {0, 0, 0};
        for (Py_ssize_t j = 0; j < blen[bi]; j++) {
            int k = keys[bstart[bi] + j];
            s[0] += sums[k * 3]; s[1] += sums[k * 3 + 1]; s[2] += sums[k * 3 + 2];
        }
        i64 c = btot[bi];
        for (int ch = 0; ch < 3; ch++) pp[bi * 3 + ch] = (unsigned char)((s[ch] + c / 2) / c);
    }
    for (Py_ssize_t u = 0; u < used; u++) {
        int k = keys[u];
        i64 c = count[k];
        int rr = (int)((sums[k * 3] + c / 2) / c), gg = (int)((sums[k * 3 + 1] + c / 2) / c),
            bb = (int)((sums[k * 3 + 2] + c / 2) / c);
        int best = 0; long dist = 1L << 30;
        for (int pi = 0; pi < nb; pi++) {
            long dr = pp[pi * 3] - rr, dg = pp[pi * 3 + 1] - gg, db = pp[pi * 3 + 2] - bb;
            long d = dr * dr + dg * dg + db * db;
            if (d < dist) { best = pi; dist = d; }
        }
        lut[k] = (unsigned char)best;
    }
    idx = PyBytes_FromStringAndSize(NULL, n);
    if (!idx) goto done;
    {
        unsigned char *ip = (unsigned char *)PyBytes_AS_STRING(idx);
        for (Py_ssize_t p = 0; p < n; p++) ip[p] = pk[p] < 0 ? 255 : lut[pk[p]];
    }
pack:
    if (pal && idx) res = PyTuple_Pack(2, pal, idx);
done:
    Py_XDECREF(pal); Py_XDECREF(idx);
    PyMem_Free(count); PyMem_Free(sums); PyMem_Free(pk); PyMem_Free(keys);
    PyMem_Free(bstart); PyMem_Free(blen); PyMem_Free(btot); PyMem_Free(lut);
    PyBuffer_Release(&in);
    return res;
}

/* ------------------------------------------------------------------ */
/* sixel                                                               */

static PyObject *
img_sixel_encode(PyObject *self, PyObject *args)
{
    Py_buffer ib, pb;
    Py_ssize_t w, h;
    if (!PyArg_ParseTuple(args, "y*nny*", &ib, &w, &h, &pb)) return NULL;
    PyObject *res = NULL;
    Buf b = {0};
    unsigned char *bits = NULL;
    if (w <= 0 || h <= 0 || ib.len < w * h) {
        PyErr_SetString(PyExc_ValueError, "bad image size");
        goto done;
    }
    const unsigned char *idx = (const unsigned char *)ib.buf;
    const unsigned char *pal = (const unsigned char *)pb.buf;
    Py_ssize_t ncolors = pb.len / 3;
    bits = (unsigned char *)malloc((size_t)w);
    if (!bits) { PyErr_NoMemory(); goto done; }
    if (buf_str(&b, "\x1bP0;1;0q\"1;1;") < 0 || buf_int(&b, (long)w) < 0 ||
        buf_str(&b, ";") < 0 || buf_int(&b, (long)h) < 0) goto done;
    for (Py_ssize_t i = 0; i < ncolors; i++) {
        if (buf_str(&b, "#") < 0 || buf_int(&b, (long)i) < 0 || buf_str(&b, ";2;") < 0) goto done;
        for (int c = 0; c < 3; c++) {
            if (c && buf_str(&b, ";") < 0) goto done;
            if (buf_int(&b, (pal[i * 3 + c] * 100 + 127) / 255) < 0) goto done;
        }
    }
    for (Py_ssize_t top = 0; top < h; top += 6) {
        Py_ssize_t band = h - top < 6 ? h - top : 6;
        unsigned char present[256];
        memset(present, 0, sizeof present);
        for (Py_ssize_t y = top; y < top + band; y++)
            for (Py_ssize_t x = 0; x < w; x++) present[idx[y * w + x]] = 1;
        int first = 1;
        for (int color = 0; color < 255; color++) {
            if (!present[color] || color >= ncolors) continue;
            memset(bits, 0, (size_t)w);
            for (Py_ssize_t dy = 0; dy < band; dy++) {
                const unsigned char *row = idx + (top + dy) * w;
                for (Py_ssize_t x = 0; x < w; x++)
                    if (row[x] == color) bits[x] |= (unsigned char)(1 << dy);
            }
            Py_ssize_t last = w;
            while (last > 0 && !bits[last - 1]) last--;
            if (!first && buf_str(&b, "$") < 0) goto done;
            first = 0;
            if (buf_str(&b, "#") < 0 || buf_int(&b, color) < 0) goto done;
            Py_ssize_t x = 0;
            while (x < last) {
                unsigned char v = bits[x];
                Py_ssize_t run = 1;
                while (x + run < last && bits[x + run] == v) run++;
                char ch = (char)(63 + v);
                if (run > 3) {
                    if (buf_str(&b, "!") < 0 || buf_int(&b, (long)run) < 0 || buf_put(&b, &ch, 1) < 0) goto done;
                } else {
                    for (Py_ssize_t k = 0; k < run; k++) if (buf_put(&b, &ch, 1) < 0) goto done;
                }
                x += run;
            }
        }
        if (top + 6 < h && buf_str(&b, "-") < 0) goto done;
    }
    if (buf_str(&b, "\x1b\\") < 0) goto done;
    res = PyUnicode_DecodeASCII(b.p, b.n, NULL);
done:
    free(b.p);
    free(bits);
    PyBuffer_Release(&ib);
    PyBuffer_Release(&pb);
    return res;
}

/* ------------------------------------------------------------------ */
/* cells                                                               */

static const unsigned int QUAD[16] = {0x20, 0x2598, 0x259D, 0x2580, 0x2596, 0x258C, 0x259E, 0x259B,
                                      0x2597, 0x259A, 0x2590, 0x259C, 0x2584, 0x2599, 0x259F, 0x2588};
static const char RAMP[] = " .:-=+*#%@";
static const int BAYER[16] = {0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5};
static const int BRAILLE_BITS[8] = {0x01, 0x08, 0x02, 0x10, 0x04, 0x20, 0x40, 0x80};
static const int CUBE[6] = {0, 95, 135, 175, 215, 255};
static const int ANSI16[16][3] = {{0, 0, 0}, {205, 0, 0}, {0, 205, 0}, {205, 205, 0}, {0, 0, 238},
    {205, 0, 205}, {0, 205, 205}, {229, 229, 229}, {127, 127, 127}, {255, 0, 0}, {0, 255, 0},
    {255, 255, 0}, {92, 92, 255}, {255, 0, 255}, {0, 255, 255}, {255, 255, 255}};

enum { M_HALF, M_QUAD, M_SEXT, M_BRAILLE, M_ASCII };
enum { C_TRUE, C_256, C_16, C_NONE };

typedef struct { int set; int r, g, b; } Col;

static int lum3(int r, int g, int b) { return (77 * r + 150 * g + 29 * b) >> 8; }

static int cube_index(int v) { return v < 48 ? 0 : v < 115 ? 1 : (v - 35) / 40; }

static int to256(int r, int g, int b)
{
    int ri = cube_index(r), gi = cube_index(g), bi = cube_index(b);
    int cr = CUBE[ri], cg = CUBE[gi], cb = CUBE[bi];
    int avg = (r + g + b) / 3;
    int gray = avg > 238 ? 23 : (avg - 3) / 10;
    if (avg < 3) gray = 0;
    if (gray < 0) gray = 0;
    int gv = 8 + 10 * gray;
    long dc = (long)(cr - r) * (cr - r) + (long)(cg - g) * (cg - g) + (long)(cb - b) * (cb - b);
    long dg = (long)(gv - r) * (gv - r) + (long)(gv - g) * (gv - g) + (long)(gv - b) * (gv - b);
    return dg < dc ? 232 + gray : 16 + 36 * ri + 6 * gi + bi;
}

static int to16(int r, int g, int b)
{
    int best = 0; long dist = 1L << 30;
    for (int i = 0; i < 16; i++) {
        long dr = ANSI16[i][0] - r, dg = ANSI16[i][1] - g, db = ANSI16[i][2] - b;
        long d = dr * dr + dg * dg + db * db;
        if (d < dist) { best = i; dist = d; }
    }
    return best;
}

static int col_eq(Col a, Col b)
{
    if (a.set != b.set) return 0;
    if (!a.set) return 1;
    return a.r == b.r && a.g == b.g && a.b == b.b;
}

static int put_sgr(Buf *b, Col fg, Col bg, int color)
{
    if (buf_str(b, "\x1b[") < 0) return -1;
    for (int which = 0; which < 2; which++) {
        Col c = which ? bg : fg;
        int base = which ? 48 : 38;
        if (which && buf_str(b, ";") < 0) return -1;
        if (!c.set) { if (buf_int(b, base + 1) < 0) return -1; continue; }
        if (color == C_TRUE) {
            if (buf_int(b, base) < 0 || buf_str(b, ";2;") < 0 || buf_int(b, c.r) < 0 || buf_str(b, ";") < 0 ||
                buf_int(b, c.g) < 0 || buf_str(b, ";") < 0 || buf_int(b, c.b) < 0) return -1;
        } else if (color == C_256) {
            if (buf_int(b, base) < 0 || buf_str(b, ";5;") < 0 || buf_int(b, to256(c.r, c.g, c.b)) < 0) return -1;
        } else {
            int idx = to16(c.r, c.g, c.b);
            if (buf_int(b, (idx < 8 ? base - 8 : base + 52) + (idx & 7)) < 0) return -1;
        }
    }
    return buf_str(b, "m");
}

static unsigned int sextant_cp(int mask)
{
    if (mask == 0) return 0x20;
    if (mask == 63) return 0x2588;
    if (mask == 21) return 0x258C;
    if (mask == 42) return 0x2590;
    unsigned int cp = 0x1FB00 + mask - 1;
    if (mask > 21) cp--;
    if (mask > 42) cp--;
    return cp;
}

static Col mean_of(const int (*px)[3], const int *sel, int n)
{
    Col c = {0, 0, 0, 0};
    int cnt = 0; long s0 = 0, s1 = 0, s2 = 0;
    for (int k = 0; k < n; k++) if (sel[k]) { s0 += px[k][0]; s1 += px[k][1]; s2 += px[k][2]; cnt++; }
    if (!cnt) return c;
    c.set = 1;
    c.r = (int)((s0 + cnt / 2) / cnt); c.g = (int)((s1 + cnt / 2) / cnt); c.b = (int)((s2 + cnt / 2) / cnt);
    return c;
}

static PyObject *
img_cells(PyObject *self, PyObject *args)
{
    Py_buffer in;
    Py_ssize_t w, h;
    const char *mode_s, *color_s;
    int thr;
    if (!PyArg_ParseTuple(args, "y*nnssi", &in, &w, &h, &mode_s, &color_s, &thr)) return NULL;
    int mode, pw, ph, color;
    if (!strcmp(mode_s, "half")) { mode = M_HALF; pw = 1; ph = 2; }
    else if (!strcmp(mode_s, "quadrant")) { mode = M_QUAD; pw = 2; ph = 2; }
    else if (!strcmp(mode_s, "sextant")) { mode = M_SEXT; pw = 2; ph = 3; }
    else if (!strcmp(mode_s, "braille")) { mode = M_BRAILLE; pw = 2; ph = 4; }
    else if (!strcmp(mode_s, "ascii")) { mode = M_ASCII; pw = 1; ph = 2; }
    else { PyBuffer_Release(&in); return PyErr_Format(PyExc_ValueError, "unknown mode '%s'", mode_s); }
    if (!strcmp(color_s, "truecolor")) color = C_TRUE;
    else if (!strcmp(color_s, "256")) color = C_256;
    else if (!strcmp(color_s, "16")) color = C_16;
    else if (!strcmp(color_s, "none")) color = C_NONE;
    else { PyBuffer_Release(&in); return PyErr_Format(PyExc_ValueError, "unknown colour level '%s'", color_s); }
    if (w < 0 || h < 0 || in.len < w * h * 4) {
        PyBuffer_Release(&in);
        PyErr_SetString(PyExc_ValueError, "data shorter than width * height * 4");
        return NULL;
    }
    const unsigned char *src = (const unsigned char *)in.buf;
    int mono = color == C_NONE;
    Py_ssize_t cols = w / pw, rows = h / ph;
    PyObject *list = PyList_New(rows);
    if (!list) { PyBuffer_Release(&in); return NULL; }
    Buf b = {0};
    int npx = pw * ph;
    for (Py_ssize_t row = 0; row < rows; row++) {
        b.n = 0;
        Col cur_fg = {0}, cur_bg = {0};
        for (Py_ssize_t col = 0; col < cols; col++) {
            int px[8][3], solid[8], lums[8];
            int nsolid = 0;
            for (int dy = 0; dy < ph; dy++) {
                const unsigned char *p = src + ((row * ph + dy) * w + col * pw) * 4;
                for (int dx = 0; dx < pw; dx++, p += 4) {
                    int k = dy * pw + dx;
                    solid[k] = p[3] >= thr;
                    px[k][0] = p[0]; px[k][1] = p[1]; px[k][2] = p[2];
                    lums[k] = lum3(p[0], p[1], p[2]);
                    nsolid += solid[k];
                }
            }
            unsigned int ch = 0x20;
            Col fg = {0}, bg = {0};
            if (mode == M_HALF) {
                if (!solid[0] && !solid[1]) ch = 0x20;
                else if (!solid[1]) { ch = 0x2580; fg.set = 1; fg.r = px[0][0]; fg.g = px[0][1]; fg.b = px[0][2]; }
                else if (!solid[0]) { ch = 0x2584; fg.set = 1; fg.r = px[1][0]; fg.g = px[1][1]; fg.b = px[1][2]; }
                else if (mono) {
                    static const unsigned int T[4] = {0x20, 0x2584, 0x2580, 0x2588};
                    ch = T[(lums[0] >= 128) * 2 + (lums[1] >= 128)];
                } else if (px[0][0] == px[1][0] && px[0][1] == px[1][1] && px[0][2] == px[1][2]) {
                    ch = 0x2588; fg.set = 1; fg.r = px[0][0]; fg.g = px[0][1]; fg.b = px[0][2];
                } else {
                    ch = 0x2580;
                    fg.set = 1; fg.r = px[0][0]; fg.g = px[0][1]; fg.b = px[0][2];
                    bg.set = 1; bg.r = px[1][0]; bg.g = px[1][1]; bg.b = px[1][2];
                }
            } else if (mode == M_ASCII) {
                if (nsolid) {
                    fg = mean_of((const int (*)[3])px, solid, npx);
                    ch = (unsigned char)RAMP[lum3(fg.r, fg.g, fg.b) * 10 / 256];
                    if (ch == 0x20 || mono) fg.set = 0;
                }
            } else {
                int on[8] = {0};
                if (nsolid) {
                    if (mono) {
                        Py_ssize_t gx = col * pw, gy = row * ph;
                        for (int k = 0; k < npx; k++)
                            if (solid[k] && lums[k] * 16 >
                                BAYER[((gy + k / pw) & 3) * 4 + ((gx + k % pw) & 3)] * 256 + 128)
                                on[k] = 1;
                    } else {
                        if (nsolid < npx) {
                            for (int k = 0; k < npx; k++) on[k] = solid[k];
                        } else if (mode == M_BRAILLE) {
                            int s = 0;
                            for (int k = 0; k < npx; k++) s += lums[k];
                            int mean = s / npx;
                            for (int k = 0; k < npx; k++) on[k] = lums[k] >= mean;
                        } else {
                            int s = 0, any = 0;
                            for (int k = 0; k < npx; k++) s += lums[k];
                            int mean = (s + npx / 2) / npx;
                            for (int k = 0; k < npx; k++) { on[k] = lums[k] > mean; any |= on[k]; }
                            if (!any) for (int k = 0; k < npx; k++) on[k] = 1;
                        }
                        int offs[8];
                        for (int k = 0; k < npx; k++) offs[k] = !on[k] && solid[k];
                        fg = mean_of((const int (*)[3])px, on, npx);
                        if (mode != M_BRAILLE) bg = mean_of((const int (*)[3])px, offs, npx);
                    }
                }
                int mask = 0;
                for (int k = 0; k < npx; k++) if (on[k]) mask |= 1 << k;
                if (mode == M_BRAILLE) {
                    int bits = 0;
                    for (int k = 0; k < 8; k++) if (mask & (1 << k)) bits |= BRAILLE_BITS[k];
                    ch = bits ? 0x2800 + (unsigned int)bits : 0x20;
                } else if (mode == M_QUAD) ch = QUAD[mask];
                else ch = sextant_cp(mask);
                if (ch == 0x20) fg.set = 0;
                else if (ch == 0x2588) bg.set = 0;
            }
            if (!mono && !(col_eq(fg, cur_fg) && col_eq(bg, cur_bg))) {
                int r = (!fg.set && !bg.set) ? buf_str(&b, "\x1b[0m") : put_sgr(&b, fg, bg, color);
                if (r < 0) goto fail;
                cur_fg = fg; cur_bg = bg;
            }
            if (buf_cp(&b, ch) < 0) goto fail;
        }
        if ((cur_fg.set || cur_bg.set) && buf_str(&b, "\x1b[0m") < 0) goto fail;
        PyObject *s = PyUnicode_DecodeUTF8(b.p ? b.p : "", b.n, NULL);
        if (!s) goto fail;
        PyList_SET_ITEM(list, row, s);
    }
    free(b.p);
    PyBuffer_Release(&in);
    return list;
fail:
    free(b.p);
    Py_DECREF(list);
    PyBuffer_Release(&in);
    return NULL;
}

static PyMethodDef methods[] = {
    {"unfilter", img_unfilter, METH_VARARGS, "Undo PNG scanline filters."},
    {"resize", img_resize, METH_VARARGS, "Area-average RGBA resampling."},
    {"quantize", img_quantize, METH_VARARGS, "Median-cut palette and indices."},
    {"sixel_encode", img_sixel_encode, METH_VARARGS, "DCS sixel sequence."},
    {"cells", img_cells, METH_VARARGS, "Unicode block, braille or ASCII cells."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_images", "C image primitives for flexablelib.", -1, methods
};

PyMODINIT_FUNC PyInit__images(void) { return PyModule_Create(&module); }
