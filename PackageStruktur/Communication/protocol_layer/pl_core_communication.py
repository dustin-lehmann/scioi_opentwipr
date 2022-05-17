#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
"""
this module contains the functions used for protocol_layer_core communication
"""
# ---------------------------------------------------------------------------
# Module Imports 
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------
from queue import Queue
from Communication.core_communication.core_messages import BASE_MESSAGE_SIZE
from cobs import cobs as cobs
from dataclasses import dataclass


@dataclass(frozen=True)
class MsgProtocol:
    """
    the MsgProtocol class is responsible for the structure of messages by determining the position of each byte
    """
    HEADER_POS: int = 0
    SRC_POS: int = 1
    ADD_0_POS: int = 2
    ADD_1_POS: int = 3
    CMD_POS: int = 4
    MSG_POS: int = 5
    LEN_POS: int = 6
    CRC8_POS: int = 7
    DATA_START_POS: int = 8


class RawMessage:
    """
    creates a RawMessage from input bytes that can then be interpreted from the hw-layer
    """
    def __init__(self, byte_list: list):
        length = len(byte_list)
        self.header = byte_list[MsgProtocol.HEADER_POS]
        self.src = byte_list[MsgProtocol.SRC_POS]
        self.add0 = byte_list[MsgProtocol.ADD_0_POS]
        self.add1 = byte_list[MsgProtocol.ADD_1_POS]
        self.cmd = byte_list[MsgProtocol.CMD_POS]
        self.len = byte_list[MsgProtocol.LEN_POS]
        self.crc8 = byte_list[MsgProtocol.CRC8_POS]
        self.data = byte_list[MsgProtocol.DATA_START_POS:length - 1]


def pl_create_raw_msg_rx(bytes_msg: list):
    """
    create from a list of bytes a raw message that can be interpreted later
    :param bytes_msg: list of bytes to create message from
    :return: nothing
    """
    raw_message = RawMessage(bytes_msg)
    return raw_message


def pl_translate_msg_tx(msg):
    """
    - this message builder creates a buffer from a given Message so it can be sent
    - Note this is a temporary test version to test the function and is based on the function implemented by Dennis
        (general.py, message_builder())
    :param msg: msg that is supposed to be translated
    :return: translated message as bytearray
    """
    # determine the size of data
    payload_size = len(msg.raw_data)
    # length of complete message
    msg_length = BASE_MESSAGE_SIZE + payload_size
    buffer = bytearray(msg_length)

    buffer[MsgProtocol.HEADER_POS] = msg.header
    buffer[MsgProtocol.SRC_POS] = msg.src
    buffer[MsgProtocol.ADD_0_POS] = msg.add0
    buffer[MsgProtocol.ADD_1_POS] = msg.add1
    buffer[MsgProtocol.CMD_POS] = msg.cmd
    buffer[MsgProtocol.MSG_POS] = msg.msg
    buffer[MsgProtocol.LEN_POS] = msg.len
    buffer[MsgProtocol.CRC8_POS] = msg.crc8
    buffer[MsgProtocol.DATA_START_POS:msg_length] = msg.data

    return buffer
