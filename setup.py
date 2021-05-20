#!/usr/bin/env python

import os
import uuid
from setuptools import setup, find_packages

def read(*paths):
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

VERSION = read('datagristle/_version.py').split('=')[1].strip()[1:-1]
REQUIREMENTS = read('requirements.txt')
DESCRIPTION = 'A toolbox and library of ETL, data quality, and data analysis tools'

assert VERSION.count('.') == 2

setup(name='datagristle',
      version=VERSION,
      description=DESCRIPTION,
      long_description=(read('README.rst') + '\n\n' + read('CHANGELOG.rst')),
      long_description_content_type='text/markdown',
      keywords="data analysis quality utility etl",
      author='Ken Farmer',
      author_email='kenfar@gmail.com',
      url='http://github.com/kenfar/DataGristle',
      license='BSD',
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Information Technology',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: BSD License',
                   'Programming Language :: Python',
                   'Operating System :: POSIX',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Database',
                   'Topic :: Scientific/Engineering :: Information Analysis',
                   'Topic :: Text Processing',
                   'Topic :: Utilities'],
      scripts=['scripts/gristle_converter',
               'scripts/gristle_determinator',
               'scripts/gristle_differ',
               'scripts/gristle_dir_merger',
               'scripts/gristle_file_converter',
               'scripts/gristle_freaker',
               'scripts/gristle_metadata',
               'scripts/gristle_md_reporter',
               'scripts/gristle_processor',
               'scripts/gristle_profiler',
               'scripts/gristle_slicer',
               'scripts/gristle_sorter',
               'scripts/gristle_validator',
               'scripts/gristle_viewer'],
      install_requires=REQUIREMENTS,
      packages=find_packages(),
     )
