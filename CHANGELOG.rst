v0.59 - 2015-01
===============

-  gristle\_differ

   -  totally rewritten. Can now handle very large files, perform
      post-transform transformations, handle more complex comparisons,
      and use column names rather than just positions.

-  gristle\_determinator

   -  added read-limit argument. This allows the tool to be easily run
      against a subset of a very large input file.

-  gristle\_scalar

   -  removed from toolkit. There are better tools in other solutions
      can be used instead. This tool may come back again later, but only
      if enormously rewritten.

-  gristle\_filter

   -  removed from toolkit. There are better tools in other solutions
      can be used instead. This tool may come back again later, but only
      if enormously rewritten.

-  minor:

   -  gristle\_md\_reporter - slight formatting change: text
      descriptions of fields are now included, and column widths were
      tweaked.
   -  all utilities - a substantial performance improvement for large
      files when quoting information is not provided.

v0.58 - 2014-08
===============

-  gristle\_dir\_merger

   -  initial addition to toolkit. Merges directories of files using a
      variety of matching criteria and matching actions.

v0.57 - 2014-07
===============

-  gristle\_processor

   -  initial addition to toolkit. Provides ability to scan through
      directory structure recursively, and delete files that match
      config criteria.

v0.56 - 2014-03
===============

-  gristle\_determinator

   -  added hasnoheader arg
   -  fixed problem printing top\_values on empty file with header

-  gristle\_validator

   -  added hasnoheader arg

-  gristle\_freaker

   -  added hasnoheader arg

v0.55 - 2014-02
===============

-  gristle\_determinator - fixed a few problems:

   -  the 'Top Values not shown - all unique' message being truncated
   -  floats not handled correctly for stddev & variance
   -  quoted ints & floats not handled

v0.54 - 2014-02
===============

-  gristle\_validator - major updates to allow validation of csv files
   based on the json schema standard, with help from the Validictory
   module.

v0.53 - 2014-01
===============

-  gristle\_freaker - major updates to enable distributes on all columns
   to be automatically gathered through either (all or each) args. 'All'
   combines all columns into a single tuple prior to producing
   distribution. 'Each' creates a separate distribution for every column
   within the csv file.
-  travisci - added support and started using this testing service.
