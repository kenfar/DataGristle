#!/usr/bin/env python
""" Purpose of this module is to manage the metadata database - creating tables as
    necessary, and providing put, get, delete, and list methods for all tables.

    Dependencies:
       - sqlalchemy (0.7 - though earlier versions will probably work)
       - envoy
       - appdirs

    A secondary objective is to test out some modules I haven't used previously.
    Because of this experimentation I have sometimes used a few different
    techniques (for example to run queries in sqlalchemy), and have included
    a considerable amount of comments, documentation & test harnesses.

    Basic Model:
       - schema
       - collection
       - field
       - element

    Extended Model (not yet built):
       - instance_type
       - schema_instance   - done
       - collection_instance
       - inspect_profile
       - schema_inspect
       - inspect
       - structure_inspect
       - field_value

    To do:
       - add more attributes?
       - contemplate reuse

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013 Ken Farmer
"""

from __future__ import division
import appdirs
import os
from sqlalchemy import (Table, Column, Integer, String, MetaData, DATETIME,
                        UniqueConstraint, ForeignKeyConstraint, CheckConstraint,
                        event, text, create_engine)
import datetime
#from pprint import pprint
#import envoy
import simplesql



def main():
    """ Only used for trivial testing
    """
    return



class GristleMetaData(object):
    """ Manages metadata for datagristle project.

        Upon initialization it connects to an existing sqlite database in the
        standard xdg location, or builds one as necessary.  Finally, it builds
        table objects for internal reference.

        Four tables are supported:
             - schema
             - element
             - collection
             - field

        Each of these tables supports these method types:
             - get  - given a key, will return all other attributes
             - put  - first attempts to insert row, if it hits an integrity error
                      it tries to update it.
             - del  - given a key, will delete row
             - list - will return all rows and attributes within table

        Names are standardized in the following way:  [tablename]_[method type]:
             - schema_put()
             - collection_put()
             - field_list()
             - element_list()
             - etc

        Additionally a number of reporting methods also exist.
    """

    def __init__(self, db_dir=None, db_name='metadata.db'):
        """ Gets datagristle config, and creates db objects if necessary.
        """
        if db_dir is None:
            user_data_dir = appdirs.user_data_dir('datagristle')
        else:
            user_data_dir = db_dir
        if not os.path.exists(user_data_dir):
            print 'data dir (%s) missing - it will be created' % user_data_dir
            os.makedirs(user_data_dir)

        #class FKListener(PoolListener):
        #    def connect(self, dbapi_con, con_record):
        #        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')

        self.fqdb_name  = os.path.join(user_data_dir, db_name)
        self.db         = create_engine('sqlite:////%s' % self.fqdb_name,
                                           logging_name='/tmp/gristle_sql.log')
        def _fk_pragma_on_connect(dbapi_con, con_record):
            """ turns foreign key enforcement on"""
            dbapi_con.execute('pragma foreign_keys=ON')

        event.listen(self.db, 'connect', _fk_pragma_on_connect)

        self.db.echo    = False

        self.metadata = MetaData(self.db)
        self.create_db_tables_declaratively()


    def create_db_tables_declaratively(self):
        """ Will create database and objects within the database if they do not
            already exist.   Will not update them if they have otherwise
            different from this configuration however.
        """

        self.schema_tools       = SchemaTools(self.metadata)
        self.schema             = self.schema_tools.table_create()

        self.element_tools      = ElementTools(self.metadata)
        self.element            = self.element_tools.table_create()

        self.collection_tools   = CollectionTools(self.metadata)
        self.collection         = self.collection_tools.table_create()

        self.field_tools        = FieldTools(self.metadata)
        self.field              = self.field_tools.table_create()

        self.field_value_tools  = FieldValueTools(self.metadata)
        self.field_value        = self.field_value_tools.table_create()

        self.instance_tools     = InstanceTools(self.metadata)
        self.instance           = self.instance_tools.table_create()

        self.analysis_profile_tools     = AnalysisProfileTools(self.metadata)
        self.analysis_profile           = self.analysis_profile_tools.table_create()

        self.analysis_tools             = AnalysisTools(self.metadata)
        self.analysis                   = self.analysis_tools.table_create()

        self.collection_analysis_tools  = CollectionAnalysisTools(self.metadata)
        self.collection_analysis        = self.collection_analysis_tools.table_create()

        self.field_analysis_tools       = FieldAnalysisTools(self.metadata)
        self.field_analysis             = self.field_analysis_tools.table_create()

        self.field_analysis_value_tools = FieldAnalysisValueTools(self.metadata)
        self.field_analysis_value       = self.field_analysis_value_tools.table_create()

        self.metadata.create_all()





    #---- reporting methods -------------------------------------------------
    # these are heavily-tested by test harness

    def get_data_dictionary(self, schema_name, collection_name):
        """ Returns a result set that corresponds to given
            schema & struct names.
        """
        sql = """ SELECT s.schema_name,                                   \
                         s.schema_desc,                                   \
                         col.collection_name,                             \
                         field.field_name,                                \
                         field.field_type,                                \
                         field.field_len                                  \
                  FROM schema                 s                           \
                     INNER JOIN collection    col                         \
                       ON s.schema_id        = col.schema_id              \
                     INNER JOIN field                                     \
                       ON col.collection_id  = field.collection_id        \
                  WHERE s.schema_name        = :schema_name               \
                    AND col.collection_name  = :collection_name           \
              """
        select_sql = text(sql)
        result = self.db.execute(select_sql, schema_name=schema_name,
                                 collection_name=collection_name)
        return result




class SchemaTools(simplesql.TableTools):
    """ Includes all methods for Schema table.
    """

    def table_create(self):
        """ Creates the schema table
        """
        #                UniqueConstraint(columns=['schema_name']),
        self.schema   = Table('schema'          ,
                        self.metadata           ,
                        Column('schema_id'      ,
                               Integer          ,
                               nullable=False   ,
                               primary_key=True),
                        Column('schema_name'    ,
                               String(40)       ,
                               nullable=False)  ,
                        Column('schema_desc'    ,
                               String(255)      ,
                               nullable=False)  ,
                        UniqueConstraint('schema_name', name='schema_uk1'),
                        extend_existing=True    )
        self._table      = self.schema
        self._table_name = 'schema'
        self._unique_constraints = ['schema_name']

        return self.schema


class ElementTools(simplesql.TableTools):
    """ Inclues all methods for element table
    """

    def table_create(self):
        """ Creates the 'element' table.
        """
        self.element = Table('element'                                      ,
                       self.metadata                                        ,
                       Column('element_name', String(60),  nullable=False   ,
                                                           primary_key=True),
                       Column('element_desc', String(255), nullable=False)  ,
                       Column('element_type', String(10),  nullable=False)  ,
                       Column('element_len' , Integer,     nullable=True)   ,
                       CheckConstraint ('element_len > 0 ',
                                        name='element_ck1')    ,
                       extend_existing=True )

        self._table      = self.element
        self._table_name = 'element'

        return self._table


class CollectionTools(simplesql.TableTools):
    """ Includes all methods for collection table.
    """

    def table_create(self):
        """ Handles creation of collection table.
        """

        self.collection = Table('collection',
              self.metadata,
              Column('collection_id'   , Integer       , nullable=False   ,
                     primary_key=True),
              Column('schema_id'       , Integer       , nullable=False  ),
              Column('collection_name' , String(40)    , nullable=False  ),
              Column('collection_desc' , String(256)   , nullable=False  ),
              UniqueConstraint('schema_id', 'collection_name',
                               name='collection_uk1'),
              ForeignKeyConstraint(columns=['schema_id'],
                                   refcolumns=['schema.schema_id'],
                                   name='collection_fk1') ,
                                   extend_existing=True )
        self._table      = self.collection
        self._table_name = 'collection'
        return self._table




class FieldTools(simplesql.TableTools):
    """ Includes all methods used to work with field table
    """

    def table_create(self):
        """ Creates the 'field' table.
        """

        self.field = Table('field',
            self.metadata,
            Column('field_id'        , Integer     , nullable=False   ,
                   primary_key=True),
            Column('collection_id'   , Integer     , nullable=False  ),
            Column('field_name'      , String(40)  , nullable=False  ),
            Column('field_desc'      , String(256) , nullable=True   ),
            Column('field_order'     , Integer     , nullable=True   ),
            Column('field_type'      , String(10)  , nullable=True   ),
            Column('field_len'       , Integer     , nullable=True   ),
            Column('element_name'    , String(60)  , nullable=True   ),
            UniqueConstraint('collection_id',
                   'field_name',
                   name='field_uk1'),
            ForeignKeyConstraint(columns=['collection_id'],
                   refcolumns=['collection.collection_id'],
                   name='field_fk1'),
            ForeignKeyConstraint(columns=['element_name'],
                   refcolumns=['element.element_name'],
                   name='field_fk2'),
            CheckConstraint('field_len > 0',
                   name='field_len_ck1'),
            CheckConstraint("field_type in ('string','int','date','time','timestamp','float')",
                   name='field_len_ck2'),
            CheckConstraint("( (element_name IS NULL AND field_type IS NOT NULL) \
                   OR (element_name IS NOT NULL AND field_type IS NULL) ) ",
                   name='field_ck3') ,
            CheckConstraint("  (field_type IS NULL AND field_len IS NULL)   \
                   OR (field_type  = 'string' AND field_len IS NOT NULL)    \
                   OR (field_type <> 'string' AND field_len IS NULL)  ",
                   name='field_ck4') ,
            extend_existing=True )
        self._table      = self.field
        self._table_name = 'field'
        self.instance    = None # assigned in InstanceTools
        return self._table


class FieldValueTools(simplesql.TableTools):
    """ Includes all methods used to work with the field value table
    """

    def table_create(self):
        """ Creates the 'field_value' table.
        """

        self.field_value = Table('field_value',
            self.metadata,
            Column('field_id'        , Integer     , nullable=False  ),
            Column('fv_value'        , String(256) , nullable=False  ),
            Column('fv_desc'         , String(2048),                 ),
            Column('fv_issues'       , String(2048),                 ),
            UniqueConstraint('field_id',
                   'fv_value',
                   name='field_value_uk1'),
            ForeignKeyConstraint(columns=['field_id'],
                   refcolumns=['field.field_id'],
                   name='field_value_fk1'),
            extend_existing=True )
        self._table      = self.field_value
        self._table_name = 'field_value'
        return self._table



class InstanceTools(simplesql.TableTools):
    """ Includes all methods for working with 'instance' table.
    """

    def table_create(self):
        """ Creates the 'instance' table.
        """
        self.instance = Table('instance' ,
             self.metadata           ,
             Column('instance_id'    ,
                    Integer          ,
                    nullable=False   ,
                    primary_key=True),
             Column('schema_id'      ,
                    Integer          ,
                    nullable=False  ),
             Column('instance_name'  ,
                    String(255)      ,
                    nullable=False  ),
             UniqueConstraint('schema_id','instance_name', name='instance_uk1'),
             ForeignKeyConstraint(columns=['schema_id'],
                                  refcolumns=['schema.schema_id'],
                                  name='instance_fk1') ,
             extend_existing=True    )

        self._table      = self.instance
        self._table_name = 'instance'
        return self._table



class AnalysisProfileTools(simplesql.TableTools):
    """ Includes all methods for the 'analysis_profile' table.
    """

    def table_create(self):
        """ Creates 'analysis_profile' table.
        """
        self.analysis_profile = Table('analysis_profile' ,
             self.metadata           ,
             Column('analysis_profile_id'    ,
                    Integer          ,
                    nullable=False   ,
                    primary_key=True),
             Column('instance_id'    ,
                    Integer          ,
                    nullable=False  ),
             Column('collection_id'  ,
                    Integer          ,
                    nullable=False  ),
             Column('analysis_profile_name'  ,
                    String(255)      ,
                    nullable=False  ),
             UniqueConstraint('instance_id','collection_id',
                              'analysis_profile_name',
                              name='analysis_profile_k1'),
             ForeignKeyConstraint(columns=['instance_id'],
                                  refcolumns=['instance.instance_id'],
                                  name='analysis_profile_fk1') ,
             ForeignKeyConstraint(columns=['collection_id'],
                                  refcolumns=['collection.collection_id'],
                                  name='analysis_profile_fk1') ,
             extend_existing=True    )

        self._table      = self.analysis_profile
        self._table_name = 'analysis_profile'
        return self._table



class AnalysisTools(simplesql.TableTools):
    """ Includes all methods for working with 'analysis' table.
    """

    def table_create(self):
        """ Creates the 'analysis' table.
        """
        # issue: default relies on python - not database, so could be bypassed
        # by raw sql inserts.
        #            onupdate=datetime.datetime.now()   ,
        #            server_default=func.current_timestamp()   ,
        #            server_default=u'CURRENT_TIMESTAMP',
        #            default='CURRENT_TIMESTAMP',
        self.analysis = Table('analysis' ,
             self.metadata           ,
             Column('analysis_id'    ,
                    Integer          ,
                    nullable=False   ,
                    primary_key=True),
             Column('instance_id'    ,
                    Integer          ,
                    nullable=False  ),
             Column('analysis_profile_id'  ,
                    Integer          ,
                    nullable=True   ),
             Column('analysis_timestamp'  ,
                    DATETIME         ,
                    default=datetime.datetime.now,
                    onupdate=datetime.datetime.now,
                    nullable=False  ),
             Column('analysis_tool'  ,
                    String(20)       ,
                    nullable=False  ),
             UniqueConstraint('instance_id','analysis_timestamp',
                    name='analysis_uk1'),
             ForeignKeyConstraint(columns=['instance_id'],
                    refcolumns=['instance.instance_id'],
                    name='analysis_fk1') ,
             ForeignKeyConstraint(columns=['analysis_profile_id'],
                    refcolumns=['analysis_profile.analysis_profile_id'],
                    name='analysis_fk2') ,
             extend_existing=True    )

        self._table      = self.analysis
        self._table_name = 'analysis'
        self.insert_defaulted.append('analysis_timestamp')
        self.update_defaulted.append('analysis_timestamp')
        return self._table


class CollectionAnalysisTools(simplesql.TableTools):
    """ Includes all methods for the 'collection_analysis' table.
    """

    def table_create(self):
        """ Creates the 'collection_analysis' table.
        """
        self.collection_analysis = Table('collection_analysis' ,
             self.metadata           ,
             Column('ca_id'          ,
                    Integer          ,
                    nullable=False   ,
                    primary_key=True ),
             Column('analysis_id'    ,
                    Integer          ,
                    nullable=False  ),
             Column('collection_id'  ,
                    Integer          ,
                    nullable=False  ),
             Column('ca_name'        ,
                    String(80)       ,
                    nullable=False  ),
             Column('ca_location'    ,
                    String(256)      ,
                    nullable=False  ),
             Column('ca_rowcount'    ,
                    Integer          ,
                    nullable=True   ),
             UniqueConstraint('analysis_id','collection_id',
                    name='collection_analysis_uk1'),
             ForeignKeyConstraint(columns=['analysis_id'],
                    refcolumns=['analysis.analysis_id'],
                    name='collection_analysis_fk1') ,
             ForeignKeyConstraint(columns=['collection_id'],
                    refcolumns=['collection.collection_id'],
                    name='collection_analysis_fk2') ,
             extend_existing=True    )

        self._table      = self.collection_analysis
        self._table_name = 'collection_analysis'
        return self._table



class FieldAnalysisTools(simplesql.TableTools):
    """ Includes all methods for the 'field_analysis' table.
    """

    def table_create(self):
        """ Creates the 'field_analysis' table.
        """
        self.field_analysis = Table('field_analysis' ,
             self.metadata           ,
             Column('fa_id'          ,
                    Integer          ,
                    nullable=False   ,
                    primary_key=True),
             Column('ca_id'          ,
                    Integer          ,
                    nullable=False  ),
             Column('field_id'       ,
                    Integer          ,
                    nullable=False  ),
             Column('fa_case'        ,
                    String(10)       ,
                    nullable=True   ),
             UniqueConstraint('ca_id','field_id'               ,
                              name='field_analysis_uk1')       ,
             ForeignKeyConstraint(columns=['ca_id']            ,
                                  refcolumns=['collection_analysis.ca_id'],
                                  name='field_analysis_fk1')   ,
             ForeignKeyConstraint(columns=['field_id']         ,
                                  refcolumns=['field.field_id'],
                                  name='field_analysis_fk2')   ,
             CheckConstraint ("fa_case IN ('lower','upper','mixed','unk')",
                              name='field_analysis_ck1')       ,
             extend_existing=True    )

        self._table      = self.field_analysis
        self._table_name = 'field_analysis'
        return self._table



class FieldAnalysisValueTools(simplesql.TableTools):
    """ Includes all methods for the 'field_analysis' table.
    """

    def table_create(self):
        """ Creates the 'field_analysis' table.
        """
        self.field_analysis_value = Table('field_analysis_value' ,
             self.metadata           ,
             Column('fav_id'         ,
                    Integer          ,
                    nullable=False   ,
                    primary_key=True),
             Column('fa_id'          ,
                    Integer          ,
                    nullable=False  ),
             Column('fav_value'      ,
                    String           ,
                    nullable=False  ),
             Column('fav_count'      ,
                    Integer          ,
                    nullable=False  ),
             UniqueConstraint('fa_id','fav_value'              ,
                              name='field_analysis_value_uk1') ,
             ForeignKeyConstraint(columns=['fa_id']            ,
                                  refcolumns=['field_analysis.fa_id'],
                                  name='field_analysis_value_fk1')   ,
             extend_existing=True    )

        self._table      = self.field_analysis_value
        self._table_name = 'field_analysis_value'
        return self._table




if __name__ == '__main__':
    main()
