import os

class Utils(object):

    def getWIndowsSize():
        if os.name == "nt":
            mode = os.popen('mode').read().split()
            lines = "L¡neas:" if "L¡neas:" in mode else ("Líneas" if "Líneas" in mode else "Lines")
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
    
        