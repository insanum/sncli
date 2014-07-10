
import re, urwid

class ViewHelp(urwid.ListBox):

    def __init__(self, config):
        self.config = config

        lines = []
        lines.extend(self.create_kb_help_lines(u'Keybinds Common', 'common'))
        lines.extend(self.create_kb_help_lines(u'Keybinds Note List', 'titles'))
        lines.extend(self.create_kb_help_lines(u'Keybinds Note Content', 'notes'))
        lines.extend(self.create_config_help_lines())
        lines.extend(self.create_color_help_lines())
        lines.append(urwid.Text(('help_header', u'')))

        super(ViewHelp, self).__init__(urwid.SimpleFocusListWalker(lines))

    def get_status_bar(self):
        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        status_title = \
            urwid.AttrMap(urwid.Text(u'Help',
                                     wrap='clip'),
                          'status_bar')
        status_index = \
            ('pack', urwid.AttrMap(urwid.Text(u' ' +
                                              str(cur + 1) +
                                              u'/' +
                                              str(total)),
                                   'status_bar'))
        return \
            urwid.AttrMap(urwid.Columns([ status_title, status_index ]),
                          'status_bar')

    def create_kb_help_lines(self, header, use):
        lines = [ urwid.AttrMap(urwid.Text(u''),
                                'help_header',
                                'help_focus') ]
        lines.append(urwid.AttrMap(urwid.Text(u' ' + header),
                                   'help_header',
                                   'help_focus'))
        for c in self.config.keybinds:
            if use not in self.config.get_keybind_use(c):
                continue
            lines.append(
                urwid.AttrMap(urwid.AttrMap(
                    urwid.Text(
                    [
                     ('help_descr',  '{:>24}  '.format(self.config.get_keybind_descr(c))),
                     ('help_config', '{:>25}  '.format(u'kb_' + c)),
                     ('help_value',  u"'" + self.config.get_keybind(c) + u"'")
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
        lines = [ urwid.AttrMap(urwid.Text(u''),
                                'help_header',
                                'help_focus') ]
        lines.append(urwid.AttrMap(urwid.Text(u' Configuration'),
                                   'help_header',
                                   'help_focus'))
        for c in self.config.configs:
            if c in [ 'sn_username', 'sn_password' ]: continue
            lines.append(
                urwid.AttrMap(urwid.AttrMap(
                    urwid.Text(
                    [
                     ('help_descr',  '{:>24}  '.format(self.config.get_config_descr(c))),
                     ('help_config', '{:>25}  '.format(u'cfg_' + c)),
                     ('help_value',  u"'" + self.config.get_config(c) + u"'")
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
        lines = [ urwid.AttrMap(urwid.Text(u''),
                                'help_header',
                                'help_focus') ]
        lines.append(urwid.AttrMap(urwid.Text(u' Colors'),
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
                     ('help_descr',  '{:>24}  '.format(self.config.get_color_descr(c))),
                     ('help_config', '{:>25}  '.format(u'clr_' + c)),
                     (re.search('^(.*)(_fg|_bg)$', c).group(1),
                          u"'" + self.config.get_color(c) + u"'")
                    ]
                    ),
                    attr_map = None,
                    focus_map = fmap
                ), 'default', 'help_focus'))
        return lines

    def keypress(self, size, key):
        return key

