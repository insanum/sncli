
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import time, urwid
from . import utils
import re
from .clipboard import Clipboard
import logging

class ViewNote(urwid.ListBox):

    def __init__(self, config, args):
        self.config = config
        self.ndb = args['ndb']
        self.key = args['key']
        self.log = args['log']
        self.search_string = ''
        self.search_mode = 'gstyle'
        self.search_direction = ''
        self.note = self.ndb.get_note(self.key) if self.key else None
        self.old_note = None
        self.tabstop = int(self.config.get_config('tabstop'))
        self.clipboard = Clipboard()
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
        lines.append(urwid.AttrMap(urwid.Divider('-'), 'default'))
        return lines

    def update_note_view(self, key=None, version=None):
        if key: # setting a new note
            self.key      = key
            self.note     = self.ndb.get_note(self.key)
            self.old_note = None

        if self.key and version:
            # verify version is within range
            if int(version) <= 0 or int(version) >= self.note['version'] + 1:
                self.log('Version v{0} is unavailable (key={1})'.
                         format(version, self.key))
                return

        if (not version and self.old_note) or \
           (self.key and version and version == self.note['version']):
            self.log('Displaying latest version v{0} of note (key={1})'.
                     format(self.note['version'], self.key))
            self.old_note = None
        elif self.key and version:
            # get a previous version of the note
            self.log('Fetching version v{0} of note (key={1})'.
                     format(version, self.key))
            version_note = self.ndb.get_note_version(self.key, version)
            if not version_note:
                self.log('Failed to get version v{0} of note (key={1})'.
                         format(version, self.key))
                # don't do anything, keep current note/version
            else:
                self.old_note = version_note

        self.body[:] = \
            urwid.SimpleFocusListWalker(self.get_note_content_as_list())
        if not self.search_string:
            self.focus_position = 0

    def lines_after_current_position(self):
        lines_after_current_position = list(range(self.focus_position + 1, len(self.body.positions()) - 1))
        return lines_after_current_position

    def lines_before_current_position(self):
        lines_before_current_position = list(range(0, self.focus_position))
        lines_before_current_position.reverse()
        return lines_before_current_position

    def search_note_view_next(self, search_string=None, search_mode=None):
        if search_string:
            self.search_string = search_string
        if search_mode:
            self.search_mode = search_mode
        note_range = self.lines_after_current_position() if self.search_direction == 'forward' else self.lines_before_current_position()
        self.search_note_range(note_range)

    def search_note_view_prev(self, search_string=None, search_mode=None):
        if search_string:
            self.search_string = search_string
        if search_mode:
            self.search_mode = search_mode
        note_range = self.lines_after_current_position() if self.search_direction == 'backward' else self.lines_before_current_position()
        self.search_note_range(note_range)

    def search_note_range(self, note_range):
        for line in note_range:
            line_content = self.note['content'].split('\n')[line]
            if (self.is_match(self.search_string, line_content)):
                self.focus_position = line
                break
        self.update_note_view()

    def is_match(self, term, full_text):
        if self.search_mode == 'gstyle':
            return term in full_text
        else:
            sspat = utils.build_regex_search(term)
            return sspat and sspat.search(full_text)

    def get_status_bar(self):
        if not self.key:
            return \
                urwid.AttrMap(urwid.Text('No note...'),
                              'status_bar')

        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        if self.old_note:
            t = time.localtime(float(self.old_note['modificationDate']))
            title    = utils.get_note_title(self.old_note)
            version  = self.old_note['version']
        else:
            t = time.localtime(float(self.note['modificationDate']))
            title    = utils.get_note_title(self.note)
            flags    = utils.get_note_flags(self.note)
            tags     = utils.get_note_tags(self.note)
            version  = self.note.get('version', 0)

        mod_time = time.strftime('Date: %a, %d %b %Y %H:%M:%S', t)

        status_title = \
            urwid.AttrMap(urwid.Text('Title: ' +
                                     title,
                                     wrap='clip'),
                          'status_bar')

        status_key_index = \
            ('pack', urwid.AttrMap(urwid.Text(' [' + 
                                              self.key + 
                                              '] ' +
                                              str(cur + 1) +
                                              '/' +
                                              str(total)),
                                   'status_bar'))

        status_date = \
            urwid.AttrMap(urwid.Text(mod_time,
                                     wrap='clip'),
                          'status_bar')

        if self.old_note:
            status_tags_flags = \
                ('pack', urwid.AttrMap(urwid.Text('[OLD:v' + 
                                                  str(version) + 
                                                  ']'),
                                       'status_bar'))
        else:
            status_tags_flags = \
                ('pack', urwid.AttrMap(urwid.Text('[' + 
                                                  tags + 
                                                  '] [v' + 
                                                  str(version) + 
                                                  '] [' + 
                                                  flags + 
                                                  ']'),
                                       'status_bar'))

        pile_top = urwid.Columns([ status_title, status_key_index ])
        pile_bottom = urwid.Columns([ status_date, status_tags_flags ])

        if self.old_note or \
           not (utils.note_published(self.note) and 'publishkey' in self.note):
            return urwid.AttrMap(urwid.Pile([ pile_top, pile_bottom ]),
                                 'status_bar')

        pile_publish = \
            urwid.AttrMap(urwid.Text('Published: http://simp.ly/publish/' +
                                     self.note['publishkey']),
                          'status_bar')
        return \
            urwid.AttrMap(urwid.Pile([ pile_top, pile_bottom, pile_publish ]),
                          'status_bar')

    def copy_note_text(self):
        line_content = self.note['content'].split('\n')[self.focus_position]
        self.clipboard.copy(line_content)

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
