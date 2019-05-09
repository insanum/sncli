Install
#######

Prerequisites
*************

+ A love for the command line
+ `Python 3`_
+ `Pip`_

.. topic:: Dependencies

	The Python modules `Urwid`_, `Requests`_, and `Simperium3`_ will also be installed.

Installation
*************

Pip
===

.. coder-block:: shell

	$ pip install sncli

Arch AUR
==========

Use your favorite `AUR helper`_ to install ``sncli=git``.

Manually
==========

.. code-block:: shell

	$ git clone https://github.com/insanum/sncli.git
	$ cd sncli/
	$ python setup.py install

Using Pipenv
==============

.. code-block:: shell
    
	$ git clone https://github.com/insanum/sncli.git
	$ cd sncli/
	$ pipenv install
	$ pipenv run sncli


.. _Python 3: http://www.python.org
.. _Pip: https://pip.pypa.io/en/stable/
.. _Urwid: http://urwid.org
.. _Requests: http://docs.python=requests.org
.. _Simperium3: https://simperium.com/docs/reference/python/
.. _AUR helper: https://wiki.archlinux.org/index.php/AUR_helpers
