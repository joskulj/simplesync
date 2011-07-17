#!/usr/bin/env python

# simplesync - sycncronization daemon
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
import socket
import sys
import time

from threading import Thread

# state of the server
STATE_NOT_STARTED = 0
STATE_RUNNING = 1
STATE_STOPPING = 2
STATE_PAUSING = 3

# commands
COMMAND_START = "start"
COMMAND_STOP = "stop"
COMMAND_PAUSE = "pause"
COMMAND_CONTINUE = "continue"

COMMAND_LIST = [ COMMAND_START, COMMAND_STOP, COMMAND_PAUSE, COMMAND_CONTINUE ]

class DaemonSyncThread(object):
    """
    thread to syncronize the files
    """

    def __init__(self):
        """
        creates an instance
        """
        self._state = STATE_NOT_STARTED
        self._sleep_interval = 10

    def is_running(self):
        """
        Returns:
        - True:  server is running
        - False: server is not running
        """
        return self._state != STATE_STOPPING

    def stop(self):
        """
        signals the thread to stop
        """
        self._state = STATE_STOPPING

    def start_pausing(self):
        """
        signals the thread to pause
        """
        self._state = STATE_PAUSING

    def stop_pausing(self):
        """
        signals the thread to stop pausing
        """
        self._state = STATE_RUNNING

    def start(self):
        """
        starts the thread
        """
        self._state = STATE_RUNNING
        while self.is_running():
            print "loop entered."
            if self._state == STATE_RUNNING:
                print "SyncThread running."
            if self._state == STATE_PAUSING:
                print "SyncThread paused."
            print "sleep"
            time.sleep(self._sleep_interval)
            print "wake up"
        print "SyncThread stopped."
        #if self._state == STATE_NOT_STARTED:
        #    self._state = STATE_RUNNING
        #    if self._state != STATE_STOPPING:
        #        # TODO: implement file synchronization
        #        if self._state == STATE_RUNNING:
        #            print "DaemonSyncThread running"
        #        if self._state == STATE_PAUSING:
        #            print "DaemonSyncThread paused"
        #        # time.sleep(self._sleep_interval)
        #    print "SyncThread stopped."

class DaemonListenerThread(Thread):

    def __init__(self, sync_thread, port):
        """
        create instance
        Parameters:
        - sync_thread
          sync thread to control
        - port
          port to communicate with the client
        """
        Thread.__init__(self)
        self._sync_thread = sync_thread
        self._socket = self.init_socket(port)

    def init_socket(self, port):
        """
        initializes the socket to communicate with the client
        Parameters:
        - port
          port to use
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(("", port))
        return server_socket

    def run(self):
        """
        starts the thread
        """
        print "DaemonListenerThread started."
        flag = True
        while flag:
            print "Read socket"
            data, address = self._socket.recvfrom(256)
            print "DaemonListenerThread received: " + data
            if data == COMMAND_STOP:
                self._sync_thread.stop()
                flag = False
            time.sleep(2)
        #if data in COMMAND_LIST:
        #    if data == COMMAND_PAUSE:
        #        self._sync_thread.start_pausing()
        #    if data == COMMAND_CONTINUE:
        #        self._sync_thread.stop_pausing()
        #    if data == COMMAND_STOP:
        #         self._sync_thread.stop()
        #         flag = False
        #else:
        #    print "unknown command received"
        print "DaemonListenerThread stopped."

class DaemonClient(object):
    """
    client to communicate with the listener thread
    """

    def __init__(self, port):
        """
        create instance
        Parameters:
        - port
          port to use
        """
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        """
        sends data to the server
        Parameters:
        - data
          data to send
        """
        self._socket.sendto(data, ("localhost", self._port))

    def stop(self):
        """
        signals the server to stop
        """
        self.send(COMMAND_STOP)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Parameter missing."
    else:
        gtk.gdk.threads_init
        if not sys.argv[1] in COMMAND_LIST:
            print "Unknown parameter: %s." % sys.argv[1]
        else:
            if sys.argv[1] == COMMAND_START:
                sync_thread = DaemonSyncThread()
                listener_thread = DaemonListenerThread(sync_thread, 5000)
                listener_thread.start()
                sync_thread.start()
            if sys.argv[1] == COMMAND_STOP:
                client = DaemonClient(5000)
                client.stop()
            if sys.argv[1] == COMMAND_START:
                pass
            if sys.argv[1] == COMMAND_START:
                pass
