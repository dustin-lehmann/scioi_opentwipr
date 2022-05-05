#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
""" This Module contains the base interface class that provides all the essential Signals for an Interface """
# ---------------------------------------------------------------------------
# Module Imports
import socket
from threading import Event
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------




class HostIpEvent(Event):
    """
    Custom Event that is used to share the HostIp between threads
    """
    def __init__(self):
        super().__init__()
        self.received_host_address = 0

class GetHostIp:
    def __init__(self, host_ip_event: HostIpEvent):
        host_ip_event.received_host_address = self.gethostip()
        host_ip_event.set()

    def gethostip(self):
        """
        receive host-ip via UDP
        :return: ip-Address of host to establish connection
        """

        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("", 37020))
        data, addr = client.recvfrom(1024)

        # decode received data to string
        data = (data.decode('utf-8'))

        # set host address to received data
        host_address = data
        print("received Host-Ip: %s" % data)
        return host_address

