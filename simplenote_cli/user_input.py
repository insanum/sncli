
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import urwid

class UserInput(urwid.Edit):

    def __init__(self, config, caption, edit_text, callback_func, args):
        self.config = config
        self.callback_func      = callback_func
        self.callback_func_args = args
        super(UserInput, self).__init__(caption=caption,
                                        edit_text=edit_text,
                                        wrap='clip')

    def keypress(self, size, key):
        size = (size[0],) # if this isn't here then urwid freaks out...
        if key == 'esc':
            self.callback_func(self.callback_func_args, None)
        elif key == 'enter':
            self.callback_func(self.callback_func_args, self.edit_text)
        else:
            return super(UserInput, self).keypress(size, key)
        return None

