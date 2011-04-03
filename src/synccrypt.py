## simplesync - cryptographic functions
#
# Copyright 2010 Jochen Skulj, jochen@jochenskulj.de
#
# Some of these cryptographic functions are taken from Eli Bendersky's
# website 
# http://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto/
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

import getpass
import random
import struct
import os.path

from Crypto.Cipher import AES

# Constants for copy modes
ENCRYPTION_EXTENSION = ".encrypt"

# helper functions for encryption and decryption

def normalize_key(key):
    """
    normalize a key to a valid length
    - key
      key to normalize
    Returns:
    - normalized keys
    """
    result = key
    targetlength = 16
    if len(key) > 16:
        targetlength = 24
    if len(key) > 24:
        targetlength = 32
    part = key
    while len(result) < targetlength:
        part = part[::-1]
        result = result + part
    return result[:targetlength]

def split_line(line, length):
    """
    splits a line into several substrings with a given
    length
    Parameters:
    - line
      line to split into substrings
    - length
      length of each substring
    Returns:
    - list of substrings
    """
    result = []
    pos = 0
    while pos + length < len(line):
        part = line[pos:pos + length]
        result.append(part)
        pos = pos + length
    if pos < len(line):
        result.append(line[pos:])
    return result

def encrypt_file(srcfilename, destfilename, key, chunksize=64*1024):
    """ 
    encrypts a file using AES with a given key
    Parameters:
    - srcfilename
      name of the file to encrypt
    - destfilename
      name of the destination file
    - key
      encryption key. The encryption key must be 16, 24 or 32
      bytes long.
    - chunksize
      size of the chunks to read and encrypt the file
    """
    rlist = []
    for i in range(16):
        rlist.append(chr(random.randint(0, 255)))
    iv = "".join(rlist)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(srcfilename)
    srcfile = open(srcfilename, "rb")
    destfile = open(destfilename, "wb")
    destfile.write(struct.pack('<Q', filesize))
    destfile.write(iv)
    while True:
        chunk = srcfile.read(chunksize)
        if len(chunk) == 0:
            break
        elif len(chunk) % 16 != 0:
            chunk += ' ' * (16 - len(chunk) % 16)
            destfile.write(encryptor.encrypt(chunk))
    srcfile.close()
    destfile.close()

def decrypt_file(srcfilename, destfilename, key, chunksize=64*1024):
    """
    decrypt a file using AES with a given key
    Parameters:
    - srcfilename
      name of the file to decrypt
    - destfilename
      name of the destination file
    - key
      encryption key. The encryption key must be 16, 24 or 32
      bytes long.
    - chunksize
      size of the chunks to read and encrypt the file
    """
    srcfile = open(srcfilename, "rb")
    origsize = struct.unpack('<Q', srcfile.read(struct.calcsize('Q')))[0]
    iv = srcfile.read(16)
    decryptor = AES.new(key, AES.MODE_CBC, iv)
    destfile = open(destfilename, "wb")
    while True:
        chunk = srcfile.read(chunksize)
        if len(chunk) == 0:
            break
        destfile.write(decryptor.decrypt(chunk))
    destfile.truncate(origsize)
    srcfile.close()
    destfile.close()

class SyncCrypt(object):
    """
    class to handle encryption and decryption
    """

    def __init__(self, guiflag = False):
        """
        creates an instance
        Parameters:
        - guiflag
          determines if a GUI is used for user input
        """
        self._guiflag = guiflag
        self._key = None

    def get_decrypted_filename(self, filename):
        """
        returns the filename of an decrypted file
        Parameters:
        - filename
          filename of an encrypted file
        Returns:
        - name of an decrypted file
        """
        flen = len(filename)
        elen = len(ENCRYPTION_EXTENSION)
        return filename[0:flen - elen]

    def enter_password(self, repeat=False):
        """
        prompts the user to enter a password
        Parameters:
        - repeat
          prompts to repeat the password
        """
        if guiflag:
            # TODO: implement GUI
        else:
            if repeat:
                while True:
                    key1 = getpass.getpass("Enter password: ")
                    key2 = getpass.getpass("Repeat password: ")
                    if key1 == key2:
                        self._key = key1
                        break
                    else:
                        print "Entered password don't match."
            else:
                self._key = getpass.getpass("Enter password: ")

    def encrypt_file(self, filename):
        """
        encrypts a file
        Parameters:
        - filename
          name of the file to encrypt. The encrypted filename gets
          the suffix ».encrypt«
        Returns:
        - name of the encrypted file
        """
        destfilename = filename + ENCRYPTION_EXTENSION
        if not self._key:
            self.enter_password(True)
        encrypt_file(filename, destfilename, self._key)
        return destfilename

    def decrypt_file(self, filename):
        """
        decrypts a file
        Parameters:
        - filename
          name of the file to decrypt. The filemane has to be end
          with the suffix ».encrypt«
        Returns:
        - name of the decrypted files
        """
        flen = len(filename)
        elen = len(ENCRYPTION_EXTENSION)
        destfilename = self.get_decrypted_filename(filename)
        if not self._key:
            self.enter_password()
        decrypt_file(filename, destfilename, self._key)
        return destfilename
