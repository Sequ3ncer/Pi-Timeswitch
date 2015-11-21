#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as sql
import logging
import time
import os

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logging.getLogger(__name__).addHandler(NullHandler())
LOGGER = logging.getLogger(__name__)

### Helper methodes
## create db

def create_db(filename):
    '''Deletes the old database and creates all tables.'''

    if os.path.exists(filename):
        os.remove(filename)

    try:
        connection = sql.connect(filename)
        cur = connection.cursor()

        cur.execute('''CREATE TABLE Sequences(
            id INTEGER PRIMARY KEY,
            pin_id INTEGER,
            start_time TEXT,
            start_range TEXT,
            end_time TEXT,
            end_range TEXT,
            FOREIGN KEY(pin_id) REFERENCES Pins(id) ON UPDATE CASCADE)''')

        cur.execute('''CREATE TABLE Pins(
            id INTEGER PRIMARY KEY,
            name TEXT)''')

        connection.close()

    except sql.Error, e:
        raise

## validate data

def is_absolute_time(check_time):
    try:
        time.strptime(check_time, '%H:%M')
        return True
    except ValueError:
        return False

def is_relative_time(check_time):
    try:
        as_int = int(check_time)
        return 0 <= as_int and as_int <= 1440
    except ValueError:
        return False

def get_sequences_from_rows(rows):
    sequences = []
    for (sequence_id, pin_id, start_time, start_range, end_time, end_range) in rows:
        sequences.append(Sequence(start_time, start_range, end_time,
                                  end_range, sequence_id=sequence_id))

    return sequences

### MODEL ###

class PiSwitchModel(object):
    '''This class saves and loads pins and schedules.'''

    def __init__(self, filename):
        self.sql_file = filename


    def get_sequences(self):
        '''Returns all schedules in the dataset.'''
        sequences = []
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute("SELECT * FROM Sequences")

            rows = cur.fetchall()

            for (sequence_id, pin_id, start_time,
                 start_range, end_time, end_range) in rows:
                sequences.append(Sequence(start_time, start_range, end_time,
                                          end_range, sequence_id=sequence_id))

            return sequences

    def get_sequence(self, sequence_id):
        '''Returns all schedules in the dataset.'''

        LOGGER.info("get_sequence({0})".format(sequence_id))

        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''SELECT * FROM Sequences
                        WHERE id=?''', (sequence_id,))

            row = cur.fetchone()
            if row is None:
                return None
            else:
                return Sequence(**row)

    def set_sequence(self, sequence):
        '''Adds the given sequence to the dataset.\
           Removes the old schedule if it exists.'''
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            if sequence.get_id() == -1:
                LOGGER.info("set_sequence({0}) - adding new sequence"\
                    .format(sequence.get_id()))
                vals = (sequence.get_pin().get_id(), sequence.get_start()[0],
                        sequence.get_start()[1], sequence.get_end()[0],
                        sequence.get_end()[1])

                cur.execute('''INSERT INTO
                            Sequences(pin_id, start_time, start_range,\
                            end_time, end_range)
                            VALUES (?, ?, ?, ?, ?)''', vals)
            else:
                LOGGER.info("set_sequence({0}) - updating sequence"\
                    .format(sequence.get_id()))
                vals = (sequence.sequence_id, sequence.get_pin().get_id(),
                        sequence.get_start()[0], sequence.get_start()[1],
                        sequence.get_end()[0], sequence.get_end()[1])
                cur.execute('''REPLACE INTO
                            Sequences(id, pin_id, start_time, start_range,\
                            end_time, end_range)
                            VALUES (?, ?, ?, ?, ?, ?)''', vals)


    def delete_sequence(self, sequence_id):
        '''Deletes the sequences with the given id.'''
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''DELETE FROM Sequences
                        WHERE id=?''', (sequence_id,))

    def get_sequences_for_pin(self, pin_id):
        '''Returns all sequences for the pin.'''
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''SELECT * FROM Sequences
                WHERE pin_id=?''', (str(pin_id),))

            rows = cur.fetchall()

            return get_sequences_from_rows(rows)

    def delete_sequences_for_pin(self, pin_id):
        '''Deletes all sequences for the pin.'''
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''DELETE FROM Sequences
                WHERE pin_id=?''', (str(pin_id),))

            rows = cur.fetchall()

            return get_sequences_from_rows(rows)

    def get_pins(self):
        '''Returns all pins.'''
        pins = []
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''SELECT * FROM Pins''')

            rows = cur.fetchall()

            for row in rows:
                sequences = self.get_sequences_for_pin(row[0])
                pins.append(Pin(row[0], sequences, row[1]))

            return pins

    def get_pin(self, pin_id):
        '''Returns the pin with the given id.'''
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''SELECT * FROM Pins
                WHERE id=?''', (str(pin_id),))

            row = cur.fetchone()
            if row is None:
                return None

            sequences = self.get_sequences_for_pin(pin_id)
            rawPin = row
            return Pin(rawPin[0], sequences, rawPin[1])

    def delete_pin(self, pin_id):
        '''Deletes all sequence for the pin and the pin it selfs.'''
        self.delete_sequences_for_pin(pin_id)

        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''DELETE FROM Pins WHERE id=?''',
                        (str(pin_id),))


    def set_pin(self, pin):
        '''Alters the pin name or adds the pin if he
        did not exist. Also adds sequences.'''
        with sql.connect(self.sql_file) as connection:
            cur = connection.cursor()
            cur.execute('''REPLACE INTO Pins(id, name)
                        VALUES (?, ?)''',
                        (pin.get_id(), pin.get_name()))

            if pin.get_sequences() is not None:
                for sequence in pin.get_sequences():
                    self.set_sequence(sequence)

##### data access classes #####

class Sequence(object):
    def __init__(self, start_time, start_range, end_time,
                 end_range, pin=None, sequence_id=-1):
        self.pin = pin
        self.id = sequence_id

        self.start_time = start_time
        self.start_range = start_range
        self.end_time = end_time
        self.end_range = end_range

    def get_pin(self):
        return self.pin

    def set_pin(self, pin):
        self.pin = pin
        if (self.pin):
            self.pin_id = pin.get_id()

    def get_id(self):
        return self.id

    def set_id(self, sequence_id):
        self.id = sequence_id

    def get_start(self):
        return (self.start_time, self.start_range)

    def set_start(self, start_time, start_range):
        self.start_time, self.start_range = start_time, start_range

    def get_end(self):
        return (self.end_time, self.end_range)

    def set_end(self, end_time, end_range):
        self.end_time, self.end_range = end_time, end_range

class Pin(object):

    def __init__(self, pin_num, sequences=None, name=None, state=0):
        ''' State = 0 -> Undef | 1 -> ON | -1 -> OFF

        '''
        self.pin_num = pin_num
        self.sequences = sequences if sequences else []
        for sequence in self.sequences:
            sequence.set_pin(self)

        self.state = state
        self.id = pin_num
        if name is None:
            self.name = "Pin {0}".format(pin_num)
        else:
            self.name = name

    def get_sequences(self):
        return self.sequences

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name

    def get_state(self):
        return self.state

    def set_state(self, new_state):
        if (new_state in [-1, 0, 1]):
            self.state = new_state
        else:
            raise ValueError("Pin state must be in [-1,0,1]")

    def get_id(self):
        return self.pin_num

    def set_id(self, pin_id):
        self.pin_num = pin_id
