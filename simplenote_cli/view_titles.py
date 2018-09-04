
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import re, time, datetime, urwid, subprocess
from . import utils, view_note

class ViewTitles(urwid.ListBox):

    def __init__(self, config, args):
        self.config = config
        self.ndb = args['ndb']
        self.search_string = args['search_string']
        self.log = args['log']
        self.note_list, self.match_regex, self.all_notes_cnt = \
            self.ndb.filter_notes(self.search_string, sort_mode=self.config.get_config('sort_mode'))
        super(ViewTitles, self).__init__(
                  urwid.SimpleFocusListWalker(self.get_note_titles()))

    def update_note_list(self, search_string, search_mode='gstyle', sort_mode='date'):
        self.search_string = search_string
        self.note_list, self.match_regex, self.all_notes_cnt = \
            self.ndb.filter_notes(self.search_string, search_mode, sort_mode=sort_mode)
        self.body[:] = \
            urwid.SimpleFocusListWalker(self.get_note_titles())
        if len(self.note_list) == 0:
            self.log('No notes found!')
        else:
            self.focus_position = 0

    def sort_note_list(self, sort_mode):
        self.ndb.filtered_notes_sort(self.note_list, sort_mode)
        self.body[:] = \
            urwid.SimpleFocusListWalker(self.get_note_titles())

    def format_title(self, note):
        """
        Various formatting tags are supported for dynamically building
        the title string. Each of these formatting tags supports a width
        specifier (decimal) and a left justification (-) like that
        supported by printf.

        %F -- flags
        %T -- tags
        %D -- date
        %N -- note title
        """

        t = time.localtime(float(note['modificationDate']))
        mod_time = time.strftime(self.config.get_config('format_strftime'), t)
        title = utils.get_note_title(note)
        flags = utils.get_note_flags(note)
        tags  = utils.get_note_tags(note)

        # get the age of the note
        dt = datetime.datetime.fromtimestamp(time.mktime(t))
        if dt > datetime.datetime.now() - datetime.timedelta(days=1):
            note_age = 'd' # less than a day old
        elif dt > datetime.datetime.now() - datetime.timedelta(weeks=1):
            note_age = 'w' # less than a week old
        elif dt > datetime.datetime.now() - datetime.timedelta(weeks=4):
            note_age = 'm' # less than a month old
        elif dt > datetime.datetime.now() - datetime.timedelta(weeks=52):
            note_age = 'y' # less than a year old
        else:
            note_age = 'a' # ancient

        def recursive_format(title_format):
            if not title_format:
                return None
            fmt = re.search("^(.*)%([-]*)([0-9]*)([FDTN])(.*)$", title_format)
            if not fmt:
                m = ('pack', urwid.AttrMap(urwid.Text(title_format),
                                           'default'))
                l_fmt = None
                r_fmt = None
            else:
                l = fmt.group(1) if fmt.group(1) else None
                m = None
                r = fmt.group(5) if fmt.group(5) else None
                align = 'left' if fmt.group(2) == '-' else 'right'
                width = int(fmt.group(3)) if fmt.group(3) else 'pack'
                if fmt.group(4) == 'F':
                    m = (width, urwid.AttrMap(urwid.Text(flags,
                                                         align=align,
                                                         wrap='clip'),
                                              'note_flags'))
                elif fmt.group(4) == 'D':
                    m = (width, urwid.AttrMap(urwid.Text(mod_time,
                                                         align=align,
                                                         wrap='clip'),
                                              'note_date'))
                elif fmt.group(4) == 'T':
                    m = (width, urwid.AttrMap(urwid.Text(tags,
                                                         align=align,
                                                         wrap='clip'),
                                              'note_tags'))
                elif fmt.group(4) == 'N':
                    if   note_age == 'd': attr = 'note_title_day'
                    elif note_age == 'w': attr = 'note_title_week'
                    elif note_age == 'm': attr = 'note_title_month'
                    elif note_age == 'y': attr = 'note_title_year'
                    elif note_age == 'a': attr = 'note_title_ancient'
                    if width != 'pack':
                        m = (width, urwid.AttrMap(urwid.Text(title,
                                                             align=align,
                                                             wrap='clip'),
                                                  attr))
                    else:
                        m = urwid.AttrMap(urwid.Text(title,
                                                     align=align,
                                                     wrap='clip'),
                                          attr)
                l_fmt = recursive_format(l)
                r_fmt = recursive_format(r)

            tmp = []
            if l_fmt: tmp.extend(l_fmt)
            tmp.append(m)
            if r_fmt: tmp.extend(r_fmt)
            return tmp

        # convert the format string into the actual note title line
        title_line = recursive_format(self.config.get_config('format_note_title'))
        return urwid.Columns(title_line)

    def get_note_title(self, note):
        return urwid.AttrMap(self.format_title(note),
                             'default',
                             { 'default'            : 'note_focus',
                               'note_title_day'     : 'note_focus',
                               'note_title_week'    : 'note_focus',
                               'note_title_month'   : 'note_focus',
                               'note_title_year'    : 'note_focus',
                               'note_title_ancient' : 'note_focus',
                               'note_date'          : 'note_focus',
                               'note_flags'         : 'note_focus',
                               'note_tags'          : 'note_focus' })

    def get_note_titles(self):
        lines = []
        for n in self.note_list:
            lines.append(self.get_note_title(n.note))
        return lines

    def get_status_bar(self):
        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        hdr = 'Simplenote'

        # include simplenote connection status in header
        hdr += ' (' + self.ndb.simplenote.status + ')'

        if self.search_string != None:
            hdr += ' - Search: ' + self.search_string

        status_title = \
            urwid.AttrMap(urwid.Text(hdr,
                                     wrap='clip'),
                          'status_bar')
        status_index = \
            ('pack', urwid.AttrMap(urwid.Text(' ' +
                                              str(cur + 1) +
                                              '/' +
                                              str(total)),
                                   'status_bar'))
        return \
            urwid.AttrMap(urwid.Columns([ status_title, status_index ]),
                          'status_bar')

    def update_note_title(self, key=None):
        if not key:
            self.body[self.focus_position] = \
                self.get_note_title(self.note_list[self.focus_position].note)
        else:
            for i in range(len(self.note_list)):
                if self.note_list[i].note['localkey'] == key:
                    self.body[i] = self.get_note_title(self.note_list[i].note)

    def focus_note(self, key):
        for i in range(len(self.note_list)):
            if 'localkey' in self.note_list[i].note and \
               self.note_list[i].note['localkey'] == key:
                self.focus_position = i

    def keypress(self, size, key):
        return key

