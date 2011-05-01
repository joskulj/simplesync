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

import gtk
import gtk.glade

from syncconfig import *
from synccrypt import *

from progressdlg import *
from passworddlg import *
 
class MainWindow(object):
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

    def init_crypt(self):
        """
        inits the crypt object
        Returns:
        - crypt object to use
        """
        result = None
        password = None
        config = self.get_config()
        if config:
            name = config.get_name()
            if crypt_map.has_key(name):
                result = crypt_map[name]
            else:
                if config.has_password():
                    check_flag = False
                    while not check_flag:
                        dlg = PasswordDialog(False)
                        if dlg.run():
                            password = dlg.get_password()
                            if config.check_password(password):
                                check_flag = True
                            else:
                                display_error("Password does not match!")
                        else:
                            password = None
                            check_flag = True
                else:
                    dlg = PasswordDialog(True)
                    if dlg.run():
                        password = dlg.get_password()
                        config.set_password(password)
            if password:
                result = SyncCrypt()
                result.set_password(password)
                crypt_map[name] = result
        return result

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

    def needs_password(self):
        """
        checks if a password is required
        Returns:
        - True:  password is required
        - False: no password required
        """
        result = False
        config = self.get_config()
        if config:
            result = config.get_value(CONFIG_KEY_ENCRYPTION)
        return result

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
        crypt = None
        if self.needs_password():
            crypt = self.init_crypt()
            if crypt:
                progress_dlg = ProgressDialog(self.get_directories(), self.get_config(), crypt)
                progress_dlg.run()
        else:
            progress_dlg = ProgressDialog(self.get_directories(), self.get_config(), crypt)
            progress_dlg.run()

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

if __name__ == "__main__":
    gtk.gdk.threads_init()
    window = MainWindow()
    gtk.main()

