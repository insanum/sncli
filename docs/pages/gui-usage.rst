Console GUI Usage
#################

Common
******

:h:
  
  View the ``help`` menu

:q:

  Quit ``sncli``

:S:

  Perform a bi-directional ync local notes to Simplenote server.

:j:

  Scroll down one line.

:k:

  Scroll up one line.

:space:

  Page down.

:b:

  Page up.

:ctrl+d:

  Scroll half a page down.

:ctrl+u:

  Scroll half a page up.

:G:

  Jump to the bottom of the page.

:g:

  Jump to the top of the page.

:s:

  Toggle the Status bar.

:e:

  Edit highlighted note.

:enter:

  Open highlighted note in sncli pager.

:meta+enter:

  Open highlighted note in an external pager (set by ``cfg_pager`` or ``$PAGER``).

:O:

  View the selected note's JSON in the pager.

.. object:: |

  Open the prompt to pip the note to another program.

:l:

	View the sync log.

:T:

  Open the dialog box for trashing the selected note.

:p:

  Toggle the selected note's pin status.

:m:

  Toggle the selected note's markdown status.

:t:

  Open a prompt with the selected note's tags.

:/:

  Open the Google style search prompt.

:meta+/:

  Open the Regular Expression style search prompt.

:?:

  Open the Google style.search prompt, but with reverse search direction.

:meta+?:

  Open the Regular Expression style prompt, but with reverse search direction.

Search Views
============

:n:

  View next search result.

:N:

  View previous search result.

:A:

  Clear the search.


Notes List Only
***************

:C:

  Create a new note.

:d:

  Sort notes by date.

:a:

  Sort notes in alphabetical order.

:ctrl+t:

  Sort notes by tags.

Pager View Only
***************

:J:

	View the next note.

:K:

	View the previous note.

:2:

	Change the notes tab stop to 2.

:4:

	Change the notes tab stop to 4.

:8:

  Change the notes tab stop to 8.

:y:

  Copy the note's higtlighted line of text to the system clipboard.

.. note:: This will only work on systems where X11 or macOS is present; it checks for ``xsel`` and  ``pbcoby`` commands.

:<:

	View an old version of the note (this cycles).

:>:

	View a newer version of the note (this cycles).

History View
============

:D:

  Show the output of ``diff`` between the current note and the selected older version of the note.

:R:

  Restore the older version of the note.

:L:

  Jump to the lastest version of the note.

:#:

  Enter a number and jump to that version of the note.
