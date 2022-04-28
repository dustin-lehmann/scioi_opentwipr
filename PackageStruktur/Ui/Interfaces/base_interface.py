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
from Communication.core_messages import BaseMessage
# ---------------------------------------------------------------------------


class BaseInterface:
    # -------------------------------------------------------Signals----------------------------------------------------
    # send a message that already consists of bytes directly to the selected clients
    send_byte_message_signal = pyqtSignal(int, BaseMessage)

    # Send a Signal, if there has been a G-Code input by the User
    user_gcode_input_signal = pyqtSignal(str)