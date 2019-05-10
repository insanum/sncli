Tips and Tricks
###############

Markdown Pager
**************

Set ``mdv`` as your pager for ``sncli`` and get a formatted view of your markdown files [Suggested by `s5unty`_]:

+ Install `mdv`_
+ Create a pager/wrapper

	.. code-block:: shell
        
		/usr/local/bin/mdless
		---------------------
		#!/bin/zsh
		# https://superuser.com/questions/1059781/what-exactly-is-in-bash-and-in-zsh
		/usr/bin/less -R -c =(mdv "$1")

+ Make the reader an executable file

	.. code-block:: shell

		sudo chmod +x /usr/local/bin/mdless
        
+ Now set ``mdless`` as your pager

	.. code-block:: shell
        
		$HOME/.snclirc
		------------------------
		cfg_pager = /usr/local/bin/mdless

Note: MDV does not yet support using a light backdround

Vim, Auto-set filetype
**********************

Modeline
========

Add a modeline to each note, for `VimOutliner`_ you would add [Suggested by `insanum`_]:

.. code-block:: vim

	; vim:ft=votl

This will change the file type for the note it's been added to.

AutoCommand
===========

You could also add an AutoCommand to your ``vimrc``: 

.. code-block:: vim

	augroup sncli_ft
	au BufEnter,BufWrite,BufRead,BufNewFile /tmp/*.txt set filetype=asciidoc
	augroup END

This will set text files opened in sncli's default temp directory to the filetype of Asciidoc. 

Open Links
**********

Find and open links faster with ``urlscan`` or ``urlview``.

+ Install `urlscan`_ or `urlview`_
+ Pip the note from the note view
+ Select a link!

.. _s5unty: https://github.com/s5unty
.. _insanum: https://github.com/insanum

.. _mdv: https://github.com/axiros/terminal_markdown_viewer
.. _VimOutliner: https://github.com/insanum/votl
.. _urlscan: https://github.com/firecat53/urlscan
.. _urlview: https://github.com/sigpipe/urlview
