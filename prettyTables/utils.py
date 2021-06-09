'''
UTILS
'''

import os


class Utils(object):
    '''
    A class that contains functions for different porpuses that are helpfull
    or essential.
    '''

    def getWIndowsSize():
        if os.name == "nt":
            mode = os.popen('mode').read().split()
            lines = "L¡neas:" if "L¡neas:" in mode else (
                "Líneas" if "Líneas" in mode else "Lines"
            )
            columns = "Columnas:" if "Columnas:" in mode else "Columns:"
            linesIndex = mode.index(lines)+1
            colsIndex = mode.index(columns)+1
            lines = mode[linesIndex]
            columns = mode[colsIndex]
        else:
            lines, columns = os.popen('stty size', 'r').read().split()
        
        return lines, columns
    
    def isarray(piece):
        return isinstance(piece, list)
    
    def lenOfElements(self, elementList, index=0, lens=[]):
        '''
        Returns the lenght of each row (sub-array) in a single array
        '''
        # Will only calculate len if index is lower than the len of the array.
        # If it isn't less, will return the final array of lens.
        if index < len(elementList):

            # Appends the lenght of the current element using the
            # "index" param, wich starts as 0. 
            lens.append(len(elementList[index]))

            # For each time it appends a lenght, calls again the function, sending 
            # the listOfElements, the lens array with the previous value\s and the
            # index plus 1, last one so looks for the next element 
            self.lenOfElements(elementList, index+1, lens)
        return lens
