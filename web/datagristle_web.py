#!/usr/bin/env python2.7

import os, sys
from pprint import pprint as pp
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gristle.metadata as md
###from sqlite3 import dbapi2 as sqlite3
from sqlalchemy import (UniqueConstraint, ForeignKeyConstraint, CheckConstraint)

from sqlalchemy import exc
from sqlalchemy import text

#----- get metadata database ----
import appdirs
#user_data_dir = appdirs.user_data_dir('datagristle')
#if not os.path.exists(user_data_dir):
#    print 'data dir (%s) missing - it will be created' % user_data_dir
#    os.makedirs(user_data_dir)

meta = md.GristleMetaData()
app  = Flask(__name__)





#==============================================================================
# Schema Handling
#==============================================================================

@app.route('/', methods=['GET'])
def datagristle():
    connection = meta.engine.connect()
    raw_sql    = """SELECT s.schema_name,
                         s.schema_id,
                         s.schema_desc,
                         COALESCE(COUNT(c.schema_id), 0) as coll_cnt
                  FROM schema s
                     LEFT OUTER JOIN collection c
                        ON s.schema_id = c.schema_id
                  GROUP BY s.schema_Name,
                           s.schema_id,
                           s.schema_desc
                  ORDER BY 1 DESC
               """
    sql     = text(raw_sql)
    result  = connection.execute(sql)
    rows    = result.fetchall()
    return render_template('splash.html', schema_rows=rows)


@app.route('/schema<int:schema_id>')
@app.route('/schema<int:schema_id>/')
def schema(schema_id):

    connection = meta.engine.connect()
    msg     = ''

    #----- Get info for single schema row: -----
    raw_sql = """SELECT schema_name, schema_id, schema_desc
                   FROM schema
                  WHERE schema_id = :schema_id"""
    sql     = text(raw_sql)

    # todo: handle odd exceptions here:
    result = connection.execute(sql, schema_id=schema_id)
    rows   = result.fetchall()
    if len(rows) == 0:   # shouldn't normally happen
       si = ''
       sn = ''
       sd = ''
       msg = 'Schema not found'
    else:
       si = schema_id
       sn = rows[0].schema_name
       sd = rows[0].schema_desc

    #----- Get list of collection rows: -----
    raw_sql = """SELECT collection_id, collection_name, collection_desc
                   FROM collection
                  WHERE schema_id = :schema_id"""
    sql     = text(raw_sql)
    # todo: handle odd exceptions here:
    result    = connection.execute(sql, schema_id=schema_id)
    coll_rows = result.fetchall()

    return render_template('schema.html',
            msg=msg,
            si=schema_id,
            sn=sn,
            sd=sd,
            coll_rows=coll_rows)


@app.route('/schema/new', methods=['GET', 'POST'])
@app.route('/schema/new', methods=['GET', 'POST'])
def schema_new():
    msg = ''
    if request.method == 'POST':
        while True:
            try:
                (rowcnt, rowid) = meta.schema_tools.insert(schema_name=request.form['sn'],
                                                schema_desc=request.form['sd'])
            except ValueError, e:
                return render_template("schema_edit.html",
                                        action='new', msg=e,
                                        sn=request.form['sn'],
                                        sd=request.form['sd'])
            else:
                return redirect('/')
    else:
        return render_template("schema_edit.html", action='new', msg=msg, sn='', sd='')


@app.route('/schema<int:schema_id>/edit', methods=['GET', 'POST'])
def schema_edit(schema_id):
    if request.method == 'POST':
        while True:
           try:
                (rowcnt, rowid) = meta.schema_tools.update(schema_name=request.form['sn'],
                                                           schema_desc=request.form['sd'],
                                                           schema_id=schema_id)
           except ValueError, e:
                return render_template("schema_edit.html",
                                       action='edit', msg=e,
                                       sn=request.form['sn'],
                                       sd=request.form['sd'],
                                       sid=schema_id)
           else:
                return redirect('/schema%i' % schema_id)
    else:
        row = meta.schema_tools.getter(schema_id=schema_id)
        if not row:
            return render_template("schema_edit.html", msg='schema not found',
                                   action='edit', sn='', sd='', sid=schema_id)
        else:
            return render_template("schema_edit.html", action='edit',
                               sn=row.schema_name, sd=row.schema_desc,
                               sid=schema_id)


@app.route('/schema<int:schema_id>/delete', methods=['GET', 'POST'])
def schema_delete(schema_id):
    """ If row has already been deleted, this function will not fail, but just
        route back to home.
    """

    if request.method == 'POST':
        rowcnt = meta.schema_tools.deleter(schema_id=schema_id)
        return redirect('/')
    return render_template("schema_delete.html", sid=schema_id)



#==============================================================================
# Collection Handling
#==============================================================================

@app.route('/schema<int:schema_id>/collection<int:coll_id>/')
def collection(schema_id, coll_id):
    coll_row   = meta.collection_tools.getter(collection_id=coll_id)

    field_q = """SELECT field_id, field_name, field_desc, field_type,
                        field_order, field_len
                    FROM field
                WHERE collection_id = :coll_id"""
    fields  = meta.engine.execute(field_q, coll_id=coll_id)
    field_rows = fields.fetchall()

    return render_template('collection.html',
            sid=schema_id, cid=coll_id, coll_rows=coll_row, field_rows=field_rows)


@app.route('/schema<int:schema_id>/collection/new', methods=['GET', 'POST'])
def collection_new(schema_id):
    msg = ''

    if request.method == 'POST':
        while True:
            try:
                rc = meta.collection_tools.setter(schema_id=schema_id,
                                                collection_name=request.form['cn'],
                                                collection_desc=request.form['cd'])
            except ValueError, e:
                return render_template("collection_edit.html", action='new', msg=e,
                                       sid=schema_id, cn=request.form['cn'],
                                       cd=request.form['cd'], cid='')
            else:
                return redirect('/schema%i' % schema_id)
    else:
        return render_template("collection_edit.html", action='new', sid=schema_id,
                               cn='', cd='', cid='')


@app.route('/schema<int:schema_id>/collection<int:coll_id>/edit', methods=['GET', 'POST'])
def collection_edit(schema_id, coll_id):
    if request.method == 'POST':
        while True:
           try:
               rc = meta.collection_tools.setter(schema_id=schema_id,
                                          collection_id=coll_id,
                                          collection_name=request.form['cn'],
                                          collection_desc=request.form['cd'])
           except ValueError, e:
               return render_template("collection_edit.html", action='edit', msg=e,
                                      cn=request.form['cn'], cd=request.form['cd'],
                                      sid=schema_id, cid=coll_id)
           else:
               return redirect('/schema%i/collection%i' % (schema_id, coll_id))
    else:
        row = meta.collection_tools.getter(collection_id=coll_id)
        if row:
            return render_template("collection_edit.html", action='edit',
                            cn=row.collection_name, cd=row.collection_desc,
                            sid=schema_id, cid=coll_id)

        else:
            return render_template("collection_edit.html", action='edit',
                            msg='Collection not found',
                            cn='', cd='', sid=schema_id, cid=coll_id)


@app.route('/schema<int:schema_id>/collection<int:coll_id>/delete', methods=['GET', 'POST'])
def collection_delete(schema_id, coll_id):
    if request.method == 'POST':
        rc = meta.collection_tools.deleter(collection_id=coll_id)
        return redirect('/schema%i' % schema_id)
    return render_template("collection_delete.html", sid=schema_id, cid=coll_id)



#==============================================================================
# Field Handling
#==============================================================================

@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/')
def field(schema_id, coll_id, field_id):
    row   = meta.field_tools.getter(field_id=field_id)

    fv_sql = """SELECT fv_value, fv_desc, fv_issues
                    FROM field_value
                WHERE field_id = :field_id"""
    fvalues = meta.engine.execute(fv_sql, field_id=field_id)
    fv_rows = fvalues.fetchall()

    return render_template('field.html',
                           sid=schema_id,
                           cid=coll_id,
                           fid=field_id,
                           field_rows=row,
                           fv_rows=fv_rows)


@app.route('/schema<int:schema_id>/collection<int:coll_id>/field/new', methods=['GET', 'POST'])
def field_new(schema_id, coll_id):
    if request.method == 'POST':
        while True:
            try:
                temp_fl = None  if request.form['fl'] == 'None' else request.form['fl']
                (rowcnt, rowid) = meta.field_tools.insert(collection_id=coll_id,
                                                  field_name=request.form['fn'],
                                                  field_desc=request.form['fd'],
                                                  field_order=request.form['fo'],
                                                  field_type=request.form['ft'],
                                                  field_len=temp_fl,
                                                  element_name=request.form['en'])
            except ValueError, e:
                return render_template("field_edit.html", sid=schema_id, cid=coll_id, action='new',
                        msg=e, fn=request.form['fn'],fd=request.form['fd'],fo=request.form['fd'],
                               ft=request.form['ft'],fl=request.form['fl'],en=request.form['en'])

            else:
                return redirect('/schema%i/collection%i' % (schema_id, coll_id))
    else:
        return render_template("field_edit.html", sid=schema_id, cid=coll_id, action='new',
                               fn='',fd='',fo='',ft='',fl='',en='')


@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/delete', methods=['GET', 'POST'])
def field_delete(schema_id, coll_id, field_id):
    if request.method == 'POST':
        rc = meta.field_tools.deleter(field_id=field_id)
        return redirect('/schema%i/collection%i' % (schema_id, coll_id))
    return render_template("field_delete.html", sid=schema_id, cid=coll_id, fid=field_id)



@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/edit', methods=['GET', 'POST'])
def field_edit(schema_id, coll_id, field_id):
    if request.method == 'POST':
        while True:
            try:
                (rowcnt, rowid) = meta.field_tools.update(field_id=field_id,
                                                  collection_id=coll_id,
                                                  field_name=request.form['fn'],
                                                  field_desc=request.form['fd'],
                                                  field_order=request.form['fo'],
                                                  field_type=request.form['ft'],
                                                  field_len=request.form['fl'],
                                                  element_name=request.form['en'])
            except ValueError, e:
                app.logger.error('Field experienced an IntegrityError!')
                msg = 'IntegrityError - data violates rules: %s' % e
                return render_template("field_edit.html", action='edit', sid=schema_id, cid=coll_id,
                                       fid=field_id, msg=msg, fn=request.form['fn'], fd=request.form['fd'],
                                       ft=request.form['ft'], fo=request.form['fo'], fl=request.form['fl'],
                                       en=request.form['en'],
                                       ft_string_select=None, ft_int_select=1,
                                       ft_select=request.form['ft'])
            else:
               return redirect('/schema%i/collection%i/field%i' % (schema_id, coll_id, field_id))
    else:
        row   = meta.field_tools.getter(field_id=field_id)
        return render_template("field_edit.html", action='edit', sid=schema_id, cid=coll_id,
                               fid=field_id, fn=row.field_name, fd=row.field_desc,
                               fo=row.field_order, ft=row.field_type,
                               fl=row.field_len, en=row.element_name,
                               ft_string_select=None, ft_int_select=1,
                               ft_select=row.field_type)



#==============================================================================
# FieldValue Handling
#==============================================================================
@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/fv<fv_value>/', methods=['GET'])
def fv(schema_id, coll_id, field_id, fv_value):

    fv_sql = """SELECT fv_desc,
                       fv_issues
                    FROM field_value
                WHERE field_id = :field_id
                  AND fv_value = :fv_value"""
    fvalues = meta.engine.execute(fv_sql, field_id=field_id, fv_value=fv_value)
    fv_row = fvalues.fetchall()

    return render_template('fv.html',
                           sid=schema_id,
                           cid=coll_id,
                           fid=field_id,
                           fvv=fv_value,
                           fvd=fv_row[0][0],
                           fvi=fv_row[0][1])



@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/fv/new', methods=['GET', 'POST'])
def fv_new(schema_id, coll_id, field_id):
    if request.method == 'POST':
        while True:
            try:
                temp_fvi = data2db(request.form['fvi'])
                temp_fvd = data2db(request.form['fvd'])
                (rowcnt, rowid) = meta.field_value_tools.insert(field_id=field_id,
                                                  fv_value=request.form['fv'],
                                                  fv_desc=request.form['fvd'],
                                                  fv_issues=request.form['fvi'])
            except ValueError, e:
                print 'fv_new - ValueError'
                return render_template("fv_edit.html", sid=schema_id, cid=coll_id, fid=field_id,
                       action='new', msg=e,
                       fv=request.form['fv'],fvd=request.form['fvd'],fvi=request.form['fvi'])

            else:
                return redirect('/schema%i/collection%i/field%i' % \
                       (schema_id, coll_id, field_id))
    else:
        return render_template("fv_edit.html", sid=schema_id, cid=coll_id, fid=field_id,
                               action='new', fv='',fvd='',fvi='')


@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/fv<fv_value>/edit', methods=['GET', 'POST'])
def fv_edit(schema_id, coll_id, field_id, fv_value):
    if request.method == 'POST':
        while True:
            try:
                temp_fvd = data2db(request.form['fvd'])
                temp_fvi = data2db(request.form['fvi'])
                (rowcnt, rowid) = meta.field_value_tools.update(field_id=field_id,
                                                  fv_value=fv_value,
                                                  fv_desc=temp_fvd,
                                                  fv_issues=temp_fvi)
            except ValueError, e:
                app.logger.error('FieldValueexperienced an IntegrityError!')
                msg = 'IntegrityError - data violates rules: %s' % e
                return render_template("fv_edit.html", action='edit', sid=schema_id, cid=coll_id,
                                       fid=field_id, msg=msg,
                                       fv=fv_value,
                                       fvd=request.form['fvd'],
                                       fvi=request.form['fvi'])
            else:
               return redirect('/schema%i/collection%i/field%i/fv%s' % \
                              (schema_id, coll_id, field_id, fv_value))
    else:
        fv_sql = """SELECT fv_desc,
                           fv_issues
                        FROM field_value
                    WHERE field_id = :field_id
                    AND fv_value = :fv_value"""
        fvalues = meta.engine.execute(fv_sql, field_id=field_id, fv_value=fv_value)
        row = fvalues.fetchall()

        return render_template("fv_edit.html", action='edit', sid=schema_id, cid=coll_id,
                               fid=field_id,
                               fv=fv_value,
                               fvd=row[0][0],
                               fvi=row[0][1])

@app.route('/schema<int:schema_id>/collection<int:coll_id>/field<int:field_id>/fv<fv_value>/delete', methods=['GET', 'POST'])
def fv_delete(schema_id, coll_id, field_id, fv_value):
    if request.method == 'POST':
        sql = """DELETE
                 FROM field_value
                 WHERE field_id = :field_id
                   AND fv_value = :fv_value"""
        fvalues = meta.engine.execute(sql, field_id=field_id, fv_value=fv_value)
        rc = meta.field_value_tools.deleter(field_id=field_id, fv_value=fv_value)
        return redirect('/schema%i/collection%i/field%i' % (schema_id, coll_id, field_id))
    else:
        return render_template("fv_delete.html", sid=schema_id, cid=coll_id,
                               fid=field_id, fv=fv_value)



#==============================================================================
# Misc
#==============================================================================


def data2db(val):
    if val == 'None':
       return None
    else:
       return val



def data2form(val):
    if val is None:
       return ''
    else:
       return val



if __name__ == "__main__":
    #app.run(debug=True)
    app.run()
