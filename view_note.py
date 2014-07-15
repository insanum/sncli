
import time, urwid
import utils

class ViewNote(urwid.ListBox):

    def __init__(self, config, args):
        self.config = config
        self.ndb = args['ndb']
        self.key = args['key']
        self.log = args['log']
        self.note = self.ndb.get_note(self.key) if self.key else None
        self.old_note = None
        self.tabstop = int(self.config.get_config('tabstop'))
        super(ViewNote, self).__init__(
                  urwid.SimpleFocusListWalker(self.get_note_content_as_list()))

    def get_note_content_as_list(self):
        lines = []
        if not self.key:
            return lines
        if self.old_note:
            for l in self.old_note['content'].split('\n'):
                lines.append(
                    urwid.AttrMap(urwid.Text(l.replace('\t', ' ' * self.tabstop)),
                                  'note_content_old',
                                  'note_content_old_focus'))
        else:
            for l in self.note['content'].split('\n'):
                lines.append(
                    urwid.AttrMap(urwid.Text(l.replace('\t', ' ' * self.tabstop)),
                                  'note_content',
                                  'note_content_focus'))
        lines.append(urwid.AttrMap(urwid.Divider(u'-'), 'default'))
        return lines

    def update_note_view(self, key=None, version=None):
        if key: # setting a new note
            self.key      = key
            self.note     = self.ndb.get_note(self.key)
            self.old_note = None

        if self.key and version:
            # verify version is within range
            if int(version) <= 0 or int(version) >= self.note['version'] + 1:
                self.log(u'Version v{0} is unavailable (key={1})'.
                         format(version, self.key))
                return

        if (not version and self.old_note) or \
           (self.key and version and version == self.note['version']):
            self.log(u'Displaying latest version v{0} of note (key={1})'.
                     format(self.note['version'], self.key))
            self.old_note = None
        elif self.key and version:
            # get a previous version of the note
            self.log(u'Fetching version v{0} of note (key={1})'.
                     format(version, self.key))
            version_note = self.ndb.get_note_version(self.key, version)
            if not version_note:
                self.log(u'Failed to get version v{0} of note (key={1})'.
                         format(version, self.key))
                # don't do anything, keep current note/version
            else:
                self.old_note = version_note

        self.body[:] = \
            urwid.SimpleFocusListWalker(self.get_note_content_as_list())
        self.focus_position = 0

    def get_status_bar(self):
        if not self.key:
            return \
                urwid.AttrMap(urwid.Text(u'No note...'),
                              'status_bar')

        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        if self.old_note:
            tnote = self.old_note
            t = time.localtime(float(tnote['versiondate']))
        else:
            tnote = self.note
            t = time.localtime(float(tnote['modifydate']))

        mod_time = time.strftime(u'Date: %a, %d %b %Y %H:%M:%S', t)
        title    = utils.get_note_title(tnote)
        flags    = utils.get_note_flags(tnote)
        tags     = utils.get_note_tags(tnote)
        version  = tnote['version']

        status_title = \
            urwid.AttrMap(urwid.Text(u'Title: ' +
                                     title,
                                     wrap='clip'),
                          'status_bar')
        status_key_index = \
            ('pack', urwid.AttrMap(urwid.Text(u' [' + 
                                              self.key + 
                                              u'] ' +
                                              str(cur + 1) +
                                              u'/' +
                                              str(total)),
                                   'status_bar'))
        status_date = \
            urwid.AttrMap(urwid.Text(mod_time,
                                     wrap='clip'),
                          'status_bar')
        status_tags_flags = \
            ('pack', urwid.AttrMap(urwid.Text(u'[' + 
                                              tags + 
                                              u'] [v' + 
                                              str(version) + 
                                              u'] [' + 
                                              flags + 
                                              u']'),
                                   'status_bar'))
        pile_top = urwid.Columns([ status_title, status_key_index ])
        pile_bottom = urwid.Columns([ status_date, status_tags_flags ])

        if utils.note_published(tnote) and 'publishkey' in tnote:
            pile_publish = \
                urwid.AttrMap(urwid.Text(u'Published: http://simp.ly/publish/' +
                                         tnote['publishkey']),
                              'status_bar')
            return \
                urwid.AttrMap(urwid.Pile([ pile_top, pile_bottom, pile_publish ]),
                              'status_bar')
        else:
            return \
                urwid.AttrMap(urwid.Pile([ pile_top, pile_bottom ]),
                              'status_bar')

    def keypress(self, size, key):
        if key == self.config.get_keybind('tabstop2'):
            self.tabstop = 2
            self.body[:] = \
                urwid.SimpleFocusListWalker(self.get_note_content_as_list())

        elif key == self.config.get_keybind('tabstop4'):
            self.tabstop = 4
            self.body[:] = \
                urwid.SimpleFocusListWalker(self.get_note_content_as_list())

        elif key == self.config.get_keybind('tabstop8'):
            self.tabstop = 8
            self.body[:] = \
                urwid.SimpleFocusListWalker(self.get_note_content_as_list())

        else:
            return key

        return None

