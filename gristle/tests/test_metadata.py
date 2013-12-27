#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
from sqlalchemy import exc
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.metadata  as mod



class TestSchema(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        self.schema_id, self.collection_id = create_basic_metadata(self.md)

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_schema_contents(self):
        row  = self.md.schema_tools.getter(schema_name='geoip')
        assert len(row) == 3  # 1 row with 3 columns
        assert row.schema_name == 'geoip'
        assert row.schema_desc == 'geoip data'

    def test_schema_selecting_nonexistent_row(self):
        assert self.md.schema_tools.getter(schema_name='bogusgeoip') is None

    def test_schema_upsert(self):
        #old_schema_rows = self.md.schema_tools.lister()
        # add new entry:
        assert self.md.schema_tools.setter(schema_name='uniq-schema',schema_desc='insert result') != 0
        assert len(self.md.schema_tools.lister()) == 2  # init row + just added row
        assert self.md.schema_tools.getter(schema_name='uniq-schema').schema_desc == 'insert result'

        # update duplicate entry:
        assert self.md.schema_tools.setter(schema_name='uniq-schema',schema_desc='update result') == 0
        assert len(self.md.schema_tools.lister()) == 2  # no changes since last check
        assert self.md.schema_tools.getter(schema_name='uniq-schema').schema_desc == 'update result'

        new_schema_rows = self.md.schema_tools.lister()
        #assert rowproxy_diff(old_schema_rows, new_schema_rows, expected_add_cnt=1, expected_del_cnt=0)

    def test_schema_list_and_delete(self):
        assert len(self.md.schema_tools.lister()) == 1
        old_schema_rows = self.md.schema_tools.lister()

        assert self.md.schema_tools.deleter(schema_name='geoip') == 1 # delete 1 row
        assert self.md.schema_tools.deleter(schema_name='geoip') == 0 # no rows left

        # delete all fields for collection
        for field in  self.md.field_tools.lister():
            if field.collection_id == self.collection_id:
                self.md.field_tools.deleter(collection_id=self.collection_id, field_id=field.field_id)

        # delete all collections for schema
        for collection in self.md.collection_tools.lister():
            if collection.schema_id == self.schema_id:
                assert self.md.collection_tools.deleter(schema_id=self.schema_id,
                                                        collection_id=collection.collection_id) == 1
        # delete all elements for schema
        for element in  self.md.element_tools.lister():
            self.md.element_tools.deleter(element_name=element.element_name)

        # delete schema
        self.md.schema_tools.deleter(schema_id=self.schema_id)

        # confirm all deletes again:
        assert len(self.md.element_tools.lister())    == 0
        assert len(self.md.field_tools.lister())      == 0
        assert len(self.md.collection_tools.lister()) == 0
        assert len(self.md.schema_tools.lister())     == 0


    def test_schema_bad_delete(self):
        #  i'd prefer for a failed delete to raise an exception
        #  need to research how that works
        old_schema_rows = self.md.schema_tools.lister()

        assert len(self.md.schema_tools.lister()) == 1
        assert self.md.schema_tools.deleter(schema_name='foobarky') == 0
        assert len(self.md.schema_tools.lister()) == 1

        new_schema_rows = self.md.schema_tools.lister()
        if old_schema_rows != new_schema_rows:
            # pylint: disable=E1101
            pytest.fail('Bad delete should have failed - but actually changed rows')
            # pylint: enable=E1101




#@pytest.mark.skipif("1 == 1")
class TestCollection(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        self.schema_id, self.collection_id = create_basic_metadata(self.md)

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_collection_row_count(self):
        assert len(self.md.collection_tools.lister()) == 1

    def test_collection_get(self):
        assert len(self.md.collection_tools.getter(schema_id=self.schema_id,
                                                   collection_name='geolite_country')) == 4

    def test_collection_select_nonexisting_row(self):
        assert self.md.collection_tools.getter(schema_id=self.schema_id,
                                               collection_name='blahFooBar') is None

    def test_collection_deletion_by_pk(self):
        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        collection_id = self.md.collection_tools.setter(**kva)
        assert collection_id != 0

        assert self.md.collection_tools.deleter(collection_id=collection_id) == 1


    def test_collection_deletion_by_uk(self):
        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        collection_id = self.md.collection_tools.setter(**kva)
        assert collection_id != 0
        assert self.md.collection_tools.deleter(schema_id=self.schema_id,
                                                collection_name='a') == 1

    def test_collection_deletion_by_partial_uk(self):
        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        collection_id = self.md.collection_tools.setter(**kva)
        assert collection_id != 0
        #print '\ndeletion by partial_uk'
        assert self.md.collection_tools.deleter(collection_name='a') == 0



    def test_collection_insert_update(self):
        old_rows = self.md.collection_tools.lister()

        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        kvb = {'schema_id'      : self.schema_id,
               'collection_name':'b',
               'collection_desc':'b1'}

        # add new entries:
        assert self.md.collection_tools.setter(**kva) != 0
        assert self.md.collection_tools.setter(**kvb) != 0
        assert len(self.md.collection_tools.lister()) == 3  # init row + just added row
        assert self.md.collection_tools.getter(schema_id=self.schema_id,
                                               collection_name='b').collection_desc == 'b1'
        assert self.md.collection_tools.getter(**kva).collection_desc == 'a1'

        # update duplicate entry:
        kvb['collection_desc'] = 'b2'
        assert self.md.collection_tools.setter(**kvb) == 0
        assert len(self.md.collection_tools.lister()) == 3  # no changes since last check
        assert self.md.collection_tools.getter(**kvb).collection_desc == 'b2'

        kvb['collection_desc'] = 'b3'
        assert self.md.collection_tools.setter(**kvb) == 0
        # should be no additions:
        assert len(self.md.collection_tools.lister()) == 3
        # should be changed:
        assert self.md.collection_tools.getter(schema_id=self.schema_id,
                                               collection_name='b').collection_desc == 'b3'
        # should be no changes to other rows:
        assert self.md.collection_tools.getter(schema_id=self.schema_id,
                                               collection_name='a').collection_desc == 'a1'

    def test_collection_insert_rejects(self):

        kv = {'collection_name':'a',
              'collection_desc':'a1',
              'schema_id'      :self.schema_id }
        orig_rowcount = len(self.md.collection_tools.lister())
        old_rows      = self.md.collection_tools.lister()

        # remove key attribute - should fail
        kv2 = kv.copy()
        kv2.pop('schema_id')
        # pylint: disable=E1101
        with pytest.raises(KeyError):
            self.md.collection_tools.setter(**kv2)
        assert len(self.md.collection_tools.lister()) == orig_rowcount  # init rows only
        # pylint: enable=E1101

        # confirm no unintended consequences:
        new_rows = self.md.collection_tools.lister()
        assert rowproxy_diff(old_rows, new_rows, expected_add_cnt=0, expected_del_cnt=0)


#@pytest.mark.skipif("1 == 1")
class TestField(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        self.schema_id, self.collection_id = create_basic_metadata(self.md)

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_field_row_count(self):
        assert len(self.md.field_tools.lister()) == 6

    def test_field_get(self):
        assert len(self.md.field_tools.getter(schema_id=self.schema_id,
                                              collection_id=self.collection_id,
                                              field_name='field-a')) == 8

    def test_field_select_nonexisting_row(self):
        print 'kenstuff:'
        assert self.md.field_tools.getter(schema_id=self.schema_id, 
                                      collection_id=self.collection_id,
                                      field_name='blahFooBar') is None

    def test_field_select_missing_collection_id(self):
        # pylint: disable=E1101
        with pytest.raises(KeyError):
            self.md.field_tools.getter(schema_id=self.schema_id, field_name='blahFooBar')
        # pylint: enable=E1101

    def test_field_update_with_invalid_element(self):
        field_keys = ['collection_id', 'field_name','field_desc', 'field_type', 'field_len','element_name']

        val_list   = [self.collection_id, 'field-z', 'field-a-desc','string',15  , None]
        kv         = dict(zip(field_keys, val_list))
        assert self.md.field_tools.setter(**kv) > 0
        assert self.md.field_tools.setter(**kv) == 0

        val_list   = [self.collection_id, 'field-z', 'field-a-desc','string', 15, 'bad_name']
        kv         = dict(zip(field_keys, val_list))
        # pylint: disable=E1101
        with pytest.raises(exc.IntegrityError):
            self.md.field_tools.setter(**kv)
        # pylint: enable=E1101



#@pytest.mark.skipif("1 == 1")
class TestElement(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        create_basic_metadata(self.md)

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_element_misc(self):

        kv = {'element_name':'cntry_name',
              'element_desc':'ISO standard country name',
              'element_type':'string',
              'element_len': 40  }

        # add new entry:
        assert self.md.element_tools.setter(**kv) != 0
        assert len(self.md.element_tools.lister()) == 2  # init + new row
        assert self.md.element_tools.getter(element_name='cntry_name').element_len == 40

        # update duplicate entry:
        kv['element_len'] = 100
        assert self.md.element_tools.setter(**kv) == 0
        assert len(self.md.element_tools.lister()) == 2  # no changes since last check
        assert self.md.element_tools.getter(element_name='cntry_name').element_len == 100



#@pytest.mark.skipif("1 == 1")
class TestReports(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        create_basic_metadata(self.md)

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_get_data_dictionary(self):

        results = self.md.get_data_dictionary('geoip','geolite_country')
        for row in results:
            assert row.schema_name == 'geoip'
            assert row.schema_desc == 'geoip data'
            assert row.collection_name == 'geolite_country'



def create_basic_metadata(md):
    """ Used by most above tests to insert a basic set of metadata.
    """

    #--- add schema & struct_types ---
    schema_id = md.schema_tools.setter(schema_name='geoip', 
                                       schema_desc='geoip data')

    #--- add elements ---
    kv = {'schema_id':schema_id,
          'element_name':'cntry_2byte',
          'element_desc':'cntry_2byte_desc',
          'element_type':'string',
          'element_len': 2 }
    md.element_tools.setter(**kv)
    assert md.element_tools.getter(element_name='cntry_2byte').element_len == 2

    #--- add collection ---
    keys = ['schema_id','collection_name','collection_desc']
    v    = [schema_id, 'geolite_country','free maxmind geoip feed']
    kv = dict(zip(keys, v))
    collection_id = md.collection_tools.setter(**kv) 
    assert collection_id > 0

    #--- add each field ---
    field_keys = ['collection_id', 'field_name','field_desc', 'field_type', 'field_len','element_name']
    val_list = [[collection_id, 'field-a', 'field-a-desc','string',15  , None],
                [collection_id, 'field-b', 'field-b-desc','string',15  , None],
                [collection_id, 'field-c', 'field-c-desc','int'   ,None, None],
                [collection_id, 'field-d', 'field-d-desc','int'   ,None, None],
                [collection_id, 'field-e', 'field-e-desc',None    ,None, 'cntry_2byte'],
                [collection_id, 'field-f', 'field-f-desc','string',40  , None ]]
    for row in val_list:
        kv = dict(zip(field_keys, row))
        assert md.field_tools.setter(**kv) > 0

    return schema_id, collection_id



def rowproxy_diff(old, new, expected_add_cnt=0, expected_del_cnt=0):

    if expected_add_cnt != len([x for x in new if x not in old]):
        return False
    elif expected_del_cnt !=  len([x for x in old if x not in new]):
        return False
    return True



def content_rpt(md):
    """ provides a report of what's left in the md.
        kinda useful for some diagnosis
    """
    rpt = '''SELECT s.schema_id,                             \
                    s.schema_name,                           \
                    c.collection_id,                         \
                    c.collection_name,                       \
                    f.field_id,                              \
                    f.field_name,                            \
                    f.field_order                            \
             FROM schema   s                                 \
                INNER JOIN collection c                      \
                  ON s.schema_id = c.schema_id               \
                INNER JOIN field      f                      \
                  ON c.collection_id = f.collection_id       \
          ''' 
    result = md.engine.execute(rpt)
    print
    #print 'final content report'
    print
    print '%-5.5s,  %-20.20s,  %-5.5s, %-20.20s, %-5.5s, %-20.20s, %-5.5s' % ('sch_id', 'sch_name', 'coll_id', 'coll_name', 'field_id', 'field_name', 'field_ord')
    for row in result:
        print '%-5.5s,  %-20.20s,  %-5.5s, %-20.20s, %-5.5s, %-20.20s, %-5.5s' % (row[0],row[1],row[2], row[3], row[4], row[5], row[6])
    print
    #print os.path.join(self.tempdir, 'metadata.db')
    #return result
