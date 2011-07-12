#!/usr/bin/env python

from setuptools import setup, find_packages

version = "0.2"
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
      scripts      = ['scripts/gristle_determinator.py'],
      packages     = find_packages(),
      test_suite   = 'gristle.tests'
     )
