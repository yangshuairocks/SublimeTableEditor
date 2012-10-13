# tablelib.py - pretty print text table.

# Copyright (C) 2012  Free Software Foundation, Inc.

# Author: Valery Kocubinsky
# Package: SublimeTableEditor
# Homepage: https://github.com/vkocubinsky/SublimeTableEditor

# This file is part of SublimeTableEditor.

# SublimeTableEditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SublimeTableEditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with SublimeTableEditor.  If not, see <http://www.gnu.org/licenses/>.

import re


class TableStyle:

    def __init__(self, hline_out_border='|',
                        hline_in_border='|'):
        self.vline = '|'
        self.hline_out_border = hline_out_border
        self.hline_in_border = hline_in_border
        self.hline_chars = set([self.vline, hline_out_border, hline_in_border])

    def __str__(self):
        return """
{0} a {0} b {0}
{1}---{2}---{1}""".format(
                    self.vline,
                    self.hline_out_border,
                    self.hline_in_border
                    )

    def hline_border_pattern(self):
        return "(?:" + "|".join(["(?:" + re.escape(ch) + ")" for ch in self.hline_chars]) + ")"

    def hline_pattern(self):
        return "^({0}|{1})+$".format(self.hline_border_pattern(), r"(\s*[-]+\s*)")

    def is_hline(self, text):
        return re.match(self.hline_pattern(), text) is not None

simple_style = TableStyle('|', '|')
emacs_style = TableStyle('|', '+')
grid_style = TableStyle('+', '+')


class TextTable:
    ALIGN_LEFT = 'left'
    ALIGN_RIGHT = 'right'
    ALIGN_CENTER = 'center'

    ROW_DATA = 'd'
    ROW_SEPARATOR = 's'
    ROW_HEADER = 'h'
    ROW_FORMAT = 'f'

    def __init__(self, text, style):
        self.text = text
        self.style = style
        self._rows = []
        self._row_types = []
        self._col_types = []
        self._col_lens = []

        self._header_found = False

    def _extend_list(self, list, size, fill_value):
        assert len(list) < size
        return list + [fill_value for x in range(size - len(list))]

    def _adjust_col(self, col, size, fillchar):
        assert len(col) < size
        return col.ljust(size, fillchar)

    def _norm(self, col):
        col = col.strip()
        if len(col) == 0:
            return '   '
        if col[0] != ' ':
            col = ' ' + col
        if (col[-1] != ' '):
            col = col + ' '
        return col

    def _is_row_separator(self, row):
        for col in row:
            if not re.match(r"^\s*[-]+\s*$", col):
                return False
        return True

    def is_format_row(self, row):
        for col in row:
            if not re.match(r"^\s*(<+|>+|#+)\s*$", col):
                return False
        return True

    def _merge(self, new_row):
        if self._is_row_separator(new_row):
            new_row = ['---' for col in new_row]
            self._row_types.append(TextTable.ROW_SEPARATOR)
            if not self._header_found and TextTable.ROW_DATA in self._row_types:
                for i, x in enumerate(self._row_types):
                    if x == TextTable.ROW_DATA:
                        self._row_types[i] = TextTable.ROW_HEADER
                    self._header_found = True
        elif self.is_format_row(new_row):
            new_row = [' ' + re.search("<|>|#", col).group(0) + ' '
                                                        for col in new_row]
            self._row_types.append(TextTable.ROW_FORMAT)
        else:
            new_row = [self._norm(col) for col in new_row]
            self._row_types.append(TextTable.ROW_DATA)
        self._rows.append(new_row)
        new_col_lens = [len(col) for col in new_row]
        if len(new_col_lens) < len(self._col_lens):
            new_col_lens.extend([0] * (len(self._col_lens) - len(new_col_lens)))
        elif len(self._col_lens) < len(new_col_lens):
            self._col_lens.extend([0] * (len(new_col_lens) - len(self._col_lens)))
        self._col_lens = [max(x, y) for x, y in zip(self._col_lens, new_col_lens)]

    def _split_line(self, line):
        line = line.strip()

        #remove first '|' character
        assert line[0] in self.style.hline_chars
        line = line[1:]

        #remove last '|' character
        if len(line) > 0 and line[-1] in self.style.hline_chars:
            line = line[:-1]

        if re.match(self.style.hline_pattern(), line):
            return re.split(self.style.hline_border_pattern(), line)
        else:
            return line.split('|')

    def _adjust_column_count(self):
        column_count = len(self._col_lens)
        for row in self._rows:
            row.extend(['   '] * (column_count - len(row)))

    def _auto_detect_column(self, start_row_ind, col_ind):
        for row, row_type in zip(self._rows[start_row_ind:],
                                self._row_types[start_row_ind:]):
            if row_type == TextTable.ROW_FORMAT:
                break
            elif row_type == TextTable.ROW_SEPARATOR:
                continue
            elif row_type == TextTable.ROW_HEADER:
                continue
            if len(row[col_ind].strip()) > 0 and not re.match("^\s*[0-9]*[.,]?[0-9]+\s*$", row[col_ind]):
                return TextTable.ALIGN_LEFT
        return TextTable.ALIGN_RIGHT

    def _adjust_column_width(self):
        out = []
        column_count = len(self._col_lens)
        row_count = len(self._rows)
        data_alignment = [None] * len(self._col_lens)
        for row_ind in range(row_count):
            row = self._rows[row_ind]
            row_type = self._row_types[row_ind]
            out_row = []
            for col_ind in range(column_count):
                col = row[col_ind]
                col_len = self._col_lens[col_ind]

                if row_type == TextTable.ROW_SEPARATOR:
                    col = '-' * col_len
                elif row_type == TextTable.ROW_HEADER:
                    col = col.center(col_len, ' ')
                elif row_type == TextTable.ROW_FORMAT:
                    if '<' in col:
                        data_alignment[col_ind] = TextTable.ALIGN_LEFT
                        col = ' ' + '<' * (col_len - 2) + ' '
                    elif '>' in col:
                        data_alignment[col_ind] = TextTable.ALIGN_RIGHT
                        col = ' ' + '>' * (col_len - 2) + ' '
                    elif '#' in col:
                        data_alignment[col_ind] = TextTable.ALIGN_CENTER
                        col = ' ' + '#' * (col_len - 2) + ' '
                elif row_type == 'd':
                    if (data_alignment[col_ind] is None):
                        data_alignment[col_ind] = self._auto_detect_column(row_ind, col_ind)
                    if data_alignment[col_ind] == TextTable.ALIGN_RIGHT:
                        col = col.rjust(col_len, ' ')
                    elif data_alignment[col_ind] == TextTable.ALIGN_LEFT:
                        col = col.ljust(col_len, ' ')
                    elif data_alignment[col_ind] == TextTable.ALIGN_CENTER:
                        col = col.center(col_len, ' ')
                out_row.append(col)
            out.append(out_row)
        self._rows = out

    def format_to_lines(self):
        lines = self.text.splitlines()
        assert len(lines) > 0, "Table is empty"
        self._prefix, sep, rest = lines[0].partition('|')
        for line in lines:
            cols = self._split_line(line.strip())
            self._merge(cols)
        self._adjust_column_count()
        self._adjust_column_width()

        def join_row(row):
            if self._is_row_separator(row):
                return (self.style.hline_out_border
                    + self.style.hline_in_border.join(row)
                    + self.style.hline_out_border)
            else:
                vline = self.style.vline
                return vline + vline.join(row) + vline
        return [self._prefix + join_row(row) for row in self._rows]

    def format_to_text(self):
        return "\n".join(self.format_to_lines())


def format_to_text(text, style):
    table = TextTable(text, style)
    return table.format_to_text()


def format_to_lines(text, style):
    table = TextTable(text, style)
    return table.format_to_lines()


if __name__ == '__main__':
    # each line begin from '|'

    raw_text = """| h1 | h2
              |-
              |a|1|
              |-
              |b|2|
              |-
              |c|3|"""
    print "Table:\n", format_to_text(raw_text, grid_style)
