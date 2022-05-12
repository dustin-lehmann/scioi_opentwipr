#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
""" This Module contains the base interface class that provides all the essential Signals for an Interface """
# ---------------------------------------------------------------------------
# Module Imports
from PyQt5.QtCore import pyqtSignal
# ---------------------------------------------------------------------------
# Imports
from Communication.core_communication.core_messages import BaseMessage  # todo: import needed here?


# ---------------------------------------------------------------------------


class BaseInterface:
    """
    this class is used to enable every interface class to use same basic signals that are necessary to communicate with
    and control the HostServer
    """
    # -------------------------------------------------------Signals----------------------------------------------------
    # send a message that already consists of bytes directly to the selected clients
    send_byte_message_signal = pyqtSignal(int, BaseMessage)  # todo: still needed? use in subclasses

    # Send a Signal, if there has been a G-Code input by the User
    user_gcode_input_signal = pyqtSignal(str)

    # Signal only used for testing todo: delete once everything is properly working
    test_signal = pyqtSignal(int, BaseMessage)

    def new_client_accepted(self):
        pass
