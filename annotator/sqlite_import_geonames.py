import sys
import os
import csv
import unicodecsv
import sqlite3
import time
from StringIO import StringIO
from zipfile import ZipFile
from urllib import urlopen
from get_database_connection import ANNIE_DB_PATH

def parse_number(num, default):
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return default

GEONAMES_ZIP_URL = "http://download.geonames.org/export/dump/allCountries.zip"

geonames_field_mappings = [
    ('geonameid', 'text primary key'),
    ('name', 'text'),
    ('asciiname', 'text'),
    ('alternatenames', None),
    ('latitude', 'real'),
    ('longitude', 'real'),
    ('feature_class', 'text'),
    ('feature_code', 'text'),
    ('country_code', 'text'),
    ('cc2', 'text'),
    ('admin1_code', 'text'),
    ('admin2_code', 'text'),
    ('admin3_code', 'text'),
    ('admin4_code', 'text'),
    ('population', 'integer'),
    ('elevation', None),
    ('dem', None),
    ('timezone', None),
    ('modification_date', None)
]

def read_geonames_csv():
    print "Downloading geoname data from: " + GEONAMES_ZIP_URL
    url = urlopen(GEONAMES_ZIP_URL)
    zipfile = ZipFile(StringIO(url.read()))
    print "done"
    #Loading geonames data may cause errors without this line:
    csv.field_size_limit(sys.maxint)
    with zipfile.open('allCountries.txt') as f:
        reader = unicodecsv.DictReader(f,
            fieldnames=[k for k,v in geonames_field_mappings],
            encoding='utf-8',
            delimiter='\t',
            quoting=csv.QUOTE_NONE)
        for d in reader:
            d['population'] = parse_number(d['population'], 0)
            d['latitude'] = parse_number(d['latitude'], 0)
            d['longitude'] = parse_number(d['longitude'], 0)
            if len(d['alternatenames']) > 0:
                d['alternatenames'] = d['alternatenames'].split(',')
            else:
                d['alternatenames'] = []
            yield d

def batched(array):
    batch_size = 100
    batch = []
    for idx, item in enumerate(array):
        batch.append(item)
        batch_idx = idx % batch_size
        if batch_idx == batch_size - 1:
            yield batch
            batch = []
    yield batch

def create_sqlite_db():
    if os.path.exists(ANNIE_DB_PATH):
        print "A database already exists at: " + ANNIE_DB_PATH
        return
    connection = sqlite3.connect(ANNIE_DB_PATH)
    cur = connection.cursor()
    # Create table
    cur.execute("CREATE TABLE geonames (" + ",".join([
        '"' + k + '" ' + sqltype
        for k, sqltype in geonames_field_mappings if sqltype]) + ")")
    cur.execute('''CREATE TABLE alternatenames
                 (geonameid text, alternatename text, alternatename_lemmatized text)''')
    i = 0
    geonames_insert_command = 'INSERT INTO geonames VALUES (' + ','.join([
        '?' for x, sqltype in geonames_field_mappings if sqltype]) + ')'
    alternatenames_insert_command  = 'INSERT INTO alternatenames VALUES (?, ?, ?)'
    for batch in batched(read_geonames_csv()):
        geoname_tuples = []
        alternatename_tuples = []
        for geoname in batch:
            i += 1
            total_row_estimate = 11000000
            if i % (total_row_estimate / 40) == 0:
                print i, '/', total_row_estimate, '+ geonames imported'
                connection.commit()
            geoname_tuples.append(
                tuple(geoname[field]
                    for field, sqltype in geonames_field_mappings
                    if sqltype))
            for alternatename in set(geoname['alternatenames'] + [geoname['name']]):
                alternatename_tuples.append((
                    geoname['geonameid'],
                    alternatename,
                    alternatename.lower().strip()))
        cur.executemany(geonames_insert_command, geoname_tuples)
        cur.executemany(alternatenames_insert_command, alternatename_tuples)
    cur.execute('''
    CREATE INDEX alternatename_index
    ON alternatenames (alternatename_lemmatized);
    ''')
    connection.commit()
    cur.execute('''CREATE TABLE alternatename_counts
                 (geonameid text primary key, count integer)''')
    cur.execute('''
    INSERT INTO alternatename_counts
    SELECT geonameid, count(alternatename)
    FROM geonames INNER JOIN alternatenames USING ( geonameid )
    GROUP BY geonameid
    ''')
    connection.commit()
    connection.close()

if __name__ == '__main__':
    import argparse
    create_sqlite_db()
