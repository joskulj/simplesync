# simplesync - server-related functions
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
import shutil
import os
import os.path

from cStringIO import StringIO

from errorlog import *
from fileproperty import *
from localproperty import *
from syncconfig import *
from synccrypt import *
from syncdebug import *

# Constants for config keys
CONFIG_KEY_TYPE = "type"
CONFIG_KEY_ROOT = "root"
CONFIG_KEY_SERVER_DIRECTORY = "server-directory"
CONFIG_KEY_ENCRYPTION = "encryption"

CONFIG_VALUE_FILE = "filesystem"
CONFIG_VALUE_FTP = "ftp"
CONFIG_VALUE_TRUE = "true"

# Name of the server meta file
SERVER_META_FILENAME = "syncsrvmeta"

def create_hash(s):
    """
    creates a hash value of a string
    Parameters:
    - s
      a string
    Returns:
    - hash value of s (hexadecimal)
    """
    # m = hashlib.md5()
    # m.update(s)
    # return m.hexdigest()
    stringio = StringIO()
    for i in range(0, len(s)):
        c = s[i:i + 1]
        if c == "/":
            stringio.write(":::")
        else:
            stringio.write(c)
    return stringio.getvalue()

class SyncServer(ErrorLog):
    """
    facade for server-related operations
    """

    def __init__(self, config, local, localdir):
        """
        creates an instance
        Parameters:
        - config
          configuration entry to use
        - local
          SyncLocal to access the local files
        - localdir
          local directory to syncronize
        """
        ErrorLog.__init__(self)
        self._instance = None
        self._config = config
        self._local = local
        self._localdir = localdir
        self._encryption = False
        if self._local.get_root():
            if self._localdir.startswith(self._local.get_root()):
                root = self._local.get_root()
                pos = len(root)
                ldir = self._localdir
                self._relative_path = ldir[pos:]
        else:
            self._relative_path = self._localdir
        self._list = []
        self._dict = {}
        typeconfig = self._config.get_value(CONFIG_KEY_TYPE)
        if typeconfig == CONFIG_VALUE_FILE:
            self._instance = SyncFileServer(self)
        if typeconfig == CONFIG_VALUE_FTP:
            pass
        encryptionconfig = self._config.get_value(CONFIG_KEY_ENCRYPTION)
        if encryptionconfig == CONFIG_VALUE_TRUE:
            self._encryption = True
        if self._instance == None:
            self.error("type configuration is invalid.")

    def clear_properties(self):
        """
        removes all file properties
        """
        self._list = []
        self._dict = {}

    def append_property(self, fileproperty):
        """
        appends a file property
        Parameters:
        - file property
          file property to append
        """
        self._list.append(fileproperty)
        self._dict[fileproperty.get_name()] = fileproperty

    def update_property(self, fileproperty):
        """
        updates a file property
        - file property
          file property to update
        """
        name = fileproperty.get_name()
        if name in self._dict.keys():
            existingproperty = self._dict[name]
            existingproperty.set_values(fileproperty)
        else:
            self.append_property(fileproperty)

    def get_property_list(self):
        """
        Returns:
        - list of file properties
        """
        return self._list

    def get_property(self, name):
        """
        returns the property identified by a name
        Parameters:
        - name
          name of the requested property
        Returns:
        - property with the given name
        """
        result = None
        if name in self._dict.keys():
            result = self._dict[name]
        return result

    def get_config(self):
        """
        Returns:
        - configuration entry to use
        """
        return self._config

    def get_local_directory(self):
        """
        Returns:
        - local directory to syncronize
        """
        return self._localdir

    def get_relative_path(self):
        """
        Returns:
        - relative path within the directory to syncronize
        """
        return self._relative_path

    def get_local(self):
        """
        Returns:
        - SyncLocal to use
        """
        return self._local

    def connect(self):
        """
        connects to server
        """
        if self._instance:
            self._instance.connect()
        else:
            self.error("connect() failed. No server instance.")

    def disconnect(self):
        """
        disconnects from server
        """
        if self._instance:
            self._instance.disconnect()
        else:
            self.error("disconnect() failed. No server instance.")

    def upload(self, fileproperty, synccrypt=None):
        """
        uploads a file to the server
        Parameters:
        - fileproperty
          property of the file to upload
        - synccrypt
          optional SyncCrypt instance to use
        """
        if self._instance:
            self._instance.upload(fileproperty, synccrypt)
        else:
            self.error("upload() failed. No server instance.")

    def download(self, fileproperty, synccrypt=None):
        """
        downloads a file from the server
        Parameters:
        - fileproperty
          property of the file to download
        - synccrypt
          optional SyncCrypt instance to use
        """
        if self._instance:
            self._instance.download(fileproperty, synncrypt)
        else:
            self.error("download() failed. No server instance.")


    def delete(self, fileproperty):
        """
        deletes a file from the server
        Parameters:
        - fileproperty
          property of the file to delete
        """
        if self._instance:
            self._instance.delete(fileproperty)
        else:
            self.error("delete() failed. No server instance.")

    def load_meta(self):
        """
        loads the meta data
        """
        if self._instance:
            self._instance.load_meta()
        else:
            self.error("load_meta() failed. No server instance.")

    def save_meta(self):
        """
        saves the meta data
        """
        if self._instance:
            self._instance.save_meta()
        else:
            self.error("save_meta() failed. No server instance.")


class SyncFileServer(object):
    """
    implementation of server-related operations for 
    syncronization via filesystem
    """

    def __init__(self, parent):
        """
        creates an instance
        Parameter:
        - parent
          parent object
        """
        self._parent = parent
        config = self._parent.get_config()
        self._root = config.get_value(CONFIG_KEY_ROOT)
        self._serverdirectory = config.get_value(CONFIG_KEY_SERVER_DIRECTORY)

    def connect(self):
        """
        connects to server
        """
        pass

    def disconnect(self):
        """
        disconnects from server
        """
        pass

    def upload(self, fileproperty, synccrypt):
        """
        uploads a file to the server
        Parameters:
        - fileproperty
          property of the file to upload
        - synccrypt
          optional SyncCrypt instance
        """
        success = False
        if fileproperty.is_directory():
            # directories are not uploaded
            success = True
        else:
            # create source path
            relativepath = fileproperty.get_path()
            root = self._parent.get_local().get_root()
            srcpath = root + relativepath
            # create destination path
            destdirectory = self._serverdirectory
            destname = create_hash(relativepath)
            destpath = os.path.join(destdirectory, destname)
            # copy file
            success = True
            try:
                if synccrypt:
                    try:
                        cryptpath = synccrypt.encrypt_file(srcpath)
                    except:
                        message = "Unable to encrypt: " + srcpath
                        self._parent.error(message)
                    srcpath = cryptpath
                shutil.copyfile(srcpath, destpath)
                if synccrypt:
                    try:
                        os.remove(srcpath)
                    except OSError:
                        message = "Unable to delete: " + srcpath
                        self._parent.error(message)
            except:
                message = "Unable to upload: " + srcpath
                self._parent.error(message)
                success = False
        # update meta data
        if success:
            self._parent.update_property(fileproperty)

    def download(self, fileproperty, synccrypt):
        """
        downloads a file from the server
        Parameters:
        - fileproperty
          property of the file to download
        - synccrypt
          optional SyncCrypt instance
        """
        # TODO: implement encryption
        success = True
        relativepath = fileproperty.get_path()
        if fileproperty.is_directory():
            # create directory path
            root = self._parent.get_local().get_root()
            dirpath = root + relativepath
            dirpath = root + relativepath
            # check if directory already exists
            exist = os.path.exists(dirpath)
            isdir = os.path.isdir(dirpath)
            if not exist and not isdir:
                # create the directory
                success = True
                try:
                    os.mkdir(dirpath)
                except OSError:
                    message = "Unable to create directory: " + dirpath
                    self._parent.error(message)
                    success =  False
        else:
            # create source path
            srcname = create_hash(relativepath)
            srcdirectory = self._serverdirectory
            srcpath = os.path.join(srcdirectory, srcname)
            # create destination path
            root = self._parent.get_local().get_root()
            destpath = root + relativepath
            # copy file
            success = True
            try:
                origpath = None
                if synccrypt:
                    origdestpath = destpaath
                    destpath = destpath + ENCRYPTION_EXTENSION
                shutil.copyfile(srcpath, destpath)
                if synccrypt:
                    try:
                        synccrypt.decrypt(destpath)
                    except:
                        message = "Unable to decrypt: " + destpath
                        self._parent.error(message)
                    if os.path.exists(origdestpath):
                        try:
                            os.remove(destpath)
                        except OSError:
                            message = "Unable to delete: " + destpath
                            self._parent.error(message)
            except:
                message = "Unable to download: " + srcpath
                self._parent.error(message)
                success = False
        # update meta data
        if success:
            self._parent.get_local().update_property(fileproperty)

    def delete(self, fileproperty):
        """
        deletes a file from the server
        Parameters:
        - fileproperty
          property of the file to delete
        """
        debug("entering SyncFileServer.delete()")
        relativepath = fileproperty.get_path()
        delname = create_hash(relativepath)
        deldirectory = self._serverdirectory
        delpath = os.path.join(deldirectory, delname)
        debug_value("delpath", delpath)
        success = True
        if not fileproperty.is_directory():
            try:
                os.remove(delpath)
                debug("file deleted")
            except:
                message = "Unable to delete: " + delpath
                debug(message)
                self._parent.error(message)
                success = False
        if success:
            name = fileproperty.get_name()
            prop = self._parent.get_property(name)
            prop.set_state(STATE_DELETED)
            debug_value("property name", prop.get_name())
            debug_value("propety state", prop.get_state())
        debug("exiting SyncFileServer.delete()")

    def get_meta_filename(self):
        """
        Returns:
        - name of the meta file
        """
        relativepath = self._parent.get_relative_path()
        return create_hash(relativepath)

    def load_meta(self):
        """
        loads the meta data
        """
        debug("entering SyncFileServer.load_meta()") 
        self._parent.clear_properties()
        directory = self._serverdirectory
        fname = self.get_meta_filename()
        propertylist = load_property_file(directory, fname)
        for p in propertylist:
            self._parent.append_property(p)
        debug("exiting SyncFileServer.load_meta()")

    def save_meta(self):
        """
        saves the meta data
        """
        debug("entering SyncFileServer.save_meta()")
        propertylist = self._parent.get_property_list()
        directory = self._serverdirectory
        fname = self.get_meta_filename()
        save_property_file(directory, fname, propertylist)
        debug("exiting SyncFileServer.save_meta()")

