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
