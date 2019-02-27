Datagristle is a toolbox of tough and flexible data connectors and analyzers.  
It's kind of an interactive mix between ETL and data analysis optimized for 
rapid analysis and manipulation of a wide variety of data.

It's neither an enterprise ETL tool, nor an enterprise analysis, reporting, 
or data mining tool.  It's intended to be an easily-adopted tool for technical
analysts that combines the most useful subset of data transformation and 
analysis capabilities necessary to do 80% of the work.  Its open source python
codebase allows it to be easily extended to with custom code to handle that
always challenging last 20%.

Current Status:  Strong support for easy analysis, simple transformations of
csv files, ability to create data dictionaries, change detection, and emerging
data quality capabilities.

More info is on the DataGristle wiki here: 
   https://github.com/kenfar/DataGristle/wiki


# Next Steps:  

   * attractive PDF output of gristle_determinator.py
   * metadata database population

# Its objectives include:

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


# Installation

   * Using [pip](http://www.pip-installer.org/en/latest/):

       ~~~
       $ pip install datagristle
       ~~~
      

# Dependencies

   * Python 3.7


# Utilities Provided in This Release:

   * gristle_slicer
       - Used to extract a subset of columns and rows out of an input file.
   * gristle_freaker
       - Produces a frequency distribution of multiple columns from input file.
   * gristle_determinator
       - Identifies file formats, generates metadata, prints file analysis report
       - This is the most mature - and also used by the other utilities so that 
         you generally do not need to enter file structure info.
   * gristle_differ
       - Allows two identically-structured files to be compared by key columns
         and split into same, inserts, deletes, chgold and chgnew files.
       - The user can configure which columns are included in the comparison.
       - Post delta transformations can include assign sequence numbers, copying
         field values, etc.
   * gristle_validator
       - Validates csv files by confirming that all records have the right number
         of fields, and by apply a json schema full of requirements to each record.
   * gristle_dir_merger
       - Used to consolidate large directories with options to control matching
         criteria as well as matching actions.
   * gristle_processor
       - Used to apply actions, like delete, compress, etc, to files based on
         very flexible criteria.
   * gristle_viewer
       - Shows one record from a file at a time - formatted based on metadata. 


# gristle_validator
    Splits a csv file into two separate files based on how records pass or fail
    validation checks:
       - Field count - checks the number of fields in each record against the
         number required.  The correct number of fields can be provided in an
         argument or will default to using the number from the first record.
       - Schema - uses csv file requirements defined in a json-schema file for
         quality checking.  These requirements include the number of fields, 
         and for each field - the type, min & max length, min & max value,
         whether or not it can be blank, existance within a list of valid
         values, and finally compliance with a regex pattern.

    The output can just be the return code (0 for success, 1+ for errors), can
    be some high level statistics, or can be the csv input records split between
    good and erroneous files.  Output can also be limited to a random subset.

    Examples:
       $ gristle_validator  sample.csv -f 3
             Prints all valid input rows to stdout, prints all records with 
             other than 3 fields to stderr along with an extra final field that
             describes the error.
       $ gristle_validator  sample.csv 
             Prints all valid input rows to stdout, prints all records with 
             other than the same number of fields found on the first record to
             stderr along with an extra final field that describes the error.
       $ gristle_validator  sample.csv  -d '|' --hasheader
             Same comparison as above, but in this case the file was too small
             or complex for the pgm to automatically determine csv dialect, so
             we had to explicitly give that info to program.
       $ gristle_validator  sample.csv --outgood sample_good.csv --outerr sample_err.csv
             Same comparison as above, but explicitly splits good and bad data
             into separate files.
       $ gristle_validator  sample.csv --randomout 1
             Same comparison as above, but only writes a random 1% of data out.
       $ gristle_validator  sample.csv --silent
             Same comparison as above, but writes nothing out.  Exit code can be
             used to determine if any bad records were found.
       $ gristle_validator  sample.csv --validschema sample_schema.csv 
             The above command checks both field count as well as validations
             described in the sample_schema.csv file.  Here's an example of what 
             that file might look like:
                items:
                    - title:            rowid
                      blank:            False
                      required:         True
                      dg_type:          integer
                      dg_minimum:       1
                      dg_maximum:       60
                    - title:            start_date
                      blank:            False
                      minLength:        8
                      maxLength:        10
                      pattern:          '[0-9]*/[0-9]*/[1-2][0-9][0-9][0-9]'
                    - title:            location
                      blank:            False
                      minLength:        2
                      maxLength:        2
                      enum:             ['ny','tx','ca','fl','wa','ga','al','mo']
    


# gristle_slicer
    Extracts subsets of input files based on user-specified columns and rows.
    The input csv file can be piped into the program through stdin or identified
    via a command line option.  The output will default to stdout, or redirected
    to a filename via a command line option.

    The columns and rows are specified using python list slicing syntax -
    so individual columns or rows can be listed as can ranges.   Inclusion
    or exclusion logic can be used - and even combined.

    Examples:
       $ gristle_slicer sample.csv
                    Prints all rows and columns
       $ gristle_slicer sample.csv -c":5, 10:15" -C 13
                    Prints columns 0-4 and 10,11,12,14 for all records
       $ gristle_slicer sample.csv -C:-1
                    Prints all columns except for the last for all records
       $ gristle_slicer sample.csv -c:5 -r-100
                    Prints columns 0-4 for the last 100 records
       $ gristle_slicer sample.csv -c:5 -r-100 -d'|' --quoting=quote_all
                    Prints columns 0-4 for the last 100 records, csv
                    dialect info (delimiter, quoting) provided manually)
       $ cat sample.csv | gristle_slicer -c:5 -r-100 -d'|' --quoting=quote_all
                    Prints columns 0-4 for the last 100 records, csv
                    dialect info (delimiter, quoting) provided manually)
     

# gristle_freaker
    Creates a frequency distribution of values from columns of the input file
    and prints it out in columns - the first being the unique key and the last 
    being the count of occurances.

    
    Examples:
       $ gristle_freaker sample.csv -d '|'  -c 0
                    Creates two columns from the input - the first with
                    unique keys from column 0, the second with a count of
                    how many times each exists.
       $ gristle_freaker sample.csv -d '|'  -c 0 --sortcol 1 --sortorder forward --writelimit 25
                    In addition to what was described in the first example, 
                    this example adds sorting of the output by count ascending 
                    and just prints the first 25 entries.
       $ gristle_freaker sample.csv -d '|'  -c 0 --sampling_rate 3 --sampling_method interval
                    In addition to what was described in the first example,
                    this example adds a sampling in which it only references
                    every third record.
       $ gristle_freaker sample.csv -d '|'  -c 0,1
                    Creates three columns from the input - the first two
                    with unique key combinations from columns 0 & 1, the 
                    third with the number of times each combination exists.
       $ gristle_freaker sample.csv -d '|'  -c -1
                    Creates two columns from the input - the first with unique
                    keys from the last column of the file (negative numbers 
                    wrap), then a second with the number of times each exists.
       $ gristle_freaker sample.csv -d '|'  --columntype all
                    Creates two columns from the input - all columns combined
                    into a key, then a second with the number of times each
                    combination exists.
       $ gristle_freaker sample.csv -d '|'  --columntype each
                    Unlike the other examples, this one performs a separate
                    analysis for every single column of the file.  Each analysis
                    produces three columns from the input - the first is a 
                    column number, second is a unique value from the column, 
                    and the third is the number of times that value appeared.  
                    This output is repeated for each column.


# gristle_viewer
    Displays a single record of a file, one field per line, with field names 
    displayed as labels to the left of the field values.  Also allows simple 
    navigation between records.

    Examples:
       $ gristle_viewer sample.csv -r 3 
                    Presents the third record in the file with one field per line
                    and field names from the header record as labels in the left
                    column.
       $ gristle_viewer sample.csv -r 3  -d '|' -q quote_none
                    In addition to what was described in the first example this
                    adds explicit csv dialect overrides.
                           

# gristle_determinator
    Analyzes the structures and contents of csv files in the end producing a 
    report of its findings.  It is intended to speed analysis of csv files by
    automating the most common and frequently-performed analysis tasks.  It's
    useful in both understanding the format and data and quickly spotting issues.

    Examples:
       $ gristle_determinator japan_station_radiation.csv
                    This command will analyze a file with radiation measurements
                    from various Japanese radiation stations.

        File Structure:
        format type:       csv
        field cnt:         4
        record cnt:        100
        has header:        True
        delimiter:                   
        csv quoting:       False   
        skipinitialspace:  False    
        quoting:           QUOTE_NONE  
        doublequote:       False   
        quotechar:         "       
        lineterminator:    '\n'    
        escapechar:        None    

        Field Analysis Progress: 
        Analyzing field: 0
        Analyzing field: 1
        Analyzing field: 2
        Analyzing field: 3

        Fields Analysis Results: 

            ------------------------------------------------------
            Name:             station_id           
            Field Number:     0                    
            Wrong Field Cnt:  0                    
            Type:             timestamp            
            Min:              1010000001           
            Max:              1140000006           
            Unique Values:    99                   
            Known Values:     99                   
            Top Values not shown - all values are unique

            ------------------------------------------------------
            Name:             datetime_utc         
            Field Number:     1                    
            Wrong Field Cnt:  0                    
            Type:             timestamp            
            Min:              2011-02-28 15:00:00  
            Max:              2011-02-28 15:00:00  
            Unique Values:    1                    
            Known Values:     1                    
            Top Values: 
                2011-02-28 15:00:00                      x 99 occurrences

            ------------------------------------------------------
            Name:             sa                   
            Field Number:     2                    
            Wrong Field Cnt:  0                    
            Type:             integer              
            Min:              -999                 
            Max:              52                   
            Unique Values:    35                   
            Known Values:     35                   
            Mean:             2.45454545455        
            Median:           38.0                 
            Variance:         31470.2681359        
            Std Dev:          177.398613681        
            Top Values: 
                41                                       x 7 occurrences
                42                                       x 7 occurrences
                39                                       x 6 occurrences
                37                                       x 5 occurrences
                46                                       x 5 occurrences
                17                                       x 4 occurrences
                38                                       x 4 occurrences
                40                                       x 4 occurrences
                45                                       x 4 occurrences
                44                                       x 4 occurrences

            ------------------------------------------------------
            Name:             ra                   
            Field Number:     3                    
            Wrong Field Cnt:  0                    
            Type:             integer              
            Min:              -888                 
            Max:              0                    
            Unique Values:    2                    
            Known Values:     2                    
            Mean:             -556.121212121       
            Median:           -888.0               
            Variance:         184564.833792        
            Std Dev:          429.610095077        
            Top Values: 
                -888                                     x 62 occurrences
                0                                        x 37 occurrences


# gristle_differ
    gristle_differ compares two files, typically an old and a new file, based 
    on explicit keys in a way that is far more accurate than diff.  It can also
    compare just subsets of columns, and perform post-delta transforms to 
    populate fields with static values, values from other fields, variables
    from the command line, or incrementing sequence numbers.

    Examples:

       $ gristle_differ file0.dat file1.dat --key-cols '0, 2' --ignore_cols '19,22,33'

            - Sorts both files on columns 0 & 2
            - Dedupes both files on column 0
            - Compares all fields except fields 19,22, and 23
            - Automatically determines the csv dialect
            - Produces the following files:
               - file1.dat.insert
               - file1.dat.delete
               - file1.dat.same
               - file1.dat.chgnew
               - file1.dat.chgold

       $ gristle_differ file0.dat file1.dat --key-cols '0' --compare_cols '1,2,3,4,5,6,7' -d '|'

            - Sorts both files on columns 0 
            - Dedupes both files on column 0
            - Compares fields 1,2,3,4,5,6,7
            - Uses '|' as the field delimiter
            - Produces the same output file names as example 1.


       $ gristle_differ file0.dat file1.dat --config-fn ./foo.yml  \
                   --variables batchid:919 --variables pkid:82304

            - Produces the same output file names as example 1.
            - But in this case it gets the majority of its configuration items from
              the config file ('foo.yml').  This could include key columns, comparison
              columns, ignore columns, post-delta transformations, and other information.
	    - The two variables options are used to pass in user-defined variables that
              can be referenced by the post-delta transformations.  The batchid will get
              copied into a batch_id column for every file, and the pkid is a sequence
              that will get incremented and used for new rows in the insert, delete and
              chgnew files.


# gristle_metadata
    Gristle_metadata provides a command-line interface to the metadata database.
    It's mostly useful for scripts, but also useful for occasional direct
    command-line access to the metadata.

    Examples:
       $ gristle_metadata --table schema --action list
                    Prints a list of all rows for the schema table.
       $ gristle_metadata --table element --action put --prompt
                    Allows the user to input a row into the element table and 
                    prompts the user for all fields necessary.
                           

# gristle_md_reporter
    Gristle_md_reporter allows the user to create data dictionary reports that
    combine information about the collection and fields along with field value
    descriptions and frequencies.

    Examples:
       $ gristle_md_reporter --report datadictionary --collection_id 2
                    Prints a data dictionary report of collection_id 2.
       $ gristle_md_reporter --report datadictionary --collection_name presidents
                    Prints a data dictionary report of the president collection.
       $ gristle_md_reporter --report datadictionary --collection_id 2 --field_id 3
                    Prints a data dictionary report of the president collection,
                    only shows field-level information for field_id 3.


# gristle_dir_merger
    Gristle_dir_merger consolidates directory structures of files.  Is both fast
    and flexible with a variety of options for choosing which file to use based
    on full (name and md5) and partial matches (name only) .

    Examples
       $ gristle_dir_merger /tmp/foo /data/foo
             - Compares source of /tmp/foo to dest of /data/foo.
             - Files will be consolidated into /data/foo, and deleted from /tmp/foo.
             - Comparison will be: match-on-name-and-md5 (default)
             - Full matches will use: keep_dest (default)
             - Partial matches will use: keep_newest (default)
             - Bottom line: this is what you normally want.
       $ gristle_dir_merger /tmp/foo /data/foo --dry-run
             - Same as the first example - except it only prints what it would do
               without actually doing it.
             - Bottom line: this is a good step to take prior to running it for real.
       $ gristle_dir_merger /tmp/foo /data/foo -r
             - Same as the first example - except it runs recursively through
               the directories.
       $ gristle_dir_merger /tmp/foo /data/foo --on-partial-match keep-biggest
             - Comparison will be: match-on-name-and-md5 (default)
             - Full matches will use: keep_dest (default)
             - Partial matches will use: keep_biggest (override)
             - Bottom line: this is a good combo if you know that some files
               have been modified on both source & dest, and newest isn't the best.
       $ gristle_dir_merger /tmp/foo /data/foo --match-on-name-only --on-full-match keep-source
             - Comparison will be: match-on-name-only (override)
             - Full matches will use: keep_source (override)
             - Bottom line: this is a good way to go if you have
               files that have changed in both directories, but always want to
               use the source files.


# Development & Testing

   * If you're going to test directly out of the source code then set up the
     pathing to point to the parent directory.  If using virtualenvwrapper
     then just run:
      * $ add2virtualenv .


# Licensing

   * Gristle uses the BSD license - see the separate LICENSE file for further 
     information


# Copyright

   * Copyright 2011,2012,2013,2014,2015,2017 Ken Farmer

