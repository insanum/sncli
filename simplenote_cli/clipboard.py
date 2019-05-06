import os
from distutils import spawn
from subprocess import Popen, PIPE


class Clipboard(object):
    def __init__(self):
        self.copy_command = self.get_copy_command()

    def get_copy_command(self):
        if (spawn.find_executable('xsel')):
            return ['xsel', '-ib']
        if (spawn.find_executable('pbcopy')):
            return ['pbcopy']
        return None

    def copy(self, text):
        if (self.copy_command):
            proc = Popen(self.copy_command, stdin=PIPE)
            proc.communicate(text.encode('utf-8'))
