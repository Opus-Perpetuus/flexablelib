
from typing import NamedTuple
import os


class Utils():
    '''
    ## UTILS

    functions for different porpuses that are of help:
    ```
    - getWIndowsSize
    - isarray
    - lenOfElements
    - flatten
    ```
    '''
    def getWIndowsSize(self):
        return os.get_terminal_size()
    
    def isarray(self, piece):
        return isinstance(piece, list)
    
    def lenOfElements(self, elementList, index=0, lengths=None):
        """
        Returns the lenght of each row (sub-array) in a single array
        """
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

    def flatten(self, tf, i=0, c=0):
        """ 
        Flatten a list containing lists that could also contain lists, 
        and so on 
        """
        c += 1
        if i < len(tf):
            if self.isarray(tf[i]):
                temp = tf.pop(i)
                for x in range(len(temp)):
                    tf.insert(i + x, temp[x])
                return self.flatten(tf, i, c)
            else:
                return self.flatten(tf, i+1, c)
        else:
	        return tf
