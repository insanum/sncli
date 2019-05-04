Command Line Usage
##################

.. code-block:: shell

  sncli [OPTIONS] [COMMAND] [COMMAND_ARGS]

Options
========

.. option:: <none>

  Open ``sncli`` in the console GUI.

.. option:: -c <file>, --config=<file>

  Sets the :doc:`/pages/configuration` used by ``sncli``. The default is ``$HOME/.snclirc``.

.. option:: -h, --help 

  View ``sncli`` options and subcommands.

.. option:: -k <key>, --key=<key>

	Idenifies a note by it's key.

.. option:: -n, --nosync

  Prevent ``sncli`` from performing a server sync.

.. option:: -r, --regex

	This will cause ``sncli`` to treat search strings (listed below as ``[term]``) as a regular expression.

.. option:: -t <title>, --title=<title>

	If creating a new note from ``stdin``, this will allow you to set the title to <title>.
	
.. option:: -v, --verbose

  Displays the commands verbose output.

Commands
========

Create
------

.. option:: sncli create

	Opens a new note in your ``cfg_editor``.

.. option:: echo 'your note content here' | sncli create -

	This will create and save a note with ``your note content here``. You can use the option ``-t <title>`` to add an title to the created note.

Dump
----

.. option:: sncli dump

	Dump notes in plain text format to ``stdin``.

Options to dump a specific note: ``-k <key>``

Edit
----

.. option:: sncli -k <key> edit

	Opens the requested note in your ``cfg_editor``.

Export
------

.. option:: sncli export

	Export all notes in JSON to ``stdin``.

Options to export specific notes: ``-r [term]; [term]; -k <key>``

Flags
-----

.. option:: sncli -k <key> {flag}

  This will add or remove a flag from the requested note.

Flags that can be added or removed: ``pin; unpin; markdown; unmarkdown; trash; untrash``

Import
------

.. option:: echo '{"tags":["testing","new"],"content":"New note!"}' | sncli import -

  Import a JSON formatted note.

JSON fields: ``content; tags; systemTags; modificationDate; creationDate; deleted``

List
----

.. option:: sncli list

	List all notes by ``key [flags] title``.
	
Options for listing specific notes: ``-r [term]; [term]``

Sync
----

.. option:: sncli sync
	
	Performs a full, bi-directional sync between the local notes cache and the Simplenote server.

Tags
----

.. option:: sncli -k <key> tab add <text>

  Add tag <text> to a specific note.

.. option:: sncli -k <key> tab get

  List the tags of a specific note in ``stdin``.

.. option:: sncli -k <key> tab rm <text>

  Remove tag <text> from a specific note.

.. option:: sncli -k <key> tab set <text>

  Set <text> as tags for a specific note.
