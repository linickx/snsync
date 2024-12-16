"""
    Note File (local file) functions/settings for snsync
"""
# pylint: disable=W0718
# pylint: disable=C0301

import sys
import os
import string
import hashlib
import time
import datetime


def file_birthtime(fstat_record):
    # Where fstat_record is result from os.stat()
    try:
        return fstat_record.st_birthtime
    except AttributeError:
        return fstat_record.st_ctime


class Note:
    """
        Main Note File (local file) object
    """

    def __init__(self, config, logger):
        """"
            Initial Notes Setup
        """

        self.log = logger
        self.config = config

        # create note dir if it does not exist - cfg_nt_path
        if not os.path.exists(self.config.get_config('cfg_nt_path')):
            try:
                os.mkdir(self.config.get_config('cfg_nt_path'))
                self.log.info("Creating directory %s", self.config.get_config('cfg_nt_path'))
            except Exception:
                self.log.critical("Error creating directory %s", self.config.get_config('cfg_nt_path'))
                self.log.debug("Exception: %s", sys.exc_info()[1])
                sys.exit(1)

        # Try to create Recycle Bin (Trash) - cfg_nt_trashpath
        if not os.path.exists(self.config.get_config('cfg_nt_path') + "/" + self.config.get_config('cfg_nt_trashpath')):
            try:
                os.mkdir(self.config.get_config('cfg_nt_path') + "/" + self.config.get_config('cfg_nt_trashpath'))
                self.log.info("Creating directory %s", self.config.get_config('cfg_nt_path') + "/" + self.config.get_config('cfg_nt_trashpath'))
            except Exception:
                self.log.critical("Error creating directory %s/%s", self.config.get_config('cfg_nt_path'), self.config.get_config('cfg_nt_trashpath'))
                self.log.debug("Exception: %s", sys.exc_info()[1])
                sys.exit(1)

    def write(self, note, filename, access_time):
        self.log.debug('Filename: %s ', filename)
        try:
            f = open(filename, 'w', encoding='utf-8')
            f.write(note['content'])
            f.close()
            self.log.info("Writing %s", filename)

            os.utime(filename, (access_time, float(note['modifydate'])))
            return filename
        except Exception:
            self.log.error("Error writing note id: %s, %r", note['key'], filename, exc_info=True)
            self.log.debug("Exception: %s", sys.exc_info()[1])
        return False

    def new(self, note):
        """
            Create a new note file, returns filename
        """
        path = self.config.get_config('cfg_nt_path')
        filename = self.get_filename(note['content'])
        access_time = time.time()
        filetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")

        if filename:
            if os.path.isfile(path + "/" + filename):
                filename = filetime + "_" + filename  # Don't blast over files with same name, i.e. same first line.

            result = self.write(note, path + "/" + filename, access_time)
            return result
        else:
            self.log.error("Error generating filename for note: %s", note['key'])

        return False

    def get_filename(self, content):
        """
            Generate Safe Filename from Note Content
        """
        note_data = str.splitlines(content)
        try:
            line_one = note_data[0]
        except Exception:
            self.log.info("Probable Empty note, no first line note content -> %s", str(content))
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

        self.log.debug("Line 0: %s", str(note_data[0]))

        if line_one in ("\n", "", " "):
            try:
                line_one = note_data[1]
            except Exception:
                self.log.info("Probable Empty note, no second line note content -> %s", str(content))
                self.log.debug("Exception: %s", sys.exc_info()[1])
                return False

            self.log.debug("Line 1: %s", str(note_data[1]))

        file_ext = self.config.get_config('cfg_nt_ext')
        filename_len = int(self.config.get_config('cfg_nt_filenamelen'))

        # http://stackoverflow.com/a/295146
        try:
            safechars = string.ascii_letters + string.digits + " -_."
            safename = ''.join(c for c in line_one if c in safechars)

            if len(safename) >= filename_len: # truncate long names
                safename = safename[:filename_len]

            if len(safename) == 0:
                self.log.error("Filename is empty!")
                return False

            self.log.debug("Make Safe In: %s Out: %s", line_one, safename)
            filename = safename.strip() + "." + file_ext
            return filename
        except Exception:
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

    def gen_meta(self, filename):
        """
            Generate notefile meta from filename - returns dict
        """
        nf_meta = {}
        nf_meta['filename'] = filename
        nf_meta['deleted'] = 0

        # http://stackoverflow.com/a/5297483
        nf_meta['key'] = hashlib.md5(str(filename).encode('utf-8')).hexdigest()
        self.log.debug("Note File Meta Key: %s", nf_meta['key'])

        path = self.config.get_config('cfg_nt_path')

        # WARNING THIS IS PLATFORM SPECIFIC
        nf_meta['createdate'] = file_birthtime(os.stat(path + "/" + filename))
        self.log.debug("Note File Meta Created: %s [%s]", nf_meta['createdate'], time.ctime(nf_meta['createdate']))

        nf_meta['modifydate'] = os.stat(path + "/" + filename).st_mtime
        self.log.debug("Note File Meta Modified: %s [%s]", nf_meta['modifydate'], time.ctime(nf_meta['modifydate']))

        return nf_meta

    def update(self, note, nf_meta):
        """
            Create a new note file, returns filename
        """
        path = self.config.get_config('cfg_nt_path')
        filename = str(nf_meta['filename'])
        access_time = time.time()

        result = self.write(note, path + "/" + filename, access_time)
        if result:
            return True
        return False

    def open(self, filename):
        """
            Open a notefile, returns Dict: content & modifydate
        """
        notefile = {}
        path = self.config.get_config('cfg_nt_path')

        if os.path.isfile(path + "/" + filename):
            try:
                f = open(path + "/" + filename, 'r', encoding='utf-8')
                notefile['content'] = f.read()
                f.close()
            except Exception:
                self.log.error("Failed to OPEN/READ: %s", path + "/" + filename)
                self.log.debug("Exception: %s", sys.exc_info()[1])
                return False
        else:
            self.log.error("Notefile not found: %s", path + "/" + filename)
            return False

        notefile['modifydate'] = os.stat(path + "/" + filename).st_mtime
        self.log.debug("Note File Modified: %s [%s]", notefile['modifydate'], time.ctime(notefile['modifydate']))

        notefile['createdate'] = file_birthtime(os.stat(path + "/" + filename))
        self.log.debug("Note File Created: %s [%s]", notefile['createdate'], time.ctime(notefile['createdate']))

        return notefile
