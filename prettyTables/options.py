"""
OPTIONS

some parameters for the creation of styles,
formatting, and other things.
"""

import re
from collections import namedtuple

ColumnAlignmentNames = namedtuple(
    'ColumnAlignmentNames',
    [
        'left',
        'center',
        'right',
        'float',
        'bytes'
    ]
)

TableAlignmentNames = namedtuple(
    'ColumnAlignmentNames',
    [
        'left',
        'center',
        'right',
    ]
)


# +-------------------------+ CONSTANTS +------------------------+

# For styles without vertical lines.
INVISIBLE_SEPARATOR = ' '
# Default value for an empty cell.
NONE_VALUE_REPLACEMENT = ''
# Default value to fill cells when aligning.
DEFAULT_FILL_CHAR = ' '
# The style is set if the user doesn't choose or puts an incorrect value.
DEFAULT_STYLE = 'grid_eheader'
# Default index column header.
I_COL_TIT = 'i'
# Default space a cell has on each side (after aligning).
CELL_MARGIN = 1
# Not used yet.
DEFAULT_TABLE_ALIGNMENT = 'l'
# Default string that is shown when a cell is trimmed.
DEFAULT_TRIMMING_SIGN = '...'
# How small can a column be.
MIN_COLUMN_SIZE = 3
# Names of the column alignments
COLUMN_ALIGNS = ColumnAlignmentNames(
    left='l',
    center='c',
    right='r',
    float='f',
    bytes='b'
)
# Every alignment code a caller may set on a column.
ALIGNMENT_CODES = frozenset(COLUMN_ALIGNS)
# Names of the table alignments
TABLE_ALIGNS = TableAlignmentNames(
    left='tl',
    center='tc',
    right='tr',
)

# +--------------------------+ REGEX +---------------------------+

# To find integer numbers.
INT_FILTER = re.compile(r'^[-+]?[0-9]*$').match
# To find float numbers: digits around a decimal point, an exponent, or both.
#
# Exponents used to be excluded, which is why "exponential numbers only align
# incorrectly" was in the README's known issues: `1.5e-05` matched neither
# filter, so it fell through to the text branch and was right-aligned while
# the numbers beside it sat on the decimal axis. Python prints small and
# large floats this way whether or not anyone asked it to.
FLT_FILTER = re.compile(
    r'^[-+]?(?:[0-9]*[.][0-9]*(?:[eE][-+]?[0-9]+)?|[0-9]+[eE][-+]?[0-9]+)$'
).match
# Whether a number is written with an exponent. Such a value cannot be
# rounded to fewer decimals without changing what it says.
EXP_FILTER = re.compile(r'^[-+]?[0-9.]+[eE][-+]?[0-9]+$').match


# +--------------------------------------------------------------+
