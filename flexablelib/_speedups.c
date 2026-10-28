/*
 * C implementations of the hot paths in prettyTables.
 *
 * Rendering a table measures every cell several times: once per pass of the
 * two-pass width computation, again while aligning, and again for each wrapped
 * sub-row. On a table of any size, measurement dominates the runtime, and in
 * pure Python it costs a function call and a dict lookup per character.
 *
 * This module reimplements the three hottest operations -- visible width,
 * escape stripping, and padding -- over CPython's native string buffer, with
 * no per-character allocation and a binary search over baked-in Unicode range
 * tables instead of unicodedata lookups.
 *
 * The behaviour must match prettyTables/text_width.py exactly. That module is
 * the reference and the fallback when this extension is unavailable; the two
 * are exercised against each other by the test suite.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "_width_tables.h"

/* Codepoints that terminate or delimit escape sequences. */
#define ESC 0x1B
#define BEL 0x07

/*
 * U+FE0F, the emoji presentation selector. It has no width of its own; what
 * it does is make the character in front of it render as an emoji, which is
 * two columns wide even where the bare character is one. `⚠` is one column,
 * `⚠️` is two. See measured_clusters() in text_width.py -- the two
 * implementations must agree on this or a status column drifts by a column
 * per emoji depending on whether the extension was built.
 */
#define VS16 0xFE0F

/* Py_NewRef arrived in 3.10; the package supports 3.8 upward. */
#if PY_VERSION_HEX < 0x030A0000
static inline PyObject *
Py_NewRef(PyObject *object)
{
    Py_INCREF(object);
    return object;
}
#endif


/*
 * Is the codepoint inside one of the sorted, non-overlapping ranges?
 *
 * The tables are generated in ascending order by tools/generate_width_tables.py,
 * which is what makes the binary search valid.
 */
static int
in_ranges(const struct width_range *table, size_t count, Py_UCS4 codepoint)
{
    size_t low = 0;
    size_t high = count;

    while (low < high) {
        size_t middle = low + (high - low) / 2;
        if (codepoint < table[middle].start) {
            high = middle;
        }
        else if (codepoint > table[middle].end) {
            low = middle + 1;
        }
        else {
            return 1;
        }
    }
    return 0;
}


/* Terminal columns occupied by one codepoint: 0, 1, or 2. */
static int
codepoint_width(Py_UCS4 codepoint)
{
    /* Printable ASCII is the overwhelming majority of real table data and is
     * always one column. Checking it first skips both binary searches. */
    if (codepoint >= 0x20 && codepoint < 0x7F) {
        return 1;
    }
    if (in_ranges(zero_width_ranges, ZERO_WIDTH_RANGES_COUNT, codepoint)) {
        return 0;
    }
    if (in_ranges(wide_ranges, WIDE_RANGES_COUNT, codepoint)) {
        return 2;
    }
    return 1;
}


/*
 * Length of the escape sequence starting at `start`, or 0 if there is none.
 *
 * Recognises the same three families as the regex in text_width.py:
 *   CSI  ESC [ params(0x30-0x3F)* intermediates(0x20-0x2F)* final(0x40-0x7E)
 *   OSC  ESC ] ... terminated by BEL or by ESC backslash
 *   Fe   ESC followed by one byte in 0x40-0x5F
 *
 * OSC is tested before the two-byte form because ']' (0x5D) falls inside the
 * Fe range; matching it as a bare two-byte escape would leave the hyperlink
 * payload to be counted as visible text.
 *
 * An unterminated sequence returns 0, so the lone ESC is measured as an
 * ordinary character rather than swallowing the rest of the string.
 */
static Py_ssize_t
ansi_sequence_length(int kind, const void *data, Py_ssize_t length,
                     Py_ssize_t start)
{
    Py_ssize_t position;
    Py_UCS4 next;

    if (start + 1 >= length) {
        return 0;
    }

    next = PyUnicode_READ(kind, data, start + 1);

    if (next == ']') {
        position = start + 2;
        while (position < length) {
            Py_UCS4 current = PyUnicode_READ(kind, data, position);
            if (current == BEL) {
                return position - start + 1;
            }
            if (current == ESC) {
                if (position + 1 < length
                    && PyUnicode_READ(kind, data, position + 1) == '\\') {
                    return position - start + 2;
                }
                break;
            }
            position++;
        }
        /* Unterminated OSC. ']' is 0x5D, inside the two-byte escape range, so
         * the reference regex falls through to that alternative and consumes
         * just ESC ']'. Match it, or the two implementations disagree on how
         * much of a malformed sequence is visible. */
        return 2;
    }

    if (next == '[') {
        position = start + 2;
        while (position < length) {
            Py_UCS4 current = PyUnicode_READ(kind, data, position);
            if (current < 0x30 || current > 0x3F) {
                break;
            }
            position++;
        }
        while (position < length) {
            Py_UCS4 current = PyUnicode_READ(kind, data, position);
            if (current < 0x20 || current > 0x2F) {
                break;
            }
            position++;
        }
        if (position < length) {
            Py_UCS4 final_byte = PyUnicode_READ(kind, data, position);
            if (final_byte >= 0x40 && final_byte <= 0x7E) {
                return position - start + 1;
            }
        }
        return 0;
    }

    if (next >= 0x40 && next <= 0x5F) {
        return 2;
    }

    return 0;
}


/* Shared prologue: validate the argument and expose its buffer. */
static int
unpack_string(PyObject *object, int *kind, const void **data,
              Py_ssize_t *length)
{
    if (!PyUnicode_Check(object)) {
        PyErr_Format(PyExc_TypeError, "expected str, got %.100s",
                     Py_TYPE(object)->tp_name);
        return -1;
    }
#if PY_VERSION_HEX < 0x030C0000
    if (PyUnicode_READY(object) < 0) {
        return -1;
    }
#endif
    *kind = PyUnicode_KIND(object);
    *data = PyUnicode_DATA(object);
    *length = PyUnicode_GET_LENGTH(object);
    return 0;
}


static Py_ssize_t
measure(int kind, const void *data, Py_ssize_t length)
{
    Py_ssize_t total = 0;
    Py_ssize_t position = 0;
    /* Width of the last printable codepoint, so an emoji presentation
     * selector can promote it. Zero means there is nothing to promote --
     * either nothing has been seen yet, or it was already two columns. */
    int previous_width = 0;

    while (position < length) {
        Py_UCS4 codepoint = PyUnicode_READ(kind, data, position);
        int width;

        if (codepoint == ESC) {
            Py_ssize_t skip = ansi_sequence_length(kind, data, length, position);
            if (skip > 0) {
                position += skip;
                continue;
            }
        }

        if (codepoint == VS16) {
            if (previous_width == 1) {
                total += 1;
                previous_width = 2;
            }
            position++;
            continue;
        }

        width = codepoint_width(codepoint);
        total += width;
        previous_width = width;
        position++;
    }
    return total;
}


PyDoc_STRVAR(visible_width_doc,
"visible_width(text, /)\n--\n\n"
"Terminal columns occupied by the string, ignoring ANSI escape sequences\n"
"and counting East Asian Wide characters as two columns.");

static PyObject *
py_visible_width(PyObject *Py_UNUSED(module), PyObject *argument)
{
    int kind;
    const void *data;
    Py_ssize_t length;

    if (unpack_string(argument, &kind, &data, &length) < 0) {
        return NULL;
    }
    return PyLong_FromSsize_t(measure(kind, data, length));
}


PyDoc_STRVAR(strip_ansi_doc,
"strip_ansi(text, /)\n--\n\n"
"Return the string with every ANSI escape sequence removed.");

static PyObject *
py_strip_ansi(PyObject *Py_UNUSED(module), PyObject *argument)
{
    int kind;
    const void *data;
    Py_ssize_t length;
    Py_ssize_t position = 0;
    Py_ssize_t written = 0;
    Py_UCS4 *buffer;
    PyObject *result;

    if (unpack_string(argument, &kind, &data, &length) < 0) {
        return NULL;
    }

    /* Nothing to strip is the common case; hand back the original object
     * rather than allocating a copy. */
    for (position = 0; position < length; position++) {
        if (PyUnicode_READ(kind, data, position) == ESC) {
            break;
        }
    }
    if (position == length) {
        return Py_NewRef(argument);
    }
    position = 0;

    /* The output can only be shorter, so one allocation at input size is
     * enough and no growth check is needed in the loop. */
    buffer = PyMem_New(Py_UCS4, (size_t)length ? (size_t)length : 1);
    if (buffer == NULL) {
        return PyErr_NoMemory();
    }

    while (position < length) {
        Py_UCS4 codepoint = PyUnicode_READ(kind, data, position);
        if (codepoint == ESC) {
            Py_ssize_t skip = ansi_sequence_length(kind, data, length, position);
            if (skip > 0) {
                position += skip;
                continue;
            }
        }
        buffer[written++] = codepoint;
        position++;
    }

    result = PyUnicode_FromKindAndData(PyUnicode_4BYTE_KIND, buffer, written);
    PyMem_Free(buffer);
    return result;
}


PyDoc_STRVAR(pad_to_width_doc,
"pad_to_width(text, width, align='l', fill=' ', /)\n--\n\n"
"Pad the string to an exact visible width. `align` is 'l', 'r', or 'c'.\n"
"A string already at or beyond the width is returned unchanged.");

static PyObject *
py_pad_to_width(PyObject *Py_UNUSED(module), PyObject *args)
{
    PyObject *text;
    PyObject *fill = NULL;
    Py_ssize_t width;
    const char *align = "l";
    int kind;
    const void *data;
    Py_ssize_t length;
    Py_ssize_t deficit;
    PyObject *left_pad = NULL;
    PyObject *right_pad = NULL;
    PyObject *joined = NULL;
    PyObject *result = NULL;

    if (!PyArg_ParseTuple(args, "On|sU", &text, &width, &align, &fill)) {
        return NULL;
    }
    if (unpack_string(text, &kind, &data, &length) < 0) {
        return NULL;
    }

    deficit = width - measure(kind, data, length);
    if (deficit <= 0) {
        return Py_NewRef(text);
    }

    if (fill == NULL) {
        fill = PyUnicode_FromString(" ");
        if (fill == NULL) {
            return NULL;
        }
    }
    else {
        Py_INCREF(fill);
    }

    if (align[0] == 'r') {
        left_pad = PySequence_Repeat(fill, deficit);
        if (left_pad == NULL) {
            goto done;
        }
        result = PyUnicode_Concat(left_pad, text);
    }
    else if (align[0] == 'c') {
        Py_ssize_t left_count = deficit / 2;
        left_pad = PySequence_Repeat(fill, left_count);
        right_pad = PySequence_Repeat(fill, deficit - left_count);
        if (left_pad == NULL || right_pad == NULL) {
            goto done;
        }
        joined = PyUnicode_Concat(left_pad, text);
        if (joined == NULL) {
            goto done;
        }
        result = PyUnicode_Concat(joined, right_pad);
    }
    else {
        right_pad = PySequence_Repeat(fill, deficit);
        if (right_pad == NULL) {
            goto done;
        }
        result = PyUnicode_Concat(text, right_pad);
    }

done:
    Py_XDECREF(left_pad);
    Py_XDECREF(right_pad);
    Py_XDECREF(joined);
    Py_DECREF(fill);
    return result;
}


PyDoc_STRVAR(widths_of_doc,
"widths_of(strings, /)\n--\n\n"
"Visible width of every string in the sequence, as a list of ints.\n"
"Measuring a whole column in one call avoids the per-item interpreter\n"
"overhead that dominates when this is driven from a Python loop.");

static PyObject *
py_widths_of(PyObject *Py_UNUSED(module), PyObject *sequence)
{
    PyObject *fast;
    PyObject *result;
    Py_ssize_t count;
    Py_ssize_t index;

    fast = PySequence_Fast(sequence, "expected an iterable of str");
    if (fast == NULL) {
        return NULL;
    }
    count = PySequence_Fast_GET_SIZE(fast);
    result = PyList_New(count);
    if (result == NULL) {
        Py_DECREF(fast);
        return NULL;
    }

    for (index = 0; index < count; index++) {
        PyObject *item = PySequence_Fast_GET_ITEM(fast, index);
        int kind;
        const void *data;
        Py_ssize_t length;
        PyObject *value;

        if (unpack_string(item, &kind, &data, &length) < 0) {
            Py_DECREF(result);
            Py_DECREF(fast);
            return NULL;
        }
        value = PyLong_FromSsize_t(measure(kind, data, length));
        if (value == NULL) {
            Py_DECREF(result);
            Py_DECREF(fast);
            return NULL;
        }
        PyList_SET_ITEM(result, index, value);
    }

    Py_DECREF(fast);
    return result;
}


static PyMethodDef module_methods[] = {
    {"visible_width", py_visible_width, METH_O, visible_width_doc},
    {"strip_ansi", py_strip_ansi, METH_O, strip_ansi_doc},
    {"pad_to_width", py_pad_to_width, METH_VARARGS, pad_to_width_doc},
    {"widths_of", py_widths_of, METH_O, widths_of_doc},
    {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(module_doc,
"Accelerated text measurement for prettyTables.\n\n"
"Import prettyTables.fast rather than this module directly; it falls back to\n"
"the pure-Python implementation when the extension is not built.");

static struct PyModuleDef speedups_module = {
    PyModuleDef_HEAD_INIT,
    "prettyTables._speedups",
    module_doc,
    -1,
    module_methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit__speedups(void)
{
    return PyModule_Create(&speedups_module);
}
