"""
Print formatted tabular data in different styles
"""

# FORMATION OF THE TABLE
#
# Main Class.
# Here the whole table is formed

from styleCompositions import __style_compositions as style_catalogue, HorizontalComposition
from columns import _column_sizes, _typify_column, _align_columns, _align_headers
from table_strings import _get_separators, _get_data_rows, DataRows
from utils import get_window_size, is_multi_row
from options import NONE_VALUE_REPLACEMENT
from cells import _wrap_cells

DEFAULT_STYLE = 'grid_eheader'


def _zip_columns(columns, headers=False):
    if headers:
        row = tuple(map(lambda x: x, columns))
        if is_multi_row(row):
            return tuple(zip(*row))
        else:
            return row
    else:
        half_checked_rows = zip(*columns)
        sub_zipped = tuple(map(lambda s_row: tuple(zip(*s_row)) if is_multi_row(s_row) else s_row,
                               half_checked_rows))
        return sub_zipped


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

    # _headers_added_to_count = False

    _real_row_count = 0
    _real_column_count = 0

    def __init__(self, rows=None, columns=None, headers=None, style_name='',
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
        self.show_margin = True
        self.show_empty_columns = False
        self.show_empty_rows = False
        self.generic_column_name = 'column'
        self.style_name = style_name

        # +------------------+ TABLE CHARACTERISTICS +-------------------+
        self.show_headers = True
        self.table_height = 0
        self.table_width = 0
        self._line_spacing = 0
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
        self.headers = [] if headers is None else headers  # TODO fix header adding
        self.rows = []
        if rows is not None:
            [self.add_row(row) for row in rows]
        # TODO add table structure
        self._auto_headers = []  # TODO add auto headers independency of headers
        self._processed_columns = {}
        self._processed_headers = []
        self._processed_rows = []
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
        return style_catalogue.__getattribute__(self._checked_style_name)

    @property
    def _checked_style_name(self):
        if self.style_name in self.possible_styles:
            return self.style_name
        else:
            return DEFAULT_STYLE

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
    def possible_styles(self):
        """
        Returns a tuple with the admitted style names.
        """
        return style_catalogue._fields

    @property
    def row_count(self):
        """
        This count decides if empty rows will be shown or not.
        """
        # if show headers is false, subtract it from count
        checked_real_row_count = self._real_row_count
        if self.show_empty_rows:
            return checked_real_row_count
        else:
            # if show empty rows is set to false, subtract the length of the detected empty rows
            updated_row_count = checked_real_row_count - len(self._empty_row_indexes)
            return updated_row_count

    @property
    def column_count(self):
        """
        This counts the rows based on the show_empty_columns property.

        If it is set to True, empty columns are counted.
        If it is set to False, empty columns are not counted.
        """
        if self.show_empty_columns:
            return self._real_column_count
        else:
            # if show empty columns is set to false, subtract the length of the detected empty columns
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
                     table s_row count, new rows gets
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
        # self.__check_if_header_is_going_to_be_counted()
        self.headers.append(header)
        self._column_widths[header] = 0
        self._column_types[header] = None
        self._column_alignments[header] = ''
        self._cell_types[header] = []
        self.columns[header] = []

        return header

    def _add_column_data(self, data, column_header):
        if data is not None:
            self._real_column_count += 1
            self._real_row_count += len(data) - self._real_row_count
            self.columns[column_header] += data

        return column_header, self.columns[column_header]

    def _adjust_columns_to_row_count(self, rows_added_before=False):
        for header, column_body in self.columns.items():
            if len(column_body) < self._real_row_count:
                difference = self._real_row_count - len(column_body)
                if rows_added_before:
                    [self.columns[header].insert(0, self.missing_val) for _ in range(difference)]
                else:
                    self.columns[header] += [self.missing_val for _ in range(difference)]

    def _transpose_column_to_rows(self, data):
        for column_i in range(self._real_column_count):
            for row_i in range(self._real_row_count):
                if data is None:
                    self.__fill_row_from_empty_column(row_i, column_i)
                else:
                    self.__fill_row_from_column(row_i, column_i, data)

    def __fill_row_from_empty_column(self, row_i, column_i):
        if column_i + 1 == self._real_column_count:  # +1 because column count starts from 1
            self.rows[row_i].append(self.missing_val)
        else:
            self.__fill_row_missing_values_from_column(row_i, column_i)

    def __fill_row_from_column(self, row_i, column_i, data):
        if column_i + 1 == self._real_column_count:  # +1 because column count starts from 1
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
        Add a s_row to the table. Can be left empty to add
        an empty s_row.

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
        for row_i in range(self._real_row_count):
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
        if len(self.rows) < self._real_row_count:
            rows_to_add = self._real_row_count - len(self.rows)
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

    def __parse_exponentials(self):
        pass

    def __parse_bytes(self):
        pass

    def __parse_escape_codes(self):
        pass

    # +------------------------+ TABLE BODY +------------------------+

    def compose(self):
        if len(self.columns) != 0:
            self._typify_table()
            self._parse_data()  # TODO add parsing
            self._wrap_data()
            self._get_column_widths()

        return self._form_string()

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
        list(map(self._column_widths_as_list.append, sizes))
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

    def _form_string(self):
        # Data from column dict is put in tuples
        unaligned_columns = self.__get_processed_columns_data()
        unaligned_header = self.__get_processed_columns_data(header=True)

        # Header and body rows get aligned
        aligned_header = _align_headers(self._style_composition,
                                        unaligned_header,
                                        self._column_alignments_as_list,
                                        self._column_widths_as_list)
        aligned_header = _zip_columns(aligned_header, headers=True)
        aligned_columns = _align_columns(self._style_composition,
                                         unaligned_columns,
                                         self._column_alignments_as_list,
                                         self._column_widths_as_list)
        aligned_columns = _zip_columns(aligned_columns)

        # String separators and data rows are joined
        separators: HorizontalComposition = _get_separators(
            self._style_composition,
            tuple(self._column_widths.values())
        )
        data_rows: DataRows = _get_data_rows(self._style_composition, aligned_header, aligned_columns)

        # Table string is formed
        header_superior = ''.join([separators.superior_header_line, '\n']) if (
            separators.superior_header_line is not None
        ) else NONE_VALUE_REPLACEMENT
        no_header_superior = separators.superior_header_line_no_header
        header_inferior = ''.join(['\n', separators.inferior_header_line]) if (
            separators.inferior_header_line is not None
        ) else NONE_VALUE_REPLACEMENT
        body_line = ''.join(['\n', separators.table_body_line]) if (
            separators.table_body_line is not None
        ) else NONE_VALUE_REPLACEMENT
        end_line = separators.table_end_line

        header_row = data_rows.header_row
        body_rows = data_rows.body_rows

        if self.show_headers:
            superior_row = ''.join([header_superior, header_row, header_inferior])
        else:
            superior_row = no_header_superior

        if superior_row is None and end_line is not None:
            table_string = '\n'.join([f'{body_line}\n'.join(body_rows), end_line])
        elif end_line is None and superior_row is not None:
            table_string = '\n'.join([superior_row, f'{body_line}\n'.join(body_rows)])
        elif superior_row is None and end_line is None:
            table_string = f'{body_line}\n'.join(body_rows)
        else:
            table_string = '\n'.join([superior_row, f'{body_line}\n'.join(body_rows), end_line])

        return table_string

    def __get_processed_columns_data(self, header=False):
        columns_with_headers = self._processed_columns.values()
        for column_w_h in columns_with_headers:
            get = 'header' if header else 'data'
            yield column_w_h[get]

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
    # new_table.show_headers = False
    new_table.add_row(data=[1])
    new_table.add_column(data=['Kg', 'ml'])
    new_table.headers = ['Amount', 'Unit']
    print(new_table)
    print('rows: ', new_table.row_count)
    print('columns: ', new_table.column_count)


if __name__ == '__main__':
    test()
    # print('This is not supposed to be shown!')
