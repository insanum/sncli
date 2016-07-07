
# Copyright (c) 2014 Eric Davis
# This file is *slightly* modified from simplynote.py.

# -*- coding: utf-8 -*-
"""
    simplenote.py
    ~~~~~~~~~~~~~~

    Python library for accessing the Simplenote API

    :copyright: (c) 2011 by Daniel Schauenberg
    :license: MIT, see LICENSE for more details.
"""

import urllib.parse
from requests.exceptions import RequestException
import base64
import time
import datetime
import logging
import requests

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson as json

NOTE_FETCH_LENGTH = 100

class SimplenoteLoginFailed(Exception):
    pass

class Simplenote(object):
    """ Class for interacting with the simplenote web service """

    def __init__(self, username, password, host):
        """ object constructor """
        self.username = urllib.parse.quote(username)
        self.password = urllib.parse.quote(password)
        self.AUTH_URL = 'https://{0}/api/login'.format(host)
        self.DATA_URL = 'https://{0}/api2/data'.format(host)
        self.INDX_URL = 'https://{0}/api2/index?'.format(host)
        self.token = None

    def authenticate(self, user, password):
        """ Method to get simplenote auth token

        Arguments:
            - user (string):     simplenote email address
            - password (string): simplenote password

        Returns:
            Simplenote API token as string

        """
        auth_params = "email=%s&password=%s" % (user, password)
        values = base64.encodestring(auth_params.encode())
        try:
            res = requests.post(self.AUTH_URL, data=values)
            token = res.text
            if res.status_code != 200:
                raise SimplenoteLoginFailed(
                        'Login to Simplenote API failed! statuscode: {}'.format(res.status_code))
        except requests.exceptions.ConnectionError: # no connection exception
            token = None
        except RequestException as e:
            raise SimplenoteLoginFailed('Login to Simplenote API failed!')

        return token

    def get_token(self):
        """ Method to retrieve an auth token.

        The cached global token is looked up and returned if it exists. If it
        is `None` a new one is requested and returned.

        Returns:
            Simplenote API token as string

        """
        if self.token == None:
            self.token = self.authenticate(self.username, self.password)
        return self.token


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
        # request note
        params_version = ""
        if version is not None:
            params_version = '/' + str(version)
         
        params = {'auth': self.get_token(),
                  'email': self.username }
        url = '{}/{}{}'.format(self.DATA_URL, str(noteid), params_version)
        #logging.debug('REQUEST: ' + self.DATA_URL+params)
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()
            note = res.json()
        except RequestException as e:
            # logging.debug('RESPONSE ERROR: ' + str(e))
            return e, -1
        except ValueError as e:
            return e, -1

        # # use UTF-8 encoding
        # note["content"] = note["content"].encode('utf-8')
        # # For early versions of notes, tags not always available
        # if "tags" in note:
        #     note["tags"] = [t.encode('utf-8') for t in note["tags"]]
        #logging.debug('RESPONSE OK: ' + str(note))
        return note, 0

    def update_note(self, note):
        """ function to update a specific note object, if the note object does not
        have a "key" field, a new note is created

        Arguments
            - note (dict): note object to update

        Returns:
            A tuple `(note, status)`

            - note (dict): note object
            - status (int): 0 on sucesss and -1 otherwise

        """
        # Note: all strings in notes stored as type str
        # - use s.encode('utf-8') when bytes type needed

        # determine whether to create a new note or updated an existing one
        params = {'auth': self.get_token(),
                  'email': self.username}
        if "key" in note:
            # set modification timestamp if not set by client
            if 'modifydate' not in note:
                note["modifydate"] = time.time()

            url = '%s/%s' % (self.DATA_URL, note["key"])
        else:
            url = self.DATA_URL

        #logging.debug('REQUEST: ' + url + ' - ' + str(note))
        try:
            res = requests.post(url, data=json.dumps(note), params=params)
            res.raise_for_status()
            note = res.json()
        except RequestException as e:
            # logging.debug('RESPONSE ERROR: ' + str(e))
            return e, -1
        except ValueError as e:
            return e, -1
        #logging.debug('RESPONSE OK: ' + str(note))
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

            - notes (list): A list of note objects with all properties set except
            `content`.
            - status (int): 0 on sucesss and -1 otherwise

        """
        # initialize data
        status = 0
        notes = { "data" : [] }
        json_data = {}

        # get the note index
        params = {'auth': self.get_token(),
                  'email': self.username,
                  'length': NOTE_FETCH_LENGTH
                  }
        if since is not None:
            params['since'] = since

        # perform initial HTTP request
        try:
            #logging.debug('REQUEST: ' + self.INDX_URL+params)
            res = requests.get(self.INDX_URL, params=params)
            res.raise_for_status()
            #logging.debug('RESPONSE OK: ' + str(res))
            json_data = res.json()
            notes["data"].extend(json_data["data"])
        except RequestException as e:
            # if problem with network request/response
            status = -1
        except ValueError as e:
            # if invalid json data
            status = -1

        # get additional notes if bookmark was set in response
        while "mark" in json_data:
            params = {'auth': self.get_token(),
                      'email': self.username,
                      'mark': json_data['mark'],
                      'length': NOTE_FETCH_LENGTH
                      }
            if since is not None:
                params['since'] = since

            # perform the actual HTTP request
            try:
                #logging.debug('REQUEST: ' + self.INDX_URL+params)
                res = requests.get(self.INDX_URL, params=params)
                res.raise_for_status()
                json_data = res.json()
                #logging.debug('RESPONSE OK: ' + str(res))
                notes["data"].extend(json_data["data"])
            except RequestException as e:
                # if problem with network request/response
                status = -1
            except ValueError as e:
                # if invalid json data
                status = -1

        # parse data fields in response
        note_list = notes["data"]

        # Can only filter for tags at end, once all notes have been retrieved.
        #Below based on simplenote.vim, except we return deleted notes as well
        if (len(tags) > 0):
            note_list = [n for n in note_list if (len(set(n["tags"]).intersection(tags)) > 0)]

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
        note["deleted"] = 1
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

        params = {'auth': self.get_token(),
                  'email': self.username }
        url = '{}/{}'.format(self.DATA_URL, str(note_id))

        try:
            #logging.debug('REQUEST DELETE: ' + self.DATA_URL+params)
            res = requests.delete(url, params=params)
            res.raise_for_status()
        except RequestException as e:
            return e, -1
        return {}, 0

