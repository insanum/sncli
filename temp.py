
import os, tempfile

def tempfile_create(note):
    ext = '.txt'
    if note and 'markdown' in note['systemtags']:
        ext = '.mkd'
    tf = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    if note:
        tf.write(note['content'])
    tf.flush()
    return tf

def tempfile_delete(tf):
    if tf:
        os.unlink(tf.name)

def tempfile_name(tf):
    if tf:
        return tf.name
    return ''

