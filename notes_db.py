# nvPY: cross-platform note-taking app with simplenote syncing
# copyright 2012 by Charl P. Botha <cpbotha@vxlabs.com>
# new BSD license

import codecs
import copy
import glob
import os
import json
import logging
from Queue import Queue, Empty
import re
import simplenote
simplenote.NOTE_FETCH_LENGTH=100
from simplenote import Simplenote

from threading import Thread
import time
import utils

class SyncError(RuntimeError):
    pass

class ReadError(RuntimeError):
    pass

class WriteError(RuntimeError):
    pass

class NotesDB(utils.SubjectMixin):
    """NotesDB will take care of the local notes database and syncing with SN.
    """
    def __init__(self, config):
        utils.SubjectMixin.__init__(self)

        self.config = config

        # create db dir if it does not exist
        if not os.path.exists(self.config.get_config('db_path')):
            os.mkdir(self.config.get_config('db_path'))

        now = time.time()
        # now read all .json files from disk
        fnlist = glob.glob(self.helper_key_to_fname('*'))

        self.notes = {}

        for fn in fnlist:
            try:
                n = json.load(open(fn, 'rb'))

            except IOError, e:
                logging.error('NotesDB_init: Error opening %s: %s' % (fn, str(e)))
                raise ReadError ('Error opening note file')

            except ValueError, e:
                logging.error('NotesDB_init: Error reading %s: %s' % (fn, str(e)))
                raise ReadError ('Error reading note file')

            else:
                # we always have a localkey, also when we don't have a note['key'] yet (no sync)
                localkey = os.path.splitext(os.path.basename(fn))[0]
                self.notes[localkey] = n
                # we maintain in memory a timestamp of the last save
                # these notes have just been read, so at this moment
                # they're in sync with the disc.
                n['savedate'] = now

        # initialise the simplenote instance we're going to use
        # this does not yet need network access
        self.simplenote = Simplenote(self.config.get_config('sn_username'),
                                     self.config.get_config('sn_password'))

        # we'll use this to store which notes are currently being synced by
        # the background thread, so we don't add them anew if they're still
        # in progress. This variable is only used by the background thread.
        self.threaded_syncing_keys = {}

    def create_note(self, title):
        # need to get a key unique to this database. not really important
        # what it is, as long as it's unique.
        new_key = utils.generate_random_key()
        while new_key in self.notes:
            new_key = utils.generate_random_key()

        timestamp = time.time()

        # note has no internal key yet.
        new_note = {
                    'content' : title,
                    'modifydate' : timestamp,
                    'createdate' : timestamp,
                    'savedate' : 0, # never been written to disc
                    'syncdate' : 0, # never been synced with server
                    'tags' : []
                    }

        self.notes[new_key] = new_note

        return new_key

    def filter_notes(self, search_string=None):
        """Return list of notes filtered with search string.

        Based on the search mode that has been selected in self.config,
        this method will call the appropriate helper method to do the
        actual work of filtering the notes.

        @param search_string: String that will be used for searching.
         Different meaning depending on the search mode.
        @return: notes filtered with selected search mode and sorted according
        to configuration. Two more elements in tuple: a regular expression
        that can be used for highlighting strings in the text widget; the
        total number of notes in memory.
        """

        if self.config.get_config('search_mode') == 'regexp':
            filtered_notes, match_regexp, active_notes = self.filter_notes_regexp(search_string)
        else:
            filtered_notes, match_regexp, active_notes = self.filter_notes_gstyle(search_string)

        if self.config.get_config('sort_mode') == 'alpha':
            if self.config.get_config('pinned_ontop') == 'no':
                # sort alphabetically on title
                filtered_notes.sort(key=lambda o: utils.get_note_title(o.note))
            else:
                filtered_notes.sort(utils.sort_by_title_pinned)

        else:
            if self.config.get_config('pinned_ontop') == 'no':
                # last modified on top
                filtered_notes.sort(key=lambda o: -float(o.note.get('modifydate', 0)))
            else:
                filtered_notes.sort(utils.sort_by_modify_date_pinned, reverse=True)

        return filtered_notes, match_regexp, active_notes

    def _helper_gstyle_tagmatch(self, tag_pats, note):
        if tag_pats:
            tags = note.get('tags')

            # tag: patterns specified, but note has no tags, so no match
            if not tags:
                return 0

            # for each tag_pat, we have to find a matching tag
            for tp in tag_pats:
                # at the first match between tp and a tag:
                if next((tag for tag in tags if tag.startswith(tp)), None) is not None:
                    # we found a tag that matches current tagpat, so we move to the next tagpat
                    continue

                else:
                    # we found no tag that matches current tagpat, so we break out of for loop
                    break

            else:
                # for loop never broke out due to no match for tagpat, so:
                # all tag_pats could be matched, so note is a go.
                return 1


            # break out of for loop will have us end up here
            # for one of the tag_pats we found no matching tag
            return 0


        else:
            # match because no tag: patterns were specified
            return 2

    def _helper_gstyle_mswordmatch(self, msword_pats, content):
        """If all words / multi-words in msword_pats are found in the content,
        the note goes through, otherwise not.

        @param msword_pats:
        @param content:
        @return:
        """

        # no search patterns, so note goes through
        if not msword_pats:
            return True

        # search for the first p that does NOT occur in content
        if next((p for p in msword_pats if p not in content), None) is None:
            # we only found pats that DO occur in content so note goes through
            return True

        else:
            # we found the first p that does not occur in content
            return False

    def filter_notes_gstyle(self, search_string=None):

        filtered_notes = []
        # total number of notes, excluding deleted
        active_notes = 0

        if not search_string:
            for k in self.notes:
                n = self.notes[k]
                if not n.get('deleted'):
                    active_notes += 1
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

            return filtered_notes, [], active_notes

        # group0: ag - not used
        # group1: t(ag)?:([^\s]+)
        # group2: multiple words in quotes
        # group3: single words
        # example result for 't:tag1 t:tag2 word1 "word2 word3" tag:tag3' ==
        # [('', 'tag1', '', ''), ('', 'tag2', '', ''), ('', '', '', 'word1'), ('', '', 'word2 word3', ''), ('ag', 'tag3', '', '')]

        groups = re.findall('t(ag)?:([^\s]+)|"([^"]+)"|([^\s]+)', search_string)
        tms_pats = [[] for _ in range(3)]

        # we end up with [[tag_pats],[multi_word_pats],[single_word_pats]]
        for gi in groups:
            for mi in range(1,4):
                if gi[mi]:
                    tms_pats[mi-1].append(gi[mi])

        for k in self.notes:
            n = self.notes[k]

            if not n.get('deleted'):
                active_notes += 1
                c = n.get('content')

                tagmatch = self._helper_gstyle_tagmatch(tms_pats[0], n)
                msword_pats = tms_pats[1] + tms_pats[2]

                if tagmatch and self._helper_gstyle_mswordmatch(msword_pats, c):
                    # we have a note that can go through!

                    # tagmatch == 1 if a tag was specced and found
                    # tagmatch == 2 if no tag was specced (so all notes go through)
                    tagfound = 1 if tagmatch == 1 else 0
                    # we have to store our local key also
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=tagfound))

        return filtered_notes, '|'.join(tms_pats[1] + tms_pats[2]), active_notes

    def filter_notes_regexp(self, search_string=None):
        """Return list of notes filtered with search_string,
        a regular expression, each a tuple with (local_key, note).
        """

        if search_string:
            try:
                sspat = re.compile(search_string)
            except re.error:
                sspat = None

        else:
            sspat = None

        filtered_notes = []
        # total number of notes, excluding deleted ones
        active_notes = 0
        for k in self.notes:
            n = self.notes[k]
            # we don't do anything with deleted notes (yet)
            if n.get('deleted'):
                continue

            active_notes += 1

            c = n.get('content')
            if self.config.search_tags == 'yes':
                t = n.get('tags')
                if sspat:
                    # this used to use a filter(), but that would by definition
                    # test all elements, whereas we can stop when the first
                    # matching element is found
                    # now I'm using this awesome trick by Alex Martelli on
                    # http://stackoverflow.com/a/2748753/532513
                    # first parameter of next is a generator
                    # next() executes one step, but due to the if, this will
                    # either be first matching element or None (second param)
                    if t and next((ti for ti in t if sspat.search(ti)), None) is not None:
                        # we have to store our local key also
                        filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=1))

                    elif sspat.search(c):
                        # we have to store our local key also
                        filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

                else:
                    # we have to store our local key also
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))
            else:
                if (not sspat or sspat.search(c)):
                    # we have to store our local key also
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

        match_regexp = search_string if sspat else ''

        return filtered_notes, match_regexp, active_notes

    def get_note(self, key):
        return self.notes[key]

    def get_note_systemtags(self, key):
        return self.notes[key].get('systemtags')

    def get_note_tags(self, key):
        return self.notes[key].get('tags')

    def get_note_content(self, key):
        return self.notes[key].get('content')

    def get_note_status(self, key):
        n = self.notes[key]
        o = utils.KeyValueObject(saved=False, synced=False, modified=False)
        modifydate = float(n['modifydate'])
        savedate = float(n['savedate'])

        if savedate > modifydate:
            o.saved = True
        else:
            o.modified = True

        if float(n['syncdate']) > modifydate:
            o.synced = True

        return o

    def flag_what_changed(self, note, what_changed):
        if 'what_changed' not in note:
            note['what_changed'] = []
        if what_changed not in note['what_changed']:
            note['what_changed'].append(what_changed)

    def set_note_deleted(self, key):
        n = self.notes[key]
        if not n['deleted']:
            n['deleted'] = 1
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status',
                                  utils.KeyValueObject(what='modifydate',
                                                       key=key,
                                                       msg='Note trashed.'))
            self.flag_what_changed(n, 'deleted')

    def set_note_content(self, key, content):
        n = self.notes[key]
        old_content = n.get('content')
        if content != old_content:
            n['content'] = content
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status',
                                  utils.KeyValueObject(what='modifydate',
                                                       key=key,
                                                       msg='Note content updated.'))
            self.flag_what_changed(n, 'content')

    def set_note_tags(self, key, tags):
        n = self.notes[key]
        old_tags = n.get('tags')
        tags = utils.sanitise_tags(tags)
        if tags != old_tags:
            n['tags'] = tags
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status',
                                  utils.KeyValueObject(what='modifydate',
                                                       key=key,
                                                       msg='Note tags updated.'))
            self.flag_what_changed(n, 'tags')

    def set_note_pinned(self, key, pinned):
        n = self.notes[key]
        old_pinned = utils.note_pinned(n)
        if pinned != old_pinned:
            if 'systemtags' not in n:
                n['systemtags'] = []
            systemtags = n['systemtags']
            if pinned:
                systemtags.append('pinned')
            else:
                systemtags.remove('pinned')
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status',
                utils.KeyValueObject(what='modifydate',
                                     key=key,
                                     msg='Note pinned.' if pinned else 'Note unpinned.'))
            self.flag_what_changed(n, 'systemtags')

    def set_note_markdown(self, key, markdown):
        n = self.notes[key]
        old_markdown = utils.note_markdown(n)
        if markdown != old_markdown:
            if 'systemtags' not in n:
                n['systemtags'] = []
            systemtags = n['systemtags']
            if markdown:
                systemtags.append('markdown')
            else:
                systemtags.remove('markdown')
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status',
                utils.KeyValueObject(what='modifydate',
                                     key=key,
                                     msg='Note markdown flagged.' if markdown else 'Note markdown unflagged.'))
            self.flag_what_changed(n, 'systemtags')

    def helper_key_to_fname(self, k):
            return os.path.join(self.config.get_config('db_path'), k) + '.json'

    def helper_save_note(self, k, note):
        """Save a single note to disc.

        """

        fn = self.helper_key_to_fname(k)
        json.dump(note, open(fn, 'wb'), indent=2)

        # record that we saved this to disc.
        note['savedate'] = time.time()

    def sync_note(self, k, check_for_new):
        """Sync a single note with the server.

        Update existing note in memory with the returned data.
        This is a sychronous (blocking) call.
        """

        note = self.notes[k]

        # update if note has no key or it has been modified since last sync
        if not note.get('key') or \
           float(note.get('modifydate')) > float(note.get('syncdate')):
            logging.debug('Sync worker: updating note %s', k)

            # only send required fields
            cn = copy.deepcopy(note)
            if 'what_changed' in note:
                del note['what_changed']

            del cn['minversion']
            del cn['createdate']
            del cn['syncdate']
            del cn['savedate']

            if 'what_changed' in cn:
                if 'deleted' not in cn['what_changed']:
                    del cn['deleted']
                if 'systemtags' not in cn['what_changed']:
                    del cn['systemtags']
                if 'tags' not in cn['what_changed']:
                    del cn['tags']
                if 'content' not in cn['what_changed']:
                    del cn['content']
                del cn['what_changed']

            uret = self.simplenote.update_note(cn)
            #uret = self.simplenote.update_note(note)

            if uret[1] == 0: # success!
                n = uret[0]
                # if content was unchanged there'll be no content sent back
                new_content = True if n.get('content', None) else False
                # store when we've synced
                n['syncdate'] = time.time()
                note.update(n)
                logging.debug('Sync worker: updated note %s', k)
                return (k, new_content)
            else:
                logging.debug('ERROR: Sync worker: update failed for note %s', k)
                return None

        else:
            if not check_for_new:
                return None

            logging.debug('Sync worker: checking for server update of note %s', k)

            # our note is synced so lets check if server has something newer
            gret = self.simplenote.get_note(note['key'])

            if gret[1] == 0: # success!
                n = gret[0]
                if int(n.get('syncnum')) > int(note.get('syncnum')):
                    # store what we pulled down from the server
                    n['syncdate'] = time.time()
                    note.update(n)
                    logging.debug('Sync worker: server had an update for note %s', k)
                    return (k, True)
                else:
                    logging.debug('Sync worker: server in sync with note %s', k)
                    return (k, False)
            else:
                logging.debug('ERROR: Sync worker: get failed for note %s', k)
                return None

    # sync worker thread...
    def sync_worker(self):
        logging.debug('Sync worker: started')
        while True:
            time.sleep(5)
            now = time.time()
            for k,n in self.notes.items():
                modifydate = float(n.get('modifydate', -1))
                if (now - modifydate) > 3:
                    self.sync_note(k, False)

    def sync_full(self):
        """Perform a full bi-directional sync with server.

        This follows the recipe in the SimpleNote 2.0 API documentation.
        After this, it could be that local keys have been changed, so
        reset any views that you might have.
        """

        local_updates = {}
        local_deletes = {}
        now = time.time()

        self.notify_observers('progress:sync_full', utils.KeyValueObject(msg='Starting full sync.'))
        # 1. go through local notes, if anything changed or new, update to server
        for ni,lk in enumerate(self.notes.keys()):
            n = self.notes[lk]
            if not n.get('key') or float(n.get('modifydate')) > float(n.get('syncdate')):
                uret = self.simplenote.update_note(n)
                if uret[1] == 0:
                    # replace n with uret[0]
                    # if this was a new note, our local key is not valid anymore
                    del self.notes[lk]
                    # in either case (new or existing note), save note at assigned key
                    k = uret[0].get('key')
                    # we merge the note we got back (content could be empty!)
                    n.update(uret[0])
                    # and put it at the new key slot
                    self.notes[k] = n

                    # record that we just synced
                    uret[0]['syncdate'] = now

                    # whatever the case may be, k is now updated
                    local_updates[k] = True
                    if lk != k:
                        # if lk was a different (purely local) key, should be deleted
                        local_deletes[lk] = True

                    self.notify_observers('progress:sync_full',
                            utils.KeyValueObject(msg='Synced modified note %d to server. (key=%s)' % (ni,lk)))

                else:
                    self.notify_observers('progress:sync_full',
                            utils.KeyValueObject(msg='ERROR: Failed to sync modified note %d to server. (key=%s)' % (ni,lk)))
                    self.notify_observers('progress:sync_full',
                            utils.KeyValueObject(msg="SyncError: " + str(uret[0])))

        # 2. if remote syncnum > local syncnum, update our note; if key is new, add note to local.
        # this gets the FULL note list, even if multiple gets are required
        self.notify_observers('progress:sync_full',
                utils.KeyValueObject(msg='Retrieving full note list from server, could take a while.'))
        nl = self.simplenote.get_note_list()
        if nl[1] == 0:
            nl = nl[0]
            self.notify_observers('progress:sync_full',
                    utils.KeyValueObject(msg='Retrieved full note list from server.'))

        else:
            self.notify_observers('progress:sync_full',
                    utils.KeyValueObject(msg='ERROR: Could not get note list from server.'))
            return 1

        server_keys = {}
        lennl = len(nl)
        sync_from_server_errors = 0
        for ni,n in enumerate(nl):
            k = n.get('key')
            server_keys[k] = True
            # this works, only because in phase 1 we rewrite local keys to
            # server keys when we get an updated not back from the server
            if k in self.notes:
                # we already have this
                # check if server n has a newer syncnum than mine
                if int(n.get('syncnum')) > int(self.notes[k].get('syncnum', -1)):
                    # and the server is newer
                    ret = self.simplenote.get_note(k)
                    if ret[1] == 0:
                        self.notes[k].update(ret[0])
                        local_updates[k] = True
                        # in both cases, new or newer note, syncdate is now.
                        self.notes[k]['syncdate'] = now
                        self.notify_observers('progress:sync_full',
                                utils.KeyValueObject(msg='Synced newer note %d (%d) from server.' % (ni,lennl)))
                    else:
                        self.notify_observers('progress:sync_full',
                                utils.KeyValueObject(msg='ERROR: Failed to sync newer note %s from server: %s' % (k,ret[0])))
                        sync_from_server_errors+=1

            else:
                # new note
                ret = self.simplenote.get_note(k)
                if ret[1] == 0:
                    self.notes[k] = ret[0]
                    local_updates[k] = True
                    # in both cases, new or newer note, syncdate is now.
                    self.notes[k]['syncdate'] = now
                    self.notify_observers('progress:sync_full',
                            utils.KeyValueObject(msg='Synced new note %d (%d) from server.' % (ni,lennl)))
                else:
                    self.notify_observers('progress:sync_full',
                            utils.KeyValueObject(msg='ERROR: Failed syncing new note %s from server: %s' % (k,ret[0])))
                    sync_from_server_errors+=1

        # 3. for each local note not in server index, remove.
        for lk in self.notes.keys():
            if lk not in server_keys:
                del self.notes[lk]
                local_deletes[lk] = True

        # sync done, now write changes to db_path
        for uk in local_updates.keys():
            try:
                self.helper_save_note(uk, self.notes[uk])
            except WriteError, e:
                raise WriteError(e)

        for dk in local_deletes.keys():
            fn = self.helper_key_to_fname(dk)
            if os.path.exists(fn):
                os.unlink(fn)

        self.notify_observers('progress:sync_full', utils.KeyValueObject(msg='Full sync complete.'))

        return sync_from_server_errors

    # save worker thread...
    def save_worker(self):
        logging.debug('Save worker: started')
        while True:
            time.sleep(5)
            #logging.debug('Save worker: checking for work')
            for k,n in self.notes.items():
                savedate = float(n.get('savedate'))
                if float(n.get('modifydate')) > savedate or \
                   float(n.get('syncdate')) > savedate:
                    try:
                        # this will write the new savedate into the note
                        self.helper_save_note(k, n)
                        logging.debug('Save worker: saved note %s', k)
                    except WriteError, e:
                        msg = 'ERROR: Failed to write file to the filesystem!'
                        logging.error(msg)
                        print msg
                        os._exit(1)

