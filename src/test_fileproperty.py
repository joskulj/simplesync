#!/usr/bin/python

import unittest

from cStringIO import StringIO
from fileproperty import *

class FilePropertyTest(unittest.TestCase):

	def test_scan_tag(self):
		string = "<a>Test</a>"
		extract = scan_tag("a", string)
		self.assertEquals(extract, "Test")
		string = "<tag></tag>"
		extract = scan_tag("tag", string)
		self.assertEquals(extract, "")
		extract = scan_tag("c", "abcdef")
		self.assertEquals(extract, None)

	def test_scan(self):
		file_property = FileProperty()
		file_property.scan("./fileproperty.py")
		self.assertEquals(file_property.get_name(), "fileproperty.py")

	def test_get_property(self):
		file_property = FileProperty()
		property_string = file_property.get_property_string()
		flag = property_string.startswith("<fileproperty>")
		self.assertEquals(flag, True)
		flag = property_string.endswith("</fileproperty>")
		self.assertEquals(flag, True)

	def test_set_property(self):
		stringio = StringIO()
		stringio.write("<fileproperty>")
		stringio.write("<name>file.txt</name>")
		stringio.write("<path>/home/jochen/file.txt</path>")
		stringio.write("<timestamp>1242.99</timestamp>")
		stringio.write("</fileproperty>")
		property_string = stringio.getvalue()
		file_property = FileProperty()
		file_property.set_property_string(property_string)
		name = file_property.get_name()
		path = file_property.get_path()
		timestamp = file_property.get_timestamp()
		self.assertEquals(name, "file.txt")
		self.assertEquals(path, "/home/jochen/file.txt")
		self.assertEquals(timestamp, 1242.99)

if __name__ == "__main__":
	unittest.main()

