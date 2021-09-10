
from typing import NamedTuple
import os


class Utils:
    '''
    UTILS

    functions for different porpuses that are helpfull
    or essential.
    '''
    def getWIndowsSize():
        return os.get_terminal_size()
    
    def isarray(piece):
        return isinstance(piece, list)
    
    def lenOfElements(self, elementList, index=0, lengths=None):
        '''
        Returns the lenght of each row (sub-array) in a single array
        '''
        if lengths == None:
            lengths = []
        # Will only calculate len if index is lower than the len of the array.
        # If it isn't less, will return the final array of lengths.
        if index < len(elementList):

            # Appends the lenght of the current element using the
            # "index" param, wich starts as 0. 
            lengths.append(len(elementList[index]))

            # For each time it appends a lenght, calls again the function, sending 
            # the listOfElements, the lengths array with the previous value\s and the
            # index plus 1, last one so looks for the next element 
            self.lenOfElements(elementList, index+1, lengths)

        return lengths
