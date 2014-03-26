#!/usr/bin/env python2.7

import os, sys
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gristle.metadata as md

meta = md.GristleMetaData()

app = Flask(__name__)

@app.route('/', methods=['GET'])
def datagristle():
    schema_q = """SELECT schema_name, schema_id, schema_desc
                    FROM schema"""
    schemas = meta.engine.execute(schema_q)
    schema_rows = schemas.fetchall()
    return render_template('splash.html', schema_rows=schema_rows)

@app.route('/newschema', methods=['GET', 'POST'])
def newschema():
    if request.method == 'POST':
        rc = meta.schema_tools.setter(schema_name=request.form['newsn'],
                                      schema_desc=request.form['newsd'])
        return redirect('/')
    return render_template("schema_new.html")

@app.route('/schema<int:schema_id>')
def schema(schema_id):
    schema_q = """SELECT schema_name, schema_id, schema_desc
                    FROM schema
                WHERE schema_id = :schema_id"""
    coll_q = """SELECT collection_id, collection_name, collection_desc
                    FROM collection
                WHERE schema_id = :schema_id"""

    schema = meta.engine.execute(schema_q, schema_id=schema_id)
    schema_row = schema.fetchall()

    colls = meta.engine.execute(coll_q, schema_id=schema_id)
    coll_rows = colls.fetchall()

    return render_template('schema.html',
            schema_row=schema_row, coll_rows=coll_rows)

@app.route('/schema<int:schema_id>/edit', methods=['GET', 'POST'])
def schema_edit(schema_id):
    if request.method == 'POST':
        rc = meta.schema_tools.setter(schema_id=schema_id,
                                      schema_name=request.form['newsn'],
                                      schema_desc=request.form['newsd'])
        return redirect('/schema%i' % schema_id)
    schema_q = """SELECT schema_name, schema_id, schema_desc
                    FROM schema
                WHERE schema_id = :schema_id"""
    schema = meta.engine.execute(schema_q, schema_id=schema_id)
    schema_row = schema.fetchall()
    return render_template("schema_edit.html", fields=schema_row[0], sid=schema_id)

@app.route('/schema<int:schema_id>/delete', methods=['GET', 'POST'])
def schema_delete(schema_id):
    if request.method == 'POST':
        rc = meta.schema_tools.deleter(schema_id=schema_id)
        return redirect('/')
    return render_template("schema_delete.html", sid=schema_id)

@app.route('/schema<int:schema_id>/collection<int:coll_id>')
def collection(schema_id, coll_id):
    coll_q = """SELECT collection_id, collection_name, collection_desc
                    FROM collection
                WHERE collection_id = :coll_id"""
    field_q = """SELECT field_id, field_name, field_desc, field_type,
                        field_order, field_len
                    FROM field
                WHERE collection_id = :coll_id"""
    colls = meta.engine.execute(coll_q, coll_id=coll_id)
    fields= meta.engine.execute(field_q, coll_id=coll_id)
    coll_rows = colls.fetchall()
    field_rows = fields.fetchall()
    return render_template('collection.html',
            schema_id=schema_id, coll_rows=coll_rows, field_rows=field_rows)

if __name__ == "__main__":
    app.run()
