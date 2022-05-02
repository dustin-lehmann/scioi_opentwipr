from enum import Enum
from typing import List
import select
import socket
from queue import Queue
import time
from params import *


def check_header(header):
    if not (header[0] == HEADER_0 and header[1] == HEADER_1):
        return 0
    return 1


def get_msg_len(header):
    msb = header[2] << 8  # shift two hex points to the left
    msg_len = msb + header[3]
    rest_len = msg_len - HEADER_SIZE
    return msg_len, rest_len


class SocketState(Enum):
    NOT_CONNECTED = 0
    CONNECTED = 1


class Socket:
    def __init__(self, socket_type, address=None, port=None):
        self.inputs = []
        self.outputs = []
        self.socket_type = socket_type
        self.address = address
        self.port = port
        self.state = SocketState(0)
        self.flag_handshake = 0
        self.sock: socket.socket = None

        self.outgoing_queue = Queue()
        self.incoming_queue = Queue()
        self.ui_print_queue: Queue = None

        self.debug_mode = False

    def connect(self,address=None, port=None):
        if address is not None:
            self.address = address
        if port is not None:
            self.port = port

        if self.port is None or self.address is None:
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.socket_type == "Server":
            self.print("Starting server on {:s} listening on port {:d}...".format(self.address, self.port))
            self.sock.bind((self.address, self.port))
            self.sock.listen(5)
            clientsocket, addr = self.sock.accept()
            clientsocket.setblocking(False)
            self.inputs.append(clientsocket)
            self.outputs.append(clientsocket)
            self.state = SocketState.CONNECTED
            self.print("New connection from {}:{}!".format(addr[0], addr[1]))
        elif self.socket_type == "Client":
            self.print("Trying to connect client to {:s} on port {:d}...".format(self.address, self.port))
            self.sock.connect((self.address, self.port))
            self.print("Connected client to {:s} on port {:d}!".format(self.address, self.port))
            self.sock.setblocking(False)
            self.outputs.append(self.sock)
            self.state = SocketState.CONNECTED
        self.inputs.append(self.sock)

    def tick(self):
        if self.socket_type == "Client" and self.state == SocketState.NOT_CONNECTED:
            self.connect()

        readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, 0)

        for sock in readable:
            if self.socket_type == "Server" and sock is self.sock:
                connection, client_address = sock.accept()
                connection.setblocking(False)
                self.inputs.append(connection)
                self.outputs.append(connection)
                self.state = SocketState.CONNECTED
                self.print("New client: " + client_address[0])
            else:
                try:
                    # first read: header including msg id byte
                    header = sock.recv(HEADER_SIZE)
                    if header:
                        if not check_header(header):
                            print("Header corrupted, resetting network buffer!")
                            # FIXME: bug with negative argument for function recv()
                            # discovered after using MSG_HOST_OUT_LOAD_SEQUENCE
                            # not critical, it also seems to not appear in the current version
                            # empty network buffer
                            sock.recv(8192)
                            return
                        # second read: payload and tail
                        msg_len, rest_len = get_msg_len(header)
                        rest_of_msg = sock.recv(rest_len)
                        if not rest_of_msg:
                            print("Failed reading rest of the message!")

                        # reconstruct message
                        msg = header + rest_of_msg
                    else:
                        # client disconnected, because readable contains no data
                        print("Empty header! Client disconnected!")
                        raise ConnectionAbortedError

                except (ConnectionResetError, ConnectionAbortedError, InterruptedError):
                    self.print("Connection lost!")
                    self.outputs.remove(sock)
                    self.inputs.remove(sock)
                    sock.close()
                    self.state = SocketState.NOT_CONNECTED
                    return

                if len(msg) > 0:
                    self.incoming_queue.put(msg, False)
                    if self.debug_mode:
                        pass
                        # print("Message added to incoming queue!")
                else:
                    self.print("Connection lost")
                    self.outputs.remove(sock)
                    self.inputs.remove(sock)
                    sock.close()
                    self.state = SocketState.NOT_CONNECTED

        for sock in writable:
            while self.outgoing_queue.qsize() > 0:
                data = self.outgoing_queue.get_nowait()
                # if self.debug_mode:
                #     print("Send!")
                sock.send(data)

        for sock in exceptional:
            self.print("Server exception with " + sock.getpeername())
            self.inputs.remove(sock)
            if sock in self.outputs:
                self.outputs.remove(sock)
            sock.close()

    def print(self, string):
        if self.ui_print_queue is not None:
            self.ui_print_queue.put_nowait(string)
        else:
            print(string)
