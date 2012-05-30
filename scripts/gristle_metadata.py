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
    funcs = {'schema'    : my_md.schema_tools    ,
             'element'   : my_md.element_tools   ,
             'collection': my_md.collection_tools,
             'field'     : my_md.field_tools     ,
             'instance'  : my_md.instance_tools  ,
             'analysis_profile'    :  my_md.analysis_profile_tools    ,
             'analysis'            :  my_md.analysis_tools            ,
             'collection_analysis' :  my_md.collection_analysis_tools ,
             'field_analysis'      :  my_md.field_analysis_tools      ,
             'field_analysis_value':  my_md.field_analysis_value_tools }
    actions = {'list'    : 'lister',
               'get'     : 'getter',
               'set'     : 'setter',
               'del'     : 'deleter'}

    # eliminate any Nones so they don't confuse _create_where
    # alternatively change _create_where so that it checks for None pk/uks
    for key in dargs.keys():
        if dargs[key] is None:
            dargs.pop(key)

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

    parser  = argparse.ArgumentParser(description=use, formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument('--table', '-t',
           choices=['schema', 'element', 'collection', 'field', 'instance',
                    'analysis_profile', 'analysis', 'collection_analysis', 'field_analysis', 'field_analysis_value'],
           required=True,
           help='table to perform action upon')
    parser.add_argument('--action', '-a',
           choices=['list', 'get', 'set','del'],
           required=True,
           help='action to perform upon table')


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
           choices=['string','int','date','time','timestamp'])
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
           choices=['string','int','date','time','timestamp'])
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
           choices=['determinator'],
           default='determinator')
    parser.add_argument('--analysis_timestamp'  ,
           help='generally set by tool')


    parser.add_argument('--ca_id'               , '--cai',
           type=int)
    parser.add_argument('--ca_name'             , '--can',
           default='unk')
    parser.add_argument('--ca_location'         , '--cal',
           default='unk')
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


    args = parser.parse_args()
    return args



if __name__ == '__main__':
    sys.exit(main())

