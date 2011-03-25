#!/usr/bin/python

import unittest

from localproperty import *

class LocalPropertyTest(unittest.TestCase):

	def test_check_directory(self):
		flag = check_directory("/home/joskulj")
		self.assertEquals(flag, True)
		flag = check_directory("/home/annahaeschen")
		self.assertEquals(flag, False)

	def test_read_directory(self):
		reader = LocalPropertyReader("/home/joskulj")
		reader.read_directory("/home/joskulj/src/simplesync/src")
		for p in reader.get_properties():
			print p.get_name() + ": " + p.get_state() 
			if p.get_current():
				l = len(p.get_current().get_property_string())
				self.assertEquals(l > 0, True)
		reader.save_meta()

if __name__ == "__main__":
	unittest.main()

