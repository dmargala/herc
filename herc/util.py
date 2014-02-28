import csv

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel,
        codec="iso-8859-1", **kwargs):
    """Outputs utf-8 encoded strings from CSV"""
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data, codec),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell.strip(), 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data, codec):
    """A little generator for encoding data from the CSV files"""
    for line in unicode_csv_data:
        dline = line.decode(codec)
        yield dline.encode('utf-8')