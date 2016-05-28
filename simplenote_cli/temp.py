
# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

import os, json, tempfile

def tempfile_create(note, raw=False):
    if raw:
        # dump the raw json of the note
        tf = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        json.dump(note, tf, indent=2)
        tf.flush()
    else:
        ext = '.txt'
        if note and \
           'systemtags' in note and \
           'markdown' in note['systemtags']:
            ext = '.mkd'
        tf = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        if note:
            contents = note['content']
            tf.write(contents.encode('utf-8'))
        tf.flush()
    return tf

def tempfile_delete(tf):
    if tf:
        os.unlink(tf.name)

def tempfile_name(tf):
    if tf:
        return tf.name
    return ''

def tempfile_content(tf):
    # This seems like a hack. When editing with Gedit, tf file contents weren't getting 
    updated_tf_contents = open(tf.name, 'r').read()
    tf.write(updated_tf_contents.encode('utf-8'))
    return updated_tf_contents
