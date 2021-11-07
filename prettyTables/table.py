"""
Print formatted tabular data in different styles
"""

# FORMATION OF THE TABLE
#
# Main Class.
# Here the whole table is formed


from separators import Separators
# from columns import Columns
from cells import Cells
from styleCompositions import StyleCompositions
from utils import Utils


class Table(object):
    """
    TABLE

    Makes a table out of tabular like data:
    """

    def __init__(self, rows=None, columns=None, headers=None, styleName='pwrshll_alike',
                 missing_val='NA', strAlign=None, intAlign=None, floatAlign=None,
                 boolAlign=None, tableAlign=None, col_alignment=None, spaces=0):

        # +------------------------+ TABLE BODY +------------------------+
        self.columns = {} if columns is None else columns
        self.headers = [] if headers is None else headers
        self.rows = [] if rows is None else rows
        # +------------------------+ PARAMETERS +------------------------+
        self.missing_val = missing_val
        self.str_align = strAlign
        self.int_align = intAlign
        self.float_align = floatAlign
        self.bool_align = boolAlign
        self.table_align = tableAlign
        self.col_alignment = col_alignment
        self.add_index = False
        self.i_start = 0
        self.i_step = 1
        self.parse_numbers = True
        self.parse_str_numbers = False
        self.window_size = Utils().getWIndowsSize()
        self.adjust_to_window = True
        self.expand_body_to = 'r'
        self.expand_header_to = 'r'
        self.spaces = spaces  # TODO ¿Qué es?
        self.float_spaces = 2
        self.format_exponential = True
        # +--------------------------+ STYLE +---------------------------+
        # HEADER STYLES: None, l, u, t, c
        #   None: unmodified
        #   l: lower case
        #   u: upper case
        #   t: title
        #   c: capitalized
        self.header_style = None
        self.style_name = styleName
        self.show_margin = True
        self.show_empty_columns = True
        self.generic_column_name = 'column'
        # +------------------+ TABLE CHARACTERISTICS +-------------------+
        self.irregular_cols_info = {'empty': {}, 'irregular': {}}
        self.table_height = 0
        self.table_width = 0
        self.column_types = {}
        self.show_headers = True
        self._row_count = 0
        self._column_count = 0
        self._include_header = False

    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ PROPERTIES +--------------------------+ start

    # end +---------------------------+ PROPERTIES +----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ COLUMN ADDING +------------------------+ start

    def add_column(self, header=None, data=None):
        """
        Add a columns to the table.
        header_name = [data, data, ...]
        """
        column_title = self._add_header_title(header)
        self._add_column_data(data, column_title)
        self._adjust_columns_to_count()
        self._check_existent_rows_vs_row_count()
        self._transpose_column_to_rows(data)
        # if len(self.rows) < 3:
        #     self._adjust_rows_to_count()

        return self.columns

    def _add_column_data(self, data, column_title):
        if data is not None:
            if (len(data) + (1 if self._include_header else 0)) > self._row_count:
                self._row_count += (len(data) + (1 if self._include_header else 0)) - self._row_count
            self.columns[column_title] += data
        self._column_count += 1

        return  column_title, self.columns[column_title]

    def _add_header_title(self, header):
        if header is None:
            header = f'{self.generic_column_name} {len(self.headers) + 1}'
        else:
            self.__check_if_header_added()
            header = str(header)
        self.headers.append(header)
        self.columns[header] = []

        return header

    def _transpose_column_to_rows(self, data):
        for column_i in range(self._column_count):
            for row_i in range(self._row_count - int(self.show_headers)):
                if data is None:
                    self.__fill_empty_row(row_i, column_i)
                else:
                    self.__fill_row(row_i, column_i, data)

    def _adjust_columns_to_count(self):
        for title, column_body in self.columns.items():
            if len(column_body) < self._row_count - int(self.show_headers):
                difference = len(column_body) < self._row_count - int(self.show_headers)
                self.columns[title] += [self.missing_val for _ in range(difference)]

    # end +--------------------------+ COLUMN ADDING +--------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ ROW ADDING +--------------------------+ start

    def add_row(self):
        pass

    def transpose_row_to_columns(self):
        pass

    def _check_existent_rows_vs_row_count(self):
        if len(self.rows) < self._row_count - int(self.show_headers):
            rows_to_add = (self._row_count - int(self.show_headers)) - len(self.rows)
            [self.rows.append([]) for _ in range(rows_to_add)]

    def _adjust_rows_to_count(self):
        for i in range(len(self.rows)):
            if len(self.rows[i]) < self._column_count:
                # print('loops: ', self.column_count - len(self.rows[i]))
                for x in range(self._column_count - len(self.rows[i])):
                    self.rows[i].append(self.missing_val)

    def __fill_row(self, row_i, column_i, data):
        if column_i == self._column_count - 1:
            try:
                self.rows[row_i].append(data[row_i])
            except IndexError:
                pass
        else:
            self.__fill_row_missing_values(row_i, column_i)

    def __fill_empty_row(self, row_i, column_i):
        if column_i == self._column_count - 1:
            self.rows[row_i].append(self.missing_val)
        else:
            self.__fill_row_missing_values(row_i, column_i)

    def __fill_row_missing_values(self, row_i, column_i):
        try:
            self.rows[row_i][column_i]
        except IndexError:
            self.rows[row_i].append(self.missing_val)

    def __check_if_header_added(self):
        if self._include_header is False:  # if header gets added, add 1 to count just once
            if self.show_headers is True:
                self._row_count += 1
                self._include_header = True

    # end +---------------------------+ ROW ADDING +----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-----------------------+ INIT FUNCTIONS +------------------------+ start

    def __transpose_columns(self):
        return list(zip(list(map(lambda column: column[1], iter(self.columns.items())))))

    # end +-------------------------+ INIT FUNCTIONS +--------------------------+ end
    # +-----------------------------------------------------------------------------+

    def _check_height_width(self):
        print(self.table_height, ' x ', self.table_width)

    def _read_pandas_dataframe(self):
        pass

    def _read_csv_file(self):
        pass

    def _read_html_table(self):
        pass

    def _read_text_file(self):
        pass


    # def __str__(self) -> str:
    #     return self.make()

    # def make(self):
    #     self._checkHeader()
    #     self._adjustCellsPerRow()
    #     self._wrapCells()
    #     self._transformToColumns()
    #     self._typify()
    #     self._alignFloatColumns()
    #     self._columnSizes()
    #     self._makeSeparators()
    #     self._alignHeaders()
    #     self._alignColumns()
    #     self._transformToRows()
    #     self._addVerticalSeparators()
    #     self.fullyFormed = self._unifyAll()
    #
    #     if self.spaces != 0:
    #         spaced = map(lambda x: ''.join([' ' * self.spaces, x]),
    #                      self.fullyFormed.splitlines())
    #         self.fullyFormed = '\n'.join(spaced)
    #
    #     return self.fullyFormed


def test():
    import json

    new_table = Table()
    # new_table.show_headers = False
    new_table.missing_val = None
    new_table.add_column('Header 1', ['data1', 2])
    new_table.add_column()
    new_table.add_column('Second Column', ['Data 1', 'Data 2', 'Data3'])
    new_table.add_column('Third Column', ['Data 1-2', 'Data 2-2', 'Data3-2'])
    new_table.add_column()
    new_table.add_column('Another Column', ['Data 1-3'])
    new_table.add_column('Another Column', ['e', 'e', 'e', 'Data 4-1'])
    new_table.add_column(data=['Data 1-4', 'e', 'e', 'Data 4-2'])
    new_table.add_column(data=['Data 1-5', 'Data 2-5', 'Data 3-5', 'Data 4-5', 'Data 5-5'])
    print('columns: ', json.dumps(new_table.columns, indent=4))
    print('------ROWS------')
    list(map(print, new_table.rows))
    print('------ROWS------')
    print('headers: ', new_table.headers)
    # print('colTypes: ', new_table.colTypes)
    # print('colAlginment: ', new_table.colAlginment)
    print('styleName: ', json.dumps(new_table.style_name, indent=4))
    print('irregular_cols_info: ', new_table.irregular_cols_info)
    print(f'HxW: {new_table.table_height} x {new_table.table_width}')
    print(f'Row count: {new_table._row_count}')
    print(f'Column count: {new_table._column_count}')
    print(f'Include header: {new_table._include_header}')
    # print(new_table)


if __name__ == '__main__':
    test()

    import os
    from styleCompositions import StyleCompositions

    # os.system('cls' if os.name == 'nt' else 'clear')
    # a = 1.0 / 96516.51698
    # extra1 = '╭───────────────╮\n│ MINI    TABLE │\n╞═══════╤═══════╡\n│ DATA1 │ DATA2 │\n╰───────┴───────╯'
    # extra2 = 'MINI   TABLE\nDATA1  DATA2\n'
    # normal = 'otherData2'
    #
    # headers = ['H1', 'H2', 'H3', 'H4', 'H5', 'SIZE', 'UNITY']
    # data = [
    #     ['Data1', a, True, True, True, 1, 'MB'],
    #     ['Data2', 16.144, False, False, False, 4566, 'MB'],
    #     ['otherData3', 1229.51155, True, 12, 12.25, 12, 'MB'],
    #     ['otherData4', 29.2, False, 13, 13, 13, 'MB'],
    #     ['otherData5', 548498.165, False, 13, 13, 13, 'MB'],
    #     ['otherData6', 29.545, False, 13, 13, 13, 'MB']
    # ]
    # headers2 = ['STRING', 'LEN', 'TYPE', 'ID']
    # data2 = [['gamelang Word', 13, 'Phrase', '1e8ñrz8ty136s66ñ4b8k38qn9ñadryzb5'],
    #          ['gameless Elongated', 18, 'Phrase', '4j4ycaicwenh2ñs25ñmmmr239ñ23w0bn803hcs'],
    #          ['gamelike', 8, 'Word', 'p2in3782mub17480eq72mq3pc7v9zon'],
    #          ['Gamelion', 8, 'String', '4hv2d710s6vsñ8n0ybfms2c301qr7dj'],
    #          ['gamelotte', 9, 'Word', '1tg5y3jn7xf9046681qe8o1pul50c046w29xz'],
    #          ['gamely', 6, 'String', 'mq58xu8vq84x784ngcw44w5410u28fñ'],
    #          ['gamene', 6, 'Word', '98r75qj996c379tg1kñpz10dw534m22a'],
    #          ['gameness', 8, 'String', 'yfv5886ff04sp7a1t8z30tugq3bx47jd'],
    #          ['gamesome', 8, 'Word', 'owus19312vy2hube4rdha0ej9s98v28fz'],
    #          ['gamesomely', 10, 'String', '0ms888ib3768p3khz32f8272456v219']]
    # headers3 = ['STRING', 'FLOAT']
    # data3 = [['Some string', 2.167],
    #          ['Wraped\nstring', 156.5]]

    # styles = [''] + list(StyleCompositions._asdict().keys())

    # newTable = Table([['s', 1]])
    # newTable.styleName = 'grid'
    # print(newTable.styleName)
    # print(newTable.colAlginment)
    # print(newTable)

    # with open('txt.txt', 'w', encoding='utf-8') as txt:
    #     txt.write('start\n\n')
    #
    # selHe = headers
    # selDat = data
    # for style in styles:
    #     for header in [selHe, None]:
    #         dataDisplay = ''.join(['[', *[(str(x) + ',' if selDat.index(x) == 0
    #                                        else '\n\t\t  ' + str(x) + ',')
    #                                       for x in selDat], ']'])
    #         command = f'>>> style="{style}"\n>>> headers={header}\n>>> data={dataDisplay}\n\n'
    #         if style == '':
    #             table = Table(selDat, headers=header, formatExponentials=True)
    #         else:
    #             table = Table(selDat, style, headers=header, formatExponentials=True)
    #         formed = ''.join(['>>> ', table.make().replace('\n', '\n    ')])
    #         # print(toPrint)
    #
    #         with open('txt.txt', 'a', encoding='utf-8') as txt:
    #             txt.write(command)
    #             txt.write(formed)
    #             txt.write('\n\n')

    # print('This is not supposed to be shown!')
