sncli
#####
Simplenote Command Line Interface

.. image:: ../screenshots/screenshot1.png
 :width: 90%
 :align: center

sncli is a Python application that gives you access to your Simplenote account via the command line. You can access your notes via a customizable console GUI that implements vi-like keybinds or via a simple command line interface that you can script.

Notes can be viewed/created/edited in both an online and offline mode. All changes are saved to a local cache on disk and automatically sync'ed when sncli is brought online.

.. topic:: GitHub
        
 This project is on `GitHub`_ and pull requests are welcome.

Console GUI Features
********************

+ full two-way sync with Simplenote performed dynamically in the background
+ all actions logged and easily reviewed
+ list note titles (configurable format w/ title, date, flags, tags, keys, etc)
+ sort notes by date, alpha by title, tags, pinned on top
+ search for notes using a Google style search pattern or Regular Expression
+ view note contents and meta data
+ view and restore previous versions of notes
+ pipe note contents to external command
+ create and edit notes (using your editor)
+ edit note tags
+ trash/untrash notes
+ pin/unpin notes
+ flag notes as markdown or not
+ vi-like keybinds (fully configurable)
+ Colors! (fully configurable)

Command Line Scripting
**********************

+ force a full two-way sync with Simplenote
+ all actions logged and easily reviewed
+ list note titles and keys
+ search for notes using a Google style search pattern or Regular Expression
+ dump note contents
+ create a new note (via stdin or editor)
+ import a note with raw json data (stdin or editor)
+ edit a note (via editor)
+ trash/untrash a note
+ pin/unpin a note
+ flag note as markdown or not
+ view and edit note tags

Editing Notes
*************

The flow sncli uses for editing notes is:

1. Create temporary file.
2. Load the note contents into it.
3. Launch the editor with the file.
4. Wait for the editor to exit.
5. Load the file contents into the internal note.

As a result, the note doesn't get updated in sncli until the editor is closed. By default, the temporary file is created in the OS's default temporary directory (eg. ``/tmp/`` on Linux). This can be changed with the ``cfg_tempdir`` option. This may be useful to create temporary files on a persistent file system to avoid data loss.

.. _search:

Search Styles
*************

sncli supports two styles of search strings. First is a Google style search string and second is a Regular Expression.

Google Style
============

A Google style search string is a group of tokens (separated by spaces) with an implied AND between each token. This style search is case insensitive. For example:

.. code-block:: 

  /tag:tag1 tag:tag2 word1 "word2 word3" tag:tag3

Regular Expression
==================

Regular expression searching also supports the use of flags (currently only case-insensitive) by adding a final forward slash followed by the flags. The following example will do a case-insensitive search for ``something``:

.. code-block::

  (regex) /something/i


.. _GitHub: https://github.com/insanum/sncli
