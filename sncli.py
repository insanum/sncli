#!/usr/bin/env python2

import os, sys, re, signal, time, datetime, logging
import copy, json, urwid, datetime, ConfigParser
import utils
from simplenote import Simplenote
from notes_db import NotesDB, SyncError, ReadError, WriteError
from logging.handlers import RotatingFileHandler

class Config:

    def __init__(self):
        self.home = os.path.abspath(os.path.expanduser('~'))
        defaults = {
                    'sn_username'             : '',
                    'sn_password'             : '',
                    'db_path'                 : os.path.join(self.home, '.sncli'),
                    'search_mode'             : 'gstyle',
                    'search_tags'             : '1',
                    'sort_mode'               : '1',
                    'pinned_ontop'            : '1',
                    'tabstop'                 : '4',
                    'format_strftime'         : '%Y/%m/%d',
                    'format_note_title'       : '[%D] %F %N%>%T',

                    'kb_help'                 : 'h',
                    'kb_quit'                 : 'q',
                    'kb_down'                 : 'j',
                    'kb_up'                   : 'k',
                    'kb_page_down'            : ' ',
                    'kb_page_up'              : 'b',
                    'kb_half_page_down'       : 'ctrl d',
                    'kb_half_page_up'         : 'ctrl u',
                    'kb_bottom'               : 'G',
                    'kb_top'                  : 'g',
                    'kb_view_note'            : 'enter',
                    'kb_view_log'             : 'l',
                    'kb_tabstop2'             : '2',
                    'kb_tabstop4'             : '4',
                    'kb_tabstop8'             : '8',

                    'clr_default_fg'          : 'default',
                    'clr_default_bg'          : 'default',

                    'clr_note_title_day_fg'       : 'dark blue',
                    'clr_note_title_day_bg'       : 'default',
                    'clr_note_title_day_focus_fg' : 'white',
                    'clr_note_title_day_focus_bg' : 'default',

                    'clr_note_title_week_fg'       : 'dark blue',
                    'clr_note_title_week_bg'       : 'default',
                    'clr_note_title_week_focus_fg' : 'white',
                    'clr_note_title_week_focus_bg' : 'default',

                    'clr_note_title_month_fg'       : 'dark blue',
                    'clr_note_title_month_bg'       : 'default',
                    'clr_note_title_month_focus_fg' : 'white',
                    'clr_note_title_month_focus_bg' : 'default',

                    'clr_note_title_year_fg'       : 'dark blue',
                    'clr_note_title_year_bg'       : 'default',
                    'clr_note_title_year_focus_fg' : 'white',
                    'clr_note_title_year_focus_bg' : 'default',

                    'clr_note_title_ancient_fg'       : 'dark blue',
                    'clr_note_title_ancient_bg'       : 'default',
                    'clr_note_title_ancient_focus_fg' : 'white',
                    'clr_note_title_ancient_focus_bg' : 'default',

                    'clr_note_date_fg'        : 'dark blue',
                    'clr_note_date_bg'        : 'default',
                    'clr_note_date_focus_fg'  : 'white',
                    'clr_note_date_focus_bg'  : 'default',

                    'clr_note_flags_fg'       : 'dark blue',
                    'clr_note_flags_bg'       : 'default',
                    'clr_note_flags_focus_fg' : 'white',
                    'clr_note_flags_focus_bg' : 'default',

                    'clr_note_tags_fg'        : 'dark blue',
                    'clr_note_tags_bg'        : 'default',
                    'clr_note_tags_focus_fg'  : 'white',
                    'clr_note_tags_focus_bg'  : 'default',

                    'clr_note_content_fg'       : 'default',
                    'clr_note_content_bg'       : 'default',
                    'clr_note_content_focus_fg' : 'white',
                    'clr_note_content_focus_bg' : 'light red',

                    'clr_help_header_fg'      : 'dark blue',
                    'clr_help_header_bg'      : 'default',
                    'clr_help_key_fg'         : 'default',
                    'clr_help_key_bg'         : 'default',
                    'clr_help_config_fg'      : 'dark green',
                    'clr_help_config_bg'      : 'default',
                    'clr_help_descr_fg'       : 'default',
                    'clr_help_descr_bg'       : 'default'
                   }

        cp = ConfigParser.SafeConfigParser(defaults)
        self.configs_read = cp.read([os.path.join(self.home, '.snclirc')])

        cfg_sec = 'sncli'

        if not cp.has_section(cfg_sec):
            cp.add_section(cfg_sec)
            self.ok = False
        else:
            self.ok = True

        self.sn_username       = cp.get(cfg_sec,    'sn_username', raw=True)
        self.sn_password       = cp.get(cfg_sec,    'sn_password', raw=True)
        self.db_path           = cp.get(cfg_sec,    'db_path')
        self.search_mode       = cp.get(cfg_sec,    'search_mode')
        self.search_tags       = cp.getint(cfg_sec, 'search_tags')
        self.sort_mode         = cp.getint(cfg_sec, 'sort_mode')
        self.pinned_ontop      = cp.getint(cfg_sec, 'pinned_ontop')
        self.tabstop           = cp.getint(cfg_sec, 'tabstop')
        self.format_strftime   = cp.get(cfg_sec,    'format_strftime',   raw=True)
        self.format_note_title = cp.get(cfg_sec,    'format_note_title', raw=True)

        self.clr_default_fg          = cp.get(cfg_sec, 'clr_default_fg')
        self.clr_default_bg          = cp.get(cfg_sec, 'clr_default_bg')

        self.clr_note_title_day_fg       = cp.get(cfg_sec, 'clr_note_title_day_fg')
        self.clr_note_title_day_bg       = cp.get(cfg_sec, 'clr_note_title_day_bg')
        self.clr_note_title_day_focus_fg = cp.get(cfg_sec, 'clr_note_title_day_focus_fg')
        self.clr_note_title_day_focus_bg = cp.get(cfg_sec, 'clr_note_title_day_focus_bg')

        self.clr_note_title_week_fg       = cp.get(cfg_sec, 'clr_note_title_week_fg')
        self.clr_note_title_week_bg       = cp.get(cfg_sec, 'clr_note_title_week_bg')
        self.clr_note_title_week_focus_fg = cp.get(cfg_sec, 'clr_note_title_week_focus_fg')
        self.clr_note_title_week_focus_bg = cp.get(cfg_sec, 'clr_note_title_week_focus_bg')

        self.clr_note_title_month_fg       = cp.get(cfg_sec, 'clr_note_title_month_fg')
        self.clr_note_title_month_bg       = cp.get(cfg_sec, 'clr_note_title_month_bg')
        self.clr_note_title_month_focus_fg = cp.get(cfg_sec, 'clr_note_title_month_focus_fg')
        self.clr_note_title_month_focus_bg = cp.get(cfg_sec, 'clr_note_title_month_focus_bg')

        self.clr_note_title_year_fg       = cp.get(cfg_sec, 'clr_note_title_year_fg')
        self.clr_note_title_year_bg       = cp.get(cfg_sec, 'clr_note_title_year_bg')
        self.clr_note_title_year_focus_fg = cp.get(cfg_sec, 'clr_note_title_year_focus_fg')
        self.clr_note_title_year_focus_bg = cp.get(cfg_sec, 'clr_note_title_year_focus_bg')

        self.clr_note_title_ancient_fg       = cp.get(cfg_sec, 'clr_note_title_ancient_fg')
        self.clr_note_title_ancient_bg       = cp.get(cfg_sec, 'clr_note_title_ancient_bg')
        self.clr_note_title_ancient_focus_fg = cp.get(cfg_sec, 'clr_note_title_ancient_focus_fg')
        self.clr_note_title_ancient_focus_bg = cp.get(cfg_sec, 'clr_note_title_ancient_focus_bg')

        self.clr_note_date_fg        = cp.get(cfg_sec, 'clr_note_date_fg')
        self.clr_note_date_bg        = cp.get(cfg_sec, 'clr_note_date_bg')
        self.clr_note_date_focus_fg  = cp.get(cfg_sec, 'clr_note_date_focus_fg')
        self.clr_note_date_focus_bg  = cp.get(cfg_sec, 'clr_note_date_focus_bg')

        self.clr_note_flags_fg       = cp.get(cfg_sec, 'clr_note_flags_fg')
        self.clr_note_flags_bg       = cp.get(cfg_sec, 'clr_note_flags_bg')
        self.clr_note_flags_focus_fg = cp.get(cfg_sec, 'clr_note_flags_focus_fg')
        self.clr_note_flags_focus_bg = cp.get(cfg_sec, 'clr_note_flags_focus_bg')

        self.clr_note_tags_fg        = cp.get(cfg_sec, 'clr_note_tags_fg')
        self.clr_note_tags_bg        = cp.get(cfg_sec, 'clr_note_tags_bg')
        self.clr_note_tags_focus_fg  = cp.get(cfg_sec, 'clr_note_tags_focus_fg')
        self.clr_note_tags_focus_bg  = cp.get(cfg_sec, 'clr_note_tags_focus_bg')

        self.clr_note_content_fg       = cp.get(cfg_sec, 'clr_note_content_fg')
        self.clr_note_content_bg       = cp.get(cfg_sec, 'clr_note_content_bg')
        self.clr_note_content_focus_fg = cp.get(cfg_sec, 'clr_note_content_focus_fg')
        self.clr_note_content_focus_bg = cp.get(cfg_sec, 'clr_note_content_focus_bg')

        self.clr_help_header_fg      = cp.get(cfg_sec, 'clr_help_header_fg')
        self.clr_help_header_bg      = cp.get(cfg_sec, 'clr_help_header_bg')
        self.clr_help_key_fg         = cp.get(cfg_sec, 'clr_help_key_fg')
        self.clr_help_key_bg         = cp.get(cfg_sec, 'clr_help_key_bg')
        self.clr_help_config_fg      = cp.get(cfg_sec, 'clr_help_config_fg')
        self.clr_help_config_bg      = cp.get(cfg_sec, 'clr_help_config_bg')
        self.clr_help_descr_fg       = cp.get(cfg_sec, 'clr_help_descr_fg')
        self.clr_help_descr_bg       = cp.get(cfg_sec, 'clr_help_descr_bg')

        self.keybinds = \
            {
              'help'           : [ cp.get(cfg_sec, 'kb_help'),           'Help' ],
              'quit'           : [ cp.get(cfg_sec, 'kb_quit'),           'Quit' ],
              'down'           : [ cp.get(cfg_sec, 'kb_down'),           'Scroll down one line' ],
              'up'             : [ cp.get(cfg_sec, 'kb_up'),             'Scroll up one line' ],
              'page_down'      : [ cp.get(cfg_sec, 'kb_page_down'),      'Page down' ],
              'page_up'        : [ cp.get(cfg_sec, 'kb_page_up'),        'Page up' ],
              'half_page_down' : [ cp.get(cfg_sec, 'kb_half_page_down'), 'Half page down' ],
              'half_page_up'   : [ cp.get(cfg_sec, 'kb_half_page_up'),   'Half page up' ],
              'bottom'         : [ cp.get(cfg_sec, 'kb_bottom'),         'Goto bottom' ],
              'top'            : [ cp.get(cfg_sec, 'kb_top'),            'Goto top' ],
              'view_note'      : [ cp.get(cfg_sec, 'kb_view_note'),      'View note' ],
              'view_log'       : [ cp.get(cfg_sec, 'kb_view_log'),       'View log' ],
              'tabstop2'       : [ cp.get(cfg_sec, 'kb_tabstop2'),       'View with tabstop=2' ],
              'tabstop4'       : [ cp.get(cfg_sec, 'kb_tabstop4'),       'View with tabstop=4' ],
              'tabstop8'       : [ cp.get(cfg_sec, 'kb_tabstop8'),       'View with tabstop=8' ]
            }

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
            print e
            exit(1)

        self.last_view = []

        # XXX
        self.all_notes, match_regex, self.all_notes_cnt = self.ndb.filter_notes()
        return

        self.ndb.add_observer('synced:note', self.observer_notes_db_synced_note)
        self.ndb.add_observer('change:note-status', self.observer_notes_db_change_note_status)
        self.ndb.add_observer('progress:sync_full', self.observer_notes_db_sync_full)
        self.sync_full()

        self.all_notes, match_regex, self.all_notes_cnt = self.ndb.filter_notes()

    def do_it(self):

        def list_get_note_titles():
            lines = []
            for n in self.all_notes:
                #lines.append(
                #    urwid.Text(('note_title_day', utils.get_note_title(n.note))))
                lines.append(
                    urwid.AttrMap(urwid.Text(utils.get_note_title(n.note)),
                                  'note_title_day', 'note_title_day_focus'))
            return lines

        def list_get_note_content(index, tabstop):
            lines = []
            for l in self.all_notes[index].note['content'].split('\n'):
                lines.append(
                    urwid.AttrMap(urwid.Text(l.replace('\t', ' ' * tabstop)),
                                  'note_content',
                                  'note_content_focus'))
            return lines

        def list_get_note_json(index):
            return self.all_notes[index].note

        def get_config():
            return self.config

        def push_last_view(view):
            self.last_view.append(view)

        def pop_last_view():
            return self.last_view.pop()

        def get_logfile():
            return self.logfile

        def handle_common_scroll_keybind(obj, size, key):

            if key == self.config.keybinds['down'][0]:
                last = len(obj.body.positions())
                if obj.focus_position == (last - 1):
                    return
                obj.focus_position += 1
                obj.render(size)

            elif key == self.config.keybinds['up'][0]:
                if obj.focus_position == 0:
                    return
                obj.focus_position -= 1
                obj.render(size)

            elif key == self.config.keybinds['page_down'][0]:
                last = len(obj.body.positions())
                next_focus = obj.focus_position + size[1]
                if next_focus >= last:
                    next_focus = last - 1
                obj.change_focus(size, next_focus,
                                 offset_inset=0,
                                 coming_from='above')

            elif key == self.config.keybinds['page_up'][0]:
                if 'bottom' in obj.ends_visible(size):
                    last = len(obj.body.positions())
                    next_focus = last - size[1] - size[1]
                else:
                    next_focus = obj.focus_position - size[1]
                if next_focus < 0:
                    next_focus = 0
                obj.change_focus(size, next_focus,
                                 offset_inset=0,
                                 coming_from='below')

            elif key == self.config.keybinds['half_page_down'][0]:
                last = len(obj.body.positions())
                next_focus = obj.focus_position + (size[1] / 2)
                if next_focus >= last:
                    next_focus = last - 1
                obj.change_focus(size, next_focus,
                                 offset_inset=0,
                                 coming_from='above')

            elif key == self.config.keybinds['half_page_up'][0]:
                if 'bottom' in obj.ends_visible(size):
                    last = len(obj.body.positions())
                    next_focus = last - size[1] - (size[1] / 2)
                else:
                    next_focus = obj.focus_position - (size[1] / 2)
                if next_focus < 0:
                    next_focus = 0
                obj.change_focus(size, next_focus,
                                 offset_inset=0,
                                 coming_from='below')

            elif key == self.config.keybinds['bottom'][0]:
                obj.change_focus(size, (len(obj.body.positions()) - 1),
                                 offset_inset=0,
                                 coming_from='above')

            elif key == self.config.keybinds['top'][0]:
                obj.change_focus(size, 0,
                                 offset_inset=0,
                                 coming_from='below')

        class NoteTitles(urwid.ListBox):
            def __init__(self):
                self.keybinds = get_config().keybinds
                body = urwid.SimpleFocusListWalker(list_get_note_titles())
                super(NoteTitles, self).__init__(body)

            def keypress(self, size, key):
                if key == self.keybinds['quit'][0]:
                    raise urwid.ExitMainLoop()

                elif key == self.keybinds['help'][0]:
                    push_last_view(self)
                    sncli_loop.widget = Help()

                elif key == self.keybinds['view_log'][0]:
                    push_last_view(self)
                    sncli_loop.widget = ViewLog()

                elif key == self.keybinds['view_note'][0]:
                    push_last_view(self)
                    sncli_loop.widget = NoteContent(self.focus_position, get_config().tabstop)

                else:
                    handle_common_scroll_keybind(self, size, key)

        class NoteContent(urwid.ListBox):
            def __init__(self, nl_focus_index, tabstop):
                self.keybinds = get_config().keybinds
                self.nl_focus_index = nl_focus_index
                body = \
                    urwid.SimpleFocusListWalker(
                            list_get_note_content(self.nl_focus_index, tabstop))
                self.note = list_get_note_json(self.nl_focus_index)
                super(NoteContent, self).__init__(body)

            def keypress(self, size, key):
                if key == self.keybinds['quit'][0]:
                    sncli_loop.widget = pop_last_view()

                elif key == self.keybinds['help'][0]:
                    push_last_view(self)
                    sncli_loop.widget = Help()

                elif key == self.keybinds['view_log'][0]:
                    push_last_view(self)
                    sncli_loop.widget = ViewLog()

                elif key == self.keybinds['tabstop2'][0]:
                    sncli_loop.widget = NoteContent(self.nl_focus_index, 2)

                elif key == self.keybinds['tabstop4'][0]:
                    sncli_loop.widget = NoteContent(self.nl_focus_index, 4)

                elif key == self.keybinds['tabstop8'][0]:
                    sncli_loop.widget = NoteContent(self.nl_focus_index, 8)

                else:
                    handle_common_scroll_keybind(self, size, key)

        class ViewLog(urwid.ListBox):
            def __init__(self):
                self.keybinds = get_config().keybinds
                f = open(get_logfile())
                lines = []
                for line in f:
                    lines.append(
                        urwid.AttrMap(urwid.Text(line.rstrip()),
                                      'note_content',
                                      'note_content_focus'))
                f.close()
                body = urwid.SimpleFocusListWalker(lines)
                super(ViewLog, self).__init__(body)

            def keypress(self, size, key):
                if key == self.keybinds['quit'][0]:
                    sncli_loop.widget = pop_last_view()

                elif key == self.keybinds['help'][0]:
                    push_last_view(self)
                    sncli_loop.widget = Help()

                else:
                    handle_common_scroll_keybind(self, size, key)

        class Help(urwid.ListBox):
            def __init__(self):
                self.keybinds = get_config().keybinds

                lines = []

                # Common keybinds
                keys = [ 'help',
                         'quit',
                         'down',
                         'up',
                         'page_down',
                         'page_up',
                         'half_page_down',
                         'half_page_up',
                         'bottom',
                         'top',
                         'view_log' ]
                lines.extend(self.create_help_lines(u"Common", keys))

                # NoteTitles keybinds
                keys = [ 'view_note' ]
                lines.extend(self.create_help_lines(u"Note List", keys))

                # NoteContent keybinds
                keys = [ 'tabstop2',
                         'tabstop4',
                         'tabstop8' ]
                lines.extend(self.create_help_lines(u"Note Content", keys))

                lines.append(urwid.Text(('help_header', u'')))

                body = urwid.SimpleFocusListWalker(lines)
                super(Help, self).__init__(body)

            def create_help_lines(self, header, keys):
                lines = [ urwid.Text(('help_header', u'')) ]
                lines.append(urwid.Text( [ u' ', ('help_header', header) ] ))
                for k in keys:
                    lines.append(
                        urwid.Text(
                          [
                            ('help_key', '{:>20}  '.format(u"'" + self.keybinds[k][0] + u"'")),
                            '  ',
                            ('help_config', '{:<20}  '.format(u'kb_' + k)),
                            '  ',
                            ('help_descr', self.keybinds[k][1])
                          ]
                        ))
                return lines

            def keypress(self, size, key):

                if key == self.keybinds['quit'][0]:
                    sncli_loop.widget = pop_last_view()

                elif key == self.keybinds['down'][0]:
                    key = super(Help, self).keypress(size, 'down')
                    return

                elif key == self.keybinds['up'][0]:
                    key = super(Help, self).keypress(size, 'up')
                    return

                else:
                    handle_common_scroll_keybind(self, size, key)

        palette = [
                    ('default',
                        self.config.clr_default_fg,
                        self.config.clr_default_bg ),
                    ('note_title_day',
                        self.config.clr_note_title_day_fg,
                        self.config.clr_note_title_day_bg ),
                    ('note_title_day_focus',
                        self.config.clr_note_title_day_focus_fg,
                        self.config.clr_note_title_day_focus_bg ),
                    ('note_title_week',
                        self.config.clr_note_title_week_fg,
                        self.config.clr_note_title_week_bg ),
                    ('note_title_week_focus',
                        self.config.clr_note_title_week_focus_fg,
                        self.config.clr_note_title_week_focus_bg ),
                    ('note_title_month',
                        self.config.clr_note_title_month_fg,
                        self.config.clr_note_title_month_bg ),
                    ('note_title_month_focus',
                        self.config.clr_note_title_month_focus_fg,
                        self.config.clr_note_title_month_focus_bg ),
                    ('note_title_year',
                        self.config.clr_note_title_year_fg,
                        self.config.clr_note_title_year_bg ),
                    ('note_title_year_focus',
                        self.config.clr_note_title_year_focus_fg,
                        self.config.clr_note_title_year_focus_bg ),
                    ('note_title_ancient',
                        self.config.clr_note_title_ancient_fg,
                        self.config.clr_note_title_ancient_bg ),
                    ('note_title_ancient_focus',
                        self.config.clr_note_title_ancient_focus_fg,
                        self.config.clr_note_title_ancient_focus_bg ),
                    ('note_date',
                        self.config.clr_note_date_fg,
                        self.config.clr_note_date_bg ),
                    ('note_date_focus',
                        self.config.clr_note_date_focus_fg,
                        self.config.clr_note_date_focus_bg ),
                    ('note_flags',
                        self.config.clr_note_flags_fg,
                        self.config.clr_note_flags_bg ),
                    ('note_flags_focus',
                        self.config.clr_note_flags_focus_fg,
                        self.config.clr_note_flags_focus_bg ),
                    ('note_tags',
                        self.config.clr_note_tags_fg,
                        self.config.clr_note_tags_bg ),
                    ('note_tags_focus',
                        self.config.clr_note_tags_focus_fg,
                        self.config.clr_note_tags_focus_bg ),
                    ('note_content',
                        self.config.clr_note_content_fg,
                        self.config.clr_note_content_bg ),
                    ('note_content_focus',
                        self.config.clr_note_content_focus_fg,
                        self.config.clr_note_content_focus_bg ),
                    ('help_header',
                        self.config.clr_help_header_fg,
                        self.config.clr_help_header_bg ),
                    ('help_key',
                        self.config.clr_help_key_fg,
                        self.config.clr_help_key_bg ),
                    ('help_config',
                        self.config.clr_help_config_fg,
                        self.config.clr_help_config_bg ),
                    ('help_descr',
                        self.config.clr_help_descr_fg,
                        self.config.clr_help_descr_bg )
                  ]

        sncli_loop = urwid.MainLoop(NoteTitles(),
                                    palette,
                                    handle_mouse=False)
        sncli_loop.run()

    def sync_full(self):
        try:
            sync_from_server_errors = self.ndb.sync_full()
        except Exception, e:
            print e
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
        print "observer_notes_db_synced_note: " + evt.msg

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
    sncli().do_it()

if __name__ == '__main__':
    main()

