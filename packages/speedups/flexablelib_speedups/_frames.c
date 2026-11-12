/*
 * C hot paths for drawing terminal frames with flexablelib.
 *
 * A frame of a terminal interface is a few dozen to a few hundred lines, each
 * built from cells that are measured, cut and padded to an exact width, framed
 * by box-drawing borders, and finally compared with the previous frame so only
 * the lines that changed are written. In pure Python every one of those steps
 * walks strings a character at a time; here they run over CPython's string
 * buffers directly.
 *
 * The reference behaviour, and the fallback when this extension is not
 * installed, is flexablelib/_frames.py (which in turn delegates to
 * flexablelib/text_width.py). The two must agree exactly; the test suite
 * checks them against each other on random input.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>

#include "_width_tables.h"

#define ESC 0x1B
#define BEL 0x07
#define VS16 0xFE0F

#if PY_VERSION_HEX < 0x030A0000
static inline PyObject *
Py_NewRef(PyObject *object)
{
    Py_INCREF(object);
    return object;
}
#endif

static int
in_ranges(const struct width_range *table, size_t count, Py_UCS4 cp)
{
    size_t low = 0, high = count;
    while (low < high) {
        size_t mid = low + (high - low) / 2;
        if (cp < table[mid].start) high = mid;
        else if (cp > table[mid].end) low = mid + 1;
        else return 1;
    }
    return 0;
}

static int
cp_width(Py_UCS4 cp)
{
    if (cp >= 0x20 && cp < 0x7F) return 1;
    if (in_ranges(zero_width_ranges, ZERO_WIDTH_RANGES_COUNT, cp)) return 0;
    if (in_ranges(wide_ranges, WIDE_RANGES_COUNT, cp)) return 2;
    return 1;
}

/* Length of the escape sequence at `start` (0 when there is none); the same
 * three families, in the same order, as the regex in text_width.py. */
static Py_ssize_t
seq_len(int kind, const void *data, Py_ssize_t length, Py_ssize_t start)
{
    Py_ssize_t pos;
    Py_UCS4 next;
    if (start + 1 >= length) return 0;
    next = PyUnicode_READ(kind, data, start + 1);
    if (next == ']') {
        for (pos = start + 2; pos < length; pos++) {
            Py_UCS4 c = PyUnicode_READ(kind, data, pos);
            if (c == BEL) return pos - start + 1;
            if (c == ESC) {
                if (pos + 1 < length && PyUnicode_READ(kind, data, pos + 1) == '\\')
                    return pos - start + 2;
                break;
            }
        }
        return 2;
    }
    if (next == '[') {
        pos = start + 2;
        while (pos < length) {
            Py_UCS4 c = PyUnicode_READ(kind, data, pos);
            if (c < 0x30 || c > 0x3F) break;
            pos++;
        }
        while (pos < length) {
            Py_UCS4 c = PyUnicode_READ(kind, data, pos);
            if (c < 0x20 || c > 0x2F) break;
            pos++;
        }
        if (pos < length) {
            Py_UCS4 f = PyUnicode_READ(kind, data, pos);
            if (f >= 0x40 && f <= 0x7E) return pos - start + 1;
        }
        return 0;
    }
    if (next >= 0x40 && next <= 0x5F) return 2;
    return 0;
}

static int
unpack(PyObject *o, int *kind, const void **data, Py_ssize_t *length)
{
    if (!PyUnicode_Check(o)) {
        PyErr_Format(PyExc_TypeError, "expected str, got %.100s",
                     Py_TYPE(o)->tp_name);
        return -1;
    }
#if PY_VERSION_HEX < 0x030C0000
    if (PyUnicode_READY(o) < 0) return -1;
#endif
    *kind = PyUnicode_KIND(o);
    *data = PyUnicode_DATA(o);
    *length = PyUnicode_GET_LENGTH(o);
    return 0;
}

static Py_ssize_t
measure(int kind, const void *data, Py_ssize_t length)
{
    Py_ssize_t total = 0, pos = 0;
    int prev = 0;
    while (pos < length) {
        Py_UCS4 cp = PyUnicode_READ(kind, data, pos);
        int w;
        if (cp == ESC) {
            Py_ssize_t skip = seq_len(kind, data, length, pos);
            if (skip > 0) { pos += skip; continue; }
        }
        if (cp == VS16) {
            if (prev == 1) { total += 1; prev = 2; }
            pos++;
            continue;
        }
        w = cp_width(cp);
        total += w;
        prev = w;
        pos++;
    }
    return total;
}

/* A growable UCS4 buffer. */
typedef struct { Py_UCS4 *data; Py_ssize_t len, cap; } buf_t;

static int
buf_init(buf_t *b, Py_ssize_t cap)
{
    b->cap = cap > 16 ? cap : 16;
    b->len = 0;
    b->data = PyMem_New(Py_UCS4, (size_t)b->cap);
    if (!b->data) { PyErr_NoMemory(); return -1; }
    return 0;
}

static int
buf_grow(buf_t *b, Py_ssize_t extra)
{
    if (b->len + extra <= b->cap) return 0;
    while (b->len + extra > b->cap) b->cap *= 2;
    if (!PyMem_Resize(b->data, Py_UCS4, (size_t)b->cap)) {
        PyErr_NoMemory();
        return -1;
    }
    return 0;
}

static int
buf_put(buf_t *b, Py_UCS4 c)
{
    if (buf_grow(b, 1) < 0) return -1;
    b->data[b->len++] = c;
    return 0;
}

static int
buf_put_str(buf_t *b, PyObject *s)
{
    int kind; const void *data; Py_ssize_t n, i;
    if (unpack(s, &kind, &data, &n) < 0) return -1;
    if (buf_grow(b, n) < 0) return -1;
    for (i = 0; i < n; i++) b->data[b->len++] = PyUnicode_READ(kind, data, i);
    return 0;
}

static int
buf_put_ascii(buf_t *b, const char *s)
{
    Py_ssize_t n = (Py_ssize_t)strlen(s), i;
    if (buf_grow(b, n) < 0) return -1;
    for (i = 0; i < n; i++) b->data[b->len++] = (Py_UCS4)(unsigned char)s[i];
    return 0;
}

static int
buf_put_spaces(buf_t *b, Py_ssize_t n)
{
    Py_ssize_t i;
    if (n <= 0) return 0;
    if (buf_grow(b, n) < 0) return -1;
    for (i = 0; i < n; i++) b->data[b->len++] = ' ';
    return 0;
}

static PyObject *
buf_finish(buf_t *b)
{
    PyObject *r = PyUnicode_FromKindAndData(PyUnicode_4BYTE_KIND, b->data, b->len);
    PyMem_Free(b->data);
    b->data = NULL;
    return r;
}

/*
 * Append `text` cut to `budget` columns, then `suffix` (and a reset when an
 * escape was seen), exactly as text_width.truncate_to_width does after its
 * early returns. Clusters are a character plus the emoji selectors after it,
 * counted within one run of text (an escape ends the cluster).
 */
static int
cut_into(buf_t *b, int kind, const void *data, Py_ssize_t length,
         Py_ssize_t budget, PyObject *suffix)
{
    Py_ssize_t pos = 0, used = 0;
    int saw = 0;
    while (pos < length) {
        Py_UCS4 cp = PyUnicode_READ(kind, data, pos);
        Py_ssize_t end;
        int w, k;
        if (cp == ESC) {
            Py_ssize_t skip = seq_len(kind, data, length, pos);
            if (skip > 0) {
                Py_ssize_t i;
                for (i = 0; i < skip; i++)
                    if (buf_put(b, PyUnicode_READ(kind, data, pos + i)) < 0) return -1;
                saw = 1;
                pos += skip;
                continue;
            }
        }
        w = cp_width(cp);
        end = pos + 1;
        while (end < length && PyUnicode_READ(kind, data, end) == VS16) end++;
        if (end > pos + 1 && w == 1) w = 2;
        if (used + w > budget) {
            if (suffix && buf_put_str(b, suffix) < 0) return -1;
            if (saw && buf_put_ascii(b, "\x1b[0m") < 0) return -1;
            return 0;
        }
        for (k = 0; k < end - pos; k++)
            if (buf_put(b, PyUnicode_READ(kind, data, pos + k)) < 0) return -1;
        used += w;
        pos = end;
    }
    if (suffix && buf_put_str(b, suffix) < 0) return -1;
    if (saw && buf_put_ascii(b, "\x1b[0m") < 0) return -1;
    return 0;
}

static PyObject *
truncate_impl(PyObject *text, Py_ssize_t width, PyObject *suffix)
{
    int kind, skind; const void *data, *sdata; Py_ssize_t length, slen, sw;
    buf_t b;
    if (unpack(text, &kind, &data, &length) < 0) return NULL;
    if (measure(kind, data, length) <= width) return Py_NewRef(text);
    if (unpack(suffix, &skind, &sdata, &slen) < 0) return NULL;
    sw = measure(skind, sdata, slen);
    if (width <= sw) {
        if (width <= 0) return PyUnicode_FromString("");
        return PyUnicode_Substring(suffix, 0, width < slen ? width : slen);
    }
    if (buf_init(&b, length + slen + 4) < 0) return NULL;
    if (cut_into(&b, kind, data, length, width - sw, suffix) < 0) {
        PyMem_Free(b.data);
        return NULL;
    }
    return buf_finish(&b);
}

/* fit_line: cut what overflows (no marker), then pad to exactly `width`. */
static PyObject *
fit_impl(PyObject *text, Py_ssize_t width, char align)
{
    int kind; const void *data; Py_ssize_t length, w, deficit, left;
    buf_t b;
    if (unpack(text, &kind, &data, &length) < 0) return NULL;
    w = measure(kind, data, length);
    if (buf_init(&b, length + (width > 0 ? width : 0) + 4) < 0) return NULL;
    if (w > width && width <= 0) {
        /* no room at all: truncate_to_width returns '' and nothing pads */
        PyMem_Free(b.data);
        return PyUnicode_FromString("");
    }
    if (w > width) {
        PyObject *empty = PyUnicode_FromString("");
        if (!empty) { PyMem_Free(b.data); return NULL; }
        if (cut_into(&b, kind, data, length, width, empty) < 0) {
            Py_DECREF(empty);
            PyMem_Free(b.data);
            return NULL;
        }
        Py_DECREF(empty);
        /* measure what was kept (a wide character may leave one short) */
        w = measure(PyUnicode_4BYTE_KIND, b.data, b.len);
        deficit = width - w;
        if (deficit > 0) {
            /* pad around the cut text: rebuild in place */
            buf_t out;
            Py_ssize_t i;
            if (buf_init(&out, b.len + deficit) < 0) { PyMem_Free(b.data); return NULL; }
            left = align == 'r' ? deficit : (align == 'c' ? deficit / 2 : 0);
            buf_put_spaces(&out, left);
            if (buf_grow(&out, b.len) < 0) { PyMem_Free(b.data); PyMem_Free(out.data); return NULL; }
            for (i = 0; i < b.len; i++) out.data[out.len++] = b.data[i];
            buf_put_spaces(&out, deficit - left);
            PyMem_Free(b.data);
            return buf_finish(&out);
        }
        return buf_finish(&b);
    }
    deficit = width - w;
    if (deficit <= 0) { PyMem_Free(b.data); return Py_NewRef(text); }
    left = align == 'r' ? deficit : (align == 'c' ? deficit / 2 : 0);
    {
        Py_ssize_t i;
        if (buf_put_spaces(&b, left) < 0) { PyMem_Free(b.data); return NULL; }
        if (buf_grow(&b, length) < 0) { PyMem_Free(b.data); return NULL; }
        for (i = 0; i < length; i++) b.data[b.len++] = PyUnicode_READ(kind, data, i);
        if (buf_put_spaces(&b, deficit - left) < 0) { PyMem_Free(b.data); return NULL; }
    }
    return buf_finish(&b);
}

/* Columns [start, start+width) of `text`; see _frames._py_slice_columns. */
static PyObject *
slice_impl(PyObject *text, Py_ssize_t start, Py_ssize_t width)
{
    int kind; const void *data; Py_ssize_t length, pos = 0, col = 0, produced = 0, end;
    int saw = 0;
    buf_t b;
    if (unpack(text, &kind, &data, &length) < 0) return NULL;
    if (width <= 0) return PyUnicode_FromString("");
    end = start + width;
    if (buf_init(&b, width + 16) < 0) return NULL;
    while (pos < length && col < end) {
        Py_UCS4 cp = PyUnicode_READ(kind, data, pos);
        Py_ssize_t stop, k;
        int w;
        if (cp == ESC) {
            Py_ssize_t skip = seq_len(kind, data, length, pos);
            if (skip > 0) {
                for (k = 0; k < skip; k++)
                    if (buf_put(&b, PyUnicode_READ(kind, data, pos + k)) < 0) goto fail;
                saw = 1;
                pos += skip;
                continue;
            }
        }
        w = cp_width(cp);
        stop = pos + 1;
        while (stop < length && PyUnicode_READ(kind, data, stop) == VS16) stop++;
        if (stop > pos + 1 && w == 1) w = 2;
        if (col >= start) {
            if (col + w <= end) {
                for (k = pos; k < stop; k++)
                    if (buf_put(&b, PyUnicode_READ(kind, data, k)) < 0) goto fail;
                produced += w;
            } else {
                if (buf_put_spaces(&b, end - col) < 0) goto fail;
                produced += end - col;
            }
        } else if (col + w > start) {
            Py_ssize_t n = (col + w < end ? col + w : end) - start;
            if (buf_put_spaces(&b, n) < 0) goto fail;
            produced += n;
        }
        col += w;
        pos = stop;
    }
    if (produced < width && buf_put_spaces(&b, width - produced) < 0) goto fail;
    if (saw && buf_put_ascii(&b, "\x1b[0m") < 0) goto fail;
    return buf_finish(&b);
fail:
    PyMem_Free(b.data);
    return NULL;
}

/* ---------------------------------------------------------------- API */

static PyObject *
py_slice_columns(PyObject *m, PyObject *args)
{
    PyObject *text;
    Py_ssize_t start, width;
    (void)m;
    if (!PyArg_ParseTuple(args, "Onn", &text, &start, &width)) return NULL;
    return slice_impl(text, start, width);
}

static PyObject *
py_visible_width(PyObject *m, PyObject *arg)
{
    int kind; const void *data; Py_ssize_t length;
    (void)m;
    if (unpack(arg, &kind, &data, &length) < 0) return NULL;
    return PyLong_FromSsize_t(measure(kind, data, length));
}

static PyObject *
py_strip_ansi(PyObject *m, PyObject *arg)
{
    int kind; const void *data; Py_ssize_t length, pos;
    buf_t b;
    (void)m;
    if (unpack(arg, &kind, &data, &length) < 0) return NULL;
    for (pos = 0; pos < length; pos++)
        if (PyUnicode_READ(kind, data, pos) == ESC) break;
    if (pos == length) return Py_NewRef(arg);
    if (buf_init(&b, length) < 0) return NULL;
    pos = 0;
    while (pos < length) {
        Py_UCS4 cp = PyUnicode_READ(kind, data, pos);
        if (cp == ESC) {
            Py_ssize_t skip = seq_len(kind, data, length, pos);
            if (skip > 0) { pos += skip; continue; }
        }
        b.data[b.len++] = cp;
        pos++;
    }
    return buf_finish(&b);
}

static PyObject *
py_widths_of(PyObject *m, PyObject *seq)
{
    PyObject *fast, *result;
    Py_ssize_t n, i;
    (void)m;
    fast = PySequence_Fast(seq, "expected an iterable of str");
    if (!fast) return NULL;
    n = PySequence_Fast_GET_SIZE(fast);
    result = PyList_New(n);
    if (!result) { Py_DECREF(fast); return NULL; }
    for (i = 0; i < n; i++) {
        int kind; const void *data; Py_ssize_t length;
        PyObject *v;
        if (unpack(PySequence_Fast_GET_ITEM(fast, i), &kind, &data, &length) < 0) {
            Py_DECREF(result); Py_DECREF(fast); return NULL;
        }
        v = PyLong_FromSsize_t(measure(kind, data, length));
        if (!v) { Py_DECREF(result); Py_DECREF(fast); return NULL; }
        PyList_SET_ITEM(result, i, v);
    }
    Py_DECREF(fast);
    return result;
}

static PyObject *
py_truncate(PyObject *m, PyObject *args)
{
    PyObject *text, *suffix = NULL, *r;
    Py_ssize_t width;
    (void)m;
    if (!PyArg_ParseTuple(args, "On|O", &text, &width, &suffix)) return NULL;
    if (suffix == NULL) {
        suffix = PyUnicode_FromString("...");
        if (!suffix) return NULL;
        r = truncate_impl(text, width, suffix);
        Py_DECREF(suffix);
        return r;
    }
    return truncate_impl(text, width, suffix);
}

static char
align_char(const char *align)
{
    if (align[0] == 'r') return 'r';
    if (align[0] == 'c') return 'c';
    return 'l';
}

static PyObject *
py_fit_line(PyObject *m, PyObject *args)
{
    PyObject *text;
    Py_ssize_t width;
    const char *align = "l";
    (void)m;
    if (!PyArg_ParseTuple(args, "On|s", &text, &width, &align)) return NULL;
    return fit_impl(text, width, align_char(align));
}

static PyObject *
py_fit_lines(PyObject *m, PyObject *args)
{
    PyObject *seq, *fast, *result;
    Py_ssize_t width, n, i;
    const char *align = "l";
    char a;
    (void)m;
    if (!PyArg_ParseTuple(args, "On|s", &seq, &width, &align)) return NULL;
    a = align_char(align);
    fast = PySequence_Fast(seq, "expected an iterable of str");
    if (!fast) return NULL;
    n = PySequence_Fast_GET_SIZE(fast);
    result = PyList_New(n);
    if (!result) { Py_DECREF(fast); return NULL; }
    for (i = 0; i < n; i++) {
        PyObject *v = fit_impl(PySequence_Fast_GET_ITEM(fast, i), width, a);
        if (!v) { Py_DECREF(result); Py_DECREF(fast); return NULL; }
        PyList_SET_ITEM(result, i, v);
    }
    Py_DECREF(fast);
    return result;
}

/*
 * border_grid(width, height, horiz, vert, glyphs) -> list of str
 *
 * `horiz[y*width + x]` is non-zero when a border runs from (x, y) to (x+1, y);
 * `vert[y*width + x]` when one runs from (x, y) to (x, y+1). `glyphs` holds the
 * 11 box glyphs (h, v, tl, tr, bl, br, lt, rt, tt, bt, x). Each point gets the
 * glyph for the arms that meet there; points with none are spaces.
 */
static PyObject *
py_border_grid(PyObject *m, PyObject *args)
{
    Py_ssize_t W, H, x, y;
    Py_buffer hb, vb;
    PyObject *glyph_seq, *gfast, *result;
    Py_UCS4 g[11];
    int i;
    /* index into g by (up, down, left, right) */
    static const signed char table[16] = {
        /* u d l r */
        -1, /* 0000 */ 0, /* 0001 r */ 0, /* 0010 l */ 0, /* 0011 lr */
        1,  /* 0100 d */ 2, /* 0101 dr tl */ 3, /* 0110 dl tr */ 8, /* 0111 dlr tt */
        1,  /* 1000 u */ 4, /* 1001 ur bl */ 5, /* 1010 ul br */ 9, /* 1011 ulr bt */
        1,  /* 1100 ud */ 6, /* 1101 udr lt */ 7, /* 1110 udl rt */ 10 /* 1111 x */
    };
    (void)m;
    if (!PyArg_ParseTuple(args, "nny*y*O", &W, &H, &hb, &vb, &glyph_seq)) return NULL;
    if (W < 0 || H < 0 || hb.len < W * H || vb.len < W * H) {
        PyBuffer_Release(&hb); PyBuffer_Release(&vb);
        PyErr_SetString(PyExc_ValueError, "edge buffers must hold width*height bytes");
        return NULL;
    }
    gfast = PySequence_Fast(glyph_seq, "glyphs must be a sequence of 11 str");
    if (!gfast || PySequence_Fast_GET_SIZE(gfast) != 11) {
        Py_XDECREF(gfast); PyBuffer_Release(&hb); PyBuffer_Release(&vb);
        if (!PyErr_Occurred())
            PyErr_SetString(PyExc_ValueError, "glyphs must hold 11 strings");
        return NULL;
    }
    for (i = 0; i < 11; i++) {
        PyObject *s = PySequence_Fast_GET_ITEM(gfast, i);
        int kind; const void *data; Py_ssize_t n;
        if (unpack(s, &kind, &data, &n) < 0 || n != 1) {
            Py_DECREF(gfast); PyBuffer_Release(&hb); PyBuffer_Release(&vb);
            if (!PyErr_Occurred())
                PyErr_SetString(PyExc_ValueError, "each glyph must be one character");
            return NULL;
        }
        g[i] = PyUnicode_READ(kind, data, 0);
    }
    Py_DECREF(gfast);
    result = PyList_New(H);
    if (!result) { PyBuffer_Release(&hb); PyBuffer_Release(&vb); return NULL; }
    {
        const unsigned char *h = (const unsigned char *)hb.buf;
        const unsigned char *v = (const unsigned char *)vb.buf;
        Py_UCS4 *line = PyMem_New(Py_UCS4, (size_t)(W > 0 ? W : 1));
        if (!line) {
            Py_DECREF(result); PyBuffer_Release(&hb); PyBuffer_Release(&vb);
            return PyErr_NoMemory();
        }
        for (y = 0; y < H; y++) {
            PyObject *s;
            for (x = 0; x < W; x++) {
                int left = x > 0 && h[y * W + x - 1];
                int right = h[y * W + x] != 0;
                int up = y > 0 && v[(y - 1) * W + x];
                int down = v[y * W + x] != 0;
                int key = (up << 3) | (down << 2) | (left << 1) | right;
                line[x] = table[key] < 0 ? ' ' : g[(int)table[key]];
            }
            s = PyUnicode_FromKindAndData(PyUnicode_4BYTE_KIND, line, W);
            if (!s) {
                PyMem_Free(line); Py_DECREF(result);
                PyBuffer_Release(&hb); PyBuffer_Release(&vb);
                return NULL;
            }
            PyList_SET_ITEM(result, y, s);
        }
        PyMem_Free(line);
    }
    PyBuffer_Release(&hb);
    PyBuffer_Release(&vb);
    return result;
}

/* changed_lines(old, new) -> indices of `new` that differ from `old`. */
static PyObject *
py_changed_lines(PyObject *m, PyObject *args)
{
    PyObject *old, *new_, *of, *nf, *result;
    Py_ssize_t no, nn, i;
    (void)m;
    if (!PyArg_ParseTuple(args, "OO", &old, &new_)) return NULL;
    of = PySequence_Fast(old, "old must be a sequence of str");
    if (!of) return NULL;
    nf = PySequence_Fast(new_, "new must be a sequence of str");
    if (!nf) { Py_DECREF(of); return NULL; }
    no = PySequence_Fast_GET_SIZE(of);
    nn = PySequence_Fast_GET_SIZE(nf);
    result = PyList_New(0);
    if (!result) goto fail;
    for (i = 0; i < nn; i++) {
        int same = 0;
        if (i < no) {
            same = PyUnicode_Compare(PySequence_Fast_GET_ITEM(of, i),
                                     PySequence_Fast_GET_ITEM(nf, i)) == 0;
            if (PyErr_Occurred()) goto fail;
        }
        if (!same) {
            PyObject *v = PyLong_FromSsize_t(i);
            if (!v || PyList_Append(result, v) < 0) { Py_XDECREF(v); goto fail; }
            Py_DECREF(v);
        }
    }
    Py_DECREF(of); Py_DECREF(nf);
    return result;
fail:
    Py_XDECREF(result); Py_DECREF(of); Py_DECREF(nf);
    return NULL;
}

/*
 * render_diff(old, new) -> str
 *
 * The bytes to turn a screen showing `old` into `new`: for each changed line
 * a cursor move to its row, the line, and a clear-to-end-of-line; when `new`
 * is shorter, a clear below its last line.
 */
static PyObject *
py_render_diff(PyObject *m, PyObject *args)
{
    PyObject *old, *new_, *of, *nf;
    Py_ssize_t no, nn, i;
    buf_t b;
    char move[48];
    (void)m;
    if (!PyArg_ParseTuple(args, "OO", &old, &new_)) return NULL;
    of = PySequence_Fast(old, "old must be a sequence of str");
    if (!of) return NULL;
    nf = PySequence_Fast(new_, "new must be a sequence of str");
    if (!nf) { Py_DECREF(of); return NULL; }
    no = PySequence_Fast_GET_SIZE(of);
    nn = PySequence_Fast_GET_SIZE(nf);
    if (buf_init(&b, 256) < 0) { Py_DECREF(of); Py_DECREF(nf); return NULL; }
    for (i = 0; i < nn; i++) {
        PyObject *line = PySequence_Fast_GET_ITEM(nf, i);
        if (i < no) {
            int cmp = PyUnicode_Compare(PySequence_Fast_GET_ITEM(of, i), line);
            if (PyErr_Occurred()) goto fail;
            if (cmp == 0) continue;
        }
        PyOS_snprintf(move, sizeof(move), "\x1b[%zd;1H", i + 1);
        if (buf_put_ascii(&b, move) < 0 || buf_put_str(&b, line) < 0 ||
            buf_put_ascii(&b, "\x1b[K") < 0) goto fail;
    }
    if (nn < no) {
        PyOS_snprintf(move, sizeof(move), "\x1b[%zd;1H\x1b[J", nn + 1);
        if (buf_put_ascii(&b, move) < 0) goto fail;
    }
    Py_DECREF(of); Py_DECREF(nf);
    return buf_finish(&b);
fail:
    PyMem_Free(b.data); Py_DECREF(of); Py_DECREF(nf);
    return NULL;
}

static PyMethodDef methods[] = {
    {"visible_width", py_visible_width, METH_O, "Visible terminal columns of a string."},
    {"strip_ansi", py_strip_ansi, METH_O, "The string without ANSI escapes."},
    {"widths_of", py_widths_of, METH_O, "Visible width of every string."},
    {"truncate", py_truncate, METH_VARARGS, "truncate(text, width, suffix='...')"},
    {"fit_line", py_fit_line, METH_VARARGS, "fit_line(text, width, align='l')"},
    {"fit_lines", py_fit_lines, METH_VARARGS, "fit_lines(lines, width, align='l')"},
    {"slice_columns", py_slice_columns, METH_VARARGS,
     "slice_columns(text, start, width) -> exactly width columns"},
    {"border_grid", py_border_grid, METH_VARARGS,
     "border_grid(width, height, horiz, vert, glyphs) -> list of str"},
    {"changed_lines", py_changed_lines, METH_VARARGS, "changed_lines(old, new)"},
    {"render_diff", py_render_diff, METH_VARARGS, "render_diff(old, new) -> str"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "flexablelib_speedups._frames",
    "C frame primitives for flexablelib (optional; see flexablelib._frames).",
    -1, methods, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit__frames(void)
{
    return PyModule_Create(&module);
}
