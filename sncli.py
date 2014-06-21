#!/usr/bin/env python2

import os, sys, signal, time, logging, json, urwid, ConfigParser, utils
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
            print e
            exit(1)

        # XXX
        #self.all_notes, match_regex, self.all_notes_cnt = self.ndb.filter_notes()
        #return

        self.ndb.add_observer('synced:note', self.observer_notes_db_synced_note)
        self.ndb.add_observer('change:note-status', self.observer_notes_db_change_note_status)
        self.ndb.add_observer('progress:sync_full', self.observer_notes_db_sync_full)
        self.sync_full()

        self.all_notes, match_regex, self.all_notes_cnt = self.ndb.filter_notes()

    def do_it(self):

        #self.urwid_one()
        #self.urwid_two()
        #self.urwid_three()
        #self.urwid_four()
        #self.urwid_five()
        #self.urwid_six()
        #self.urwid_seven()
        #self.urwid_eight()
        #return

        def list_get_note_titles():
            note_titles = []
            for n in self.all_notes:
                note_titles.append(urwid.Text(('note_title', utils.get_note_title(n.note))))
            return note_titles

        def list_get_note(index):
            note_contents = []
            for l in self.all_notes[index].note['content'].split('\n'):
                note_contents.append(urwid.Text(('note_view', l)))
            return note_contents

        class NoteTitleListBox(urwid.ListBox):
            def __init__(self):
                body = urwid.SimpleFocusListWalker( list_get_note_titles() )
                super(NoteTitleListBox, self).__init__(body)
                self.focus.set_text(('note_title_focus', self.focus.text))

            def keypress(self, size, key):
                key = super(NoteTitleListBox, self).keypress(size, key)

                if key in ('q', 'Q'):
                    raise urwid.ExitMainLoop()

                elif key == 'j':
                    last = len(self.body.positions())
                    if self.focus_position == (last - 1):
                        return
                    self.focus.set_text(('note_title', self.focus.text))
                    self.focus_position = self.focus_position + 1
                    self.focus.set_text(('note_title_focus', self.focus.text))

                elif key == 'k':
                    if self.focus_position == 0:
                        return
                    self.focus.set_text(('note_title', self.focus.text))
                    self.focus_position = self.focus_position - 1
                    self.focus.set_text(('note_title_focus', self.focus.text))

                elif key == ' ':
                    last = len(self.body.positions())
                    next_focus = self.focus_position + size[1]
                    if next_focus >= last:
                        next_focus = last - 1
                    self.focus.set_text(('note_title', self.focus.text))
                    self.change_focus(size, next_focus,
                                      offset_inset=0,
                                      coming_from='above')
                    self.focus.set_text(('note_title_focus', self.focus.text))

                elif key == 'b':
                    if 'bottom' in self.ends_visible(size):
                        last = len(self.body.positions())
                        next_focus = last - size[1] - size[1]
                    else:
                        next_focus = self.focus_position - size[1]
                    if next_focus < 0:
                        next_focus = 0
                    self.focus.set_text(('note_title', self.focus.text))
                    self.change_focus(size, next_focus,
                                      offset_inset=0,
                                      coming_from='below')
                    self.focus.set_text(('note_title_focus', self.focus.text))

                elif key == 'ctrl d':
                    last = len(self.body.positions())
                    next_focus = self.focus_position + (size[1] / 2)
                    if next_focus >= last:
                        next_focus = last - 1
                    self.focus.set_text(('note_title', self.focus.text))
                    self.change_focus(size, next_focus,
                                      offset_inset=0,
                                      coming_from='above')
                    self.focus.set_text(('note_title_focus', self.focus.text))

                elif key == 'ctrl u':
                    if 'bottom' in self.ends_visible(size):
                        last = len(self.body.positions())
                        next_focus = last - size[1] - (size[1] / 2)
                    else:
                        next_focus = self.focus_position - (size[1] / 2)
                    if next_focus < 0:
                        next_focus = 0
                    self.focus.set_text(('note_title', self.focus.text))
                    self.change_focus(size, next_focus,
                                      offset_inset=0,
                                      coming_from='below')
                    self.focus.set_text(('note_title_focus', self.focus.text))

                elif key == 'enter':
                    sncli_loop.widget = NoteViewListBox(self.focus_position)

                else:
                    return key

        class NoteViewListBox(urwid.ListBox):
            def __init__(self, index):
                body = urwid.SimpleFocusListWalker( list_get_note(index) )
                super(NoteViewListBox, self).__init__(body)

            def keypress(self, size, key):
                key = super(NoteViewListBox, self).keypress(size, key)

                if key in ('q', 'Q'):
                    sncli_loop.widget = NoteTitleListBox()

                elif key in [ 'j', 'enter' ]:
                    key = super(NoteViewListBox, self).keypress(size, 'down')

                elif key == 'k':
                    key = super(NoteViewListBox, self).keypress(size, 'up')

                elif key == ' ':
                    key = super(NoteViewListBox, self).keypress(size, 'page down')

                elif key == 'b':
                    key = super(NoteViewListBox, self).keypress(size, 'page up')

                elif key == 'ctrl d':
                    last = len(self.body.positions())
                    next_focus = self.focus_position + (size[1] / 2)
                    if next_focus >= last:
                        next_focus = last - 1
                    self.change_focus(size, next_focus,
                                      offset_inset=0,
                                      coming_from='above')

                elif key == 'ctrl u':
                    if 'bottom' in self.ends_visible(size):
                        last = len(self.body.positions())
                        next_focus = last - size[1] - (size[1] / 2)
                    else:
                        next_focus = self.focus_position - (size[1] / 2)
                    if next_focus < 0:
                        next_focus = 0
                    self.change_focus(size, next_focus,
                                      offset_inset=0,
                                      coming_from='below')

                else:
                    return key

        palette = [
                    ('note_title_focus', 'black',    'dark red'),
                    ('note_title',       'dark red', 'default'),
                    ('note_view',        'default',  'default')
                  ]

        sncli_loop = urwid.MainLoop(NoteTitleListBox(),
                                    palette,
                                    handle_mouse=False)
        sncli_loop.run()

    def urwid_one(self):
        txt = urwid.Text(u"Hello World!")
        fill = urwid.Filler(txt, 'top')
        loop = urwid.MainLoop(fill)
        loop.run()

    def urwid_two(self):
        def show_or_exit(key):
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()
            txt.set_text(repr(key))

        txt = urwid.Text(u"Hello World!")
        fill = urwid.Filler(txt, 'top')
        loop = urwid.MainLoop(fill, unhandled_input=show_or_exit)
        loop.run()

    def urwid_three(self):
        def exit_on_q(key):
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()

        palette = [ ('banner', 'black', 'light gray'),
                    ('streak', 'black', 'dark red'),
                    ('bg',     'black', 'dark blue') ]

        txt = urwid.Text(('banner', u"Hello World!"), align='center')
        map1 = urwid.AttrMap(txt, 'streak')
        fill = urwid.Filler(map1)
        map2 = urwid.AttrMap(fill, 'bg')
        loop = urwid.MainLoop(map2, palette, unhandled_input=exit_on_q)
        loop.run()

    def urwid_four(self):
        def exit_on_q(key):
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()

        palette = [ ('banner',  '', '', '', '#ffa', '#60d'),
                    ('streak',  '', '', '', 'g50',  '#60a'),
                    ('inside',  '', '', '', 'g38',  '#808'),
                    ('outside', '', '', '', 'g27',  '#a06'),
                    ('bg',      '', '', '', 'g7',   '#d06') ]

        placeholder = urwid.SolidFill()
        loop = urwid.MainLoop(placeholder, palette, unhandled_input=exit_on_q)
        loop.screen.set_terminal_properties(colors=256)
        loop.widget = urwid.AttrMap(placeholder, 'bg')
        loop.widget.original_widget = urwid.Filler(urwid.Pile([]))

        div = urwid.Divider()
        outside = urwid.AttrMap(div, 'outside')
        inside = urwid.AttrMap(div, 'inside')
        txt = urwid.Text(('banner', u" Hello World "), align='center')
        streak = urwid.AttrMap(txt, 'streak')
        pile = loop.widget.base_widget # .base_widget skips the decorations
        for item in [outside, inside, streak, inside, outside]:
            pile.contents.append((item, pile.options()))

        loop.run()

    def urwid_five(self):
        def exit_on_q(key):
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()

        class QuestionBox(urwid.Filler):
            def keypress(self, size, key):
                if key != 'enter':
                    return super(QuestionBox, self).keypress(size, key)
                self.original_widget = urwid.Text(u"Nice to meet you,\n%s.\n\nPress Q to exit." % ask.edit_text) 
        ask = urwid.Edit(u"What is your name?\n")
        fill = QuestionBox(ask)
        loop = urwid.MainLoop(fill, unhandled_input=exit_on_q)
        loop.run()

    def urwid_six(self):
        palette = [ ('I say', 'default,bold', 'default', 'bold') ]
        ask = urwid.Edit(('I say', u"What is your name?\n"))
        reply = urwid.Text(u"")
        button = urwid.Button(u'Exit')
        div = urwid.Divider()
        pile = urwid.Pile([ask, div, reply, div, button])
        top = urwid.Filler(pile, valign='top')

        def on_ask_change(edit, new_edit_text):
            reply.set_text(('I say', u"Nice to meet you, %s" % new_edit_text))

        def on_exit_clicked(button):
            raise urwid.ExitMainLoop()

        urwid.connect_signal(ask, 'change', on_ask_change)
        urwid.connect_signal(button, 'click', on_exit_clicked)

        urwid.MainLoop(top, palette).run()

    def urwid_seven(self):
        def question():
            return urwid.Pile( [ urwid.Edit(('I say', u"What is your name?\n")) ] )

        def answer(name):
            return urwid.Text(('I say', u"Nice to meet you, " + name + "\n"))

        class ConversationListBox(urwid.ListBox):
            def __init__(self):
                body = urwid.SimpleFocusListWalker( [ question() ] )
                super(ConversationListBox, self).__init__(body)

            def keypress(self, size, key):
                key = super(ConversationListBox, self).keypress(size, key)
                if key != 'enter':
                    return key
                name = self.focus[0].edit_text
                if not name:
                    raise urwid.ExitMainLoop()
                # replace or add response
                self.focus.contents[1:] = [(answer(name), self.focus.options())]
                pos = self.focus_position
                # add a new question
                self.body.insert(pos + 1, question())
                self.focus_position = pos + 1

        palette = [ ('I say', 'default,bold', 'default') ]
        urwid.MainLoop(ConversationListBox(), palette).run()

    def urwid_eight(self):
        choices = u'Chapman Cleese Gilliam Idle Jones Palin'.split()

        def menu(title, choices):
            body = [ urwid.Text(title), urwid.Divider() ]
            for c in choices:
                button = urwid.Button(c)
                urwid.connect_signal(button, 'click', item_chosen, c)
                body.append(urwid.AttrMap(button, None, focus_map='reversed'))
            return urwid.ListBox(urwid.SimpleFocusListWalker(body))

        def item_chosen(button, choice):
            response = urwid.Text([u'You chose ', choice, u'\n'])
            done = urwid.Button(u'Ok')
            urwid.connect_signal(done, 'click', exit_program)
            main.original_widget = urwid.Filler(urwid.Pile([response, urwid.AttrMap(done, None, focus_map='reversed')]))
        def exit_program(button):
            raise urwid.ExitMainLoop() 

        main = urwid.Padding(menu(u'Pythons', choices), left=2, right=2)
        top = urwid.Overlay(main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                            align='center', width=('relative', 60),
                            valign='middle', height=('relative', 60),
                            min_width=20, min_height=9)
        urwid.MainLoop(top, palette=[ ('reversed', 'standout', '') ]).run()

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

