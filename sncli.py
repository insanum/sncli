#!/usr/bin/env python2

import os, sys, re, signal, time, datetime, shlex, md5, logging
import subprocess, thread, threading
import copy, json, urwid, datetime
import view_titles, view_note, view_help, view_log, user_input
import utils, temp
from config import Config
from simplenote import Simplenote
from notes_db import NotesDB, SyncError, ReadError, WriteError
from logging.handlers import RotatingFileHandler

class sncli:

    def __init__(self, do_sync):
        self.do_sync = do_sync
        self.config = Config()

        if not os.path.exists(self.config.get_config('db_path')):
            os.mkdir(self.config.get_config('db_path'))

        # configure the logging module
        self.logfile = os.path.join(self.config.get_config('db_path'), 'sncli.log')
        self.loghandler = RotatingFileHandler(self.logfile, maxBytes=100000, backupCount=1)
        self.loghandler.setLevel(logging.DEBUG)
        self.loghandler.setFormatter(logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(message)s'))
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.loghandler)
        self.config.logfile = self.logfile

        logging.debug('sncli logging initialized')

        try:
            self.ndb = NotesDB(self.config)
        except Exception, e:
            print e
            exit(1)

        self.last_view = []
        self.status_bar = self.config.get_config('status_bar')

        self.status_message_alarm = None
        self.status_message_lock = threading.Lock()

        self.thread_save = threading.Thread(target=self.ndb.save_worker)
        self.thread_save.setDaemon(True)

        self.thread_sync = threading.Thread(target=self.ndb.sync_worker)
        self.thread_sync.setDaemon(True)

        self.ndb.add_observer('synced:note', self.observer_notes_db_synced_note)
        self.ndb.add_observer('change:note-status', self.observer_notes_db_change_note_status)
        self.ndb.add_observer('progress:sync_full', self.observer_notes_db_sync_full)

        self.view_titles = \
            view_titles.ViewTitles(self.config,
                                   {
                                    'ndb'            : self.ndb,
                                    'search_string'  : None,
                                    'status_message' : self.status_message_set
                                   })
        self.view_note = \
            view_note.ViewNote(self.config,
                               {
                                'ndb'            : self.ndb,
                                'key'            : None,
                                'status_message' : self.status_message_set
                               })

        self.view_log  = view_log.ViewLog(self.config)
        self.view_help = view_help.ViewHelp(self.config)

    def start_threads(self):
        self.thread_save.start()
        self.thread_sync.start()

    def sync_full_threaded(self):
        thread.start_new_thread(self.ndb.sync_full, ())

    def sync_full_initial(self, loop, arg):
        self.sync_full_threaded()

    def observer_notes_db_change_note_status(self, ndb, evt_type, evt):
        logging.debug(evt.msg)
        self.status_message_set(evt.msg)

    def observer_notes_db_sync_full(self, ndb, evt_type, evt):
        logging.debug(evt.msg)
        self.status_message_set(evt.msg)

    def observer_notes_db_synced_note(self, ndb, evt_type, evt):
        logging.debug(evt.msg)
        self.status_message_set(evt.msg)
        # XXX
        # update view if note synced back is the visible one

    def get_editor(self):
        editor = self.config.get_config('editor')
        if not editor and os.environ['EDITOR']:
            editor = os.environ['EDITOR']
        if not editor:
            self.status_message_set(u'No editor configured!')
            return None
        return editor

    def get_pager(self):
        pager = self.config.get_config('pager')
        if not pager and os.environ['PAGER']:
            pager = os.environ['PAGER']
        if not pager:
            self.status_message_set(u'No pager configured!')
            return None
        return pager

    def header_clear(self):
        self.master_frame.contents['header'] = ( None, None )
        self.sncli_loop.draw_screen()

    def header_set(self, w):
        self.master_frame.contents['header'] = ( w, None )
        self.sncli_loop.draw_screen()

    def header_get(self):
        return self.master_frame.contents['header'][0]

    def header_focus(self):
        self.master_frame.focus_position = 'header'

    def footer_clear(self):
        self.master_frame.contents['footer'] = ( None, None )
        self.sncli_loop.draw_screen()

    def footer_set(self, w):
        self.master_frame.contents['footer'] = ( w, None )
        self.sncli_loop.draw_screen()

    def footer_get(self):
        return self.master_frame.contents['footer'][0]

    def footer_focus(self):
        self.master_frame.focus_position = 'footer'

    def body_clear(self):
        self.master_frame.contents['body'] = ( None, None )
        self.sncli_loop.draw_screen()

    def body_set(self, w):
        self.master_frame.contents['body'] = ( w, None )
        self.update_status_bar()
        self.sncli_loop.draw_screen()

    def body_get(self):
        return self.master_frame.contents['body'][0]

    def body_focus(self):
        self.master_frame.focus_position = 'body'

    def status_message_timeout(self, loop, arg):
        self.status_message_lock.acquire()

        self.status_message_alarm = None
        self.footer_clear()

        self.status_message_lock.release()

    def status_message_cancel(self):
        self.status_message_lock.acquire()

        if self.status_message_alarm:
            self.sncli_loop.remove_alarm(self.status_message_alarm)
        self.status_message_alarm = None

        self.status_message_lock.release()

    def status_message_set(self, msg):
        self.status_message_lock.acquire()

        # if there is already a message showing then concatenate them
        existing_msg = ''
        if self.status_message_alarm and \
           'footer' in self.master_frame.contents.keys():
            existing_msg = \
                self.master_frame.contents['footer'][0].base_widget.text + u'\n'

        # cancel any existing state message alarm
        if self.status_message_alarm:
            self.sncli_loop.remove_alarm(self.status_message_alarm)
        self.status_message_alarm = None

        self.footer_set(urwid.AttrMap(urwid.Text(existing_msg + msg),
                                      'status_message'))

        self.status_message_alarm = \
            self.sncli_loop.set_alarm_at(time.time() + 5,
                                         self.status_message_timeout,
                                         None)

        self.status_message_lock.release()

    def update_status_bar(self):
        if self.status_bar != 'yes':
            self.header_clear()
        else:
            self.header_set(self.body_get().get_status_bar())

    def switch_frame_body(self, new_view, save_current_view=True):
        if new_view == None:
            if len(self.last_view) == 0:
                # XXX verify all notes saved...
                raise urwid.ExitMainLoop()
            else:
                self.body_set(self.last_view.pop())
        else:
            if self.body_get().__class__ != new_view.__class__:
                if save_current_view:
                    self.last_view.append(self.body_get())
                self.body_set(new_view)

    def search_quit(self):
        self.footer_clear()
        self.body_focus()
        self.master_frame.keypress = self.frame_keypress

    def search_input(self, search_string):
        self.footer_clear()
        self.body_focus()
        self.master_frame.keypress = self.frame_keypress
        if search_string:
            self.view_titles.update_note_list(search_string)
            self.body_set(self.view_titles)

    def tags_input(self, tags):
        self.footer_clear()
        self.body_focus()
        self.master_frame.keypress = self.frame_keypress
        if tags != None:
            self.ndb.set_note_tags(
                self.view_titles.note_list[self.view_titles.focus_position].note['key'], tags)
            self.view_titles.update_note_title(None)

    def pipe_input(self, cmd):
        self.footer_clear()
        self.body_focus()
        self.master_frame.keypress = self.frame_keypress
        if cmd != None:
            note = self.view_titles.note_list[self.view_titles.focus_position].note
            args = shlex.split(cmd)
            try:
                pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
                pipe.communicate(note['content'])
                pipe.stdin.close()
                pipe.wait()
            except OSError, e:
                self.status_message_set(u'Pipe error: ' + str(e))

    def frame_keypress(self, size, key):

        lb = self.body_get()

        if key == self.config.get_keybind('quit'):
            self.switch_frame_body(None)

        elif key == self.config.get_keybind('help'):
            self.switch_frame_body(self.view_help)

        elif key == self.config.get_keybind('sync'):
            self.sync_full_threaded()

        elif key == self.config.get_keybind('view_log'):
            self.switch_frame_body(self.view_log)

        elif key == self.config.get_keybind('down'):
            if len(lb.body.positions()) <= 0:
                return None
            last = len(lb.body.positions())
            if lb.focus_position == (last - 1):
                return None
            lb.focus_position += 1
            lb.render(size)

        elif key == self.config.get_keybind('up'):
            if len(lb.body.positions()) <= 0:
                return None
            if lb.focus_position == 0:
                return None
            lb.focus_position -= 1
            lb.render(size)

        elif key == self.config.get_keybind('page_down'):
            if len(lb.body.positions()) <= 0:
                return None
            last = len(lb.body.positions())
            next_focus = lb.focus_position + size[1]
            if next_focus >= last:
                next_focus = last - 1
            lb.change_focus(size, next_focus,
                            offset_inset=0,
                            coming_from='above')

        elif key == self.config.get_keybind('page_up'):
            if len(lb.body.positions()) <= 0:
                return None
            if 'bottom' in lb.ends_visible(size):
                last = len(lb.body.positions())
                next_focus = last - size[1] - size[1]
            else:
                next_focus = lb.focus_position - size[1]
            if next_focus < 0:
                next_focus = 0
            lb.change_focus(size, next_focus,
                            offset_inset=0,
                            coming_from='below')

        elif key == self.config.get_keybind('half_page_down'):
            if len(lb.body.positions()) <= 0:
                return None
            last = len(lb.body.positions())
            next_focus = lb.focus_position + (size[1] / 2)
            if next_focus >= last:
                next_focus = last - 1
            lb.change_focus(size, next_focus,
                            offset_inset=0,
                            coming_from='above')

        elif key == self.config.get_keybind('half_page_up'):
            if len(lb.body.positions()) <= 0:
                return None
            if 'bottom' in lb.ends_visible(size):
                last = len(lb.body.positions())
                next_focus = last - size[1] - (size[1] / 2)
            else:
                next_focus = lb.focus_position - (size[1] / 2)
            if next_focus < 0:
                next_focus = 0
            lb.change_focus(size, next_focus,
                            offset_inset=0,
                            coming_from='below')

        elif key == self.config.get_keybind('bottom'):
            if len(lb.body.positions()) <= 0:
                return None
            lb.change_focus(size, (len(lb.body.positions()) - 1),
                            offset_inset=0,
                            coming_from='above')

        elif key == self.config.get_keybind('top'):
            if len(lb.body.positions()) <= 0:
                return None
            lb.change_focus(size, 0,
                            offset_inset=0,
                            coming_from='below')

        elif key == self.config.get_keybind('status'):
            if self.status_bar == 'yes':
                self.status_bar = 'no'
            else:
                self.status_bar = self.config.get_config('status_bar')

        elif key == self.config.get_keybind('trash_note'):
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.ndb.set_note_deleted(note['key'])

        elif key == self.config.get_keybind('create_note'):
            if self.body_get().__class__ == view_titles.ViewTitles:
                editor = self.get_editor()
                if not editor: return None

                tf = temp.tempfile_create(None)
                try:
                    subprocess.check_call(editor + u' ' + temp.tempfile_name(tf), shell=True)
                except Exception, e:
                    self.status_message_set(u'Editor error: ' + str(e))

                content = ''.join(temp.tempfile_content(tf))
                if content:
                    self.status_message_set(u'New note created')
                    self.ndb.create_note(content)
                temp.tempfile_delete(tf)

        elif key == self.config.get_keybind('edit_note'):
            if self.body_get().__class__ == view_titles.ViewTitles:
                editor = self.get_editor()
                if not editor: return None

                note = lb.note_list[lb.focus_position].note
                md5_old = md5.new(note['content']).digest()
                tf = temp.tempfile_create(note)
                try:
                    subprocess.check_call(editor + u' ' + temp.tempfile_name(tf), shell=True)
                except Exception, e:
                    self.status_message_set(u'Editor error: ' + str(e))

                new_content = ''.join(temp.tempfile_content(tf))
                md5_new = md5.new(new_content).digest()
                if md5_old != md5_new:
                    self.status_message_set(u'Note updated')
                    self.ndb.set_note_content(note['key'], new_content)
                    lb.update_note_title(None)
                temp.tempfile_delete(tf)

        elif key == self.config.get_keybind('view_note'):
            # only when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.view_note.update_note(note['key'])
                self.switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('view_note_ext'):
            # only when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                pager = self.get_pager()
                if not pager: return None

                note = lb.note_list[lb.focus_position].note
                md5_old = md5.new(note['content']).digest()
                tf = temp.tempfile_create(note)
                try:
                    subprocess.check_call(pager + u' ' + temp.tempfile_name(tf), shell=True)
                except Exception, e:
                    self.status_message_set(u'Pager error: ' + str(e))

                new_content = ''.join(temp.tempfile_content(tf))
                md5_new = md5.new(new_content).digest()
                if md5_old != md5_new:
                    self.status_message_set(u'Note updated')
                    self.ndb.set_note_content(note['key'], new_content)
                    lb.update_note_title(None)
                temp.tempfile_delete(tf)

        elif key == self.config.get_keybind('pipe_note'):
            # only when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.status_message_cancel()
                self.footer_set(
                    urwid.AttrMap(
                        user_input.UserInput(self.config,
                                             key, '',
                                             self.pipe_input),
                                  'search_bar'))
                self.footer_focus()
                self.master_frame.keypress = self.footer_get().keypress

        elif key == self.config.get_keybind('view_next_note'):
            # only when viewing the note content
            if self.body_get().__class__ == view_note.ViewNote:
                if len(self.view_titles.body.positions()) <= 0:
                    return None
                last = len(self.view_titles.body.positions())
                if self.view_titles.focus_position == (last - 1):
                    return None
                self.view_titles.focus_position += 1
                lb.update_note(
                    self.view_titles.note_list[self.view_titles.focus_position].note['key'])
                self.switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('view_prev_note'):
            # only when viewing the note content
            if self.body_get().__class__ == view_note.ViewNote:
                if len(self.view_titles.body.positions()) <= 0:
                    return None
                if self.view_titles.focus_position == 0:
                    return None
                self.view_titles.focus_position -= 1
                lb.update_note(
                    self.view_titles.note_list[self.view_titles.focus_position].note['key'])
                self.switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('search'):
            # search when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                self.status_message_cancel()
                self.footer_set(urwid.AttrMap(
                                    user_input.UserInput(self.config,
                                                         key, '',
                                                         self.search_input),
                                              'search_bar'))
                self.footer_focus()
                self.master_frame.keypress = self.footer_get().keypress

        elif key == self.config.get_keybind('note_pin'):
            # pin note when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.ndb.set_note_pinned(note['key'], 1)
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_unpin'):
            # unpin note when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.ndb.set_note_pinned(note['key'], 0)
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_markdown'):
            # markdown note when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.ndb.set_note_markdown(note['key'], 1)
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_unmarkdown'):
            # unmarkdown note when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.ndb.set_note_markdown(note['key'], 0)
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_tags'):
            # edit tags when viewing the note list
            if self.body_get().__class__ == view_titles.ViewTitles:
                note = lb.note_list[lb.focus_position].note
                self.status_message_cancel()
                self.footer_set(
                    urwid.AttrMap(
                        user_input.UserInput(self.config,
                                             'Tags: ',
                                             '%s' % ','.join(note['tags']),
                                             self.tags_input),
                                  'search_bar'))
                self.footer_focus()
                self.master_frame.keypress = self.footer_get().keypress

        elif key == self.config.get_keybind('clear_search'):
            self.view_titles.update_note_list(None)
            self.body_set(self.view_titles)

        else:
            return lb.keypress(size, key)

        self.update_status_bar()
        return None

    def init_view(self, loop, arg):
        self.master_frame.keypress = self.frame_keypress
        self.body_set(self.view_titles)
        self.start_threads()

        if self.do_sync:
            # start full sync after initial view is up
            self.sncli_loop.set_alarm_in(1, self.sync_full_initial, None)

    def ba_bam_what(self):

        palette = \
          [
            ('default',
                self.config.get_color('default_fg'),
                self.config.get_color('default_bg') ),
            ('status_bar',
                self.config.get_color('status_bar_fg'),
                self.config.get_color('status_bar_bg') ),
            ('status_message',
                self.config.get_color('status_message_fg'),
                self.config.get_color('status_message_bg') ),
            ('search_bar',
                self.config.get_color('search_bar_fg'),
                self.config.get_color('search_bar_bg') ),
            ('note_focus',
                self.config.get_color('note_focus_fg'),
                self.config.get_color('note_focus_bg') ),
            ('note_title_day',
                self.config.get_color('note_title_day_fg'),
                self.config.get_color('note_title_day_bg') ),
            ('note_title_week',
                self.config.get_color('note_title_week_fg'),
                self.config.get_color('note_title_week_bg') ),
            ('note_title_month',
                self.config.get_color('note_title_month_fg'),
                self.config.get_color('note_title_month_bg') ),
            ('note_title_year',
                self.config.get_color('note_title_year_fg'),
                self.config.get_color('note_title_year_bg') ),
            ('note_title_ancient',
                self.config.get_color('note_title_ancient_fg'),
                self.config.get_color('note_title_ancient_bg') ),
            ('note_date',
                self.config.get_color('note_date_fg'),
                self.config.get_color('note_date_bg') ),
            ('note_flags',
                self.config.get_color('note_flags_fg'),
                self.config.get_color('note_flags_bg') ),
            ('note_tags',
                self.config.get_color('note_tags_fg'),
                self.config.get_color('note_tags_bg') ),
            ('note_content',
                self.config.get_color('note_content_fg'),
                self.config.get_color('note_content_bg') ),
            ('note_content_focus',
                self.config.get_color('note_content_focus_fg'),
                self.config.get_color('note_content_focus_bg') ),
            ('help_focus',
                self.config.get_color('help_focus_fg'),
                self.config.get_color('help_focus_bg') ),
            ('help_header',
                self.config.get_color('help_header_fg'),
                self.config.get_color('help_header_bg') ),
            ('help_config',
                self.config.get_color('help_config_fg'),
                self.config.get_color('help_config_bg') ),
            ('help_value',
                self.config.get_color('help_value_fg'),
                self.config.get_color('help_value_bg') ),
            ('help_descr',
                self.config.get_color('help_descr_fg'),
                self.config.get_color('help_descr_bg') )
          ]

        self.master_frame = urwid.Frame(body=urwid.Filler(urwid.Text(u'')),
                                        header=None,
                                        footer=None,
                                        focus_part='body')

        self.sncli_loop = urwid.MainLoop(self.master_frame,
                                         palette,
                                         handle_mouse=False)

        self.sncli_loop.set_alarm_in(0, self.init_view, None)

        self.sncli_loop.run()

def SIGINT_handler(signum, frame):
    print('\nSignal caught, bye!')
    sys.exit(1)

signal.signal(signal.SIGINT, SIGINT_handler)

def main():
    sncli(True if len(sys.argv) > 1 else False).ba_bam_what()

if __name__ == '__main__':
    main()

