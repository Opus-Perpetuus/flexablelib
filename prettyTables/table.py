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
                 missing_val='', strAlign=None, intAlign=None, floatAlign=None,
                 boolAlign=None, tableAlign=None, col_alignment=None, spaces=0):

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
        # +------------------------+ TABLE BODY +------------------------+
        self.columns = {} if columns is None else columns
        self.headers = [] if headers is None else headers
        self.rows = [] if rows is None else rows
        # +-----------------------+ INIT ACTIONS +-----------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ PROPERTIES +--------------------------+ start

    # end +---------------------------+ PROPERTIES +----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ COLUMN ADDING +------------------------+ start

    def add_column(self, header=None, data=None):
        """
        Add a column to the table.
        Can be left empty to add an empty column.

        :param header: The title of the column.
                       If not provided, gets filled with
                       a generic name.
        :param data: Data provided as any iterable.
                     If not provided, column gets filled
                     with the missing value.
                     If the column is greater than the
                     table row count, new rows gets
                     added, and the new spaces in other
                     columns filled with missing value,
                     but if smaller, the remaining
                     spaces of the column get those
                     instead.
        """
        column_title = self._add_header_title(header)
        self._add_column_data(data, column_title)
        self._adjust_columns_to_row_count()
        self._check_existent_rows_vs_row_count()
        self._transpose_column_to_rows(data)

        return self.columns

    def _add_header_title(self, header):
        if header is None:
            header = f'{self.generic_column_name} {len(self.headers) + 1}'
        else:
            self.__check_if_header_added_from_column()
            header = str(header)
            if header in self.headers:
                header = f'{header} {self.headers.count(header) + 1}'
        self.headers.append(header)
        self.columns[header] = []

        return header

    def _add_column_data(self, data, column_title):
        if data is not None:
            if (len(data) + (1 if self._include_header else 0)) > self._row_count:
                self._row_count += (len(data) + (1 if self._include_header else 0)) - self._row_count
            self.columns[column_title] += data
        self._column_count += 1

        return column_title, self.columns[column_title]

    def _adjust_columns_to_row_count(self, rows_added_after=False):
        for title, column_body in self.columns.items():
            if len(column_body) < self._row_count - int(self.show_headers):
                difference = (self._row_count - len(column_body)) - int(self.show_headers)
                if rows_added_after:
                    print('DIF: ', difference)
                    [self.columns[title].insert(0, self.missing_val) for _ in range(difference)]
                else:
                    self.columns[title] += [self.missing_val for _ in range(difference)]

    def _transpose_column_to_rows(self, data):
        for column_i in range(self._column_count):
            for row_i in range(self._row_count - int(self.show_headers)):
                if data is None:
                    self.__fill_empty_row_from_column(row_i, column_i)
                else:
                    self.__fill_row_from_column(row_i, column_i, data)

    def __check_if_header_added_from_column(self):
        if self._include_header is False:  # if header gets added, add 1 to count just once
            if self.show_headers is True:
                self._row_count += 1
                self._include_header = True

    def __fill_empty_row_from_column(self, row_i, column_i):
        if column_i == self._column_count - 1:
            self.rows[row_i].append(self.missing_val)
        else:
            self.__fill_row_missing_values_from_column(row_i, column_i)

    def __fill_row_from_column(self, row_i, column_i, data):
        if column_i == self._column_count - 1:
            try:
                self.rows[row_i].append(data[row_i])
            except IndexError:
                pass
        else:
            self.__fill_row_missing_values_from_column(row_i, column_i)

    def __fill_row_missing_values_from_column(self, row_i, column_i):
        try:
            self.rows[row_i][column_i]
        except IndexError:
            self.rows[row_i].append(self.missing_val)

    # end +--------------------------+ COLUMN ADDING +--------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ ROW ADDING +--------------------------+ start

    def add_row(self, data=None):
        """
        Add a row to the table. Can be left empty to add
        an empty row.

        :param data: Data provided as any iterable.
        """
        added_to_column_count = self._add_row_data(data)
        add_titles = True if added_to_column_count is not None else False
        self._adjust_rows_to_column_count(add_titles, added_to_column_count)
        self._transpose_row_to_columns(data)
        self._adjust_columns_to_row_count(rows_added_after=True)

    def _add_row_data(self, data):
        self.rows.append([])
        self._row_count += 1
        if data is None:
            [self.rows[-1].append(self.missing_val) for _ in range(self._column_count)]
        else:
            return self.__check_data_and_fill_last_row(data)

    def _transpose_row_to_columns(self, data):
        col_titles = tuple(self.columns.keys())
        for column_i in range(self._column_count):
            if data is None:
                try:
                    self.columns[col_titles[column_i]].append(self.missing_val)
                except IndexError:
                    pass
            else:
                try:
                    self.columns[col_titles[column_i]].append(data[column_i])
                except IndexError:
                    try:
                        self.columns[col_titles[column_i]].append(self.missing_val)
                    except IndexError:
                        pass

    def _check_existent_rows_vs_row_count(self):
        if len(self.rows) < self._row_count - int(self.show_headers):
            rows_to_add = (self._row_count - int(self.show_headers)) - len(self.rows)
            [self.rows.append([]) for _ in range(rows_to_add)]

    def _adjust_rows_to_column_count(self, there_is_titles_to_add, count_of_new_titles):
        if there_is_titles_to_add:
            [self._add_header_title(None) for _ in range(count_of_new_titles)]
        for row_i in range(self._row_count - int(self.show_headers)):
            if len(self.rows[row_i]) < self._column_count:
                difference = self._column_count - len(self.rows[row_i])
                [self.rows[row_i].append(self.missing_val) for _ in range(difference)]

    def __check_data_and_fill_last_row(self, data):
        added_columns_to_count = None
        if len(data) > self._column_count:
            added_columns_to_count = len(data) - self._column_count
            self._column_count += added_columns_to_count
        for column_i in range(self._column_count):
            try:
                self.rows[-1].append(data[column_i])
            except IndexError:
                self.rows[-1].append(self.missing_val)
        return added_columns_to_count

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
    new_table.show_headers = True
    new_table.missing_val = None
    new_table.add_column('Header 1', ['data1', 2])
    new_table.add_column()
    new_table.add_column('Second Column', ['Data 1', 'Data 2', 'Data3'])
    new_table.add_column('Third Column', ['Data 1-2', 'Data 2-2', 'Data3-2'])
    new_table.add_column(header='Empty Column')
    new_table.add_column('Another Column', ['Data 1-3'])
    new_table.add_column('Another Column', ['e', 'e', 'e', 'Data 4-1'])
    new_table.add_column(data=['Data 1-4', 'e', 'e', 'Data 4-2'])
    new_table.add_column(data=['Data 1-5', 'Data 2-5', 'Data 3-5', 'Data 4-5', 'Data 5-5'])
    new_table.add_row(['Data 6-1', 'Data 6-2'])
    new_table.add_row()
    new_table.add_row(['Data 7-1',
                       'Data 7-2',
                       'Data 7-3',
                       'Data 7-4',
                       'Data 7-5',
                       'Data 7-6',
                       'Data 7-7',
                       'Data 7-8',
                       'Data 7-9',
                       'Data 7-10',
                       'Data 7-11'])
    # print('columns: ', json.dumps(new_table.columns, indent=4))
    # print('------ROWS------')
    # list(map(print, new_table.rows))
    # print('------ROWS------')
    # print('headers: ', new_table.headers)
    # print('colTypes: ', new_table.colTypes)
    # print('colAlginment: ', new_table.colAlginment)
    # print('styleName: ', json.dumps(new_table.style_name, indent=4))
    # print('irregular_cols_info: ', new_table.irregular_cols_info)
    # print(f'HxW: {new_table.table_height} x {new_table.table_width}')
    # print(f'Row count: {new_table._row_count}')
    # print(f'Column count: {new_table._column_count}')
    # print(f'Include header: {new_table._include_header}')
    # print(new_table)


if __name__ == '__main__':
    test()
    # print('This is not supposed to be shown!')
