#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
""" This Module is responsible for receiving the Host-Server Ip via UDP """
# ---------------------------------------------------------------------------
# Module Imports
from enum import Enum
import select
import socket
from queue import Queue
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from Communication.layer_core_communication.hw_layer_core_communication import hl_tx_handling, hl_rx_handling


class SocketState(Enum):
    """
    class to describe the current state of socket
    """
    NOT_CONNECTED = 0
    CONNECTED = 1


class Socket:
    def __init__(self, socket_type, server_address=None, server_port=None):
        self.input_connections = []
        self.output_connections = []
        self.socket_type = socket_type
        self.server_address = server_address
        self.server_port = server_port
        self.state = SocketState(0)
        self.sock: socket.socket = None

        self.outgoing_queue = Queue()
        self.incoming_queue = Queue()

    def connect(self, server_address=None, server_port=None):
        """
        connect to client if server_address AND server Port are defined
        :param server_address: address of Host-Server
        :param server_port: port of Host-Server
        :return: nothing
        """
        if server_address is not None:
            self.server_address = server_address
        if server_port is not None:
            self.server_port = server_port

        if server_port is None or server_address is None:
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.socket_type == "Client":
            print(
                "Trying to connect client to {:s} on port {:d}...".format(str(self.server_address), self.server_port))
            self.sock.connect((self.server_address, self.server_port))
            print("Connected client to {:s} on port {:d}!".format(self.server_address, self.server_port))
            self.sock.setblocking(False)
            self.output_connections.append(self.sock)
            self.state = SocketState.CONNECTED
        self.input_connections.append(self.sock)

    def tick(self):
        """
        once the Client received the Server-Ip via UDP it is going to tick periodically, checks if there is any data to
        be received or transmitted, if yes the respective function for handling those tasks are started
        :return: nothing
        """
        if self.socket_type == 'Client' and self.state == SocketState.NOT_CONNECTED:
            self.connect(self.server_address, self.server_port)

        readable, writable, exceptional  = select.select(self.input_connections, self.output_connections, self.input_connections, 0)

        # rx data
        for connection in readable:
            try:
                # save received data
                data = connection.recv(8192)
                # self.incoming_queue.put_nowait(data)
                hl_rx_handling(data, self.incoming_queue, True)

            except (ConnectionResetError, ConnectionAbortedError, InterruptedError):
                print("Connection lost")
                self.output_connections.remove(connection)
                self.input_connections.remove(connection)
                connection.close()
                self.state = SocketState.NOT_CONNECTED
                return

        # tx data
        for connection in writable:
            while self.outgoing_queue.qsize() > 0:
                # data = self.outgoing_queue.get_nowait()
                # connection.send(data)
                hl_tx_handling(self.outgoing_queue, connection)

        for connection in exceptional:
            print("Server exception with " + connection.getpeername())
            self.input_connections.remove(connection)
            if connection in self.output_connections:
                self.output_connections.remove(connection)
            connection.close()

    def send(self, data): #TODO: Check if this is thread safe!
        assert(isinstance(data,(list,bytearray,bytes)))
        if isinstance(data, list):
            data = bytes(data)
        self.outgoing_queue.put_nowait(data)

    def tx_thread(self):
        pass

    def rx_thread(self):
        pass

client = Socket("Client")