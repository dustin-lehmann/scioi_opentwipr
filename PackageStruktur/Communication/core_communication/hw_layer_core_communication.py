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


def hw_layer_process_data_rx(data, hw_rx_queue: Queue, cops_encode_rx=True):
    """
    process received data in form of bytes and put
    :param cops_encode_rx: if true -> data is encoded via cobs and has to be processed before put into queue
    :param data: data that is supposed to be put in a clients queue
    :param hw_rx_queue: queue that data is supposed to be put into
    :return: nothing
    """
    # if bytes are encoded by cops -> decode
    if cops_encode_rx:
        # chop data into separate bytes
        byte_list = hw_layer_chop_bytes_rx(data)
        for entry in byte_list:
            # put byte into rx queue
            entry = bytes(entry)
            x = cobs.decode(entry)
            x = list(x) #todo: find a way to not have list -> bytes -> back to list again
            hw_rx_queue.put_nowait(x)
    # if not encoded by cobs
    else:
        hw_rx_queue.put_nowait(data)


def hw_layer_chop_bytes_rx(bytestring, delimiter=0x00):
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


def hw_layer_put_bytes_in_queue_tx(bytestring: bytes, cobs_encode=True):
    """
    take in byte-string, encode and put in the outgoing queue to be sent
    :param bytestring: bytestring that is supposed to be sent later
    :param cobs_encode: if true -> encode data before sending
    :return: nothing
    """
    if cobs_encode:
        # encode via cobs
        bytestring = cobs.encode(bytestring)
        # add 0x00 byte, that signals the end of the message for the recipient
        bytestring = bytestring.__add__(b'\x00')
        return bytestring
    else:
        return bytestring
