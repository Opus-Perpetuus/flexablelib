from .table import Table
from .style_compositions import TableComposition, SeparatorLine

# Names, not the objects themselves: `from prettyTables import *` walks this
# list and raises TypeError on anything that is not a string.
__all__ = ['Table', 'TableComposition', 'SeparatorLine']