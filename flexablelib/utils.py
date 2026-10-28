import os
import json
import shutil
from typing import Iterable, Union


def float_format(number, decimal_spaces):
    return ''.join(['{:.', str(decimal_spaces), 'f}']).format(number)


def get_window_size():
    """
    Returns the size of the terminal window.

    ```
    tuple(cols, lines)
    ```

    Reading the console is the one piece of I/O in the whole package, and it
    is the one thing that has to not raise: the very first bug reported
    against prettyTables was a table that could not be printed at all because
    this call blew up (issue #1). ``ValueError`` joins ``OSError`` in the
    handler because a redirected or emulated console can report a size that
    does not unpack, and ``shutil`` supplies a documented 80x24 fallback when
    it cannot find out either.
    """
    try:
        size = os.get_terminal_size()
    except (OSError, ValueError):
        size = shutil.get_terminal_size(fallback=(80, 24))

    return size.columns, size.lines


def is_list(piece):
    return isinstance(piece, list)


def is_tuple(piece):
    return isinstance(piece, tuple)


def is_dict(piece):
    return isinstance(piece, dict)


def is_set(piece):
    return isinstance(piece, set)


def is_str(piece):
    return isinstance(piece, str)


def is_bytes(piece):
    return isinstance(piece, bytes)


def is_some_instance(piece, *instances):
    """
    Returns True if the data piece is any instance of the requested.

    isinstance already accepts a tuple of types and does the whole test in one
    C call. The previous loop ran one call per type and, on no match, fell off
    the end returning None rather than False -- harmless where the result is
    only used in a condition, but wrong.

    This runs tens of thousands of times per render, so it is worth the
    directness.
    """
    return isinstance(piece, instances)


def is_empty_cell(cell, value_placer=None):
    """
    Whether a cell holds nothing at all.

    ``show_empty_rows`` and ``show_empty_columns`` have to agree on what
    empty means. A column is empty when every cell in it types as
    ``NoneType``, which covers three things: the placeholder the table pads
    short rows with, a real ``None``, and the empty string. Rows used to
    count only the placeholder, so a row the caller filled with ``''``
    stayed on screen while a column filled exactly the same way vanished.

    The string test is by type and not by ``== ''`` so that a value with an
    unusual ``__eq__`` -- an array, say -- cannot answer for the whole row.
    """
    if value_placer is not None and cell is value_placer:
        return True
    if cell is None:
        return True
    return isinstance(cell, str) and cell == ''


def is_multi_row(row):
    """
    True when every cell in the row is itself a sequence of sub-rows.

    Built two intermediate sequences and a lambda per cell before; `all` short
    circuits on the first plain cell instead, and the common case -- an
    ordinary row -- exits on the first element. An empty row is still True,
    as it was when the old sum() and len() were compared at zero.
    """
    return all(isinstance(cell, (list, tuple)) for cell in row)


def length_of_elements(element_list, index=0, lengths=None):
    """
    Returns the length of each row (sub-array) in a single array
    """
    if lengths is None:
        lengths = []
    # Will only calculate len if index is lower than the len of the array.
    # If it isn't less, will return the final array of lengths.
    if index < len(element_list):

        # Appends the length of the current element using the
        # "index" param, which starts as 0.
        lengths.append(len(element_list[index]))

        # For each time it appends a length, calls again the function, sending
        # the listOfElements, the lengths array with the previous value\s and the
        # index plus 1, last one so looks for the next element
        length_of_elements(element_list, index + 1, lengths)

    return lengths


def flatten(list_to_flatten, i=0, c=0):
    """
    Flatten a list containing lists that could also contain lists,
    and so on
    """
    c += 1
    if i < len(list_to_flatten):
        if is_list(list_to_flatten[i]):
            temp = list_to_flatten.pop(i)
            for x in range(len(temp)):
                list_to_flatten.insert(i + x, temp[x])
            return flatten(list_to_flatten, i, c)
        else:
            return flatten(list_to_flatten, i + 1, c)
    else:
        return list_to_flatten


def read_json(file):
    with open(file) as json_file:
        data = json.load(json_file)
    json_file.close()
    return data


def read_file(filename):
    """
    Read a text file whole.

    Opened read-only. It was 'r+' before, which asks for write access on a
    file that is only ever read and fails outright on anything read-only --
    setup.py reads README.md through here while building.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()


def delete_repetitions(iterable: Iterable, 
                      ) -> Union[list, tuple]:
    cleansed_list = []
    for element in iterable:
        if element not in cleansed_list:
            cleansed_list.append(element)
    
    return cleansed_list


class IndexColumnTitle(str):
    """
    The header of the index column.

    It prints as ``'i'`` like any other header, but it is equal only to
    itself. Every one of the ``_with_i`` structures is a dict keyed by
    header, so a data column the caller decides to call ``'i'`` used to land
    on the same entry as the index column -- one of the two overwrote the
    other and the columns after it disappeared from the render. Identity
    equality keeps them apart without renaming anybody's column.

    Naming a column 'i' is listed in the README as a known issue. This is
    what closes it.
    """
    __slots__ = ()

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __hash__(self):
        return id(self)


class IndexCounter(object):
    """
    A simple class to keep track of the index
    """
    def __init__(self):
        self.index = 0
        self.start_added = False
    
    def __call__(self, start=0, step=1, add_step=True):
        if not self.start_added:
            self.index = start - step
            self.start_added = True
        if add_step:
            self.index += step
        return self.index
    
    def reset_count(self):
        self.index = 0
        self.start_added = False


class ValuePlacer(object):
    """
    A little class to place a value in a cell
    """
    def __init__(self):
        pass
    
    def __call__(self, value):
        return value
    
