
import os, ConfigParser

class Config:

    def __init__(self):
        self.home = os.path.abspath(os.path.expanduser('~'))
        defaults = \
          {
            'sn_username'       : '',
            'sn_password'       : '',
            'db_path'           : os.path.join(self.home, '.sncli'),
            'search_mode'       : 'gstyle',
            'search_tags'       : '1',
            'sort_mode'         : '1',
            'pinned_ontop'      : '1',
            'tabstop'           : '4',
            'format_strftime'   : '%Y/%m/%d',
            'format_note_title' : '[%D] %F %-N %T',

            'kb_help'           : 'h',
            'kb_quit'           : 'q',
            'kb_down'           : 'j',
            'kb_up'             : 'k',
            'kb_page_down'      : ' ',
            'kb_page_up'        : 'b',
            'kb_half_page_down' : 'ctrl d',
            'kb_half_page_up'   : 'ctrl u',
            'kb_bottom'         : 'G',
            'kb_top'            : 'g',
            'kb_view_note'      : 'enter',
            'kb_view_log'       : 'l',
            'kb_tabstop2'       : '2',
            'kb_tabstop4'       : '4',
            'kb_tabstop8'       : '8',

            'clr_default_fg' : 'default',
            'clr_default_bg' : 'default',

            'clr_note_focus_fg' : 'white',
            'clr_note_focus_bg' : 'light red',

            'clr_note_title_day_fg' : 'light red',
            'clr_note_title_day_bg' : 'default',

            'clr_note_title_week_fg' : 'light green',
            'clr_note_title_week_bg' : 'default',

            'clr_note_title_month_fg' : 'brown',
            'clr_note_title_month_bg' : 'default',

            'clr_note_title_year_fg' : 'light blue',
            'clr_note_title_year_bg' : 'default',

            'clr_note_title_ancient_fg' : 'light blue',
            'clr_note_title_ancient_bg' : 'default',

            'clr_note_date_fg' : 'dark blue',
            'clr_note_date_bg' : 'default',

            'clr_note_flags_fg' : 'dark magenta',
            'clr_note_flags_bg' : 'default',

            'clr_note_tags_fg' : 'dark red',
            'clr_note_tags_bg' : 'default',

            'clr_note_content_fg'       : 'default',
            'clr_note_content_bg'       : 'default',
            'clr_note_content_focus_fg' : 'white',
            'clr_note_content_focus_bg' : 'light red',

            'clr_help_focus_fg'  : 'white',
            'clr_help_focus_bg'  : 'dark gray',
            'clr_help_header_fg' : 'dark blue',
            'clr_help_header_bg' : 'default',
            'clr_help_key_fg'    : 'default',
            'clr_help_key_bg'    : 'default',
            'clr_help_config_fg' : 'dark green',
            'clr_help_config_bg' : 'default',
            'clr_help_descr_fg'  : 'default',
            'clr_help_descr_bg'  : 'default'
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

        self.clr_default_fg = cp.get(cfg_sec, 'clr_default_fg')
        self.clr_default_bg = cp.get(cfg_sec, 'clr_default_bg')

        self.clr_note_focus_fg = cp.get(cfg_sec, 'clr_note_focus_fg')
        self.clr_note_focus_bg = cp.get(cfg_sec, 'clr_note_focus_bg')

        self.clr_note_title_day_fg = cp.get(cfg_sec, 'clr_note_title_day_fg')
        self.clr_note_title_day_bg = cp.get(cfg_sec, 'clr_note_title_day_bg')

        self.clr_note_title_week_fg = cp.get(cfg_sec, 'clr_note_title_week_fg')
        self.clr_note_title_week_bg = cp.get(cfg_sec, 'clr_note_title_week_bg')

        self.clr_note_title_month_fg = cp.get(cfg_sec, 'clr_note_title_month_fg')
        self.clr_note_title_month_bg = cp.get(cfg_sec, 'clr_note_title_month_bg')

        self.clr_note_title_year_fg = cp.get(cfg_sec, 'clr_note_title_year_fg')
        self.clr_note_title_year_bg = cp.get(cfg_sec, 'clr_note_title_year_bg')

        self.clr_note_title_ancient_fg = cp.get(cfg_sec, 'clr_note_title_ancient_fg')
        self.clr_note_title_ancient_bg = cp.get(cfg_sec, 'clr_note_title_ancient_bg')

        self.clr_note_date_fg = cp.get(cfg_sec, 'clr_note_date_fg')
        self.clr_note_date_bg = cp.get(cfg_sec, 'clr_note_date_bg')

        self.clr_note_flags_fg = cp.get(cfg_sec, 'clr_note_flags_fg')
        self.clr_note_flags_bg = cp.get(cfg_sec, 'clr_note_flags_bg')

        self.clr_note_tags_fg = cp.get(cfg_sec, 'clr_note_tags_fg')
        self.clr_note_tags_bg = cp.get(cfg_sec, 'clr_note_tags_bg')

        self.clr_note_content_fg       = cp.get(cfg_sec, 'clr_note_content_fg')
        self.clr_note_content_bg       = cp.get(cfg_sec, 'clr_note_content_bg')
        self.clr_note_content_focus_fg = cp.get(cfg_sec, 'clr_note_content_focus_fg')
        self.clr_note_content_focus_bg = cp.get(cfg_sec, 'clr_note_content_focus_bg')

        self.clr_help_focus_fg  = cp.get(cfg_sec, 'clr_help_focus_fg')
        self.clr_help_focus_bg  = cp.get(cfg_sec, 'clr_help_focus_bg')
        self.clr_help_header_fg = cp.get(cfg_sec, 'clr_help_header_fg')
        self.clr_help_header_bg = cp.get(cfg_sec, 'clr_help_header_bg')
        self.clr_help_key_fg    = cp.get(cfg_sec, 'clr_help_key_fg')
        self.clr_help_key_bg    = cp.get(cfg_sec, 'clr_help_key_bg')
        self.clr_help_config_fg = cp.get(cfg_sec, 'clr_help_config_fg')
        self.clr_help_config_bg = cp.get(cfg_sec, 'clr_help_config_bg')
        self.clr_help_descr_fg  = cp.get(cfg_sec, 'clr_help_descr_fg')
        self.clr_help_descr_bg  = cp.get(cfg_sec, 'clr_help_descr_bg')

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

