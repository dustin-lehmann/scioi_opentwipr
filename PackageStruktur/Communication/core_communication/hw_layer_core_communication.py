#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: 12/05/22
# version ='1.0'
# ---------------------------------------------------------------------------
"""
this module contains the functions used for hw_layer_core communication
"""
# ---------------------------------------------------------------------------
# Module Imports
import cobs.cobs as cobs
from queue import Queue


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------


def hw_layer_process_rx(data, rx_queue: Queue, cops_encode_rx=True):
    """
    process received data in form of bytes and put
    :param cops_encode_rx: if true -> data is encoded via cobs and has to be processed before put into queue
    :param data: data that is supposed to be be put in a clients queue
    :param rx_queue: queue that data is supposed to be put into
    :return: nothing
    """
    # if bytes are encoded by cops -> decode
    if cops_encode_rx:
        # chop data into seperate bytes
        byte_list = hw_layer_chop_bytes(data)
        for entry in byte_list:
            # put byte into rx queue
            entry = bytes(entry)
            x = cobs.decode(entry)
            rx_queue.put_nowait(x)
    # if not encoded by cobs
    else:
        rx_queue.put_nowait(data)


def hw_layer_chop_bytes(bytestring, delimiter=0x00):
    """
    chop the by cobs encoded byte-strings into separate messages, return an array of integers
    :param delimiter: delimiter that is used to separate each message
    :param bytestring: bytestring that is supposed to be chopped int separate messages
    :return: list, with separate messages as elements
    """
    # empty list to append the messages later on
    chopped_bytes = []
    # start position of each byte
    start_byte = 0

    # convert bytes into list
    data_list = list(bytestring)

    for x in range(len(data_list)):
        # check if the byte equals delimiter, if so -> end of byte
        if data_list[x] == delimiter:
            chopped_bytes.append(data_list[start_byte:x])
            # start of next byte is right after delimiter
            start_byte = x + 1

    return chopped_bytes


def hw_layer_translate_msg_tx(msg):
    """
    - this message builder creates a buffer from a given Message so it can be sent to the client(s)
    - Note this is a temporary test version to test the function and is based on the function implemented by Dennis
        (general.py, message_builder())!! todo: Once basic functionality is established the complete structure has to be created here (crc-8 check, etc.)
    - after the message has been translated to bytes it gets encoded via cobs, the host then has to decode later
    :param msg: msg that is supposed to be translated
    :return: translated message
    """
    # determine the size of data
    payload_size = len(msg.raw_data)
    # length of complete message
    # msg_length = BASE_MESSAGE_SIZE + payload_size
    msg_length = 3 + payload_size
    buffer = bytearray(msg_length)

    buffer[0] = msg.ID0
    buffer[1] = msg.ID1
    buffer[2] = msg.ID2
    buffer[3:3 + payload_size] = msg.raw_data

    # encode buffer via cobs
    buffer = cobs.encode(buffer)
    # add 0x00 byte, that signals the end of the message for the recipient
    buffer = buffer.__add__(b'\x00')

    return buffer
