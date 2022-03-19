#!/usr/bin/env python
""" Purpose of this module is to manage the metadata database - creating tables as
    necessary, and providing put, get, delete, and list methods for all tables.

    Dependencies:
       - sqlalchemy (0.7 - though earlier versions will probably work)
       - appdirs

    A secondary objective is to test out some modules I haven't used previously.
    Because of this experimentation I have sometimes used a few different
    techniques (for example to run queries in sqlalchemy), and have included
    a considerable amount of comments, documentation & test harnesses.

    Data Model - Data Dictionary Section
       - schema
       - collection
       - field
       - field_value
       - element

    Data Model - Instance Section
       - instance
       - analysis_profile

    Data Model - Analysis Section
       - analysis
       - collection_analysis
       - field_analysis
       - field_analysis_value

    Reporting Views
       - rpt_collection_analysis_v

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""

import datetime
import hashlib
import logging
import os
from pprint import pprint as pp
import time
from typing import Tuple, List, Dict

import appdirs
from sqlalchemy import (Table, Column, Boolean, Integer, String, Float, Index,
                        MetaData, DATETIME,
                        UniqueConstraint, ForeignKeyConstraint, CheckConstraint,
                        event, text, create_engine)
from sqlalchemy import exc

import datagristle.simplesql as simplesql




class GristleMetaData(object):
    """ Manages metadata for datagristle project.

        Upon initialization it connects to an existing sqlite database in the
        standard xdg location, or builds one as necessary.  Finally, it builds
        table objects for internal reference.

        The 11 tables included describe data structures, instances, analysis
        profiles and analysis results.

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
        logging.basicConfig(filename='/tmp/datagristle_metadata.log')
        logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

        if db_dir is None:
            user_data_dir = appdirs.user_data_dir('datagristle')
        else:
            user_data_dir = db_dir
        if not os.path.exists(user_data_dir):
            print('data dir (%s) missing - it will be created' % user_data_dir)
            os.makedirs(user_data_dir)

        self.fqdb_name = os.path.join(user_data_dir, db_name)
        self.engine = create_engine('sqlite:////%s' % self.fqdb_name)
        def _fk_pragma_on_connect(dbapi_con, con_record):
            """ turns foreign key enforcement on"""
            dbapi_con.execute('pragma foreign_keys=ON')

        event.listen(self.engine, 'connect', _fk_pragma_on_connect)

        self.engine.echo = False

        self.metadata = MetaData(self.engine)

        #-------------------------------------------------------------------
        # This explicit connection was not initially needed - originally all
        # work was performed through implicit connections.  But the need to
        # run methods like:
        #    existing_views = engine.dialect.get_view_names(connect)
        # requires the explicit connection.
        #-------------------------------------------------------------------
        self.connect = self.engine.connect()

        self.create_db_tables_declaratively()



    def create_db_tables_declaratively(self):
        """ Will create database and objects within the database if they do not
            already exist.   Will not update them if they have otherwise
            different from this configuration however.
        """

        self.schema_tools = SchemaTools(self.metadata, self.engine)
        self.schema = self.schema_tools.table_create()

        self.element_tools = ElementTools(self.metadata, self.engine)
        self.element = self.element_tools.table_create()

        self.collection_tools = CollectionTools(self.metadata, self.engine)
        self.collection = self.collection_tools.table_create()

        self.field_tools = FieldTools(self.metadata, self.engine)
        self.field = self.field_tools.table_create()

        self.field_value_tools = FieldValueTools(self.metadata, self.engine)
        self.field_value = self.field_value_tools.table_create()

        self.instance_tools = InstanceTools(self.metadata, self.engine)
        self.instance = self.instance_tools.table_create()

        self.analysis_profile_tools = AnalysisProfileTools(self.metadata, self.engine)
        self.analysis_profile = self.analysis_profile_tools.table_create()

        self.analysis_tools = AnalysisTools(self.metadata, self.engine)
        self.analysis = self.analysis_tools.table_create()

        self.collection_analysis_tools = CollectionAnalysisTools(self.metadata, self.engine)
        self.collection_analysis = self.collection_analysis_tools.table_create()

        self.field_analysis_tools = FieldAnalysisTools(self.metadata, self.engine)
        self.field_analysis = self.field_analysis_tools.table_create()

        self.field_analysis_value_tools = FieldAnalysisValueTools(self.metadata, self.engine)
        self.field_analysis_value = self.field_analysis_value_tools.table_create()

        self.file_index_tools = FileIndexTools(self.metadata, self.engine)
        self.file_index = self.file_index_tools.table_create()

        self.migration_tools = MigrationTools(self.metadata, self.engine)
        self.migration = self.migration_tools.table_create()

        self.metadata.create_all()

        # we can't easily create views with sqlalchemy - so do that manually:
        create_views(self.engine, self.connect)





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
        result = self.engine.execute(select_sql, schema_name=schema_name,
                                     collection_name=collection_name)
        return result




class SchemaTools(simplesql.TableTools):
    """ Includes all methods for Schema table.
    """

    def table_create(self):
        """ Creates the schema table
        """
        #                UniqueConstraint(columns=['schema_name']),
        self.schema = Table('schema',
                            self.metadata,
                            Column('schema_id',
                                   Integer,
                                   nullable=False,
                                   primary_key=True),
                            Column('schema_name',
                                   String(40),
                                   nullable=False),
                            Column('schema_desc',
                                   String(255),
                                   nullable=False),
                            UniqueConstraint('schema_name', name='schema_uk1'),
                            extend_existing=True)
        self._table = self.schema
        self._table_name = 'schema'
        self._unique_constraints = ['schema_name']

        return self.schema


    def insert(self, **kwargs):
        """ Inserts schema values into database.
            Inputs:
                - keyword arg of schema_name
                - keyword arg of schema_desc
            Returns:
                - lastrowid
                - rowcount
            Raises:
                - exc.IntegrityError
        """
        required_col_list = ['schema_name', 'schema_desc']
        self.validate(required_col_list, **kwargs)

        raw_sql = """ INSERT INTO schema
                      (schema_name,
                       schema_desc)
                      VALUES (:schema_name,
                              :schema_desc)
                  """
        sql    = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        schema_name=kwargs['schema_name'],
                                        schema_desc=kwargs['schema_desc'])
        except exc.IntegrityError as err:
            raise ValueError('Insert failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)


    def update(self, **kwargs):
        """ updates schema
            Inputs:
                - keyword arg of schema_name
                - keyword arg of schema_desc
            Returns:
                - lastrowid
                - rowcount
            Raises:
                - exc.IntegrityError
        """

        required_col_list = ['schema_id', 'schema_name', 'schema_desc']
        self.validate(required_col_list, **kwargs)

        raw_sql = """ UPDATE schema
                         SET schema_name = :schema_name,
                             schema_desc = :schema_desc
                       WHERE schema_id   = :schema_id
                  """
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        schema_name=kwargs['schema_name'],
                                        schema_desc=kwargs['schema_desc'],
                                        schema_id=kwargs['schema_id'])
        except exc.IntegrityError as err:
            raise ValueError('Update failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)


    @staticmethod
    def validate(required_col_list, **kwargs):
        """ Check for common schema problems.
        """
        missing_col_list = [i for i in required_col_list if i not in kwargs]
        if missing_col_list:
            raise ValueError('mandatory columns missing: %s' % missing_col_list)

        if (kwargs['schema_name'] is None
                or kwargs['schema_name'].strip() == ''):
            raise ValueError('schema_name may not be blank')





class ElementTools(simplesql.TableTools):
    """ Inclues all methods for element table
    """

    def table_create(self):
        """ Creates the 'element' table.
        """
        self.element = Table('element',
                             self.metadata,
                             Column('element_name',
                                    String(60),
                                    nullable=False,
                                    primary_key=True),
                             Column('element_desc',
                                    String(255),
                                    nullable=False),
                             Column('element_type',
                                    String(10),
                                    nullable=False),
                             Column('element_len',
                                    Integer,
                                    nullable=True),
                             CheckConstraint('element_len > 0 ',
                                             name='element_ck1'),
                             extend_existing=True)

        self._table = self.element
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
                                Column('collection_id',
                                       Integer,
                                       nullable=False,
                                       primary_key=True),
                                Column('schema_id',
                                       Integer,
                                       nullable=False),
                                Column('collection_name',
                                       String(40),
                                       nullable=False),
                                Column('collection_desc',
                                       String(256),
                                       nullable=False),
                                UniqueConstraint('schema_id',
                                                 'collection_name',
                                                 name='collection_uk1'),
                                ForeignKeyConstraint(columns=['schema_id'],
                                                     refcolumns=['schema.schema_id'],
                                                     name='collection_fk1',
                                                     ondelete='CASCADE'),
                                extend_existing=True)
        self._table = self.collection
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
                           Column('field_id',
                                  Integer,
                                  nullable=False,
                                  primary_key=True),
                           Column('collection_id',
                                  Integer,
                                  nullable=False),
                           Column('field_name',
                                  String(40),
                                  nullable=False),
                           Column('field_desc',
                                  String(256),
                                  nullable=True),
                           Column('field_order',
                                  Integer,
                                  nullable=True),
                           Column('field_type',
                                  String(10),
                                  nullable=True),
                           Column('field_len',
                                  Integer,
                                  nullable=True),
                           Column('element_name',
                                  String(60),
                                  nullable=True),
                           UniqueConstraint('collection_id',
                                            'field_name',
                                            name='field_uk1'),
                           ForeignKeyConstraint(columns=['collection_id'],
                                                refcolumns=['collection.collection_id'],
                                                name='field_fk1',
                                                ondelete='CASCADE'),
                           ForeignKeyConstraint(columns=['element_name'],
                                                refcolumns=['element.element_name'],
                                                name='field_fk2',
                                                ondelete='RESTRICT'),
                           CheckConstraint('field_len > 0',
                                           name='field_ck1'),
                           CheckConstraint("field_type in ('string','int','date','time','timestamp','float', 'unknown')",
                                           name='field_ck2'),
                           CheckConstraint("( (element_name IS NULL AND field_type IS NOT NULL) \
                                           OR (element_name IS NOT NULL AND field_type IS NULL) ) ",
                                           name='field_ck3'),
                           CheckConstraint("  (field_type IS NULL AND field_len IS NULL)   \
                                           OR (field_type  = 'string' AND field_len IS NOT NULL)    \
                                           OR (field_type <> 'string' AND field_len IS NULL)  ",
                                           name='field_ck4'),
                           extend_existing=True)
        self._table = self.field
        self._table_name = 'field'
        self.instance = None # assigned in InstanceTools
        return self._table


    def get_field_id(self,
                     collection_id,
                     field_order=None,
                     field_name=None,
                     field_type=None,
                     field_len=None,
                     field_desc=None):
        """Get field_id if one exists, ir not doesn't exist then create it.
           Return final id.
           Is used by processes that can't use the getter - because they don't
           have a pk or uk - in the first case implemented they've got collection_id
           and a field_order or field_name.  For this first implementation we'll
           assume field_order.
        """
        assert field_order is not None or field_name
        sql = """ SELECT field_id
                  FROM  field
                  WHERE collection_id  = :collection_id
                    AND field_order    = :field_order
              """
        select_sql = text(sql)
        result = self.engine.execute(select_sql,
                                     collection_id=collection_id,
                                     field_order=field_order)
        rows = result.fetchall()
        try:
            return rows[0].field_id
        except IndexError:  # No rows found
            if not field_name:
                field_name = 'field%s' % field_order
            if not field_desc:
                field_desc = 'field%s' % field_order
            return self.setter(collection_id=collection_id,
                               field_order=field_order,
                               field_name=field_name,
                               field_type=field_type,
                               field_len=field_len,
                               field_desc=field_desc)


    def insert(self, **kwargs):
        """ Inserts schema values into database.
            Inputs:
                - keyword arg of schema_name
                - keyword arg of schema_desc
            Returns:
                - lastrowid
                - rowcount
            Raises:
                - exc.IntegrityError
        """
        required_col_list = ['collection_id', 'field_name', 'field_desc',
                             'field_order', 'field_type', 'field_len',
                             'element_name']
        vkwargs = self.validate(required_col_list, **kwargs)

        raw_sql = """ INSERT INTO field
                      (collection_id,
                       field_name,
                       field_desc,
                       field_order,
                       field_type,
                       field_len)
                      VALUES (:collection_id,
                              :field_name,
                              :field_desc,
                              :field_order,
                              :field_type,
                              :field_len)
                  """
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        collection_id=vkwargs['collection_id'],
                                        field_name=vkwargs['field_name'],
                                        field_desc=vkwargs['field_desc'],
                                        field_order=vkwargs['field_order'],
                                        field_type=vkwargs['field_type'],
                                        field_len=vkwargs['field_len'])
        except exc.IntegrityError as err:
            print(sql)
            raise ValueError('Insert failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)


    def update(self, **kwargs):
        """ Updates field values into database.
            Inputs:
                - keyword args of field_id, collection_id, field_name, field_desc,
                  field_order, field_type, field_len, element_name
            Returns:
                - lastrowid
                - rowcount
            Raises:
                - exc.IntegrityError
        """
        required_col_list = ['field_id', 'collection_id', 'field_name',
                             'field_desc', 'field_order', 'field_type',
                             'field_len', 'element_name']
        vkwargs = self.validate(required_col_list, **kwargs)

        raw_sql = """ UPDATE field
                         SET collection_id  =  :collection_id,
                             field_name     =  :field_name,
                             field_desc     =  :field_desc,
                             field_order    =  :field_order,
                             field_type     =  :field_type,
                             field_len      =  :field_len,
                             element_name   =  :element_name
                             WHERE field_id =  :field_id
                  """
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        field_id=vkwargs['field_id'],
                                        collection_id=vkwargs['collection_id'],
                                        field_name=vkwargs['field_name'],
                                        field_desc=vkwargs['field_desc'],
                                        field_order=vkwargs['field_order'],
                                        field_type=vkwargs['field_type'],
                                        field_len=vkwargs['field_len'],
                                        element_name=vkwargs['element_name'])
        except exc.IntegrityError as err:
            print(sql)
            raise ValueError('Insert failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)


    @staticmethod
    def validate(self, required_col_list, **kwargs):
        """ Check for common schema problems.
        """
        missing_col_list  = [i for i in required_col_list if i not in kwargs]
        if missing_col_list:
            raise ValueError('mandatory columns missing: %s' % missing_col_list)

        if (kwargs['element_name'] == 'None'
                or kwargs['element_name'] == ''):
            kwargs['element_name'] = None
        else:
            kwargs['element_name'] = kwargs['element_name']

        if (kwargs['field_len'] == 'None'
                or kwargs['field_len'] == ''):
            kwargs['field_len'] = None
        else:
            kwargs['field_len'] = kwargs['field_len']


        if (kwargs['field_name'] is None
                or kwargs['field_name'].strip() == ''):
            raise ValueError('field_name may not be blank')

        if kwargs['element_name']:
            if kwargs['field_type'] or kwargs['field_len']:
                raise ValueError('field_type and field_len must be blank if element_name is provided')

        if kwargs['field_type'] not in ['string', 'int']:
            raise ValueError('field_type of %s is invalid.  Must be either string or int' \
                % kwargs['field_type'])

        try:
            if kwargs['field_len'] and len(kwargs['field_len']) > 0:
                if int(kwargs['field_len']) < 1:
                    raise ValueError('Field_len if provided must be > 0')
        except ValueError:
            raise ValueError('Field_len must be a non-zero integer')

        if kwargs['field_type'] == 'int' and kwargs['field_len']:
            raise ValueError('field_len must not be provided for field_type of int.')

        try:
            if kwargs['field_order']:
                if int(kwargs['field_order']) < 0:
                    raise ValueError('Field_order if provided must be >= 0')
        except ValueError:
            raise ValueError('Field_order must be a non-negative integer')

        return kwargs



class FieldValueTools(simplesql.TableTools):
    """ Includes all methods used to work with the field value table
    """

    def table_create(self):
        """ Creates the 'field_value' table.
        """

        self.field_value = Table('field_value',
                                 self.metadata,
                                 Column('field_id',
                                        Integer,
                                        nullable=False),
                                 Column('fv_value',
                                        String(256),
                                        nullable=False),
                                 Column('fv_desc',
                                        String(2048)),
                                 Column('fv_issues',
                                        String(2048)),
                                 UniqueConstraint('field_id',
                                                  'fv_value',
                                                  name='field_value_uk1'),
                                 ForeignKeyConstraint(columns=['field_id'],
                                                      refcolumns=['field.field_id'],
                                                      name='field_value_fk1',
                                                      ondelete='CASCADE'),
                                 extend_existing=True)
        self._table = self.field_value
        self._table_name = 'field_value'
        return self._table


    @staticmethod
    def validate(required_col_list, **kwargs):
        """ Check for common schema problems.
        """
        missing_col_list = [i for i in required_col_list if i not in kwargs]
        if missing_col_list:
            raise ValueError('mandatory columns missing: %s' % missing_col_list)
        return kwargs


    def insert(self, **kwargs):
        """ Inserts field_value into database.
            Inputs:
                - keyword arg of field_id, fv_value, fv_desc, and fv_issues
            Returns:
                - lastrowid
                - rowcount
            Raises:
                - exc.IntegrityError
        """
        required_col_list = ['field_id', 'fv_value', 'fv_desc', 'fv_issues']
        vkwargs = self.validate(required_col_list, **kwargs)

        raw_sql = """ INSERT INTO field_value
                      (field_id,
                       fv_value,
                       fv_desc,
                       fv_issues)
                      VALUES (:field_id,
                              :fv_value,
                              :fv_desc,
                              :fv_issues)
                  """
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        field_id=kwargs['field_id'],
                                        fv_value=kwargs['fv_value'],
                                        fv_desc=kwargs['fv_desc'],
                                        fv_issues=kwargs['fv_issues'])
        except exc.IntegrityError as err:
            raise ValueError('Insert failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)

    def update(self, **kwargs):
        """ Updates field_value into database.
            Inputs:
                - keyword arg of field_id, fv_value, fv_desc, and fv_issues
            Returns:
                - lastrowid
                - rowcount
            Raises:
                - exc.IntegrityError
        """
        required_col_list = ['field_id', 'fv_value', 'fv_desc', 'fv_issues']
        vkwargs = self.validate(required_col_list, **kwargs)

        raw_sql = """ UPDATE field_value
                         SET fv_desc   =  :fv_desc,
                             fv_issues =  :fv_issues
                       WHERE field_id =  :field_id
                         AND fv_value =  :fv_value
                  """
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        field_id=vkwargs['field_id'],
                                        fv_value=vkwargs['fv_value'],
                                        fv_desc=vkwargs['fv_desc'],
                                        fv_issues=vkwargs['fv_issues'])
        except exc.IntegrityError as err:
            print(sql)
            raise ValueError('Insert failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)



class InstanceTools(simplesql.TableTools):
    """ Includes all methods for working with 'instance' table.
    """

    def table_create(self):
        """ Creates the 'instance' table.
        """
        self.instance = Table('instance',
                              self.metadata,
                              Column('instance_id',
                                     Integer,
                                     nullable=False,
                                     primary_key=True),
                              Column('schema_id',
                                     Integer,
                                     nullable=False),
                              Column('instance_name',
                                     String(255),
                                     nullable=False),
                              UniqueConstraint('schema_id', 'instance_name', name='instance_uk1'),
                              ForeignKeyConstraint(columns=['schema_id'],
                                                   refcolumns=['schema.schema_id'],
                                                   name='instance_fk1',
                                                   ondelete='CASCADE'),
                              extend_existing=True)

        self._table = self.instance
        self._table_name = 'instance'
        return self._table

    def get_instance_id(self, schema_id, instance_name='default'):
        """Get instance_id if one exists, ir not doesn't exist then create it.
           Return final instance_id.

           Note that this code assumes that only a single instance exists for
           a given schema.   This is only going to be true for the short-term.
        """
        sql = """ SELECT instance_id
                  FROM instance
                  WHERE schema_id = :schema_id
              """
        select_sql = text(sql)
        result = self.engine.execute(select_sql, schema_id=schema_id)
        rows = result.fetchall()
        try:
            return rows[0].instance_id
        except IndexError:  # No rows found
            return self.setter(schema_id=schema_id,
                               instance_name=instance_name)



class AnalysisProfileTools(simplesql.TableTools):
    """ Includes all methods for the 'analysis_profile' table.
    """

    def table_create(self):
        """ Creates 'analysis_profile' table.
        """
        self.analysis_profile = Table('analysis_profile',
                                      self.metadata,
                                      Column('analysis_profile_id',
                                             Integer,
                                             nullable=False,
                                             primary_key=True),
                                      Column('instance_id',
                                             Integer,
                                             nullable=False),
                                      Column('collection_id',
                                             Integer,
                                             nullable=False),
                                      Column('analysis_profile_name',
                                             String(255),
                                             nullable=False),
                                      UniqueConstraint('instance_id', 'collection_id',
                                                       'analysis_profile_name',
                                                       name='analysis_profile_k1'),
                                      ForeignKeyConstraint(columns=['instance_id'],
                                                           refcolumns=['instance.instance_id'],
                                                           name='analysis_profile_fk1',
                                                           ondelete='CASCADE'),
                                      ForeignKeyConstraint(columns=['collection_id'],
                                                           refcolumns=['collection.collection_id'],
                                                           name='analysis_profile_fk1',
                                                           ondelete='CASCADE'),
                                      extend_existing=True)

        self._table = self.analysis_profile
        self._table_name = 'analysis_profile'
        return self._table


    def get_analysis_profile_id(self, instance_id, collection_id,
                                analysis_profile_name='default'):
        """Get analysis_profile_id if one exists, ir not doesn't exist then create it.
           Return final id.

           Note that this code assumes that only a single analysis_profile
           exists for a given schema.   This is only going to be true for the
           short-term.
        """
        sql = """ SELECT analysis_profile_id
                  FROM analysis_profile
                  WHERE instance_id  = :instance_id
              """
        select_sql = text(sql)
        result = self.engine.execute(select_sql, instance_id=instance_id)
        rows = result.fetchall()
        try:
            return rows[0].analysis_profile_id
        except IndexError:  # No rows found
            return self.setter(instance_id=instance_id,
                               collection_id=collection_id,
                               analysis_profile_name=analysis_profile_name)




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
        self.analysis = Table('analysis',
                              self.metadata,
                              Column('analysis_id',
                                     Integer,
                                     nullable=False,
                                     primary_key=True),
                              Column('instance_id',
                                     Integer,
                                     nullable=False),
                              Column('analysis_profile_id',
                                     Integer,
                                     nullable=True),
                              Column('analysis_timestamp',
                                     DATETIME,
                                     default=datetime.datetime.now,
                                     onupdate=datetime.datetime.now,
                                     nullable=False),
                              Column('analysis_tool',
                                     String(20),
                                     nullable=False),
                              UniqueConstraint('instance_id', 'analysis_timestamp',
                                               name='analysis_uk1'),
                              ForeignKeyConstraint(columns=['instance_id'],
                                                   refcolumns=['instance.instance_id'],
                                                   name='analysis_fk1',
                                                   ondelete='CASCADE'),
                              ForeignKeyConstraint(columns=['analysis_profile_id'],
                                                   refcolumns=['analysis_profile.analysis_profile_id'],
                                                   name='analysis_fk2',
                                                   ondelete='CASCADE'),
                              extend_existing=True)

        self._table = self.analysis
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
        self.collection_analysis = Table('collection_analysis',
                                         self.metadata,
                                         Column('ca_id',
                                                Integer,
                                                nullable=False,
                                                primary_key=True),
                                         Column('analysis_id',
                                                Integer,
                                                nullable=False),
                                         Column('collection_id',
                                                Integer,
                                                nullable=False),
                                         Column('ca_name',
                                                String(80),
                                                nullable=False),
                                         Column('ca_location',
                                                String(256),
                                                nullable=False),
                                         Column('ca_row_cnt',
                                                Integer,
                                                nullable=True),
                                         Column('ca_field_cnt',
                                                Integer,
                                                nullable=True),
                                         Column('ca_delimiter',
                                                String(10),
                                                nullable=True),
                                         Column('ca_hasheader',
                                                Boolean,
                                                nullable=True),
                                         Column('ca_quoting',
                                                String(20),
                                                nullable=True),
                                         Column('ca_quote_char',
                                                String(1),
                                                nullable=True),
                                         UniqueConstraint('analysis_id','collection_id',
                                                name='collection_analysis_uk1'),
                                         ForeignKeyConstraint(columns=['analysis_id'],
                                                refcolumns=['analysis.analysis_id'],
                                                name='collection_analysis_fk1',
                                                ondelete='CASCADE'),
                                         ForeignKeyConstraint(columns=['collection_id'],
                                                refcolumns=['collection.collection_id'],
                                                name='collection_analysis_fk2',
                                                ondelete='CASCADE'),
                                         extend_existing=True)

        self._table = self.collection_analysis
        self._table_name = 'collection_analysis'
        return self._table



class FieldAnalysisTools(simplesql.TableTools):
    """ Includes all methods for the 'field_analysis' table.
    """

    def table_create(self):
        """ Creates the 'field_analysis' table.
        """
        self.field_analysis = Table('field_analysis',
                                    self.metadata,
                                    Column('fa_id',
                                           Integer,
                                           nullable=False,
                                           primary_key=True),
                                    Column('ca_id',
                                           Integer,
                                           nullable=False),
                                    Column('field_id',
                                           Integer,
                                           nullable=False),
                                    Column('fa_type',
                                           String(10),
                                           nullable=True),
                                    Column('fa_unique_cnt',
                                           Integer,
                                           nullable=True),
                                    Column('fa_known_cnt',
                                           Integer,
                                           nullable=True),
                                    Column('fa_unknown_cnt',
                                           Integer,
                                           nullable=True),
                                    Column('fa_min',
                                           String(256),
                                           nullable=True),
                                    Column('fa_max',
                                           String(256),
                                           nullable=True),
                                    Column('fa_mean',
                                           Float,
                                           nullable=True),
                                    Column('fa_median',
                                           Float,
                                           nullable=True),
                                    Column('fa_stddev',
                                           Float,
                                           nullable=True),
                                    Column('fa_variance',
                                           Float,
                                           nullable=True),
                                    Column('fa_min_len',
                                           Integer,
                                           nullable=True),
                                    Column('fa_max_len',
                                           Integer,
                                           nullable=True),
                                    Column('fa_mean_len',
                                           Integer,
                                           nullable=True),
                                    Column('fa_case',
                                           String(10),
                                           nullable=True),
                                    UniqueConstraint('ca_id', 'field_id',
                                           name='field_analysis_uk1'),
                                    ForeignKeyConstraint(columns=['ca_id'],
                                           refcolumns=['collection_analysis.ca_id'],
                                           name='field_analysis_fk1',
                                           ondelete='CASCADE'),
                                    ForeignKeyConstraint(columns=['field_id'],
                                           refcolumns=['field.field_id'],
                                           name='field_analysis_fk2',
                                           ondelete='CASCADE'),
                                    CheckConstraint ("fa_case IN ('lower', 'upper', 'mixed', 'unk')",
                                           name='field_analysis_ck1'),
                                    extend_existing=True)

        self._table = self.field_analysis
        self._table_name = 'field_analysis'
        return self._table



class FieldAnalysisValueTools(simplesql.TableTools):
    """ Includes all methods for the 'field_analysis' table.
    """

    def table_create(self):
        """ Creates the 'field_analysis' table.
        """
        self.field_analysis_value = Table('field_analysis_value',
                                          self.metadata,
                                          Column('fav_id',
                                                 Integer,
                                                 nullable=False,
                                                 primary_key=True),
                                          Column('fa_id',
                                                 Integer,
                                                 nullable=False),
                                          Column('fav_value',
                                                 String,
                                                 nullable=False),
                                          Column('fav_count',
                                                 Integer,
                                                 nullable=False),
                                          UniqueConstraint('fa_id', 'fav_value',
                                                           name='field_analysis_value_uk1'),
                                          ForeignKeyConstraint(columns=['fa_id'],
                                                               refcolumns=['field_analysis.fa_id'],
                                                               name='field_analysis_value_fk1',
                                                               ondelete='CASCADE'),
                                          extend_existing=True)

        self._table = self.field_analysis_value
        self._table_name = 'field_analysis_value'
        return self._table



class FileIndexTools(simplesql.TableTools):
    """ Includes all methods for the 'file_index' table.
    """

    def table_create(self):
        """ Creates the 'file_index' table.
        """
        self.file_index = Table('file_index',
                                self.metadata,
                                Column('file_hash',
                                        String(256),
                                        nullable=False,
                                        primary_key=True),
                                Column('record_count',
                                        Integer,
                                        nullable=True),
                                Column('column_count',
                                        Integer,
                                        nullable=True),
                                Column('last_update_epoch',
                                        Float,
                                        index=True,
                                        nullable=False),
                                UniqueConstraint('file_hash',
                                                 name='file_index_uk1'),
                                extend_existing=True)

        self._table = self.file_index
        self._table_name = 'file_index'
        self.instance = None # assigned in InstanceTools
        return self._table


    def _hash_file_index(self, filename, mod_datetime, file_bytes):
        string = bytes(filename + mod_datetime.isoformat() + str(file_bytes), 'utf-8')
        hash_object = hashlib.sha1(string)
        hex_digest = hash_object.hexdigest()
        return hex_digest


    def get_file_index_rec_count(self,
                                 filename,
                                 mod_datetime,
                                 file_bytes) -> int:
        """ Return the record count or -1 if there's no record count
        """

        file_hash = self._hash_file_index(filename, mod_datetime, file_bytes)
        sql = """ SELECT record_count
                  FROM file_index
                  WHERE file_hash = :file_hash
              """
        select_sql = text(sql)
        result = self.engine.execute(select_sql, file_hash=file_hash)
        rows = result.fetchall()
        self.update(filename, mod_datetime, file_bytes)
        try:
            return rows[0].record_count
        except IndexError:  # No rows found
            return -1


    def set_file_index_counts(self,
                              filename,
                              mod_datetime,
                              file_bytes,
                              rec_count,
                              col_count) -> Tuple[int, int]:
        """ Write file_index counts
        """

        file_hash = self._hash_file_index(filename, mod_datetime, file_bytes)
        raw_sql = """ INSERT INTO file_index
                          (file_hash,
                           record_count,
                           column_count,
                           last_update_epoch)
                      Values(:file_hash,
                             :rec_count,
                             :col_count,
                             :epoch
                             )
                  """
        sql = text(raw_sql)
        curr_epoch = time.time()
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        file_hash=file_hash,
                                        rec_count=rec_count,
                                        col_count=col_count,
                                        epoch=curr_epoch)
        except exc.IntegrityError as err:
            raise ValueError('Insert failed. %s' % err)
        else:
            self.prune()
            return (result.lastrowid,
                    result.rowcount)


    def update(self,
               filename,
               mod_datetime,
               file_bytes) -> int:
        """ Updates the last_update_epoch
        """

        file_hash = self._hash_file_index(filename, mod_datetime, file_bytes)
        raw_sql = """ UPDATE file_index
                      SET last_update_epoch = :epoch
                      WHERE file_hash = :file_hash
                  """
        sql = text(raw_sql)
        curr_epoch = time.time()
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        file_hash=file_hash,
                                        epoch=curr_epoch)
        except exc.IntegrityError as err:
            raise ValueError('Update failed. %s' % err)
        else:
            return (result.lastrowid,
                    result.rowcount)


    def prune(self) -> int:
        """ Deletes any entries more than a year old
        """

        min_epoch = time.time() - (86400 * 365)
        raw_sql = """ DELETE FROM file_index
                      WHERE last_update_epoch < :epoch
                  """
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        epoch=min_epoch)
        except exc.IntegrityError as err:
            raise ValueError('Delete failed. %s' % err)
        else:
            return result.rowcount



class MigrationTools(simplesql.TableTools):
    """ Tracks the schema versions
    """

    def table_create(self):
        """ Handles creation of collection table.
        """

        self.migration = Table('migration',
                                self.metadata,
                                Column('version',
                                       String(10),
                                       nullable=False,
                                       primary_key=True),
                                Column('installation_timestamp',
                                       DATETIME,
                                       default=datetime.datetime.now,
                                       onupdate=datetime.datetime.now,
                                       nullable=False),
                                Column('comment',
                                       String(256),
                                       nullable=True),
                                extend_existing=True)
        self._table = self.migration
        self._table_name = 'migration'
        return self._table


    def write(self):
        """ Write to migration table
        """
        raw_sql = """ DELETE FROM migration"""
        sql = text(raw_sql)
        try:
            connection = self.engine.connect()
            result = connection.execute(sql)
        except exc.IntegrityError as err:
            raise ValueError('Delete failed. %s' % err)

        raw_sql = """ INSERT INTO migration
                      (version,
                       installation_timestamp,
                       comment)
                      VALUES ('0.2.2',
                              :dt,
                              'Adds file_index')
                  """
        sql = text(raw_sql)
        curr_epoch = time.time()
        try:
            connection = self.engine.connect()
            result = connection.execute(sql,
                                        dt=datetime.datetime.now())
        except exc.IntegrityError as err:
            raise ValueError(f'Insert failed: {err}')





def create_views(engine, connect):
    """ Creates all views.
        Each view function that it calls is responsible for checking
        whether or not it already exists.
    """

    create_view_rpt_collection_analysis_v(engine, connect)
    create_view_rpt_field_analysis_v(engine, connect)



def create_view_rpt_collection_analysis_v(engine, connection):
    """ Creates this view - if it doesn't already exist.

        This view will join schema, collection, instance, analysis, and
        collection_analysis tables together.  It will usually produce more
        rows that the user wants - since a given schema may have multiple
        instances and multiple analysis may be performed.  For this reason
        it is anticipated that it will typically be restricted by both
        instance id or name and analysis id or timestamp.
    """

    sql = """ CREATE VIEW rpt_collection_analysis_v AS
              SELECT s.schema_id,
                     s.schema_name,
                     c.collection_id,
                     c.collection_name,
                     i.instance_id,
                     i.instance_name,
                     a.analysis_id,
                     a.analysis_timestamp,
                     ca.ca_id,
                     ca.ca_name,
                     ca.ca_location,
                     ca.ca_row_cnt,
                     ca.ca_field_cnt,
                     ca.ca_delimiter,
                     ca.ca_hasheader,
                     ca.ca_quoting,
                     ca.ca_quote_char
              FROM schema  s
                  INNER JOIN collection c
                     ON s.schema_id = c.schema_id
                  INNER JOIN instance i
                     ON s.schema_id = i.schema_id
                  INNER JOIN analysis a
                     ON i.instance_id = a.instance_id
                  INNER JOIN collection_analysis  ca
                     ON a.analysis_id = ca.analysis_id
                    AND c.collection_id = ca.collection_id
          """
    existing_views = engine.dialect.get_view_names(connection)
    if 'rpt_collection_analysis_v' not in existing_views:
        create_sql = text(sql)
        _ = engine.execute(create_sql)



def create_view_rpt_field_analysis_v(engine, connection):
    """ Creates this view - if it doesn't already exist.

        This view will join collection, field, collection_analysis and
        field_analysis tables together.   It will usually produce more
        rows than the user wants - since a given collection may have
        multiple analysis rows.  For this reason it is anticipated that
        it will typically be restricted by connection_analysis.ca_id or
        connection_analysis.analysis_id.
    """

    sql = """ CREATE VIEW rpt_field_analysis_v AS
              SELECT c.collection_id,
                     ca.analysis_id,
                     ca.ca_id,
                     f.field_id,
                     f.field_name,
                     f.field_type,
                     f.field_order,
                     f.field_len,
                     fa.fa_type,
                     fa.fa_unique_cnt,
                     fa.fa_known_cnt,
                     fa.fa_unknown_cnt,
                     fa.fa_min,
                     fa.fa_max,
                     fa.fa_mean,
                     fa.fa_median,
                     fa.fa_stddev,
                     fa.fa_variance,
                     fa.fa_min_len,
                     fa.fa_max_len,
                     fa.fa_mean_len,
                     fa.fa_case
              FROM collection c
                  INNER JOIN collection_analysis ca
                     ON c.collection_id = ca.collection_id
                  INNER JOIN field f
                     ON c.collection_id = f.collection_id
                  INNER JOIN field_analysis fa
                     ON f.field_id = fa.field_id
          """
    existing_views = engine.dialect.get_view_names(connection)
    if 'rpt_field_analysis_v' not in existing_views:
        create_sql = text(sql)
        _ = engine.execute(create_sql)
