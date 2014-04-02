#!/usr/bin/env python
""" Purpose of this module is to provide a small set of simple common sql
    functions

    Issues:
       - Currently when the setter attempts to update a row with integrity
         violations it fails to raise IntegrityError.  This violation is
         determined manually, and IntegrityError is manually raised instead.

    Dependencies:
       - sqlalchemy (0.7 - though earlier versions will probably work)
       - sqlite3

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011,2012,2013 Ken Farmer
"""

from __future__ import division
from sqlalchemy import exc
from sqlalchemy import UniqueConstraint
#from pprint import pprint

import logging



class TableTools(object):
    """ Provides generic and simple tools for managing data within a table.
    """

    def __init__(self, metadata, engine):
        self.metadata = metadata
        self.engine   = engine
        self._table       = None
        self._table_name  = None
        self._unique_constraints = None
        self.insert_defaulted = []       # cols added here aren't inserted
        self.update_defaulted = []       # cols added here aren't updated


    def deleter(self, **kw):
        """ Requires the key of the row.
            Returns a count of rows deleted (will be either 0 or 1).
            Will only work on tables with primary keys.
            Does not confirm that it has the key for the row - so can be
            dangerous.
            Note - it may not delete anything if an insufficient unique
            key is provided.
            Uses 'generative sql' to build up query.
        """
        try:
            gener_sql = self._table.delete()
            gener_sql = self._create_where(gener_sql, kw)
            result = gener_sql.execute()
        except KeyError:
            # could mean row was not there
            # could mean that part of key was missing?
            return 0

        assert result.rowcount in [0, 1]
        return result.rowcount


    def getter(self, **kw):
        """ Requires the key of the row
            Returns a single row if found, otherwise returns None
            Will only work on tables with primary keys.
            Uses 'generative sql' to build up query.
        """
        gener_sql = self._table.select()
        gener_sql = self._create_where(gener_sql, kw)
        result    = gener_sql.execute()
        rows      = result.fetchall()
        assert len(rows) in [0, 1]
        try:
            return rows[0]
        except IndexError:   # no rows found
            return None


    def get_id(self, **kw):
        """ Requires the key of the row - for tables with a primary key
            that is a surrogate key and a natural key defined within a
            unique constraint.
            Returns a single row if found, otherwise returns None
            No longer being used - but kept around just in case
            Uses 'generative sql' to build up query.
        """
        gener_sql = self._table.select()
        #uk       = self._get_unique_constraints()
        gener_sql = self._create_where(gener_sql, kw)
        result    = gener_sql.execute()
        rows      = result.fetchall()
        try:
            return rows[0].id
        except AttributeError:  # no rows found
            return None


    def lister(self, **kw):
        """ Returns all rows for the table, not in any particular order.
            Inputs:
                - assumes some args, but ignores them
                - these are only included because of the way that these functions
                  are called.
            Outputs:
                - all rows & columns for table
        """
        sel_sql  = self._table.select()
        result   = sel_sql.execute()
        rows     = result.fetchall()
        return rows


    def setter(self, **kw):
        """ Inserts new entry or updates existing entry.
            Assumptions:
                - the table has a primary key named 'id'
                - the table has a single unique constraint on its natural key
            Insert details:
                - attempt insert
                - if it works, return new id otherwise continue onto update
            Update details
                - if id provided, update based on id
                - if id not provided, update based on unique constraint
                - if constraint violation occurs - manually generate exception!
            Returns number of rows inserted.
        """
        kw_insert = {}
        #broken code - not sure what it did exactly!
        for key in kw.keys():
            if kw[key] not in self.insert_defaulted:
                kw_insert[key] = kw[key]

        try:
            ins_sql = self._table.insert()
            result = ins_sql.execute(kw_insert)
            #print kw_insert
            if result.rowcount == 0:
                raise KeyError    # by missing column
            else:
                return  result.lastrowid
        except exc.IntegrityError, except_detail:
            # possibly caused by violation of primary key constraint
            # possibly caused by violation of check or fk key constraint
            # print 'insert exception'
            # print e
            #print except_detail
            kw_update = {}
            for key in kw.keys():
                if kw[key] not in self.update_defaulted:
                    kw_update[key] = kw[key]
            upd_sql      = self._table.update()
            upd_sql      = self._create_where(upd_sql, kw_update)
            #print kw_update
	    try:
                result = upd_sql.execute(kw_update)
            except exc.IntegrityError, except_detail:
	        print 'insert failed, update failed'
		print except_detail
		raise
            if result.rowcount == 0:       # this is the only way to catch
                print 'update exception'
                print except_detail        # might want to get rid of this
                print result
                # usually constraint violations
                raise exc.IntegrityError (upd_sql, kw_update, None)
            return 0




    def _create_where(self, sql, filter_col):
        """ Creates where condition necessary to identify a single row based
            on primary key or unique key.
            Arguments:
               - sql = sqlalchemy sql object
               - filter_col = column to be used for selecting a row
            Returns:
               - where condition string
        """
        #print '\nprovided filter_col: ' +  ','.join(filter_col)
        #print self._table.primary_key
        where     = None
        technique = 'pk'
        for column in self._table.c:
            if column.name in self._table.primary_key:
                if column.name not in filter_col:
                    technique = 'uk'
        #print technique

        if technique == 'pk':
            for column in self._table.c:
                if column.name in self._table.primary_key:
                    where = sql.where(self._table.c[column.name]
                                      == filter_col[column.name])
        elif technique == 'uk':
            for constraint in self._get_unique_constraints():
                #print '   constraint:         %s' %  constraint
                #print '     syscat:           %s' %  self._table.c[constraint]
                #print '     filter_col:       %s' %  ','.join(filter_col)
                #print '     filter_col[sub]:  %s' %  filter_col[constraint]
                #print 'Constraint:  %s' % constraint
                #print 'constraint: %s' % self._table.c[constraint]
                #print 'filter_col: %s' % filter_col[constraint]
                where = sql.where(self._table.c[constraint]
                                  == filter_col[constraint])
            if where is None:
                if not self._get_unique_constraints():
                    raise KeyError, 'no pk provided but table lacks a uk'
                else:
                    raise KeyError, 'no pk or uk provided'

        if where is None:
            raise KeyError

        return where


    def _get_unique_constraints(self):
        """ Returns list of constraints for instance table
        """
        results = []
        for constraint in self._table.constraints:
            if isinstance(constraint, UniqueConstraint):
                for column in constraint.columns:
                    results.append(column.name)
        #print 'constraint_list: ' + ','.join(results)
        return results

