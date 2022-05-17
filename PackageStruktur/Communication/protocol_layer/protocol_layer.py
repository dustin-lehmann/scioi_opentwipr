#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
""" This file represents the protocol layer of the application """
# ---------------------------------------------------------------------------
# Module Imports 
# ---------------------------------------------------------------------------
import threading
# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------
from Communication.hardware_layer.host_server import HostServer
from Communication.protocol_layer.pl_core_communication import pl_translate_msg_tx, pl_create_raw_msg_rx


class ProtocolLayer:
    """
    The protocol layer is the middleman between HL and ML, it translates the tx/rx queues so that data can be
    exchanged between the two other layers
    """
    def __init__(self, host_server: HostServer):
        # variable to start protocol layer #todo
        self.pl_start = False
        self.host_server = host_server

        # start PL transmit thread
        pl_tx_thread = threading.Thread(target=self._pl_tx_thread)
        pl_tx_thread.start()

        # start PL receive thread
        pl_rx_thread = threading.Thread(target=self._pl_rx_thread_)
        pl_rx_thread.start()

    def _pl_tx_thread(self):
        """
        - Routine for checking the tx queue, if size is not 0, process msg from hl by translate it into a bytearray
        - loop through the clients and check if there are any data that is supposed to be sent
        :return: nothing
        """
        for client in self.host_server.clients:
            while client.pl_ml_tx_queue.qsize() > 0:
                msg = client.pl_ml_tx_queue.get_nowait()
                msg_bytearray = pl_translate_msg_tx(msg)
                client.tx_queue.put_nowait(msg_bytearray)

    def _pl_rx_thread_(self):
        """
        - Routine for checking the rx queue, if size is not 0, create a raw message from bytes_msg
        - loop through the clients and check if there are any data that is supposed to be sent
        :return: nothing
        """
        for client in self.host_server.clients:
            # check if the hardware layer put data in the rx queue
            while client.rx_queue.qsize() > 0:
                # get data from rx_queue
                bytes_msg = client.rx_queue.get_nowait()
                raw_message = pl_create_raw_msg_rx(bytes_msg)
                client.pl_ml_rx_queue.put_nowait(raw_message)




