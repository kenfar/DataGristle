#!/usr/bin/env python
""" Command line interface to metadata database.

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
sys.path.append('../gristle')  # allows running from project structure

import metadata               as metadata

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
    args         = get_args()
    dargs        = vars(args)
    my_md        = metadata.GristleMetaData()

    #crud_schema(my_md, args)
    #func = getattr(my_md, '%s_tools.lister' % args.table)
    #func = getattr(schema_tools, lister)

    #THE SOLUTION: 
    funcs = {'schema'              : my_md.schema_tools              ,
             'element'             : my_md.element_tools             ,
             'collection'          : my_md.collection_tools          ,
             'field'               : my_md.field_tools               ,
             'instance'            : my_md.instance_tools            ,
             'analysis_profile'    : my_md.analysis_profile_tools    ,
             'analysis'            : my_md.analysis_tools            ,
             'collection_analysis' : my_md.collection_analysis_tools ,
             'field_analysis'      : my_md.field_analysis_tools      ,
             'field_analysis_value': my_md.field_analysis_value_tools }
    actions = {'list'    : 'lister',
               'get'     : 'getter',
               'set'     : 'setter',
               'del'     : 'deleter'}

    # eliminate any Nones so they don't confuse _create_where
    # alternatively change _create_where so that it checks for None pk/uks
    for key in dargs.keys():
        if dargs[key] is None:
            dargs.pop(key)

    # get a pointer to the function (ie, my_md.element_tools.lister)
    function = getattr(funcs[args.table], actions[args.action])

    results = function(**dargs)
    if args.action == 'set':
        if int(results) == 0:
            print 'set updated prior values'
        else:
            print 'set inserted new values'
    elif args.action == 'del':
        if int(results) == 0:
            print 'delete failed'
        else:
            print 'delete succeeded'
    elif args.action == 'get':
        print results
    elif args.action == 'list':
        for row in results:
            print row


    #2 - WORKS:
    #results = getattr(schema_tools, 'lister')(**dargs)
    #print results
    #7 - WORKS:
    #funcs = {'schema': schema_tools.lister}
    #print funcs['schema'](**dargs)


    return 0



def get_args():
    global parser
    """ gets opts & args and returns them
        Input:
            - command line args & options
        Output:
            - opts dictionary
            - args dictionary 
    """

    use = ''' \n\
       \n  gristle_metadata.py is used to provide command-line CRUD interaction with the gristle metadata database.                                \
       \n                                                                    \
       \n gristle_metadata.py [table] [action] [misc options]                \
       \n   where tables could be any of [schema, struct_type, or struct]    \
       \n     and actions could be any of [add, rename, update, delete, list]. \
       \n     ...                                                            \
       \n                                                                    \
       '''


    table_choices=['schema', 'element', 'collection', 'field', 'instance',
                   'analysis_profile', 'analysis', 'collection_analysis', 
                   'field_analysis', 'field_analysis_value']
    action_choices=['list', 'get', 'set','del']
    type_choices=['string','int','date','time','timestamp','float']

    parser  = argparse.ArgumentParser(description=use, 
                                      formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument('--table', '-t',
           choices=table_choices,
           required=True,
           help='table to perform action upon')
    parser.add_argument('--action', '-a',
           choices=action_choices,
           required=True,
           help='action to perform upon table')
    parser.add_argument('--prompt', '-p',
           action='store_true',
           default=False,
           help='causes program to prompt for each field')


    parser.add_argument('--schema_id'   , '--si',
           help='id of schema')
    parser.add_argument('--schema_name' , '--sn',
           help='name of schema')
    parser.add_argument('--schema_desc' , '--sd',
           help='description of schema')


    parser.add_argument('--element_name', '--en')
    parser.add_argument('--element_desc', '--ed')
    parser.add_argument('--element_type', '--et',
           help='element type',
           choices=type_choices)
    parser.add_argument('--element_len' , '--el',
           help='element length',
           type=int)


    parser.add_argument('--collection_id'  , '--ci',
           type=int)
    parser.add_argument('--collection_name', '--cn')
    parser.add_argument('--collection_desc', '--cd')


    parser.add_argument('--field_id'       , '--fi')
    parser.add_argument('--field_name'     , '--fn')
    parser.add_argument('--field_desc'     , '--fd')
    parser.add_argument('--field_type'     , '--ft',
           choices=type_choices)
    parser.add_argument('--field_len'      , '--fl',
           type=int)
    parser.add_argument('--field_order'    , '--fo',
           type=int)


    parser.add_argument('--instance_id'       , '--ii',
           type=int)
    parser.add_argument('--instance_name'     , '--in')
    parser.add_argument('--instance_location' , '--il')


    parser.add_argument('--analysis_profile_id'    , '--api',
           type=int)
    parser.add_argument('--analysis_profile_name'  , '--apn')


    parser.add_argument('--analysis_id'         , '--ai',
           type=int)
    parser.add_argument('--analysis_tool'       , '--at',
           choices=['determinator'])
    parser.add_argument('--analysis_timestamp'  ,
           help='generally set by tool')


    parser.add_argument('--ca_id'               , '--cai',
           type=int)
    parser.add_argument('--ca_name'             , '--can')
    parser.add_argument('--ca_location'         , '--cal')
    parser.add_argument('--ca_rowcount'         , '--car',
           type=int)


    parser.add_argument('--fa_id'               , '--fai',
           type=int)
    parser.add_argument('--fa_case'             , '--fac')


    parser.add_argument('--fav_id'              , '--favi',
           type=int)
    parser.add_argument('--fav_value'           , '--favv')
    parser.add_argument('--fav_count'           , '--favc',
           type=int)

    # removed defaults because it messed with lister() function in main 
    # needs unused columns to have values of None
    #       default='determinator')  - from analysis_tool
    #       default='unk')  - from ca_name
    #       default='unk')  - from ca_location

    args = parser.parse_args()

    if args.prompt:
        if args.action != 'list':
            args = prompt_user(args)

    return args


def prompt_user(args):
    """ Inputs:
          - args - the parsed argument dictionary
        Outputs:
          - args - the parsed argument dictionary with additions
        This function prompts the user for appropriate args - based on the
        table they selected.  It can simplify use of the program for users
        uncertain of exactly which fields they need to provide.
    """

    # consider prompter()
    #    make get_args a class
    #    make this one of the methods

    if  args.table == 'schema':
        args.schema_id   = raw_input('schema_id [%s]:   ' % args.schema_id)
        args.schema_name = raw_input('schema_name [%s]: ' % args.schema_name)
        args.schema_desc = raw_input('schema_desc [%s]: ' % args.schema_desc)
    elif args.table == 'collection':
        args.collection_id     = raw_input('collection_id [%s]:   ' % args.collection_id)
        args.collection_name   = raw_input('collection_name [%s]: ' % args.collection_name)
        args.collection_desc   = raw_input('collection_desc [%s]: ' % args.collection_desc)
    elif args.table == 'field':
        args.field_id     = raw_input('field_id    [%s]: ' % args.field_id)
        args.field_name   = raw_input('field_name  [%s]: ' % args.field_name)
        args.field_desc   = raw_input('field_desc  [%s]: ' % args.field_desc)
        args.field_type   = raw_input('field_type  [%s]: ' % args.field_type)
        args.field_len    = raw_input('field_len   [%s]: ' % args.field_len)
        args.field_order  = raw_input('field_order [%s]: ' % args.field_order)
    elif args.table == 'element':
        args.element_name     = raw_input('element_name     [%s]: ' % args.element_name)
        args.element_desc     = raw_input('element_desc     [%s]: ' % args.element_desc)
        args.element_type     = raw_input('element_type     [%s]: ' % args.element_type)
        args.element_len     = raw_input('element_len     [%s]: ' % args.element_len)
    elif args.table == 'instance':
        args.instance_id       = raw_input('instance_id       [%s]: ' % args.instance_id)
        args.instance_name     = raw_input('instance_name     [%s]: ' % args.instance_name)
        args.instance_location = raw_input('instance_location [%s]: ' % args.instance_location)
    elif args.table == 'analysis_profile':
        args.analysis_profile_id   = raw_input('analysis_profile_id   [%s]: ' % args.analysis_profile_id)
        args.analysis_profile_name = raw_input('analysis_profile_name [%s]: ' % args.analysis_profile_name)
    elif args.table == 'analysis':
        args.analysis_id        = raw_input('analysis_id   [%s]: ' % args.analysis_id)
        args.analysis_tool      = raw_input('analysis_tool [%s]: ' % args.analysis_tool)
        args.analysis_timestamp = raw_input('analysis_timestamp [%s]: ' % args.analysis_timestamp)
    elif args.table == 'collection_analysis':
        args.ca_id        = raw_input('ca_id       [%s]: ' % args.ca_id)
        args.ca_name      = raw_input('ca_name     [%s]: ' % args.ca_name)
        args.ca_location  = raw_input('ca_location [%s]: ' % args.ca_location)
        args.ca_rowcount  = raw_input('ca_rowcount [%s]: ' % args.ca_rowcount)
    elif args.table == 'field_analysis':
        args.fa_id        = raw_input('fa_id       [%s]: ' % args.fa_id)
        args.fa_case      = raw_input('fa_case     [%s]: ' % args.fa_case)
    elif args.table == 'field_analysis_value':
        args.fav_id        = raw_input('fav_id       [%s]: ' % args.fav_id)
        args.fav_value     = raw_input('fav_value    [%s]: ' % args.fav_value)
        args.fav_count     = raw_input('fav_count    [%s]: ' % args.fav_count)

    return args


if __name__ == '__main__':
    sys.exit(main())

