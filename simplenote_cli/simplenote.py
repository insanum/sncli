
# Copyright (c) 2014 Eric Davis
# This file is ~*slightly*~ heavily modified from simplynote.py.
# Updated in 2018 to work with the new Simperium api.

# -*- coding: utf-8 -*-
"""
    simplenote.py
    ~~~~~~~~~~~~~~

    Python library for accessing the Simplenote API

    :copyright: (c) 2011 by Daniel Schauenberg
    :license: MIT, see LICENSE for more details.
"""

import base64
import datetime
import json
import logging
import time
import urllib.parse
import uuid

import requests
from requests.exceptions import ConnectionError, RequestException, HTTPError

from simperium.core import Api, Auth

# Application token provided for sncli.
# Please do not abuse.
APP_TOKEN = '26864ab5d6fd4a37b80343439f107350'

# Simplenote app id on Simperium
SIMPLENOTE_APP_ID = 'chalk-bump-f49'

NOTE_FETCH_LENGTH = 100

class SimplenoteLoginFailed(Exception):
    pass

class Simplenote(object):
    """ Class for interacting with the simplenote web service """

    def __init__(self, username: str, password: str):
        """ object constructor """
        self.auth = Auth(SIMPLENOTE_APP_ID, APP_TOKEN)

        self.api = None

        self.username = username
        self.password = password
        self.token = None
        self.status = 'offline'

        # attempt initial auth
        try:
            self.get_api()
        except ConnectionError as e:
            logging.debug(e)
            self.status = 'offline: no connection'
        except HTTPError as e:
            logging.debug(e)
            self.status = 'offline: login failed; check username and password'
        except Exception as e:
            logging.debug(e)
            self.status = 'offline: unknown auth error; check log for details'

    def authenticate(self, user: str, password: str) -> Api:
        """ Method to get simplenote auth token

        Arguments:
            - user (string):     simplenote email address
            - password (string): simplenote password

        Returns:
            Simplenote API instance

        """

        token = self.auth.authorize(user, password)
        api = Api(SIMPLENOTE_APP_ID, token)
        self.status = "online"
        return api

    def get_api(self) -> Api:
        if self.api is None:
            self.api = self.authenticate(self.username, self.password)
        return self.api

    def get_note(self, noteid, version=None):
        """ method to get a specific note

        Arguments:
            - noteid (string): ID of the note to get
            - version (int): optional version of the note to get

        Returns:
            A tuple `(note, status)`

            - note (dict): note object
            - status (int): 0 on sucesss and -1 otherwise

        """

        try:
            note = self.get_api().note.get(noteid, version=version)
            if version is not None:
                note['version'] = version
            if note is None:
                return None, -1
            note['key'] = noteid
            return note, 0 if note is not None else -1
        except Exception as e:
            logging.debug(e)
            return None, -1


    def update_note(self, note):
        """ function to update a specific note object, if the note object does not
        have a "key" field, a new note is created

        Arguments
            - note (dict): note object to update

        Returns:
            A tuple `(note, status)`

            - note (dict): note object (or error instance if failure)
            - status (int): 0 on sucesss and -1 otherwise

        """
        # Note: all strings in notes stored as type str
        # - use s.encode('utf-8') when bytes type needed

        try:
            # determine whether to create a new note or updated an existing one
            if 'key' not in note:
                # new note; build full note object to send to avoid 400 errors
                note = {
                    'tags': note['tags'],
                    'deleted': note['deleted'],
                    'content': note['content'],
                    'modificationDate': note['modificationDate'],
                    'creationDate': note['creationDate'],
                    'systemTags': [],
                    'shareURL': '',
                    'publishURL': '',
                }
                key, note = self.get_api().note.new(note, include_response=True)
                note['version'] = 1
            else:
                key, note = self.get_api().note.set(note['key'], note, include_response=True)
            note['key'] = key
        except ConnectionError as e:
            self.status = 'offline, connection error'
            return e, -1
        except RequestException as e:
            logging.debug('RESPONSE ERROR: ' + str(e))
            self.status = 'error updating note, check log'
            return e, -1
        except ValueError as e:
            return e, -1
        return note, 0

    def add_note(self, note):
        """wrapper function to add a note

        The function can be passed the note as a dict with the `content`
        property set, which is then directly send to the web service for
        creation. Alternatively, only the body as string can also be passed. In
        this case the parameter is used as `content` for the new note.

        Arguments:
            - note (dict or string): the note to add

        Returns:
            A tuple `(note, status)`

            - note (dict): the newly created note
            - status (int): 0 on sucesss and -1 otherwise

        """
        if type(note) == str:
            return self.update_note({"content": note})
        elif (type(note) == dict) and "content" in note:
            return self.update_note(note)
        else:
            return "No string or valid note.", -1

    def _convert_index_to_note(cls, entry):
        """
        Helper function to convert a note as returned in the api index method
        to how sncli expects it.
        """
        note = entry['d']
        note['key'] = entry['id']
        note['version'] = entry['v']
        return note

    def get_note_list(self, since=None, tags=[]):
        """ function to get the note list

        The function can be passed optional arguments to limit the
        date range of the list returned and/or limit the list to notes
        containing a certain tag. If omitted a list of all notes
        is returned.

        Arguments:
            - since=time.time() epoch stamp: only return notes modified
              since this date
            - tags=[] list of tags as string: return notes that have
              at least one of these tags

        Returns:
            A tuple `(notes, status)`

            - notes (list): A list of note objects with all properties set.
            - status (int): 0 on sucesss and -1 otherwise

        """
        # initialize data
        status = 0
        note_list = []
        mark = None

        while True:

            try:
                data = self.get_api().note.index(data=True, mark=mark, limit=NOTE_FETCH_LENGTH)

                note_list.extend(map(self._convert_index_to_note, data['index']))

                if 'mark' not in data:
                    break
                mark = data['mark']

            except ConnectionError as e:
                self.status = 'offline, connection error'
                status = -1
                break
            except RequestException as e:
                # if problem with network request/response
                status = -1
                break
            except ValueError as e:
                # if invalid json data
                status = -1
                break

        # Can only filter for tags at end, once all notes have been retrieved.
        #Below based on simplenote.vim, except we return deleted notes as well
        if (len(tags) > 0):
            note_list = [n for n in note_list if (len(set(n["tags"]).intersection(tags)) > 0)]

        if since is not None:
            note_list = [n for n in note_list if n['modificationDate'] > since]

        return note_list, status

    def trash_note(self, note_id):
        """ method to move a note to the trash

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(note, status)`

            - note (dict): the newly created note or an error message
            - status (int): 0 on sucesss and -1 otherwise

        """
        # get note
        note, status = self.get_note(note_id)
        if (status == -1):
            return note, status
        # set deleted property
        note["deleted"] = True
        # update note
        return self.update_note(note)

    def delete_note(self, note_id):
        """ method to permanently delete a note

        Arguments:
            - note_id (string): key of the note to trash

        Returns:
            A tuple `(note, status)`

            - note (dict): an empty dict or an error message
            - status (int): 0 on sucesss and -1 otherwise

        """
        # notes have to be trashed before deletion
        note, status = self.trash_note(note_id)
        if (status == -1):
            return note, status

        try:
            self.get_api().note.delete(note_id)
        except ConnectionError as e:
            self.status = 'offline, connection error'
            return e, -1
        except RequestException as e:
            return e, -1
        return {}, 0
