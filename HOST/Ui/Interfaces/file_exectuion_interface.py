#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: 27/04/2022
# version ='1.0'
# ---------------------------------------------------------------------------
"""
This Module provides an alternative to interact with the HostServer instead of using a Terminal interface the commands
in the file are executed
"""
# ---------------------------------------------------------------------------
# Module Imports
# QCoreApplication since there is no UI needed
from PyQt5.QtWidgets import QWidget
from time import sleep
# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------
from Ui.Interfaces.base_interface import BaseInterface


class FileExecutionInterface(BaseInterface, QWidget):

    def __init__(self):
        super().__init__()
        self.test_number = 0
        self.client_index =0
        self.client_is_connected = False
        # my_message = SetLEDMessage(1, 1)
        # self.send_messages_to_host_server(my_message, 0)

    def send_messages_to_host_server(self, msg, client_index):
        """
        send each command you want to be executed as a message one by one to the host Server
        :param msg: msg to be sent
        :param client_index: index of client the message is meant for
        :return: nothing
        """
        while True:
            if self.client_is_connected:
                self.send_byte_message_signal.emit(client_index, msg)
                print("File is being executed")
            else:
                print("message can not be sent since no client is connected")
            sleep(1)

    def new_client_accepted(self):
        pass
