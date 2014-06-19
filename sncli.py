#!/usr/bin/env python2

import os, sys, signal, time, logging, json
import ConfigParser
from simplenote import Simplenote
from notes_db import NotesDB, SyncError, ReadError, WriteError
from logging.handlers import RotatingFileHandler

class Config:

    def __init__(self):
        self.home = os.path.abspath(os.path.expanduser('~'))
        defaults = {
                    'sn_username'  : 'edavis@insanum.com',
                    'sn_password'  : 'biteme55',
                    'db_path'      : os.path.join(self.home, '.sncli'),
                    'search_mode'  : 'gstyle',
                    'search_tags'  : '1',
                    'sort_mode'    : '1',
                    'pinned_ontop' : '1',
                   }

        cp = ConfigParser.SafeConfigParser(defaults)
        self.configs_read = cp.read([os.path.join(self.home, '.snclirc')])

        cfg_sec = 'sncli'

        if not cp.has_section(cfg_sec):
            cp.add_section(cfg_sec)
            self.ok = False
        else:
            self.ok = True

        self.sn_username  = cp.get(cfg_sec, 'sn_username', raw=True)
        self.sn_password  = cp.get(cfg_sec, 'sn_password', raw=True)
        self.db_path      = cp.get(cfg_sec, 'db_path')
        self.search_mode  = cp.get(cfg_sec, 'search_mode')
        self.search_tags  = cp.getint(cfg_sec, 'search_tags')
        self.sort_mode    = cp.getint(cfg_sec, 'sort_mode')
        self.pinned_ontop = cp.getint(cfg_sec, 'pinned_ontop')

class sncli:

    def __init__(self):
        self.config = Config()

        if not os.path.exists(self.config.db_path):
            os.mkdir(self.config.db_path)

        # configure the logging module
        self.logfile = os.path.join(self.config.db_path, 'sncli.log')
        self.loghandler = RotatingFileHandler(self.logfile, maxBytes=100000, backupCount=1)
        self.loghandler.setLevel(logging.DEBUG)
        self.loghandler.setFormatter(logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(message)s'))
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.loghandler)
        logging.debug('sncli logging initialized')

        try:
            self.ndb = NotesDB(self.config)
        except Exception, e:
            print("ERROR: Please check sncli.log")
            print(e)
            exit(1)

        self.ndb.add_observer('synced:note', self.observer_notes_db_synced_note)
        self.ndb.add_observer('change:note-status', self.observer_notes_db_change_note_status)
        self.ndb.add_observer('progress:sync_full', self.observer_notes_db_sync_full)
        self.sync_full()

    def do_it(self):
        while True:
            time.sleep(1)

    def sync_full(self):
        try:
            sync_from_server_errors = self.ndb.sync_full()
        except Exception, e:
            print("ERROR: Please check sncli.log")
            print(e)
            exit(1)
        else:
            if sync_from_server_errors > 0:
                print('Error syncing %d notes from server. Please check sncli.log for details.' % (sync_from_server_errors))

    def set_note_status(self, msg):
        print(msg)

    def observer_notes_db_change_note_status(self, ndb, evt_type, evt):
        skey = self.get_selected_note_key()
        if skey == evt.key:
            # XXX
            #self.view.set_note_status(self.ndb.get_note_status(skey))
            self.set_note_status(self.ndb.get_note_status(skey))

    def set_status_text(self, msg):
        print(msg)

    def observer_notes_db_sync_full(self, ndb, evt_type, evt):
        logging.debug(evt.msg)
        # XXX
        #self.view.set_status_text(evt.msg)
        self.set_status_text(evt.msg)

    def observer_notes_db_synced_note(self, ndb, evt_type, evt):
        """This observer gets called only when a note returns from
        a sync that's more recent than our most recent mod to that note.
        """

        selected_note_o = self.notes_list_model.list[self.selected_note_idx]
        # if the note synced back matches our currently selected note,
        # we overwrite.

        # XXX
        #if selected_note_o.key == evt.lkey:
        #    if selected_note_o.note['content'] != evt.old_note['content']:
        #        self.view.mute_note_data_changes()
        #        # in this case, we want to keep the user's undo buffer so that they
        #        # can undo synced back changes if they would want to.
        #        self.view.set_note_data(selected_note_o.note, reset_undo=False)
        #        self.view.unmute_note_data_changes()


def SIGINT_handler(signum, frame):
    print('Signal caught, bye!')
    sys.exit(1)

signal.signal(signal.SIGINT, SIGINT_handler)

def main():
    SNCLI = sncli()
    SNCLI.do_it()

if __name__ == '__main__':
    main()

#notes_list, status = sn.get_note_list()
#if status == -1:
#    exit(1)

#for i in notes_list:
#    note = sn.get_note(i['key'], version=i['version'])
#    if note[1] == 0:
#        print '-----------------------------------'
#        print i['key']
#        print note[0]['content']

