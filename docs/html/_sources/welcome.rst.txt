sncli
#####
Simplenote Command Line Interface

.. image:: screenshot1.png
    :width: 90%
    :align: center


.. note:: This project is on `GitHub`_ and `pull requests`_ are welcome.

Console GUI Features
====================

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
======================

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

TLDR
====

Notes can be viewed/created/edited in both an online and offline mode. All changes are saved to a local cache on disk and automatically sync'ed when sncli is brought online.


.. _pull requests: https://github.com/insanum/sncli/pulls
.. _GitHub: https://github.com/insanum/sncli
