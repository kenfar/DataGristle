#!/usr/bin/env python
""" Used to hold all common  general-purpose functions and classes

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""
from __future__ import division

import sys
import argparse
import math
from os.path import isdir, isfile, exists
from os.path import join as pjoin


from gristle._version import __version__
import file_type



def isnumeric(number):
    """ Tests whether or not the input is numeric.
        Args:
           - number:  a string containing a number that may be either an integer
             or a float, a positive or a negative or zero.
        Returns:  True or False
    """
    try:
        float(number)
        return True
    except (TypeError, ValueError):
        return False


def get_common_key(count_dict):
    """  Provides the most common key in a dictionary as well as its frequency
         expressed as a percentage.  For example:
         cd = ['car':    7
               'boat':  30
               'truck':  8
               'plane':  5
         print most_common_key(cd)
         >>> boat, 60
    """
    sorted_keys  = (sorted(count_dict, key=count_dict.get))
    total_values = sum(count_dict.itervalues())
    most_common_key       = sorted_keys[-1]
    most_common_key_value = count_dict[sorted_keys[-1]]
    most_common_pct       = most_common_key_value / total_values 
    return most_common_key, most_common_pct



def coalesce(default, *args):
    """ Returns the first non-None value.
        If no non-None args exist, then return default.
    """
    for arg in args:
        if arg not in (None, "'None'", 'None'):
            return arg
    return default


def dict_coalesce(struct, key, default=None):
    try:
        return struct[key]
    except KeyError:
        return default


def ifprint(value, string, *args):
    if value is not None:
        print string % args


class ArgProcessor(object):
    def __init__(self, short_desc, long_desc):
        self.parser     = argparse.ArgumentParser(short_desc,
                              formatter_class=argparse.RawTextHelpFormatter)
        self.add_custom_args()
        self.add_standard_args()
        self.args       = self.parser.parse_args()

        if self.args.long_help:
            print long_desc
            sys.exit(0)

        #if self.args.files[0] == '-':  # stdin
        #    if not self.args.delimiter:
        #        self.parser.error('Please provide delimiter when piping data into program via stdin')

        self.custom_validation()


    def add_standard_args(self):
        """
        """
        self.parser.add_argument('--long-help',
                default=False,
                action='store_true',
                help='Print more verbose help')

        self.parser.add_argument('-V', '--Version',
                action='version',
                version='version: %s' % __version__)


    def add_option_csv_dialect(self):
        """
        """
        self.parser.add_argument('-d', '--delimiter',
                action=DelimiterAction,
                help=('Specify a quoted single-column field delimiter. This may be'
                      ' determined automatically by the program.'))
        self.parser.add_argument('--escapechar',
                default='"',
                help='Specify escaping character - generally only used for '
                     ' stdin data.  Default is "')
        self.parser.add_argument('--quoting',
                choices=('quote_all','quote_minimal','quite_nonnumeric','quote_none'),
                default='quote_none',
                help='Specify field quoting - generally only used for stdin data.'
                     '  The default: is quote_none.')
        self.parser.add_argument('--quotechar',
                default='"',
                help='Specify field quoting character - generally only used for '
                     'stdin data.  Default is double-quote')
        self.parser.add_argument('--recdelimiter',
                help='Specify a quoted end-of-record delimiter. ')
        self.parser.add_argument('--hasheader',
                dest='hasheader',
                default=None,
                action='store_true',
                help='Indicate that there is a header in the file.')
        self.parser.add_argument('--hasnoheader',
                dest='hasheader',
                default=None,
                action='store_false',
                help=('Indicate that there is no header in the file.'
                        'Occasionally helpful in overriding automatic '
                        'csv dialect guessing.'))

    def add_option_dry_run(self, help_msg=None):
        """
        """
        help_info = help_msg or 'Performs most processing except for final changes.'
        self.parser.add_argument('--dry-run',
                default=False,
                action='store_true',
                help=help_info)

    def add_option_stats(self, help_msg=None, default=True):
        """
        """
        help_info = help_msg or 'Writes detailed processing stats'
        self.parser.add_argument('--stats',
                dest='stats',
                action='store_true',
                help=help_info)

        help_info = help_msg or 'Turns off stats'
        self.parser.add_argument('--nostats',
                dest='stats',
                action='store_false',
                help=help_info)

    def add_option_config_name(self):
        """
        """
        help_info = 'Name of config within xdg dir (such as .confg/gristle_differ/* on linux)'
        self.parser.add_argument('--config-name',
                help=help_info)

    def add_option_config_fn(self):
        """
        """
        help_info = 'Name of config file.'
        self.parser.add_argument('--config-fn',
                help=help_info)

    def add_option_logging(self, help_msg=None):
        """
        """
        self.parser.add_argument('--log-level',
                            choices=['debug','info','warning','error', 'critical'],
                            help='Specify verbosity of logging')
        self.parser.add_argument('--console-log',
                            action='store_true',
                            default=True,
                            dest='log_to_console',
                            help='Turns on printing of logs to the console')
        self.parser.add_argument('--no-console-log',
                            action='store_false',
                            dest='log_to_console',
                            help='Turns off printing of logs to the console')


    def add_positional_file_args(self, stdin=True):
        """
        """
        if stdin is True:
            default=['-']
            help=('Specifies the input file(s).  The default is stdin.  Multiple '
                  'filenames can be provided.')
        else:
            default=None
            help='Specifies the input file(s). '
        print 'default: %s' % default
           
        self.parser.add_argument('files',
                                default=default,
                                nargs='*',
                                #type=argparse.FileType('r'),
                                help=help)

    def add_custom_args(self):
        """ Must be overriden by subclass with its argument additions.
        """
        raise NotImplementedError('Must be overriden by sub-classing script')

    def custom_validation(self):
        """ Intended to be overridden by subclass.
        """
        pass


class DelimiterAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        val = dialect_del_fixer(values)
        setattr(namespace, self.dest, val)


def dialect_del_fixer(values):
    if values == '\\t':
        val = '\t'
    elif values == 'tab':
        val = '\t'
    elif values == '\\n':
        val = '\n'
    else:
        val = values
    return val



def get_dialect(files, delimiter, quotename, quotechar, recdelimiter, hasheader):
    if files[0] != '-':
        for fn in files:
            assert isfile(fn)
            my_file   = file_type.FileTyper(fn ,
                            delimiter          ,
                            recdelimiter       ,
                            hasheader          ,
                            quoting=quotename  ,
                            quote_char=quotechar,
                            read_limit=5000    )
            try:
                my_file.analyze_file()
                dialect = my_file.dialect
                break
            except file_type.IOErrorEmptyFile:
                continue
            else:
                sys.exit(errno.ENODATA)
    else:
        # dialect parameters needed for stdin - since the normal code can't
        # analyze this data.
        dialect                = csv.Dialect
        dialect.delimiter      = delimiter
        dialect.quoting        = file_type.get_quote_number(quotename)
        dialect.quotechar      = quotechar
        dialect.lineterminator = '\n'                 # naive assumption
        dialect.hasheader      = hasheader

    return dialect






def abort(summary, details=None, rc=1):
    """ Creates formatted error message within a box of = characters
        then exits.
    """

    #---prints top line:
    print('=' * 79)

    #---prints message within = characters, assumes it is kinda short:
    print '=== ',
    print '%-69.69s' % summary,
    print(' ===')
    if 'logger' in vars() and logger:
        logger.critical(summary)

    #---prints exception msg, breaks it into multiple lines:
    if details:
        for i in range(int(math.ceil(len(details)/68))):
            print '=== ',
            print '%-69.69s' % details[i*68:(i*68)+68],
            print ' ==='
    if 'logger' in vars() and logger:
        logger.critical(details)

    #---prints bottom line:
    print('=' * 79)

    sys.exit(rc)
