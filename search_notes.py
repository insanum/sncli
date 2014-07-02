
import urwid

class SearchNotes(urwid.Edit):

    def __init__(self, config, key, callback_obj):
        self.config = config
        self.callback_obj = callback_obj
        super(SearchNotes, self).__init__(key, wrap='clip')

    def keypress(self, size, key):
        size = (size[0],) # if this isn't here then urwid freaks out...
        if key == 'esc':
            self.callback_obj.search_quit()
        elif key == 'enter':
            self.callback_obj.search_complete(self.edit_text)
        else:
            return super(SearchNotes, self).keypress(size, key)
        return None

