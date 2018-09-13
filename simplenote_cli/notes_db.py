
# Copyright (c) 2014 Eric Davis
# This file is *heavily* modified from nvpy.

# nvPY: cross-platform note-taking app with simplenote syncing
# copyright 2012 by Charl P. Botha <cpbotha@vxlabs.com>
# new BSD license

import os, time, re, glob, json, copy, threading
from . import utils
from .simplenote import Simplenote
import logging

class ReadError(RuntimeError):
    pass

class WriteError(RuntimeError):
    pass

class NotesDB():
    """NotesDB will take care of the local notes database and syncing with SN.
    """
    def __init__(self, config, log, update_view):
        self.config      = config
        self.log         = log
        self.update_view = update_view

        self.last_sync = 0 # set to zero to trigger a full sync
        self.sync_lock = threading.Lock()
        self.go_cond   = threading.Condition()

        # create db dir if it does not exist
        if not os.path.exists(self.config.get_config('db_path')):
            os.mkdir(self.config.get_config('db_path'))

        now = time.time()
        # now read all .json files from disk
        fnlist = glob.glob(self.helper_key_to_fname('*'))

        self.notes = {}

        for fn in fnlist:
            try:
                n = json.load(open(fn, 'r'))
            except IOError as e:
                raise ReadError ('Error opening {0}: {1}'.format(fn, str(e)))
            except ValueError as e:
                raise ReadError ('Error reading {0}: {1}'.format(fn, str(e)))
            else:
                # we always have a localkey, also when we don't have a note['key'] yet (no sync)
                localkey = n.get('localkey', os.path.splitext(os.path.basename(fn))[0])
                # we maintain in memory a timestamp of the last save
                # these notes have just been read, so at this moment
                # they're in sync with the disc.
                n['savedate'] = now
                # set a localkey to each note in memory
                # Note: 'key' is used only for syncing with server - 'localkey'
                #       is used for everything else in sncli
                n['localkey'] = localkey

                # add the note to our database
                self.notes[localkey] = n

        # initialise the simplenote instance we're going to use
        # this does not yet need network access
        self.simplenote = Simplenote(self.config.get_config('sn_username'),
                                     self.config.get_config('sn_password'))

        # we'll use this to store which notes are currently being synced by
        # the background thread, so we don't add them anew if they're still
        # in progress. This variable is only used by the background thread.
        self.threaded_syncing_keys = {}

    def filtered_notes_sort(self, filtered_notes, sort_mode='date'):
        if sort_mode == 'date':
            if self.config.get_config('pinned_ontop') == 'yes':
                filtered_notes.sort(key=utils.sort_by_modify_date_pinned, reverse=True)
            else:
                filtered_notes.sort(key=lambda o:
                        -float(o.note.get('modificationDate', 0)))
        elif sort_mode == 'alpha':
            if self.config.get_config('pinned_ontop') == 'yes':
                filtered_notes.sort(key=utils.sort_by_title_pinned)
            else:
                filtered_notes.sort(key=lambda o: utils.get_note_title(o.note))
        elif sort_mode == 'tags':
            pinned = self.config.get_config('pinned_ontop')
            utils.sort_notes_by_tags(filtered_notes, pinned_ontop=pinned)

    def filter_notes(self, search_string=None, search_mode='gstyle', sort_mode='date'):
        """Return list of notes filtered with search string.

        Based on the search mode that has been selected in self.config,
        this method will call the appropriate helper method to do the
        actual work of filtering the notes.

        Returns a list of filtered notes with selected search mode and sorted
        according to configuration. Two more elements in tuple: a regular
        expression that can be used for highlighting strings in the text widget
        and the total number of notes in memory.
        """

        if search_mode == 'gstyle':
            filtered_notes, match_regexp, active_notes = \
                self.filter_notes_gstyle(search_string)
        else:
            filtered_notes, match_regexp, active_notes = \
                self.filter_notes_regex(search_string)

        self.filtered_notes_sort(filtered_notes, sort_mode)

        return filtered_notes, match_regexp, active_notes

    def _helper_gstyle_tagmatch(self, tag_pats, note):
        # Returns:
        #  2 = match    - no tag patterns specified
        #  1 = match    - all tag patterns match a tag on this note
        #  0 = no match - note has no tags or not all tag patterns match

        if not tag_pats:
            # match because no tag patterns were specified
            return 2

        note_tags = note.get('tags')

        if not note_tags:
            # tag patterns specified but note has no tags, so no match
            return 0

        # for each tag_pat, we have to find a matching tag
        # .lower() used for case-insensitive search
        tag_pats_matched = 0
        for tp in tag_pats:
            tp = tp.lower()
            for t in note_tags:
                if tp in t.lower():
                    tag_pats_matched += 1
                    break

        if tag_pats_matched == len(tag_pats):
            # all tag patterns specified matched a tag on this note
            return 1

        # note doesn't match
        return 0

    def _helper_gstyle_wordmatch(self, word_pats, content):
        if not word_pats:
            return True

        word_pats_matched = 0
        lowercase_content = content.lower() # case insensitive search
        for wp in word_pats:
            wp = wp.lower() # case insensitive search
            if wp in lowercase_content:
                word_pats_matched += 1

        if word_pats_matched == len(word_pats):
            return True;

        return False

    def filter_notes_gstyle(self, search_string=None):

        filtered_notes = []

        # total number of notes, excluding deleted
        # if tag:trash then counts deleted as well
        active_notes = 0

        if not search_string:
            for k in self.notes:
                n = self.notes[k]
                if n.get('deleted'):
                    continue
                active_notes += 1
                filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

            return filtered_notes, [], active_notes

        # group0: tag:([^\s]+)
        # group1: multiple words in quotes
        # group2: single words

        # example result for: 'tag:tag1 tag:tag2 word1 "word2 word3" tag:tag3'
        # [ ('tag1', '',            ''),
        #   ('tag2', '',            ''),
        #   ('',     '',            'word1'),
        #   ('',     'word2 word3', ''),
        #   ('tag3', '',            '') ]

        groups = re.findall('tag:([^\s]+)|"([^"]+)"|([^\s]+)', search_string)
        all_pats = [[] for _ in range(3)]

        search_trash = False
        for g in groups:
            if g[0] == 'trash':
                groups.remove(g)
                search_trash = True

        # we end up with [[tag_pats],[multi_word_pats],[single_word_pats]]
        for g in groups:
            for i in range(3):
                if g[i]: all_pats[i].append(g[i])

        for k in self.notes:
            n = self.notes[k]

            if not search_trash and n.get('deleted'):
                continue

            active_notes += 1

            if search_trash and len(groups) == 0:
                # simple search of only 'tag:trash' to get all trashed notes
                if n.get('deleted'):
                    filtered_notes.append(
                        utils.KeyValueObject(key=k,
                                             note=n,
                                             tagfound=1))
                continue

            tagmatch = self._helper_gstyle_tagmatch(all_pats[0], n)

            word_pats = all_pats[1] + all_pats[2]

            if tagmatch and \
               self._helper_gstyle_wordmatch(word_pats, n.get('content')):
                # we have a note that can go through!
                filtered_notes.append(
                    utils.KeyValueObject(key=k,
                                         note=n,
                                         tagfound=1 if tagmatch == 1 else 0))

        return filtered_notes, '|'.join(all_pats[1] + all_pats[2]), active_notes

    def filter_notes_regex(self, search_string=None):
        """
        Return a list of notes filtered using the regex search_string.
        Each element in the list is a tuple (local_key, note).
        """
        sspat = utils.build_regex_search(search_string)

        filtered_notes = []
        active_notes = 0 # total number of notes, including deleted ones

        for k in self.notes:
            n = self.notes[k]

            active_notes += 1

            if not sspat:
                filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))
                continue

            if self.config.get_config('search_tags') == 'yes':
                tag_matched = False
                for t in n.get('tags'):
                    if sspat.search(t):
                        tag_matched = True
                        filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=1))
                        break
                if tag_matched:
                    continue

            if sspat.search(n.get('content')):
                filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

        match_regexp = search_string if sspat else ''
        return filtered_notes, match_regexp, active_notes

    def import_note(self, note):
        # need to get a key unique to this database. not really important
        # what it is, as long as it's unique.
        new_key = note['key'] if note.get('key') else utils.generate_random_key()
        while new_key in self.notes:
            new_key = utils.generate_random_key()

        timestamp = time.time()

        try:
            modifydate = float(note.get('modificationDate', timestamp))
            createdate = float(note.get('creationDate', timestamp))
        except ValueError:
            raise ValueError('date fields must be numbers or string representations of numbers')

        # note has no internal key yet.
        new_note = {
                    'content'    : note.get('content', ''),
                    'deleted'    : note.get('deleted', False),
                    'modificationDate' : modifydate,
                    'creationDate' : createdate,
                    'savedate'   : 0, # never been written to disc
                    'syncdate'   : 0, # never been synced with server
                    'tags'       : note.get('tags', []),
                    'systemTags' : note.get('systemTags', [])
                   }

        # sanity check all note values
        if not isinstance(new_note['content'], str):
            raise ValueError('"content" must be a string')
        if not new_note['deleted'] in (True, False):
            raise ValueError('"deleted" must be True or False')

        for n in (new_note['modificationDate'], new_note['creationDate']):
            if not 0 <= n <= timestamp:
                raise ValueError('date fields must be real')

        if not isinstance(new_note['tags'], list):
            raise ValueError('"tags" must be an array')
        for tag in new_note['tags']:
            if not isinstance(tag, str):
                raise ValueError('items in the "tags" array must be strings')

        if not isinstance(new_note['systemTags'], list):
            raise ValueError('"systemTags" must be an array')
        for tag in new_note['systemTags']:
            if not isinstance(tag, str):
                raise ValueError('items in the "systemTags" array must be strings')

        self.notes[new_key] = new_note

        return new_key

    def create_note(self, content):
        # need to get a key unique to this database. not really important
        # what it is, as long as it's unique.
        new_key = utils.generate_random_key()
        while new_key in self.notes:
            new_key = utils.generate_random_key()

        timestamp = time.time()

        # note has no internal key yet.
        new_note = {
                    'localkey'   : new_key,
                    'content'    : content,
                    'deleted'    : False,
                    'modificationDate' : timestamp,
                    'creationDate' : timestamp,
                    'savedate'   : 0, # never been written to disc
                    'syncdate'   : 0, # never been synced with server
                    'tags'       : []
                   }

        self.notes[new_key] = new_note

        return new_key

    def get_note(self, key):
        return self.notes[key]

    def get_note_systemtags(self, key):
        return self.notes[key].get('systemTags')

    def get_note_tags(self, key):
        return self.notes[key].get('tags')

    def get_note_content(self, key):
        return self.notes[key].get('content')

    def flag_what_changed(self, note, what_changed):
        if 'what_changed' not in note:
            note['what_changed'] = []
        if what_changed not in note['what_changed']:
            note['what_changed'].append(what_changed)

    def set_note_deleted(self, key, deleted):
        n = self.notes[key]
        if n['deleted'] != deleted:
            n['deleted'] = deleted
            n['modificationDate'] = time.time()
            self.flag_what_changed(n, 'deleted')
            self.log('Note {0} (key={1})'.format('trashed' if deleted else 'untrashed', key))

    def set_note_content(self, key, content):
        n = self.notes[key]
        old_content = n.get('content')
        if content != old_content:
            n['content'] = content
            n['modificationDate'] = time.time()
            self.flag_what_changed(n, 'content')
            self.log('Note content updated (key={0})'.format(key))

    def set_note_tags(self, key, tags):
        n = self.notes[key]
        old_tags = n.get('tags')
        tags = utils.sanitise_tags(tags)
        if tags != old_tags:
            n['tags'] = tags
            n['modificationDate'] = time.time()
            self.flag_what_changed(n, 'tags')
            self.log('Note tags updated (key={0})'.format(key))

    def set_note_pinned(self, key, pinned):
        n = self.notes[key]
        old_pinned = utils.note_pinned(n)
        if pinned != old_pinned:
            if 'systemTags' not in n:
                n['systemTags'] = []
            systemtags = n['systemTags']
            if pinned:
                systemtags.append('pinned')
            else:
                systemtags.remove('pinned')
            n['modificationDate'] = time.time()
            self.flag_what_changed(n, 'systemTags')
            self.log('Note {0} (key={1})'.format('pinned' if pinned else 'unpinned', key))

    def set_note_markdown(self, key, markdown):
        n = self.notes[key]
        old_markdown = utils.note_markdown(n)
        if markdown != old_markdown:
            if 'systemTags' not in n:
                n['systemTags'] = []
            systemtags = n['systemTags']
            if markdown:
                systemtags.append('markdown')
            else:
                systemtags.remove('markdown')
            n['modificationDate'] = time.time()
            self.flag_what_changed(n, 'systemTags')
            self.log('Note markdown {0} (key={1})'.format('flagged' if markdown else 'unflagged', key))

    def helper_key_to_fname(self, k):
        return os.path.join(self.config.get_config('db_path'), k) + '.json'

    def helper_save_note(self, k, note):
        # Save a single note to disc.
        fn = self.helper_key_to_fname(k)
        json.dump(note, open(fn, 'w'), indent=2)

        # record that we saved this to disc.
        note['savedate'] = time.time()

    def sync_notes(self, server_sync=True, full_sync=True):
        """Perform a full bi-directional sync with server.

        Params:

        `server_sync` (bool): sync to the server if true

        `full_sync` (bool): perform a full sync. Set to false to only sync
            changes since the last sync. Full sync should happen on sncli start,
            and partial syncs can happen periodically or after modifying a note.


        This follows the recipe in the SimpleNote 2.0 API documentation.
        After this, it could be that local keys have been changed, so
        reset any views that you might have!

        From Simplenote API v2.1.3...

        To check for changes you can use 'syncnum' and 'version'. 'syncnum' will
        increment whenever there is any change to a note, content change, tag
        change, etc. 'version' will increment whenever the content property is
        changed. You should store both these numbers in your client to track
        changes and determine when a note needs to be updated or saved.

        Psuedo-code algorithm for syncing:

            1. for any note changed locally, including new notes:
                   save note to server, update note with response
                   // (new syncnum, version, possible newly-merged content)

            2. get the note index

            3. for each remote note
                   if remote syncnum > local syncnum ||
                      a new note and key is not in local store
                       retrieve note, update note with response

            4. for each local note not in the index
                   PERMANENT DELETE, remove note from local store
        """

        local_updates = {}
        local_deletes = {}
        server_keys = {}
        now = time.time()

        sync_start_time = time.time()
        sync_errors = 0
        skip_remote_syncing = False
        failed_update_keys = set()

        if server_sync and full_sync:
            self.log("Starting full sync")

        # 1. for any note changed locally, including new notes:
        #        save note to server, update note with response
        for note_index, local_key in enumerate(set(self.notes.keys())):
            n = self.notes[local_key]

            # new note or note with newer modification
            if not n.get('key') or \
               float(n.get('modificationDate')) > float(n.get('syncdate')):

                savedate = float(n.get('savedate'))
                if float(n.get('modificationDate')) > savedate or \
                   float(n.get('syncdate')) > savedate:
                    # this will trigger a save to disk after sync algorithm
                    # we want this note saved even if offline or sync fails
                    local_updates[local_key] = True

                if not server_sync:
                    # the 'what_changed' field will be written to disk and
                    # picked up whenever the next full server sync occurs
                    continue

                # only send required fields
                cn = copy.deepcopy(n)
                if 'what_changed' in n:
                    del n['what_changed']

                if 'localkey' in cn:
                    del cn['localkey']

                if 'minversion' in cn:
                    del cn['minversion']
                del cn['syncdate']
                del cn['savedate']

                if 'what_changed' in cn:
                    if 'deleted' not in cn['what_changed']:
                        del cn['deleted']
                    if 'systemTags' not in cn['what_changed'] and 'systemTags' in cn:
                        del cn['systemTags']
                    if 'tags' not in cn['what_changed']:
                        del cn['tags']
                    if 'content' not in cn['what_changed']:
                        del cn['content']
                    del cn['what_changed']

                uret = self.simplenote.update_note(cn)

                if uret[1] == 0: # success
                    # if this is a new note our local key is not valid anymore
                    # merge the note we got back (content could be empty)
                    # record syncdate and save the note at the assigned key
                    del self.notes[local_key]
                    k = uret[0]['key']
                    n.update(uret[0])
                    n['syncdate'] = now
                    n['localkey'] = k
                    self.notes[k] = n

                    local_updates[k] = True
                    if local_key != k:
                        # if local_key was a different key it should be deleted
                        local_deletes[local_key] = True
                        if local_key in local_updates:
                            del local_updates[local_key]

                    self.log('Synced note to server (key={0})'.format(local_key))
                else:
                    self.log('ERROR: Failed to sync note to server (key={0})'.format(local_key))
                    sync_errors += 1
                    failed_update_keys.add(local_key)

        # 2. get the note index
        if not server_sync:
            nl = []
        else:
            nl = self.simplenote.get_note_list()

            if nl[1] == 0:  # success
                nl = nl[0]
            else:
                self.log('ERROR: Failed to get note list from server')
                sync_errors += 1
                nl = []
                skip_remote_syncing = True

        # 3. for each remote note
        #        if remote newer than local ||
        #           a new note and key is not in local store
        #            retrieve note, update note with response
        if not skip_remote_syncing:
            len_nl = len(nl)
            for note_index, n in enumerate(nl):
                k = n['key']
                server_keys[k] = True
                # this works because in the prior step we rewrite local keys to
                # server keys when we get an updated note back from the server
                if k in self.notes:
                    # we already have this note
                    # if the server note has a newer modification date OR
                    # (higher version and same content [metadata changed]), then
                    # update from server.
                    # This should prevent old content overwriting new content,
                    # while allowing new metadata to update.
                    if n['modificationDate'] > self.notes[k].get('modificationDate', -1) or \
                            (n['version'] > self.notes[k]['version'] and \
                            n['content'] == self.notes[k]['content']):
                        self.notes[k].update(n)
                        local_updates[k] = True
                        self.notes[k]['syncdate'] = now
                        self.notes[k]['localkey'] = k
                        self.log('Synced newer note from server (key={0})'.format(k))
                else:
                    # this is a new note
                    self.notes[k] = n
                    local_updates[k] = True
                    self.notes[k]['syncdate'] = now
                    self.notes[k]['localkey'] = k
                    self.log('Synced new note from server (key={0})'.format(k))

        # 4. for each local note not in the index
        #        PERMANENT DELETE, remove note from local store
        # Only do this when a full sync (i.e. entire index) is performed!
        if server_sync and full_sync and not skip_remote_syncing:
            for local_key in list(self.notes.keys()):
                if local_key not in server_keys and local_key not in failed_update_keys:
                    del self.notes[local_key]
                    local_deletes[local_key] = True

        # sync done, now write changes to db_path

        for k in list(local_updates.keys()):
            try:
                self.helper_save_note(k, self.notes[k])
            except WriteError as e:
                raise WriteError (str(e))
            self.log("Saved note to disk (key={0})".format(k))

        for k in list(local_deletes.keys()):
            fn = self.helper_key_to_fname(k)
            if os.path.exists(fn):
                os.unlink(fn)
                self.log("Deleted note from disk (key={0})".format(k))

        if not sync_errors:
            self.last_sync = sync_start_time

        # if there were any changes then update the current view
        if len(local_updates) > 0 or len(local_deletes) > 0:
            self.update_view()

        if server_sync and full_sync:
            self.log("Full sync completed")

        return sync_errors

    def get_note_version(self, key, version):
        gret = self.simplenote.get_note(key, version)
        return gret[0] if gret[1] == 0 else None

    def get_note_status(self, key):
        n = self.notes[key]
        o = utils.KeyValueObject(saved=False, synced=False, modified=False)
        modifydate = float(n['modificationDate'])
        savedate   = float(n['savedate'])
        syncdate   = float(n['syncdate'])

        if savedate > modifydate:
            o.saved = True
        else:
            o.modified = True

        if syncdate > modifydate:
            o.synced = True

        return o

    def verify_all_saved(self):
        all_saved = True
        self.sync_lock.acquire()
        for k in list(self.notes.keys()):
            o = self.get_note_status(k)
            if not o.saved:
                all_saved = False
                break
        self.sync_lock.release()
        return all_saved

    def sync_now(self, do_server_sync=True):
        self.sync_lock.acquire()
        self.sync_notes(server_sync=do_server_sync,
                        full_sync=True if not self.last_sync else False)
        self.sync_lock.release()

    # sync worker thread...
    def sync_worker(self, do_server_sync):
        time.sleep(1) # give some time to wait for GUI initialization
        self.log('Sync worker: started')
        self.sync_now(do_server_sync)
        while True:
            self.go_cond.acquire()
            self.go_cond.wait(15)
            self.sync_now(do_server_sync)
            self.go_cond.release()

    def sync_worker_go(self):
        self.go_cond.acquire()
        self.go_cond.notify()
        self.go_cond.release()

