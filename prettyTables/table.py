'''
Print formated tabular data in different styles
'''

''' 
FORMATION OF THE TABLE

Main Class.
Here the whole table is formed
'''

from .utils import *
from .adjust import *
from .compose import *
from .compositionSets import StyleCompositions


class Table(object):
    '''
    # TABLE
    
    Makes a table out of tabular like data:

    ```
    tabularData: list[list[any]]
    headers: 'first' | list[any] | None = None
    style:  'clean ' # if None provided
            'plain '
            'bold_borderline'
            'grid'
            'windows_alike'
            'thin_borderline'
            'bold_header'
            'pipes'
    strAlign: 'l' | 'c' | 'r' = 'l'
    numAlign: 'l' | 'c' | 'r' = 'r'
    colAlign: list[str]  # ['l', 'r'...]
    adjustWidthsTo: 'l' | 'r' = 'r'
    adjustHeaderWidthTo: 'l' | 'r' = 'l'
    expandToWindow: True | False = False
    ```
    '''  
    
    def __init__(
        self,
        tabularData,
        headers=None,
        style='clean',
        strAlign='left',
        numAlign='right',
        colalign=[],
        adjustWidthsTo = 'right',
        adjustHeaderWidthTo = 'left',
        expandToWindow=False
    ):
        self.adjustHeaderWidthTo = adjustHeaderWidthTo
        self.adjustWidthsTo = adjustWidthsTo
        self.expandToWindow = expandToWindow
        self.strAlign = strAlign
        self.data = tabularData
        self.headers = headers
        self.style = style
        self.headerIncluded = False
        self.windowSize = Utils.getWIndowsSize()
    
¿


if __name__ == '__main__':

    print('This is not supposed to be executed!')
