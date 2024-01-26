#!/usr/bin/env python
""" See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2024 Ken Farmer
"""
#adjust pylint for pytest oddities:
#pylint: disable=missing-docstring
#pylint: disable=unused-argument
#pylint: disable=attribute-defined-outside-init
#pylint: disable=protected-access
#pylint: disable=no-self-use

import datetime as dt
from os.path import exists, join as pjoin
from pprint import pprint as pp
import sqlite3
import tempfile

import datagristle.metadata as mod



class TestCreateTable:

    def setup_method(self, method):
        self.db_dir = tempfile.TemporaryDirectory(prefix='test_gristle_metadata_').name
        self.db_file = pjoin(self.db_dir, 'gristle_metadata.db')
        self.md = mod.GristleMetaData(db_dir=self.db_dir)

        self.db_conn = sqlite3.connect(pjoin(self.db_dir, 'gristle_metadata.db'))
        self.db_conn.row_factory = sqlite3.Row

    def test_table_create(self):
        assert exists(pjoin(self.db_dir, 'gristle_metadata.db'))



class TestWrites:

    def setup_method(self, method):
        self.db_dir = tempfile.TemporaryDirectory(prefix='test_gristle_metadata_').name
        self.db_file = pjoin(self.db_dir, 'gristle_metadata.db')
        self.md = mod.GristleMetaData(db_dir=self.db_dir)

        self.db_conn = sqlite3.connect(pjoin(self.db_dir, 'gristle_metadata.db'))
        self.db_conn.row_factory = sqlite3.Row


    def test_writes_against_empty_db(self):
        filename = 'foo.csv'
        mod_datetime = dt.datetime(2024, 1, 14)
        file_bytes = 8888
        self.md.file_index_tools.set_file_index_counts(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes,
                rec_count=22,
                col_count=5)

        rows = select_row(self.db_conn, self.md, filename, mod_datetime, file_bytes)
        assert rows[0]['record_count'] == 22


    def test_writes_against_full_db(self):

        filename = 'foo.csv'
        mod_datetime = dt.datetime(2024, 1, 14)
        file_bytes = 8888
        self.md.file_index_tools.set_file_index_counts(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes,
                rec_count=22,
                col_count=5)
        rows = select_row(self.db_conn, self.md, filename, mod_datetime, file_bytes)
        assert rows[0]['record_count'] == 22

        filename = 'bar.csv'
        mod_datetime = dt.datetime(2024, 1, 15)
        file_bytes = 9999
        self.md.file_index_tools.set_file_index_counts(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes,
                rec_count=32,
                col_count=7)
        rows = select_row(self.db_conn, self.md, filename, mod_datetime, file_bytes)
        assert rows[0]['record_count'] == 32



class TestReads:

    def setup_method(self, method):
        self.db_dir = tempfile.TemporaryDirectory(prefix='test_gristle_metadata_').name
        self.db_file = pjoin(self.db_dir, 'gristle_metadata.db')
        self.md = mod.GristleMetaData(db_dir=self.db_dir)

        self.db_conn = sqlite3.connect(pjoin(self.db_dir, 'gristle_metadata.db'))
        self.db_conn.row_factory = sqlite3.Row


    def test_read_against_existing_entry(self):
        filename = 'foo.csv'
        mod_datetime = dt.datetime(2024, 1, 14)
        file_bytes = 8888
        self.md.file_index_tools.set_file_index_counts(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes,
                rec_count=22,
                col_count=5)
        foo_rec_count = self.md.file_index_tools.get_file_index_rec_count(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes)
        assert foo_rec_count == 22

        filename = 'bar.csv'
        mod_datetime = dt.datetime(2024, 1, 15)
        file_bytes = 9999
        self.md.file_index_tools.set_file_index_counts(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes,
                rec_count=32,
                col_count=7)
        bar_rec_count = self.md.file_index_tools.get_file_index_rec_count(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes)
        assert bar_rec_count == 32


    def test_read_against_nonexisting_entry(self):
        filename = 'foo.csv'
        mod_datetime = dt.datetime(2024, 1, 14)
        file_bytes = 8888

        bar_rec_count = self.md.file_index_tools.get_file_index_rec_count(filename=filename,
                mod_datetime=mod_datetime,
                file_bytes=file_bytes)
        assert bar_rec_count == -1




def select_row(db_conn,
               md,
               filename: str,
               mod_datetime,
               file_bytes) -> list:

    hash = md.file_index_tools._hash_file_index(filename=filename,
            mod_datetime=mod_datetime,
            file_bytes=file_bytes)

    sql = """ SELECT *
              FROM file_index
              WHERE file_hash = :file_hash
          """
    cursor = db_conn.cursor()
    result = cursor.execute(sql, {'file_hash': hash})
    rows = result.fetchall()
    #pp([dict(row) for row in rows])
    return rows

