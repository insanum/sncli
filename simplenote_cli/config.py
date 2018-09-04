
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import os, sys, urwid, collections, configparser, subprocess

class Config:

    def __init__(self, custom_file=None):
        self.home = os.path.abspath(os.path.expanduser('~'))
        defaults = \
        {
         'cfg_sn_username'       : '',
         'cfg_sn_password'       : '',
         'cfg_db_path'           : os.path.join(self.home, '.sncli'),
         'cfg_search_tags'       : 'yes',  # with regex searches
         'cfg_sort_mode'         : 'date', # 'alpha' or 'date'
         'cfg_pinned_ontop'      : 'yes',
         'cfg_tabstop'           : '4',
         'cfg_format_strftime'   : '%Y/%m/%d',
         'cfg_format_note_title' : '[%D] %F %-N %T',
         'cfg_status_bar'        : 'yes',
         'cfg_editor'            : os.environ['EDITOR'] if 'EDITOR' in os.environ else 'vim {fname} +{line}',
         'cfg_pager'             : os.environ['PAGER'] if 'PAGER' in os.environ else 'less -c',
         'cfg_diff'              : 'diff -b -U10',
         'cfg_max_logs'          : '5',
         'cfg_log_timeout'       : '5',
         'cfg_log_reversed'      : 'yes',
         'cfg_tempdir'           : '',

         'kb_help'            : 'h',
         'kb_quit'            : 'q',
         'kb_sync'            : 'S',
         'kb_down'            : 'j',
         'kb_up'              : 'k',
         'kb_page_down'       : 'space',
         'kb_page_up'         : 'b',
         'kb_half_page_down'  : 'ctrl d',
         'kb_half_page_up'    : 'ctrl u',
         'kb_bottom'          : 'G',
         'kb_top'             : 'g',
         'kb_status'          : 's',
         'kb_create_note'     : 'C',
         'kb_edit_note'       : 'e',
         'kb_view_note'       : 'enter',
         'kb_view_note_ext'   : 'meta enter',
         'kb_view_note_json'  : 'O',
         'kb_pipe_note'       : '|',
         'kb_view_next_note'  : 'J',
         'kb_view_prev_note'  : 'K',
         'kb_view_log'        : 'l',
         'kb_tabstop2'        : '2',
         'kb_tabstop4'        : '4',
         'kb_tabstop8'        : '8',
         'kb_prev_version'    : '<',
         'kb_next_version'    : '>',
         'kb_diff_version'    : 'D',
         'kb_restore_version' : 'R',
         'kb_latest_version'  : 'L',
         'kb_select_version'  : '#',
         'kb_search_gstyle'   : '/',
         'kb_search_regex'    : 'meta /',
         'kb_search_prev_gstyle'   : '?',
         'kb_search_prev_regex'   : 'meta ?',
         'kb_search_next'     : 'n',
         'kb_search_prev'     : 'N',
         'kb_clear_search'    : 'A',
         'kb_sort_date'       : 'd',
         'kb_sort_alpha'      : 'a',
         'kb_sort_tags'       : 'ctrl t',
         'kb_note_trash'      : 'T',
         'kb_note_pin'        : 'p',
         'kb_note_markdown'   : 'm',
         'kb_note_tags'       : 't',
         'kb_copy_note_text'  : 'y',

         'clr_default_fg'                : 'default',
         'clr_default_bg'                : 'default',
         'clr_status_bar_fg'             : 'dark gray',
         'clr_status_bar_bg'             : 'light gray',
         'clr_log_fg'                    : 'dark gray',
         'clr_log_bg'                    : 'light gray',
         'clr_user_input_bar_fg'         : 'white',
         'clr_user_input_bar_bg'         : 'light red',
         'clr_note_focus_fg'             : 'white',
         'clr_note_focus_bg'             : 'light red',
         'clr_note_title_day_fg'         : 'light red',
         'clr_note_title_day_bg'         : 'default',
         'clr_note_title_week_fg'        : 'light green',
         'clr_note_title_week_bg'        : 'default',
         'clr_note_title_month_fg'       : 'brown',
         'clr_note_title_month_bg'       : 'default',
         'clr_note_title_year_fg'        : 'light blue',
         'clr_note_title_year_bg'        : 'default',
         'clr_note_title_ancient_fg'     : 'light blue',
         'clr_note_title_ancient_bg'     : 'default',
         'clr_note_date_fg'              : 'dark blue',
         'clr_note_date_bg'              : 'default',
         'clr_note_flags_fg'             : 'dark magenta',
         'clr_note_flags_bg'             : 'default',
         'clr_note_tags_fg'              : 'dark red',
         'clr_note_tags_bg'              : 'default',
         'clr_note_content_fg'           : 'default',
         'clr_note_content_bg'           : 'default',
         'clr_note_content_focus_fg'     : 'white',
         'clr_note_content_focus_bg'     : 'light red',
         'clr_note_content_old_fg'       : 'yellow',
         'clr_note_content_old_bg'       : 'dark gray',
         'clr_note_content_old_focus_fg' : 'white',
         'clr_note_content_old_focus_bg' : 'light red',
         'clr_help_focus_fg'             : 'white',
         'clr_help_focus_bg'             : 'light red',
         'clr_help_header_fg'            : 'dark blue',
         'clr_help_header_bg'            : 'default',
         'clr_help_config_fg'            : 'dark green',
         'clr_help_config_bg'            : 'default',
         'clr_help_value_fg'             : 'dark red',
         'clr_help_value_bg'             : 'default',
         'clr_help_descr_fg'             : 'default',
         'clr_help_descr_bg'             : 'default'
        }

        cp = configparser.SafeConfigParser(defaults)
        if custom_file is not None:
            self.configs_read = cp.read([custom_file])
        else:
            self.configs_read = cp.read([os.path.join(self.home, '.snclirc')])

        cfg_sec = 'sncli'

        if not cp.has_section(cfg_sec):
            cp.add_section(cfg_sec)


        # special handling for password so we can retrieve it by running a command
        sn_password = cp.get(cfg_sec, 'cfg_sn_password', raw=True)
        if not sn_password:
            command = cp.get(cfg_sec, 'cfg_sn_password_eval', raw=True)
            if command:
                try:
                    sn_password = subprocess.check_output(command, shell=True, universal_newlines=True)
                    # remove trailing newlines to avoid requiring butchering shell commands (they can't usually be in passwords anyway)
                    sn_password = sn_password.rstrip('\n')
                except subprocess.CalledProcessError as e:
                    print('Error evaluating command for password.')
                    print(e)
                    sys.exit(1)

        # ordered dicts used to ease help

        self.configs = collections.OrderedDict()
        self.configs['sn_username'] = [ cp.get(cfg_sec, 'cfg_sn_username', raw=True), 'Simplenote Username' ]
        self.configs['sn_password'] = [ sn_password, 'Simplenote Password' ]
        self.configs['db_path'] = [ cp.get(cfg_sec, 'cfg_db_path'), 'Note storage path' ]
        self.configs['search_tags'] = [ cp.get(cfg_sec, 'cfg_search_tags'), 'Search tags as well' ]
        self.configs['sort_mode'] = [ cp.get(cfg_sec, 'cfg_sort_mode'), 'Sort mode' ]
        self.configs['pinned_ontop'] = [ cp.get(cfg_sec, 'cfg_pinned_ontop'), 'Pinned at top of list' ]
        self.configs['tabstop'] = [ cp.get(cfg_sec, 'cfg_tabstop'), 'Tabstop spaces' ]
        self.configs['format_strftime'] = [ cp.get(cfg_sec, 'cfg_format_strftime', raw=True), 'Date strftime format' ]
        self.configs['format_note_title'] = [ cp.get(cfg_sec, 'cfg_format_note_title', raw=True), 'Note title format' ]
        self.configs['status_bar'] = [ cp.get(cfg_sec, 'cfg_status_bar'), 'Show the status bar' ]
        self.configs['editor'] = [ cp.get(cfg_sec, 'cfg_editor'), 'Editor command' ]
        self.configs['pager'] = [ cp.get(cfg_sec, 'cfg_pager'), 'External pager command' ]
        self.configs['diff'] = [ cp.get(cfg_sec, 'cfg_diff'), 'External diff command' ]
        self.configs['max_logs'] = [ cp.get(cfg_sec, 'cfg_max_logs'), 'Max logs in footer' ]
        self.configs['log_timeout'] = [ cp.get(cfg_sec, 'cfg_log_timeout'), 'Log timeout' ]
        self.configs['log_reversed'] = [ cp.get(cfg_sec, 'cfg_log_reversed'), 'Log file reversed' ]
        self.configs['tempdir'] = [ cp.get(cfg_sec, 'cfg_tempdir'), 'Temporary directory for note storage' ]

        self.keybinds = collections.OrderedDict()
        self.keybinds['help'] = [ cp.get(cfg_sec, 'kb_help'), [ 'common' ], 'Help' ]
        self.keybinds['quit'] = [ cp.get(cfg_sec, 'kb_quit'), [ 'common' ], 'Quit' ]
        self.keybinds['sync'] = [ cp.get(cfg_sec, 'kb_sync'), [ 'common' ], 'Full sync' ]
        self.keybinds['down'] = [ cp.get(cfg_sec, 'kb_down'), [ 'common' ], 'Scroll down one line' ]
        self.keybinds['up'] = [ cp.get(cfg_sec, 'kb_up'), [ 'common' ], 'Scroll up one line' ]
        self.keybinds['page_down'] = [ cp.get(cfg_sec, 'kb_page_down'), [ 'common' ], 'Page down' ]
        self.keybinds['page_up'] = [ cp.get(cfg_sec, 'kb_page_up'), [ 'common' ], 'Page up' ]
        self.keybinds['half_page_down'] = [ cp.get(cfg_sec, 'kb_half_page_down'), [ 'common' ], 'Half page down' ]
        self.keybinds['half_page_up'] = [ cp.get(cfg_sec, 'kb_half_page_up'), [ 'common' ], 'Half page up' ]
        self.keybinds['bottom'] = [ cp.get(cfg_sec, 'kb_bottom'), [ 'common' ], 'Goto bottom' ]
        self.keybinds['top'] = [ cp.get(cfg_sec, 'kb_top'), [ 'common' ], 'Goto top' ]
        self.keybinds['status'] = [ cp.get(cfg_sec, 'kb_status'), [ 'common' ], 'Toggle status bar' ]
        self.keybinds['view_log'] = [ cp.get(cfg_sec, 'kb_view_log'), [ 'common' ], 'View log' ]
        self.keybinds['create_note'] = [ cp.get(cfg_sec, 'kb_create_note'), [ 'titles' ], 'Create a new note' ]
        self.keybinds['edit_note'] = [ cp.get(cfg_sec, 'kb_edit_note'), [ 'titles', 'notes' ], 'Edit note' ]
        self.keybinds['view_note'] = [ cp.get(cfg_sec, 'kb_view_note'), [ 'titles' ], 'View note' ]
        self.keybinds['view_note_ext'] = [ cp.get(cfg_sec, 'kb_view_note_ext'), [ 'titles', 'notes' ], 'View note with pager' ]
        self.keybinds['view_note_json'] = [ cp.get(cfg_sec, 'kb_view_note_json'), [ 'titles', 'notes' ], 'View note raw json' ]
        self.keybinds['pipe_note'] = [ cp.get(cfg_sec, 'kb_pipe_note'), [ 'titles', 'notes' ], 'Pipe note contents' ]
        self.keybinds['view_next_note'] = [ cp.get(cfg_sec, 'kb_view_next_note'), [ 'notes' ], 'View next note' ]
        self.keybinds['view_prev_note'] = [ cp.get(cfg_sec, 'kb_view_prev_note'), [ 'notes' ], 'View previous note' ]
        self.keybinds['tabstop2'] = [ cp.get(cfg_sec, 'kb_tabstop2'), [ 'notes' ], 'View with tabstop=2' ]
        self.keybinds['tabstop4'] = [ cp.get(cfg_sec, 'kb_tabstop4'), [ 'notes' ], 'View with tabstop=4' ]
        self.keybinds['tabstop8'] = [ cp.get(cfg_sec, 'kb_tabstop8'), [ 'notes' ], 'View with tabstop=8' ]
        self.keybinds['prev_version'] = [ cp.get(cfg_sec, 'kb_prev_version'), [ 'notes' ], 'View previous version' ]
        self.keybinds['next_version'] = [ cp.get(cfg_sec, 'kb_next_version'), [ 'notes' ], 'View next version' ]
        self.keybinds['diff_version'] = [ cp.get(cfg_sec, 'kb_diff_version'), [ 'notes' ], 'Diff version of note' ]
        self.keybinds['restore_version'] = [ cp.get(cfg_sec, 'kb_restore_version'), [ 'notes' ], 'Restore version of note' ]
        self.keybinds['latest_version'] = [ cp.get(cfg_sec, 'kb_latest_version'), [ 'notes' ], 'View latest version' ]
        self.keybinds['select_version'] = [ cp.get(cfg_sec, 'kb_select_version'), [ 'notes' ], 'Select version' ]
        self.keybinds['search_gstyle'] = [ cp.get(cfg_sec, 'kb_search_gstyle'), [ 'titles', 'notes' ], 'Search using gstyle' ]
        self.keybinds['search_prev_gstyle'] = [ cp.get(cfg_sec, 'kb_search_prev_gstyle'), [ 'notes' ], 'Search backwards using gstyle' ]
        self.keybinds['search_regex'] = [ cp.get(cfg_sec, 'kb_search_regex'), [ 'titles', 'notes' ], 'Search using regex' ]
        self.keybinds['search_prev_regex'] = [ cp.get(cfg_sec, 'kb_search_prev_regex'), [ 'notes' ], 'Search backwards using regex' ]
        self.keybinds['search_next'] = [ cp.get(cfg_sec, 'kb_search_next'), [ 'notes' ], 'Go to next search result' ]
        self.keybinds['search_prev'] = [ cp.get(cfg_sec, 'kb_search_prev'), [ 'notes' ], 'Go to previous search result' ]
        self.keybinds['clear_search'] = [ cp.get(cfg_sec, 'kb_clear_search'), [ 'titles' ], 'Show all notes' ]
        self.keybinds['sort_date'] = [ cp.get(cfg_sec, 'kb_sort_date'), [ 'titles' ], 'Sort notes by date' ]
        self.keybinds['sort_alpha'] = [ cp.get(cfg_sec, 'kb_sort_alpha'), [ 'titles' ], 'Sort notes by alpha' ]
        self.keybinds['sort_tags'] = [ cp.get(cfg_sec, 'kb_sort_tags'), [ 'titles' ], 'Sort notes by tags' ]
        self.keybinds['note_trash'] = [ cp.get(cfg_sec, 'kb_note_trash'), [ 'titles', 'notes' ], 'Trash a note' ]
        self.keybinds['note_pin'] = [ cp.get(cfg_sec, 'kb_note_pin'), [ 'titles', 'notes' ], 'Pin note' ]
        self.keybinds['note_markdown'] = [ cp.get(cfg_sec, 'kb_note_markdown'), [ 'titles', 'notes' ], 'Flag note as markdown' ]
        self.keybinds['note_tags'] = [ cp.get(cfg_sec, 'kb_note_tags'), [ 'titles', 'notes' ], 'Edit note tags' ]
        self.keybinds['copy_note_text'] = [ cp.get(cfg_sec, 'kb_copy_note_text'), [ 'notes' ], 'Copy line (xsel/pbcopy)' ]

        self.colors = collections.OrderedDict()
        self.colors['default_fg'] = [ cp.get(cfg_sec, 'clr_default_fg'), 'Default fg' ]
        self.colors['default_bg'] = [ cp.get(cfg_sec, 'clr_default_bg'), 'Default bg' ]
        self.colors['status_bar_fg'] = [ cp.get(cfg_sec, 'clr_status_bar_fg'), 'Status bar fg' ]
        self.colors['status_bar_bg'] = [ cp.get(cfg_sec, 'clr_status_bar_bg'), 'Status bar bg' ]
        self.colors['log_fg'] = [ cp.get(cfg_sec, 'clr_log_fg'), 'Log message fg' ]
        self.colors['log_bg'] = [ cp.get(cfg_sec, 'clr_log_bg'), 'Log message bg' ]
        self.colors['user_input_bar_fg'] = [ cp.get(cfg_sec, 'clr_user_input_bar_fg'), 'User input bar fg' ]
        self.colors['user_input_bar_bg'] = [ cp.get(cfg_sec, 'clr_user_input_bar_bg'), 'User input bar bg' ]
        self.colors['note_focus_fg'] = [ cp.get(cfg_sec, 'clr_note_focus_fg'), 'Note title focus fg' ]
        self.colors['note_focus_bg'] = [ cp.get(cfg_sec, 'clr_note_focus_bg'), 'Note title focus bg' ]
        self.colors['note_title_day_fg'] = [ cp.get(cfg_sec, 'clr_note_title_day_fg'), 'Day old note title fg' ]
        self.colors['note_title_day_bg'] = [ cp.get(cfg_sec, 'clr_note_title_day_bg'), 'Day old note title bg' ]
        self.colors['note_title_week_fg'] = [ cp.get(cfg_sec, 'clr_note_title_week_fg'), 'Week old note title fg' ]
        self.colors['note_title_week_bg'] = [ cp.get(cfg_sec, 'clr_note_title_week_bg'), 'Week old note title bg' ]
        self.colors['note_title_month_fg'] = [ cp.get(cfg_sec, 'clr_note_title_month_fg'), 'Month old note title fg' ]
        self.colors['note_title_month_bg'] = [ cp.get(cfg_sec, 'clr_note_title_month_bg'), 'Month old note title bg' ]
        self.colors['note_title_year_fg'] = [ cp.get(cfg_sec, 'clr_note_title_year_fg'), 'Year old note title fg' ]
        self.colors['note_title_year_bg'] = [ cp.get(cfg_sec, 'clr_note_title_year_bg'), 'Year old note title bg' ]
        self.colors['note_title_ancient_fg'] = [ cp.get(cfg_sec, 'clr_note_title_ancient_fg'), 'Ancient note title fg' ]
        self.colors['note_title_ancient_bg'] = [ cp.get(cfg_sec, 'clr_note_title_ancient_bg'), 'Ancient note title bg' ]
        self.colors['note_date_fg'] = [ cp.get(cfg_sec, 'clr_note_date_fg'), 'Note date fg' ]
        self.colors['note_date_bg'] = [ cp.get(cfg_sec, 'clr_note_date_bg'), 'Note date bg' ]
        self.colors['note_flags_fg'] = [ cp.get(cfg_sec, 'clr_note_flags_fg'), 'Note flags fg' ]
        self.colors['note_flags_bg'] = [ cp.get(cfg_sec, 'clr_note_flags_bg'), 'Note flags bg' ]
        self.colors['note_tags_fg'] = [ cp.get(cfg_sec, 'clr_note_tags_fg'), 'Note tags fg' ]
        self.colors['note_tags_bg'] = [ cp.get(cfg_sec, 'clr_note_tags_bg'), 'Note tags bg' ]
        self.colors['note_content_fg'] = [ cp.get(cfg_sec, 'clr_note_content_fg'), 'Note content fg' ]
        self.colors['note_content_bg'] = [ cp.get(cfg_sec, 'clr_note_content_bg'), 'Note content bg' ]
        self.colors['note_content_focus_fg'] = [ cp.get(cfg_sec, 'clr_note_content_focus_fg'), 'Note content focus fg' ]
        self.colors['note_content_focus_bg'] = [ cp.get(cfg_sec, 'clr_note_content_focus_bg'), 'Note content focus bg' ]
        self.colors['note_content_old_fg'] = [ cp.get(cfg_sec, 'clr_note_content_old_fg'), 'Old note content fg' ]
        self.colors['note_content_old_bg'] = [ cp.get(cfg_sec, 'clr_note_content_old_bg'), 'Old note content bg' ]
        self.colors['note_content_old_focus_fg'] = [ cp.get(cfg_sec, 'clr_note_content_old_focus_fg'), 'Old note content focus fg' ]
        self.colors['note_content_old_focus_bg'] = [ cp.get(cfg_sec, 'clr_note_content_old_focus_bg'), 'Old note content focus bg' ]
        self.colors['help_focus_fg'] = [ cp.get(cfg_sec, 'clr_help_focus_fg'), 'Help focus fg' ]
        self.colors['help_focus_bg'] = [ cp.get(cfg_sec, 'clr_help_focus_bg'), 'Help focus bg' ]
        self.colors['help_header_fg'] = [ cp.get(cfg_sec, 'clr_help_header_fg'), 'Help header fg' ]
        self.colors['help_header_bg'] = [ cp.get(cfg_sec, 'clr_help_header_bg'), 'Help header bg' ]
        self.colors['help_config_fg'] = [ cp.get(cfg_sec, 'clr_help_config_fg'), 'Help config fg' ]
        self.colors['help_config_bg'] = [ cp.get(cfg_sec, 'clr_help_config_bg'), 'Help config bg' ]
        self.colors['help_value_fg'] = [ cp.get(cfg_sec, 'clr_help_value_fg'), 'Help value fg' ]
        self.colors['help_value_bg'] = [ cp.get(cfg_sec, 'clr_help_value_bg'), 'Help value bg' ]
        self.colors['help_descr_fg'] = [ cp.get(cfg_sec, 'clr_help_descr_fg'), 'Help description fg' ]
        self.colors['help_descr_bg'] = [ cp.get(cfg_sec, 'clr_help_descr_bg'), 'Help description bg' ]

    def get_config(self, name):
        return self.configs[name][0]

    def get_config_descr(self, name):
        return self.configs[name][1]

    def get_keybind(self, name):
        return self.keybinds[name][0]

    def get_keybind_use(self, name):
        return self.keybinds[name][1]

    def get_keybind_descr(self, name):
        return self.keybinds[name][2]

    def get_color(self, name):
        return self.colors[name][0]

    def get_color_descr(self, name):
        return self.colors[name][1]

