Console GUI Usage
#################

Common
******

.. object:: h
  
  View the help menu

.. object:: q

  Exit the current view or the program.

.. object:: S

  Perform a bi-directional ync local notes to Simplenote server.

.. object:: j

  Scroll down one line.

.. object:: k

  Scroll up one line.

.. object:: space

  Page down.

.. object:: b

  Page up.

.. object:: ctrl+d

  Scroll half a page down.

.. object:: ctrl+u

  Scroll half a page up.

.. object:: G

  Jump to the bottom of the page.

.. object:: g

  Jump to the top of the page.

.. object:: s

  Toggle the Status bar.

.. object:: e

  Edit highlighted note.

.. object:: enter

  Open highlighted note in sncli pager.

.. object:: meta+enter

  Open highlighted note in an external pager (set by ``cfg_pager`` or ``$PAGER``).

.. object:: O

  View the selected note's JSON in the pager.

.. object:: |

  Open the prompt to pip the note to another program.

.. object:: l

	View the sync log.

.. object:: T

  Open the dialog box for trashing the selected note.

.. object:: p

  Toggle the selected note's pin status.

.. object:: m

  Toggle the selected note's markdown status.

.. object:: t

  Open a prompt with the selected note's tags.

.. object:: /

  Open the Google style search prompt.

.. object:: meta+/

  Open the Regular Expression style search prompt.

.. object:: ?

  Open the Google style.search prompt, but with reverse search direction.

.. object:: meta+?

  Open the Regular Expression style prompt, but with reverse search direction.

Search Views
============

.. object:: n

  View next search result.

.. object:: N

  View previous search result.

.. object:: A

  Clear the search.


Notes List Only
***************

.. object:: C

  Create a new note.

.. object:: d

  Sort notes by date.

.. object:: a

  Sort notes in alphabetical order.

.. object:: ctrl+t

  Sort notes by tags.

Pager View Only
***************

.. object:: J

	View the next note.

.. object:: K

	View the previous note.

.. object:: 2

	Change the notes tab stop to 2.

.. object:: 4

	Change the notes tab stop to 4.

.. object:: 8

  Change the notes tab stop to 8.

.. object:: y

  Copy the note's higtlighted line of text to the system clipboard.

.. note:: This will only work on systems where X11 or macOS is present; it checks for ``xsel`` and  ``pbcoby`` commands.

.. object:: <

	View an old version of the note (this cycles).

.. object:: >

	View a newer version of the note (this cycles).

History View
============

.. object:: D

  Show the output of ``diff`` between the current note and the selected older version of the note.

.. object:: R

  Restore the older version of the note.

.. object:: L

  Jump to the lastest version of the note.

.. object:: #

  Open the prompt and enter a version of the note to be displayed.
