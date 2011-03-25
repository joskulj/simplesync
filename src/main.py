#!/usr/bin/python

# simplesync - main program
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

import glob
import os
import os.path
import sys

from cStringIO import StringIO

from localproperty import *
from syncconfig import *
from synccrypt import *
from syncserver import *
from syncprocessor import *

__author__ = "Jochen Skulj"
__copyright__ = "Copyright 2010, Jochen Skulj"
__credits__ = [ ]
__license__ = "GPL"
__version__ = "0.2.0"
__maintainer__ = "Jochen Skulj"
__email__ = "jochen@jochenskulj.de"
__status__ = "Development"

# command parameters keys
PARAMETER_CONFIG = "-c"
PARAMETER_DIRECTORY = "-d"
PARAMETER_RECURSIVE = "-r"

# constants for config keys
CONFIG_KEY_ENCRYPTION = "encryption"

class OutputBase(object):
	"""
	Base class for classes to handle output
	"""

	def __init__(self):
		"""
		creates an instance
		"""
		pass

	def output(self, message):
		"""
		processes the output of a message
		Parameters:
		- message
		  message string to output
		"""
		pass

class OutputConsole(OutputBase):
	"""
	class to handle output on console
	"""

	def __init__(self):
		"""
		creates an instance
		"""
		pass

	def output(self, message):
		"""
		processes the output of a message
		Parameters:
		- message
		  message string to output
		"""
		print message

def get_version():
	"""
	Returns:
	- version number of the application
	"""
	return __version__

def get_parameter(key, expand=True):
	"""
	retrieves the command line parameter following afte a given
	key
	Parameters:
	- key
	  key that indicates the parameter
	- expand
	  expand parameter as a file or directory
	Returns:
	- parameter or None
	"""
	result = None
	length = len(sys.argv)
	for index in range(1, length):
		arg = sys.argv[index]
		if arg == key:
			result = ""
			if index < length - 1:
				result = sys.argv[index + 1]
				if result.startswith("-"):
					result = ""
				else:
					if expand:
						result = os.path.expanduser(os.path.abspath(result))
					break
	return result


def get_config():
	"""
	Returns:
	- configuration to use
	"""
	result = None
	config_name = get_parameter(PARAMETER_CONFIG, False)
	if not config_name:
		sys.stderr.write("No configuration specified.\n")
		sys.exit(-1)
	config_list = SyncConfigList()
	result = config_list.get_entry(config_name)
	if not result:
		sys.stderr.write("Configuration not found: ")
		sys.stderr.write(config_name)
		sys.stderr.write("\n")
		sys.exit(-1)
	return result

def get_directory():
	"""
	Returns:
	- directory to sync
	"""
	result = get_parameter(PARAMETER_DIRECTORY)
	if result == None:
		result = os.getcwd()
	return result

def get_subdirectories(dirpath):
	"""
	retrieves the subdirectories of a directory
	Parameters:
	- dirpath
	  path of a directory to retrieve subdirectories from
	Returns:
	- list of subdirectories
	"""
	result = []
	for element in glob.glob(os.path.join(dirpath, "*")):
		if os.path.isdir(element):
			result.append(element)
	return result

def get_action_string(index, total, action):
	"""
	creates an string zu display the current action
	Parameters:
	- index
	  index of the current action
	- total
	  total number of all actions
	- action
	  string to display an action
	Retueerns:
	- string to display the current action
	"""
	stringio = StringIO()
	stringio.write("[")
	stringio.write(str(index + 1))
	stringio.write("/")
	stringio.write(str(total))
	stringio.write("] ")
	stringio.write(action)
	stringio.write(" ...")
	return stringio.getvalue()

def syncronize(directory, output, recursive = False):
	"""
	synchronizes a directory
	Parameters:
	- directory
	  directory to synchronize
	- output
	  output instance to use
	- recursive
	  syncronize subdirectories recursively
	"""
	config = get_config()
	root = os.path.expanduser("~")
	local = SyncLocal(root)
	server = SyncServer(config, local, directory)
	processor = SyncProcessor(local, directory, server)
	encryptionflag = config.get_value(CONFIG_KEY_ENCRYPTION)
	if encryptionflag:
		if encryptionflag.lower().strip() == "true":
			synccrypt = SyncCrypt(False)
			synccrypt.enter_password(True)
			processor.set_encryption(synccrypt)
	output.output("Connecting server ...")
	processor.startup()
	output.output("Syncronizing %s ..." % directory)
	total = processor.get_action_count()
	if processor.needs_encryption():
		synccrypt = SyncCrypt(False)
		synccrypt.enter_password(false)
		processor.set_encryption(synccrypt)
	while processor.has_open_actions():
		index = processor.get_action_index()
		action = processor.get_action_title()
		output.output(get_action_string(index, total, action))
		processor.process_next_action()
		if server.has_errors():
			for error in server.get_errors():
				output.output("ERROR: " + error)
				server.clear_errors()
	if recursive:
		for subdir in get_subdirectories(directory):
			syncronize(subdir, output, True)
	output.output("Disconnecting ...")
	processor.shutdown()
	output.output("Done.")

def main():
	"""
	main function
	"""
	output = OutputConsole()
	output.output("simplesync %s" % get_version())
	config = get_config()
	directory = get_directory()
	recursive = get_parameter(PARAMETER_RECURSIVE) != None
	syncronize(directory, output, recursive)

if __name__ == "__main__":
	main()
