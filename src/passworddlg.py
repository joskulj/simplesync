#!/usr/bin/env python

# passworddlg - SimpleSync Password Dialog
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

CONFIG_KEY_ENCRYPTION = "encryption"

crypt_map = { }

def display_error(text):
    """
    displays an error
    Parameters:
    - text
      error text to display
    """
    error_dialog = gtk.MessageDialog(
        type=gtk.MESSAGE_ERROR, 
        buttons=gtk.BUTTONS_OK,
        message_format=text)
    error_dialog.run()
    error_dialog.destroy()
 
class PasswordDialog(object):
    """
    implements the dialog to ask for the password
    """

    def __init__(self, repeat_flag):
        """
        creates an instance
        Parameters:
        - repeat_flag
          flag if a repeat input of the password is required
        """
        self._repeat_flag = repeat_flag
        self._dialog = None
        self._password = None
        self._widget_tree = None
        self._label_heading = None
        self._label_password_2 = None
        self._entry_password_1 = None
        self._entry_password_2 = None
        self._running = False
        self_result = False
        self.init_widgets(repeat_flag)

    def init_widgets(self, repeat_flag):
        """
        initializes the widget tree
         Parameters:
        - repeat_flag
          flag if a repeat input of the password is required
        """
        gladefile = "simplesync.glade"
        windowname = "passworddialog"
        self._widget_tree = gtk.glade.XML(gladefile, windowname)
        self._dialog = self._widget_tree.get_widget("passworddialog")
        self._button_ok = self._widget_tree.get_widget("button_ok")
        self._label_heading = self._widget_tree.get_widget("label_heading")
        self._label_password_2 = self._widget_tree.get_widget("label_password_2")
        self._entry_password_1 = self._widget_tree.get_widget("entry_password_1")
        self._entry_password_1.set_visibility(False)
        self._entry_password_2 = self._widget_tree.get_widget("entry_password_2")
        self._entry_password_2.set_visibility(False)
        dic = { "on_button_ok_clicked" : self.on_button_ok_clicked,
                "on_button_cancel_clicked" : self.on_button_cancel_clicked,
                "on_entry_activate" : self.on_entry_activate }
        self._widget_tree.signal_autoconnect(dic)
        if not repeat_flag:
            self._label_heading.set_text("Please enter your Password!")
            self._entry_password_1.set_activates_default(True)
            self._label_password_2.set_visible(False)
            self._entry_password_2.set_visible(False)

    def get_password(self):
        """
        Returns:
        - the entered password
        """
        return self._password

    def run(self):
        """
        runs the dialog
        Returns:
        - True:  password successfully entered
        - False: dialog cancelled
        """
        widget = self._widget_tree.get_widget("passworddialog")
        self._running = True
        while self._running:
            widget.run()
        return self._result

    def on_entry_activate(self, widget):
        """
        handles the activate event
        - widget
          widget that triggered the event
        """
        if widget.get_name() == "entry_password_1":
            if not self._repeat_flag:
                self._button_ok.clicked()
            else:
                self._entry_password_2.grab_focus()
        else:
            self._button_ok.clicked()

    def on_button_ok_clicked(self, widget):
        """
        handles the click on the OK button
        Parameters:
        - widget
          widget that triggered the event
        """
        self._password = None
        password_1 = self._entry_password_1.get_text()
        password_2 = self._entry_password_2.get_text()
        if self._repeat_flag:
            if password_1 == password_2 and len(password_1) > 0:
                self._password = password_1
                self._result = True
                self._running = False
            else:
                if len(password_1) == 0 and len(password_2) == 0:
                    display_error("No password entered!")
                else:
                    display_error("Entered Passwords don\'t match!")
        else:
            if len(password_1) == 0:
                display_error("No password entered!")
            else:
                self._password = password_1
                self._result = True
                self._running = False
        if self._password:
            dlg = self._widget_tree.get_widget("passworddialog")
            dlg.destroy()

    def on_button_cancel_clicked(self, widget):
        """
        handles the click on the Cancel button
        Parameters:
        - widget that triggered the event
        """
        self._password = None
        self._result = False
        self._running = False
        dlg = self._widget_tree.get_widget("passworddialog")
        dlg.destroy()

if __name__ == "__main__":
    gtk.gdk.threads_init()
    window = MainWindow()
    gtk.main()
