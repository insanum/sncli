
import os, urwid, ConfigParser

class Config:

    def __init__(self):
        self.home = os.path.abspath(os.path.expanduser('~'))
        defaults = \
        {
         'cfg_sn_username'       : '',
         'cfg_sn_password'       : '',
         'cfg_db_path'           : os.path.join(self.home, '.sncli'),
         'cfg_search_mode'       : 'gstyle', # gstyle/regex
         'cfg_search_tags'       : 'yes',
         'cfg_sort_mode'         : 'date',   # alpha/date
         'cfg_pinned_ontop'      : 'yes',
         'cfg_tabstop'           : '4',
         'cfg_format_strftime'   : '%Y/%m/%d',
         'cfg_format_note_title' : '[%D] %F %-N %T',
         'cfg_status_bar'        : 'yes',
         'cfg_editor'            : 'vim',
         'cfg_pager'             : 'less -c',
         'cfg_log_reversed'      : 'yes',

         'kb_help'            : 'h',
         'kb_quit'            : 'q',
         'kb_down'            : 'j',
         'kb_up'              : 'k',
         'kb_page_down'       : ' ',
         'kb_page_up'         : 'b',
         'kb_half_page_down'  : 'ctrl d',
         'kb_half_page_up'    : 'ctrl u',
         'kb_bottom'          : 'G',
         'kb_top'             : 'g',
         'kb_status'          : 's',
         'kb_create_note'     : 'C',
         'kb_view_note'       : 'enter',
         'kb_view_note_ext'   : 'meta enter',
         'kb_view_next_note'  : 'J',
         'kb_view_prev_note'  : 'K',
         'kb_view_log'        : 'l',
         'kb_tabstop2'        : '2',
         'kb_tabstop4'        : '4',
         'kb_tabstop8'        : '8',
         'kb_search'          : '/',
         'kb_clear_search'    : 'a',
         'kb_note_pin'        : 'p',
         'kb_note_unpin'      : 'P',
         'kb_note_markdown'   : 'm',
         'kb_note_unmarkdown' : 'M',
         'kb_note_tags'       : 't',

         'clr_default_fg'            : 'default',
         'clr_default_bg'            : 'default',
         'clr_status_bar_fg'         : 'dark gray',
         'clr_status_bar_bg'         : 'light gray',
         'clr_status_message_fg'     : 'dark gray',
         'clr_status_message_bg'     : 'light gray',
         'clr_search_bar_fg'         : 'white',
         'clr_search_bar_bg'         : 'light red',
         'clr_note_focus_fg'         : 'white',
         'clr_note_focus_bg'         : 'light red',
         'clr_note_title_day_fg'     : 'light red',
         'clr_note_title_day_bg'     : 'default',
         'clr_note_title_week_fg'    : 'light green',
         'clr_note_title_week_bg'    : 'default',
         'clr_note_title_month_fg'   : 'brown',
         'clr_note_title_month_bg'   : 'default',
         'clr_note_title_year_fg'    : 'light blue',
         'clr_note_title_year_bg'    : 'default',
         'clr_note_title_ancient_fg' : 'light blue',
         'clr_note_title_ancient_bg' : 'default',
         'clr_note_date_fg'          : 'dark blue',
         'clr_note_date_bg'          : 'default',
         'clr_note_flags_fg'         : 'dark magenta',
         'clr_note_flags_bg'         : 'default',
         'clr_note_tags_fg'          : 'dark red',
         'clr_note_tags_bg'          : 'default',
         'clr_note_content_fg'       : 'default',
         'clr_note_content_bg'       : 'default',
         'clr_note_content_focus_fg' : 'white',
         'clr_note_content_focus_bg' : 'light red',
         'clr_help_focus_fg'         : 'white',
         'clr_help_focus_bg'         : 'dark gray',
         'clr_help_header_fg'        : 'dark blue',
         'clr_help_header_bg'        : 'default',
         'clr_help_config_fg'        : 'dark green',
         'clr_help_config_bg'        : 'default',
         'clr_help_value_fg'         : 'dark red',
         'clr_help_value_bg'         : 'default',
         'clr_help_descr_fg'         : 'default',
         'clr_help_descr_bg'         : 'default'
        }

        cp = ConfigParser.SafeConfigParser(defaults)
        self.configs_read = cp.read([os.path.join(self.home, '.snclirc')])

        cfg_sec = 'sncli'

        if not cp.has_section(cfg_sec):
            cp.add_section(cfg_sec)

        self.configs = \
        {
         'sn_username'       : [ cp.get(cfg_sec, 'cfg_sn_username', raw=True),       'Simplenote Username' ],
         'sn_password'       : [ cp.get(cfg_sec, 'cfg_sn_password', raw=True),       'Simplenote Password' ],
         'db_path'           : [ cp.get(cfg_sec, 'cfg_db_path'),                     'Note storage path' ],
         'search_mode'       : [ cp.get(cfg_sec, 'cfg_search_mode'),                 'Search mode' ],
         'search_tags'       : [ cp.get(cfg_sec, 'cfg_search_tags'),                 'Search tags as well' ],
         'sort_mode'         : [ cp.get(cfg_sec, 'cfg_sort_mode'),                   'Sort mode' ],
         'pinned_ontop'      : [ cp.get(cfg_sec, 'cfg_pinned_ontop'),                'Pinned at top of list' ],
         'tabstop'           : [ cp.get(cfg_sec, 'cfg_tabstop'),                     'Tabstop spaces' ],
         'format_strftime'   : [ cp.get(cfg_sec, 'cfg_format_strftime', raw=True),   'Date strftime format' ],
         'format_note_title' : [ cp.get(cfg_sec, 'cfg_format_note_title', raw=True), 'Note title format' ],
         'status_bar'        : [ cp.get(cfg_sec, 'cfg_status_bar'),                  'Status bar location' ],
         'editor'            : [ cp.get(cfg_sec, 'cfg_editor'),                      'Editor' ],
         'pager'             : [ cp.get(cfg_sec, 'cfg_pager'),                       'External pager' ],
         'log_reversed'      : [ cp.get(cfg_sec, 'cfg_log_reversed'),                'Log file reversed' ]
        }

        self.keybinds = \
        {
         'help'            : [ cp.get(cfg_sec, 'kb_help'),            [ 'common' ], 'Help' ],
         'quit'            : [ cp.get(cfg_sec, 'kb_quit'),            [ 'common' ], 'Quit' ],
         'down'            : [ cp.get(cfg_sec, 'kb_down'),            [ 'common' ], 'Scroll down one line' ],
         'up'              : [ cp.get(cfg_sec, 'kb_up'),              [ 'common' ], 'Scroll up one line' ],
         'page_down'       : [ cp.get(cfg_sec, 'kb_page_down'),       [ 'common' ], 'Page down' ],
         'page_up'         : [ cp.get(cfg_sec, 'kb_page_up'),         [ 'common' ], 'Page up' ],
         'half_page_down'  : [ cp.get(cfg_sec, 'kb_half_page_down'),  [ 'common' ], 'Half page down' ],
         'half_page_up'    : [ cp.get(cfg_sec, 'kb_half_page_up'),    [ 'common' ], 'Half page up' ],
         'bottom'          : [ cp.get(cfg_sec, 'kb_bottom'),          [ 'common' ], 'Goto bottom' ],
         'top'             : [ cp.get(cfg_sec, 'kb_top'),             [ 'common' ], 'Goto top' ],
         'status'          : [ cp.get(cfg_sec, 'kb_status'),          [ 'common' ], 'Toggle status bar' ],
         'view_log'        : [ cp.get(cfg_sec, 'kb_view_log'),        [ 'common' ], 'View log' ],
         'create_note'     : [ cp.get(cfg_sec, 'kb_create_note'),     [ 'titles' ], 'Create a new note' ],
         'view_note'       : [ cp.get(cfg_sec, 'kb_view_note'),       [ 'titles' ], 'View note' ],
         'view_note_ext'   : [ cp.get(cfg_sec, 'kb_view_note_ext'),   [ 'titles' ], 'View note with pager' ],
         'view_next_note'  : [ cp.get(cfg_sec, 'kb_view_next_note'),  [ 'notes'  ], 'View next note' ],
         'view_prev_note'  : [ cp.get(cfg_sec, 'kb_view_prev_note'),  [ 'notes'  ], 'View previous note' ],
         'tabstop2'        : [ cp.get(cfg_sec, 'kb_tabstop2'),        [ 'notes'  ], 'View with tabstop=2' ],
         'tabstop4'        : [ cp.get(cfg_sec, 'kb_tabstop4'),        [ 'notes'  ], 'View with tabstop=4' ],
         'tabstop8'        : [ cp.get(cfg_sec, 'kb_tabstop8'),        [ 'notes'  ], 'View with tabstop=8' ],
         'search'          : [ cp.get(cfg_sec, 'kb_search'),          [ 'titles' ], 'Search notes' ],
         'clear_search'    : [ cp.get(cfg_sec, 'kb_clear_search'),    [ 'titles' ], 'Show all notes' ],
         'note_pin'        : [ cp.get(cfg_sec, 'kb_note_pin'),        [ 'titles' ], 'Pin note' ],
         'note_unpin'      : [ cp.get(cfg_sec, 'kb_note_unpin'),      [ 'titles' ], 'Unpin note' ],
         'note_markdown'   : [ cp.get(cfg_sec, 'kb_note_markdown'),   [ 'titles' ], 'Flag note as markdown' ],
         'note_unmarkdown' : [ cp.get(cfg_sec, 'kb_note_unmarkdown'), [ 'titles' ], 'Unflag note as markdown' ],
         'note_tags'       : [ cp.get(cfg_sec, 'kb_note_tags'),       [ 'titles' ], 'Edit note tags' ]
        }

        self.colors = \
        {
         'default_fg'            : [ cp.get(cfg_sec, 'clr_default_fg'),            'Default fg' ],
         'default_bg'            : [ cp.get(cfg_sec, 'clr_default_bg'),            'Default bg' ],
         'status_bar_fg'         : [ cp.get(cfg_sec, 'clr_status_bar_fg'),         'Status bar fg' ],
         'status_bar_bg'         : [ cp.get(cfg_sec, 'clr_status_bar_bg'),         'Status bar bg' ],
         'status_message_fg'     : [ cp.get(cfg_sec, 'clr_status_message_fg'),     'Status message fg' ],
         'status_message_bg'     : [ cp.get(cfg_sec, 'clr_status_message_bg'),     'Status message bg' ],
         'search_bar_fg'         : [ cp.get(cfg_sec, 'clr_search_bar_fg'),         'Search bar fg' ],
         'search_bar_bg'         : [ cp.get(cfg_sec, 'clr_search_bar_bg'),         'Search bar bg' ],
         'note_focus_fg'         : [ cp.get(cfg_sec, 'clr_note_focus_fg'),         'Note title focus fg' ],
         'note_focus_bg'         : [ cp.get(cfg_sec, 'clr_note_focus_bg'),         'Note title focus bg' ],
         'note_title_day_fg'     : [ cp.get(cfg_sec, 'clr_note_title_day_fg'),     'Day old note title fg' ],
         'note_title_day_bg'     : [ cp.get(cfg_sec, 'clr_note_title_day_bg'),     'Day old note title bg' ],
         'note_title_week_fg'    : [ cp.get(cfg_sec, 'clr_note_title_week_fg'),    'Week old note title fg' ],
         'note_title_week_bg'    : [ cp.get(cfg_sec, 'clr_note_title_week_bg'),    'Week old note title bg' ],
         'note_title_month_fg'   : [ cp.get(cfg_sec, 'clr_note_title_month_fg'),   'Month old note title fg' ],
         'note_title_month_bg'   : [ cp.get(cfg_sec, 'clr_note_title_month_bg'),   'Month old note title bg' ],
         'note_title_year_fg'    : [ cp.get(cfg_sec, 'clr_note_title_year_fg'),    'Year old note title fg' ],
         'note_title_year_bg'    : [ cp.get(cfg_sec, 'clr_note_title_year_bg'),    'Year old note title bg' ],
         'note_title_ancient_fg' : [ cp.get(cfg_sec, 'clr_note_title_ancient_fg'), 'Ancient note title fg' ],
         'note_title_ancient_bg' : [ cp.get(cfg_sec, 'clr_note_title_ancient_bg'), 'Ancient note title bg' ],
         'note_date_fg'          : [ cp.get(cfg_sec, 'clr_note_date_fg'),          'Note date fg' ],
         'note_date_bg'          : [ cp.get(cfg_sec, 'clr_note_date_bg'),          'Note date bg' ],
         'note_flags_fg'         : [ cp.get(cfg_sec, 'clr_note_flags_fg'),         'Note flags fg' ],
         'note_flags_bg'         : [ cp.get(cfg_sec, 'clr_note_flags_bg'),         'Note flags bg' ],
         'note_tags_fg'          : [ cp.get(cfg_sec, 'clr_note_tags_fg'),          'Note tags fg' ],
         'note_tags_bg'          : [ cp.get(cfg_sec, 'clr_note_tags_bg'),          'Note tags bg' ],
         'note_content_fg'       : [ cp.get(cfg_sec, 'clr_note_content_fg'),       'Note content fg' ],
         'note_content_bg'       : [ cp.get(cfg_sec, 'clr_note_content_bg'),       'Note content bg' ],
         'note_content_focus_fg' : [ cp.get(cfg_sec, 'clr_note_content_focus_fg'), 'Note content focus fg' ],
         'note_content_focus_bg' : [ cp.get(cfg_sec, 'clr_note_content_focus_bg'), 'Note content focus bg' ],
         'help_focus_fg'         : [ cp.get(cfg_sec, 'clr_help_focus_fg'),         'Help focus fg' ],
         'help_focus_bg'         : [ cp.get(cfg_sec, 'clr_help_focus_bg'),         'Help focus bg' ],
         'help_header_fg'        : [ cp.get(cfg_sec, 'clr_help_header_fg'),        'Help header fg' ],
         'help_header_bg'        : [ cp.get(cfg_sec, 'clr_help_header_bg'),        'Help header bg' ],
         'help_config_fg'        : [ cp.get(cfg_sec, 'clr_help_config_fg'),        'Help config fg' ],
         'help_config_bg'        : [ cp.get(cfg_sec, 'clr_help_config_bg'),        'Help config bg' ],
         'help_value_fg'         : [ cp.get(cfg_sec, 'clr_help_value_fg'),         'Help value fg' ],
         'help_value_bg'         : [ cp.get(cfg_sec, 'clr_help_value_bg'),         'Help value bg' ],
         'help_descr_fg'         : [ cp.get(cfg_sec, 'clr_help_descr_fg'),         'Help description fg' ],
         'help_descr_bg'         : [ cp.get(cfg_sec, 'clr_help_descr_bg'),         'Help description bg' ]
        }

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

