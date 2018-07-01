
'''
csv_io.py is a simple csv reading and writing library made for use with NoteR.

Copyright (C) 2018  John Chen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import csv

field_order = ['Main Findings','Method Notes','Tags','Short Name','PMID','Title','DOI']

def csv_in(path, delimiter='\t'):

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        data = []
        for row in reader:
            data.append(row)
    return data

def csv_out(data, path, delimiter='\t', header_only=False, header_from_data=True):

    with open(path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = field_order
        if header_from_data:
            fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames, delimiter=delimiter)
        writer.writeheader()
        if not header_only:
            writer.writerows(data)

def find_row(data, key, value):
    for i in range(len(data)):
        if data[i][key] == value:
            return i
    return -1

if __name__ == '__main__':
    data=csv_in('txt_records/MBL_papers_noter.tab')
    csv_out(data, 'txt_records/write_test.tab')
