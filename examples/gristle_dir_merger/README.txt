Overview of these examples:
    - Since the gristle_dir_merger alters the dest_dir when it runs it's difficult to
      demonstrate examples of its usage.  So, we're running these with the --dry-run option
      and instead of comparing the resulting output directories we're comparing the resulting
      stdout logs of what it would do.

Example-01: Merge source_dir files into dest_dir by selecting all distinct files based 
      on filename, and the newest of any partial match files (when filename matches but 
      md5 hash is different)







