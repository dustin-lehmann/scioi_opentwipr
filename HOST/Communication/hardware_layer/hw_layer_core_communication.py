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
from PyQt5.QtNetwork import QTcpSocket


# ---------------------------------------------------------------------------


def hw_layer_process_data_rx(data, cops_encode_rx=True):
    """
    process received data in form of bytes and put
    :param cops_encode_rx: if true -> data is encoded via cobs and has to be processed before put into queue
    :param data: data that is supposed to be put in a clients queue
    :return: decoded list
    """
    # chop data into separate bytes
    byte_list = _hw_layer_chop_bytes_rx(data)
    # every entry is a separate message ->
    for index in range(len(byte_list)):
        # check seconde byte (= Header after cobs encoding), if true-> normal message
        if byte_list[index][1] == 0xAA:
            # if bytes are encoded by cops -> decode
            if cops_encode_rx:
                # list to store decoded messages in
                decoded_list = []
                # put byte into rx queue
                entry = bytes(byte_list[index])
                # decode given bytes and add the message to the list
                decoded_list.append(list(cobs.decode(entry)))
                return decoded_list
            # if not encoded by cobs
            else:
                return byte_list  # todo: depending on how the end of messages are defined choose new method to process

        elif byte_list[index][0] == 0xBB:
            print("JSON-encoding detected")  # todo: implement json-handling!

        else:
            print("header of byte is not valid message is not going to be processed!")


def _hw_layer_chop_bytes_rx(bytestring, delimiter=0x00):
    """
    - chop input-bytes into separate message bytes
    - check if received bytes are predefined message or json file and based on that choose further handling of msg
    - if msg: chop the by cobs encoded byte-strings into separate messages, return an array of integers
    - if json: for now: pass
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


def hl_tx_handling(tx_queue: Queue(), socket: QTcpSocket):
    # check if there is any data in queue waiting to be sent
    while tx_queue.qsize() > 0:
        # write data from queue in socket
        socket.write(tx_queue.get_nowait())
        # send the data by using flush
        socket.flush()
