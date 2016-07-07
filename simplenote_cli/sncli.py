
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import os, sys, getopt, re, signal, time, datetime, shlex, hashlib
import subprocess, threading, logging
import copy, json, urwid, datetime
from . import view_titles, view_note, view_help, view_log, user_input
from . import utils, temp
from .config import Config
from .simplenote import Simplenote
from .notes_db import NotesDB, ReadError, WriteError
from logging.handlers import RotatingFileHandler

class sncli:

    def __init__(self, do_server_sync, verbose=False, config_file=None):
        self.config         = Config(config_file)
        self.do_server_sync = do_server_sync
        self.verbose        = verbose
        self.do_gui         = False
        force_full_sync     = False

        if not os.path.exists(self.config.get_config('db_path')):
            os.mkdir(self.config.get_config('db_path'))
            force_full_sync = True

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
        except Exception as e:
            self.log(str(e))
            sys.exit(1)

        if force_full_sync:
            # The note database doesn't exist so force a full sync. It is
            # important to do this outside of the gui because an account
            # with hundreds of notes will cause a recursion panic under
            # urwid. This simple workaround gets the job done. :-)
            self.verbose = True
            self.log('sncli database doesn\'t exist, forcing full sync...')
            self.sync_notes()
            self.verbose = verbose

    def sync_notes(self):
        self.ndb.sync_now(self.do_server_sync)

    def get_editor(self):
        editor = self.config.get_config('editor')
        if 'EDITOR' in os.environ:
            editor = os.environ['EDITOR']
        if not editor:
            self.log('No editor configured!')
            return None
        return editor

    def get_pager(self):
        pager = self.config.get_config('pager')
        if 'PAGER' in os.environ:
            pager = os.environ['PAGER']
        if not pager:
            self.log('No pager configured!')
            return None
        return pager

    def get_diff(self):
        diff = self.config.get_config('diff')
        if not diff:
            self.log('No diff command configured!')
            return None
        return diff

    def exec_cmd_on_note(self, note, cmd=None, raw=False):

        if not cmd:
            cmd = self.get_editor()
        if not cmd:
            return None

        tf = temp.tempfile_create(note if note else None, raw=raw)

        try:
            subprocess.check_call(cmd + ' ' + temp.tempfile_name(tf), shell=True)
        except Exception as e:
            self.log('Command error: ' + str(e))
            temp.tempfile_delete(tf)
            return None

        content = None
        if not raw:
            content = temp.tempfile_content(tf)
            if not content or content == '\n':
                content = None

        temp.tempfile_delete(tf)
        return content

    def exec_diff_on_note(self, note, old_note):

        diff = self.get_diff()
        if not diff:
            return None

        pager = self.get_pager()
        if not pager:
            return None

        ltf = temp.tempfile_create(note)
        otf = temp.tempfile_create(old_note)
        out = temp.tempfile_create(None)

        try:
            subprocess.call(diff + ' ' + 
                            temp.tempfile_name(ltf) + ' ' +
                            temp.tempfile_name(otf) + ' > ' +
                            temp.tempfile_name(out),
                            shell=True)
            subprocess.check_call(pager + ' ' +
                                  temp.tempfile_name(out),
                                  shell=True)
        except Exception as e:
            self.log('Command error: ' + str(e))
            temp.tempfile_delete(ltf)
            temp.tempfile_delete(otf)
            temp.tempfile_delete(out)
            return None

        temp.tempfile_delete(ltf)
        temp.tempfile_delete(otf)
        temp.tempfile_delete(out)
        return None

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
        else:
            # for some reason having problems with this being empty?
            if len(self.logs) > 0:
                self.logs.pop(0)

            log_pile = []

            for l in self.logs:
                log_pile.append(urwid.AttrMap(urwid.Text(l), 'log'))

            if self.verbose:
                self.gui_footer_log_set(log_pile)

        self.log_lock.release()

    def log(self, msg):
        logging.debug(msg)

        if not self.do_gui:
            if self.verbose:
                print(msg)
            return

        self.log_lock.acquire()

        self.log_alarms += 1
        self.logs.append(msg)

        if len(self.logs) > int(self.config.get_config('max_logs')):
            self.log_alarms -= 1
            self.logs.pop(0)

        log_pile = []
        for l in self.logs:
            log_pile.append(urwid.AttrMap(urwid.Text(l), 'log'))

        if self.verbose:
            self.gui_footer_log_set(log_pile)

        self.sncli_loop.set_alarm_in(
                int(self.config.get_config('log_timeout')),
                self.log_timeout, None)

        self.log_lock.release()

    def gui_update_view(self):
        if not self.do_gui:
            return

        try:
            cur_key = self.view_titles.note_list[self.view_titles.focus_position].note['localkey']
        except IndexError as e:
            cur_key = None
            pass
        self.view_titles.update_note_list(self.view_titles.search_string)
        self.view_titles.focus_note(cur_key)

        if self.gui_body_get().__class__ == view_note.ViewNote:
            self.view_note.update_note_view()

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

    def trash_note_callback(self, key, yes):
        if not yes:
            return

        # toggle the deleted flag
        note = self.ndb.get_note(key)
        self.ndb.set_note_deleted(key, 0 if note['deleted'] else 1)

        if self.gui_body_get().__class__ == view_titles.ViewTitles:
            self.view_titles.update_note_title()

        self.gui_update_status_bar()
        self.ndb.sync_worker_go()

    def restore_note_callback(self, key, yes):
        if not yes:
            return

        # restore the contents of the old_note
        self.log('Restoring version v{0} (key={1})'.
                 format(self.view_note.old_note['version'], key))
        self.ndb.set_note_content(key, self.view_note.old_note['content'])

        self.view_note.update_note_view()
        self.gui_update_status_bar()
        self.ndb.sync_worker_go()

    def gui_yes_no_input(self, args, yes_no):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        args[0](args[1],
                True if yes_no in [ 'YES', 'Yes', 'yes', 'Y', 'y' ]
                     else False)

    def gui_search_input(self, args, search_string):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if search_string:
            if (self.gui_body_get() == self.view_note):
                self.search_direction = args[1]
                self.view_note.search_note_view_next(search_string=search_string, search_mode=args[0])
            else:
                self.view_titles.update_note_list(search_string, args[0])
                self.gui_body_set(self.view_titles)

    def gui_version_input(self, args, version):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if version:
            try:
                # verify input is a number
                int(version)
            except ValueError as e:
                self.log('ERROR: Invalid version value')
                return
            self.view_note.update_note_view(version=version)
            self.gui_update_status_bar()

    def gui_tags_input(self, args, tags):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if tags != None:
            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                note = self.view_titles.note_list[self.view_titles.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = self.view_note.note

            self.ndb.set_note_tags(note['localkey'], tags)

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                self.view_titles.update_note_title()
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                self.view_note.update_note_view()

            self.gui_update_status_bar()
            self.ndb.sync_worker_go()

    def gui_pipe_input(self, args, cmd):
        self.gui_footer_input_clear()
        self.gui_body_focus()
        self.master_frame.keypress = self.gui_frame_keypress
        if cmd != None:
            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                note = self.view_titles.note_list[self.view_titles.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = self.view_note.old_note if self.view_note.old_note \
                                               else self.view_note.note
            args = shlex.split(cmd)
            try:
                self.gui_clear()
                pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
                pipe.communicate(note['content'])
                pipe.stdin.close()
                pipe.wait()
            except OSError as e:
                self.log('Pipe error: ' + str(e))
            finally:
                self.gui_reset()

    def gui_frame_keypress(self, size, key):
        # convert space character into name
        if key == ' ':
            key = 'space'

        lb = self.gui_body_get()

        if key == self.config.get_keybind('quit'):
            self.gui_switch_frame_body(None)

        elif key == self.config.get_keybind('help'):
            self.gui_switch_frame_body(self.view_help)

        elif key == self.config.get_keybind('sync'):
            self.ndb.last_sync = 0
            self.ndb.sync_worker_go()

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

        elif key == self.config.get_keybind('view_next_note'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if len(self.view_titles.body.positions()) <= 0:
                return None
            last = len(self.view_titles.body.positions())
            if self.view_titles.focus_position == (last - 1):
                return None
            self.view_titles.focus_position += 1
            lb.update_note_view(
                self.view_titles.note_list[self.view_titles.focus_position].note['localkey'])
            self.gui_switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('view_prev_note'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if len(self.view_titles.body.positions()) <= 0:
                return None
            if self.view_titles.focus_position == 0:
                return None
            self.view_titles.focus_position -= 1
            lb.update_note_view(
                self.view_titles.note_list[self.view_titles.focus_position].note['localkey'])
            self.gui_switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('prev_version') or \
             key == self.config.get_keybind('next_version'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            diff = -1 if key == self.config.get_keybind('prev_version') else 1

            version = diff + (self.view_note.old_note['version']
                              if self.view_note.old_note else
                                 self.view_note.note['version'])

            lb.update_note_view(version=version)

        elif key == self.config.get_keybind('diff_version'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if not self.view_note.old_note:
                self.log('Already at latest version (key={0})'.
                         format(self.view_note.key))
                return None

            self.gui_clear()
            self.exec_diff_on_note(self.view_note.note,
                                   self.view_note.old_note)
            self.gui_reset()

        elif key == self.config.get_keybind('restore_version'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if not self.view_note.old_note:
                self.log('Already at latest version (key={0})'.
                         format(self.view_note.key))
                return None

            self.gui_footer_input_set(
                urwid.AttrMap(
                    user_input.UserInput(
                        self.config,
                        'Restore v{0} (y/n): '.format(self.view_note.old_note['version']),
                        '',
                        self.gui_yes_no_input,
                        [ self.restore_note_callback, self.view_note.key ]),
                    'user_input_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('latest_version'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            lb.update_note_view(version=None)

        elif key == self.config.get_keybind('select_version'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            self.gui_footer_input_set(
                urwid.AttrMap(
                    user_input.UserInput(
                        self.config,
                        key,
                        '',
                        self.gui_version_input,
                        None),
                    'user_input_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('status'):
            if self.status_bar == 'yes':
                self.status_bar = 'no'
            else:
                self.status_bar = self.config.get_config('status_bar')

        elif key == self.config.get_keybind('create_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            self.gui_clear()
            content = self.exec_cmd_on_note(None)
            self.gui_reset()

            if content:
                self.log('New note created')
                self.ndb.create_note(content)
                self.gui_update_view()
                self.ndb.sync_worker_go()

        elif key == self.config.get_keybind('edit_note') or \
             key == self.config.get_keybind('view_note_ext') or \
             key == self.config.get_keybind('view_note_json'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                if key == self.config.get_keybind('edit_note'):
                    note = lb.note
                else:
                    note = lb.old_note if lb.old_note else lb.note

            self.gui_clear()
            if key == self.config.get_keybind('edit_note'):
                content = self.exec_cmd_on_note(note)
            elif key == self.config.get_keybind('view_note_ext'):
                content = self.exec_cmd_on_note(note, cmd=self.get_pager())
            else: # key == self.config.get_keybind('view_note_json')
                content = self.exec_cmd_on_note(note, cmd=self.get_pager(), raw=True)

            self.gui_reset()

            if not content:
                return None

            md5_old = hashlib.md5(note['content'].encode('utf-8')).digest()
            md5_new = hashlib.md5(content.encode('utf-8')).digest()

            if md5_old != md5_new:
                self.log('Note updated')
                self.ndb.set_note_content(note['localkey'], content)
                if self.gui_body_get().__class__ == view_titles.ViewTitles:
                    lb.update_note_title()
                else: # self.gui_body_get().__class__ == view_note.ViewNote:
                    lb.update_note_view()
                self.ndb.sync_worker_go()
            else:
                self.log('Note unchanged')

        elif key == self.config.get_keybind('view_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles:
                return key

            if len(lb.body.positions()) <= 0:
                return None
            self.view_note.update_note_view(
                    lb.note_list[lb.focus_position].note['localkey'])
            self.gui_switch_frame_body(self.view_note)

        elif key == self.config.get_keybind('pipe_note'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
               self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                if len(lb.body.positions()) <= 0:
                    return None
                note = lb.note_list[lb.focus_position].note
            else: # self.gui_body_get().__class__ == view_note.ViewNote:
                note = lb.old_note if lb.old_note else lb.note

            self.gui_footer_input_set(
                urwid.AttrMap(
                    user_input.UserInput(
                        self.config,
                        key,
                        '',
                        self.gui_pipe_input,
                        None),
                    'user_input_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('note_trash'):
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
                    user_input.UserInput(
                        self.config,
                        '{0} (y/n): '.format('Untrash' if note['deleted'] else 'Trash'),
                        '',
                        self.gui_yes_no_input,
                        [ self.trash_note_callback, note['localkey'] ]),
                    'user_input_bar'))
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

            pin = 1
            if 'systemtags' in note:
                if 'pinned' in note['systemtags']: pin = 0
                else:                              pin = 1

            self.ndb.set_note_pinned(note['localkey'], pin)

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                lb.update_note_title()

            self.ndb.sync_worker_go()

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

            md = 1
            if 'systemtags' in note:
                if 'markdown' in note['systemtags']: md = 0
                else:                                md = 1

            self.ndb.set_note_markdown(note['localkey'], md)

            if self.gui_body_get().__class__ == view_titles.ViewTitles:
                lb.update_note_title()

            self.ndb.sync_worker_go()

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
                    user_input.UserInput(
                        self.config,
                        'Tags: ',
                        '%s' % ','.join(note['tags']),
                        self.gui_tags_input,
                        None),
                    'user_input_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('search_gstyle') or \
             key == self.config.get_keybind('search_regex') or \
             key == self.config.get_keybind('search_prev_gstyle') or \
             key == self.config.get_keybind('search_prev_regex'):
            if self.gui_body_get().__class__ != view_titles.ViewTitles and \
                 self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            if self.gui_body_get().__class__ == view_note.ViewNote:
                if key == self.config.get_keybind('search_prev_gstyle') or \
                     key == self.config.get_keybind('search_prev_regex'):
                    self.view_note.search_direction = 'backward'
                else:
                    self.view_note.search_direction = 'forward'

            self.gui_footer_input_set(
                urwid.AttrMap(
                    user_input.UserInput(
                        self.config,
                        key,
                        '',
                        self.gui_search_input,
                        [ 'gstyle' if key == self.config.get_keybind('search_gstyle')
                                   or key == self.config.get_keybind('search_prev_gstyle')
                                   else 'regex',
                          'backward' if key == self.config.get_keybind('search_prev_gstyle')
                                    or key == self.config.get_keybind('search_prev_regex')
                                    else 'forward' ]),
                    'user_input_bar'))
            self.gui_footer_focus_input()
            self.master_frame.keypress = self.gui_footer_input_get().keypress

        elif key == self.config.get_keybind('search_next'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            self.view_note.search_note_view_next()

        elif key == self.config.get_keybind('search_prev'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            self.view_note.search_note_view_prev()

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

        elif key == self.config.get_keybind('copy_note_text'):
            if self.gui_body_get().__class__ != view_note.ViewNote:
                return key

            self.view_note.copy_note_text()

        else:
            return lb.keypress(size, key)

        self.gui_update_status_bar()
        return None

    def gui_init_view(self, loop, view_note):
        self.master_frame.keypress = self.gui_frame_keypress
        self.gui_body_set(self.view_titles)

        if view_note:
            # note that title view set first to prime the view stack
            self.gui_switch_frame_body(self.view_note)

        self.thread_sync.start()

    def gui_clear(self):
        self.sncli_loop.widget = urwid.Filler(urwid.Text(''))
        self.sncli_loop.draw_screen()

    def gui_reset(self):
        self.sncli_loop.widget = self.master_frame
        self.sncli_loop.draw_screen()

    def gui_stop(self):
        # don't exit if there are any notes not yet saved to the disk

        # TODO - verify_all_saved() was deadlocking for me. urllib2.urlopen() isn't timing out appropriately if connection is down.
        # if self.ndb.verify_all_saved():
        #     # clear the screen and exit the urwid run loop
        #     self.gui_clear()
        #     raise urwid.ExitMainLoop()
        # else:
        #     self.log(u'WARNING: Not all notes saved to disk (wait for sync worker)') 

        # clear the screen and exit the urwid run loop
        self.gui_clear()
        raise urwid.ExitMainLoop()

    def gui(self, key):

        self.do_gui = True

        self.last_view = []
        self.status_bar = self.config.get_config('status_bar')

        self.log_alarms = 0
        self.log_lock = threading.Lock()

        self.thread_sync = threading.Thread(target=self.ndb.sync_worker,
                                            args=[self.do_server_sync])
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
                                'key' : key, # initial key to view or None
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
            ('user_input_bar',
                self.config.get_color('user_input_bar_fg'),
                self.config.get_color('user_input_bar_bg') ),
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
            ('note_content_old',
                self.config.get_color('note_content_old_fg'),
                self.config.get_color('note_content_old_bg') ),
            ('note_content_old_focus',
                self.config.get_color('note_content_old_focus_fg'),
                self.config.get_color('note_content_old_focus_bg') ),
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

        self.master_frame = urwid.Frame(body=urwid.Filler(urwid.Text('')),
                                        header=None,
                                        footer=urwid.Pile([ urwid.Pile([]),
                                                            urwid.Pile([]) ]),
                                        focus_part='body')

        self.sncli_loop = urwid.MainLoop(self.master_frame,
                                         palette,
                                         handle_mouse=False)

        self.sncli_loop.set_alarm_in(0, self.gui_init_view,
                                     True if key else False)

        self.sncli_loop.run()

    def cli_list_notes(self, regex, search_string):

        note_list, match_regex, all_notes_cnt = \
            self.ndb.filter_notes(
                    search_string,
                    search_mode='regex' if regex else 'gstyle')
        for n in note_list:
            flags = utils.get_note_flags(n.note)
            print((n.key + \
                  ' [' + flags + '] ' + \
                  utils.get_note_title(n.note)))

    def cli_note_dump(self, key):

        note = self.ndb.get_note(key)
        if not note:
            self.log('ERROR: Key does not exist')
            return

        w = 60
        sep = '+' + '-'*(w+2) + '+'
        t = time.localtime(float(note['modifydate']))
        mod_time = time.strftime('%a, %d %b %Y %H:%M:%S', t)
        title = utils.get_note_title(note)
        flags = utils.get_note_flags(note)
        tags  = utils.get_note_tags(note)

        print(sep)
        print(('| {:<' + str(w) + '} |').format(('    Title: ' + title)[:w]))
        print(('| {:<' + str(w) + '} |').format(('      Key: ' + note.get('key', 'Localkey: {}'.format(note.get('localkey'))))[:w]))
        print(('| {:<' + str(w) + '} |').format(('     Date: ' + mod_time)[:w]))
        print(('| {:<' + str(w) + '} |').format(('     Tags: ' + tags)[:w]))
        print(('| {:<' + str(w) + '} |').format(('  Version: v' + str(note.get('version', 0)))[:w]))
        print(('| {:<' + str(w) + '} |').format(('    Flags: [' + flags + ']')[:w]))
        if utils.note_published(note) and 'publishkey' in note:
            print(('| {:<' + str(w) + '} |').format(('Published: http://simp.ly/publish/' + note['publishkey'])[:w]))
        else:
            print(('| {:<' + str(w) + '} |').format(('Published: n/a')[:w]))
        print(sep)
        print((note['content']))

    def cli_dump_notes(self, regex, search_string):

        note_list, match_regex, all_notes_cnt = \
            self.ndb.filter_notes(
                    search_string,
                    search_mode='regex' if regex else 'gstyle')
        for n in note_list:
            self.cli_note_dump(n.key)

    def cli_note_create(self, from_stdin, title):

        if from_stdin:
            content = ''.join(sys.stdin)
        else:
            content = self.exec_cmd_on_note(None)

        if title:
            content = title + '\n\n' + content if content else ''

        if content:
            self.log('New note created')
            self.ndb.create_note(content)
            self.sync_notes()

    def cli_note_edit(self, key):

        note = self.ndb.get_note(key)
        if not note:
            self.log('ERROR: Key does not exist')
            return

        content = self.exec_cmd_on_note(note)
        if not content:
            return

        md5_old = hashlib.md5(note['content'].encode('utf-8')).digest()
        md5_new = hashlib.md5(content.encode('utf-8')).digest()

        if md5_old != md5_new:
            self.log('Note updated')
            self.ndb.set_note_content(note['localkey'], content)
            self.sync_notes()
        else:
            self.log('Note unchanged')

    def cli_note_trash(self, key, trash):

        note = self.ndb.get_note(key)
        if not note:
            self.log('ERROR: Key does not exist')
            return

        self.ndb.set_note_deleted(key, trash)
        self.sync_notes()

    def cli_note_pin(self, key, pin):

        note = self.ndb.get_note(key)
        if not note:
            self.log('ERROR: Key does not exist')
            return

        self.ndb.set_note_pinned(key, pin)
        self.sync_notes()

    def cli_note_markdown(self, key, markdown):

        note = self.ndb.get_note(key)
        if not note:
            self.log('ERROR: Key does not exist')
            return

        self.ndb.set_note_markdown(key, markdown)
        self.sync_notes()


def SIGINT_handler(signum, frame):
    print('\nSignal caught, bye!')
    sys.exit(1)

signal.signal(signal.SIGINT, SIGINT_handler)

def usage():
    print ('''
Usage:
 sncli [OPTIONS] [COMMAND] [COMMAND_ARGS]

 OPTIONS:
  -h, --help                  - usage help
  -v, --verbose               - verbose output
  -n, --nosync                - don't perform a server sync
  -r, --regex                 - search string is a regular expression
  -k <key>, --key=<key>       - note key
  -t <title>, --title=<title> - title of note for create (cli mode)
  -c <file>, --config=<file>  - config file to read from (defaults to ~/.snclirc)

 COMMANDS:
  <none>                      - console gui mode when no command specified
  sync                        - perform a full sync with the server
  list [search_string]        - list notes (refined with search string)
  dump [search_string]        - dump notes (refined with search string)
  create [-]                  - create a note ('-' content from stdin)
  dump                        - dump a note (specified by <key>)
  edit                        - edit a note (specified by <key>)
  < trash | untrash >         - trash/untrash a note (specified by <key>)
  < pin | unpin >             - pin/unpin a note (specified by <key>)
  < markdown | unmarkdown >   - markdown/unmarkdown a note (specified by <key>)
''')
    sys.exit(0)

def main(argv):
    verbose = False
    sync    = True
    regex   = False
    key     = None
    title   = None
    config  = None

    try:
        opts, args = getopt.getopt(argv,
            'hvnrk:t:c:',
            [ 'help', 'verbose', 'nosync', 'regex', 'key=', 'title=', 'config=' ])
    except:
        usage()

    for opt, arg in opts:
        if opt in [ '-h', '--help']:
            usage()
        elif opt in [ '-v', '--verbose']:
            verbose = True
        elif opt in [ '-n', '--nosync']:
            sync = False
        elif opt in [ '-r', '--regex']:
            regex = True
        elif opt in [ '-k', '--key']:
            key = arg
        elif opt in [ '-t', '--title']:
            title = arg
        elif opt in [ '-c', '--config']:
            config = arg
        else:
            print('ERROR: Unhandled option')
            usage()

    if not args:
        sncli(sync, verbose, config).gui(key)
        return

    def sncli_start(sync=sync, verbose=verbose, config=config):
        sn = sncli(sync, verbose, config)
        if sync: sn.sync_notes()
        return sn

    if args[0] == 'sync':
        sn = sncli_start(True)

    elif args[0] == 'list':

        sn = sncli_start()
        sn.cli_list_notes(regex, ' '.join(args[1:]))

    elif args[0] == 'dump':

        sn = sncli_start()
        if key:
            sn.cli_note_dump(key)
        else:
            sn.cli_dump_notes(regex, ' '.join(args[1:]))

    elif args[0] == 'create':

        if len(args) == 1:
            sn = sncli_start()
            sn.cli_note_create(False, title)
        elif len(args) == 2 and args[1] == '-':
            sn = sncli_start()
            sn.cli_note_create(True, title)
        else:
            usage()

    elif args[0] == 'edit':

        if not key:
            usage()

        sn = sncli_start()
        sn.cli_note_edit(key)

    elif args[0] == 'trash' or args[0] == 'untrash':

        if not key:
            usage()

        sn = sncli_start()
        sn.cli_note_trash(key, 1 if args[0] == 'trash' else 0)

    elif args[0] == 'pin' or args[0] == 'unpin':

        if not key:
            usage()

        sn = sncli_start()
        sn.cli_note_pin(key, 1 if args[0] == 'pin' else 0)

    elif args[0] == 'markdown' or args[0] == 'unmarkdown':

        if not key:
            usage()

        sn = sncli_start()
        sn.cli_note_markdown(key, 1 if args[0] == 'markdown' else 0)

    else:
        usage()

