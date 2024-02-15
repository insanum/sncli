#!/usr/bin/env python3

# Copyright (c) 2014 Eric Davis
# Licensed under the MIT License

from setuptools import setup

deps = ['urwid', 'requests', 'Simperium3']

setup(
      name='sncli',
      description='Simplenote Command Line Interface',
      version='0.4.3',
      author='Eric Davis',
      author_email='edavis@insanum.com',
      url='https://github.com/insanum/sncli',
      license='MIT',
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
