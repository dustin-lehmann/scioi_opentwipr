from typing import List, Union
from params import SERVER_PORT
from PyQt5.QtNetwork import QHostAddress, QTcpServer
from robot_ui import RobotUi
from Communication.broadcast_host_ip import HostIp, BroadcastIpUDP
import threading
import crc8
from Communication.general import msg_parser, msg_builder, check_header, get_msg_len
from Communication.messages import msg_dictionary, MSG_HOST_IN_DEBUG
from Experiment.experiment import experiment_handler, sequence_handler
from Robot import data
from params import HEADER_SIZE


class HostServer:
    """
    User interface to be able to communicate with the robots
    Configuration of Host Server
    """

    def __init__(self):

        # select Host-IP
        host_ip = HostIp().selected_ip

        # start Broadcasting of IP via UDP in seperate thread
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

        # set server address to chosen ip
        self.server_address.setAddress(host_ip)

        # set Server Port
        self.server_port = SERVER_PORT

        # construct QTcpServer Object
        self.server = QTcpServer()
        self.start_host_server()

    def start_host_server(self):
        """
        start Host Server
        :return:
        """
        # set maximum amount of connections QTcpServer is going to accept
        self.server.setMaxPendingConnections(self.clients_max)

        # server listens for incoming connections on previously defined port and address
        self.server.listen(self.server_address, self.server_port)
        print("Host Server is listening on", self.server.serverAddress().toString(), ":", self.server.serverPort(),
              "!\n")

        # connect empty slot to newConnection -> Signal is emitted every time a new connection is available
        # connect to slot that is adding new clients to the list
        self.server.newConnection.connect(self.accept_new_client)

    def accept_new_client(self):

        # check if clients_max is already reached
        if self.clients_number < self.clients_max:
            # get first free index in client list and break when finished
            # reset client_index
            client_index = 0
            for i in range(self.clients_max):
                if self.client_list[i] == 0:
                    # variable is used to connect client with its functions
                    client_index = i
                    break
            # increment the number of currently registered clients
            self.clients_number += 1
            # add client to list
            self.client_list[client_index] = self.server.nextPendingConnection()
            print("New connection from", self.client_list[client_index].peerAddress().toString(), ":",
                  self.client_list[client_index].peerPort(), "!\n")

            # currently: buffer of unlimited size
            # quick fix: the buffering number depends on the size of the biggest message
            # TODO:: NOT CHANGING THIS PARAMETER WILL CAUSE THE HL TO FAIL AT READING INCOMING MESSAGES
            self.client_list[client_index].setReadBufferSize(100)

            # this connects the signals of the socket to the respective functions
            if client_index == 0:
                #self.client_list[client_index].readyRead.connect(self.read_buffer(client_index))
                #self.client_list[client_index].error.connect(self.close_socket(client_index))

                self.client_list[client_index].readyRead.connect(self.read_buffer_0)

                # self.client_list[client_index].disconnected.connect(self.close_socket_0)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_0)
            elif client_index == 1:
                self.client_list[client_index].readyRead.connect(self.read_buffer_1)
                # self.client_list[client_index].disconnected.connect(self.close_socket_1)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_1)
            elif client_index == 2:
                self.client_list[client_index].readyRead.connect(self.read_buffer_2)
                # self.client_list[client_index].disconnected.connect(self.close_socket_2)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_2)
            elif client_index == 3:
                self.client_list[client_index].readyRead.connect(self.read_buffer_3)
                # self.client_list[client_index].disconnected.connect(self.close_socket_3)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_3)
            elif client_index == 4:
                self.client_list[client_index].readyRead.connect(self.read_buffer_4)
                # self.client_list[client_index].disconnected.connect(self.close_socket_4)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_4)
            elif client_index == 5:
                self.client_list[client_index].readyRead.connect(self.read_buffer_5)
                # self.client_list[client_index].disconnected.connect(self.close_socket_5)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_5)
            elif client_index == 6:
                self.client_list[client_index].readyRead.connect(self.read_buffer_6)
                # self.client_list[client_index].disconnected.connect(self.close_socket_6)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_6)
            elif client_index == 7:
                self.client_list[client_index].readyRead.connect(self.read_buffer_7)
                # self.client_list[client_index].disconnected.connect(self.close_socket_7)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_7)
            elif client_index == 8:
                self.client_list[client_index].readyRead.connect(self.read_buffer_8)
                # self.client_list[client_index].disconnected.connect(self.close_socket_8)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_8)
            elif client_index == 9:
                self.client_list[client_index].readyRead.connect(self.read_buffer_9)
                # self.client_list[client_index].disconnected.connect(self.close_socket_9)  # disconnected == error
                self.client_list[client_index].error.connect(self.close_socket_9)

            # pause accepting new clients but keep them in connection queue
            if self.clients_number == self.clients_max:
                self.server.pauseAccepting()

        else:
            # do not accept more clients than max number of clients
            pass

    def send_message(self, client_index, msg):
        buffer = msg_builder(msg)
        bytes_sent = self.client_list[client_index].write(buffer)
        if bytes_sent == -1:
            return 0
        else:
            return 1

    def close_socket(self, client_index):
        # (1) handle client connection
        self.client_list[client_index].close()
        # remove client from list
        self.client_list[client_index] = 0
        self.clients_number -= 1
        print("Client socket", client_index, "closed and removed from the list!")
        self.server.resumeAccepting()

    def read_buffer(self, client_index):
        # first read: header including msg id byte
        header = self.client_list[client_index].read(5) #TODO: change to not having to use hard coded value -> detection of some elements (Header/ Tail?)
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



    def close_socket_0(self):
        i = 0
        self.close_socket(i)

    def close_socket_1(self):
        i = 1
        self.close_socket(i)

    def close_socket_2(self):
        i = 2
        self.close_socket(i)

    def close_socket_3(self):
        i = 3
        self.close_socket(i)

    def close_socket_4(self):
        i = 4
        self.close_socket(i)

    def close_socket_5(self):
        i = 5
        self.close_socket(i)

    def close_socket_6(self):
        i = 6
        self.close_socket(i)

    def close_socket_7(self):
        i = 7
        self.close_socket(i)

    def close_socket_8(self):
        i = 8
        self.close_socket(i)

    def close_socket_9(self):
        i = 9
        self.close_socket(i)

    def close_socket(self, client_index):
        # (1) handle client connection
        self.client_list[client_index].close()
        # remove client from list
        self.client_list[client_index] = 0
        self.clients_number -= 1
        print("Client socket", client_index, "closed and removed from the list!")
        self.server.resumeAccepting()

    def read_buffer_0(self):
        i = 0
        self.read_buffer(i)

    def read_buffer_1(self):
        i = 1
        self.read_buffer(i)

    def read_buffer_2(self):
        i = 2
        self.read_buffer(i)

    def read_buffer_3(self):
        i = 3
        self.read_buffer(i)

    def read_buffer_4(self):
        i = 4
        self.read_buffer(i)

    def read_buffer_5(self):
        i = 5
        self.read_buffer(i)

    def read_buffer_6(self):
        i = 6
        self.read_buffer(i)

    def read_buffer_7(self):
        i = 7
        self.read_buffer(i)

    def read_buffer_8(self):
        i = 8
        self.read_buffer(i)

    def read_buffer_9(self):
        i = 9
        self.read_buffer(i)

    def read_buffer(self, client_index):
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