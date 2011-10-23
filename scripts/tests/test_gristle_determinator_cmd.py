#!/usr/bin/env python
#  See the file "LICENSE" for the full license governing this code. 
""" Tests gristle_determinator.py
    
    Contains a primary class: FileStructureFixtureManager
    Which is extended by six classes that override various methods or variables.
    This is a failed experiment - since the output isn't as informative as it 
    should be.  This should be redesigned.
"""

import sys
import os
import tempfile
import random
import unittest
import time
import subprocess
import fileinput

sys.path.append('../')
sys.path.append('../../')
import gristle_determinator  as mod

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFileStructure2))
    suite.addTest(unittest.makeSuite(TestFileStructure3))
    suite.addTest(unittest.makeSuite(TestFileStructure4))
    suite.addTest(unittest.makeSuite(TestFileStructure5))
    suite.addTest(unittest.makeSuite(TestFileStructureSingleCol))
    unittest.TextTestRunner(verbosity=2).run(suite)

    return suite



def generate_test_file(delim, rec_list, quoted=False):
    (fd, fqfn) = tempfile.mkstemp()
    fp = os.fdopen(fd,"w") 
 
    for rec in rec_list:
        if quoted:
            for i in range(len(rec)):
                rec[i] = '"%s"' % rec[i] 
        outrec = delim.join(rec)+'\n'
        fp.write(outrec)

    fp.close()
    return fqfn



class FileStructureFixtureManager(unittest.TestCase):

    def setUp(self):

        self.filename  = {}  # key is fixture #
        self.recs      = {}  # key is fixture #
        self.objective = {}  # key is fixture #
        self.label     = 0
        self.value     = 1
        self.default_recs = [ ['Alabama','8','18'],
                              ['Alaska','6','16'],
                              ['Arizona','4','14'],
                              ['Arkansas','2','12'],
                              ['California','19','44'] ]

        # defines expected output in a way that can be easily looped through
        # dictionary key is record number from output
        # dictionary value is list that identifies value on each side of '=' in output
        # notes:
        #   - QUOTE_MINIMAL will generally be result rather than QUOTE_NONE - even if no quotes exist
        self.default_obj = { 2:['format type',      'csv']           ,
                             3:['field cnt',        '3']             ,
                             4:['record cnt',       '5']             ,
                             5:['has header',       'False']         ,
                             6:['delimiter',        '|']             ,
                             7:['csv quoting',      'True']          ,  
                             8:['skipinitialspace', 'False']         ,
                             9:['quoting',          'QUOTE_MINIMAL'] ,
                            10:['doublequote',      'False' ]        ,
                            11:['quotechar',        '"' ]            ,
                            12:['lineterminator',   '%r' %  '\r\n' ] ,  
                            13:['escapechar',       'None'         ] }

        # defines expected field analysis output:
        self.default_field_obj = { 2:['format type',      'csv']           ,
                                   3:['field cnt',        '3']             ,
                                   4:['record cnt',       '5']             ,
                                   5:['has header',       'False']         ,
                                   6:['delimiter',        '|']             }

        self.cmd = None  # will be overridden by instances

        self.field_analysis_results = {}

    def tearDown(self):
        for key in self.filename:
            os.remove(self.filename[key])

    def _create_fixture(self, fix):

        self.recs[fix]      = self.default_recs
        self.filename[fix]  = generate_test_file('|', self.recs[fix])
        self.objective[fix] = self.default_obj
        return self.filename[fix]


    def _eval_file_struct(self, fix):

        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, close_fds=True)
        p_output = p.communicate()[0]

        p_recs   = p_output[:-1].split('\n')
        assert(p_recs[1].startswith('File Structure:'))

        objective = self.objective[fix]
        label     = self.label
        value     = self.value

        for rownum in objective.keys():
            actual = p_recs[rownum].split(':')
            try:
               assert(actual[label].strip().startswith(objective[rownum][label]))
               assert(actual[value].strip().startswith(objective[rownum][value]))
            except:
               print 'actual:    %s %s' % (actual[label].strip(), actual[value].strip())
               print 'objective: %s %s' % (objective[rownum][label], objective[rownum][value])
               raise    

    def broken_eval_field_struct(self, fix):
        # reads entire command output - skipping past file section and focusing
        # on just the field bits

        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, close_fds=True)
        p_output = p.communicate()[0]

        p_recs        = p_output[:-1].split('\n')
        field_section = False
        i             = 0
        for rec in p_recs:      # work thru File Structure section
            #print rec
            if 'Fields Analysis Results:' in rec:
                field_section  = True
                i              = 1
            if 'Top Values:' in rec:
                field_section  = False
            if not field_section:
                continue
            i  += 1            
            if '----------------' in rec:
                continue
            if not rec:   
                continue
            if ':' in rec:
                pair = rec.split(':')
                self.field_analysis_results[pair[0].strip()] = pair[1].strip()
                #print rec
        #print self.field_analysis_results
        print 'test harness is incomplete'
        sys.exit(0)
        


        assert(p_recs[1].startswith('File Structure:'))

        objective = self.objective[fix]
        label     = self.label
        value     = self.value

        for rownum in objective.keys():
            actual = p_recs[rownum].split('=')
            try:
               assert(actual[label].strip().startswith(objective[rownum][label]))
               assert(actual[value].strip().startswith(objective[rownum][value]))
            except:
               print 'actual:    %s %s' % (actual[label].strip(), actual[value].strip())
               print 'objective: %s %s' % (objective[rownum][label], objective[rownum][value])
               raise    


    def test_simple_file_counts(self):
        fix = 1
        fn  = self._create_fixture(fix) 
        self.cmd = ['../gristle_determinator.py', '-f', fn, '-b' ]   # may need to be overridden
        #for rec in fileinput.input(fn):  print rec
        self._eval_file_struct(fix)

    def test_empty_files(self):
        # Test behavior with one or both files empty
        pass

    def test_multi_column(self):
        # Tests ability to specify multiple key or comparison columns
        pass

    def test_dialect_overrides(self):
        # Tests hasheader, delimiter, and recdelimiter args
        pass

    def broken_test_simple_field_counts(self):
        fix = 2
        fn  = self._create_fixture(fix) 
        self.cmd = ['../gristle_determinator.py', '-f', fn, '-c', 0 ]   # may need to be overridden
        #for rec in fileinput.input(fn):  print rec
        self._eval_field_struct(fix)


class TestFileStructure2(FileStructureFixtureManager):

    def _create_fixture(self, fix):

        self.recs[fix]         = self.default_recs
        self.filename[fix]     = generate_test_file('?', self.recs[fix])
        self.objective[fix]    = self.default_obj
        self.objective[fix][6] = ['delimiter', '?']  
        return self.filename[fix]

    def test_simple_field_counts(self):
        # Turning this test off since it only handles file structure and not fields.
        pass



class TestFileStructure3(FileStructureFixtureManager):

    def _create_fixture(self, fix):

        self.recs[fix]         = self.default_recs
        self.filename[fix]     = generate_test_file(',', self.recs[fix])
        self.objective[fix]    = self.default_obj
        self.objective[fix][6] = ['delimiter', ',']  
        return self.filename[fix]

    def test_simple_field_counts(self):
        """ Turning this test off since it only handles file structure and not fields.
        """
        pass



class TestFileStructure4(FileStructureFixtureManager):

    def _create_fixture(self, fix):

        self.recs[fix]         = self.default_recs
        self.filename[fix]     = generate_test_file('|', self.recs[fix], quoted=True)
        self.objective[fix]    = self.default_obj
        self.objective[fix][6] = ['delimiter', '|']  
        return self.filename[fix]

    def test_simple_field_counts(self):
        """ Turning this test off since it only handles file structure and not fields.
        """
        pass


class TestFileStructure5(FileStructureFixtureManager):

    def _create_fixture(self, fix):

        self.default_recs = [ ['Alabama','','18'],
                              ['Alaska','','16'],
                              ['Arizona','','14'],
                              ['Arkansas','','12'],
                              ['California','','44'] ]
        self.recs[fix]         = self.default_recs
        self.filename[fix]     = generate_test_file('|', self.recs[fix], quoted=True)
        self.objective[fix]    = self.default_obj
        self.objective[fix][6] = ['delimiter', '|']  
        return self.filename[fix]

    def test_simple_field_counts(self):
        """ Turning this test off since it only handles file structure and not fields.
        """
        pass


class TestFileStructureSingleCol(FileStructureFixtureManager):
    """ Test a single empty column
    """
    #print 'TestFileStrucutreSingleCol'

    def _create_fixture(self, fix):

        self.default_recs = [ ['Alabama','','18'],
                              ['Alaska','','16'],
                              ['Arizona','','14'],
                              ['Arkansas','','12'],
                              ['California','','44'] ]
        self.recs[fix]         = self.default_recs
        self.recs[fix]         = self.default_recs
        self.filename[fix]     = generate_test_file('|', self.recs[fix], quoted=True)
        self.objective[fix]    = self.default_obj
        self.objective[fix][6] = ['delimiter', '|']  
        return self.filename[fix]

    def test_simple_file_counts(self):
        pass

    def broken_test_simple_field_counts(self):
        fix = 2
        fn  = self._create_fixture(fix) 
        self.cmd = ['../gristle_determinator.py', '-f', fn, '-c', '1' ]   # may need to be overridden
        self._eval_field_struct(fix)


if __name__ == "__main__":
    unittest.main(suite())



