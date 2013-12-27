#!/usr/bin/env python
"""
    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011,2012,2013 Ken Farmer
"""

import sys
import os
import tempfile
import pytest

from sqlalchemy import create_engine, MetaData, exc
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint, CheckConstraint

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gristle.simplesql   as simplesql

#---------------------------------------------------------
# test classes included here:
#   Test_schema
#   Test_struct_type
#   Test_struct
#   Test_element
#   Test_reports
#---------------------------------------------------------


class TestSurrogateKeyTable(object):

    def setup_method(self, method):
        self.tempdir       = tempfile.mkdtemp()

        self.fqdb_name     = os.path.join(self.tempdir, 'metadata.db')
        self.db            = create_engine('sqlite:////%s' % self.fqdb_name,
                                           logging_name='/tmp/gristle_sql.log')
        self.db.echo       = False
        self.conn          = self.db.connect()   # only needed by some statements
        self.metadata      = MetaData(self.db)
        self.person_tools  = PersonTools(self.metadata, self.db)
        self.person        = self.person_tools.table_create()
        self.metadata.create_all()

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_setter_and_lister_happypath(self):
        self.person_tools.setter(person_name='bob', person_desc='personal desc')
        self.person_tools.setter(person_name='joe', person_desc='personal desc')
        self.person_tools.setter(person_name='jim', person_desc='good bowler')
        people = self.person_tools.lister()
        assert len(people) == 3
        for person in people:
            assert len(person) == 3
            assert person.id > 0
            assert person.id < 4
            assert person.person_name in ['joe','bob','jim']
            assert person.person_name in ['joe','bob','jim']

    def test_setter_null_constraint_violation(self):
        # is missing mandatory column 'person_desc'
        # pylint: disable=E1101
        with pytest.raises(exc.IntegrityError):
             self.person_tools.setter(person_name='bob')
        # pylint: enable=E1101

    def test_updating_without_id(self):
        assert len(self.person_tools.lister()) == 0
        self.person_tools.setter(person_name='bob', person_desc='should result in insert')
        assert len(self.person_tools.lister()) == 1
        self.person_tools.setter(person_name='bob', person_desc='should result in update')
        assert len(self.person_tools.lister()) == 1
        for person in self.person_tools.lister():
            assert person.person_desc == 'should result in update'

    def test_updating_with_id(self):
        assert len(self.person_tools.lister()) == 0
        self.person_tools.setter(person_name='bob', person_desc='should result in insert')
        assert len(self.person_tools.lister()) == 1
        self.person_tools.setter(id=1, person_desc='still just update')
        assert len(self.person_tools.lister()) == 1
        for person in self.person_tools.lister():
            assert person.person_name == 'bob'
            assert person.person_desc == 'still just update'

    def test_get_unique_constraints(self):
        constraints = self.person_tools._get_unique_constraints()
        assert len(constraints) == 1
        assert constraints[0] == 'person_name'

    def test_get_id(self):
        self.person_tools.setter(person_name='bob', person_desc='personal desc')
        self.person_tools.setter(person_name='joe', person_desc='personal desc')
        self.person_tools.setter(person_name='jim', person_desc='good bowler')
        assert len(self.person_tools.lister()) == 3

        assert self.person_tools.get_id(person_name='bob') == 1
        assert self.person_tools.get_id(person_name='joe') == 2
        assert self.person_tools.get_id(person_name='jim') == 3

    def test_getter(self):
        self.person_tools.setter(person_name='bob', person_desc='personal desc')
        self.person_tools.setter(person_name='joe', person_desc='personal desc')
        self.person_tools.setter(person_name='jim', person_desc='good bowler')
        assert len(self.person_tools.lister()) == 3
        assert self.person_tools.getter(id=1).person_name == 'bob'
        assert self.person_tools.getter(person_name='joe').id == 2
        # pylint: disable=E1101
        with pytest.raises(KeyError):
            self.person_tools.getter(person_desc='good bowler')
        # pylint: enable=E1101

    def test_deleter(self):
        # deleter should always return 0 or 1 - will not raise exception
        # if keys are wrong.
        self.person_tools.setter(person_name='bob', person_desc='good sleeper')
        self.person_tools.setter(person_name='joe', person_desc='good dribbler')
        self.person_tools.setter(person_name='jim', person_desc='good catcher')
        assert len(self.person_tools.lister()) == 3
        assert self.person_tools.deleter(person_name='jim') == 1
        assert self.person_tools.deleter(person_name='maximillion') == 0
        assert self.person_tools.deleter(pet_desc='good bowler') == 0
        assert self.person_tools.deleter(person_desc='good sleeper') == 0
        assert self.person_tools.deleter(id=1) == 1




class TestNaturalKeyTable(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()

        self.fqdb_name     = os.path.join(self.tempdir, 'metadata.db')
        self.db            = create_engine('sqlite:////%s' % self.fqdb_name,
                                           logging_name='/tmp/gristle_sql.log')
        self.db.echo       = False
        self.conn          = self.db.connect()   # only needed by some statements
        self.metadata      = MetaData(self.db)
        self.pet_tools     = PetTools(self.metadata, self.db)
        self.pet           = self.pet_tools.table_create()
        self.metadata.create_all()

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_setter_and_lister_happypath(self):
        self.pet_tools.setter(pet_name='fido', pet_desc='sleeper')
        self.pet_tools.setter(pet_name='ralf', pet_desc='dribbler')
        self.pet_tools.setter(pet_name='gina', pet_desc='catcher')
        pets = self.pet_tools.lister()
        assert len(pets) == 3
        for pet in pets:
            assert len(pet) == 2
            assert pet.pet_name in ['fido','ralf','gina']

    def test_updating_without_id(self):
        assert len(self.pet_tools.lister()) == 0
        self.pet_tools.setter(pet_name='gina', pet_desc='good catcher')
        assert len(self.pet_tools.lister()) == 1
        self.pet_tools.setter(pet_name='gina', pet_desc='very compulsive')
        assert len(self.pet_tools.lister()) == 1
        for pet in self.pet_tools.lister():
            assert pet.pet_desc == 'very compulsive'

    def test_updating_without_pk_or_uk(self):
        # pylint: disable=E1101
        with pytest.raises(KeyError):
           self.pet_tools.setter(pet_desc='very compulsive')
        # pylint: enable=E1101

    def test_get_unique_constraints(self):
        # there are no constraints - it should return an empty list
        constraints = self.pet_tools._get_unique_constraints()
        assert len(constraints) == 0

    def test_get_id(self):
        # there's no id - it should return None
        self.pet_tools.setter(pet_name='fido', pet_desc='foo')
        assert len(self.pet_tools.lister()) == 1
        assert self.pet_tools.get_id(pet_name='fido') is None

    def test_getter(self):
        self.pet_tools.setter(pet_name='fido', pet_desc='good sleeper')
        self.pet_tools.setter(pet_name='ralf', pet_desc='good dribbler')
        self.pet_tools.setter(pet_name='gina', pet_desc='good catcher')
        assert len(self.pet_tools.lister()) == 3
        assert self.pet_tools.getter(pet_name='ralf').pet_desc == 'good dribbler'
        # pylint: disable=E1101
        with pytest.raises(KeyError):
            self.pet_tools.getter(person_desc='good bowler')
        with pytest.raises(KeyError):
            self.pet_tools.getter(pet_desc='good bowler')
        with pytest.raises(KeyError):
            self.pet_tools.getter(id=1)
        # pylint: enable=E1101

    def test_deleter(self):
        # deleter should always return 0 or 1 - will not raise exception
        # if keys are wrong.
        self.pet_tools.setter(pet_name='fido', pet_desc='good sleeper')
        self.pet_tools.setter(pet_name='ralf', pet_desc='good dribbler')
        self.pet_tools.setter(pet_name='gina', pet_desc='good catcher')
        assert len(self.pet_tools.lister()) == 3
        assert self.pet_tools.deleter(pet_name='ralf') == 1
        assert self.pet_tools.deleter(pet_name='maximillion') == 0
        assert self.pet_tools.deleter(person_desc='good bowler') == 0
        assert self.pet_tools.deleter(pet_desc='good sleeper') == 0
        assert self.pet_tools.deleter(id=1) == 0



class TestSurrogateKeyCheckConstraintTable(object):

    def setup_method(self, method):
        self.tempdir = tempfile.mkdtemp()

        self.fqdb_name     = os.path.join(self.tempdir, 'metadata.db')
        self.db            = create_engine('sqlite:////%s' % self.fqdb_name,
                                           logging_name='/tmp/gristle_sql.log')
        self.db.echo                = False
        self.conn                   = self.db.connect()   # only needed by some statements
        self.metadata               = MetaData(self.db)
        self.animal_tools           = AnimalTools(self.metadata, self.db)
        self.animal                 = self.animal_tools.table_create()
        self.metadata.create_all()

    def teardown_method(self, method):
        os.remove(os.path.join(self.tempdir, 'metadata.db'))
        os.rmdir(self.tempdir)

    def test_setter_and_null_constraint(self):
        # constraint violation - not null on animal_age
        # pylint: disable=E1101
        with pytest.raises(exc.IntegrityError):
           self.animal_tools.setter(animal_name='dog', animal_desc='smelly')
        # pylint: enable=E1101

    def test_setter_and_check_constraint(self):
        # first confirm it works:
        assert self.animal_tools.setter(animal_name='cat',
                                        animal_desc='pees on carpet',
                                        animal_age=9) == 1

        # constraint violation - check on animal_age
        # pylint: disable=E1101
        with pytest.raises(exc.IntegrityError):
            self.animal_tools.setter(animal_name='dog', animal_desc='smelly', animal_age=999)
        # pylint: enable=E1101




class PersonTools(simplesql.TableTools):
    """ Uses a primary key on a surrogate key ('id') of the table,
        unique constraint is put on the actual natural key (person_name).
    """

    def table_create(self):
        self._table_name = 'person'
        self.person = Table(self._table_name    ,
                        self.metadata           ,
                        Column('id'             ,
                               Integer          ,
                               nullable=False   ,
                               primary_key=True),
                        Column('person_name'    ,
                               String(40)       ,
                               nullable=False)  ,
                        Column('person_desc'    ,
                               String(255)      ,
                               nullable=False)  ,
                        UniqueConstraint('person_name', name='person_uk1'))
        self._table      = self.person
        return self._table



class PetTools(simplesql.TableTools):
    """ Uses a primary key on the natural key of the table -
        no separate surrogate key.
    """

    def table_create(self):
        self._table_name = 'pet'
        self.pet = Table(self._table_name       ,
                        self.metadata           ,
                        Column('pet_name'       ,
                               String(40)       ,
                               nullable=False   ,
                               primary_key=True),
                        Column('pet_desc'       ,
                               String(255)      ,
                               nullable=False)  )
        self._table      = self.pet
        return self._table



class AnimalTools(simplesql.TableTools):
    """ Uses a primary key on the natural key of the table -
        no separate surrogate key.
    """

    def table_create(self):
        self._table_name = 'animal'
        self.animal = Table(self._table_name    ,
                        self.metadata           ,
                        Column('animal_name'    ,
                               String(40)       ,
                               nullable=False   ,
                               primary_key=True),
                        Column('animal_desc'    ,
                               String(255)      ,
                               nullable=False)  ,
                        Column('animal_age'     ,
                               Integer          ,
                               nullable=False  ),
                        CheckConstraint('animal_age < 100'))
        self._table  = self.animal

        return self._table





