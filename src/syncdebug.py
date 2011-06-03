# simplesync - debugging functions
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

import os
import os.path
import sys

from cStringIO import StringIO

DEBUG_LEVEL_INFO = "INFO"
DEBUG_LEVEL_ERROR = "ERROR"

debug_flag = None
error_flag = None

def get_log_filename():
    """
    Returns:
    - full path of the log file
    """
    return os.path.join(os.getcwd(), "ssync.log")

def delete_log_file():
    """
    deletes previous log file
    """
    fname = get_log_filename()
    try:
        os.remove(fname)
    except:
        message = "Unable to delete: " + fname
        sys.stderr.write(message + "\n")

def open_log_file():
    """
    opens log file
    Returns:
    - opened log file or None
    """
    global error_flag
    fd = None
    try:
        fname = get_log_filename()
        fd = open(fname, "a")
    except:
        if error_flag == None:
            message = "Unable to open: " + get_log_filename()
            sys.stderr.write(message + "\n")
        error_flag = True
    return fd

def log_line(line, level=DEBUG_LEVEL_INFO):
    """
    logs a line
    Parameters:
    - line
      line to log
    - level
      debug level to use
    """
    logline = "[%s] %s\n" % (level, line)
    success = True
    fd = open_log_file()
    if fd != None:
        try:
            fd.write(logline)
            fd.close()
            success = True
        except:
            success = False
    else:
        success = False
    if success == False:
        sys.stderr.write(line)

def get_debug_flag():
    """
    determines if debugging is switched on
    Returns:
    - True:  debugging switched on
    - False: debugging switched off
    """
    global debug_flag
    if debug_flag == None:
        debug_flag = False
        for arg in sys.argv:
            if arg == "--debug":
                delete_log_file()
                debug_flag = True
    return debug_flag

def debug(line):
    """
    debugs a line
    Parameters:
    - line
      line to debug
    """
    if get_debug_flag():
        log_line(line)

def debug_error(line):
    """
    debugs a line at error level
    Parameters:
    - line
      line to debug
    """
    if get_debug_flag():
        log_line(line, DEBUG_LEVEL_ERROR)

def debug_value(label, value):
    """
    debugs a value
    - label
      label for a value
    - value
      value to log
    """
    if get_debug_flag():
        stringio = StringIO()
        stringio.write(label)
        if value:
            stringio.write(" = ")
            stringio.write(str(value))
        else:
            stringio.write(" = (None)")
        log_line(stringio.getvalue())
