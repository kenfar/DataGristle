#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
from sqlalchemy import exc
try:
    import unittest2 as unittest
except ImportError:
    print 'WARNING: metadata could not import unittest2'
    import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.metadata  as mod


#---------------------------------------------------------
# test classes included here:
#   Test_schema
#   Test_struct_type
#   Test_struct
#   Test_element
#   Test_reports
#---------------------------------------------------------

#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(unittest.makeSuite(TestSchema))
#    suite.addTest(unittest.makeSuite(TestElement))
#    suite.addTest(unittest.makeSuite(TestCollection))
#    suite.addTest(unittest.makeSuite(TestField))
#    suite.addTest(unittest.makeSuite(TestReports))
#    unittest.TextTestRunner(verbosity=2).run(suite)
#
#    return suite


class TestSchema(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        self.schema_id, self.collection_id = create_basic_metadata(self.md)
        #content_rpt(self.md)

    def tearDown(self):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_schema_contents(self):
        row  = self.md.schema_tools.getter(schema_name='geoip')
        self.assertEqual(len(row), 3)  # 1 row with 3 columns
        self.assertEqual(row.schema_name, 'geoip')
        self.assertEqual(row.schema_desc, 'geoip data')

    def test_schema_selecting_nonexistent_row(self):
        self.assertIsNone(self.md.schema_tools.getter(schema_name='bogusgeoip'))

    def test_schema_upsert(self):
        #old_schema_rows = self.md.schema_tools.lister()
        # add new entry:
        self.assertIsNot(self.md.schema_tools.setter(schema_name='uniq-schema',schema_desc='insert result'), 0)
        self.assertEqual(len(self.md.schema_tools.lister()), 2)  # init row + just added row
        self.assertEqual(self.md.schema_tools.getter(schema_name='uniq-schema').schema_desc, 'insert result')

        # update duplicate entry:
        self.assertEqual(self.md.schema_tools.setter(schema_name='uniq-schema',schema_desc='update result'), 0)
        self.assertEqual(len(self.md.schema_tools.lister()), 2)  # no changes since last check
        self.assertEqual(self.md.schema_tools.getter(schema_name='uniq-schema').schema_desc, 'update result')

        new_schema_rows = self.md.schema_tools.lister()
        #self.assertTrue(rowproxy_diff(old_schema_rows, new_schema_rows, expected_add_cnt=1, expected_del_cnt=0))

    def test_schema_list_and_delete(self):
        self.assertEqual(len(self.md.schema_tools.lister()), 1)
        old_schema_rows = self.md.schema_tools.lister()

        self.assertRaises(exc.IntegrityError, self.md.schema_tools.deleter, schema_name='geoip')

        # delete all fields for collection
        for field in  self.md.field_tools.lister():
            if field.collection_id == self.collection_id:
                self.md.field_tools.deleter(collection_id=self.collection_id, field_id=field.field_id)

        # delete all collections for schema
        for collection in self.md.collection_tools.lister():
            if collection.schema_id == self.schema_id:
                self.assertEqual(self.md.collection_tools.deleter(schema_id=self.schema_id,
                                                               collection_id=collection.collection_id), 1)
        # delete all elements for schema
        for element in  self.md.element_tools.lister():
            self.md.element_tools.deleter(element_name=element.element_name)

        # delete schema
        self.md.schema_tools.deleter(schema_id=self.schema_id)

        # confirm all deletes again:
        self.assertEqual(len(self.md.element_tools.lister()),   0)
        self.assertEqual(len(self.md.field_tools.lister()),     0)
        self.assertEqual(len(self.md.collection_tools.lister()),0)
        self.assertEqual(len(self.md.schema_tools.lister()),    0)


    def test_schema_bad_delete(self):
        #  i'd prefer for a failed delete to raise an exception
        #  need to research how that works
        old_schema_rows = self.md.schema_tools.lister()

        self.assertEqual(len(self.md.schema_tools.lister()), 1)
        self.assertEqual(self.md.schema_tools.deleter(schema_name='foobarky'), 0)
        self.assertEqual(len(self.md.schema_tools.lister()), 1)

        new_schema_rows = self.md.schema_tools.lister()
        if old_schema_rows != new_schema_rows:
            #print 'failed!'
            self.fail()




class TestCollection(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        self.schema_id, self.collection_id = create_basic_metadata(self.md)

    def tearDown(self):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_collection_row_count(self):
        self.assertEqual(len(self.md.collection_tools.lister()), 1)

    def test_collection_get(self):
        self.assertEqual(len(self.md.collection_tools.getter(schema_id=self.schema_id,
                                                             collection_name='geolite_country')), 4)

    def test_collection_select_nonexisting_row(self):
        self.assertIsNone(self.md.collection_tools.getter(schema_id=self.schema_id,
                                                          collection_name='blahFooBar'))

    def test_collection_deletion_by_pk(self):
        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        collection_id = self.md.collection_tools.setter(**kva)
        self.assertIsNot(collection_id, 0)

        self.assertEqual(self.md.collection_tools.deleter(collection_id=collection_id), 1)


    def test_collection_deletion_by_uk(self):
        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        collection_id = self.md.collection_tools.setter(**kva)
        self.assertIsNot(collection_id, 0)
        self.assertEqual(self.md.collection_tools.deleter(schema_id=self.schema_id,
                                                          collection_name='a'), 1)

    def test_collection_deletion_by_partial_uk(self):
        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        collection_id = self.md.collection_tools.setter(**kva)
        self.assertIsNot(collection_id, 0)
        #print '\ndeletion by partial_uk'
        self.assertEqual(self.md.collection_tools.deleter(collection_name='a'), 0)



    def test_collection_insert_update(self):
        old_rows = self.md.collection_tools.lister()

        kva = {'schema_id'      : self.schema_id,
               'collection_name':'a',
               'collection_desc':'a1'}
        kvb = {'schema_id'      : self.schema_id,
               'collection_name':'b',
               'collection_desc':'b1'}

        # add new entries:
        self.assertIsNot(self.md.collection_tools.setter(**kva), 0)
        self.assertIsNot(self.md.collection_tools.setter(**kvb), 0)
        self.assertEqual(len(self.md.collection_tools.lister()), 3)  # init row + just added row
        self.assertEqual(self.md.collection_tools.getter(schema_id=self.schema_id,
                                                         collection_name='b').collection_desc, 'b1')
        self.assertEqual(self.md.collection_tools.getter(**kva).collection_desc, 'a1')

        # update duplicate entry:
        kvb['collection_desc'] = 'b2'
        self.assertEqual(self.md.collection_tools.setter(**kvb), 0)
        self.assertEqual(len(self.md.collection_tools.lister()), 3)  # no changes since last check
        self.assertEqual(self.md.collection_tools.getter(**kvb).collection_desc, 'b2')

        kvb['collection_desc'] = 'b3'
        self.assertEqual(self.md.collection_tools.setter(**kvb), 0)
        # should be no additions:
        self.assertEqual(len(self.md.collection_tools.lister()), 3)
        # should be changed:
        self.assertEqual(self.md.collection_tools.getter(schema_id=self.schema_id,
                                                         collection_name='b').collection_desc, 'b3')
        # should be no changes to other rows:
        self.assertEqual(self.md.collection_tools.getter(schema_id=self.schema_id,
                                                         collection_name='a').collection_desc, 'a1') 

    def test_collection_insert_rejects(self):

        kv = {'collection_name':'a',
              'collection_desc':'a1',
              'schema_id'      :self.schema_id }
        orig_rowcount = len(self.md.collection_tools.lister())
        old_rows      = self.md.collection_tools.lister()

        # remove key attribute - should fail
        kv2 = kv.copy()
        kv2.pop('schema_id')
        self.assertRaises(KeyError, self.md.collection_tools.setter, **kv2)
        self.assertEqual(len(self.md.collection_tools.lister()), orig_rowcount)  # init rows only

        # confirm no unintended consequences:
        new_rows = self.md.collection_tools.lister()
        self.assertTrue(rowproxy_diff(old_rows, new_rows, expected_add_cnt=0, expected_del_cnt=0))


class TestField(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        self.schema_id, self.collection_id = create_basic_metadata(self.md)

    def tearDown(self):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_field_row_count(self):
        self.assertEqual(len(self.md.field_tools.lister()), 6)

    def test_field_get(self):
        self.assertEqual(len(self.md.field_tools.getter(schema_id=self.schema_id,
                                                        collection_id=self.collection_id,
                                                        field_name='field-a')), 8)

    def test_field_select_nonexisting_row(self):
        self.assertIsNone(self.md.field_tools.getter(schema_id=self.schema_id,
                                                     collection_id=self.collection_id,
                                                     field_name='blahFooBar'))

    def test_field_select_missing_collection_id(self):
        self.assertRaises(KeyError, self.md.field_tools.getter,schema_id=self.schema_id,
                                                               field_name='blahFooBar')

    def test_field_update_with_invalid_element(self):
        field_keys = ['collection_id', 'field_name','field_desc', 'field_type', 'field_len','element_name']

        val_list   = [self.collection_id, 'field-z', 'field-a-desc','string',15  , None]
        kv         = dict(zip(field_keys, val_list))
        self.assertGreater(self.md.field_tools.setter(**kv), 0)
        self.assertEqual(self.md.field_tools.setter(**kv), 0)

        val_list   = [self.collection_id, 'field-z', 'field-a-desc','string', 15, 'bad_name']
        kv         = dict(zip(field_keys, val_list))
        self.assertRaises(exc.IntegrityError, self.md.field_tools.setter, **kv)



class TestElement(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        create_basic_metadata(self.md)

    def tearDown(self):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_element_misc(self):

        kv = {'element_name':'cntry_name',
              'element_desc':'ISO standard country name',
              'element_type':'string',
              'element_len': 40  }

        # add new entry:
        self.assertIsNot(self.md.element_tools.setter(**kv), 0)
        self.assertEqual(len(self.md.element_tools.lister()), 2)  # init + new row
        self.assertEqual(self.md.element_tools.getter(element_name='cntry_name').element_len, 40)

        # update duplicate entry:
        kv['element_len'] = 100
        self.assertEqual(self.md.element_tools.setter(**kv), 0)
        self.assertEqual(len(self.md.element_tools.lister()), 2)  # no changes since last check
        self.assertEqual(self.md.element_tools.getter(element_name='cntry_name').element_len, 100)



class TestReports(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)
        create_basic_metadata(self.md)

    def tearDown(self):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_get_data_dictionary(self):

        results = self.md.get_data_dictionary('geoip','geolite_country')
        for row in results:
            self.assertEqual(row.schema_name, 'geoip')
            self.assertEqual(row.schema_desc, 'geoip data')
            self.assertEqual(row.collection_name, 'geolite_country')



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
    assert(md.element_tools.getter(element_name='cntry_2byte').element_len == 2)

    #--- add collection ---
    keys = ['schema_id','collection_name','collection_desc']
    v    = [schema_id, 'geolite_country','free maxmind geoip feed']
    kv = dict(zip(keys, v))
    collection_id = md.collection_tools.setter(**kv) 
    assert(collection_id > 0)

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
        assert(md.field_tools.setter(**kv) > 0)

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
    rpt = '''SELECT schema.schema_name,                      \
                    struct.struct_name,                      \
                    struct.struct_type,                      \
                    struct.parent_struct_name,               \
                    struct.field_type,                       \
                    struct.field_len                         \
             FROM schema   schema                            \
                INNER JOIN struct struct                     \
                  ON schema.schema_name = struct.schema_name \
                INNER JOIN struct_type  stype                \
                  ON struct.struct_type = stype.struct_type  \
          ''' 
    result = md.db.execute(rpt)
    #print
    #print 'final content report'
    #print 
    #print 'schema, struct_parent_name, struct_name, struct_type, field_type, field_len'
    #for row in result:
    #    print '%s,  %-20.20s,  %-20.20s, %-10.10s, %-10.10s, %s ' % (row[0],row[3],row[1], row[2], row[4], row[5])
    #print
    #print os.path.join(self.tempdir, 'metadata.db')



#if __name__ == "__main__":
    #runner = unittest.TextTestRunner(verbosity=2)
    #runner.run(suite())
#    unittest.main(suite())
 

