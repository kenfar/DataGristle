#!/usr/bin/env python
""" Purpose of this module is to provide a small set of simple common sql functions

    Issues:
       - Currently when the setter attempts to update a row with integrity violations
         it fails to raise IntegrityError.  This violation is determined manually,
         and IntegrityError is manually raised instead.

    Dependencies:
       - sqlalchemy (0.7 - though earlier versions will probably work)
       - sqlite3

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

from __future__ import division
import os
import sys
from sqlalchemy import (exc, update)
from sqlalchemy import UniqueConstraint
from pprint import pprint




class TableTools(object):
    """
    """

    def __init__(self, metadata):
        self.metadata = metadata


    def deleter(self, **kw):
        """ Requires the key of the row.
            Returns a count of rows deleted (will be either 0 or 1).
            Will only work on tables with primary keys.
            Does not confirm that it has the key for the row - so can be
            dangerous.
            Note - it may not delete anything if an insufficient unique
            key is provided.
        """
        try:
            d = self._table.delete()
            d = self._create_where(d, kw)
            result = d.execute()
        except KeyError:
            # could mean row was not there
            # could mean that part of key was missing?
            return 0

        assert(result.rowcount in [0,1])
        return result.rowcount


    def getter(self, **kw):
        """ Requires the key of the row
            Returns a single row if found, otherwise returns None
            Will only work on tables with primary keys.
        """
        s      = self._table.select()
        s      = self._create_where(s, kw)
        result = s.execute()
        rows   = result.fetchall()
        assert(len(rows) in [0,1])
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
        """
        s      = self._table.select()
        uk     = self._get_unique_constraints()
        s      = self._create_where(s, kw)
        result = s.execute()
        rows   = result.fetchall()
        try:
            return rows[0].id
        except AttributeError:  # no rows found
            return None


    def lister(self, **kw):
        """ Returns all rows for the table, not in any particular order.
        """
        s      = self._table.select()
        result = s.execute()
        rows   = result.fetchall()
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
        #for key in kw.keys():
        #    if kw[key] not in self.insert_defaulted:
        #        kw_insert[key] = kw[key]

        try:
           i = self._table.insert()
           result = i.execute(kw_insert)
           #print kw_insert
           if result.rowcount == 0:
               raise KeyError                                # by missing column
           else:
               return  result.lastrowid
        except exc.IntegrityError, e:
           # possibly caused by violation of primary key constraint
           # possibly caused by violation of check or fk key constraint
           print 'insert exception'
           print e
           kw_update = {}
           #   broken code - not sure what it does exactly
           #for key in kw.keys():
           #   if kw[key] not in self.update_defaulted:
           #       kw_update[key] = kw[key]
           u      = self._table.update()
           u      = self._create_where(u, kw_update)
           print kw_update
           result = u.execute(kw_update)
           if result.rowcount == 0:                          # seems that this is the only way to catch
               print 'update exception'
               print e                                       # might want to get rid of this
               print result
               raise exc.IntegrityError (u, kw_update, None) # usually constraint violations 
           return 0




    def _create_where(self, sql, kw):
        """ Creates where condition necessary to identify a single row based on primary
            key or unique key.
        """
        #print '\nprovided kw: ' +  ','.join(kw)
        #print self._table.primary_key
        where     = None
        technique = 'pk'
        for column in self._table.c:
             if column.name in self._table.primary_key:
                 if column.name not in kw:
                     technique = 'uk'
        #print technique

        if technique == 'pk':
            for column in self._table.c:
                if column.name in self._table.primary_key:
                    where = sql.where(self._table.c[column.name] == kw[column.name])
        elif technique == 'uk':
            for constraint in self._get_unique_constraints():
                #print '   constraint:   %s' %  constraint
                #print '       syscat:   %s' %  self._table.c[constraint]
                #print '       kw:       %s' %  ','.join(kw)
                #print '       kw[sub]:  %s' %  kw[constraint]   # this line will not show up!
                #print 'Constraint:  %s' % constraint
                where = sql.where(self._table.c[constraint] == kw[constraint])
            if where is None:
                if not self._get_unique_constraints():
                    raise KeyError, 'no pk provided but table lacks a uk'
                else:
                    raise KeyError, 'no pk or uk provided'

        if where is None:
            raise KeyError 

        return where


    def _get_unique_constraints(self):
        results = []
        for constraint in self._table.constraints:
            if isinstance(constraint, UniqueConstraint):
                for column in constraint.columns:
                    results.append(column.name)
        #print 'constraint_list: ' + ','.join(results)
        return results

