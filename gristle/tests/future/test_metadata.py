#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 
#  todo:
#  1.  add struct!

import sys
import os
import tempfile
import random
import unittest
#import unittest2  as unittest
#import shutil

sys.path.append('../')
import metadata  as mod


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test_new_md))

    return suite


class Test_new_md(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.md      = mod.GristleMetaData(self.tempdir)

        self.md.schema_put('geoip', 'geoip data')

        self.md.struct_type_write('collection', 'a set of fields')
        self.md.struct_type_write('field', 'a single atomic cell of data')

        kv = {'struct_name':'geolite_country',
              'struct_desc':'free maxmind geoip country feed',
              'schema_name':'geoip',
              'struct_type':'collection'}
        self.md.generic_writer(self.md.struct, kv)

        kv = {'struct_name':'ip_string_block_start',
              'struct_desc':'n/a',
              'schema_name':'geoip',
              'struct_type':'field',
              'parent_struct_name':'geolite_country',
              'field_type':'string',
              'field_len':15}
        self.md.generic_writer(self.md.struct, kv)

        kv = {'struct_name':'ip_string_block_stop',
              'struct_desc':'n/a',
              'schema_name':'geoip',
              'struct_type':'field',
              'parent_struct_name':'geolite_country',
              'field_type':'string',
              'field_len':15}
        self.md.generic_writer(self.md.struct, kv)

        kv = {'struct_name':'ip_int_block_start',
              'struct_desc':'n/a',
              'schema_name':'geoip',
              'struct_type':'field',
              'parent_struct_name':'geolite_country',
              'field_type':'integer'}
        self.md.generic_writer(self.md.struct, kv)

        kv = {'struct_name':'ip_int_block_stop',
              'struct_desc':'n/a',
              'schema_name':'geoip',
              'struct_type':'field',
              'parent_struct_name':'geolite_country',
              'field_type':'integer'}
        self.md.generic_writer(self.md.struct, kv)

        kv = {'struct_name':'cntry_2byte',
              'struct_desc':'n/a',
              'schema_name':'geoip',
              'struct_type':'field',
              'parent_struct_name':'geolite_country',
              'field_type':'string',
              'field_len': 2  }
        self.md.generic_writer(self.md.struct, kv)

        kv = {'struct_name':'cntry_name',
              'struct_desc':'n/a',
              'schema_name':'geoip',
              'struct_type':'field',
              'parent_struct_name':'geolite_country',
              'field_type':'string',
              'field_len': 40  }
        self.md.generic_writer(self.md.struct, kv)


    def tearDown(self):
        self._content_rpt()
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def _content_rpt(self):
        rpt = '''SELECT schema.schema_name,                      \
                        struct.struct_name,                      \
                        struct.struct_type,                      \
                        struct.parent_struct_name,               \
                        struct.field_type,                       \
                        struct.field_len                         \
                 FROM bmd_schema   schema                        \
                    INNER JOIN bmd_struct struct                 \
                      ON schema.schema_name = struct.schema_name \
                    INNER JOIN bmd_struct_type  stype            \
                      ON struct.struct_type = stype.struct_type  \
              ''' 
        result = self.md.db.execute(rpt)
        print
        print
        print 'schema, struct_parent_name, struct_name, struct_type, field_type, field_len'
        for row in result:
            print '%s,  %-20.20s,  %-20.20s, %-10.10s, %-10.10s, %s ' % (row[0],row[3],row[1], row[2], row[4], row[5])
        print
        print os.path.join(self.tempdir, 'metadata.db')


    def test_schema(self):
        """Tests putting good & bad data into bmd_schema
        """
        row  = self.md.schema_get('geoip')
        self.assertTrue(len(row), 1)
        schema_name  = row[0][0]
        schema_desc  = row[0][1]
        self.assertEqual(schema_name, 'geoip')
        self.assertEqual(schema_desc, 'geoip data')

        bad_row  = self.md.schema_get('bogusgeoip')
        assert(len(bad_row) == 0)


    def test_struct_type(self):
        #result  = self.md.db.execute("select * from bmd_schema")
        #for row in result:
        #    print 'struct:  %s' % row
        row  = self.md.struct_type_get('collection')
        self.assertTrue(len(row), 1)
        struct_type      = row[0][0]
        struct_type_desc = row[0][1]
        self.assertEqual(struct_type,'collection')
        self.assertEqual(struct_type_desc, 'a set of fields')

        bad_row  = self.md.struct_type_get('boguscollection')
        assert(len(bad_row) == 0)


if __name__ == "__main__":
    unittest.main()


