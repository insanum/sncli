Configuration
#############

The current Simplenote API does not support ``oauth`` authentication so your Simplenote account information must live in the configuration file. Please be sure to protect this file.

The flow sncli uses for finding the config file is:

#. Specified with the command line options ``-c`` or ``config``.
#.  If the environment variable ``SNCLIRC`` is set, it will use that.
#. Lastly, it will pull from the default location of ``$HOME/.snclirc``.


The following (using your account information) is enough to start using sncli.

.. code-block::

  ~/.snclirc
  -------------------
  [sncli]
  cfg_sn_username = lebowski@thedude.com
  cfg_sn_password = nihilist

Everything else that goes into your ``snclirc`` is optional. 

General
*******

Keyboard
********

.. note:: The default keybinds can be found on the :doc:`gui-usage` page.




.. hint:: You can also find `examples`_ of acceptable key combinations on the Urwid website.


Colors
******

.. note:: The list of available colors was pulled from the Urwid `documentation`_ and you can see what they *might* look like `here`_.

Available Text Colors
=====================

.. hlist
  columns 3

  + default
  + black
  + dark red
  + dark green
  + brown
  + dark blue
  + dark magenta
  + dark cyan
  + light gray
  + dark gray
  + light red
  + light green
  + yellow
  + light blue
  + light magenta
  + light cyan
  + white

Available Background Colors
===========================

.. hlist
  columns 3

  + default
  + black
  + dark red
  + dark green
  + brown
  + dark blue
  + dark magenta
  + dark cyan
  + light gray

.. hint  ``fg`` stands for ``foreground`` and sets the text color.

  ``bg`` stands for ``background`` and sets the background color.

  ``default`` colors are set by your teminal.

Available Settings
==================

.. code-block::

  clr_default_fg = default
  clr_default_bg = default

Sets the default colors.

-----

.. code-block::

  clr_status_bar_fg = dark gray
  clr_status_bar_bg = light gray

Sets the status bar colors.

-----

.. code-block:: 

  clr_log_fg = dark gray
  clr_log_bg = light gray

Sets the colors for the sync log.

-----

.. code-block::

  clr_user_input_bar_fg = white
  clr_user_input_bar_bg = light red

Sets the prompt bar colors.

-----

.. code-block::

  clr_note_focus_fg = white
  clr_note_focus_bg = light red
  
Sets the colors for the focused (or selected) note.

-----

.. code-block::

  clr_note_title_day_fg = light red
  clr_note_title_day_bg = default
 
Sets the title colors of notes that have been updated in the last 24 hours. 
  
-----

.. code-block::

  clr_note_title_week_fg = light green
  clr_note_title_week_bg = default
 
Sets the title colors of notes that have been updated in the last week. 

-----

.. code-block::

  clr_note_title_month_fg = brown
  clr_note_title_month_bg = default
 
Sets the title colors of notes that have been updated in the last month.

-----

.. code-block::

  clr_note_title_year_fg = light blue
  clr_note_title_year_bg = default
 
Sets the title colors of notes that have not been updated in a year. 

-----

.. code-block::

  clr_note_title_ancient_fg = light blue
  clr_note_title_ancient_bg = default
 
Sets the title colors of notes that were last updated in over an year. 

-----

clr_note_date_fg = dark blue
clr_note_date_bg = default

-----

clr_note_flags_fg = dark magenta
clr_note_flags_bg = default

-----

clr_note_tags_fg = dark red
clr_note_tags_bg = default

-----

clr_note_content_fg = default
clr_note_content_bg = default

-----

clr_note_content_focus_fg = white
clr_note_content_focus_bg = light red

-----

clr_note_content_old_fg = yellow
clr_note_content_old_bg = dark gray

-----

clr_note_content_old_focus_fg = white
clr_note_content_old_focus_bg = light red

-----

clr_help_focus_fg = white
clr_help_focus_bg = light red

-----

clr_help_header_fg = dark blue
clr_help_header_bg = default

-----

clr_help_config_fg = dark green
clr_help_config_bg = default

-----

clr_help_value_fg = dark red
clr_help_value_bg = default

-----

clr_help_descr_fg = default
clr_help_descr_bg = default

-----

Example Configuration
*********************

.. code-block::

  ~/.snclirc
  --------------------
  [sncli]
  cfg_sn_username = lebowski@thedude.com
  cfg_sn_password = nihilist
  
  # as an alternate to cfg_sn_password you could use the following config item
  # any shell command can be used; its stdout is used for the password
  # trailing newlines are stripped for ease of use
  # note: if both password config are given, cfg_sn_password will be used
  cfg_sn_password_eval = gpg --quiet --for-your-eyes-only --no-tty --decrypt ~/.sncli-pass.gpg
  
  # see http://urwid.org/manual/userinput.html for examples of more key combinations
  kb_edit_note = space
  kb_page_down = ctrl f
  
  # note that values must not be quoted
  clr_note_focus_bg = light blue
  
  # if this editor config value is not provided, the $EDITOR env var will be used instead
  # warning: if neither $EDITOR or cfg_editor is set, it will be impossible to edit notes
  cfg_editor = nvim
  
  # alternatively, {fname} and/or {line} are substituted with the filename and
  # current line number in sncli's pager.
  # If {fname} isn't supplied, the filename is simply appended.
  # examples:
  cfg_editor = nvim {fname} +{line}
  cfg_editor = nano +{line}
  
  # this is also supported for the pager:
  cfg_pager = less -c +{line} -N {fname}

-----

.. _documentation: http//urwid.org/reference/constants.html
.. _here: http//urwid.org/manual/displayattributes.html#high-colors
 
.. _examples: http://urwid.org/manual/userinput.html
