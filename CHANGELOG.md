# v0.1.1 - 2017-05
   * upgraded to use python3.6

# v0.59 - 2016-11
   * gristle_differ
     - totally rewritten.  Can now handle very large files, perform post-transform
       transformations, handle more complex comparisons, and use column names rather 
       than just positions.
   * gristle_determinator
     - added read-limit argument.  This allows the tool to be easily run against a
       subset of a very large input file.
   * gristle_scalar
     - removed from toolkit.  There are better tools in other solutions can be used
       instead.  This tool may come back again later, but only if enormously rewritten.
   * gristle_filter
     - removed from toolkit.  There are better tools in other solutions can be used
       instead.  This tool may come back again later, but only if enormously rewritten.
   * minor:
     - gristle_md_reporter - slight formatting change: text descriptions of fields are
       now included, and column widths were tweaked.
     - all utilities - a substantial performance improvement for large files when 
       quoting information is not provided.

# v0.58 - 2014-08
   * gristle_dir_merger
     - initial addition to toolkit.  Merges directories of files using a variety
       of matching criteria and matching actions.   

# v0.57 - 2014-07
   * gristle_processor
     - initial addition to toolkit.  Provides ability to scan through directory
       structure recursively, and delete files that match config criteria.

# v0.56 - 2014-03

   * gristle_determinator
     - added hasnoheader arg
     - fixed problem printing top_values on empty file with header
   * gristle_validator
     - added hasnoheader arg
   * gristle_freaker
     - added hasnoheader arg

# v0.55 - 2014-02

   * gristle_determinator - fixed a few problems:
     - the 'Top Values not shown - all unique' message being truncated
     - floats not handled correctly for stddev & variance
     - quoted ints & floats not handled

# v0.54 - 2014-02

   * gristle_validator - major updates to allow validation of csv files based on
     the json schema standard, with help from the Validictory module.

# v0.53 - 2014-01

   * gristle_freaker - major updates to enable distributes on all columns to be
     automatically gathered through either (all or each) args.   'All' combines
     all columns into a single tuple prior to producing distribution.  'Each'
     creates a separate distribution for every column within the csv file.
   * travisci - added support and started using this testing service.
