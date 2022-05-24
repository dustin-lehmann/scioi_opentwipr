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
from layer_core_communication.core_messages import BASE_MESSAGE_SIZE
from cobs import cobs as cobs
from dataclasses import dataclass
from typing import Union
import unittest

# valid range of message parameters
_HEADER_VALUE = [0xAA]
_SRC_RANGE = [0, 255]
_ADD0_RANGE = [0, 255]
_ADD1_RANGE = [0, 255]
_CMD_RANGE = [0, 255]


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


class _RawMessage:
    """
    creates a RawMessage from input bytes that can then be interpreted from the hw-layer
    """

    # todo: make it possible to not only create a message by byte-input -> directly setting params
    def __init__(self, byte_list: list):
        length = len(byte_list)
        self.header: int = byte_list[MsgProtocol.HEADER_POS]
        self.src: int = byte_list[MsgProtocol.SRC_POS]
        self.add0: int = byte_list[MsgProtocol.ADD_0_POS]
        self.add1: int = byte_list[MsgProtocol.ADD_1_POS]
        self.cmd: int = byte_list[MsgProtocol.CMD_POS]
        self.msg: int = byte_list[MsgProtocol.MSG_POS]
        self.len: int = byte_list[MsgProtocol.LEN_POS]
        self.crc8: int = byte_list[MsgProtocol.CRC8_POS]
        self.data: int = byte_list[MsgProtocol.DATA_START_POS:length - 1]


def pl_create_raw_msg_rx(bytes_msg: list):
    """
    create from a list of bytes a raw message that can be interpreted later
    :param bytes_msg: list of bytes to create message from
    :return: not
    """
    raw_message = _RawMessage(bytes_msg)
    if _check_raw_msg_rx(raw_message) is True:
        return raw_message
    else:
        pass  # todo


def _check_raw_msg_rx(msg: _RawMessage):
    """
    conduct message checks
    :param msg: message that is going to be validated
    :return: true -> message valid; false -> invalid message
    """
    # no need to check for json here
    if not msg.header == 0xAA:
        print("header corrupted")
        return False
    if not _SRC_RANGE[0] <= msg.src <= _SRC_RANGE[1]:
        print("SRC not in expected range, can not create raw_msg!")
        return False
    if not _ADD0_RANGE[0] <= msg.add0 <= _ADD0_RANGE[1]:
        print("ADD_0 not in expected range, can not create raw_msg!")
        return False
    if not _ADD1_RANGE[0] <= msg.add1 <= _ADD1_RANGE[1]:
        print("ADD1 not in expected range, can not create raw_msg!")
        return False
    if not _CMD_RANGE[0] <= msg.cmd <= _CMD_RANGE[1]:
        print("CMD not in expected range, can not create raw_msg!")
        return False
    # todo: len-check
    # if not msg.len == len(msg.data):  # todo: did I get this right? or should I just look for the overhead?
    #     print("length byte of message incorrect, can not create raw_msg!")
    # todo: crc8-check!
    return True


def pl_translate_msg_tx(msg, cobs_encode = False):
    """
    - this message builder creates a buffer from a given Message so it can be sent
    :param msg: msg that is supposed to be translated
    :return: translated message as bytearray
    """
    # determine the size of data
    payload_size = len(msg.data)
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
    buffer[MsgProtocol.DATA_START_POS:msg_length] = msg.data_struct

    if cobs_encode:
        buffer = cobs.encode(buffer)

    return buffer


def pl_tx_handling(pl_ml_tx_queue: Queue(), tx_queue: Queue()):
    """
    - Routine for checking the tx queue, if size is not 0, process msg from hl by translate it into a bytearray
    - loop through the clients and check if there are any data that is supposed to be sent
    :param pl_ml_tx_queue:
    :param tx_queue:
    :return: nothing
    """
    # check if there is anything in queue to transmit
    while pl_ml_tx_queue.qsize() > 0:
        # get data from pl_ml_tx_queue
        msg = pl_ml_tx_queue.get_nowait()
        # translate msg into bytes for hardware layer
        msg_bytearray = pl_translate_msg_tx(msg)
        tx_queue.put_nowait(msg_bytearray)


def pl_rx_handling(rx_queue: Queue(), pl_ml_rx_queue: Queue()):
    """
    - Routine for checking the rx queue, if size is not 0, create a raw message from bytes_msg
    - loop through the clients and check if there are any data that is supposed to be sent
    :param rx_queue:
    :param pl_ml_rx_queue:
    :return: nothing
    """

    while rx_queue.qsize() > 0:
        # get data from rx_queue
        bytes_msg = rx_queue.get_nowait()
        # create a new raw message from data bytes
        raw_message = pl_create_raw_msg_rx(bytes_msg)
        # put raw message in queue for message-layer
        pl_ml_rx_queue.put_nowait(raw_message)

