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

from time import sleep

# pyQt
from PyQt5.QtNetwork import QHostAddress, QTcpServer
from PyQt5.QtCore import QObject, pyqtSignal

#create threads
import threading

#do crc8 checks of messages
import crc8

from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, Any

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Imports
from Communication.core_messages import BaseMessage

# Setting and Broadcasting Host-Ip
from Communication.broadcast_host_ip import HostIp, BroadcastIpUDP

# Robot User-Interface
from robot_ui import RobotUi

from Communication.general import msg_parser, msg_builder, check_header, get_msg_len
from Communication.messages import msg_dictionary, MSG_HOST_IN_DEBUG
from Experiment.experiment import experiment_handler, sequence_handler
from params import SERVER_PORT, HEADER_SIZE
from Communication.gcode_parser import gcode_parser
# ---------------------------------------------------------------------------


class HostServer(QObject):
    """
    create and configure the Host Server that is the key element of the communication
    between host(Computer) and its clients(Robots)
    """

    # Each time this Signal is emitted there has been a new connection to the Host Server
    new_connection_signal = pyqtSignal(str, int)
    finished = pyqtSignal()

    def __init__(self):

        super().__init__()

        # select IP-Address that the Host Application is going to use
        host_ip = HostIp().selected_ip

        # start Broadcasting of IP via UDP in separate thread
        broadcast_ip_thread = threading.Thread(target=BroadcastIpUDP, args=(host_ip,))
        broadcast_ip_thread.start()

        # maximum amount of clients that can be registered
        self.clients_max = 10

        # make sure at least one client can be registered
        assert (self.clients_max > 0)

        # initialize current number of clients
        self.clients_number = 0

        # create list with as many elements as the maximum number of clients
        self.client_list = [0] * self.clients_max

        # list for robot user interfaces
        self.client_ui_list: List[Union[int, RobotUi]] = [0] * self.clients_max

        # initialize QHostAddress-class
        self.server_address = QHostAddress()

        # set Host-Server address to chosen ip
        self.server_address.setAddress(host_ip)

        # set Host-Server Port
        self.server_port = SERVER_PORT

        # construct QTcpServer Object
        self.server = QTcpServer()
        self.start_host_server()

    def run(self):

        while True: # todo: integrate while not exit_io
            # make thread less CPU intensive -> better options?
            sleep(1)
        self.finished.emit()

    def start_host_server(self):
        """
        start the Host Server
        :return:
        """
        # set maximum amount of connections QTcpServer is going to accept
        self.server.setMaxPendingConnections(self.clients_max)

        # server listens for incoming connections on previously defined port and address
        self.server.listen(self.server_address, self.server_port)
        print("Host Server is listening on", self.server.serverAddress().toString(), ":", self.server.serverPort(),
              "!\n")

        # connect Signal new Connection to slot that is accepting new client and adding it to the list
        self.server.newConnection.connect(self.accept_new_client)

    def accept_new_client(self):

        # check if clients_max is already reached
        if self.clients_number < self.clients_max:
            # get first free index in client list and break when finished
            # reset client_index
            client_index = 0
            #todo: Hiereaus verkettete Liste? -> müsste man nichtmehr durch die ganzen Clients
            for i in range(self.clients_max):
                if self.client_list[i] == 0:
                    # variable is used to connect client with its functions
                    client_index = i
                    break
            # increment the number of currently registered clients
            self.clients_number += 1
            # Next pending connection is being returned as a QTcpSocket Object
            self.client_list[client_index] = self.server.nextPendingConnection()

            peer_address = self.client_list[client_index].peerAddress().toString()
            peer_port = self.client_list[client_index].peerPort()

            print("New connection from", peer_address, ":", peer_port, "!\n")

            # emit new connection signal with peer address and peer port to the interface
            self.new_connection_signal.emit(peer_address, peer_port)

            # currently: buffer of unlimited size
            # quick fix: the buffering number depends on the size of the biggest message
            # TODO:: NOT CHANGING THIS PARAMETER WILL CAUSE THE HL TO FAIL AT READING INCOMING MESSAGES
            self.client_list[client_index].setReadBufferSize(100)

            # connect readyRead-Signal to read_buffer function of new client
            self.client_list[client_index].readyRead.connect(lambda: self.read_buffer(client_index))

            # connect error-Signal to close_socket function of new client to call after connection ended
            self.client_list[client_index].error.connect(lambda: self.close_socket(client_index))

            # pause accepting new clients but keep them in connection queue
            if self.clients_number == self.clients_max:
                self.server.pauseAccepting()

        else:
            # do not accept more clients than max number of clients
            pass

    def send_message(self, client_index, msg):
        """
        send the message by writing into the clients buffer, which emits a signal that send the message to the client
        :param client_index: index of client message is sent to
        :param msg: message that is to be sent
        :return: 1 if successful, 0 if failed
        """
        buffer = msg_builder(msg)
        bytes_sent = self.client_list[client_index].write(buffer)
        if bytes_sent == -1:
            return 0
        else:
            return 1

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

        if self.clients_number > 0:
            #check if message is meant to be sent to all clients
            if recipient == "All":
                for client_index in range(self.clients_max):
                    if self.client_list[client_index] != 0:
                        if self.send_message(client_index, msg) == 1:
                            # write sent command to terminal
                            if write_to_terminal:
                                self.write_sent_command_to_terminals(client_index, line_text, "Y")
                        else:
                            # write error message to terminals
                            self.write_sent_command_to_terminals(client_index, line_text, "R")
                            self.write_message_to_terminals(client_index, "Failed to sent message!", "R")
            #
            else:
                for client_index in range(self.clients_max):
                    string = "TWIPR_" + str(client_index)
                    if recipient == string:
                        if self.client_list[client_index] != 0:  # don't send if client has disconnected
                            if self.send_message(client_index, msg) == 1:
                                # write sent command to terminal
                                if write_to_terminal:
                                    self.write_sent_command_to_terminals(client_index, line_text, "Y")
                            else:
                                # write error message to terminals
                                self.write_sent_command_to_terminals(client_index, line_text, "R")
                                self.write_message_to_terminals(client_index, "Failed to sent message!", "R")
                        else:
                            self.popup_invalid_input_main_terminal("{} not connected!".format(recipient))
            # clear the line edit
            #self.gb22_line.setText("") todo: not needed because terminal does it anyway?
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

    def close_socket(self, client_index):
        """
        close a socket once the client has disconnected
        :param client_index: index of client in client_list
        :return: nothing
        """
        # (1) handle client connection
        self.client_list[client_index].close()
        # remove client from list
        self.client_list[client_index] = 0
        self.clients_number -= 1
        print("Client socket", client_index, "closed and removed from the list!")
        self.server.resumeAccepting()

    def read_buffer(self, client_index):
        """
        read the client
        :param client_index: index of client in client_list
        :return:
        """
        # first read: header including msg id byte
        header = self.client_list[client_index].read(HEADER_SIZE)
        if not header:
            print("Empty header!")
        # static length messaging -> now: dynamic length messaging
        if not check_header(header):
            print("Header corrupted!")

        # second read: payload and tail
        msg_len, rest_len = get_msg_len(header)
        rest_of_msg = self.client_list[client_index].read(rest_len)
        if not rest_of_msg:
            print("Failed to read payload and tail!")

        msg = header + rest_of_msg

        # check crc8 byte
        self.crc_check(client_index, msg)

    def crc_check(self, client_index, msg):
        """
        execute crc-check
        :param client_index: client index in client_ui_list
        :param msg: msg that is to be checked
        :return:
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


if __name__ == "__main__":
    Host = HostServer()
