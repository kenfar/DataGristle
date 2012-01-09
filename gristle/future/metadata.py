#!/usr/bin/env python
""" Purpose of this module is to manage the metadata database

    To do:
       - create classes to access all tables easily through
    Model:
       - bmd_schema
       - bmd_struct_type
       - bmd_struct
       - bmd_element
       - 

"""

from __future__ import division
import sqlite3
import appdirs
import os
from sqlalchemy import *
from sqlalchemy import exc


#--- CONSTANTS -----------------------------------------------------------
def main():

    my_metadata = GristleMetaData()
    

class GristleMetaData(object):

    def __init__(self, db_dir=None, db_name='metadata.db'):
        # confirm environmentals:
        if db_dir is None:
            user_data_dir = appdirs.user_data_dir('datagristle')
        else:
            user_data_dir = db_dir
        if not os.path.exists(user_data_dir):
            print 'data dir (%s) is missing - it will be created' % user_data_dir
            os.makedirs(user_data_dir)

        self.fqdb_name  = os.path.join(user_data_dir, db_name)
        self.db         = create_engine('sqlite:////%s' % self.fqdb_name)
        self.db.echo    = False
        self.create_db()


    def create_db(self):
        """ Will create database and objects within the database if they do not
            already exist.   Will not update them if they have otherwise 
            different from this configuration however.
        """

        metadata = MetaData(self.db)
        self.schema   = Table('bmd_schema', 
                         metadata,
                         Column('schema_name', String(40),  primary_key=True),
                         Column('schema_desc', String(255), nullable=True)  )
        self.struct_type = Table('bmd_struct_type',
                         metadata,
                         Column('struct_type',      String(10),  primary_key=True),
                         Column('struct_type_desc', String(255), nullable=True) )
        self.struct = Table('bmd_struct',
                         metadata,
                         Column('struct_name',            String(40),  primary_key=True),
                         Column('struct_desc',            String(255), nullable=True), 
                         Column('schema_name',            String(40),  nullable=False), 
                         Column('struct_type',            String(10),  nullable=False),
                         Column('parent_struct_name',     String(40),  nullable=True),
                         Column('field_type',             String(10),  nullable=True),
                         Column('field_len',              Integer,     nullable=True)  )
        metadata.create_all()
 

    #---- schema methods ---------------

    def schema_list(self):
        s      = self.schema.select()
        result = s.execute()
        rows   = result.fetchall()
        return rows

    def schema_get(self, schema):
        s      = self.schema.select(self.schema.c.schema_name == schema)
        result = s.execute()
        rows   = result.fetchall()
        assert(len(rows) <= 1)
        return rows

    def schema_put(self, schema_name, schema_desc):
        try: 
           i = self.schema.insert()
           i.execute(schema_name=schema_name, schema_desc=schema_desc)
        except exc.IntegrityError:
           print 'WARNING:  schema data already exists' % locals()

    def schema_del(self, schema):
        i = self.schema.delete(self.schema.c.schema_name == schema)
        i.execute()
       

    #---- struct_type methods ------------------

    def struct_type_write(self, struct_type, struct_type_desc):
       try: 
           i = self.struct_type.insert()
           i.execute(struct_type=struct_type, struct_type_desc=struct_type_desc)
       except exc.IntegrityError:
           print 'WARNING:  struct_type data already exists' % locals()

    def struct_type_get(self, struct_type):
        s      = self.struct_type.select(self.struct_type.c.struct_type == struct_type)
        result = s.execute()
        rows   = result.fetchall()
        assert(len(rows) <= 1)
        return rows


    #---- struct methods ------------------

    def struct_write(self, struct_name, struct_desc, schema_name, struct_type, 
                     parent_struct_name, field_type, field_len ):
       try: 
           i = self.struct.insert()
           i.execute(struct_name=struct_name, struct_desc=struct_desc, schema_name=schema_name,
                     struct_type=struct_type, parent_struct_name=parent_struct_name, 
                     field_type=field_type, field_len=field_len)
       except exc.IntegrityError:
           print 'WARNING:  struct_type data already exists' % locals()


    def struct_get(self, struct_name, struct_desc, schema_name, struct_type,
                   parent_struct_name, field_type, field_len):
        s      = self.struct.select(self.struct.c.struct_name == struct_name)
        result = s.execute()
        rows   = result.fetchall()
        assert(len(rows) <= 1)
        return rows


    def generic_writer(self, table, kv):
       """ Alternate method for writing to tables
       """
       try: 
           i = table.insert()
           i.execute(kv)
       except exc.IntegrityError:
           print 'WARNING:  IntegrityError on %(table)s  - data violates a constraint' % locals()
           print 'kv: %s' % kv
           raise



if __name__ == '__main__':
   main()

