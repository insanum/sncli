
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import urwid

class ViewLog(urwid.ListBox):

    def __init__(self, config):
        self.config = config
        super(ViewLog, self).__init__(urwid.SimpleFocusListWalker([]))

    def update_log(self):
        lines = []
        f = open(self.config.logfile)
        for line in f:
            lines.append(
                urwid.AttrMap(urwid.Text(line.rstrip()),
                                'note_content',
                                'note_content_focus'))
        f.close()
        if self.config.get_config('log_reversed') == 'yes':
            lines.reverse()
        self.body[:] = urwid.SimpleFocusListWalker(lines)
        self.focus_position = 0

    def get_status_bar(self):
        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        status_title = \
            urwid.AttrMap(urwid.Text('Sync Log',
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

    def keypress(self, size, key):
        return key

