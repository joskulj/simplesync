# simplesync - processing actions to synchronize files
#
# Copyright 2010 Jochen Skulj, jochen@jochenskulj.de
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from syncdebug import *
from syncserver import *
from localproperty import *

# Constants representing actions
ACTION_CONFLICT = -1
ACTION_UPLOAD = 0
ACTION_DOWNLOAD = 1
ACTION_DEL_CLIENT = 2
ACTION_DEL_SERVER = 3

# Constants for action titles
TITLE_UPLOAD = "Uploading %s"
TITLE_DOWNLOAD = "Downloading %s"
TITLE_DEL_LOCAL = "Deleting %s locally"
TITLE_DEL_SERVER = "Deleting %s on server"

class ActionEntry(object):
    """
    manages a single action to process
    """

    def __init__(self, localproperty, serverproperty, action):
        """
        creates an instance
        Parameters:
        - localproperty
          file property on client side
        - serverproperty
          file property on server side
        - action
          action to process
        """
        self._localproperty = localproperty
        self._serverproperty = serverproperty
        self._action = action

    def get_name(self):
        """
        Returns:
        - name of the properties
        """
        name = None
        if self._localproperty:
            name = self._localproperty.get_name()
        if self._serverproperty:
            name = self._serverproperty.get_name()
        return name

    def get_local_property(self):
        """
        Returns:
        - file property on client side
        """
        return self._localproperty

    def get_server_property(self):
        """
        Returns:
        - file property on server side
        """
        return self._serverproperty

    def get_action(self):
        """
        Returns:
        - action to process
        """
        return self._action

    def get_title(self):
        """
        Returns:
        - title for the action to process
        """
        result = ""
        title = None
        name = None
        if self._action == ACTION_UPLOAD and self._localproperty:
            name = self._localproperty.get_name()
            title = TITLE_UPLOAD
        if self._action == ACTION_DOWNLOAD and self._serverproperty:
            name = self._serverproperty.get_name()
            title = TITLE_DOWNLOAD
        if self._action == ACTION_DEL_CLIENT and self._localproperty:
            name = self._localproperty.get_name()
            title = TITLE_DEL_LOCAL
        if self._action == ACTION_DEL_SERVER and self._serverproperty:
            name = self._serverproperty.get_name()
            title = TITLE_DEL_SERVER
        if title != None and name != None:
            result = title % name
        return result

    def is_directory_action(self):
        """
        checks, if the action represents a directory operation
        Returns:
        - True:  action represents a directory operation
        - False: action doesn't represents a directory operation
        """
        result = False
        if self._localproperty:
            result = self._localproperty.is_directory()
        if self._serverproperty:
            result = self._serverproperty.is_directory()
        return result

    def is_obsolete(self):
        """
        checks, if the action is obsolete
        Returns:
        - True:  action is obsolete
        - False: action is not obsolete
        """
        result = False
        if self._action == ACTION_UPLOAD or self._action == ACTION_DOWNLOAD:
            if not self.is_directory_action():
                localchecksum = None
                if self._localproperty:
                    localchecksum = self._localproperty.get_checksum()
                serverchecksum = None
                if self._serverproperty:
                    serverchecksum = self._serverproperty.get_checksum()
                if localchecksum == serverchecksum:
                    result = True
        return result

class PropertyEntry(object):
    """
    manages local and server properties
    """

    def __init__(self, localproperty, serverproperty):
        self._localproperty = localproperty
        self._serverproperty = serverproperty

    def set_local_property(self, localproperty):
        self._localproperty = localproperty

    def set_server_property(self, serverproperty):
        self._serverproperty = serverproperty

    def get_local_property(self):
        return self._localproperty

    def get_server_property(self):
        return self._serverproperty

class SyncProcessor(object):
    """
    controls and performs the action to synchronize a
    directory
    """

    def __init__(self, synclocal, directory, syncserver):
        """
        creates an instance
        - synclocal
          SyncLocal to access local files
        - directory
          local directory to synchronize
        - syncserver
          syncserver to use
        """
        self._synclocal = synclocal
        self._syncserver = syncserver
        self._actions = []
        self._actionindex = 0
        self._directory = directory
        self._synccrypt = None
        self._encryptupload = False

    def append_action(self, newaction):
        """
        appends a new action
        - newaction
          new action to append
        """
        debug("entering SyncProcessor.append_action()")
        debug_value("new action", newaction.get_title())
        appendflag = True
        if newaction.is_obsolete():
            appendflag = False
            debug("action is obsolete")
        for action in self._actions:
            if action.get_name() == newaction.get_name():
                appendflag = False
                debug("action already exists")
                break
        if appendflag == True:
            self._actions.append(newaction)
            debug("action appended")
        debug("exiting SyncProcessor.append_action()")

    def needs_encryption(self):
        """
        checks if the SyncProcessor needs a SyncCrypt instance to
        decrypt downloads
        Returns:
        - True:  needs a SyncCrypt instance
        - False: doesn't need a SyncCrypt instance
        """
        result = False
        for action in self._actions:
            if action.get_action() == ACTION_DOWNLOAD:
                serverproperty = action.get_server_property()
                if serverproperty.get_encrypted():
                    result = True
                    break
        return result

    def set_encryption(self, synccrypt, uploadflag=False):
        """
        sets the SyncCrypt instance
        Parameters:
        - synccrypt
          SyncCrypt instance
        - uploadflag
          determines if uploads should be encrypted
        """
        self._synccrypt = synccrypt
        self._encryptupload = uploadflag

    def startup(self):
        """
        should be called before processing starts
        """
        self._init_actions()

    def shutdown(self):
        """
        should be called after processing
        """
        self._synclocal.save_meta()
        self._syncserver.save_meta()
        self._syncserver.disconnect()

    def has_open_actions(self):
        """
        Returns:
        - True:  there are actions to process
        - False: no actions to process
        """
        return self._actionindex < len(self._actions)

    def get_actions(self):
        """
        Returns:
        - list of actions
        """
        return self._actions

    def get_action_count(self):
        """
        Returns:
        - total count of all actions
        """
        return len(self._actions)

    def get_action_index(self):
        """
        Returns:
        - index of the next action to process
        """
        return self._actionindex

    def get_action_title(self):
        """
        Returns:
        - title of the next action to process
        """
        result = None
        if self._actionindex < len(self._actions):
            result = self._actions[self._actionindex].get_title()
        return result

    def process_next_action(self):
        """
        processes the next action
        """
        if self.has_open_actions():
            action = self._actions[self._actionindex]
            self._actionindex = self._actionindex + 1
            if action.get_action() == ACTION_UPLOAD:
                localproperty = action.get_local_property()
                if self._encryptupload:
                    self._syncserver.upload(localproperty, self._synccrypt)
                else:
                    self._syncserver.upload(localproperty, False)
            if action.get_action() == ACTION_DOWNLOAD:
                serverproperty = action.get_server_property()
                self._syncserver.download(serverproperty, self._synccrypt)
            if action.get_action() == ACTION_DEL_CLIENT:
                localproperty = action.get_local_property()
                self._synclocal.delete(localproperty)
            if action.get_action() == ACTION_DEL_SERVER:
                serverproperty = action.get_server_property()
                self._syncserver.delete(serverproperty)

    def _init_actions(self):
        """
        initiates the actions to process
        """
        debug("entering SyncProcessor._init_actions()")
        for entry in self._merge_properties():
            local = entry.get_local_property()
            localcurrent = None
            if local:
                localcurrent = local.get_current()
            server = entry.get_server_property()
            if local != None and server == None:
                debug("local != None and server == None")
                debug_value("local.get_name()", local.get_name())   
                debug_value("local.get_state()", local.get_state())
                if local.get_state() != STATE_DELETED:
                    action = ActionEntry(localcurrent, server, ACTION_UPLOAD)
                    self.append_action(action)
            if local == None and server != None:
                debug("local == None and server != None")
                debug_value("server.get_name()", server.get_name()) 
                debug_value("server.get_state()", server.get_state())
                if server.get_state() != STATE_DELETED:
                    action = ActionEntry(localcurrent, server, ACTION_DOWNLOAD)
                    self.append_action(action)
            if local != None and server != None:
                debug("local != None and server != None")
                debug_value("local.get_name()", local.get_name())   
                debug_value("local.get_state()", local.get_state())
                debug_value("server.get_name()", server.get_name()) 
                debug_value("server.get_state()", server.get_state())
                delflag = False
                if server.get_state() == STATE_DELETED:
                    localstamp = local.get_timestamp()
                    serverstamp = server.get_timestamp()
                    if localstamp - serverstamp > 0.1 and local.get_state() == STATE_NEW:
                        action = ActionEntry(localcurrent, server, ACTION_UPLOAD)
                    else:
                        action = ActionEntry(localcurrent, server, ACTION_DEL_CLIENT)
                    self.append_action(action)
                    delflag = True
                if local.get_state() == STATE_DELETED:
                    action = ActionEntry(localcurrent, server, ACTION_DEL_SERVER)
                    self.append_action(action)
                    delflag = True
                if not delflag:
                    localstamp = local.get_timestamp()
                    serverstamp = server.get_timestamp()
                    debug_value("localstamp - serverstamp", localstamp - serverstamp)
                    if localstamp - serverstamp > 0.1:
                        action = ActionEntry(localcurrent, server, ACTION_UPLOAD)
                        self.append_action(action)
                        debug_value("action", action.get_title())
                    debug_value("serverstamp - localstamp", serverstamp - localstamp)
                    if serverstamp - localstamp > 0.1:
                        action = ActionEntry(localcurrent, server, ACTION_DOWNLOAD)
                        self.append_action(action)
                        debug_value("action", action.get_title())
        debug("exiting SyncProcessor._init_actions()")

    def _merge_properties(self):
        """
        merges local and server properties
        Returns:
        - list of merged PropertyEntries
        """
        debug("entering SyncProcessor._merge_properties()")
        propertylist = []
        propertydict = {}
        self._synclocal.read_directory(self._directory)
        for prop in self._synclocal.get_properties():
            entry = PropertyEntry(prop, None)
            propertylist.append(entry)
            debug_value("local property", prop.get_name())
            propertydict[prop.get_name()] = entry
        self._syncserver.connect()
        self._syncserver.load_meta()
        for prop in self._syncserver.get_property_list():
            name = prop.get_name()
            debug_value("server property", name)
            if name in propertydict.keys():
                entry = propertydict[name]
                entry.set_server_property(prop)
            else:
                entry = PropertyEntry(None, prop)
                propertylist.append(entry)
        debug("exiting SyncProcessor._merge_properties()")
        return propertylist
