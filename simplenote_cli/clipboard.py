from shutil import which
from subprocess import Popen, PIPE


class Clipboard(object):
    def __init__(self):
        self.copy_command = self.get_copy_command()

    def get_copy_command(self):
        if (which('xsel')):
            return ['xsel', '-ib']
        if (which('pbcopy')):
            return ['pbcopy']
        return None

    def copy(self, text):
        if (self.copy_command):
            proc = Popen(self.copy_command, stdin=PIPE)
            proc.communicate(text.encode('utf-8'))
