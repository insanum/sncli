# nvPY: cross-platform note-taking app with simplenote syncing
# copyright 2012 by Charl P. Botha <cpbotha@vxlabs.com>
# new BSD license

import os, time, re, glob, json, copy, threading
import utils
import simplenote
simplenote.NOTE_FETCH_LENGTH=100
from simplenote import Simplenote

class ReadError(RuntimeError):
    pass

class WriteError(RuntimeError):
    pass

class NotesDB():
    """NotesDB will take care of the local notes database and syncing with SN.
    """
    def __init__(self, config, log):
        self.config    = config
        self.log       = log

        self.last_sync = 0 # set to zero to trigger a full sync
        self.sync_lock = threading.Lock()

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
                raise ReadError ('Error opening {0}: {1}'.format(fn, str(e)))
            except ValueError, e:
                raise ReadError ('Error reading {0}: {1}'.format(fn, str(e)))
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

    def create_note(self, content):
        # need to get a key unique to this database. not really important
        # what it is, as long as it's unique.
        new_key = utils.generate_random_key()
        while new_key in self.notes:
            new_key = utils.generate_random_key()

        timestamp = time.time()

        # note has no internal key yet.
        new_note = {
                    'content'    : content,
                    'modifydate' : timestamp,
                    'createdate' : timestamp,
                    'savedate'   : 0, # never been written to disc
                    'syncdate'   : 0, # never been synced with server
                    'tags'       : []
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
            self.flag_what_changed(n, 'deleted')
            self.log('Note trashed (key={0})'.format(key))

    def set_note_content(self, key, content):
        n = self.notes[key]
        old_content = n.get('content')
        if content != old_content:
            n['content'] = content
            n['modifydate'] = time.time()
            self.flag_what_changed(n, 'content')
            self.log('Note content updated (key={0})'.format(key))

    def set_note_tags(self, key, tags):
        n = self.notes[key]
        old_tags = n.get('tags')
        tags = utils.sanitise_tags(tags)
        if tags != old_tags:
            n['tags'] = tags
            n['modifydate'] = time.time()
            self.flag_what_changed(n, 'tags')
            self.log('Note tags updated (key={0})'.format(key))

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
            self.flag_what_changed(n, 'systemtags')
            self.log('Note {0} (key={1})'.format('pinned' if pinned else 'unpinned', key))

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
            self.flag_what_changed(n, 'systemtags')
            self.log('Note markdown {0} (key={1})'.format('flagged' if markdown else 'unflagged', key))

    def helper_key_to_fname(self, k):
        return os.path.join(self.config.get_config('db_path'), k) + '.json'

    def helper_save_note(self, k, note):
        # Save a single note to disc.
        fn = self.helper_key_to_fname(k)
        json.dump(note, open(fn, 'wb'), indent=2)

        # record that we saved this to disc.
        note['savedate'] = time.time()

    def sync_notes(self, server_sync=True, full_sync=True):
        """Perform a full bi-directional sync with server.

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

        if server_sync and full_sync:
            self.log("Starting full sync")

        # 1. for any note changed locally, including new notes:
        #        save note to server, update note with response
        for note_index, local_key in enumerate(self.notes.keys()):
            n = self.notes[local_key]
            if not n.get('key') or \
               float(n.get('modifydate')) > float(n.get('syncdate')):

                savedate = float(n.get('savedate'))
                if float(n.get('modifydate')) > savedate or \
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

                if 'minversion' in cn:
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

                if uret[1] == 0: # success
                    # if this is a new note our local key is not valid anymore
                    # merge the note we got back (content could be empty)
                    # record syncdate and save the note at the assigned key
                    del self.notes[local_key]
                    k = uret[0].get('key')
                    n.update(uret[0])
                    n['syncdate'] = now
                    self.notes[k] = n

                    local_updates[k] = True
                    if local_key != k:
                        # if local_key was a different key it should be deleted
                        local_deletes[local_key] = True
                        local_updates[local_key] = False

                    self.log('Synced note to server (key={0})'.format(local_key))
                else:
                    self.log('ERROR: Failed to sync note to server (key={0})'.format(local_key))
                    sync_errors += 1

        # 2. get the note index
        if not server_sync:
            nl = []
        else:
            nl = self.simplenote.get_note_list(since=None if full_sync else self.last_sync)

            if nl[1] == 0: # success
                nl = nl[0]
            else:
                self.log('ERROR: Failed to get note list from server')
                sync_errors += 1
                nl = []

        # 3. for each remote note
        #        if remote syncnum > local syncnum ||
        #           a new note and key is not in local store
        #            retrieve note, update note with response
        len_nl = len(nl)
        sync_errors = 0
        for note_index, n in enumerate(nl):
            k = n.get('key')
            server_keys[k] = True
            # this works because in the prior step we rewrite local keys to
            # server keys when we get an updated note back from the server
            if k in self.notes:
                # we already have this note
                # if the server note has a newer syncnum we need to get it
                if int(n.get('syncnum')) > int(self.notes[k].get('syncnum', -1)):
                    gret = self.simplenote.get_note(k)
                    if gret[1] == 0:
                        self.notes[k].update(gret[0])
                        local_updates[k] = True
                        self.notes[k]['syncdate'] = now

                        self.log('Synced newer note from server (key={0})'.format(k))
                    else:
                        self.log('ERROR: Failed to sync newer note from server (key={0})'.format(k))
                        sync_errors += 1
            else:
                # this is a new note
                gret = self.simplenote.get_note(k)
                if gret[1] == 0:
                    self.notes[k] = gret[0]
                    local_updates[k] = True
                    self.notes[k]['syncdate'] = now

                    self.log('Synced new note from server (key={0})'.format(k))
                else:
                    self.log('ERROR: Failed syncing new note from server (key={0})'.format(k))
                    sync_errors += 1

        # 4. for each local note not in the index
        #        PERMANENT DELETE, remove note from local store
        # Only do this when a full sync (i.e. entire index) is performed!
        if server_sync and full_sync:
            for local_key in self.notes.keys():
                if local_key not in server_keys:
                    del self.notes[local_key]
                    local_deletes[local_key] = True

        # sync done, now write changes to db_path

        for k in local_updates.keys():
            try:
                self.helper_save_note(k, self.notes[k])
            except WriteError, e:
                raise WriteError (str(e))
            self.log("Saved note to disk (key={0})".format(k))

        for k in local_deletes.keys():
            fn = self.helper_key_to_fname(k)
            if os.path.exists(fn):
                os.unlink(fn)
                self.log("Deleted note from disk (key={0})".format(k))

        if not sync_errors:
            self.last_sync = sync_start_time

        if server_sync and full_sync:
            self.log("Full sync completed")

        return sync_errors

    def get_note_status(self, key):
        n = self.notes[key]
        o = utils.KeyValueObject(saved=False, synced=False, modified=False)
        modifydate = float(n['modifydate'])
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
        for k in self.notes.keys():
            o = self.get_note_status(k)
            if not o.saved:
                all_saved = False
                break
        self.sync_lock.release()
        return all_saved

    # sync worker thread...
    def sync_worker(self, do_sync):
        time.sleep(1) # give some time to wait for GUI initialization
        self.log('Sync worker: started')
        while True:
            self.sync_lock.acquire()
            self.sync_notes(server_sync=do_sync,
                            full_sync=True if not self.last_sync else False)
            self.sync_lock.release()
            time.sleep(5)

