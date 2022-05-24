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
from layer_core_communication.ml_core_communication import ml_tx_handling, ml_rx_handling
from Communication.client import Socket
from layer_core_communication.core_messages import BaseMessage


class MessageLayer:
    """
    - The message layer is the third layer
    - Responsible for:
        - interpreting received messages (raw-msgs) from the PL
        - create new Messages and send them to the PL

    """
    def __init__(self, client: Socket):
        # variable to start protocol layer #todo
        self.pl_start = False
        self.client = client

        # start ML transmit thread
        pl_tx_thread = threading.Thread(target=self._ml_rx_thread)
        pl_tx_thread.start()

    def _ml_rx_thread(self):
        """
        function used by rx_thread to handle protocol layer rx
        """
        while True:
            ml_rx_handling(self.client.pl_ml_rx_queue, True)

    def send_msg(self, msg: BaseMessage):
        self.client.pl_ml_tx_queue.put_nowait(msg)








