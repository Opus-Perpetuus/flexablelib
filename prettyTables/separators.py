""" SEPARATORS OF THE TABLE """

from cells import Cells
from compositionSets import StyleCompositions, HorizontalComposition


class Separators(Cells):
    """ 
    # Separators

    Separators or division lines of the table.
    ```
    colAlignment: list[str] # ['l', 'r', 'c', ...]
    colSizes: list[int] # [12, 4, ...]
    styleName: str
    ```
    """
    def __init__(self, colAlignment, colSizes, styleName,
                       headers, body, exBoTo, exHeTo):
        super().__init__(headers, body, exBoTo, exHeTo)
        self.colAlginment = colAlignment
        self.formedSeparators = None
        self.colSizes = colSizes
        self.styleName = styleName
        self.style = StyleCompositions._asdict()[self.styleName]

    def _makeSeparators(self):
        options      = self.style.tableOptions
        alignSens    = options.alignSensitive
        alignChar    = self.__checkNone(options.alignIndicator)
        wcpis        = options.whenCenteredPutInSides
        margin       = options.margin

        horiComp     = self.style.horizontalComposition
        headSupChar  = self.__checkNone(horiComp.headerSuperior)
        headInfChar  = self.__checkNone(horiComp.headerInferior)
        noHeadChar   = self.__checkNone(horiComp.startsWithNoHeader)
        tabBodyChar  = self.__checkNone(horiComp.tableBody)
        tabEndChar   = self.__checkNone(horiComp.tableEnd)

        headSup      = self._singleSep(headSupChar, alignSens, wcpis, 
                                       alignChar, margin)
        headInf      = self._singleSep(headInfChar, alignSens, wcpis, 
                                       alignChar, margin, 
                                       indicadeAlign=True)
        noHead       = self._singleSep(noHeadChar, alignSens, wcpis, 
                                       alignChar, margin,
                                       indicadeAlign=True)
        tabBody      = self._singleSep(tabBodyChar, alignSens, wcpis, 
                                       alignChar, margin)
        tabEnd       = self._singleSep(tabEndChar, alignSens, wcpis, 
                                       alignChar, margin, end=True)

        self.formedSeparators = HorizontalComposition(
            headSup, headInf, noHead, tabBody, tabEnd
            )

        return self.formedSeparators

    def _singleSep(self, 
                   chars, 
                   alignSensitive, 
                   sidesToIndCenter, 
                   alignChar, 
                   margin, 
                   indicadeAlign=False,
                   end=False):
        if chars == '':
            return ''
        else:
            left = self.__checkNone(chars.left)
            middle = self.__checkNone(chars.middle)
            inter = self.__checkNone(chars.intersection)
            right = self.__checkNone(chars.right)
            
            middleLines = [middle * (size + (margin*2)) for size in self.colSizes]

            if alignSensitive and indicadeAlign:
                sidesChar = self.__checkNone(alignChar.sides)
                centerChar = self.__checkNone(alignChar.center)
                for i in range(len(middleLines)):
                    if self.colAlginment[i] == 'l':
                        if sidesChar != '':
                            middleLines[i] = ''.join([sidesChar, middleLines[i][1:]])
                    elif self.colAlginment[i] == 'r':
                        if sidesChar != '':
                            middleLines[i] = ''.join([middleLines[i][:-1], sidesChar])
                    elif self.colAlginment[i] == 'c' or self.colAlginment[i] == 'f':
                        if centerChar != '':
                            if sidesToIndCenter:
                                middleLines[i] = ''.join(
                                    [centerChar,
                                    middleLines[i][1:-1],
                                    centerChar]
                                    )
                            else:
                                lineCenter = self.__findLineCenter(middleLines[i])
                                middleLines[i] = ''.join(
                                    [middleLines[i][:lineCenter-1], 
                                    centerChar,
                                    middleLines[i][lineCenter:]]
                                    )
            if end:
                fin = ''
            else:
                fin = '\n'
            return f'{f"{inter}".join(middleLines)}'.join([left, ''.join([right, fin])])  

    def __findLineCenter(self, line: str) -> int:
        lenLine = len(line)
        divided = int(lenLine/2)
        if (divided * 2) < lenLine:
            divided += lenLine - (divided * 2)

        return divided

    def __checkNone(self, x):
        if x == None:
            return ''
        else:
            return x


if __name__ == '__main__':
    seps = Separators(['c', 'r'], [12, 4], 'pipes')._makeSeparators()
    x = ''.join(seps)
    print(x)

