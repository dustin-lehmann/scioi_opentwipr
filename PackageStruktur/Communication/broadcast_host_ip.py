############################################################################
##                                                                        ##
## Supervisor:          Dustin Lehmann                                    ##
## Author:              David Stoll                                       ##
## Creation Date:       12.04.2022                                        ##
## Description:         Select Host Ip that should be used for            ##
##                      communication and start UDP broadcasting          ##
##                      of address to robots                              ##
############################################################################

import socket
from time import sleep



class HostIp:
    """
    class to determine which IP-address is to be used for the Host-Sever
    """

    def __init__(self):
        self.selected_ip = 0
        self.set_ip()

    def set_ip(self):
        """
        get all available IP-addresses and choose which one to use for further communication
        :return: nothing
        """
        server_address = socket.gethostbyname_ex(socket.gethostname())
        print("IP-addresses available: ")

        # Show active Ip connections until one is selected that is valid
        while True:
            try:
                # print available IPs
                for x in range(len(server_address[2])):
                    print(x, ":", server_address[2][x])
                # choose which Ip is to be used
                # self.selected_ip = server_address[2][int(input("choose the IP you want to use for communication: "))] #TODO: uncomment to make user choose
                # choose second ip since this one happens to be the correct one
                self.selected_ip = server_address[2][0]

            # error handling in case input exceeds number of available IPs
            except IndexError:
                print("Input incorrect!")
            else:
                break
        print("Selected IP: ", self.selected_ip)


class BroadcastIpUDP:
    """
    Create Thread that continuously broadcasts IP address via UDP in local Network to possible clients,
    so they are able to connect to the Host Server using said address
    """

    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.start_udp()

    def start_udp(self):
        """
        Start UDP Server and keep broadcasting the host IP-address
        :return: Nothing
        """
        # AF_INET -> Internet connection, DGRAM -> UDP,
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        server.settimeout(0.2)

        # set ip and port
        server.bind((str(self.ip_address), 44444))

        # encode message for sending
        message = self.ip_address.encode('utf-8')

        print("Broadcasting of IP via UDP started")
        while True:
            server.sendto(message, ('<broadcast>', 37020))
            sleep(1)
