#!/usr/bin/env python3
# coding=utf-8
# I like catch-all excepts
# pylint: disable=W0702
# Widescreen baby!
# pylint: disable=C0301
# No idea why pylint import fails.
# pylint: disable=F0401

"""

    Like rsync for Simplenote.
        Sync simple notes to local text files

    .. currentmodule:: snsync
    .. moduleauthor:: Nick Bettison - www.linickx.com

    # Logic
    1. Get list of notes from Simplenote (LOOP1)
    2. Add new Simplenotes to local SN DB (cache) and create txt file (with meta DB).
    3. Existing notes: Compare & update based on modifieddate (update contents & modifieddate)
    4. Deleted on SN (move local files to trash)
    5. Deleted locally (mark deleted/trashed on SN)
    6. Add new local note (file) to Simple Note (LOOP2)

    --
    IDEAS:
        - Markdown - use Simplenote markdown tag to create .md files
        - delta (fast) sync - use the last sync time to limit the processing (sn_last_sync)
        - check file permissions of config file
        - Merge (difflib) conflicts instead of creating files (maybe?)
        - garbage collection - empty trash folder (every x days?)
        - external [web?] hook - create customisable notification of status
    BUGS:
        - pylint
            - R0912 Too many branches / R0914 Too many local vars - Both: Line 82
            - R01101 Too many nested blocks (line 216)
            - W0612 Unused Var (lastsync) - See ^ideas^ this is for delta/fast sync.
            - W0612 Unused Var (args) - RTFM: I'm sure I did this for a reason :-/
    --

"""

import time
import datetime
import logging
import os
import sys
import re
import getopt

from .simplenote import Simplenote
from .config import Config
from .db import Database
from .notes import Note
from .version import __version__


start_time = time.monotonic() # Simple Performance Monitoring

logger = logging.getLogger("snsync")
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# Log to console until file is setup.
chandler = logging.StreamHandler()
chandler.setFormatter(log_formatter)
chandler.setLevel(logging.DEBUG)
logger.addHandler(chandler)

def usage():
    """
        Print Help / Usage
    """
    print('''
Usage: snsync [OPTIONS]

OPTIONS:
 -h, --help         Help!
 -d, --dry-run      Dry Run Mode (no changes made/saved)
 -s, --silent       Silent Mode (no std output)
 -c, --config=      Config file to read (default: ~/.snsync)

Version: %s
''' % __version__)
    sys.exit(0)

def main(argv=sys.argv[1:]):
    """
        Main body, system argements, 2 loops.
    """

    # Default Vars
    dry_run = False
    silent_mode = False
    config_file = None

    # CMD Line options
    try:
        opts, args = getopt.getopt(argv,
                                   'hdsc:',
                                   ['help', 'dry-run', 'silent', 'config='])
    except:
        logger.debug("Exception: %s", sys.exc_info()[1])
        usage()

    for opt, arg in opts:
        if opt in ['-h', '--help']:
            usage()
        elif opt in ['-d', '--dry-run']:
            dry_run = True
        elif opt in ['-s', '--silent']:
            silent_mode = True
        elif opt in ['-c', '--config']:
            config_file = arg
        else:
            print('ERROR: Unhandled option')
            usage()

    config = Config(config_file) # Config Setup

    note = Note(config, logger) # Local Notes Setup (folders)

    log_file = config.get_config('cfg_log_path')
    log_level = config.get_config('cfg_log_level')

    # https://docs.python.org/2.6/library/logging.html
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    if log_file == "DISABLED":
        logger.info("Console Errors Enabled")
        silent_mode = True # Disable other output (progress bar)
    else: # logfile is ready
        if not silent_mode:
            print("Logging to File: %s" % log_file)
        fhandler = logging.FileHandler(log_file)
        fhandler.setFormatter(log_formatter)
        level = LEVELS.get(log_level, logging.INFO)
        fhandler.setLevel(level)
        logger.addHandler(fhandler) # add file handler
        logger.removeHandler(chandler) # remove console handler
        logger.info('--[ START Version %s ]--', __version__) # Begining of log file

    # Catch missing configs
    if config_file is not None:
        if not os.path.isfile(config_file):
            logger.critical("Config file not found: %s", config_file)
            if not silent_mode:
                print('Config file not found: %s' % config_file)
            sys.exit(1)

    db = Database(config, logger) # DB setup

    # System Vars
    filetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S") # timestamp for files
    the_os = sys.platform

    # Uer config vars (DO NOT CHANGE THESE)
    path = config.get_config('cfg_nt_path')
    trash_path = config.get_config('cfg_nt_trashpath')
    file_ext = config.get_config('cfg_nt_ext')
    sn_username = config.get_config('sn_username')
    sn_password = config.get_config('sn_password')

    # Catch blank credentials
    if sn_username == '' or sn_password == '':
        logger.critical("Simplenote Username/Password not set, probably no ~/.snsync config file.")
        if not silent_mode:
            print('Simplenote Username/Password not set, probably no ~/.snsync config file.')
        sys.exit(1)

    # Main simplenote object
    simplenote = Simplenote(sn_username, sn_password)

    if re.match('linux', the_os):
        logger.debug('OS: Linux')
    elif re.match('darwin', the_os):
        logger.debug('OS: MacOS')
    else:
        logger.warning('Unsupported OS')

    if dry_run:
        logger.warning('DRY RUN Mode')

    try:
        notes = simplenote.get_note_list() # the mac daddy important bit!
    except:
        logger.debug("Exception: %s", sys.exc_info()[1])
        logger.critical("Simplenote Login Failed")
        if not silent_mode:
            print('Simplenote Login Failed')
        sys.exit(1)

    logger.debug('API Result: %s', notes)

    if notes[1] == 0:  # success
        notes = notes[0]
    else:
        logger.error('Simplenote LIST Request FAILED')
        sys.exit()

    # Counters!
    counter_changes = 0
    counter_modified = 0
    counter_added = 0
    counter_deleted = 0
    counter_http_errors = 0

    if not silent_mode:
        print("Scanning %s Simplenotes" % len(notes))

        # Progress bar
        sys.stdout.write("[%s]" % (" " * len(notes)))
        sys.stdout.flush()
        sys.stdout.write("\b" * (len(notes)+1)) # return to start of line, after '['

    # Loop 1
    for n in notes:

        db.commit() # Commit the last note

        if not silent_mode:
            time.sleep(0.05) # print doesn't work if too fast
            sys.stdout.write("#")
            sys.stdout.flush()

        thisnote = db.find_sn_by_key(n['key'])

        if thisnote:
            # Existig Simple Note
            thisfile = db.find_nf_by_key(n['key']) # Note File Meta
            sn_modify = False # Set default status for simplenote
            nf_modify = False # Set default status for notefile

            if thisfile and n['deleted'] == 0: # Modified S-Notes
                if os.path.isfile(path + "/" + thisfile['filename']):
                    file_modifydate = os.path.getmtime(path + "/" + thisfile['filename'])

                    sn_modifyseconds = str(n['modifydate']).split(".")[0] # Simple Note Modify Time
                    logger.debug('SN Modified: %s [%s]', sn_modifyseconds, time.ctime(int(sn_modifyseconds)))

                    sncache_modifyseconds = str(thisnote['modifydate']).split(".")[0] # Last known Simple Note Time
                    logger.debug('SN (cached) Modified: %s [%s]', sncache_modifyseconds, time.ctime(int(sncache_modifyseconds)))

                    nf_modifyseconds = str(file_modifydate).split(".")[0] # Note File modify Time
                    logger.debug('NF Modified: %s [%s]', nf_modifyseconds, time.ctime(int(nf_modifyseconds)))

                    if int(sn_modifyseconds) > int(sncache_modifyseconds):
                        sn_modify = True
                        logger.debug('SN %s is newer than NF %s', n['key'], thisfile['filename'])

                    if int(nf_modifyseconds) > int(sn_modifyseconds):
                        nf_modify = True
                        logger.debug('NF %s is newer than SN %s', thisfile['filename'], n['key'])

                    if nf_modify and sn_modify:
                        logger.error('DUP! Modified Date Clash %s', thisfile['filename'])

                        old_fqdn = path + "/" + thisfile['filename']
                        new_fqdn = path + "/DUP_" + filetime + "_" + thisfile['filename']
                        logger.info('Duplicate File Created %s', new_fqdn)

                        nf_modify = False # Reset this, gonna move the old file

                        logger.debug("DUP | Old: %s New: %s", old_fqdn, new_fqdn)
                        if not dry_run:
                            try:
                                os.rename(old_fqdn, new_fqdn)
                            except:
                                logger.error("Failed to move file  %s -> %s", old_fqdn, new_fqdn)
                                logger.debug("Exception: %s", sys.exc_info()[1])

                    if not nf_modify and not sn_modify:
                        logger.debug('No changes required for %s [%s]', thisfile['filename'], n['key'])

                    if sn_modify:
                        logger.info('[SN] > [NF] | %s -> %s', n['key'], thisfile['filename'])
                        nf_filename = thisfile['filename']

                    if nf_modify:
                        logger.info('[SN] < [NF] | %s <- %s', n['key'], thisfile['filename'])
                        nf_filename = thisfile['filename']

                else:
                    logger.critical("Local File [%s] DELETED but not marked for deletion locally, assuming delete SN -> [%s]", thisfile['filename'], n['key'])
                    counter_deleted += 1

                    if not dry_run:
                        trash_note = simplenote.trash_note(n['key'])
                        logger.debug('API Result: %s', trash_note)

                        if trash_note[1] == 0:
                            db.sn(trash_note[0])
                            db.del_nf(n['key'])
                            logger.info('SN Deleted [%s]', n['key'])
                        else:
                            logger.error('Simplenote DELETE Request Failed [%s]', n['key'])
                            counter_http_errors += 1
                            counter_deleted -= 1 # giveth and taketh away!

            elif thisfile and n['deleted'] == 1: #  Seen and Deleted SN
                if os.path.isfile(path + "/" + thisfile['filename']):
                    logger.info('Deleting File: %s', thisfile['filename'])
                    counter_deleted += 1

                    if not dry_run:
                        del thisfile['deleted'] # Remove old deleted meta
                        thisfile['deleted'] = 1
                        db.del_nf(n['key']) # delete nofile meta (forget the file)
                        db.sn(n) # update simplenote cache

                        old_fqdn = path + "/" + thisfile['filename']
                        new_fqdn = path + "/" + trash_path + "/" + filetime + "_" + thisfile['filename']

                        try:
                            os.rename(old_fqdn, new_fqdn)
                            logger.debug("TRASH | Old: %s New: %s", old_fqdn, new_fqdn)
                        except:
                            logger.error("Failed to move file  %s -> %s", old_fqdn, new_fqdn)
                            logger.debug("Exception: %s", sys.exc_info()[1])

            else: # No file meta
                if n['deleted'] == 0: # Exists in Simple note, but no meta
                    logger.critical("File Meta AWOL - %s", n['key'])
                    sn_modify = True # Generate new local file
                else: # No Meta and Deleted in Simple Note
                    logger.debug("No file meta for deleted file simplenote, probably never written to disk")

            if sn_modify: # Simplenote has been modified!
                counter_modified += 1
                if not dry_run:
                    thisnote_full = simplenote.get_note(n['key']) # Get the latest note
                    logger.debug('API Result: %s', thisnote_full)

                    if thisnote_full[1] == 0:
                        try:
                            nf_filename
                        except: # Catch critial AWOL Files
                            nf_filename = note.get_filename(thisnote_full[0]['content'])

                        # Generate new notefile meta
                        nf_meta = {}
                        nf_meta['filename'] = nf_filename
                        nf_meta['key'] = n['key']
                        nf_meta['createdate'] = n['createdate']
                        nf_meta['modifydate'] = n['modifydate']
                        nf_meta['deleted'] = n['deleted']

                        db.sn(n) # Update simplenote Cache
                        db.nf(nf_meta) # Update notefile meta

                        thisnote_file = note.update(thisnote_full[0], nf_meta) # Write to file
                    else:
                        logger.error('Simplenote DOWNLOAD Request FAILED [%s]', n['key'])
                        counter_http_errors += 1
                        counter_modified -= 1 # so far yet so close ;)

            if nf_modify: # Local note has been modified!
                counter_modified += 1
                if not dry_run:
                    notefile_full = note.open(nf_filename)

                    nf = {}
                    nf['key'] = n['key']
                    nf['content'] = notefile_full['content']
                    nf['modifydate'] = notefile_full['modifydate']
                    nf['version'] = n['version']

                    note_update = simplenote.update_note(nf)
                    logger.debug('API Result: %s', note_update)

                    if note_update[1] == 0:
                        nf_meta = {} # update meta
                        nf_meta['filename'] = nf_filename
                        nf_meta['key'] = note_update[0]['key']
                        nf_meta['createdate'] = note_update[0]['createdate']
                        nf_meta['modifydate'] = note_update[0]['modifydate']
                        nf_meta['deleted'] = note_update[0]['deleted']

                        db.sn(note_update[0])
                        db.nf(nf_meta)

                        logger.info('SN Updated [%s] from %s', n['key'], nf_filename)
                    else:
                        logger.error('Simplenote UPDATE Request FAILED [%s] <- %s', n['key'], nf_filename)
                        counter_http_errors += 1
                        counter_modified -= 1


        else:
            # New Note Added/Found in Simplenote
            logger.info('Adding SN NOTE: %s to Local DB', n['key'])
            counter_added += 1

            if dry_run:
                thisnote = False
            else:
                thisnote = db.sn(n)

            if thisnote:
                if n['deleted'] == 0: # Don't save deleted notes!
                    thisnote_full = simplenote.get_note(n['key'])
                    logger.debug('API Result: %s', thisnote_full)

                    if thisnote_full[1] == 0:  # success
                        thisnote_file = note.new(thisnote_full[0])

                        if thisnote_file:
                            nf_meta = {}
                            nf_meta['filename'] = thisnote_file
                            nf_meta['key'] = n['key']
                            nf_meta['createdate'] = n['createdate']
                            nf_meta['modifydate'] = n['modifydate']
                            nf_meta['deleted'] = n['deleted']
                            db.nf(nf_meta)
                        else:
                            logger.error("Failed to write note: %s", n['key'])

                    else:
                        logger.error('Simplenote DOWNLOAD Request FAILED [%s]', n['key'])
                        counter_http_errors += 1
                        counter_added -= 1

            else:
                if not dry_run:
                    logger.error('Failed to updated DB with %s', n['key'])

    if not silent_mode:
        sys.stdout.write("\n") # New Line for end of progress bar

    # Loop 2
    if not silent_mode:
        print("Scanning %s local files" % len(os.listdir(path)))
        # Progress bar
        sys.stdout.write("[%s]" % (" " * len(os.listdir(path))))
        sys.stdout.flush()
        sys.stdout.write("\b" * (len(os.listdir(path))+1)) # return to start of line, after '['

    for notefile in os.listdir(path): # local search for new files

        if not silent_mode:
            if not silent_mode:
                time.sleep(0.05) # print doesn't work if too fast
                sys.stdout.write("#")
                sys.stdout.flush()

        if notefile.endswith(file_ext): # only work with .txt file (or whatever!)
            logger.debug('Checking NF: %s', notefile)

            nf_meta = db.find_nf_by_name(notefile) # Note File Meta

            if not nf_meta: # If there's no meta, this must be a new file
                logger.info('NEW notefile for upload: %s', notefile)
                counter_added += 1

                if not dry_run:
                    nf_meta = note.gen_meta(notefile)
                    nf_detail = note.open(notefile)

                    new_sn_object = {}
                    new_sn_object['key'] = nf_meta['key']
                    new_sn_object['createdate'] = nf_meta['createdate']
                    new_sn_object['modifydate'] = nf_meta['modifydate']
                    new_sn_object['content'] = nf_detail['content']

                    new_sn = simplenote.add_note(new_sn_object) # Add the note!
                    logger.debug('API Result: %s', new_sn)

                    if new_sn[1] == 0:
                        logger.debug('New Simplenote Created: %s', new_sn)
                        db.sn(new_sn[0]) # Update simplenote Cache
                        db.nf(nf_meta) # Update notefile meta
                    else:
                        logger.error('Simplenote ADD Request FAILED [%s]', new_sn)
                        counter_http_errors += 1
                        counter_added -= 1

    if not silent_mode:
        sys.stdout.write("\n") # New Line for end of progress bar

    if not dry_run:
        lastsync = db.update_snsync("sn_last_sync", time.time()) # record last sync
    db.disconnect() # Saves the sqlite db.

    # end of play report
    counter_changes = counter_modified + counter_added + counter_deleted
    logger.info('Changes: %s', counter_changes)
    if not silent_mode:
        print('Changes: %s' % counter_changes)

    if counter_modified > 0:
        logger.info('Modified: %s', counter_modified)
        if not silent_mode:
            print('- Modified: %s' % counter_modified)

    if counter_added > 0:
        logger.info('Added: %s', counter_added)
        if not silent_mode:
            print('- Added: %s' % counter_added)

    if counter_deleted > 0:
        logger.info('Deleted: %s', counter_deleted)
        if not silent_mode:
            print('- Deleted: %s' % counter_deleted)

    if counter_http_errors > 0:
        logger.info('HTTP ERRORS: %s', counter_http_errors)
        if not silent_mode:
            print('HTTP ERRORS: %s' % counter_http_errors)

    end_time = time.monotonic() # http://stackoverflow.com/a/26099345
    logger.info('Time Taken: %s', datetime.timedelta(seconds=end_time - start_time))
    if not silent_mode:
        print('Time Taken: %s' % datetime.timedelta(seconds=end_time - start_time))
