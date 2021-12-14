""" SEPARATORS OF THE TABLE """

from styleCompositions import __style_compositions, HorizontalComposition


class Separators(object):
    """ 
    # Separators

    Separators or division lines of the table.
    ```
    colAlignment: list[str] # ['l', 'r', 'c', ...]
    colSizes: list[int] # [12, 4, ...]
    style_name: str
    ```
    """

    def __init__(self, colAlignment, colSizes, styleName):
        self.colAlginment = colAlignment
        self.formedSeparators = None
        self.colSizes = colSizes
        self.styleName = styleName
        self.style = __style_compositions._asdict()[self.styleName]

    def _makeSeparators(self):

        options = self.style.table_options
        alignSens = options.align_sensitive
        alignChar = self.__checkNone(options.align_indicator)
        wcpis = options.when_centered_put_in_sides
        margin = options.margin

        horiComp = self.style.horizontal_composition
        headSupChar = self.__checkNone(horiComp.header_superior)
        headInfChar = self.__checkNone(horiComp.header_inferior)
        noHeadChar = self.__checkNone(horiComp.starts_with_no_header)
        tabBodyChar = self.__checkNone(horiComp.table_body)
        tabEndChar = self.__checkNone(horiComp.table_end)

        headSup = self._singleSep(headSupChar, alignSens, wcpis,
                                  alignChar, margin)
        headInf = self._singleSep(headInfChar, alignSens, wcpis,
                                  alignChar, margin,
                                  indicadeAlign=True)
        noHead = self._singleSep(noHeadChar, alignSens, wcpis,
                                 alignChar, margin,
                                 indicadeAlign=True)
        tabBody = self._singleSep(tabBodyChar, alignSens, wcpis,
                                  alignChar, margin)
        tabEnd = self._singleSep(tabEndChar, alignSens, wcpis,
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

            middleLines = [middle * (size + (margin * 2)) for size in self.colSizes]

            if alignSensitive and indicadeAlign:
                sidesChar = self.__checkNone(alignChar.sides)
                centerChar = self.__checkNone(alignChar.center)
                for i in range(len(middleLines)):
                    if self.colAlginment[i] == 'l':
                        if sidesChar != '':
                            middleLines[i] = ''.join([sidesChar, middleLines[i][1:]])
                    elif self.colAlginment[i] == 'r' or self.colAlginment[i] == 'f':
                        if sidesChar != '':
                            middleLines[i] = ''.join([middleLines[i][:-1], sidesChar])
                    elif self.colAlginment[i] == 'c':
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
                                    [middleLines[i][:lineCenter - 1],
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
        divided = int(lenLine / 2)
        if (divided * 2) < lenLine:
            divided += lenLine - (divided * 2)

        return divided

    def __checkNone(self, x):
        if x == None:
            return ''
        else:
            return x


if __name__ == '__main__':
    print('Don\'t do it')
