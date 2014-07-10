#!/usr/bin/env python2

import os, sys, getopt, re, signal, time, datetime, shlex, md5
import subprocess, thread, threading, logging
import copy, json, urwid, datetime
import view_titles, view_note, view_help, view_log, user_input
import utils, temp
from config import Config
from simplenote import Simplenote
from notes_db import NotesDB, ReadError, WriteError
from logging.handlers import RotatingFileHandler

class sncli:

    def __init__(self):
        self.config  = Config()
        self.do_gui = False

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

        self.logs = []

        try:
            self.ndb = NotesDB(self.config, self.log, self.gui_update_view)
        except Exception, e:
            self.log(str(e))
            sys.exit(1)

    def sync_notes(self):
        self.ndb.sync_notes()

    def get_editor(self):
        editor = self.config.get_config('editor')
        if not editor and os.environ['EDITOR']:
            editor = os.environ['EDITOR']
        if not editor:
            self.log(u'No editor configured!')
            return None
        return editor

    def get_pager(self):
        pager = self.config.get_config('pager')
        if not pager and os.environ['PAGER']:
            pager = os.environ['PAGER']
        if not pager:
            self.log(u'No pager configured!')
            return None
        return pager

    def gui_header_clear(self):
        self.master_frame.contents['header'] = ( None, None )
        self.sncli_loop.draw_screen()

    def gui_header_set(self, w):
        self.master_frame.contents['header'] = ( w, None )
        self.sncli_loop.draw_screen()

    def gui_header_get(self):
        return self.master_frame.contents['header'][0]

    def gui_header_focus(self):
        self.master_frame.focus_position = 'header'

    def gui_footer_log_clear(self):
        ui = self.gui_footer_input_get()
        self.master_frame.contents['footer'] = \
                (urwid.Pile([ urwid.Pile([]), urwid.Pile([ui]) ]), None)
        self.sncli_loop.draw_screen()

    def gui_footer_log_set(self, pl):
        ui = self.gui_footer_input_get()
        self.master_frame.contents['footer'] = \
                (urwid.Pile([ urwid.Pile(pl), urwid.Pile([ui]) ]), None)
        self.sncli_loop.draw_screen()

    def gui_footer_log_get(self):
        return self.master_frame.contents['footer'][0].contents[0][0]

    def gui_footer_input_clear(self):
        pl = self.gui_footer_log_get()
        self.master_frame.contents['footer'] = \
                (urwid.Pile([ urwid.Pile([pl]), urwid.Pile([]) ]), None)
        self.sncli_loop.draw_screen()

    def gui_footer_input_set(self, ui):
        pl = self.gui_footer_log_get()
        self.master_frame.contents['footer'] = \
                (urwid.Pile([ urwid.Pile([pl]), urwid.Pile([ui]) ]), None)
        self.sncli_loop.draw_screen()

    def gui_footer_input_get(self):
        return self.master_frame.contents['footer'][0].contents[1][0]

    def gui_footer_focus_input(self):
        self.master_frame.focus_position = 'footer'
        self.master_frame.contents['footer'][0].focus_position = 1

    def gui_body_clear(self):
        self.master_frame.contents['body'] = ( None, None )
        self.sncli_loop.draw_screen()

    def gui_body_set(self, w):
        self.master_frame.contents['body'] = ( w, None )
        self.gui_update_status_bar()
        self.sncli_loop.draw_screen()

    def gui_body_get(self):
        return self.master_frame.contents['body'][0]

    def gui_body_focus(self):
        self.master_frame.focus_position = 'body'

    def log_timeout(self, loop, arg):
        self.log_lock.acquire()

        self.log_alarms -= 1
        if self.log_alarms == 0:
            self.gui_footer_log_clear()
            self.logs = []

        self.log_lock.release()

    def log(self, msg):
        logging.debug(msg)

        if not self.do_gui:
            print msg
            return

        self.log_lock.acquire()

        self.logs.append(msg)
        if len(self.logs) > self.config.get_config('max_logs'):
            self.logs.pop(0)

        log_pile = []
        for l in self.logs:
            log_pile.append(urwid.AttrMap(urwid.Text(l), 'log'))

        self.gui_footer_log_set(log_pile)

        self.sncli_loop.set_alarm_in(5, self.log_timeout, None)
        self.log_alarms += 1

        self.log_lock.release()

    def gui_update_view(self):
        if not self.do_gui:
            return

        cur_key = self.view_titles.note_list[self.view_titles.focus_position].note['key']
        self.view_titles.update_note_list(self.view_titles.search_string)
        self.view_titles.focus_note(cur_key)

        if self.gui_body_get().__class__ == view_note.ViewNote:
            self.view_note.update_note(self.view_note.note['key'])

        self.gui_update_status_bar()

    def gui_update_status_bar(self):
        if self.status_bar != 'yes':
            self.gui_header_clear()
        else:
            self.gui_header_set(self.gui_body_get().get_status_bar())

    def gui_switch_frame_body(self, new_view, save_current_view=True):
        if new_view == None:
            if len(self.last_view) == 0:
                # XXX verify all notes saved...
                self.gui_stop()
            else:
                self.gui_body_set(self.last_view.pop())
        else:
            if self.gui_body_get().__class__ != new_view.__class__:
                if save_current_view:
                    self.last_view.append(self.gui_body_get())
                self.gui_body_set(new_view)

    def gui_search_input(self, search_string):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if search_string:
            self.view_titles.update_note_list(search_string)
            self.gui_body_set(self.view_titles)

    def gui_tags_input(self, tags):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if tags != None:
            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                note = self.view_titles.note_list[self.view_titles.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = self.view_note.note

            self.ndb.set_note_tags(note['key'], tags)

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                self.view_titles.update_note_title(None)
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                self.view_note.update_note(note['key'])

            self.gui_update_status_bar()

    def gui_pipe_input(self, cmd):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if cmd != None:
            note = self.view_titles.note_list[self.view_titles.focus_position].note
            args = shlex.split(cmd)
            try:
                self.gui_clear()
                pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
                pipe.communicate(note['content'])
                pipe.stdin.close()
                pipe.wait()
            except OSError, e:
                self.log(u'Pipe error: ' + str(e))
            finally:
                self.gui_reset()

    def gui_frame_keypress(self, size, key):

        lb = self.gui_body_get()

        if key == self.config.get_keybind('quit'):
            self.gui_switch_frame_body(None)

        elif key == self.config.get_keybind('help'):
            self.gui_switch_frame_body(self.view_help)

        elif key == self.config.get_keybind('sync'):
            self.ndb.last_sync = 0

        elif key == self.config.get_keybind('view_log'):
            self.view_log.update_log()
            self.gui_switch_frame_body(self.view_log)

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
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNotes:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.ndb.set_note_deleted(note['key'])

        elif key == self.config.get_keybind('create_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            editor = self.get_editor()
            if not editor: return None

            tf = temp.tempfile_create(None)

            try:
                self.gui_clear()
                subprocess.check_call(editor + u' ' + temp.tempfile_name(tf), shell=True)
            except Exception, e:
                self.log(u'Editor error: ' + str(e))
                temp.tempfile_delete(tf)
                return None
            finally:
                self.gui_reset()

            content = ''.join(temp.tempfile_content(tf))
            if content:
                self.log(u'New note created')
                self.ndb.create_note(content)

            temp.tempfile_delete(tf)

        elif key == self.config.get_keybind('edit_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            editor = self.get_editor()
            if not editor: return None

            md5_old = md5.new(note['content']).digest()
            tf = temp.tempfile_create(note)

            try:
                self.gui_clear()
                subprocess.check_call(editor + u' ' + temp.tempfile_name(tf), shell=True)
            except Exception, e:
                self.log(u'Editor error: ' + str(e))
                temp.tempfile_delete(tf)
                return None
            finally:
                self.gui_reset()

            new_content = ''.join(temp.tempfile_content(tf))
            md5_new = md5.new(new_content).digest()
            if md5_old != md5_new:
                self.log(u'Note updated')
                self.ndb.set_note_content(note['key'], new_content)
                if self.gui_body_get().__class__ == view_titles.ViewTitles:
                    lb.update_note_title(None)
                else: # self.gui_body_get().__class__ == view_note.ViewNote:
                    lb.update_note(note['key'])

            temp.tempfile_delete(tf)

        elif key == self.config.get_keybind('view_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            if len(lb.body.positions()) <= 0:
                return None
            note = lb.note_list[lb.focus_position].note
            self.view_note.update_note(note['key'])
            self.gui_switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('view_note_ext'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            pager = self.get_pager()
            if not pager: return None

            md5_old = md5.new(note['content']).digest()
            tf = temp.tempfile_create(note)

            try:
                self.gui_clear()
                subprocess.check_call(pager + u' ' + temp.tempfile_name(tf), shell=True)
            except Exception, e:
                self.log(u'Pager error: ' + str(e))
                temp.tempfile_delete(tf)
                return None
            finally:
                self.gui_reset()

            new_content = ''.join(temp.tempfile_content(tf))
            md5_new = md5.new(new_content).digest()
            if md5_old != md5_new:
                self.log(u'Note updated')
                self.ndb.set_note_content(note['key'], new_content)
                lb.update_note_title(None)

            temp.tempfile_delete(tf)

        elif key == self.config.get_keybind('pipe_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.gui_footer_input_set(
                urwid.AttrMap(
                    user_input.UserInput(self.config,
                                         key, '',
                                         self.gui_pipe_input),
                              'search_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('view_next_note'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if len(self.view_titles.body.positions()) <= 0:
                return None
            last = len(self.view_titles.body.positions())
            if self.view_titles.focus_position == (last - 1):
                return None
            self.view_titles.focus_position += 1
            lb.update_note(
                self.view_titles.note_list[self.view_titles.focus_position].note['key'])
            self.gui_switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('view_prev_note'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if len(self.view_titles.body.positions()) <= 0:
                return None
            if self.view_titles.focus_position == 0:
                return None
            self.view_titles.focus_position -= 1
            lb.update_note(
                self.view_titles.note_list[self.view_titles.focus_position].note['key'])
            self.gui_switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('search'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            self.gui_footer_input_set(
                    urwid.AttrMap(
                        user_input.UserInput(self.config,
                                             key, '',
                                             self.gui_search_input),
                                  'search_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('note_pin'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.ndb.set_note_pinned(note['key'], 1)

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_unpin'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.ndb.set_note_pinned(note['key'], 0)
            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_markdown'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.ndb.set_note_markdown(note['key'], 1)
            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_unmarkdown'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.ndb.set_note_markdown(note['key'], 0)
            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                lb.update_note_title(None)

        elif key == self.config.get_keybind('note_tags'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.note

            self.gui_footer_input_set(
                urwid.AttrMap(
                    user_input.UserInput(self.config,
                                         'Tags: ',
                                         '%s' % ','.join(note['tags']),
                                         self.gui_tags_input),
                              'search_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('clear_search'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            self.view_titles.update_note_list(None)
            self.gui_body_set(self.view_titles)

        elif key == self.config.get_keybind('sort_date'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            self.view_titles.sort_note_list('date')

        elif key == self.config.get_keybind('sort_alpha'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            self.view_titles.sort_note_list('alpha')

        else:
            return lb.keypress(size, key)

        self.gui_update_status_bar()
        return None

    def gui_init_view(self, loop, arg):
        self.master_frame.keypress = self.gui_frame_keypress
        self.gui_body_set(self.view_titles)

        self.thread_sync.start()

    def gui_clear(self):
        self.sncli_loop.widget = urwid.Filler(urwid.Text(u''))
        self.sncli_loop.draw_screen()

    def gui_reset(self):
        self.sncli_loop.widget = self.master_frame
        self.sncli_loop.draw_screen()

    def gui_stop(self):
        # don't exit if there are any notes not yet saved to the disk
        if self.ndb.verify_all_saved():
            # clear the screen and exit the urwid run loop
            self.gui_clear()
            raise urwid.ExitMainLoop()
        else:
            self.log(u'WARNING: Not all notes saved to disk (wait for sync worker)') 

    def gui(self, do_sync):

        self.do_gui = True

        self.last_view = []
        self.status_bar = self.config.get_config('status_bar')

        self.log_alarms = 0
        self.log_lock = threading.Lock()

        self.thread_sync = threading.Thread(target=self.ndb.sync_worker,
                                            args=[do_sync])
        self.thread_sync.setDaemon(True)

        self.view_titles = \
            view_titles.ViewTitles(self.config,
                                   {
                                    'ndb'           : self.ndb,
                                    'search_string' : None,
                                    'log'           : self.log
                                   })
        self.view_note = \
            view_note.ViewNote(self.config,
                               {
                                'ndb' : self.ndb,
                                'key' : None,
                                'log' : self.log
                               })

        self.view_log  = view_log.ViewLog(self.config)
        self.view_help = view_help.ViewHelp(self.config)

        palette = \
          [
            ('default',
                self.config.get_color('default_fg'),
                self.config.get_color('default_bg') ),
            ('status_bar',
                self.config.get_color('status_bar_fg'),
                self.config.get_color('status_bar_bg') ),
            ('log',
                self.config.get_color('log_fg'),
                self.config.get_color('log_bg') ),
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
                                        footer=urwid.Pile([ urwid.Pile([]),
                                                            urwid.Pile([]) ]),
                                        focus_part='body')

        self.sncli_loop = urwid.MainLoop(self.master_frame,
                                         palette,
                                         handle_mouse=False)

        self.sncli_loop.set_alarm_in(0, self.gui_init_view, None)

        self.sncli_loop.run()

    def cli_list_notes(self, search_string):
        note_list, match_regex, all_notes_cnt = \
            self.ndb.filter_notes(search_string)
        for n in note_list:
            print n.key + u' - ' + utils.get_note_title(n.note)

    def cli_dump_notes(self, search_string, key=None):

        sep = u'+' + u'-'*39 + u'+'
        def dump_note(note):
            print sep
            print u'| Key: ' + note['key'] + u' |'
            print sep
            print note['content']

        if not key:
            note_list, match_regex, all_notes_cnt = \
                self.ndb.filter_notes(search_string)
            for n in note_list:
                dump_note(n.note)
        else:
            dump_note(self.ndb.get_note(key))

    def cli_create_note(self, from_stdin):

        def save_new_note(content):
            if content and content != u'\n':
                self.log(u'New note created')
                self.ndb.create_note(content)
                self.ndb.sync_notes()

        if from_stdin:

            content = ''.join(sys.stdin)
            save_new_note(content)
            return

        editor = self.get_editor()
        if not editor: return

        tf = temp.tempfile_create(None)

        try:
            subprocess.check_call(editor + u' ' + temp.tempfile_name(tf), shell=True)
        except Exception, e:
            self.log(u'Editor error: ' + str(e))
            temp.tempfile_delete(tf)
            return

        content = ''.join(temp.tempfile_content(tf))
        save_new_note(content)

        temp.tempfile_delete(tf)


def SIGINT_handler(signum, frame):
    print u'\nSignal caught, bye!'
    sys.exit(1)

signal.signal(signal.SIGINT, SIGINT_handler)

def usage():
    print u'Usage: sncli ...'
    sys.exit(0)

def main(argv):
    sync = True
    gui  = True
    key  = ''

    try:
        opts, args = getopt.getopt(argv, 'h',
            [ 'help', 'nosync', 'nogui', 'key=' ])
    except:
        usage()

    for opt, arg in opts:
        if opt in [ '-h', '--help']:
            usage()
        elif opt == '--nosync':
            sync = False
        elif opt == '--nogui':
            gui = False
        elif opt == '--key':
            key = arg
        else:
            print u'ERROR: Unhandled option'
            usage()

    if gui and args: usage() # not quite right...

    if gui:
        sncli().gui(sync)
        return

    if not args: usage()

    def sncli_start(sync):
        sn = sncli()
        if sync: sn.sync_notes()
        return sn

    if args[0] == 'list':

        sn = sncli_start(sync)
        sn.cli_list_notes(' '.join(args[1:]))

    elif args[0] == 'dump':

        sn = sncli_start(sync)
        if not key:
            sn.cli_dump_notes(' '.join(args[1:]))
        else:
            sn.cli_dump_notes(None, key=key)

    elif args[0] == 'create':

        if len(args) == 1:
            sn = sncli_start(sync)
            sn.cli_create_note(False)
        elif len(args) == 2 and args[1] == '-':
            sn = sncli_start(sync)
            sn.cli_create_note(True)
        else:
            usage()

    else:
        usage()

if __name__ == '__main__':
    main(sys.argv[1:])

