#!/usr/bin/env python3

# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

from setuptools import setup
import simplenote_cli

deps = ['urwid', 'requests', 'Simperium3']

setup(
      name=simplenote_cli.__productname__,
      description=simplenote_cli.__description__,
      version=simplenote_cli.__version__,
      author=simplenote_cli.__author__,
      author_email=simplenote_cli.__author_email__,
      url=simplenote_cli.__url__,
      license=simplenote_cli.__license__,
      requires=deps,
      install_requires=deps,
      packages=['simplenote_cli'],
      entry_points={
          'console_scripts': [
              'sncli = simplenote_cli.sncli:main'
          ]
      },
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console :: Curses',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
      ],
)
