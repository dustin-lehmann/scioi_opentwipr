from Communication.communication import *
from Communication.messages import *
import threading

from global_objects import *
from fsm import FSM, msg_hndlr_host, msg_hndlr_ll
from get_host_ip import GetHostIp, HostIpEvent
from queue import Queue

exit_comm = False
exit_main = False

from time import sleep

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
        self.host_ip_event.wait(5)

        if get_ip_thread.is_alive():
            print("ending the thread did not work")  # todo: thread can not be killed -> problem?

        client.server_address = self.host_ip_event.received_host_address

        client.server_port = HOST_PORT


        while not exit_comm:
            client.tick()
            # client_outgoing_queue = 0x01, 0x02, 0x03, 0x66        todo wie schicke ich sachen raus?
            # print(client_outgoing_queue)
        print("Exit Client")


def main():
    # Communication with the Host

    a = bytes([0x01,0x11,0xA0,0x24])
    # print("0x01 \t 0x02 \t 0x03")

    client_thread = ClientCommThread()
    client.outgoing_queue = client_outgoing_queue
    client.incoming_queue = client_incoming_queue
    # client.outgoing_queue = Queue()
    # client.incoming_queue = Queue()
    client.debug_mode = True
    client_thread.start()
    buffer = b"0x01"

    while 1:
        if client_incoming_queue.qsize()>0:
            print("incoming queue:")
            print(client_incoming_queue.get_nowait())
        client_outgoing_queue.put_nowait(buffer)





if __name__ == '__main__':
    main()
