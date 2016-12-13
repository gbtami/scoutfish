#!/usr/bin/env python

import json
import os
import pexpect
from pexpect.popen_spawn import PopenSpawn


class Scoutfish:
    def __init__(self, engine=''):
        if not engine:
            engine = './scoutfish'
        self.p = PopenSpawn(engine, encoding="utf-8")
        self.wait_ready()
        self.pgn = ''
        self.db = ''

    def wait_ready(self):
        self.p.sendline('isready')
        self.p.expect(u'readyok')

    def open(self, pgn, force=False):
        '''Open a PGN file and create an index if not exsisting or if force
           is set.'''
        if not os.path.isfile(pgn):
            raise NameError("File {} does not exsist".format(pgn))
        if self.pgn:
            self.close()
        self.pgn = pgn
        self.db = os.path.splitext(pgn)[0] + '.scout'
        if not os.path.isfile(self.db) or force:
            self.db = self.make(pgn)

    def close(self):
        '''Terminate scoutfish. Not really needed: engine will terminate as
           soon as pipe is closed, i.e. when we exit.'''
        self.p.sendline('quit')
        self.p.expect(pexpect.EOF)
        self.pgn = ''
        self.db = ''

    def make(self, pgn):
        '''Make an index out of a pgn file. Normally called by open()'''
        self.p.sendline('make ' + pgn)
        self.wait_ready()
        db = self.p.before.split('DB file:')[1]
        return db.split()[0]

    def setoption(self, name, value):
        '''Set an option value, like threads number'''
        self.p.sendline('setoption name ' + name + ' value ' + str(value))
        self.wait_ready()

    def scout(self, q):
        '''Run query defined by 'q' dict. Result will be a dict too'''
        if not self.db:
            raise NameError("Unknown DB, first open a PGN file")
        j = json.dumps(q)
        cmd = 'scout ' + self.db + ' ' + j
        self.p.sendline(cmd)
        self.wait_ready()
        result = json.loads(self.p.before)
        self.p.before = ''
        return result

    def get_games(self, list):
        '''Retrieve the PGN games specified in the offsets list. Games are
           added to each list entry with a new "pgn" key'''
        if not self.pgn:
            raise NameError("Unknown DB, first open a PGN file")
        with open(self.pgn, "r") as f:
            for match in list:
                f.seek(match['ofs'])
                game = ''
                for line in f:
                    if "[Event" in line and game.strip():
                        break  # Start of next game
                    game += line
                match['pgn'] = game.strip()
        return list