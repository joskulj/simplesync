#!/usr/bin/env python

# progressdlg - SimpleSync Progress Dialog
#
# Copyright 2011 Jochen Skulj, jochen@jochenskulj.de
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

import gtk
import gtk.glade
import time

from threading import Thread

from syncserver import *
from syncprocessor import *

class ProgressDialog(object):
    """
    implements the dialog to show the progress of synchronization
    """

    def __init__(self, dirlist, config, crypt):
        """
        creates an instance
        Parameters:
        - dirlist
          lists of directories to synchronize
        - config
          config to use for synchronization
        - crypt
          crypt to use
        """
        self._dirlist = dirlist
        self._config = config
        self._crypt = crypt
        self._widget_tree = self.init_widget_tree()
        self._directories_count = len(self._dirlist)
        self._directories_current = 0
        self._files_count = 0
        self._files_current = 0
        self._stop_flag = False
        self._Thread = SyncThread(self)

    def init_widget_tree(self):
        """
        initializes the widget tree
        Returns:
        - created widget tree
        """
        gladefile = "simplesync.glade"
        windowname = "progressdialog"
        widget_tree = gtk.glade.XML(gladefile, windowname) 
        dic = { "on_button_action" : self.on_button_action,
                "on_progressdialog_destroy" : self.on_progressdialog_destroy }
        widget_tree.signal_autoconnect(dic)
        return widget_tree

    def get_directory_list(self):
        """
        Returns:
        - the list of directories
        """
        return self._dirlist

    def get_config(self):
        """
        Returns:
        - configuration to use
        """
        return self._config

    def get_crypt(self):
        """
        Returns:
        - crypt instance to use
        """
        return self._crypt

    def get_stop_flag(self):
        """
        Returns:
        - True:  stop synchronizing
        - False: continue synchronizing
        """
        return self._stop_flag

    def finished(self):
        """
        signals that the task is finished
        """
        self._stop_flag = True
        widget = self._widget_tree.get_widget("button")
        widget.set_label("_Close")

    def run(self):
        """
        runs the dialog
        """
        widget = self._widget_tree.get_widget("progressdialog")
        thread = SyncThread(self)
        thread.start()
        widget.run()

    def set_directories_count(self, count):
        """
        sets the total count of directories
        Parameters:
        - count
          total counts of directories
        """
        self._directories_count = count
        self._directories_current = 0

    def set_files_count(self, count):
        """
        sets the total count of files
        Parameters:
        - count
          total counts of files
        """
        self._files_count = count
        self._files_current = 0

    def set_directory(self, directory):
        """
        sets the directory
        Parameters:
        - directory
          directory to display
        """
        label = self._widget_tree.get_widget("label_directory")
        label.set_text(directory)
        self._directories_current = self._directories_current + 1
        progressbar = self._widget_tree.get_widget("progressbar_directory")
        fraction = float(self._directories_current) / float(self._directories_count)
        progressbar.set_fraction(fraction)

    def set_file(self, filename):
        """
        sets the file
        Parameters:
        - filename
          filename to display
        """
        label = self._widget_tree.get_widget("label_file")
        label.set_text(filename)
        self._files_current = self._files_current + 1
        progressbar = self._widget_tree.get_widget("progressbar_file")
        fraction = float(self._files_current) / float(self._files_count)
        progressbar.set_fraction(fraction)

    def add_detail_line(self, line):
        """
        adds a line to the detail field
        Parameters:
        - line
          line to add
        """
        widget = self._widget_tree.get_widget("textview_detail")
        buf = widget.get_buffer()
        count = buf.get_char_count()
        text = ""
        if count > 0:
            text = text + "\n"
        text = text + line
        iterator = buf.get_iter_at_offset(count)
        buf.insert(iterator, text)

    def on_button_action(self, widget):
        """
        handles a click on the button
        Parameters:
        - widget
          widget that triggered the event
        """
        if not self._stop_flag:
            self._stop_flag = True
        else:
            dlg = self._widget_tree.get_widget("progressdialog")
            dlg.destroy()

    def on_progressdialog_destroy(self, widget):
        """
        handles the destroy event
        Parameters:
        - widget
          widget that triggered the event
        """
        self._stop_flag = True
        time.sleep(0.5)

class SyncThread(Thread):
    """
    Thread class to syncronize the files
    """

    def __init__(self, progressdialog):
        """
        creates an instance
        Parameters:
        - progressdialog
          ProgressDialog that controls the thread
        """
        Thread.__init__(self)
        self._progressdialog = progressdialog

    def run(self):
        """
        runs the thread
        """
        dlg = self._progressdialog
        for entry in dlg.get_directory_list():
            dlg.set_directory(entry)
            self.synchronize(entry)
            time.sleep(0.3)
            if dlg.get_stop_flag():
                break
        dlg.finished()

    def synchronize(self, directory):
        """
        synchronizes a directory
        Parameters:
        - directory
          directory to synchronize
        """
        dlg = self._progressdialog
        config = dlg.get_config()
        root = os.path.expanduser("~")
        local = SyncLocal(root)
        server = SyncServer(config, local, directory)
        processor = SyncProcessor(local, directory, server)
        if dlg.get_crypt():
            processor.set_encryption(dlg.get_crypt(), True)
        processor.startup()
        dlg.set_files_count(processor.get_action_count())
        while processor.has_open_actions():
            action = processor.get_action_title()
            dlg.set_file(action)
            dlg.add_detail_line(action)
            processor.process_next_action()
            if server.has_errors():
                for error in server.get_errors():
                    detail_line = " ERROR: %s" % error
                    dlg.add_detail_line(detail_line)
                    server.clear_errors()
            # if recursive:
            #     for subdir in get_subdirectories(directory):
            #         syncronize(subdir, output, True)
        processor.shutdown()

