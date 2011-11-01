#!/usr/bin/env python

from setuptools import setup, find_packages

version = "0.42"
DESCRIPTION      = 'A toolbox and library of ETL & data analysis tools'
LONG_DESCRIPTION = open('README').read()

setup(name             = 'gristle',
      version          = version,
      description      = DESCRIPTION,
      long_description = LONG_DESCRIPTION,
      author           = 'Ken Farmer',
      author_email     = 'kenfar@gmail.com',
      url              = 'http://github.com/kenfar/DataGristle',
      license          = 'BSD',
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Science/Research',
            'License ::  OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Operating System :: POSIX',
            'Topic :: Scientific/Engineering',
            'Topic :: Database',
            'Topic :: Scientific/Engineering :: Information Analysis',
            'Topic :: Text Processing',
            'Topic :: Utilities'
            ],
      download_url = 'http://github.com/downloads/kenfar/DataGristle/DataGristle-%s.tar.gz' % version,
      scripts      = ['scripts/gristle_determinator.py',
                      'scripts/gristle_differ.py',
                      'scripts/gristle_file_converter.py',
                      'scripts/gristle_filter.py',
                      'scripts/gristle_freaker.py',
                      'scripts/gristle_graphviz_generator.py',
                      'scripts/gristle_scalar.py',
                      'scripts/gristle_slicer.py',
                      'scripts/gristle_viewer.py' ],
      packages     = find_packages(),
      test_suite   = 'gristle.tests.__init__.py'
     )
