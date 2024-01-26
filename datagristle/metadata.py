#!/usr/bin/env python
""" Purpose of this module is to manage the metadata database - creating tables as
    necessary, and providing put, get, delete, and list methods for all tables.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2024 Ken Farmer
"""

import datetime as dt
import hashlib
import logging
import os
from os.path import exists
from pprint import pprint as pp
import time
from typing import Tuple

import appdirs
import sqlite3




class GristleMetaData:
    """ Manages metadata for datagristle project.

        Upon initialization it connects to an existing sqlite database in the
        standard xdg location, or builds one as necessary.  Finally, it builds
        table objects for internal reference.
    """

    def __init__(self,
                 db_dir: None|str = None,
                 db_name='gristle_metadata.db'):
        """ Gets datagristle config, and creates db objects if necessary.
        """
        logging.basicConfig(filename='/tmp/datagristle_metadata.log')

        if db_dir is None:
            self.user_data_dir = appdirs.user_data_dir('datagristle')
        else:
            self.user_data_dir = db_dir
        if not exists(self.user_data_dir):
            print('data dir (%s) missing - it will be created' % self.user_data_dir)
            os.makedirs(self.user_data_dir)

        self.fqdb_name = os.path.join(self.user_data_dir, db_name)
        self.db_conn = sqlite3.connect(self.fqdb_name)
        self.db_conn.row_factory = sqlite3.Row

        self.file_index_tools = FileIndexTools(self.db_conn)
        self.file_index_tools.table_create()



class FileIndexTools():
    """ FileIndex collects a few high-level attributes about files
        encountered, generally to optimize some features so that
        they don't require slow re-processing on large files.
    """
    def __init__(self,
                 db_conn):

        self.db_conn = db_conn


    def table_create(self):
        """ Creates the 'file_index' table.

        This table avoids keeping any data that might be sensitive in any way -
        since this data is automatically cached.  So, no file names, column names,
        etc.
        """
        query = """CREATE TABLE IF NOT EXISTS file_index (
                        file_hash           CHAR(256) NOT NULL,
                        record_count        INTEGER           ,
                        column_count        INTEGER           ,
                        last_update_epoch   FLOAT     NOT NULL,
                        PRIMARY KEY(file_hash) )
                """
        self.db_conn.execute(query)

        query = """CREATE INDEX IF NOT EXISTS file_index_idx1
                        ON file_index(last_update_epoch)
                """
        self.db_conn.execute(query)


    def _hash_file_index(self,
                         filename: str,
                         mod_datetime: dt.datetime,
                         file_bytes: int) -> str:
        string = bytes(filename + mod_datetime.isoformat() + str(file_bytes), 'utf-8')
        hash_object = hashlib.sha1(string)
        hex_digest = hash_object.hexdigest()
        return hex_digest


    def get_file_index_rec_count(self,
                                 filename: str,
                                 mod_datetime: dt.datetime,
                                 file_bytes: int) -> int:
        """ Return the record count or -1 if there's no record count
        """
        file_hash = self._hash_file_index(filename, mod_datetime, file_bytes)
        sql = """ SELECT record_count
                  FROM file_index
                  WHERE file_hash = :file_hash
              """
        cursor = self.db_conn.cursor()
        result = cursor.execute(sql, {'file_hash': file_hash})
        rows = result.fetchall()
        self.update(filename, mod_datetime, file_bytes)
        try:
            return rows[0]['record_count']
        except IndexError:
            return -1


    def set_file_index_counts(self,
                              filename: str,
                              mod_datetime: dt.datetime,
                              file_bytes: int,
                              rec_count: int,
                              col_count: int) -> None:
        """ Write file_index counts
        """
        file_hash = self._hash_file_index(filename, mod_datetime, file_bytes)
        sql = """ INSERT INTO file_index
                        (file_hash,
                         record_count,
                         column_count,
                         last_update_epoch)
                    Values(:file_hash,
                            :rec_count,
                            :col_count,
                            :epoch)
                """
        curr_epoch = time.time()
        try:
            result = self.db_conn.execute(sql,
                                          {'file_hash': file_hash,
                                           'rec_count': rec_count,
                                           'col_count': col_count,
                                           'epoch': curr_epoch})
            self.db_conn.commit()
        except sqlite3.IntegrityError as err:
            raise ValueError('Insert failed. %s' % err)
        else:
            self.prune()


    def update(self,
               filename: str,
               mod_datetime: dt.datetime,
               file_bytes: int) -> None:
        """ Updates the last_update_epoch - to ensure that recently
            accessed data is not pruned prematurely.
        """
        file_hash = self._hash_file_index(filename, mod_datetime, file_bytes)
        sql = """ UPDATE file_index
                  SET last_update_epoch = :epoch
                  WHERE file_hash = :file_hash
              """
        curr_epoch = time.time()
        try:
            result = self.db_conn.execute(sql,
                                          {'file_hash': file_hash,
                                           'epoch': curr_epoch})
        except sqlite3.IntegrityError as err:
            raise ValueError('Update failed. %s' % err)


    def prune(self) -> int:
        """ Deletes any entries more than a year old
        """

        min_epoch = time.time() - (86400 * 365)
        sql = """ DELETE FROM file_index
                  WHERE last_update_epoch < :epoch
              """
        try:
            result = self.db_conn.execute(sql,
                                          {'epoch': min_epoch})
            self.db_conn.commit()
        except sqlite3.IntegrityError as err:
            raise ValueError('Delete failed. %s' % err)
        else:
            return result.rowcount




