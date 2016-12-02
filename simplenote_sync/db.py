"""
    Database functions/settings for snsync
"""
import os
import sys
import sqlite3
import json
# pylint: disable=W0702
# pylint: disable=C0301


db_version = int("1") # Increment this with DB/Schema updates.

class Database:
    """
        Main Database object
    """

    def __init__(self, config, logger):
        """"
            Initial Database Setup
        """

        filename = config.get_config('cfg_db_path')
        self.log = logger

        if not self.isSQLite3(filename):
            self.log.warning("404 DB not found: %s", filename)
            self.dbconn, self.db = self.connect(filename)
            self.createdb_schmea_1()
        else:
            self.dbconn, self.db = self.connect(filename)

            # Future proof, i.e. if the table structure changes.
            version = self.get_schema_version()
            if version == db_version:
                self.log.debug("File Version: %s  Our Version: %s", version, db_version)
            else:
                self.log.critical("Database Version/Schemea Mismatch! - File Version: %s  Our Version: %s", version, db_version)
                sys.exit(1)

    def isSQLite3(self, filename):
        """"
            Check if a file is an sqlite3 file.
            # http://stackoverflow.com/a/15355790
        """

        if not os.path.isfile(filename):
            return False
        if os.path.getsize(filename) < 100: # SQLite database file header is 100 bytes
            return False

        with open(filename, 'rb') as fd:
            header = fd.read(100)

        return header[:16] == b'SQLite format 3\x00'

    def connect(self, filename):
        """
            Connection Setup
        """
        self.log.debug("Connecting DB: %s", filename)
        conn = sqlite3.connect(filename)
        c = conn.cursor()
        return conn, c

    def commit(self):
        """
            Commit to DB
        """
        self.dbconn.commit()

    def disconnect(self):
        """
            Connection teardown
        """
        self.dbconn.commit()
        self.dbconn.close()
        self.log.debug("Disconnecting DB")

    def get_schema_version(self):
        """
            Get the Schema Version
            # http://stackoverflow.com/a/19332352
        """
        cursor = self.dbconn.execute('PRAGMA user_version')
        return cursor.fetchone()[0]

    def set_schema_version(self, version):
        """
            Set the Schema Version
        """
        self.dbconn.execute('PRAGMA user_version={:d}'.format(version))

    def createdb_schmea_1(self):
        """
            Create a DB (Schema Version 1)
        """
        self.log.info("Creating new version 1 database")
        version = int("1")

        try:
            self.dbconn.execute('CREATE TABLE simplenote (\
                key TEXT PRIMARY KEY,\
                createdate BLOB,\
                deleted TEXT,\
                minversion TEXT,\
                modifydate BLOB,\
                syncnum TEXT,\
                systemtags TEXT,\
                tags TEXT,\
                version TEXT\
                )')
            self.dbconn.execute('CREATE TABLE notefile (\
                key TEXT PRIMARY KEY,\
                createdate TEXT,\
                deleted TEXT,\
                modifydate TEXT,\
                filename TEXT\
                )')
            self.dbconn.execute('CREATE TABLE snsync (\
                name TEXT PRIMARY KEY,\
                value BLOB\
                )')
            self.set_schema_version(version)
        except sqlite3.OperationalError:
            self.log.error("Unabled to setup local database")
            self.log.debug("Exception: %s", sys.exc_info()[1])
            sys.exit(1)

    def find_sn_by_key(self, key):
        """
            Find a simple note by key
        """

        self.log.debug("Looking for SN: %s", key)

        try:
            self.db.execute('SELECT * FROM simplenote WHERE key=?', (key,))
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        try:
            key_row = self.db.fetchone()
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        if key_row == None:
            self.log.debug("404 Not Found: %s", key)
            return False
        else:
            note = {}
            note['key'] = key_row[0]
            note['createdate'] = key_row[1]
            note['deleted'] = key_row[2]
            note['minversion'] = key_row[3]
            note['modifydate'] = key_row[4]
            note['syncnum'] = key_row[5]
            note['systemtags'] = key_row[6]
            note['tags'] = key_row[7]
            note['version'] = key_row[8]
            self.log.debug("SIMPLENOTE: %s", note)
            return note

    def sn(self, note):
        """
            Insert a note to the DB from an existing Simplenote
            - or replace (for updates)
        """
        try:
            self.log.debug("Updating SN Database: %s", note)

            self.db.execute('INSERT OR REPLACE INTO Simplenote \
                (key, createdate, deleted, minversion, modifydate, syncnum, systemtags, tags, version) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (\
                note['key'],note['createdate'],note['deleted'],\
                note['minversion'],note['modifydate'],note['syncnum'],\
                json.dumps(note['systemtags']),json.dumps(note['tags']),note['version'],)\
                )
            return True
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

    def update_snsync(self, name, value):
        """
            Add or updated meta data in snsync table
        """
        try:
            self.log.debug("Updating %s -> %s", name, value)
            self.db.execute('INSERT OR REPLACE INTO snsync (name, value) VALUES (?,?)', \
                (name, value,))
            return True
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

    def get_snsync_meta(self, name):
        """
            Get snsync meta data
        """

        self.log.debug("Looking for Meta %s", name)

        try:
            self.db.execute('SELECT * FROM snsync WHERE name=?', (name,))
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        try:
            row = self.db.fetchone()
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        if row == None:
            self.log.debug("404 SN Not Found: %s", name)
            return False
        else:
            value = row[1]
            self.log.debug("Meta Value  %s", value)
            return value

    def nf(self, nf_meta):
        """
            Insert a note file meta to the local DB
        """
        try:
            self.log.debug("Updating Note File DB: %s", nf_meta)

            self.db.execute('INSERT OR REPLACE INTO notefile \
                (key, createdate, deleted, modifydate, filename) \
                VALUES (?, ?, ?, ?, ?)', (\
                nf_meta['key'],nf_meta['createdate'],nf_meta['deleted'],\
                nf_meta['modifydate'],nf_meta['filename'],)\
                )
            return True
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

    def del_nf(self, key):
        """
            Delete Notefile Meta - to "forget a file"
        """
        try:
            self.log.debug("Deleting NF Meta for : %s", key)
            self.db.execute("DELETE FROM notefile WHERE key=?", (key,))
            return True
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

    def find_nf_by_key(self, key):
        """
            Find a note file by key
        """

        self.log.debug("Looking for NF: %s", key)

        try:
            self.db.execute('SELECT * FROM notefile WHERE key=?', (key,))
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        try:
            key_row = self.db.fetchone()
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        if key_row == None:
            self.log.debug("404 NF Not Found: %s", key)
            return False
        else:
            note = {}
            note['key'] = key_row[0]
            note['createdate'] = key_row[1]
            note['deleted'] = key_row[2]
            note['modifydate'] = key_row[3]
            note['filename'] = key_row[4]
            self.log.debug("NOTEFILE: %s", note)
            return note

    def find_nf_by_name(self, filename):
        """
            Find a note file by name (filename)
        """

        self.log.debug("Looking for NF META: %s", filename)

        try:
            self.db.execute('SELECT * FROM notefile WHERE filename=?', (filename,))
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        try:
            key_row = self.db.fetchone()
        except sqlite3.OperationalError:
            self.log.debug("Exception: %s", sys.exc_info()[1])

        if key_row == None:
            self.log.debug("404 NF Meta Not Found: %s", filename)
            return False
        else:
            note = {}
            note['key'] = key_row[0]
            note['createdate'] = key_row[1]
            note['deleted'] = key_row[2]
            note['modifydate'] = key_row[3]
            note['filename'] = key_row[4]
            self.log.debug("NOTEFILE: %s", note)
            return note
