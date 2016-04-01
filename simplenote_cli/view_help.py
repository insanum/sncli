
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import re, urwid

class ViewHelp(urwid.ListBox):

    def __init__(self, config):
        self.config = config

        self.descr_width  = 26
        self.config_width = 29

        lines = []
        lines.extend(self.create_kb_help_lines('Keybinds Common', 'common'))
        lines.extend(self.create_kb_help_lines('Keybinds Note List', 'titles'))
        lines.extend(self.create_kb_help_lines('Keybinds Note Content', 'notes'))
        lines.extend(self.create_config_help_lines())
        lines.extend(self.create_color_help_lines())
        lines.append(urwid.Text(('help_header', '')))

        super(ViewHelp, self).__init__(urwid.SimpleFocusListWalker(lines))

    def get_status_bar(self):
        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        status_title = \
            urwid.AttrMap(urwid.Text('Help',
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

    def create_kb_help_lines(self, header, use):
        lines = [ urwid.AttrMap(urwid.Text(''),
                                'help_header',
                                'help_focus') ]
        lines.append(urwid.AttrMap(urwid.Text(' ' + header),
                                   'help_header',
                                   'help_focus'))
        for c in self.config.keybinds:
            if use not in self.config.get_keybind_use(c):
                continue
            lines.append(
                urwid.AttrMap(urwid.AttrMap(
                    urwid.Text(
                    [
                     ('help_descr',  ('{:>' + str(self.descr_width) + '} ').format(self.config.get_keybind_descr(c))),
                     ('help_config', ('{:>' + str(self.config_width) + '} ').format('kb_' + c)),
                     ('help_value',  "'" + self.config.get_keybind(c) + "'")
                    ]
                    ),
                    attr_map = None,
                    focus_map = {
                                 'help_value'  : 'help_focus',
                                 'help_config' : 'help_focus',
                                 'help_descr'  : 'help_focus'
                                }
                ), 'default', 'help_focus'))
        return lines

    def create_config_help_lines(self):
        lines = [ urwid.AttrMap(urwid.Text(''),
                                'help_header',
                                'help_focus') ]
        lines.append(urwid.AttrMap(urwid.Text(' Configuration'),
                                   'help_header',
                                   'help_focus'))
        for c in self.config.configs:
            if c in [ 'sn_username', 'sn_password' ]: continue
            lines.append(
                urwid.AttrMap(urwid.AttrMap(
                    urwid.Text(
                    [
                     ('help_descr',  ('{:>' + str(self.descr_width) + '} ').format(self.config.get_config_descr(c))),
                     ('help_config', ('{:>' + str(self.config_width) + '} ').format('cfg_' + c)),
                     ('help_value',  "'" + self.config.get_config(c) + "'")
                    ]
                    ),
                    attr_map = None,
                    focus_map = {
                                 'help_value'  : 'help_focus',
                                 'help_config' : 'help_focus',
                                 'help_descr'  : 'help_focus'
                                }
                ), 'default', 'help_focus'))
        return lines

    def create_color_help_lines(self):
        lines = [ urwid.AttrMap(urwid.Text(''),
                                'help_header',
                                'help_focus') ]
        lines.append(urwid.AttrMap(urwid.Text(' Colors'),
                                   'help_header',
                                   'help_focus'))
        fmap = {}
        for c in self.config.colors:
            fmap[re.search('^(.*)(_fg|_bg)$', c).group(1)] = 'help_focus'
        for c in self.config.colors:
            lines.append(
                urwid.AttrMap(urwid.AttrMap(
                    urwid.Text(
                    [
                     ('help_descr',  ('{:>' + str(self.descr_width) + '} ').format(self.config.get_color_descr(c))),
                     ('help_config', ('{:>' + str(self.config_width) + '} ').format('clr_' + c)),
                     (re.search('^(.*)(_fg|_bg)$', c).group(1), "'" + self.config.get_color(c) + "'")
                    ]
                    ),
                    attr_map = None,
                    focus_map = fmap
                ), 'default', 'help_focus'))
        return lines

    def keypress(self, size, key):
        return key

