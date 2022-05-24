#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
"""
This file represents the protocol layer of the application
"""
# ---------------------------------------------------------------------------
# Module Imports 
# ---------------------------------------------------------------------------
import threading
# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------
from Communication.client import client, Socket
from layer_core_communication.pl_core_communication import pl_tx_handling, pl_rx_handling


class ProtocolLayer:
    """
    The protocol layer is the middleman between HL and ML, it translates the tx/rx queues so that data can be
    exchanged between the two other layers
    """
    def __init__(self, client: Socket):
        # variable to start protocol layer #todo
        self.pl_start = False
        self.client = client

        # start PL transmit thread
        pl_tx_thread = threading.Thread(target=self._pl_tx_thread)
        pl_tx_thread.start()

        # start PL receive thread
        pl_rx_thread = threading.Thread(target=self._pl_rx_thread)
        pl_rx_thread.start()

    def _pl_tx_thread(self):
        """
        function used by tx_thread to handle protocol layer tx
        """
        while True:
            pl_tx_handling(client.pl_ml_tx_queue, client.hl_tx_queue)

    def _pl_rx_thread(self):
        """
        function used by rx_thread to handle protocol layer rx
        """
        while True:
            pl_rx_handling(client.hl_rx_queue, client.pl_ml_rx_queue)