#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: 26/04/22
# version ='1.0'
# ---------------------------------------------------------------------------
""" This module provides all the core messages that are used for communication  """
# ---------------------------------------------------------------------------
# Module Imports
import sys
from ctypes import c_int8, c_uint8, c_float, c_bool
from _ctypes import Structure
import cobs.cobs as cobs
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# message IDs

# Add[0]
_WRITE_MSG_ID = 1
_READ_MSG_ID = 2

# Message specific Add[1]
_SET_LED_ID = 1
_SET_MOTOR_ID = 2
_DEBUG_MESSAGE_ID = 3

# Size of each message without the data-field (Header, Crc-8, ...)
BASE_MESSAGE_SIZE = 8


class BaseMessage:
    """
        Base Class for every Message
    """
    # header byte
    header: int = 0xAA
    # ID of the source
    src : int = 0   # todo: change later to -1
    # ID of recipient
    add0: int = -1
    # sub-ID -> specific inbox of device: Com-Module layer auf das es soll
    add1: int = -1
    # Type of the message read/ write
    cmd: int = 0    # todo
    # ID of the specific message -> id of message
    msg: int = 0   # todo
    # length of the data field
    len: int = 0    #todo
    # crc8 checksum of the data field
    crc8: int = 0 # todo
    # bytes of the data field
    data: bytearray(0)

# -------------------------------------------------------Write messages-------------------------------------------------


class WriteMessage(BaseMessage):
    """
    Base Class for every Write Message
    """

    # ID for write-messages
    add0 = _WRITE_MSG_ID

    def __init__(self):
        super().__init__()


class SetLEDMessage(WriteMessage):
    """
    Message to set the LED
    Datafield:
    Byte	|Type	|Name		|Description
    0		|uint8	|led_num	| Id of the led (1 or 2)
    1		|int8	|state		| 0: off, 1: on, -1: toggle
    """
    add1 = _SET_LED_ID

    class DatafieldStructure(Structure):
        _pack_ = 1
        _fields_ = [("led_id", c_uint8), ("led_state", c_int8)]

    def __init__(self, led_id: c_uint8, led_state: c_int8):
        super().__init__()
        self.data_struct = self.DatafieldStructure(led_id, led_state)
        self.data = bytes(self.data_struct)


class SetMotorMessage(WriteMessage):
    """
    Message to set the Motor of the tank robots, sets both Motors at once for now
    Datafield:
    Byte	|Type	|Name		|Description
    0		|bool	|dir_left	| Direction of left motor (0 forward, 1 backwards)
    1-4		|float	|speed_left	|
    5		|bool	|dir_right	| Direction of right motor (0 forward, 1 backwards)
    6-9		|float	|speed_left	|
    """
    add1 = _SET_MOTOR_ID

    class DatafieldStructure(Structure):
        _pack_ = 1
        _fields_ = [("dir_left", c_bool), ("speed_left", c_float),("dir_right", c_bool), ("speed_right", c_float)]

    def __init__(self, dir_left: c_bool, speed_left: c_float, dir_right: c_int8, speed_right: c_float ):
        super().__init__()
        self.data_struct = self.DatafieldStructure(dir_left, speed_left, dir_right, speed_right)
        self.data = bytes(self.data_struct)


class DebugMessage(WriteMessage):
    """
    Message to use for debugging
    Datafield:
    Byte	|Type	|Name		| Description
    0		|uint8	|val1		| List of integers that can be used for debugging
    1		|uint8	|val2		|
    2		|uint8	|val3		|
    3		|uint8	|val4		|
    4		|uint8	|val5		|
    5		|uint8	|val6		|
    6		|uint8	|val7		|
    7		|uint8	|val8		|
    8		|uint8	|val9		|
    9		|uint8	|val10		|
    """
    add1 = _DEBUG_MESSAGE_ID

    class DatafieldStructure(Structure):
        _pack_ = 1
        _fields_ = [("val1", c_uint8),("val2", c_uint8),("val3", c_uint8),("val4", c_uint8),("val5", c_uint8),
                    ("val6", c_uint8), ("val7", c_uint8), ("val8", c_uint8), ("val9", c_uint8), ("val10", c_uint8)]

    def __init__(self, val1: c_uint8, val2: c_uint8, val3: c_uint8, val4: c_uint8, val5: c_uint8,val6: c_uint8,
                 val7: c_uint8,val8: c_uint8,val9: c_uint8, val10: c_uint8 ):
        super().__init__()
        self.data_struct = self.DatafieldStructure(val1, val2, val3, val4, val5, val6, val7, val8, val9, val10)
        self.data = bytes(self.data_struct)


if __name__ == "__main__":
    msg = SetLEDMessage(1, 1)
    print("ende")
