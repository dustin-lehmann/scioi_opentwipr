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
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget

import sys
# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------
from Communication.core_messages import SetLEDMessage, SetMotorMessage, DebugMessage, BaseMessage
from Ui.Interfaces.base_interface import BaseInterface


class FileExecutionInterface(BaseInterface, QWidget):

    def __init__(self):
        super().__init__()
        self.test_number = 0
        self.client_index =0
        self.execute_commands()

    def send_messages_to_host_server(self, msg, client_index):
        """
        send each command you want to be executed as a message one by one to the host Server
        :param msg: msg to be sent
        :param client_index: index of client the message is meant for
        :return:
        """
        self.send_byte_message_signal.emit(client_index, msg)
        print("File is being executed")

    def execute_commands(self):
        """
        store all commands here thar are supposed to be sent to the host_server #todo: function is only temporary
        :return:
        """
        my_message = SetLEDMessage(1, 1)
        self.send_messages_to_host_server(my_message, 0)




def main():
    # pass sys.arg to allow command line arguments
    print("2")
    app = QCoreApplication(sys.argv)

    my_message = SetLEDMessage(1, 1)
    file_execution_interface = FileExecutionInterface()
    file_execution_interface.send_messages_to_host_server(file_execution_interface.client_index, my_message)

    print("3")
    sys.exit(app.exec())


if __name__ == "__main__":
    print("1")
    main()

