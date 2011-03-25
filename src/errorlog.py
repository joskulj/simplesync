# simplesync - class to log errors
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

class ErrorLog(object):
	"""
	base class to manage occured errors
	"""

	def __init__(self):
		"""
		creates an instance
		"""
		self._errors = []

	def clear_errors(self):
		"""
		clears all errors
		"""
		self._errors = []

	def error(self, errormsg):
		"""
		reports an error
		Parameters:
		- errormsg
		  error message to log
		"""
		self._errors.append(errormsg)

	def has_errors(self):
		"""
		checks, if errors are logged 
		Returns:
		- True:  errors are logged
		- False: no errors are logged
		"""
		return len(self._errors) > 0

	def get_errors(self):
		"""
		Returns:
		- list of logged errors
		"""
		return self._errors
