#!/usr/bin/env python2

import os, sys, re, signal, time, datetime, logging
import copy, json, urwid, datetime
import utils
from config import Config
from simplenote import Simplenote
from notes_db import NotesDB, SyncError, ReadError, WriteError
from logging.handlers import RotatingFileHandler

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

    def sync_full(self):
        try:
            sync_from_server_errors = self.ndb.sync_full()
        except Exception, e:
            print e
            exit(1)
        else:
            if sync_from_server_errors > 0:
                print('Error syncing %d notes from server. Please check sncli.log for details.' % (sync_from_server_errors))

    def observer_notes_db_change_note_status(self, ndb, evt_type, evt):
        logging.debug(evt.msg)
        # XXX set status text someplace visible
        skey = self.get_selected_note_key()
        if skey == evt.key:
            print self.ndb.get_note_status(skey)

    def observer_notes_db_sync_full(self, ndb, evt_type, evt):
        logging.debug(evt.msg)
        # XXX set status text someplace visible
        print evt.msg 

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

    def ba_bam_what(self):

        def format_title(note):
            """
            Various formatting tags are supporting for dynamically building
            the title string. Each of these formatting tags supports a width
            specifier (decimal) and a left justification (-) like that
            supported by printf.

            %F -- flags ('*' for pinned, 'm' for markdown)
            %T -- tags
            %D -- date
            %N -- note title
            """

            title = utils.get_note_title(note)

            # get the note flags
            if note.has_key("systemtags"):
                flags = ''
                if ('pinned' in note['systemtags']):   flags = flags + u'*'
                else:                                  flags = flags + u' '
                if ('markdown' in note['systemtags']): flags = flags + u'm'
                else:                                  flags = flags + u' '
            else:
                flags = '  '

            # get the note tags
            tags = '%s' % ','.join(note['tags'])

            # format the note modification date
            t = time.localtime(float(note['modifydate']))
            mod_time = time.strftime(self.config.format_strftime, t)

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
            title_line = recursive_format(self.config.format_note_title)
            return urwid.Columns(title_line)

        def list_get_note_titles():
            lines = []
            for n in self.all_notes:
                lines.append(
                    urwid.AttrMap(format_title(n.note),
                                  'default',
                                  { 'default'            : 'note_focus',
                                    'note_title_day'     : 'note_focus',
                                    'note_title_week'    : 'note_focus',
                                    'note_title_month'   : 'note_focus',
                                    'note_title_year'    : 'note_focus',
                                    'note_title_ancient' : 'note_focus',
                                    'note_date'          : 'note_focus',
                                    'note_flags'         : 'note_focus',
                                    'note_tags'          : 'note_focus' }))
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

        def get_logfile():
            return self.logfile

        def push_last_view(view):
            self.last_view.append(view)

        def pop_last_view():
            return self.last_view.pop()

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
                lines = [ urwid.AttrMap(urwid.Text(u''),
                                        'help_header',
                                        'help_focus') ]
                lines.append(urwid.AttrMap(urwid.Text(u' ' + header),
                                           'help_header',
                                           'help_focus'))
                for k in keys:
                    lines.append(
                        urwid.AttrMap(
                          urwid.Text(
                            [
                              ('help_key', '{:>20}  '.format(u"'" + self.keybinds[k][0] + u"'")),
                              ('help_config', '{:<20}  '.format(u'kb_' + k)),
                              ('help_descr', self.keybinds[k][1])
                            ]
                          ),
                          attr_map = None,
                          focus_map = {
                                        'help_key'    : 'help_focus',
                                        'help_config' : 'help_focus',
                                        'help_descr'  : 'help_focus'
                                      }
                        ))
                return lines

            def keypress(self, size, key):
                if key == self.keybinds['quit'][0]:
                    sncli_loop.widget = pop_last_view()

                else:
                    handle_common_scroll_keybind(self, size, key)

        palette = \
          [
            ('default',
                self.config.clr_default_fg,
                self.config.clr_default_bg ),
            ('note_focus',
                self.config.clr_note_focus_fg,
                self.config.clr_note_focus_bg ),
            ('note_title_day',
                self.config.clr_note_title_day_fg,
                self.config.clr_note_title_day_bg ),
            ('note_title_week',
                self.config.clr_note_title_week_fg,
                self.config.clr_note_title_week_bg ),
            ('note_title_month',
                self.config.clr_note_title_month_fg,
                self.config.clr_note_title_month_bg ),
            ('note_title_year',
                self.config.clr_note_title_year_fg,
                self.config.clr_note_title_year_bg ),
            ('note_title_ancient',
                self.config.clr_note_title_ancient_fg,
                self.config.clr_note_title_ancient_bg ),
            ('note_date',
                self.config.clr_note_date_fg,
                self.config.clr_note_date_bg ),
            ('note_flags',
                self.config.clr_note_flags_fg,
                self.config.clr_note_flags_bg ),
            ('note_tags',
                self.config.clr_note_tags_fg,
                self.config.clr_note_tags_bg ),
            ('note_content',
                self.config.clr_note_content_fg,
                self.config.clr_note_content_bg ),
            ('note_content_focus',
                self.config.clr_note_content_focus_fg,
                self.config.clr_note_content_focus_bg ),
            ('help_focus',
                self.config.clr_help_focus_fg,
                self.config.clr_help_focus_bg ),
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


def SIGINT_handler(signum, frame):
    print('\nSignal caught, bye!')
    sys.exit(1)

signal.signal(signal.SIGINT, SIGINT_handler)

def main():
    sncli().ba_bam_what()

if __name__ == '__main__':
    main()

