
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import os, json, tempfile

def tempfile_create(note, raw=False, tempdir=None):
    if raw:
        # dump the raw json of the note
        tf = tempfile.NamedTemporaryFile(suffix='.json', delete=False, dir=tempdir)

        contents = json.dumps(note, indent=2)
        tf.write(contents.encode('utf-8'))
        tf.flush()
    else:
        ext = '.txt'
        if note and \
           'systemTags' in note and \
           'markdown' in note['systemTags']:
            ext = '.mkd'
        tf = tempfile.NamedTemporaryFile(suffix=ext, delete=False, dir=tempdir)
        if note:
            contents = note['content']
            tf.write(contents.encode('utf-8'))
        tf.flush()
    return tf

def tempfile_delete(tf):
    if tf:
        tf.close()
        os.unlink(tf.name)

def tempfile_name(tf):
    if tf:
        return tf.name
    return ''

def tempfile_content(tf):
    # This 'hack' is needed because some editors use an intermediate temporary
    # file, and rename it to that of the correct file, overwriting it. This
    # means that the tf file handle won't be updated with the new contents, and
    # the tempfile must be re-opened and read
    if not tf:
        return None

    with open(tf.name, 'rb') as f:
        updated_tf_contents = f.read()
        return updated_tf_contents.decode('utf-8')
