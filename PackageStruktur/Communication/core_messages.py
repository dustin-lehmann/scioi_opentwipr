#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: 26/04/22
# version ='1.0'
# ---------------------------------------------------------------------------
""" This module provides all the messages that are used for communication  """
# ---------------------------------------------------------------------------
# Module Imports
from ctypes import c_int8, c_uint8, c_float, c_bool
from _ctypes import Structure
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


class BaseMessage:
    """
        Base Class for every Message
    """
    ID0: int = 0
    ID1: int = 0
    ID2: int = 0
    raw_data: bytes = 0
    crc8: int

# -------------------------------------------------------Write messages-------------------------------------------------


class WriteMessage(BaseMessage):
    """
    Base Class for every Write Message
    """
    ID0 = 1
    ID1 = 0
    ID2 = 0


class SetLEDMessage(WriteMessage):
    """
    Message to set the LED

    Byte	|Type	|Name		|Description
    0		|uint8	|led_num	| Id of the led (1 or 2)
    1		|int8	|state		| 0: off, 1: on, -1: toggle
    """
    ID2 = 1

    class MsgStructure(Structure):
        _pack_ = 1
        _fields_ = [("led_id", c_uint8), ("led_state", c_int8)]

    def __init__(self, led_id: c_uint8, led_state: c_int8):
        super().__init__()
        self.data = self.MsgStructure(led_id, led_state)
        self.raw_data = bytes(self.data)


class SetMotorMessage(WriteMessage):
    """
    Message to set the Motor of the tank robots, sets both Motors at once for now

    Byte	|Type	|Name		|Description
    0		|bool	|dir_left	| Direction of left motor (0 forward, 1 backwards)
    1-4		|float	|speed_left	|
    5		|bool	|dir_right	| Direction of right motor (0 forward, 1 backwards)
    6-9		|float	|speed_left	|
    """
    ID2 = 2

    class MsgStructure(Structure):
        _pack_ = 1
        _fields_ = [("dir_left", bool), ("speed_left", c_float*4),("dir_right", bool) ("speed_right", c_float*4)]

    def __init__(self, dir_left: c_bool, speed_left: c_float*4, dir_right: c_int8, speed_right: c_float*4 ):
        super().__init__()
        self.data = self.MsgStructure(dir_left, speed_left, dir_right, speed_right)
        self.raw_data = bytes(self.data)


class DebugMessage(WriteMessage):
    """
    Message to use for debugging

    Byte	|Type	|Name		|Description
    0-9		|uint8	|val 1- val10	| List of integers that can be used for debugging
    """
    ID2 = 2

    class MsgStructure(Structure):
        _pack_ = 1
        _fields_ = [("val", c_uint8*10)]

    def __init__(self, val1: c_uint8, val2: c_uint8, val3: c_uint8, val4: c_uint8, val5: c_uint8,val6: c_uint8,
                 val7: c_uint8,val8: c_uint8,val9: c_uint8, val10: c_uint8 ):
        super().__init__()
        self.data = self.MsgStructure(val1, val2, val3, val4, val5, val6, val7, val8, val9, val10)
        self.raw_data = bytes(self.data)



if __name__ == "__main__":
    LED = SetLEDMessage(1, -1)
    Motor = SetMotorMessage(0,1.0,1,1.0)
    DebugMessage = DebugMessage(0,1,2,3,4,5,6,7,8,9)
