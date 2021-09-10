""" CELLS OF THE TABLE """


class Cells(object):
    """ 
    # Cells

    Cells of data that conforms the table.
    ```
    headers : list[any] | tuple[any] | str
    body    : list[list[any]] | tuple[tuple[any]]

    # Where to adjust body and headers
    exBoTo  : 'l' | 'r' 
    exHeTo  : 'l' | 'r' 
    """
    def __init__(self, headers, body, exBoTo, exHeTo) -> None:
        self.headers = body[0] if headers == 'firstrow' else headers 
        self.body    = body
        self.exBoTo  = exBoTo
        self.exHeTo  = exHeTo

    def _addBodySpacing(self, x: int, y: int, left: int, right: int):
        """ 
        ### Add Body Spacing

        Add spaces to a specific cell of the body
        ```
        x     : int (column)
        y     : int (row)
        left  : int (space to ad to the left) 
        right : int (space to ad to the right) 
        ```
        """
        l = ' ' * left  # Space for the left
        r = ' ' * right # Space for the right

        self.body[y][x] = ''.join([l, str(self.body[y][x]), r])

        return self.body[y][x]

    def _addHeaderSpacing(self, x: int, left: int, right: int):
        """ 
        ### Add Header Spacing

        Add spaces to a specific cell of the header
        ```
        x     : int (column)
        left  : int (space to ad to the left) 
        right : int (space to ad to the right) 
        ```
        """
        l = ' ' * left  # Space for the left
        r = ' ' * right # Space for the right

        self.headers[x] = ''.join([l, str(self.headers[x]), r])

        return self.headers[x]

    def _adjustCellsPerRow(self):
        """ 
        ### Adjust Cells Per Row

        This makes the cells per row the same  (if different)
        """

        hlen = len(self.headers)
        mlen = max([len(x) for x in self.body] + [hlen])

        if hlen < mlen:
            self.headers = self.__adjustSingleRow(self.headers, mlen - hlen, True)
        for row in range(len(self.body)):
            blen = len(self.body[row])
            if blen < mlen:
                self.body[row] = self.__adjustSingleRow(self.body[row], mlen - blen)

        return self.headers, self.body
        
    def __adjustSingleRow(self, row, diff, header=False):
        for _ in range(diff):
            if header:
                if self.exHeTo == 'l':
                    row.insert(0, '')
                elif self.exHeTo == 'r':
                    row.append('')
            else:
                if self.exBoTo == 'l':
                    row.insert(0, '')
                elif self.exBoTo == 'r':
                    row.append('')

        return row


if __name__ == '__main__':
        
    cells = Cells(['h1', 'h2'], [[1, 2, 3, 4], ['is', 'not'], [True, False, True]], 'r', 'r')
    cells._adjustCellsPerRow()
    cells._addBodySpacing(0, 0, 1, 1)
    table = [cells.headers, cells.body]

    print(table[0])
    [print(x) for x in table[1]]