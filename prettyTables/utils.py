import os


def float_format(number, decimal_spaces):
    return ''.join(['{:.', str(decimal_spaces), 'f}']).format(number)


def get_window_size():
    try:
        return os.get_terminal_size()
    except OSError:
        import shutil
        return shutil.get_terminal_size()


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
    Returns True if the data piece is any instance of the requested
    """
    is_instance = False
    for another in instances:
        is_instance = is_instance or isinstance(piece, another)
        if is_instance:
            return True


def is_multi_row(row):
    row_to_check = [*row]
    are_list_or_tuples = tuple(map(lambda col: is_list(col) or is_tuple(col), row_to_check))
    return True if sum(are_list_or_tuples) == len(tuple(row_to_check)) else False


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
