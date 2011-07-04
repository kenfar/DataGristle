#!/usr/bin/env python

from setuptools.core import setup, find_packages

version = "0.1"
DESCRIPTION      = 'A toolbox of ETL & Analysis Tools'
LONG_DESCRIPTION = open('README').read()

setup(name             = 'DataGristle',
      version          = version,
      description      = DESCRIPTION,
      long_description = LONG_DESCRIPTION,
      author           = 'Ken Farmer',
      author_email     = 'kenfar@gmail.com',
      url              = 'http://github.com/kenfar/DataGristle',
      license          = 'BSD',
      classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'License ::  OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Intended Audience :: System Administrators',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Topic :: Scientific/Engineering',
            'Topic :: Database',
            'Topic :: Utilities'
            ],
      download_url = 'http://github.com/downloads/kenfar/DataGristle/DataGristle-%s.tar.gz' % version,
      scripts      = ['dg_determinator.py'],
      packages     = find_packages(),
      test_suite   = 'data_gristle.tests'
     )
