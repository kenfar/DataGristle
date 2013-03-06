Datagristle is a toolbox of tough and flexible data connectors and analyzers.  
It's kind of an interactive mix between ETL and data analysis optimized for 
rapid analysis and manipulation of a wide variety of data.

It's neither an enterprise ETL tool, nor an enterprise analysis, reporting, 
or data mining tool.  It's intended to be an easily-adopted tool for technical
analysts that combines the most useful subset of data transformation and 
analysis capabilities necessary to do 80% of the work.  Its open source python
codebase allows it to be easily extended to with custom code to handle that
always challenging last 20%.

Current Status:  Strong support for easy analysis and simple transformations of
csv files. 

#Next Steps:  

   * attractive PDF output of gristle_determinator.py
   * metadata database population

#Its objectives include:

   * multi-platform (unix, linux, mac os, windows with effort) 
   * multi-language (primarily python)
   * free - no cripple-licensing
   * primary audience is programming data analysts - not non-technical analysts
   * primary environment is command-line rather than windows, graphical desktop
     or eclipse
   * extensible
   * allow a bi-directional iteration between ETL & data analysis
   * can quickly perform initial data analysis prior to longer-duration, deeper
     analysis with heavier-weight tools.


#Installation

   * Using [pip](http://www.pip-installer.org/en/latest/) (preferred) or [easyinstall](http://peak.telecommunity.com/DevCenter/EasyInstall):

       $ pip install datagristle
       $ easy_install datagristle

   * Or install manually from pypi:

       $ mkdir ~\Downloads
       $ wget https://pypi.python.org/packages/source/d/datagristle/datagristle-0.46.tar.gz
       $ tar -xvf easy_install datagristle
       $ cd ~\Downloads\datagristle-*
       $ python setup.py install
      


#Dependencies

   * Python 2.6 or Python 2.7

#Mature Utilities Provided in This Release:

   * gristle_determinator
       - Identifies file formats, generates metadata, prints file analysis report
       - This is the most mature - and also used by the other utilities so that 
         you generally do not need to enter file structure info.
   * gristle_freaker
       - Produces a frequency distribution of multiple columns from input file.
   * gristle_slicer
       - Used to extract a subset of columns and rows out of an input file.
   * gristle_viewer
       - Shows one record from a file at a time - formatted based on metadata. 

#Immature Utilities Provided in This Release:

   * gristle_differ
       - Shows differences between two files
   * gristle_file\_converter
       - Converts a csv from one dialect to another.  Can handle multi-character
         field delimiters as well as record delimiters.
   * gristle_filter
       - Applies simple filter logic to file.
   * gristle_scalar
       - Performs scalar operations (min, max, avg, count unique, etc) on a file
   * gristle_validator
       - Validates a file - currently just confirms number of fields for each row.
   * gristle_metadata
       - Manages metadata - allows users to query, add, update, delete
         file, field, transformation, reporting descriptions.
   * gristle_validator 
       - Confirms validity of database and file structure and contents.

#Future utilities:

   * gristle_generator
       - Generates test data based on gristle metadata
   * gristle_file\_joiner.py
       - joins two files on their common keys and produces a new file
   * gristle_grouper.py
       - reads a file, aggregates on a given set of fields, produces a new file
   * gristle_db\_loader.py 
       - loads a file into a database
   * gristle_db\_extractor.py 
       - extracts data from a database into a file
   * gristle_field\_merge.py 
       - prints the matched values from multiple files side by side along with counts

#Licensing

   * Gristle uses the BSD license - see the separate LICENSE file for further 
     information


#Copyright

   * Copyright 2011,2012,2013 Ken Farmer

