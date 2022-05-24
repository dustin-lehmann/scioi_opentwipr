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
import threading

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from layer_core_communication.hl_core_communication import hl_tx_handling, hl_rx_handling
from get_host_ip import GetHostIp, HostIpEvent

exit_comm = False
HOST_PORT = 6666


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

        # Event used to share the Host-Ip between the two threads
        self.host_ip_event = HostIpEvent()

        self.tx_queue = Queue()
        self.rx_queue = Queue()
        self.pl_ml_tx_queue = Queue()
        self.pl_ml_rx_queue = Queue()

    def start(self):

        # start the thread that receives the IP from the Host
        get_ip_thread = threading.Thread(target=GetHostIp, args=(self.host_ip_event,), daemon=True)
        get_ip_thread.start()

        # start transmit thread
        client_tx_thread = threading.Thread(target=self._tx_thread)
        client_tx_thread.start()

        # start communication thread
        client_comm_thread = threading.Thread(target=self._comm_thread)
        client_comm_thread.start()


    def _tx_thread(self):
        """
        - Routine of the tx-Thread is going to be executed
        - loop through the clients and check if there are any data that is supposed to be sent
        - check each queue and put data from there into the socket, flush to send data via socket
        :return: nothing
        """
        while True:
            hl_tx_handling(self.tx_queue, self.sock)

    def _comm_thread(self):
        """
        function to be executed by communication thread that handles hl tx/rx
        :return: nothing
        """
        while not exit_comm:
            # check if any values have been received if not try again
            if self.server_address is None or self.server_port is None:
                flag = self.host_ip_event.wait(5)
                if not flag:
                    print("Timeout while trying to receive the Host-Ip (5 seconds), trying again...")
                # set client address to the received address from the shared event
                self.server_address = self.host_ip_event.received_host_address
                # for now use global of host_port as client port
                self.server_port = HOST_PORT
            # ip and port of Host are known, so communication/ connection is possible
            else:
                self._tick()

        print("Exit Client")

    def _tick(self):
        """
        once the Client received the Server-Ip via UDP it is going to tick periodically, checks if there is any data to
        be received or transmitted, if yes the respective function for handling those tasks are started
        :return: nothing
        """
        if self.socket_type == 'Client' and self.state == SocketState.NOT_CONNECTED:
            self._connect(self.server_address, self.server_port)

        readable, writable, exceptional = select.select(self.input_connections, self.output_connections,
                                                        self.input_connections, 0)

        # rx data
        for connection in readable:
            try:
                # save received data
                data = connection.recv(8192)
                # self.incoming_queue.put_nowait(data)
                hl_rx_handling(data, self.rx_queue, False)

            except (ConnectionResetError, ConnectionAbortedError, InterruptedError):
                print("Connection lost")
                self.output_connections.remove(connection)
                self.input_connections.remove(connection)
                connection.close()
                self.state = SocketState.NOT_CONNECTED
                return

        # tx data
        for connection in writable:
            hl_tx_handling(self.tx_queue, connection)

        for connection in exceptional:
            print("Server exception with " + connection.getpeername())
            self.input_connections.remove(connection)
            if connection in self.output_connections:
                self.output_connections.remove(connection)
            connection.close()

    def _send(self, data):  # TODO: Check if this is thread safe!
        assert (isinstance(data, (list, bytearray, bytes)))
        if isinstance(data, list):
            data = bytes(data)
        self.tx_queue.put_nowait(data)

    def _connect(self, server_address=None, server_port=None):
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


client = Socket("Client")
