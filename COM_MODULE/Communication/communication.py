from enum import Enum
from typing import List
import select
import socket
from queue import Queue
import time



class SocketState(Enum):
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
        self.flag_handshake = 0
        self.sock: socket.socket = None

        self.outgoing_queue = Queue()
        self.incoming_queue = Queue()

    def connect(self, server_address=None, server_port=None):
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
        if self.socket_type == 'Client' and self.state == SocketState.NOT_CONNECTED:
            self.connect(self.server_address, self.server_port)

        readable, writable, exceptional  = select.select(self.input_connections, self.output_connections, self.input_connections, 0)

        for connection in readable:
            try:
                data = connection.recv(8192)
                self.incoming_queue.put_nowait(data)
                # TODO: Add Callback Function for receiving data
            except (ConnectionResetError, ConnectionAbortedError, InterruptedError):
                print("Connection lost")
                self.output_connections.remove(connection)
                self.input_connections.remove(connection)
                connection.close()
                self.state = SocketState.NOT_CONNECTED
                return

        #     # else:
        #     #     self.print("Connection lost")
        #     #     self.outputs.remove(connection)
        #     #     self.inputs.remove(connection)
        #     #     connection.close()
        #     #     self.state = SocketState.NOT_CONNECTED
        #
        for connection in writable:
            while self.outgoing_queue.qsize() > 0:
                data = self.outgoing_queue.get_nowait()
                connection.send(data)

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