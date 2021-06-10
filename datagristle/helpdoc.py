#!/usr/bin/env python
""" Manages help info

    See the file "LICENSE" for the full license governing this code.
    Copyright 2021 Ken Farmer
"""


HELP_SECTION = """Help Options:
   -h, --help           Show help message and exit.
   --long-help          Show verbose help and exit.
   -V, --version        Show version info and exit.
   --verbosity VERBOSITY
                        Controls level of detail.  Valid values include: quiet, normal, high, debug."""


CSV_SECTION = """CSV Dialect Options:    These options are useful in explicitely-defining your csv dialect, in
                        overriding the dialect auto-detect, or in overriding any config file or
                        environmental variables you may have defined.
   -d, --delimiter DELIMITER
                        Provide a quoted single-character field delimiter.
                        Used when dialect auto-detect fails or when processing data via stdin.
   -q, --quoting QUOTETYPE
                        Specify quoting behavior.
                        Used when dialect auto-detect fails or when processing data via stdin.
                        Valid values include: quote_none, quote_minimal, quote_nonnumeric, quote_all.
   --quotechar CHAR     Defines the quoting character.
                        This can be any single-character value, but defaults to '"'.
   --doublequote        Causes an adjacent preceding quote to escape the following quote.
                        Provides a way of ignoring quotes within quoted strings.
   --no-doublequote     Turns off doublequoting.
   --escapechar CHAR    Causes the following character to be escaped.
                        Provides a way of ignoring quotes within quoted strings, or delimiters
                        within unquoted strings.
   --has-header         Indicates there is a header in the file.
   --has-no-header      Indicates there is no header in the file.
                        Useful for overriding dialect auto-detect behavior.
   --skipinitialspace   Ignore space after a delimiter and before a quoted string.
   --no-skipinitialspace
                        Ignore space after a delimiter and before a quoted string. """


CONFIG_SECTION = """Config File Options:
   --config-fn CONFIG_FN
                        Specifies a configuration file.
   --gen-config CONFIG_FN
                        Generates a configuration file from options.  """


def expand_long_help(val):
    return  val.replace('{see: helpdoc.CSV_SECTION}', CSV_SECTION).\
                replace('{see: helpdoc.CONFIG_SECTION}', CONFIG_SECTION).\
                replace('{see: helpdoc.HELP_SECTION}', HELP_SECTION)


def get_short_help_from_long(val):
    """ Extracts 100% of the help - except for the details section within
        option descriptions.

        Rules:
        1. Sections of options are defined by having the string "Options: " within the first
           thirty characters of the line.  The section ends with a blank line.
        2. Options within a section are defined by starting with a dash
        3. Short description of options are defined by being the first sentence after the option.
           They must end in a period.  They cannot span lines.  And they must exist.
        4. Long descriptions of options are defined by being any sentence after the
           first sentence of the option, on a separate line from the short description, and
           continue until another option is encountered or the section ends.  Long descriptions
           are removed.
        5. These long-descriptions are the only item that should be removed.
    """
    results = []

    option_section = False
    notes_section = False
    example_section = False
    notes_section = False
    short_desc_found = False

    for line in val.split('\n'):

        # First lets figure out what part of the help we're in:
        if line.strip() == '':
            option_section = False
            example_section = False
            notes_section = False
            licensing_section = False
            option = False
            short_desc_found = False
        elif line.strip().startswith('Examples:'):
            example_section = True
        elif line.strip().startswith('Notes:'):
            notes_section = True
        elif line.strip().startswith('Licensing'):
            licensing_section = True
        elif 'Options:' in line[:30]:
            option_section = True
        elif option_section == True and line.strip().startswith('-'):
            option = True
            short_desc_found = False

        # Now we can determine if we can skip some details:
        if example_section:
            continue
        elif notes_section:
            continue
        elif licensing_section:
            continue
        elif option:
            if short_desc_found:
                continue  # must be in the details
            else:
                temp_line = line.replace('...', '   ') # need to ignore ellipses
                if '.' in temp_line:
                    short_desc_found = True
                else:
                    pass # no desc on this line, need to try the next

        results.append(line)
    return '\n'.join(results)
