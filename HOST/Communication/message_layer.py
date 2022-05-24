#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: 05/23/22
# version ='1.0'
# ---------------------------------------------------------------------------
"""
This file represents the message-layer of the application
"""
# ---------------------------------------------------------------------------
# Module Imports
# ---------------------------------------------------------------------------
import threading
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from Communication.host_server import HostServer
from layer_core_communication.ml_core_communication import ml_tx_handling, ml_rx_handling


class MessageLayer:
    """
    The protocol layer is the middleman between HL and ML, it translates the tx/rx queues so that data can be
    exchanged between the two other layers
    """
    def __init__(self, host_server: HostServer):
        # variable to start protocol layer #todo
        self.pl_start = False
        self.host_server = host_server

        # start ML receive thread
        ml_rx_thread = threading.Thread(target=self._ml_rx_thread)
        ml_rx_thread.start()

    def _ml_rx_thread(self):
        """
        function used by rx_thread to handle protocol layer rx
        """
        while True:
            for client in self.host_server.clients:
                ml_rx_handling(client.pl_ml_rx_queue, debug = True)






