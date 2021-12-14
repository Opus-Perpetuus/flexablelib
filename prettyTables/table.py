"""
Print formatted tabular data in different styles
"""

# FORMATION OF THE TABLE
#
# Main Class.
# Here the whole table is formed

from columns import _column_sizes, _typify_column
from utils import get_window_size, is_bytes
from cells import _wrap_cells
from styleCompositions import __style_compositions
style_catalogue = __style_compositions._asdict()


class Table(object):
    """
    TABLE

    Makes a table out of tabular like data

        STYLE NAMES LIST

            plain

        # Box drawing Tables
            pretty_grid
            pretty_columns
            bold_header
            bheader_columns
            bold_eheader
            beheader_columns
            bheader_ebody
            round_edges
            re_eheader
            re_ebody

            # Thin borderline
                thin_borderline
                th_bd_eheader
                th_bd_ebody
                th_bd_empty
            # Bold Borderline
                bold_borderline
                bd_bl_eheader
                bd_bl_ebody
                bd_bl_empty

        # +-|~oO:
            pwrshll_alike
            presto
            grid
            grid_eheader
            grid_ebody
            grid_empty
            pipes
            tilde_grid
            tilg_eheader
            tilg_columns
            tilg_empty
            orgtbl

        # Simple (horizontal lines)
            clean
            simple
            simple_bold
            simple_head
            simple_head_bold
            sim_th_bl
            sim_bd_bl
            sim_head_th_bl
            sim_head_bd_bl

        # Other
            dashes
    """

    def __init__(self, rows=None, columns=None, headers=None, style_name='pwrshll_alike',
                 missing_val='', str_align=None, int_align=None, float_align=None,
                 bool_align=None, table_align=None, col_alignment=None, spaces=0):

        # +------------------------+ PARAMETERS +------------------------+
        self.missing_val = missing_val
        self.str_align = str_align
        self.int_align = int_align
        self.float_align = float_align
        self.bool_align = bool_align
        self.table_align = table_align
        self.general_table_alignment = col_alignment
        self.add_index = False
        self.i_start = 0
        self.i_step = 1
        self.parse_numbers = True
        self.parse_str_numbers = False
        self.window_size = get_window_size()
        self.adjust_to_window = True
        self.auto_wrap_text = False
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
        self.style_name = style_name
        self.show_margin = True
        self.show_empty_columns = False
        self.show_empty_rows = False
        self.generic_column_name = 'column'
        # +------------------+ TABLE CHARACTERISTICS +-------------------+
        self.show_headers = True
        self.table_height = 0
        self.table_width = 0
        self._line_spacing = 0
        self._real_row_count = 0
        self._real_column_count = 0
        self._include_header_in_row_count = False
        self._cell_types = {}
        self._column_types = {}
        self._column_types_as_list = []
        self._column_widths = {}
        self._column_widths_as_list = []
        self._table_alignment = 'l'
        self._column_alignments = {}
        self._column_alignments_as_list = []
        self._row_alignments = {}
        self._row_alignments_as_list = []
        self._cells_alignment = []
        # +------------------------+ TABLE BODY +------------------------+
        self.columns = {} if columns is None else columns
        self.headers = [] if headers is None else headers
        self.rows = [] if rows is None else rows
        # TODO add table structure
        self._processed_columns = {}
        self._processed_headers = []
        self._processed_rows = []
        self.__table_string = ''
        # +-----------------------+ INIT ACTIONS +-----------------------+

    # +-----------------------------------------------------------------------------+
    # start +---------------------------+ METHODS +---------------------------+ start

    def __str__(self):
        return self.compose()

    # end +-----------------------------+ METHODS +-----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------------+ PROPERTIES +--------------------------+ start

    @property
    def _style_composition(self):
        try:
            return style_catalogue[self.style_name]
        except KeyError:
            return style_catalogue['pwrshll_alike']

    @property
    def _empty_row_indexes(self):
        none_type_rows = []
        for i, row in enumerate(self.rows):
            if row.count(None) == len(row):
                none_type_rows.append(i)
        return none_type_rows

    @property
    def _empty_column_indexes(self):
        none_type_columns = []
        for i, type_name in enumerate(self._column_types_as_list):
            if type_name == 'NoneType':
                none_type_columns.append(i)
        return none_type_columns

    @property
    def row_count(self):
        """
        This count consideres if empty rows are shown or not
        """
        if self.show_empty_rows:
            return self._real_row_count
        else:
            updated_row_count = self._real_row_count - len(self._empty_row_indexes)
            return updated_row_count

    @property
    def column_count(self):
        """
        This count checks if empty columns are set to show
        """
        if self.show_empty_columns:
            return self._real_column_count
        else:
            updated_column_count = self._real_column_count - len(self._empty_column_indexes)
            return updated_column_count

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
        column_header = self._add_column_header(header)
        self._add_column_data(data, column_header)
        self._adjust_columns_to_row_count()
        self._check_existent_rows_vs_row_count()
        self._transpose_column_to_rows(data)
        self._adjust_rows_to_column_count(False, 1)

        return self.columns

    def _add_column_header(self, header):
        if header is None:
            header = f'{self.generic_column_name} {len(self.headers) + 1}'
        else:
            header = str(header)
            if header in self.headers:
                header = f'{header} {self.headers.count(header) + 1}'
        self.__check_if_header_is_going_to_be_displayed()
        self.headers.append(header)
        self._column_widths[header] = 0
        self._column_types[header] = None
        self._column_alignments[header] = ''
        self._cell_types[header] = []
        self.columns[header] = []

        return header

    def _add_column_data(self, data, column_header):
        if data is not None:
            if (len(data) + (1 if self._include_header_in_row_count else 0)) > self._real_row_count:
                self._real_row_count += (
                    len(data) + (1 if self._include_header_in_row_count else 0)
                ) - self._real_row_count
            self.columns[column_header] += data
        self._real_column_count += 1

        return column_header, self.columns[column_header]

    def _adjust_columns_to_row_count(self, rows_added_before=False):
        for header, column_body in self.columns.items():
            if len(column_body) < self._real_row_count - int(self.show_headers):
                difference = (self._real_row_count - len(column_body)) - int(self.show_headers)
                if rows_added_before:
                    [self.columns[header].insert(0, self.missing_val) for _ in range(difference)]
                else:
                    self.columns[header] += [self.missing_val for _ in range(difference)]

    def _transpose_column_to_rows(self, data):
        for column_i in range(self._real_column_count):
            for row_i in range(self._real_row_count - int(self.show_headers)):
                if data is None:
                    self.__fill_row_from_empty_column(row_i, column_i)
                else:
                    self.__fill_row_from_column(row_i, column_i, data)

    def __check_if_header_is_going_to_be_displayed(self):
        if self._include_header_in_row_count is False:  # if header gets added, add 1 to count just once
            if self.show_headers is True:
                self._real_row_count += 1
                self._include_header_in_row_count = True

    def __fill_row_from_empty_column(self, row_i, column_i):
        if column_i == self._real_column_count - 1:
            self.rows[row_i].append(self.missing_val)
        else:
            self.__fill_row_missing_values_from_column(row_i, column_i)

    def __fill_row_from_column(self, row_i, column_i, data):
        if column_i == self._real_column_count - 1:
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
        add_headers = True if added_to_column_count is not None else False
        self._adjust_rows_to_column_count(add_headers, added_to_column_count)
        self._transpose_row_to_columns(data)
        self._adjust_columns_to_row_count(rows_added_before=True)

    def _add_row_data(self, data):
        self.rows.append([])
        self._real_row_count += 1
        if data is None:
            [self.rows[-1].append(self.missing_val) for _ in range(self._real_column_count)]
        else:
            return self.__check_data_and_fill_last_row(data)

    def _adjust_rows_to_column_count(self, there_is_headers_to_add, count_of_new_headers):
        if there_is_headers_to_add:
            [self._add_column_header(None) for _ in range(count_of_new_headers)]
        for row_i in range(self._real_row_count - int(self.show_headers)):
            if len(self.rows[row_i]) < self._real_column_count:
                difference = self._real_column_count - len(self.rows[row_i])
                [self.rows[row_i].append(self.missing_val) for _ in range(difference)]

    def _transpose_row_to_columns(self, data):
        column_headers = tuple(self.columns.keys())
        for column_i in range(self._real_column_count):
            if data is None:
                self.__fil_column_from_empty_row(column_headers, column_i)
            else:
                self.__fill_column_from_row(column_headers, column_i, data)

    def _check_existent_rows_vs_row_count(self):
        if len(self.rows) < self._real_row_count - int(self.show_headers):
            rows_to_add = (self._real_row_count - int(self.show_headers)) - len(self.rows)
            [self.rows.append([]) for _ in range(rows_to_add)]

    def __check_data_and_fill_last_row(self, data):
        added_columns_to_count = None
        if len(data) > self._real_column_count:
            added_columns_to_count = len(data) - self._real_column_count
            self._real_column_count += added_columns_to_count
        for column_i in range(self._real_column_count):
            try:
                self.rows[-1].append(data[column_i])
            except IndexError:
                self.rows[-1].append(self.missing_val)
        return added_columns_to_count

    def __fil_column_from_empty_row(self, column_headers, column_i):
        try:
            self.columns[column_headers[column_i]].append(self.missing_val)
        except IndexError:
            pass

    def __fill_column_from_row(self, column_headers, column_i, data):
        try:
            self.columns[column_headers[column_i]].append(data[column_i])
        except IndexError:
            self.__fil_column_from_empty_row(column_headers, column_i)

    # end +---------------------------+ ROW ADDING +----------------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +-------------------+ STRING TABLE COMPOSITION +------------------+ start

    # +----------------------+ NUMBER PARSING +----------------------+
    def __parse_numbers(self):
        pass

    def __parse_float(self):
        pass

    def __parse_int_boolean(self):
        pass

    def __pase_exponentials(self):
        pass

    def __parse_bytes(self):
        pass

    def __parse_escape_codes(self):
        pass

    # +------------------------+ TABLE BODY +------------------------+

    def compose(self):
        self._typify_table()
        self._parse_data()  # TODO add parsing
        self._wrap_data()
        self._get_column_widths()

        return self.__table_string

    def _typify_table(self):
        for header, column_content in self.columns.items():
            cell_types, column_type, column_alignment = _typify_column(column_content)
            self._column_types[header] = column_type
            self._cell_types[header] = cell_types
            self._column_alignments[header] = column_alignment
            self._column_alignments_as_list.append(column_alignment)
            self._column_types_as_list.append(column_type)

    def _get_column_widths(self):
        sizes = _column_sizes(self._processed_columns)
        self._column_widths_as_list += sizes
        for i, column in enumerate(self.columns.items()):
            header, _ = column
            self._column_widths[header] = sizes[i]

    def _wrap_data(self):
        rows = self.rows
        headers = self.headers
        processed_headers, processed_rows = _wrap_cells(headers, rows)
        processed_columns, transformed_headers = _wrap_cells(processed_headers, processed_rows, columns=True)
        self._processed_headers = processed_headers
        self._processed_rows = processed_rows
        for i, column in enumerate(self.columns.items()):
            header, data = column
            self._processed_columns[header] = {
                'header': transformed_headers[i],
                'data': processed_columns[i]
            }

    def _parse_data(self):
        pass

    def _update_string_table(self):
        pass

    # +------------------------+ TABLE BODY +------------------------+

    # end +---------------------+ STRING TABLE COMPOSITION +--------------------+ end
    # +-----------------------------------------------------------------------------+

    # +-----------------------------------------------------------------------------+
    # start +------------------------+ DATA READING +-------------------------+ start

    def _read_pandas_dataframe(self):
        pass

    def _read_csv_file(self):
        pass

    def _read_html_table(self):
        pass

    def _read_text_file(self):
        pass

    # end +--------------------------+ DATA READING +---------------------------+ end
    # +-----------------------------------------------------------------------------+

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
    new_table.show_empty_columns = True
    new_table.show_empty_rows = True
    new_table.show_headers = True
    new_table.missing_val = None
    new_table.add_column('Header 1', [1, 2, True, False, True, True])
    new_table.add_column()
    new_table.add_column('Another\nColumn', ['e', 'e', 'e', 'Data 4-1'])
    new_table.add_column('Header 1.1', [b'data1', b'2', b'\x01', b'', b'b16asd65', b'1177'])
    new_table.add_column('Header 1.1', [2.112, .1651, 5156.1, 12.23, 98.1, 10.0135, .165165])
    new_table.add_column('another', data=['Very wide\nsentence', 'Another wrapped\nphrase', 'Yes\nINDEED\nit is'])
    new_table.add_column()
    new_table.add_column('another', data=[True, False])
    new_table.add_row()
    # new_table.add_row(['Data 7-1',
    #                    'Data 7-2',
    #                    'Data 7-3',
    #                    'Data 7-4',
    #                    'Data 7-5',
    #                    'Data 7-6',
    #                    'Data 7-7',
    #                    'Data 7-8',
    #                    'Data 7-9',
    #                    'Data 7-10',
    #                    'Data 7-11'])
    new_table.style_name = 'pretty_columns'
    print(new_table)
    print('-------------ROWS------------')
    print(new_table.headers, end='\n\n')
    list(map(print, new_table.rows))
    print('-------------ROWS------------')
    print('-------PROCESSED ROWS--------')
    list(map(print, new_table._processed_headers))
    print('\n')
    list(map(lambda x: print('\n'.join(list(map(str, x))), '\n'), new_table._processed_rows))
    print('-------PROCESSED ROWS--------')
    print('------PROCESSED COLUMNS------')
    print(new_table._processed_columns)
    print('------PROCESSED COLUMNS------')
    print(new_table.window_size)
    print('_column_alignments_as_list: ', new_table._column_alignments_as_list)
    print('col_widths_as_list: ', new_table._column_widths_as_list)
    print('_column_types_as_list: ', new_table._column_types_as_list)
    print(f'HxW: {new_table.table_height} x {new_table.table_width}')
    print(f'Row count: {new_table.row_count}')
    print(f'Column count: {new_table.column_count}')
    print(f'Empty columns: {new_table._empty_column_indexes}')
    print(f'Empty rows: {new_table._empty_row_indexes}')


if __name__ == '__main__':
    test()
    # print('This is not supposed to be shown!')
