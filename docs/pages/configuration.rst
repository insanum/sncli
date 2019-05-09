Example Configuration
#####################

.. caution:: Values must not be quoted!

::

  [sncli]
  cfg_sn_username = lebowski@thedude.com
  # cfg_sn_password = nihilist
  cfg_sn_password_eval = gpg --quiet --for-your-eyes-only --no-tty --decrypt ~/.sncli-pass.gpg
  
  ## NOTE: if both password config are given, cfg_sn_password will be used
  
  # sets the datebase path for your notes
  cfg_db_path = os.path.join(self.home. .sncli)
  
  # allows you to do regex searches with tags
  cfg_search_tags = yes
  
  # sets the default notes sort
  # can be set to `alpha` or `date`
  cfg_sort_mode = date
  
  # keep pins messages at top
  cfg_pinned_ontop = yes
  
  # sets the default tapstop
  cfg_tabstop = 4

  # show the status bar
  cfg_status_bar = yes

  ### DATE
  ## run `man strftime` for all options
  # cfg_format_strftime = %Y/%m/%d
  cfg_format_stftime = %d %B %Y   

  ### TITLES
  ## %D - date
  ## %N - title
  ## %T - tags
  ## %F - flags (fixed to 5 char width)
    # X - not synced
    # T - trashed
    # S - published/shared
    # m - markdown
  ## The dash changes text alignment to the left
  cfg_format_note_title = [%D] %F %-N %T 

  ### EDITOR and PAGER
  # sncli will check your configuration file for the $EDITOR,
  # if this varaible is blank it will check for your OS's $EDITOR
  ## WARNING: if neither $EDITOR or cfg_editor is set, it will be impossible to edit notes
  # `{fname}` is substituted with the filename
  # `{line}` is substituted for the current line number in sncli's pager
  
  # The default editor and pager
  # cfg_editor = os.environ[EDITOR] if EDITOR in os.environ else vim {fname} +{line}
  # cfg_pager = os.environ[PAGER] if PAGER in os.environ else less -c 
  ## If {fname} isn't supplied, the filename is simply appended

  # EXAMPLES
  # cfg_editor = nvim {fname} +{line}
  # cfg_editor = nano +{line}
  cfg_editor = vim +{line}

  # set the pager
  cfg_pager = less -c +{line} -N {fname}
  
  # set the diff pager
  # cfg_diff = diff -b -U10
  cfg_diff = colordiff -bl

  ### THE LOG
  # set the max number of logs sncli saves
  cfg_max_logs = 5
  
  # set the log timeout
  cfg_log_timeout = 5

  # does the log work in reverse
  cfg_log_reversed = yes

  ### TEMP DIR
  # set sncli's temp directory
  # this will default to your OS's temp folder
  cfg_tempdir = ~/.sncli/temp/

  ### KEYBINDING
  ## see http://urwid.org/manual/userinput.html for examples of more key combinations

  ## NOTES LIST KEYBINDS
  # sort notes by date
  kb_sort_date = d

  # sort notes alphabetically
  kb_sort_alpha = a

  # sort notes by tags
  kb_sort_tags = ctrl t

  ## COMMON KEYBINDINS
  # open help menu
  kb_help = h

  # quit the current view or exit the program
  kb_quit = q

  # sync notes
  kb_sync = S

  # scroll down one note 
  kb_down = j
  
  # scroll up one note
  kb_up = k

  # scroll down a page
  kb_page_down = space

  # scroll up a page
  kb_page_up = b

  # scroll down half a page
  kb_half_page_down = ctrl d

  # scroll up half a page
  kb_half_page_up = ctrl u

  # jump to the bottom of the page/list
  kb_bottom = G

  # jump to the top of the page/list
  kb_top = g

  # toggle the status bar
  kb_status = s

  # create a new note
  kb_create_note = C

  # edit a note 
  kb_edit_note = e

  # view note in the pager
  kb_view_note = enter

  # view note in `cfg_pager`
  kb_view_note_ext = meta enter

  # view note in JSON format
  kb_view_note_json = O

  # open the pipe prompt
  kb_pipe_note = |

  # view the snyc log
  kb_view_log = l

  # open trash dialog
  kb_note_trash = T

  # pin or unpin a note
  kb_note_pin = p

  # set or unset a note's filetype to markdown
  kb_note_markdown = m

  # open the tag prmopt
  kb_note_tags = t

  # open Google search style prompt
  kb_search_gstyle = /

  # open regex search style promp
  kb_search_regex  = meta /

  # open Google reverse style prompt
  kb_search_prev_gstyle = ?

  # open regex reverse style prompt
  kb_search_prev_regex = meta ?

  ## SEARCH KEYBINDS
  # jump to next search result
  kb_search_next = n

  # jump to previous search result
  kb_search_prev = N

  # clear search results
  kb_clear_search = A

  ## PAGER KEYBINDS
  # view the next note
  kb_view_next_note = J

  # view the previous note
  kb_view_prev_note = K

  # change tab stop to 2
  kb_tabstop2 = 2

  # change tab stop to 4
  kb_tabstop4 = 4

  # change tab stop to 8
  kb_tabstop8 = 8

  # view an older version of the note
  kb_prev_version = <

  # view a newer version of the note
  kb_next_version = >

  # view difference between currently selected note and the most recent one
  kb_diff_version = D

  # restore an version of the note
  kb_restore_version = R

  # jump to the most recent version of the note
  kb_latest_version = L

  # open the verison selection prompt
  kb_select_version = #

  # copy the highlighted line of text
  kb_copy_note_text = y

  ### COLORS
  ## see http//urwid.org/reference/constants.html for accepted colors
  # `fg` means foreground, the text color
  # `bg` means background color

  ## COMMON 
  # the status bar
  clr_status_bar_fg = dark gray
  clr_status_bar_bg = light gray

  # the prompt bar
  clr_user_input_bar_fg = white
  clr_user_input_bar_bg = light red

  ## NOTES LIST
  # the default colors
  clr_default_fg = default
  clr_default_bg = default

  # the selected note,
  clr_note_focus_fg = white
  clr_note_focus_bg = light red
  
  # titles of notes that have been updated in the last 24 hours
  clr_note_title_day_fg = light red
  clr_note_title_day_bg = default

  # titles of notes that have been updated in the last week
  clr_note_title_week_fg = light green
  clr_note_title_week_bg = default

  # titles of notes that have been updated in the last month
  clr_note_title_month_fg = brown
  clr_note_title_month_bg = default

  # titles of notes that have note been updated in a year
  clr_note_title_year_fg = light blue
  clr_note_title_year_bg = default
 
  # titles of notes that were last updated over a year ago
  clr_note_title_ancient_fg = light blue
  clr_note_title_ancient_bg = default
 
  # for the date
  clr_note_date_fg = dark blue
  clr_note_date_bg = default

  # for the flags (markdown, pinned, shared)
  clr_note_flags_fg = dark magenta
  clr_note_flags_bg = default

  # tags in list view
  clr_note_tags_fg = dark red
  clr_note_tags_bg = default

  ## PAGER
  # note's content
  clr_note_content_fg = default
  clr_note_content_bg = default

  # the selected line of text
  clr_note_content_focus_fg = white
  clr_note_content_focus_bg = light red

  ## HISTORY PAGER
  # note content in history view
  clr_note_content_old_fg = yellow
  clr_note_content_old_bg = dark gray

  # selected line of text in history view
  clr_note_content_old_focus_fg = white
  clr_note_content_old_focus_bg = light red

  ## SYNC LOG
  # the content of the sync log
  clr_log_fg = dark gray
  clr_log_bg = light gray

  ## HELP PAGE
  # current line of text in help view
  clr_help_focus_fg = white
  clr_help_focus_bg = light red

  # the help view's header
  clr_help_header_fg = dark blue
  clr_help_header_bg = default

  # the help view topics
  clr_help_config_fg = dark green
  clr_help_config_bg = default

  # the help topics' values
  clr_help_value_fg = dark red
  clr_help_value_bg = default

  # the descriptions of the help topics
  clr_help_descr_fg = default
  clr_help_descr_bg = default

  ### NOTE: You do not need to keep default vaules in your config
  # they are listed here as examples to give a complete view of 
  # what setting are customizable.
