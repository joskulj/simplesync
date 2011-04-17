# simplesync - managing the configuration files
#
# Copyright 2010-2011 Jochen Skulj, jochen@jochenskulj.de
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

import crypt
import os.path
import random

CONFIG_PATH = "~/.simplesyncrc"

class SyncConfig(object):
    """
    manages a single configuration entry
    """

    def __init__(self, name):
        """
        creates an instance
        Parameters:
        - name
          name of the configuration entry
        """
        self._name = name
        self._password = None
        self._crypt_key = None
        self._dict = { }

    def get_name(self):
        """
        Returns:
        - name of the configuration value
        """
        return self._name

    def set_value(self, key, value):
        """
        sets a property value
        Parameters:
        - key
          key of the property to set
        - value
          property value to set
        """
        self._dict[key] = value

    def set_password(self, password, encrypt=True):
        """
        sets the password
        Parameters:
        - password
          password to set
        - encrypt
          flag if the password should be encrypted
        """
        if encrypt:
            if not self._crypt_key:
                random_number = int(random.random() * 100000000)
                self._crypt_key = str(random_number)
            self._password = crypt.crypt(password, self._crypt_key)
        else:
            self._password = password

    def set_crypt_key(self, crypt_key):
        """
        sets the random key to crypt the password
        Parameters:
        - crypt_key
          random key to crypt the password
        """
        self._crypt_key = crypt_key

    def check_password(self, password):
        """
        checks a password
        Parameters:
        Returns:
        - True:  password match
        - False: password doesn't match
        """
        result = False
        if self._crypt_key and password:
            crypt_password = crypt.crypt(password, self._crypt_key)
            if crypt_password == self._password:
                result = True
        return result

    def has_password(self):
        """
        Returns:
        - True:  a password is set
        - False: no password is set
        """
        return self._password != None

    def get_password(self):
        """
        Returns:
        - encrypted passwort
        """
        return self._password

    def get_crypt_key(self):
        """
        Returns:
        - random key to crypt the password
        """
        return self._crypt_key

    def has_value(self, key):
        """
        checks if the configuration entry has a property of
        a given key
        Parameters:
        - key
          key to check
        Returns:
        - True:  property exists
        - False: property doesn't exists
        """
        return key in self._dict.keys()

    def get_keys(self):
        """
        Returns:
        - list of the keys
        """
        return self._dict.keys()

    def get_value(self, key):
        """
        returns the value of a property by its key
        Parameters:
        - key
          property key
        Returns:
        - property value or None if the property doesn't exist
        """
        result = None
        if self.has_value(key):
            result = self._dict[key]
        return result

    def print_config(self):
        for key in self._dict.keys():
            value = self._dict[key]
            print "[" + key + "] = |" + value + "|"

class SyncConfigList(object):
    """
    manages all configuration entries
    """

    def __init__(self):
        """
        creates an instance
        """
        self._directories = []
        self._list = []
        self._dict = {}
        self._loaded = self._load_config_file()

    def get_entries(self):
        """
        Returns:
        - list of configuration entries
        """
        return self._list

    def get_entry(self, name):
        """
        returns the config entry with a given name
        Parameters:
        - name
          name of a config entry
        Returns:
        - configuration entry with the given name or None if there
          isn't an entry with such a name
        """
        result = None
        if name in self._dict.keys():
            result = self._dict[name]
        return result

    def get_directories(self):
        """
        returns the list of directories
        Returns:
        - list of directories
        """
        return self._directories

    def add_entry(self, entry):
        """
        adds a new entry
        Parameters:
        - entry
          entry to add
        """
        self._list.append(entry)
        self._dict[entry.get_name()] = entry

    def clear_directories(self):
        """
        clears the list of directories
        """
        self._directories = []

    def add_directory(self, directory):
        """
        adds a directory
        Parameters:
        - directory
          directory to add
        """
        self._directories.append(directory)

    def save(self):
        """
        saves the configuration list
        Returns:
        - True:  configuration was save
        - False: saving configuration file failed
        """
        filepath = os.path.expanduser(CONFIG_PATH)
        result = False
        try:
            config_file = open(filepath, "w")
            config_file.write("# simplesync configuration file")
            for config in self._list:
                config_file.write("\n[config:%s]\n" % config.get_name())
                if config.has_password():
                    crypt_key = config.get_crypt_key()
                    if crypt_key:
                        config_file.write("[cryptkey:%s]\n" % crypt_key)
                    password = config.get_password()
                    config_file.write("[password:%s]\n" % password)
                for key in config.get_keys():
                    value = config.get_value(key)
                    config_file.write("%s = %s\n" % (key, value))
                config_file.write("\n")
            for directory in self._directories:
                config_file.write("[directory:%s]\n" % directory)
            config_file.close()
        except:
            result = False
        return result

    def _load_config_file(self):
        """
        loads the configuration file
        Returns:
        - True:  configuration file was loaded
        - False: no configuration file to load
        """
        filepath = os.path.expanduser(CONFIG_PATH)
        result = False
        try:
            config_file = open(filepath, "r")
            new_entry = None
            for line in config_file.readlines():
                line = self.strip_string(line)
                if not self.is_comment(line):
                    if self.is_name(line):
                        if new_entry:
                            self._list.append(new_entry)
                            self._dict[new_entry.get_name()] = new_entry
                        new_entry = SyncConfig(self.get_name(line))
                    if self.is_password(line):
                        if new_entry:
                            new_entry.set_password(self.get_password(line), False)
                    if self.is_crypt_key(line):
                        if new_entry:
                            new_entry.set_crypt_key(self.get_crypt_key(line))
                    if self.is_property(line):
                        key = self.get_key(line)
                        value = self.get_value(line)
                        if new_entry:
                            new_entry.set_value(key, value)
                    if self.is_directory(line):
                        self.add_directory(self.get_directory(line))
            if new_entry:
                self._list.append(new_entry)
                self._dict[new_entry.get_name()] = new_entry
            config_file.close()
            result = True
        except IOError:
            result = False
        return result

    def strip_string(self, string):
        return string.rstrip().lstrip()

    def is_comment(self, string):
        return string.startswith("#")

    def is_name(self, string):
        return string.startswith("[config:") and string.endswith("]")
    
    def is_property(self, string):
        return string.find("=") > - 1

    def is_directory(self, string):
        return string.startswith("[directory:") and string.endswith("]")

    def is_password(self, string):
        return string.startswith("[password:") and string.endswith("]")

    def is_crypt_key(self, string):
        return string.startswith("[cryptkey:") and string.endswith("]")
    
    def get_name(self, string):
        return string[8:len(string) - 1]

    def get_key(self, string):
        pos = string.find("=")
        result = self.strip_string(string[0:pos])
        return result

    def get_value(self, string):
        pos = string.find("=")
        result = self.strip_string(string[pos + 1:])
        pos = string.find("=")
        return result

    def get_directory(self, string):
        return string[11:len(string) - 1]

    def get_password(self, string):
        return string[10:len(string) - 1]

    def get_crypt_key(self, string):
        return string[10:len(string) - 1]
