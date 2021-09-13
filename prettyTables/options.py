'''
# OPTIONS

some parameters for the creation of styles
and formating:
```
# Standard Invisible separator. This mark a standar
# of blank space for tables without visible vertical separators.
INVISIBLE_SEPARATOR = '  '

MARGIN = 1
ESCAPE_CODES = ['\n', '\r']
MIN_COLUMN_WIDTH = 2
LINE_SPACING = 1
DEC_SPACES = 2
FLOATFMT = lambda number, decimals=DEC_SPACES: \
           ''.join(['{a:.', decimals, 'f}']).format(number)
```
'''

# Standard Invisible separator. This mark a standar
# of blank space for tables without visible vertical separators.
INVISIBLE_SEPARATOR = '  '

MARGIN = 1
ESCAPE_CODES = ['\n', '\r']
MIN_COLUMN_WIDTH = 2
LINE_SPACING = 1       #TODO Decide if LineSpacing will be optional or deafult
DEC_SPACES = 6
FLOATFMT = lambda number, decimals=DEC_SPACES: \
           ''.join(['{:.', str(decimals), 'f}']).format(number)