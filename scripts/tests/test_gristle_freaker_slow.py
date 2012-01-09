#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 

import sys
import os
import tempfile
import random
import unittest
import csv

sys.path.append('../')
sys.path.append('../../')
import gristle_freaker  as mod
from pprint import pprint as pp


gen_rec_number     = 10000000   # 10 million
print 'Number of records that will be generated: %d' % gen_rec_number

# shut off the printing of warnings & info statements from module
old_stdout = sys.stdout
old_stderr = sys.stderr
null       = open(os.devnull, 'wb')
sys.stdout = sys.stderr = null


def suite():

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test_ColumnLengthTracker))
    suite.addTest(unittest.makeSuite(Test_create_key))
    suite.addTest(unittest.makeSuite(Test_create_output_row))
    suite.addTest(unittest.makeSuite(Test_freq_sorter))
    suite.addTest(unittest.makeSuite(Test_build_freq))
    suite.addTest(unittest.makeSuite(Test_get_opts_and_args))

    return suite

# create test plan
# create cmd test program


class Test_build_freq(unittest.TestCase):
   def setUp(self):
       self.dialect                = csv.Dialect
       self.dialect.delimiter      = '|'
       self.dialect.quoting        = True
       self.dialect.quotechar      = '"'
       self.dialect.hasheader      = False
       self.dialect.lineterminator = '\n'
       self.files                  = []
       self.files.append(self.generate_test_file(self.dialect.delimiter, gen_rec_number))
       self.columns                = [1,2]
       self.number                 = gen_rec_number

   def generate_test_file(self, delim, record_cnt):
       (fd, fqfn) = tempfile.mkstemp(prefix='FreakerTestIn_')
       fp = os.fdopen(fd,"w")

       cnt = 0
       for i in range(record_cnt):
           cnt += 1
           fields = []
           fields.append(str(i))
           fields.append(random.choice(('A1','A2','A3','A4')))
           fields.append(random.choice(('B1','B2')))
           fp.write(delim.join(fields)+'\n')

       fp.close()
       return fqfn
         
   def test_bf_01_multicol(self):
       sampling_method = 'non'
       sampling_rate   = None
       field_freq, truncated = mod.build_freq(self.files, self.dialect, self.columns, self.number, sampling_method, sampling_rate)
       assert(not truncated)
       assert(sum(field_freq.values()) == gen_rec_number)
       assert(len(field_freq) == 8)               
       for key in field_freq.keys():
           assert(key[0] in ['A1','A2','A3','A4'])
           assert(key[1] in ['B1','B2'])



if __name__ == "__main__":
    unittest.main()




