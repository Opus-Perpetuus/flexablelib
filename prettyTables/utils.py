import os


def FLOAT_FORMAT(number, decimal_spaces):
    return ''.join(['{:.', str(decimal_spaces), 'f}']).format(number)


def get_window_size():
    try:
        return os.get_terminal_size()
    except OSError:
        import shutil
        return shutil.get_terminal_size()


def is_array(piece):
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


def length_of_elements(elementList, index=0, lengths=None):
    """
    Returns the length of each row (sub-array) in a single array
    """
    if lengths is None:
        lengths = []
    # Will only calculate len if index is lower than the len of the array.
    # If it isn't less, will return the final array of lengths.
    if index < len(elementList):

        # Appends the length of the current element using the
        # "index" param, which starts as 0.
        lengths.append(len(elementList[index]))

        # For each time it appends a length, calls again the function, sending
        # the listOfElements, the lengths array with the previous value\s and the
        # index plus 1, last one so looks for the next element
        length_of_elements(elementList, index + 1, lengths)

    return lengths


def flatten( tf, i=0, c=0):
    """
    Flatten a list containing lists that could also contain lists,
    and so on
    """
    c += 1
    if i < len(tf):
        if is_array(tf[i]):
            temp = tf.pop(i)
            for x in range(len(temp)):
                tf.insert(i + x, temp[x])
            return flatten(tf, i, c)
        else:
            return flatten(tf, i+1, c)
    else:
        return tf
