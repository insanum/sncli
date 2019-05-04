Tips and Tricks
###############

Markdown Pager
==============

Set ``mdv`` as your pager for ``sncli`` and get a formatted view of your markdown files.  [1]_

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

        $ sudo chmod +x /usr/local/bin/mdless
        
+ Now set ``mdless`` as your pager

        .. code-block:: shell
        
                $HOME/.snclirc
                ------------------------
                cfg_pager = /usr/local/bin/mdless

.. note: MDV does not yet support using a light backdround

Vim, Auto-set filetype
======================

Modeline
--------

Add a modeline to each note, for `VimOutliner`_ you would add:  [2]_

.. code-block:: vim

        ; vim:ft=votl

Just replace ``votl`` with your preferred filetype.

AutoCommand
-----------

You could also add an AutoCommand to your ``vimrc``:  [3]_

.. code-block:: vim

        augroup sncli_ft
        au BufEnter,BufWrite,BufRead,BufNewFile /tmp/*.txt set filetype=asciidoc
        augroup END

This will set any file opened in sncli's directory (set to default in this example) to the filetype of Asciidoc. 

Open Links
==========

+ Install `urlscan`_ or `urlview`_
+ Pip the note

.. code-block:: shell

        $HOME/.snclirc
        ------------------
        cfg_pager = mdless | urlview

+ Select a link!

-----

.. rubric:: Footnotes

.. [1] Suggested by `s5unty`_
.. [2] Suggested by `insanum`_
.. [3] Suggested by `1094`_


.. _s5unty: https://github.com/s5unty
.. _insanum: https://github.com/insanum
.. _1094: https://github.com/1094

.. _mdv: https://github.com/axiros/terminal_markdown_viewer
.. _VimOutliner: https://github.com/insanum/votl
.. _urlscan: https://github.com/firecat53/urlscan
.. _urlview: https://github.com/sigpipe/urlview
