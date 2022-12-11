#!/usr/bin/env python
""" Used to help interact with the csv module.

    See the file "LICENSE" for the full license governing this code.
    Copyright 2011-2022 Ken Farmer
"""

import copy
import csv
import fileinput
import os.path
from pprint import pprint as pp
from typing import Optional, Any, Union, Type
import _csv

from datagristle import common as comm

DEFAULT_DELIMITER = ','
DEFAULT_QUOTING = 'quote_none'
DEFAULT_QUOTECHAR = '"'
DEFAULT_ESCAPECHAR = None
DEFAULT_DOUBLEQUOTE = False
DEFAULT_HAS_HEADER = False
DEFAULT_SKIPINITIALSPACE = False
DEFAULT_LINETERMINATOR = '\n'




def get_quote_number(quote_name: Optional[str]) -> Optional[int]:
    """ used to help applications look up quote names typically provided by users.
        Inputs:
           - quote_name
        Outputs:
           - quote_number
    """
    assert type(quote_name) in (str, type(None))

    if quote_name is None:
        return None
    else:
        return csv.__dict__[quote_name.upper()]



def get_quote_name(quote_number: int) -> str:
    """ used to help applications look up quote names
    """
    assert quote_number is not None

    for key, value in csv.__dict__.items():
        if value == quote_number:
            return key
    else:
        raise ValueError('invalid quote_number: {}'.format(quote_number))



class Header:
    """ Manages csv header information to support the use of field names rather
        than field numbers in configs.
    """

    def __init__(self):
        self.raw_field_names = []
        self.raw_fields_by_position = {}
        self.raw_fields_by_name = {}

        self.field_names = []
        self.fields_by_position = {}
        self.fields_by_name = {}


    def load_from_file(self,
                       file_name: str,
                       dialect: 'Dialect') -> None:

        if file_name == '-':
            comm.abort(f'Invalid file_name for Header: {file_name}')

        reader = csv.reader(open(file_name, newline=''), dialect=dialect)
        for field_names in reader:
            break
        else:
            raise EOFError


        for field_sub, raw_field_name in enumerate(field_names):
            if dialect.has_header:
                field_name = self.format_raw_header_field_name(raw_field_name)
            else:
                raw_field_name = field_name = f'field_{field_sub}'

            field_name = self._make_field_name_unique(field_name, field_names)

            self.field_names.append(field_name)
            self.fields_by_position[field_sub] = field_name
            self.fields_by_name[field_name] = field_sub

            self.raw_field_names.append(raw_field_name)
            self.raw_fields_by_position[field_sub] = raw_field_name
            self.raw_fields_by_name[raw_field_name] = field_sub


    def load_from_list(self,
                       field_names: list[str]):


        for field_sub, raw_field_name in enumerate(field_names):
            field_name = self.format_raw_header_field_name(raw_field_name)

            field_name = self._make_field_name_unique(field_name, field_names)

            self.field_names.append(field_name)
            self.fields_by_position[field_sub] = field_name
            self.fields_by_name[field_name] = field_sub

            self.raw_field_names.append(raw_field_name)
            self.raw_fields_by_position[field_sub] = raw_field_name
            self.raw_fields_by_name[raw_field_name] = field_sub


    def _make_field_name_unique(self,
                                starting_field_name: str,
                                field_names: list[str]) -> str:
        temp_field_name = starting_field_name
        for count in range(999):
            if temp_field_name in self.field_names:
                temp_field_name = starting_field_name + f'__{count}'
            else:
                break
        else:
            comm.abort('Error: cannot create unique header field name - 999 attempts failed')
        return temp_field_name


    def format_raw_header_field_name(self,
                                     field_name:str) -> str:
        return field_name.strip().replace(' ', '_').lower()


    def load_from_files(self,
                        file_names: list[str],
                        dialect) -> None:
        for file_name in file_names:
            try:
                self.load_from_file(file_name, dialect)
                return
            except EOFError:
                pass
        raise EOFError


    def get_field_position(self,
                           field_name: str) -> int:
        return self.fields_by_name[field_name]


    def get_field_name(self,
                       field_position: int) -> str:
        return self.fields_by_position[field_position]


    def get_field_position_from_any(self,
                                    lookup: Union[str, int]) -> int:
        """ Returns a field position given either a field name or position
        """
        if comm.isnumeric(lookup):
             return int(lookup)
        else:
             return self.get_field_position(lookup)


    def get_field_positions_from_any(self,
                                    lookups: list[Union[str, int]]) -> list[int]:
        """ Returns a list of field positions given a list of positions or names
        """
        return [self.get_field_position_from_any(x) for x in lookups]


    def get_raw_field_name(self,
                           field_position):
        return self.raw_fields_by_position[field_position]


    def get_raw_field_position(self,
                               raw_field_name):
        return self.raw_fields_by_name[raw_field_name]



class Dialect(csv.Dialect):
    """ A simple Dialect class

    This dialect class includes has_header and minimal defaulting that make it work
    better for this application - where we want to pass around csv info, not define
    reusable dialects.
    """
    def __init__(self,
                 delimiter: str,
                 quoting: int,
                 quotechar: str,
                 doublequote: bool,
                 escapechar: Optional[str],
                 skipinitialspace: bool,
                 has_header: bool) -> None:

        self.delimiter = delimiter
        self.doublequote = doublequote
        self.escapechar = escapechar
        self.quotechar = quotechar
        self.quoting = quoting
        self.skipinitialspace = skipinitialspace
        self.lineterminator = DEFAULT_LINETERMINATOR
        self.has_header = has_header

        self.validate()


    def __str__(self):
        string = f'''Dialect({self.delimiter=},   \n
                             {self.quoting=},     \n
                             {self.quotechar=},   \n
                             {self.doublequote=}, \n
                             {self.escapechar=},  \n
                             {self.skipinitialspace=},  \n
                             {self.has_header=})'''
        return string


    def validate(self):
        if not self.delimiter:
            comm.abort('delimiter is invalid')

        if self.quoting not in [csv.QUOTE_NONE, csv.QUOTE_MINIMAL,
                               csv.QUOTE_ALL, csv.QUOTE_NONNUMERIC]:
            comm.abort(f'Dialect: quoting is invalid.  Value provided is: {self.quoting}')

        # Make sure we only have either doublequoting or escapechar turned on
        if self.doublequote and self.escapechar:
            comm.abort(f'Dialect: cannot have both doublequoting ({self.doublequote}) and escapechar ({self.escapechar}).')

        if self.quoting == csv.QUOTE_NONE and self.doublequote:
            comm.abort('Dialect: doublequote is incompatible with quote_none')


    def get_quote_name(self) -> str:
        """ used to help applications look up quote names
        """
        for key, value in csv.__dict__.items():
            if value == self.quoting:
                return key
        else:
            raise ValueError('invalid quote_number: {}'.format(self.quoting))



class BuildDialect(csv.Dialect):
    """ Builds a Dialect instance one step at a time

    """
    def __init__(self) -> None:
        self._step1: dict[str, Any] = {}
        self._step2: dict[str, Any] = {}
        self._step3: dict[str, Any] = {}
        self.final: dict[str, Any] = {}
        self.dialect: Dialect


    def step1_discover_dialect(self,
                         files: list[str]) -> None:
        if files[0] == '-':
            return

        for infile in files:
            try:
                if os.path.getsize(infile) > 0:
                    self._step1 = self._discover_from_file(infile, 
                                                          read_limit=5000)
                if self._step1:
                    break
            except _csv.Error as err:
                pass  # lets hope there's another file in the set that it can use


    def step2_override_dialect(self,
                         delimiter: Optional[str] = None,
                         has_header: Optional[bool] = None,
                         quoting: Optional[int] = None,
                         quotechar: Optional[str] = None,
                         doublequote: bool = True,
                         escapechar: Optional[str] = None,
                         skipinitialspace: Optional[bool] = None) -> None:
        # add verbosity?

        self._step2 = copy.deepcopy(self._step1)
        if delimiter:
            self._step2['delimiter'] = delimiter

        if doublequote:
            self._step2['doublequote'] = doublequote
            self._step2['escapechar'] = None

        if escapechar:
            self._step2['escapechar'] = escapechar
            self._step2['doublequote'] = False

        if quotechar:
            self._step2['quotechar'] = quotechar

        if quoting:
            if isinstance(quoting, int):
                self._step2['quoting'] = quoting
            else:
                self._step2['quoting'] = get_quote_number(quoting)

        if skipinitialspace is not None:
            self._step2['skipinitialspace'] = skipinitialspace

        if has_header is not None:
            self._step2['has_header'] = has_header



    def step3_default_dialect(self) -> None:
        # research: the configulator module hsa csv defaults, do those just get
        # blended in with the overrides?!?
        """ defaults the dialect with any non-None values from other args
        """
        if self._step2:
            self._step3 = copy.deepcopy(self._step2)
        else:
            self._step3 = copy.deepcopy(self._step1)

        if self._step3.get('delimiter') is None:
            self._step3['delimiter'] = DEFAULT_DELIMITER

        if self._step3.get('quoting') is None:
            self._step3['quoting'] = get_quote_number(DEFAULT_QUOTING)

        if self._step3.get('quotechar') is None:
            self._step3['quotechar'] = DEFAULT_QUOTECHAR

        if self._step3.get('has_header') is None:
            self._step3['has_header'] = DEFAULT_HAS_HEADER

        if self._step3.get('skipinitialspace') is None:
            self._step3['skipinitialspace'] = DEFAULT_SKIPINITIALSPACE

        if self._step3.get('doublequote') is None:
            self._step3['doublequote'] = DEFAULT_DOUBLEQUOTE

        if self._step3.get('escapechar') is None:
            self._step3['escapechar'] = DEFAULT_ESCAPECHAR


    def step4_finalize_dialect(self) -> None:

        self.final = copy.deepcopy(self._step3)

        assert isinstance(self.final['delimiter'], str)
        assert isinstance(self.final['quoting'], int)
        assert isinstance(self.final['quotechar'], str)
        assert isinstance(self.final['doublequote'], bool)
        assert isinstance(self.final['escapechar'], (str, type(None)))
        assert isinstance(self.final['skipinitialspace'], bool)
        assert isinstance(self.final['has_header'], bool)

        self.dialect = Dialect(delimiter=self.final['delimiter'],
                               quoting=self.final['quoting'],
                               quotechar=self.final['quotechar'],
                               doublequote=self.final['doublequote'],
                               escapechar=self.final['escapechar'],
                               skipinitialspace=self.final['skipinitialspace'],
                               has_header=self.final['has_header'])


    def simple_dialect(self, **kw) -> None:
        self.dialect = Dialect(**kw)


    def get_final_dialect(self):
        return self.dialect


    def _discover_from_file(self,
                           fqfn: str,
                           read_limit: int = 5000) -> dict[str, Any]:
        """ gets the dialect for a file
            Uses the csv.Sniffer class
            Then performs additional processing to try to improve accuracy of quoting.
        """
        # Verify we have an actual file - not an input stream:
        assert os.path.isfile(fqfn)

        discover_dict = {}
        with open(fqfn, newline='') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(read_limit))
            discover_dict = convert_dialect_to_dict(dialect)

        # See if we can improve quoting accuracy:
        discover_dict['quoting'] = self._get_dialect_quoting(dialect, fqfn)

        # Populate the escapechar attribute
        discover_dict['escapechar'] = self._get_dialect_escapechar(dialect)

        # Populate the has_header attribute:
        discover_dict['has_header'] = self._get_has_header(fqfn, read_limit)

        return discover_dict


    def _get_dialect_quoting(self,
                             dialect: type[_csv.Dialect],
                             fqfn: str) -> int:
        """ Since Sniffer tends to default to QUOTE_MINIMAL we're going to try to
            get a more accurate guess.  In the event that there's an extremely
            consistent set of data that is either all quoted or not quoted at
            all we will return that appropriate value.
        """

        # total_field_cnt has a key for each number of fields found in a
        # record, and a value that indicates how often this total was found
        #total_field_cnt  = collections.defaultdict(int)
        total_field_cnt: dict[Any, Union[int, float]] = {}

        # quoted_field_cnt has a key for each number of quoted fields found
        # in a record, and a value that indicates how often this total was
        # found.
        #quoted_field_cnt = collections.defaultdict(int)
        quoted_field_cnt: dict[Any, Union[int, float]] = {}

        for rec in fileinput.input(fqfn):
            fields = rec[:-1].split(dialect.delimiter)
            try:
                total_field_cnt[len(fields)] += 1
            except KeyError:
                total_field_cnt[len(fields)] = 1

            quoted_cnt = 0
            for field in fields:
                if len(field) >= 2:
                    if field[0] == '"' and field[-1] == '"':
                        quoted_cnt += 1
            try:
                quoted_field_cnt[quoted_cnt] += 1
            except KeyError:
                quoted_field_cnt[quoted_cnt] = 1

            if fileinput.lineno() > 1000:
                break
        fileinput.close()

        # "Exact" scenario: simplest and most clear in which we have no confusing
        # data, every record has the same number of fields and either all are quoted
        # or none are.  This is handled specially since it's often screwed up
        # by the Sniffer, and it's a common situation.
        if len(total_field_cnt) == 1 and len(quoted_field_cnt) == 1:
            if list(total_field_cnt.keys())[0] == list(quoted_field_cnt.keys())[0]:
                return csv.QUOTE_ALL
            elif list(quoted_field_cnt.values())[0] == 0:
                return csv.QUOTE_NONE

        # "Almost Exact" scenario: almost the same as with the exact scenario
        # above, but in this case it allows for a few malformed records.
        # The numbers must be nearly identical - with both the most common field
        # count and most common quoted field count occuring 95% of the time.
        common_field_cnt, common_field_pct = comm.get_common_key(total_field_cnt)
        common_quoted_field_cnt, common_quoted_field_pct = comm.get_common_key(quoted_field_cnt)

        if common_field_pct > .95 and common_quoted_field_pct > .95:
            if common_field_cnt == common_quoted_field_cnt:
                return csv.QUOTE_ALL
            elif common_quoted_field_cnt == 0:
                return csv.QUOTE_NONE

        # Final scenario - we can't make much of an improvement, it's probably
        # either QUOTED_MINIMAL or QUOTED_NONNUMERIC.  Sniffer probably labeled
        # it QUOTED_MINIMAL.
        return dialect.quoting


    def _get_dialect_escapechar(self,
                                dialect: type[_csv.Dialect]):
        """ Populate the escapechar on a dialog if it is missing
        """
        if dialect.doublequote is True:
            return None
        elif 'escapechar' not in dialect.__dict__:
            return None
        else:
            return dialect.escapechar


    def _get_has_header(self,
                        fqfn: str,
                        read_limit: int = 50000) -> bool:
        """ Figure out whether or not there's a header based on the first 50,000 bytes
            Raises:
                - csv.Snipper() can throw exceptions if it can't interpret file
        """
        sample = open(fqfn, 'r').read(read_limit)
        return csv.Sniffer().has_header(sample)



    def get_quote_name(self) -> str:
        """ used to help applications look up quote names
        """
        for key, value in csv.__dict__.items():
            if value == self.quoting:
                return key
        else:
            raise ValueError('invalid quote_number: {}'.format(self.quoting))



def convert_dialect_to_dict(in_dialect: Type[_csv.Dialect]) -> dict:
    out: dict[str, Any] = {}
    out['delimiter'] = in_dialect.delimiter
    out['quoting'] = get_quote_name(in_dialect.quoting)
    out['quotechar'] = in_dialect.quotechar
    out['doublequote'] = in_dialect.doublequote
    out['escapechar'] = in_dialect.escapechar
    out['skipinitialspace'] = in_dialect.skipinitialspace
    return out



def is_valid_dialect(dialect) -> bool:
    # note that we're not checking escapechar for None - since that's valid.
    if (dialect.delimiter is None
            or dialect.quoting is None
            or dialect.quotechar is None
            or dialect.has_header is None
            or dialect.doublequote is None):
        return False
    if dialect.quoting not in (None, csv.QUOTE_NONE, csv.QUOTE_ALL,
                               csv.QUOTE_NONNUMERIC, csv.QUOTE_MINIMAL):
        return False
    return True



def print_dialect(dialect, name) -> None:

    print(f'{name} Dialect: ')
    print(f'    delimiter:              {dialect.delimiter}')
    print(f'    quoting:                {dialect.quoting}')
    print(f'    quoting (translated):   {dialect.get_quote_name()}')
    print(f'    has_header:             {dialect.has_header}')
    print(f'    doublequote:            {dialect.doublequote}')
    print(f'    escapechar:             {dialect.escapechar}')



