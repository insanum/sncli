# -*- coding: utf-8 -*-
"""
    simplenote.py
    ~~~~~~~~~~~~~~

    Python library for accessing the Simplenote API

    :copyright: (c) 2011 by Daniel Schauenberg
    :license: MIT, see LICENSE for more details.
"""

import urllib
import urllib2
from urllib2 import HTTPError
import base64
import time
import datetime

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson as json

AUTH_URL = 'https://simple-note.appspot.com/api/login'
DATA_URL = 'https://simple-note.appspot.com/api2/data'
INDX_URL = 'https://simple-note.appspot.com/api2/index?'
NOTE_FETCH_LENGTH = 100

class SimplenoteLoginFailed(Exception):
    pass


class Simplenote(object):
    """ Class for interacting with the simplenote web service """

    def __init__(self, username, password):
        """ object constructor """
        self.username = urllib2.quote(username)
        self.password = urllib2.quote(password)
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
        values = base64.encodestring(auth_params)
        request = Request(AUTH_URL, values)
        try:
            res = urllib2.urlopen(request).read()
            token = urllib2.quote(res)
        except HTTPError:
            raise SimplenoteLoginFailed('Login to Simplenote API failed!')
        except IOError: # no connection exception
            token = None
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
         
        params = '/%s%s?auth=%s&email=%s' % (str(noteid), params_version, self.get_token(), self.username)
        request = Request(DATA_URL+params)
        try:
            response = urllib2.urlopen(request)
        except HTTPError, e:
            return e, -1
        except IOError, e:
            return e, -1
        note = json.loads(response.read())
        # use UTF-8 encoding
        note["content"] = note["content"].encode('utf-8')
        # For early versions of notes, tags not always available
        if note.has_key("tags"):
            note["tags"] = [t.encode('utf-8') for t in note["tags"]]
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
        # use UTF-8 encoding
        note["content"] = unicode(note["content"], 'utf-8')
        if "tags" in note:
            note["tags"] = [unicode(t, 'utf-8') for t in note["tags"]]

        # determine whether to create a new note or updated an existing one
        if "key" in note:
            # set modification timestamp if not set by client
            if 'modifydate' not in note:
                note["modifydate"] = time.time()

            url = '%s/%s?auth=%s&email=%s' % (DATA_URL, note["key"],
                                              self.get_token(), self.username)
        else:
            url = '%s?auth=%s&email=%s' % (DATA_URL, self.get_token(), self.username)
        request = Request(url, urllib.quote(json.dumps(note)))
        response = ""
        try:
            response = urllib2.urlopen(request)
        except IOError, e:
            return e, -1
        note = json.loads(response.read())
        if note.has_key("content"):
            # use UTF-8 encoding
            note["content"] = note["content"].encode('utf-8')
        if note.has_key("tags"):
            note["tags"] = [t.encode('utf-8') for t in note["tags"]]
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
            - since=YYYY-MM-DD string: only return notes modified
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
        ret = []
        response = {}
        notes = { "data" : [] }

        # get the note index
        params = 'auth=%s&email=%s&length=%s' % (self.get_token(), self.username,
                                                 NOTE_FETCH_LENGTH)
        if since is not None:
            try:
                sinceUT = time.mktime(datetime.datetime.strptime(since, "%Y-%m-%d").timetuple())
                params += '&since=%s' % sinceUT
            except ValueError:
                pass

        # perform initial HTTP request
        try:
            request = Request(INDX_URL+params)
            response = json.loads(urllib2.urlopen(request).read())
            notes["data"].extend(response["data"])
        except IOError:
            status = -1

        # get additional notes if bookmark was set in response
        while "mark" in response:
            vals = (self.get_token(), self.username, response["mark"], NOTE_FETCH_LENGTH)
            params = 'auth=%s&email=%s&mark=%s&length=%s' % vals
            if since is not None:
                try:
                    sinceUT = time.mktime(datetime.datetime.strptime(since, "%Y-%m-%d").timetuple())
                    params += '&since=%s' % sinceUT
                except ValueError:
                    pass

            # perform the actual HTTP request
            try:
                request = Request(INDX_URL+params)
                response = json.loads(urllib2.urlopen(request).read())
                notes["data"].extend(response["data"])
            except IOError:
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

        params = '/%s?auth=%s&email=%s' % (str(note_id), self.get_token(),
                                           self.username)
        request = Request(url=DATA_URL+params, method='DELETE')
        try:
            urllib2.urlopen(request)
        except IOError, e:
            return e, -1
        return {}, 0


class Request(urllib2.Request):
    """ monkey patched version of urllib2's Request to support HTTP DELETE
        Taken from http://python-requests.org, thanks @kennethreitz
    """

    def __init__(self, url, data=None, headers={}, origin_req_host=None,
                unverifiable=False, method=None):
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)
        self.method = method

    def get_method(self):
        if self.method:
            return self.method

        return urllib2.Request.get_method(self)


