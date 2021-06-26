Overview of these examples:
    - Since the gristle_dir_merger alters the source and dest_dir when it runs it's difficult to
      demonstrate examples of its usage:
        - *__dest directory has the pre-merge contents
        - *__source directory also has the pre-merge contents
        - *__dest_results contains the post-merge version of *__dest
    - If you would like to run gristle_dir_merger on these directories there are two options:
        - set dry-result to true in the config and determine impacts from the log output
        - juggle copies of the directories around


Example-01: Merge source_dir files into dest_dir by selecting all distinct files based 
      on filename, and the newest of any partial match files (when filename matches but 
      md5 hash is different)
    - This example is not set up for automated testing since it uses the newest option, which
      requires more set-up work since the file modification times don't survive going through
      github.  But it still demonstrates what the operation looks like - the *dest and *source
      files are the before images and the *dest_results is what happens when it runs.

Example-02: Merge nested directories.  Source files on full matches will be deleted, and
      the biggest of any partial match (on md5) will be kept.

