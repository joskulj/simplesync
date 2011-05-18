# simplesync - managing file properties
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

import hashlib
import os
import os.path
import re
import socket
import sys

from cStringIO import StringIO

from syncdebug import *
from utilio import *

GLOBAL_TAG = "fileproperty"
NAME_TAG = "name"
PATH_TAG = "path"
HOSTNAME_TAG = "hostname"
TIMESTAMP_TAG = "timestamp"
STATE_TAG = "state"
CHECKSUM_TAG = "checksum"
TYPE_TAG = "type"
ENCRYPTED_TAG = "encrypted"
START_TAG = "<simplesyncmeta>"
END_TAG = "</simplesyncmeta>"

TYPE_FILE = "file"
TYPE_DIRECTORY = "directory"

# utility functions

def scan_tag(tag, tagstring):
    """
    extracts a substring that is enclosed by an tag from a string
    Parameters:
    - tag
      enclosing tag
    - tagstring
      string to extract the substring from
    Returns:
    - extracted substring or None if the given tag is not included in the
      tagstring
    """
    result = None
    starttag = "<" + tag + ">"
    endtag = "</" + tag + ">"
    patternstring = starttag + ".*" + endtag
    pattern = re.compile(patternstring)
    match = pattern.search(tagstring)
    if match:
        substring = match.group()
        startindex = len(tag) + 2
        endindex = len(substring) - startindex - 1
        result = substring[startindex:endindex]
    return result

def append_node(stringio, tagname, value):
    """
    creates a node for a single property that form the property
    strings and appends it to a StringIO instance
    Parameters:
    - stringio
      StringIO instance to add the node to
    - tagname
      tag name to use
    - value
      value for the node
    """
    result = None
    if value != None:
        stringio.write("<")
        stringio.write(tagname)
        stringio.write(">")
        stringio.write(value)
        stringio.write("</")
        stringio.write(tagname)
        stringio.write(">")
        result = stringio.getvalue()

def load_property_file(directory, filename):
    """
    loads a list of properties from a file
    Parameters:
    - directory
      directory in which the file to load is located
    - filename
      name of the file to load
    Returns:
    - list of loaded properties
    """
    debug("entering load_property_file()")
    debug_value("directory", directory)
    debug_value("filename", filename)
    propertylist = []
    content = None
    f = open_file(directory, filename, "r")
    if f:
        stringio = StringIO()
        for line in f.readlines():
            stringio.write(line)
        f.close()
        content = stringio.getvalue()
    if content:
        pos = 0
        while pos < len(content):
            start = content.find("<fileproperty>", pos)
            end = content.find("</fileproperty>", start)
            if start != -1 and end != -1:
                end = end + len("</fileproperty>")
                substr = content[start:end]
                fileproperty = FileProperty()
                fileproperty.set_property_string(substr)
                name = fileproperty.get_name()
                debug_value("fileproperty.name", fileproperty.get_name())
                debug_value("fileproperty.path", fileproperty.get_path())
                debug_value("fileproperty.hostname", fileproperty.get_hostname())
                debug_value("fileproperty.timestamp", fileproperty.get_timestamp())
                debug_value("fileproperty.checksum", fileproperty.get_checksum())
                debug_value("fileproperty.state", fileproperty.get_state())
                debug_value("fileproperty.type", fileproperty.get_type())
                debug("--")
                propertylist.append(fileproperty)
                pos = end
            else:
                pos = len(content) + 1
        debug("exiting load_property_file()")
    return propertylist

def save_property_file(directory, filename, propertylist):
    """
    saves a list of properties to a file
    Parameters:
    - directory
      directory in which the file should be saved
    - filename
      name of the file to save
    - propertylist
      list of properties to save
    Returns:
    - True:  file was successfully saved
    - False: file could not be saved
    """
    debug("entering save_property_file()")
    debug_value("directory", directory)
    debug_value("filename", filename)
    success = False
    if propertylist:
        f = open_file(directory, filename, "w")
        if f:
            f.write(START_TAG)
            for p in propertylist:
                debug_value("fileproperty.name", p.get_name())
                debug_value("fileproperty.path", p.get_path())
                debug_value("fileproperty.hostname", p.get_hostname())
                debug_value("fileproperty.timestamp", p.get_timestamp())
                debug_value("fileproperty.checksum", p.get_checksum())
                debug_value("fileproperty.state", p.get_state())
                debug_value("fileproperty.type", p.get_type())
                debug_value("fileproperty.encrypted", p.get_encrypted())
                debug("--")
                f.write(p.get_property_string())
            f.write(END_TAG)
            f.close()
            success = True
        else:
            success = False
    return success
    debug("exiting save_property_file()")

def create_checksum(filename):
    """
    creates a checksum for a file
    Parameters:
    - filename
      name of the file to create a checksum for
    Return:
    - checksum for the given file
    """
    m = hashlib.md5()
    try:
        fd = open(filename, "rb")
    except IOError:
        return None
    content = fd.readlines()
    fd.close()
    for line in content:
        m.update(line)
    return m.hexdigest()

# classes

class FileProperty(object):
    """
    manages the basic file properties
    """

    def __init__(self):
        """
        creates an instance
        """
        self._name = None
        self._path = None
        self._hostname = socket.gethostname()
        self._timestamp = None
        self._state = None
        self._checksum = None
        self._type = TYPE_FILE
        self._encrypted = False

    def get_name(self):
        return self._name

    def get_path(self):
        return self._path

    def get_hostname(self):
        return self._hostname

    def get_timestamp(self):
        return self._timestamp

    def get_state(self):
        return self._state

    def get_checksum(self):
        return self._checksum

    def get_type(self):
        return self._type

    def get_encrypted(self):
        return self._encrypted

    def is_host_property(self):
        return self._hostname == socket.gethostname()

    def is_directory(self):
        result = False
        if self.get_type() == TYPE_DIRECTORY:
            result = True
        return result

    def get_property_string(self):
        """
        Returns:
        - file properties as a property string
        """
        stringio = StringIO()
        stringio.write("<")
        stringio.write(GLOBAL_TAG)
        stringio.write(">")
        append_node(stringio, NAME_TAG, self._name)
        append_node(stringio, PATH_TAG, self._path)
        append_node(stringio, HOSTNAME_TAG, self._hostname)
        append_node(stringio, TIMESTAMP_TAG, str(self._timestamp))
        append_node(stringio, STATE_TAG, self._state)
        append_node(stringio, CHECKSUM_TAG, self._checksum)
        append_node(stringio, TYPE_TAG, self._type)
        append_node(stringio, ENCRYPTED_TAG, str(self._encrypted))
        stringio.write("</")
        stringio.write(GLOBAL_TAG)
        stringio.write(">")
        return stringio.getvalue()

    def set_values(self, otherproperty):
        """
        copies the values from an other property object
        Parameters:
        - otherproperty
          other property to take the values from
        """
        self._name = otherproperty.get_name()
        self._path = otherproperty.get_path()
        self._timestamp = otherproperty.get_timestamp()
        self._state = otherproperty.get_state()
        self._checksum = otherproperty.get_checksum()
        self._type = otherproperty.get_type()

    def set_property_string(self, propertystring):
        """
        sets the file properties by a property string
        Parameters:
        - propertystring
          property string to set
        """
        globalvalue = scan_tag(GLOBAL_TAG, propertystring)
        if globalvalue:
            namevalue = scan_tag(NAME_TAG, propertystring)
            pathvalue = scan_tag(PATH_TAG, propertystring)
            hostnamevalue = scan_tag(HOSTNAME_TAG, propertystring)
            timestampvalue = scan_tag(TIMESTAMP_TAG, propertystring)
            statevalue = scan_tag(STATE_TAG, propertystring)
            checksumvalue = scan_tag(CHECKSUM_TAG, propertystring)
            typevalue = scan_tag(TYPE_TAG, propertystring)
            encryptedvalue = scan_tag(ENCRYPTED_TAG, propertystring)
            if namevalue:
                self._name = namevalue
            else:
                self._name = None 
            if pathvalue:
                self._path = pathvalue
            else:
                self._path = None
            if hostnamevalue:
                self._hostname = hostnamevalue
            else:
                self._hostname = None
            if timestampvalue:
                try:
                    self._timestamp = float(timestampvalue)
                except ValueError:
                    self._timestamp = None
            if statevalue:
                self._state = statevalue
            else:
                self._state = None
            if checksumvalue:
                self._checksum = checksumvalue
            else:
                self._checksum = None
            if typevalue:
                self._type = typevalue
            else:
                self._type = TYPE_FILE
            if encryptedvalue:
                if encryptedvalue == "True":
                    self._encrypted = True
                else:
                    self._encrypted = False
            else:
                self._encrypted = False

    def set_state(self, state):
        self._state = state

    def set_checksum(self, checksum):
        self._checksum = checksum

    def set_encrypted(self, flag):
        self._encrypted = flag

    def scan(self, filepath, rootpath = None):
        """
        scans the properties of a local file
        Parameters:
        - file_path
          path of the file or directory to scan
        - root_path
          absolute path of the directory that
          is syncronized
        Returns:
        - True
          scanning was successful
        - False
          scanning failed
        """
        debug("entering FileProperty.scan()")
        debug_value("filepath", filepath)
        result = False
        if os.path.exists(filepath):
            debug("file exists")
            abspath = os.path.abspath(filepath)
            if rootpath != None and os.path.exists(rootpath):
                prefix = os.path.abspath(rootpath)
                if abspath.startswith(prefix):
                    index = len(prefix)
                    self._path = abspath[index:]
            else:
                self._path = abspath
            (tmp, filename) = os.path.split(abspath)
            self._name = filename
            self._timestamp = os.path.getmtime(abspath)
            if os.path.isdir(filepath):
                self._type = TYPE_DIRECTORY
                debug("is directory")
            if os.path.isfile(filepath):
                self._type = TYPE_FILE
                self._checksum = create_checksum(abspath)
                debug("is file")
        debug("exiting FileProperty.scan()")
        return result
