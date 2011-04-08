#!/usr/bin/env python

# simplesync-gtk - SimpleSync GTK application
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

import dis
import gtk
import gtk.glade
import pygtk
import time

from threading import Thread

from localproperty import *
from syncconfig import *
from synccrypt import *
from syncserver import *
from syncprocessor import *

class MainWindow:
    """
    implements the main window of the application
    """

    def __init__(self):
        """
        creates an instance
        """
        self._config_list = SyncConfigList()
        self._widget_tree = self.init_widget_tree()
        self._directory_model = self.init_directory_model()
        self._connection_model = self.init_connection_model()

    def init_widget_tree(self):
        """
        initializes the widget tree
        Returns:
        - created widget tree
        """
        gladefile = "simplesync.glade"
        windowname = "mainwindow"
        widget_tree = gtk.glade.XML(gladefile, windowname) 
        dic = {"on_mainwindow_destroy" : self.on_exit
                , "on_add_directory" : self.on_add_directory
                , "on_remove_directory" : self.on_remove_directory
                , "on_synchronize" : self.on_synchronize
                , "on_exit" : self.on_exit }
        widget_tree.signal_autoconnect(dic)
        mainwindow = widget_tree.get_widget(windowname)
        mainwindow.set_size_request(400, 400)
        return widget_tree

    def init_directory_model(self):
        """
        initializes the model for the directories
        Returns:
        - created model for the directories
        """
        view = self._widget_tree.get_widget("treeview_directories")
        # creates a column
        column = gtk.TreeViewColumn("Directory:", gtk.CellRendererText(), text=0)
        column.set_resizable(True)      
        column.set_sort_column_id(0)
        view.append_column(column)
        # creates the model
        model = gtk.ListStore(str)
        for directory in self._config_list.get_directories():
            model.append([directory])
        view.set_model(model)
        return model

    def init_connection_model(self):
        """
        initializes the model for connections
        Returns:
        - created model for connections
        """
        view = self._widget_tree.get_widget("combobox_connections")
        model = gtk.ListStore(str)
        view.set_model(model)
        cell_renderer = gtk.CellRendererText()
        view.pack_start(cell_renderer)
        view.add_attribute(cell_renderer, 'text', 0) 
        entry_available = False
        for entry in self._config_list.get_entries():
            model.append([entry.get_name()])
            entry_available = True
        if entry_available:
            view.set_active(0)
        return model

    def get_directories(self):
        """
        Returns:
        -- list of all directories
        """
        result = []
        model = self._directory_model
        iterator = model.get_iter_first()
        while iterator:
            value = model.get_value(iterator, 0)
            result.append(value)
            iterator = model.iter_next(iterator)
        return result

    def get_config(self):
        """
        Returns:
        - selected configuration to use
        """
        widget = self._widget_tree.get_widget("combobox_connections")
        model = widget.get_model()
        iterator = widget.get_active_iter()
        config_name = model.get_value(iterator, 0)
        return self._config_list.get_entry(config_name)

    def on_add_directory(self, widget):
        """
        handles the event to add a directory
        Parameters:
        - widget
          widget that triggered the event
        """
        diag = gtk.FileChooserDialog('Select directory',
                                    action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                    buttons=(gtk.STOCK_CANCEL,
                                             gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        res = diag.run()
        fname = diag.get_filename()
        diag.destroy()
        if res == gtk.RESPONSE_OK:
            self._directory_model.append([fname])

    def on_remove_directory(self, widget):
        """
        handles the event to remove a directory
        Parameters:
        - widget
          widget that triggered the event
        """
        widget = self._widget_tree.get_widget("treeview_directories")
        selection = widget.get_selection()
        [model, iterator] = selection.get_selected()
        if iterator:
            position = selection.get_selected_rows()
            value = model.get_value(iterator, 0)
            item = self._directory_model.remove(iterator)

    def on_synchronize(self, widget):
        """
        handles the event to syncronize the files
        Parameters:
        - widget
          widget that triggered the event
        """
        dialog = ProgressDialog(self.get_directories(), self.get_config())
        dialog.run()

    def on_exit(self, widget):
        """
        handles the event to exit the application
        Parameters:
        - widget
          widget that triggered the event
        """
        self._config_list.clear_directories()
        for directory in self.get_directories():
            self._config_list.add_directory(directory)
        self._config_list.save()
        gtk.main_quit() 

class ProgressDialog:
    """
    implements the dialog to show the progress of synchronization
    """

    def __init__(self, dirlist, config):
        """
        creates an instance
        Parameters:
        - dirlist
          lists of directories to synchronize
        """
        self._dirlist = dirlist
        self._config = config
        self._widget_tree = self.init_widget_tree()
        self._stop_flag = False
        self._thread = None
        self._directories_count = len(self._dirlist)
        self._directories_current = 0
        self._files_count = 0
        self._files_current = 0

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
        self._thread = SyncThread(self)
        self._thread.start()
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
        print count
        text = ""
        if count > 0:
            text = text + "\n"
        text = text + line
        print text
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
        # TODO: implement synchronization
        root = os.path.expanduser("~")
        local = SyncLocal(root)
        server = SyncServer(config, local, directory)
        processor = SyncProcessor(local, directory, server)
        # TODO: implement crypting support
        # encryptionflag = config.get_value(CONFIG_KEY_ENCRYPTION)
        # if encryptionflag:
        # if encryptionflag.lower().strip() == "true":
        #     synccrypt = SyncCrypt(False)
        #     synccrypt.enter_password(True)
        #     processor.set_encryption(synccrypt)
        processor.startup()
        dlg.set_files_count(processor.get_action_count())
        # TODO: implement crypting support
        # if processor.needs_encryption():
        #     synccrypt = SyncCrypt(False)
        #     synccrypt.enter_password(false) 
        #     processor.set_encryption(synccrypt)
        while processor.has_open_actions():
            action = processor.get_action_title()
            dlg.set_file(action)
            processor.process_next_action()
            if server.has_errors():
                for error in server.get_errors():
                    # output.output("ERROR: " + error)
                    server.clear_errors()
            # if recursive:
            #     for subdir in get_subdirectories(directory):
            #         syncronize(subdir, output, True)
        processor.shutdown()

if __name__ == "__main__":
    gtk.gdk.threads_init()
    window = MainWindow()
    gtk.main()
