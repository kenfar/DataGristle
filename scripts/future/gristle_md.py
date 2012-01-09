#!/usr/bin/env python
""" Command line interface to metadata database.
    To do:
       - support schema
       - support struct type
       - support struct collection
       - support struct item

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""

#--- standard modules ------------------
from __future__ import division
import sys
import argparse
#from pprint import pprint as pp

#--- gristle modules -------------------
sys.path.append('../')     # allows running from project structure
sys.path.append('../../')  # allows running from project structure
sys.path.append('/home/kenfar/projects/datagristle/gristle')

import metadata2      as metadata
#import metadata               as metadata

#------------------------------------------------------------------------------
# Command-line section 
#------------------------------------------------------------------------------
def main():
    """ runs all processes:
            - gets opts & args
            - analyzes file to determine csv characteristics unless data is 
              provided via stdin
            - runs each input record through process_cols to get output
            - writes records
    """
    args = get_args()
    print args


    sys.exit(0)
    my_md = metadata.GristleMetaData()

    if args.table == 'schema':
        crud_schema(my_md, args)

    return 0


def crud_schema(my_md, args):

        if args.action == 'list':
            results = my_md.schema_list()
            if len(results) == 0:
                print('No schemas have been added yet')
            else:
                print '%-20.20s  | %-60.60s' % ('schema name', 'schema desc')
                print '%-20.20s  | %-60.60s' % ('--------------------','--------------------------------------------')
                for row in results:
                    print '%-20.20s  | %-60.60s' % (row[0], row[1])
        if args.action == 'get':
            arg_schema = raw_input('Schema Name: ')
            results = my_md.schema_get(arg_schema)
            if len(results) == 0:
                print('Schema %s not found' % arg_schema)
            else:
                print '%-20.20s  | %-60.60s' % ('schema name', 'schema desc')
                print '%-20.20s  | %-60.60s' % ('--------------------','--------------------------------------------')
                print '%-20.20s  | %-60.60s' % (results[0][0], results[0][1])
        elif args.action == 'put':
            arg_schema = raw_input('Schema Name: ')
            arg_desc   = raw_input('Schema Desc: ')
            my_md.schema_put(arg_schema, arg_desc)
        elif args.action == 'del':
            arg_schema = raw_input('Schema Name: ')
            my_md.schema_del(arg_schema)
            
            

def get_args():
    global parser
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """
    use = '''gristle_md.py is used to provide command-line CRUD interaction  \
       \n with the gristle metadata database.                                \
       \n                                                                    \
       \n gristle_md.py [table] [action] [misc options]                      \
       \n   where tables could be any of:  schema, struct_type, or struct    \
       \n     and actions could be any of: add, rename, update, delete, list.\
       \n                                                                    \
       '''

    parser = argparse.ArgumentParser(use, formatter_class=argparse.RawTextHelpFormatter)
    subcmd             = parser.add_subparsers(dest='subcmd_name')


    #----- schema stuff -------
    schema_subcmd      = subcmd.add_parser('schema')
    schema_subcmd.add_argument('action',
                  choices=['add','rename', 'update','delete','list'],
                  help='action to perform upon schema')
    schema_subcmd.add_argument('--schema_name', '--sn',
                  help='name of schema')
    schema_subcmd.add_argument('--schema_desc', '--sd',
                  help='description of schema')
    def arg_schema(args):
        if args.action == 'list':
            if args.schema_name:
                parser.error("Do not include a schema_name with the list command")
        if args.action == 'add':
            if not args.schema_name or not args.schema_desc:
                parser.error("Add action requires both schema_name and desc")
    schema_subcmd.set_defaults(func=arg_schema)


    #----- struct_type stuff -------
    struct_type_subcmd = subcmd.add_parser('struct_type')
    struct_type_subcmd.add_argument('action',
                       choices=['add','update','delete','list'])
    struct_type_subcmd.add_argument('--struct_type_name', '--stn')
    struct_type_subcmd.add_argument('--struct_type_desc', '--std')
    def arg_struct_type(args):
        if args.action == 'list':
            if args.struct_type_name:
                parser.error("Do not include a name with the list command")
        if args.action == 'add':
            if not args.struct_type_name or not args.struct_type_desc:
                parser.error("Add action requires both name and struct_desc")
    struct_type_subcmd.set_defaults(func=arg_struct_type)


    #----- struct stuff -------
    struct_subcmd = subcmd.add_parser('struct')
    struct_subcmd.add_argument('action',
                  choices=['add','update','delete','list'],
                  help='action to perform upon a struct')
    struct_subcmd.add_argument('--struct_name', '--sn')
    struct_subcmd.add_argument('--struct_desc', '--sd')
    def arg_struct(args):
        if args.action == 'list':
            if args.struct_name:
                parser.error("Do not include a struct_name with the list command")
        if args.action == 'add':
            if not args.struct_name or not args.struct_desc:
                parser.error("Add action requires both struct_name and struct_desc")
    struct_subcmd.set_defaults(func=arg_struct)


    args = schema_subcmd.parse_args()
    #args = parser.parse_args()
    args.func(args)
    return args



if __name__ == '__main__':
    sys.exit(main())

