
# v0.1.7 - 2020-07
   * Improvement: now supports python versions 3.7 and 3.8
   * BREAKING CHANGE: dropped support for python version 3.6
   * Bumped versions on dependent modules to eliminate vulnerabilities
   * gristle_differ
     - BREAKING CHANGE: col_names renamed to col-names for consistency
     - Fixes --already-unix option bug with file parsing
     - Fixes --stats bug with empty files
     - Improvement: added ability to use column names from file headers
     - Improvement: if a key-col is in the ignore-cols - it will simply be ignored, 
       and the program will continue processing.
     - Improvement: if a key-col is in the compare-cols - it will simply be ignored, 
       and the program will continue processing.
     - Improvement: if neither compare or ignore cols are provided it will use all cols 
       as compare-cols and continue processing.
     - Improvement: CLI help is updated to provide more details and accurate examples of these options.

# v0.1.6 - 2019-02
   * upgraded to support python3.7

# v0.1.5 - 2018-05
   * fixed setup.py bug in which pip10 no longer includes req module

# v0.1.4 - 2017-12
   * fixed gristle_validator bug in which checks on dg_maximum were not being run

# v0.1.3 - 2017-08
   * additional improvements to code quality, but with some breaking changes
   * changed argument handling for multiple utilities to simplify code and get more consistency.
     - affects: gristle_freaker, gristle_slicer, and gristle_viewer
     - This means words are separated by hyphens, not underscores.  --sortorder is --sort-order.
   * changed file handling for multiple utilities to simplify code and get more consistency.
     - affects: gristle_freaker, gristle_slicer, gristle_validator, and gristle_viewer
     - This means that behavior in handling multiple files, piped input, and other edge cases
       is more consistent between utilities.


# v0.1.2 - 2017-06
   * long-overdue code quality updates

# v0.1.1 - 2017-05
   * upgraded to use python3.6
   * changed versioning format, which has broken pypy for history

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
