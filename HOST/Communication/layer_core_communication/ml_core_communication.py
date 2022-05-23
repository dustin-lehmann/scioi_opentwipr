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
from Communication.layer_core_communication import core_messages


def ml_tx_handling(pl_ml_tx_queue: Queue(), msg: core_messages.BaseMessage):
    """
    - Routine for checking putting messages into the tx queue
    - put a message into the tx queue for the next layer
    :param msg: msg to be sent
    :param pl_ml_tx_queue: queue that connects to the next layer
    :return: nothing
    """
    # check if there is anything in queue to transmit
    pl_ml_tx_queue.put_nowait(msg)


def ml_rx_handling(rx_queue: Queue()):
    """
    - Routine for checking the rx queue, if size is not 0, do sth
    :param rx_queue: rx queue harware-/protocol-layer
    :param pl_ml_rx_queue: rx queue protocol-/ message-layer
    :return: nothing
    """
    while rx_queue.qsize() > 0:
        rx_queue.get_nowait()
        print("raw message received")
