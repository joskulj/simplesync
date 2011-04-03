# simplesync - access to local files
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

import re
import glob
import os
import os.path
import shutil

from cStringIO import StringIO
from fileproperty import *
from utilio import *
from syncdebug import *

# filename for the file containing meta data
META_FILENAME = ".simplesyncmeta"

# Constants for the file state
STATE_UNKNOWN = "unknown"
STATE_NEW = "new"
STATE_EXISTING = "existing"
STATE_UPDATED = "updated"
STATE_DELETED = "deleted"

class LocalProperty(object):
    """
    represents the properties of a local file
    """

    def __init__(self, filepath, rootpath, meta = None):
        """
        creates an instance
        Parameters:
        - filepath
        - rootpath
        - meta
          meta properties of a the file
        """
        self._state = STATE_UNKNOWN
        self._meta = None
        if filepath != None:
            self._current = FileProperty()
            self._current.scan(filepath, rootpath)
        else:
            self._current = None
        self.update_state()

    def get_name(self):
        """
        Returns:
        - name of the file
        """
        result = None
        if self._current:
            result = self._current.get_name()
        else:
            if self._meta:
                result = self._meta.get_name()
        return result

    def is_directory(self):
        """
        checks if the property represents a directory
        Returns:
        - True:  property represents a directory
        - False: property doesn't represent a directory
        """
        result = False
        if self._current:
            if self._current.get_type() == TYPE_DIRECTORY:
                result = True
        if self._meta:
            if self._meta.get_type() == TYPE_DIRECTORY:
                result = True
        return result

    def get_timestamp(self):
        """
        Returns:
        - timstamp of the file
        """
        result = None
        if self._current:
            result = self._current.get_timestamp()
        else:
            if self._meta:
                result = self._meta.get_timestamp()
        return result

    def get_state(self):
        """
        Returns:
        - state of the local file
        """
        self.update_state()
        return self._state

    def get_current(self):
        """
        Returns:
        - current file property
        """
        return self._current

    def get_meta(self):
        """
        Returns:
        - meta property
        """
        return self._meta

    def set_current(self, current):
        """
        sets the current file property
        Parameters:
        - current
          current file property
        """
        self._current = current
        self.update_state()

    def set_meta(self, meta):
        """
        sets the meta properties
        Parameters:
        - meta
          meta property
        """
        self._meta = meta
        self.update_state()

    def update_state(self):
        """
        updates the state of the local file
        """
        debug("entering LocalProperty.update_state()")
        debug_value("name", self.get_name())
        debug_value("current exist", self._current != None)
        debug_value("meta exist", self._meta != None)
        if self._meta == None and self._current != None:
            self._state = STATE_NEW
        if self._meta != None and self._current == None:
            self._state = STATE_DELETED
        if self._meta != None and self._current != None:
            meta_timestamp = self._meta.get_timestamp()
            current_timestamp = self._current.get_timestamp()
            debug_value("meta timestamp", meta_timestamp)
            debug_value("current timestamp", current_timestamp)
            if current_timestamp - meta_timestamp < 0.1:
                self._state = STATE_EXISTING
            else:
                self._state = STATE_UPDATED
        if self._current:
            self._current.set_state(self._state)
        debug_value("state", self._state)
        debug("exiting LocalProperty.update_state()")

class SyncLocal(object):
    """
    access local files for syncronization
    """

    def __init__(self, root):
        """
        creates an instance
        Parameters:
        - root
          root directory to be synced
        """
        self._root = root
        self._directory = None
        self._list = []
        self._dict = {}

    def get_root(self):
        """
        Returns:
        - root directory to be synced
        """
        return self._root

    def append_property(self, fileproperty):
        """
        appends a file property to the list
        Parameters:
        - fileproperty
          file property to append
        """
        self._list.append(fileproperty)
        self._dict[fileproperty.get_name()] = fileproperty

    def update_property(self, fileproperty):
        """
        updates a file property
        Parameters:
        - fileproperty
          fileproperty to update
        """
        name = fileproperty.get_name()
        if name in self._dict.keys():
            entry = self._dict[name]
            entry.set_current(fileproperty)
        else:
            newproperty = LocalProperty(None, None)
            newproperty.set_current(fileproperty)
            self._list.append(newproperty)
            self._dict[name] = newproperty

    def get_properties(self):
        """
        Returns:
        - list of properties
        """
        return self._list

    def get_property(self, name):
        """
        gets a file property by its name
        Parameters:
        - name
          name of a property
        Returns:
        - file property or None
        """
        result = None
        if name in self._dict.keys():
            result = self._dict[name]
        return result

    def delete(self, fileproperty):
        """
        deletes a to a file property corresponding file
        Parameters:
        - fileproperty
          corresponding file property
        """
        if not fileproperty:
            return
        name = fileproperty.get_name()
        if name in self._dict.keys():
            root = self._root
            deldirectory = fileproperty.get_path()
            delpath = root + deldirectory
            success = True
            if fileproperty.is_directory():
                try:
                    shutil.rmtree(delpath)
                except OSError:
                    success = False
            else:
                try:
                    os.remove(delpath)
                except:
                    success = False
        if success:
            self.update_property(fileproperty)

    def read_directory(self, dirpath):
        """
        reads a given directory
        Parameters:
        - dirpath
          full path of the directory to read
        """
        debug("entering SyncLocal.read_directory()")
        debug_value("dirpath", dirpath)
        self._list = []
        self._dict = {}
        if check_directory(dirpath):
            self._directory = dirpath
            for infile in glob.glob(os.path.join(dirpath, "*")):
                debug_value("infile", infile)
                localproperty = LocalProperty(infile, self._root)
                debug_value("path", localproperty.get_current().get_path())
                debug_value("timestamp", localproperty.get_current().get_timestamp())
                debug_value("checksum", localproperty.get_current().get_checksum())
                self.append_property(localproperty)
            self.load_meta()
            for p in self._list:
                p.update_state()
        else:
            self._directory = None
        debug("exiting SyncLocal.read_directory()")

    def load_meta(self):
        """
        loads the metadata
        """
        debug("entering SyncLocal.load_meta()")
        success = False
        if self._directory:
            propertylist = load_property_file(self._directory, META_FILENAME)
            for fileproperty in propertylist:
                name = fileproperty.get_name()
                debug_value("name", name)
                debug_value("path", fileproperty.get_path())
                debug_value("timestamp", fileproperty.get_timestamp())
                debug_value("checksum", fileproperty.get_checksum())
                if name in self._dict.keys():
                    debug("existing property")
                    self._dict[name].set_meta(fileproperty)
                else:
                    debug("new property")
                    newproperty = LocalProperty(None, None)
                    newproperty.set_meta(fileproperty)
                    self._list.append(newproperty)
                    self._dict[name] = newproperty
            success = True
        debug("exiting SyncLocal.load_meta")
        return success

    def save_meta(self):
        success = False
        if self._directory:
            propertylist = []
            for p in self._list:
                if p.get_current():
                    propertylist.append(p.get_current())
            save_property_file(self._directory, META_FILENAME, propertylist)
            success = True
        return success
