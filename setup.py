#!/usr/bin/env python2

# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

from distutils.core import setup
import simplenote_cli

setup(
      name=simplenote_cli.__productname__,
      description=simplenote_cli.__description__,
      version=simplenote_cli.__version__,
      author=simplenote_cli.__author__,
      author_email=simplenote_cli.__author_email__,
      url=simplenote_cli.__url__,
      requires=[ 'urwid', 'pyperclip' ],
      packages=[ 'simplenote_cli' ],
      scripts=[ 'sncli' ]
     )

