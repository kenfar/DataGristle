#!/usr/bin/env python
""" Creates graphviz networkmap dot file from the first two columns of an input file.

    To do:
       - Replace internal terminology related to ips & users with something more
         generic.
       - Add user controls to affect graph type, colors, fonts, arrowheads, etc.
       - Add user controls to choose which columns to use for diagram.

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
import sys
import os
import optparse
import csv
import collections
import fileinput
import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')  # allows running out of project structure

import gristle.file_type           as file_type 


#from pprint import pprint as pp
#pp(sys.path)



def main():
    """ Gets args, analyzes input file for structure, reads one record at a time into 3 arrays:
          - ip        (which is column 0)
          - user      (which is column 1)
          - edge_list 
        Then prints out graphviz dot file to produce a network map from the above data.
    """
    field_0_freq = collections.defaultdict(int)
    field_1_freq = collections.defaultdict(int)
    edge_list   = []

    (opts, args) = get_opts_and_args()
    MyFile       = file_type.FileTyper(opts.filename, 
                                       opts.delimiter,
                                       opts.recdelimiter,
                                       opts.hasheader)

    if opts.delimiter and len(opts.delimiter) > 1:
        MyFile.delimiter    = opts.delimiter
        MyFile.recdelimiter = opts.recdelimiter
        MyFile.hasheader    = opts.hasheader
    else:
        MyFile.analyze_file()

    print 'graph networkmap {'

    rec_cnt = -1
    csvfile = open(MyFile.fqfn, "r")
    field_0_style="filled"
    field_0_color="red"
    field_1_style="filled"
    field_1_color="green"

    for fields in csv.reader(csvfile, MyFile.dialect):
        rec_cnt += 1
        if rec_cnt > 500:
           break

        ip   = '"%s"' % fields[0]     # 'ip' terminology is obsolete
        t    = fields[1].split("@")   # this transformation is obsolete!
        user = t[0]                   # 'user' terminology is obsolete
        field_0_freq[ip]   += 1
        field_1_freq[user] += 1
        edge_list.append([ip, user])

    for key in field_0_freq:
        put_item(key, field_0_style, field_0_color)
    for key in field_1_freq:
        put_item(key, field_1_style, field_1_color)
    for edge in edge_list:
        put_edge(edge[0], edge[1])

    print '}'

    csvfile.close()
    return 0     


def put_item(name, style, color):
    rec = '%(name)30s [style="%(style)s", color="%(color)s"] ;' % locals()
    print rec

def put_edge(name0, name1):
    rec = '%(name0)30s -- %(name1)30s ;' % locals()
    print rec



def get_opts_and_args():
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = ("%prog is used to create a graphviz dot notation file from an input file: \n"
          + "   %prog -v -f [file] -d [delimiter value] "
          + " --delimiter [value] --recdelimiter [value] --hasheader --help \n"
          + "   example:  %prog -f ../data/*tiny_a* ")

    parser = optparse.OptionParser(usage = use)

    parser.add_option('-f', '--file', dest='filename', help='input file')

    parser.add_option('-v', '--verbose',
                      action='store_true',
                      dest='verbose',
                      default=True,
                      help='provides more detail')

    parser.add_option('-d', '--delimiter',
                      help='specify a field delimiter - essential for multi-column delimiters.  Delimiter must be quoted.')

    parser.add_option('--recdelimiter',
                      help='specify an end-of-record delimiter.  The deimiter must be quoted.')

    parser.add_option('--hasheader',
                      default=False,
                      action='store_true',
                      help='indicates that there is a header in the file.  Essential for multi-column delimited files.')


    (opts, args) = parser.parse_args()

    # validate opts
    if opts.filename is None:
        parser.error("no filename was provided")
    elif not os.path.exists(opts.filename):
        parser.error("filename %s could not be accessed" % opts.filename)


    return opts, args



if __name__ == '__main__':
    sys.exit(main())

