#!/usr/bin/python

import unittest
import os.path
import shutil

from synccrypt import *

class TestHelper(object):

    def __init__(self):
        self._path = os.path.expanduser("~/tmp")
        self._charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self._charcount = len(self._charset)
        self._crypt = SyncCrypt()
        self._crypt.set_password("test")

    def get_char(self, index):
        charindex = index % self._charcount
        return self._charset[charindex:charindex + 1]

    def create_filename(self, index):
        pattern = "file-%i.txt"
        return pattern % index

    def create_file(self, fname, size):
        filepath = os.path.join(self._path, fname)
        fd = open(filepath, "w")
        for i in range(0, size):
            fd.write(self.get_char(i))
        fd.close()

    def encrypt_file(self, fname):
        filepath = os.path.join(self._path, fname)
        self._crypt.encrypt_file(filepath)

    def backup_file(self, fname):
        filepath = os.path.join(self._path, fname)
        shutil.move(filepath, filepath + ".backup")

    def decrypt_file(self, fname):
        filepath = os.path.join(self._path, fname)
        self._crypt.decrypt_file(filepath + ".encrypt")

    def check_file(self, fname, size):
        result = True
        filepath = os.path.join(self._path, fname)
        fd = open(filepath, "r")
        content = ""
        for line in fd.readlines():
            content = content + line
        fd.close()
        if len(content) != size:
            result = False
        for i in range(0, len(content) - 1):
            ch = content[i:i + 1]
            if ch != self.get_char(i):
                result = False
        return result

class SyncCryptTest(unittest.TestCase):

    def test_crypt(self):
        helper = TestHelper()
        for i in range(1, 2048):
            fname = helper.create_filename(i)
            helper.create_file(fname, i)
            helper.encrypt_file(fname)
            helper.backup_file(fname)
            helper.decrypt_file(fname)
            if not helper.check_file(fname, i):
                print "encryption of %i bytes failed." % i

if __name__ == "__main__":
    unittest.main()

