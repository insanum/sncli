import os
from distutils import spawn


class Clipboard(object):
    def __init__(self):
        self.copy_command = self.get_copy_command()

    def get_copy_command(self):
        if (spawn.find_executable('xsel')):
            return 'echo "%s" | xsel -ib'
        if (spawn.find_executable('pbcopy')):
            return 'echo "%s" | pbcopy'
        return None
    
    def copy(self, text):
        if (self.copy_command):
            os.system(self.copy_command % text)
