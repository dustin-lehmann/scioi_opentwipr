import time
from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PyQt5.QtCore import QObject, QThread
from PyQt5.QtCore import pyqtSignal as Signal
from typing import Union
import queue
import crc8

from dataclasses import dataclass

''' TODO
- callback functions for receive
- Identify Clients by ID
- add old function back in to set the IP 

'''


class Client:
    rx_queue: queue.Queue
    tx_queue: queue.Queue
    socket: QTcpSocket
    id: str
    type: str
    ip: str

    def __init__(self, socket):
        self.socket = socket
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()
        self.id = None
        self.type = None
        self.ip = None

    def send(self, data):
        if isinstance(data, list):
            data = bytes(data)
        self.tx_queue.put_nowait(data)

    def rxAvailable(self):
        return self.rx_queue.qsize()


class HostServer(QObject):
    ip: str
    max_clients: int
    num_clients: int
    clients: list[Client]

    address: QHostAddress
    port: int

    server: QTcpServer

    new_connection_signal = Signal(str, int)
    finished_signal = Signal()

    thread = QThread()

    def __init__(self):
        super().__init__()

        self.max_clients = 10
        self.num_clients = 0
        self.clients = []

        self.ip = "192.168.0.110"  # TODO

        self.address = QHostAddress()
        self.address.setAddress(self.ip)

        self.port = 6666  # TODO
        self.server = QTcpServer()

    def run(self):
        while True:
            for client in self.clients:
                while client.tx_queue.qsize() > 0:
                    client.socket.write(client.tx_queue.get_nowait())
                    client.socket.flush()

    def start(self):
        self.listen()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        self.thread.start()

    def listen(self):
        self.server.setMaxPendingConnections(self.max_clients)
        self.server.listen(self.address, self.port)
        print("Host Server is listening on", self.server.serverAddress().toString(), ":", self.server.serverPort(),
              "!\n")
        self.server.newConnection.connect(self.acceptNewClient)

    def send(self, buffer, client: Union[Client, int, list, str] = None):
        if isinstance(buffer, list):
            buffer = bytes(buffer)

        if isinstance(client, Client):
            client.send(buffer)
        elif isinstance(client, list):
            assert ([isinstance(c, Client) for c in client])
            for c in client:
                c.send(buffer)
        elif isinstance(client, int):
            if client >= len(self.clients):
                return
            self.clients[client].send(buffer)
        elif client is None:
            for c in self.clients:
                c.send(buffer)
        elif isinstance(client, str):
            pass  # TODO

    def acceptNewClient(self):
        # check if clients_max is already reached
        if len(self.clients) < self.max_clients:

            socket = self.server.nextPendingConnection()
            client = Client(socket)
            self.clients.append(client)

            # Next pending connection is being returned as a QTcpSocket Object

            peer_address = socket.peerAddress().toString()
            peer_port = socket.peerPort()

            client.ip = peer_address

            print("New connection from", peer_address, ":", peer_port, "!\n")
            # emit new connection signal with peer address and peer port to the interface
            self.new_connection_signal.emit(peer_address, peer_port)

            # currently: buffer of unlimited size
            # quick fix: the buffering number depends on the size of the biggest message
            # TODO:: NOT CHANGING THIS PARAMETER WILL CAUSE THE HL TO FAIL AT READING INCOMING MESSAGES
            socket.setReadBufferSize(100)
            # connect readyRead-Signal to read_buffer function of new client
            socket.readyRead.connect(lambda: self.read_buffer(client))
            # connect error-Signal to close_socket function of new client to call after connection ended
            socket.error.connect(lambda: self.close_socket(client))
            # pause accepting new clients but keep them in connection queue
            if len(self.clients) == self.max_clients:
                self.server.pauseAccepting()
        else:
            # do not accept more clients than max number of clients
            pass

    def close_socket(self, client: Client):
        """
        close a socket once the client has disconnected
        :param client:
        :return: nothing
        """
        # (1) handle client connection
        client.socket.close()
        print("Client socket", client.ip, "closed and removed from the list!")
        # remove client from list
        self.clients.remove(client)
        self.server.resumeAccepting()

    def read_buffer(self, client: Client):
        """
        read the client
        :param client:
        :return:
        """
        num = client.socket.bytesAvailable()
        data = client.socket.read(num)
        client.rx_queue.put_nowait(data)
        # TODO: add callback function for RX


host = HostServer()
