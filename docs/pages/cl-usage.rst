Command Line Usage
##################

.. code-block:: shell

  sncli [OPTIONS] [COMMAND] [COMMAND_ARGS]

Options
********

.. option:: <none>

  Open ``sncli`` in the console GUI.

-----

.. option:: -c <file>
.. option::  --config=<file>

  Sets the :doc:`/pages/configuration` used by ``sncli``. The default is ``$HOME/.snclirc``.

-----

.. option:: -h
.. option:: --help 

  View ``sncli`` options and subcommands.

-----

.. option:: -k <key>
.. option:: --key=<key>

	Idenifies a note by it's key.

-----

.. option:: -n
.. option:: --nosync

  Prevent ``sncli`` from performing a server sync.

-----

.. option:: -r
.. option:: --regex

	This will cause ``sncli`` search strings as a regular expression. See :ref:`search` for more.

-----

.. option:: -t <title>
.. option:: --title=<title>

	If creating a new note from ``stdin``, this will allow you to set the title to <title>.

-----

.. option:: -v
.. option:: --verbose

  Displays the command's verbose output.

Commands
********

Notes
=====

.. option:: create

  Opens a new note in the editor.

.. code-block:: shell

  echo [your note content here] | sncli -t <title> create -

.. note:: Creating a note from ``stdin`` is the only command  that accepts ``-t <title>``.

-----

.. option:: dump

  Dump notes in plain text format to ``stdin``.

.. code-block:: shell

  sncli dump
  sncli -k <key> dump
  sncli dump [search_string]
  sncli -r dump [search_string]

-----

.. option:: edit

  Opens the specific note in the editor..

.. code-block:: shell

  sncli -k <key> edit

-----

.. option:: export

  Export notes in JSON to ``stdin``.

.. code-block:: shell

  sncli -k <key> export
  sncli export [search_string]
  sncli -r export [search_string]

-----

.. option:: import

  Import a JSON formatted note.

  Fields are: content; tags; systemTags; modificationDate; creationDate; deleted

.. code-block:: shell

  echo '{"tags":["testing","new"],"content":"New note!"}' | sncli import -

-----

.. option:: list

  List all notes by ``key [flags] title``.

.. code-block:: shell

  sncli list [search_string]
  sncli list -r [search_string]

-----

.. option:: sync
	
	Performs a full, bi-directional sync between the local notes cache and the Simplenote server.

Flags
=====

.. option:: pin | unpin

  Pin or unpin a specific note.

.. code-block:: shell

  sncli -k <key> pin
  sncli -k <key> unpin

.. option:: markdown | unmarkdown

  Add or remove the markdown as the note's file type.

.. code-block:: shell

  sncli -k <key> markdown
  sncli -k <key> unmarkdown

.. option:: trash | untrash

  Move a note to or from trash. 

.. code-block:: shell

  sncli -k <key> trash
  sncli -k <key> untrash

Tags
====

.. option:: tag <add|get|rm|set>

  Manage your note's tags.

.. code-block:: shell

  sncli -k <key> tag add <tags>

Add tag <text> to a specific note.

.. code-block:: shell

  sncli -k <key> tag get

List the tags of a specific note in ``stdin``.

.. code-block:: shell

  sncli -k <key> tag rm <tags>

Remove tag <tags> from a specific note.

.. code-block:: shell

  sncli -k <key> tag set <tags>

Set <tags> as tags for a specific note.

.. note:: ``tag set`` will overwrite all previous tags for the specific note.
