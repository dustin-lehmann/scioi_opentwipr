import Communication.core_messages
from Communication.communication import *
from Communication.core_messages import SetLEDMessage
import threading

import cobs.cobs as cobs

from global_objects import *
from fsm import FSM, msg_hndlr_host, msg_hndlr_ll
from get_host_ip import GetHostIp, HostIpEvent
from queue import Queue
from Communication.core_messages import translate_rx_message

exit_comm = False
exit_main = False

from time import sleep

import cobs.cobs as cobs
from abc import ABC


class ClientCommThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.host_ip_event = HostIpEvent()

    def run(self):
        """
        -start new thread that tries to obtain the Host-Ip
        :return:
        """
        get_ip_thread = threading.Thread(target=GetHostIp, args=(self.host_ip_event,), daemon=True)
        get_ip_thread.start()
        # wait until started thread triggers Event with timeout of 5seconds

        while not exit_comm:
            # check if any values have been received if not try again
            if client.server_address is None or client.server_port is None:
                flag = self.host_ip_event.wait(5)
                if not flag:
                    print("Timeout while trying to receive the Host-Ip (5 seconds), trying again...")
                # set client address to the received address from the shared event
                client.server_address = self.host_ip_event.received_host_address
                # for now use global of host_port as client port
                client.server_port = HOST_PORT
            # ip and port of Host are known, so communication/ connection is possible
            else:
                client.tick()

        print("Exit Client")


def main():
    # Communication with the Host

    a = bytes([0x01,0x11,0xA0,0x24])
    # print("0x01 \t 0x02 \t 0x03")

    client_thread = ClientCommThread()
    client.outgoing_queue = client_outgoing_queue
    client.incoming_queue = client_incoming_queue

    client.debug_mode = True
    client_thread.start()

    # from here just debugging
    buffer = b"\x01\x02\x03\x04\x05\x06\x07\x08\x01"
    buffer2 = b"\xBB\x02\x01\x05\x06\x07\x08\x01\x00"
    # print("before encoding: {}".format(buffer))
    buffer = cobs.encode(buffer)
    buffer = buffer.__add__(b'\x00')
    print(buffer)




    while 1:
        if client_incoming_queue.qsize()>0:
            print("incoming queue:")
            incoming_bytestring = client_incoming_queue.get_nowait()
            print(incoming_bytestring)
            translated_message= translate_rx_message(incoming_bytestring)
            print(translated_message)
        client_outgoing_queue.put_nowait(buffer)
        sleep(0.6) #todo: not possible to send much data
        # client_outgoing_queue.put_nowait(buffer2)
        client_outgoing_queue.put_nowait(buffer2)
        sleep(0.6)





if __name__ == '__main__':
    main()
