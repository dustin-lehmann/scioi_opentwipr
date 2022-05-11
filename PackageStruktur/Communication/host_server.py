#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: 10/04/22
# version ='1.0'
# ---------------------------------------------------------------------------
"""
This module handles the Server thread. The Host Ip is selected and then continuously broadcasted through another
thread, the Host Server that is responsible for all the communication between Host and its clients is created all the
functions for handling clients are provided and Signals are emitted if the status of the Server changes f.e.
when a new client connection is made. Those Signals have to be connected with the respective interface
slots(= functions)
"""
# ---------------------------------------------------------------------------
# Module Imports
from datetime import datetime
from time import sleep

# pyQt
from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PyQt5.QtCore import QObject, pyqtSignal as Signal, QThread

#create threads
import threading

#do crc8 checks of messages
import crc8

from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, Any

import queue

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Imports
from Communication.core_messages import BaseMessage

# Setting and Broadcasting Host-Ip
from Communication.broadcast_host_ip import HostIp, BroadcastIpUDP

from Communication.core_messages import translate_msg_tx

# Robot User-Interface
from robot_ui import RobotUi

from Communication.general import msg_parser, msg_builder, check_header, get_msg_len
from Communication.messages import msg_dictionary, MSG_HOST_IN_DEBUG
from Experiment.experiment import experiment_handler, sequence_handler
from params import SERVER_PORT, HEADER_SIZE
from Communication.gcode_parser import gcode_parser
# ---------------------------------------------------------------------------


class Client:
    """
    -represents a client that has to be connected to the Server
    -each client has their own receive/ transmit queue that is constantly checked by a thread each
    """
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

    def send_message(self, data):
        if isinstance(data, list):
            data = bytes(data)
        self.tx_queue.put_nowait(data)

    def rxAvailable(self):
        return self.rx_queue.qsize()


def debug_print_rx_byte(client_ip, client_data, pos=False):
    """
    handle the incoming data from the client, by adding information like time/ ip to each incoming message
    :param client_ip: ip of client
    :param client_data: data that has been sent
    :return: nothing
    """
    if pos:
        client_data = " ".join("0x{:02X}({:d})".format(b, i) for (i, b) in enumerate(client_data))
    else:
        client_data = " ".join("0x{:02X}".format(b) for b in client_data)
    time = datetime.now().strftime("%H:%M:%S:")
    string = "{} from {}: {}".format(time, client_ip, client_data)
    print(string) # todo: not only display of message, add callback function


class HostServer(QObject):
    """
    create and configure the Host Server that is the key element of the communication between host(Computer) and its
    clients(Robots):
    - The HostServer launches three separate threads:
        - broadcast IP
        - client rx thread
        - client tx thread
    """

    ip: str
    max_clients: int
    num_clients: int
    clients: list[Client]

    address: QHostAddress
    port: int

    server: QTcpServer

    new_client_accepted_signal = Signal(str, int)
    finished_signal = Signal()

    thread = QThread()

    def __init__(self):

        super().__init__()

        # select IP-Address that the Host Application is going to use
        host_ip = HostIp().selected_ip

        self.max_clients = 10
        self.num_clients = 0
        self.clients = []

        self.ip = host_ip

        self.address = QHostAddress()
        self.address.setAddress(self.ip)

        self.port = 6666  # TODO: move to some other file -> params?
        self.server = QTcpServer()

        # start Broadcasting of IP via UDP in separate thread
        broadcast_ip_thread = threading.Thread(target=BroadcastIpUDP, args=(host_ip,))
        broadcast_ip_thread.start()

        # start transmit thread
        client_tx_thread = threading.Thread(target=self.tx_thread)
        client_tx_thread.start()

        # start receive thread
        client_rx_thread = threading.Thread(target=self.rx_thread)
        client_rx_thread.start()

    def run(self):
        """
        just the run method so that the Host Server thread can be started
        :return: nothing
        """
        while True:
            pass

    def tx_thread(self):
        """
        - Routine of the tx-Thread is going to be executed
        - loop through the clients and check if there are any data that is supposed to be sent
        :return: nothing
        """
        while True:
            for client in self.clients:
                while client.tx_queue.qsize() > 0:
                    client.socket.write(client.tx_queue.get_nowait())
                    client.socket.flush()

    def rx_thread(self):
        """
        - Routine of the rx-Thread is going to be executed
        - loop through the clients and check if there is any incoming data
        :return: nothing
        """
        while True:
            for client in self.clients:
                while client.rx_queue.qsize() > 0: # todo
                    client_ip = client.ip
                    client_data = client.rx_queue.get_nowait()
                    debug_print_rx_byte(client_ip, client_data)

    def start(self):
        """
        start the Host Server:
        - listen for new connections
        - move the HostServer to a new thread where it is being executed
        - connect the start signal of the thread to the run method of HostServer
        - start the HostServer in the thread
        :return: nothing
        """
        self.listen()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        self.thread.start()

    def listen(self):
        """
        - listen on the selected Ip for new connections
        - connect the accept_new_client-function to the Signal that is connected once there is a new Connection
        :return: nothing
        """
        self.server.setMaxPendingConnections(self.max_clients)
        self.server.listen(self.address, self.port)
        print("Host Server is listening on", self.server.serverAddress().toString(), ":", self.server.serverPort(),
              "!\n")
        self.server.newConnection.connect(self.accept_new_client)

    def accept_new_client(self):
        """
        -handling of accepting a new client
        -create a new client object with the socket of the newly accepted client
        :return: nothing
        """
        # check if clients_max is already reached
        if len(self.clients) < self.max_clients:
            # Next pending connection is being returned as a QTcpSocket Object
            socket = self.server.nextPendingConnection()
            client = Client(socket)
            # add a new client to the list
            self.clients.append(client)
            peer_address = socket.peerAddress().toString()
            peer_port = socket.peerPort()

            client.ip = peer_address

            print("New connection from", peer_address, ":", peer_port, "!\n")
            # emit new connection signal with peer address and peer port to the interface
            self.new_client_accepted_signal.emit(peer_address, peer_port)

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

    def send_message(self, msg, client: Union[Client, int, list, str] = None):
        """
        - send a message to selected clients
        - it is possible to select a single client, a list of clients, all at once, or a client via its name (string)
        :param buffer: message that has to be sent
        :param client: which client(s) are supposed to receive the message
        :return: nothing
        """

        # change command list in buffer to bytes
        # if isinstance(msg, list): #todo: implement a way to send multiple messages at once -> even needed?
        #     buffer = bytes(buffer)

        # buffer = msg_builder(msg)
        buffer = translate_msg_tx(msg)

        # only one client
        if isinstance(client, Client):
            client.send_message(buffer)

        # multiple clients in list
        elif isinstance(client, list):
            assert ([isinstance(c, Client) for c in client])
            for c in client:
                c.send_message(buffer)

        # client as number (eg. "1" for client_1)
        elif isinstance(client, int):
            if client >= len(self.clients):
                return
            self.clients[client].send_message(buffer)

        # send to all clients
        elif client is None:
            for c in self.clients:
                c.send_message(buffer)

        # client as a string (eg. "green robot")
        elif isinstance(client, str):
            pass  # TODO

    def process_user_input_gcode(self, input_text, write_to_terminal=False, recipient="All"):
        """
        processing of the user input (GCODE) that is sent via the user_input_signal
        :param input_text: input text
        :param write_to_terminal: Determines if the processing of the message is going to be displayed on terminal
        :param recipient: Determines the client the message is for, Default ="All"
        :return: nothing
        """

        # parse input from line edit, the output of the parser is either a msg for ML/LL or
        # a list of strings containing g-codes that are meant for the HL (internal call)
        gcode_parser_output = gcode_parser.parse(input_text)

        if type(gcode_parser_output) == list:
            # validity check
            if gcode_parser_output[0]['type'] == 'M60':
                self.invalid_gcode(input_text)
                return

            self.execute_internal_call(gcode_parser_output, write_to_terminal, input_text)  # HL -> HL
        else:
            if write_to_terminal:
                self.write_message_to_all_terminals(input_text, 'W')
            self.send_message_from_input(gcode_parser_output, write_to_terminal, input_text, recipient)  # HL -> ML/LL
            print("Message to ML/LL")

    def send_message_from_input(self, msg, write_to_terminal, line_text, recipient):
        """
        send a message from the main terminal by emitting a Signal that is sent to the HostServer
        :param msg: output of the gcode parser
        :param write_to_terminal:
        :param line_text: line text before gcode parsing
        :param recipient: receiver of message
        :return: nothing
        """

        # check if any clients are registered

        if len(self.clients) > 0:
            # check if message is meant to be sent to all clients
            if recipient == "All":
                for client_index in range(self.max_clients):
                    if self.client_list[client_index] != 0:
                        # todo: check if params msg and client_index got mixed up and are in wrong order
                        if self.send_message(msg, client_index) == 1:
                            # write sent command to terminal
                            if write_to_terminal:
                                self.write_sent_command_to_terminals(client_index, line_text, "Y")
                        else:
                            # write error message to terminals
                            self.write_sent_command_to_terminals(client_index, line_text, "R")
                            self.write_message_to_terminals(client_index, "Failed to sent message!", "R")
            #
            else:
                for client_index in range(self.max_clients):
                    string = "TWIPR_" + str(client_index)
                    if recipient == string: #todo: find better way to do comparison than using a string -> list object?
                        if self.client_list[client_index] != 0:  # don't send if client has disconnected
                            if self.send_message(msg, client_index) == 1:
                                # write sent command to terminal
                                if write_to_terminal:
                                    self.write_sent_command_to_terminals(client_index, line_text, "Y")
                            else:
                                # write error message to terminals
                                self.write_sent_command_to_terminals(client_index, line_text, "R")
                                self.write_message_to_terminals(client_index, "Failed to sent message!", "R")
                        else:
                            self.popup_invalid_input_main_terminal("{} not connected!".format(recipient))

        else:
            # warning popup
            #self.popup_invalid_input_main_terminal("Please connect a client!") #TODO: use again
            print("Connect client first!")

    def invalid_gcode(self, user_input: str) -> None:
        """
        print 'invalid GCODE' to console
        :param user_input:
        :return:
        """
        string = "Invalid G-code! Please refer to the documentation for further information! (F1)"
        print("invalid GCODE")

    def execute_internal_call(self, cmd_list: List[Dict[str, Any]], write_to_terminal: bool, line_text: str) -> None:
        # the cmd list comprises dictionaries containing a g-code and its arguments respectively
        for gcode in cmd_list:
            if gcode['type'] == 'M61':
                print("internal call function called (Debug message)")
            else:
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
        read the clients buffer
        :param client: buffer that is supposed to be read
        :return:
        """
        num = client.socket.bytesAvailable()
        data = client.socket.read(num)
        client.rx_queue.put_nowait(data)
        # TODO: add callback function for RX -> with crc8-check

    def chop_bytes(self, bytestring, delimiter=0x00):
        """
        chop the by cobs encoded bytestrings into separate messages return, array of integers
        :param delimiter: delimiter that is used to seperate each message
        :param bytestring: bytestring that is supposed to be chopped int separate messages
        :return: list, with separate messages as elements
        """
        # empty list to append the messages later on
        chopped_bytes = []
        # # start position of each byte
        start_byte = 0

        # convert bytes into list
        data_list = list(bytestring)

        for x in range(len(data_list)):
            if data_list[x] == delimiter:
                chopped_bytes.append(data_list[start_byte:(x - 1)])
                start_byte = x + 1

        return chopped_bytes

    def crc_check(self, client_index, msg):
        """
        execute crc-check
        :param client_index: client index in client_ui_list
        :param msg: msg that is to be checked
        :return: nothing
        """
        # create a new CRC8 object
        crc_object = crc8.crc8()
        crc_object.update(msg)
        crc_byte = crc_object.digest()
        # and check the received message
        if crc_byte == b'\x00':
            # CRC8 check successful -> create abstract message object from bytearray
            msg = msg_parser(msg)
            # print("New message has been received successfully . . . handling message!\n")
            if msg.id in msg_dictionary:
                msg_cast = msg_dictionary[msg.id](msg)
                msg_cast.handler(self.client_ui_list[client_index], experiment_handler, sequence_handler)
                # show received message if wanted
                terminal_string = msg_cast.get_string()
                terminal_color = msg_cast.get_color()
                if terminal_string:
                    self.write_received_msg_to_terminals(client_index, terminal_string, terminal_color)
            else:
                self.write_message_to_terminals(client_index, "Received message with unknown message id!", "R")
        else:
            self.write_message_to_terminals(client_index, "Received corrupted message!", "R")


host = HostServer()


