
import urwid

class ViewLog(urwid.ListBox):

    def __init__(self, config, args):
        self.config = config
        f = open(self.config.logfile)
        lines = []
        for line in f:
            lines.append(
                urwid.AttrMap(urwid.Text(line.rstrip()),
                                'note_content',
                                'note_content_focus'))
        f.close()
        super(ViewLog, self).__init__(urwid.SimpleFocusListWalker(lines))

    def get_status_bar(self):
        cur   = -1
        total = 0
        if len(self.body.positions()) > 0:
            cur   = self.focus_position
            total = len(self.body.positions())

        status_title = \
            urwid.AttrMap(urwid.Text(u'Sync Log',
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

