# Utility functions for Input/Output

import os.path

def check_directory(dirpath):
	"""
	checks if a directory exists
	Parameters:
	- dirpath
	  full path of the directory to check
	Returns:
	- True:  directory exists
	- False: directory doesn't exists
	"""
	result = True
	if not os.path.exists(dirpath):
		result = False
	if not os.path.isdir(dirpath):
		result = False
	return result

def check_file(filepath):
	"""
	checks if a file exists
	Parameters:
	- filepath
	  full path of the file to check
	Returns:
	- True:  file exists
	- False: file doesn't exists
	"""
	result = True
	if not os.path.exists(filepath):
		result = False
	if not os.path.isfile(fillepath):
		result = False
	return result

def open_file(path, filename, mode):
	"""
	opens a file specified by path and filename
	Parameters:
	- path
	  path of the file to open
	- filename
	  filename of the file to open
	- mode
	  mode for opening the file
	Returns:
	- open file or None if the file couldn't be opened
	"""
	result = None
	try:
		fname = os.path.join(path, filename)
		result = open(fname, mode)
	except IOError:
		result = None
	return result
