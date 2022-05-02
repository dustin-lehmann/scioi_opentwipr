from Communication.communication import *
from Communication.messages import *
import threading
from queue import Queue
from estimation.positionestimation import *
from global_objects import *
from fsm import FSM, msg_hndlr_host, msg_hndlr_ll
import random
import subprocess
import os

exit_comm = False
exit_main = False

fsm_main = FSM()

from time import sleep


# ----------------------------------------------------------------------------------------------------------------------
class GetIpThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
            host_address = GetHostIP().gethostip()



class ClientCommThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.host_address = 0
        exit_recevie_ip = False

    def run(self):
        get_ip_thread = GetIpThread()
        get_ip_thread.start()
        get_ip_thread.join(10)
        if get_ip_thread.is_alive():
            exit_receive_ip = True

        client.address = self.host_address
        client.port = HOST_PORT
        client.connect()
        while not exit_comm:
            client.tick()
        print("Exit Client")

class ClientMessageHandlerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while not exit_comm:
            if not msg_hndlr_host.flag_waiting:
                msg_hndlr_host.update()
        print("Exit Client Message Handler")


class ServerMessageHandlerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while not exit_comm:
            if not msg_hndlr_ll.flag_waiting:
                msg_hndlr_ll.update()
        print("Exit Server Message Handler")


# Experiment Thread
# Logging Thread

# class LoggingThread(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self)
#
#     def run(self):
#         while not exit_comm:
#             time.sleep(0.1)


def main():

    # Communication with the Host
    client_thread = ClientCommThread()
    client.outgoing_queue = client_outgoing_queue
    client.incoming_queue = client_incoming_queue
    client.debug_mode = True
    client_thread.start()

    # Message Handler C++
    msg_hndlr_ll.msg_dictionary = msg_dictionary_ll
    msg_hndlr_ll.incoming_queue = server_incoming_queue
    msg_hndlr_ll.outgoing_queue = server_outgoing_queue
    msg_hndlr_ll.list_of_allowed_messages = ll_allowed_message_ids
    # Start Server Message Handler Thread
    server_msghndlr_thread = ServerMessageHandlerThread()
    server_msghndlr_thread.start()

    # Message Handler Host
    msg_hndlr_host.msg_dictionary = msg_dictionary_host
    msg_hndlr_host.incoming_queue = client_incoming_queue
    msg_hndlr_host.outgoing_queue = client_outgoing_queue
    msg_hndlr_host.list_of_allowed_messages = hl_allowed_message_ids
    # Start Client Message Handler Thread
    client_msghndlr_thread = ClientMessageHandlerThread()
    client_msghndlr_thread.start()

    # Start Logging Thread
    # logging_thread = LoggingThread()
    # logging_thread.start()

    time_last_fsm = time.time_ns()
    time_last_msg = time.time_ns()
    while not exit_main:
        if (time.time_ns() - time_last_fsm) > 20 * 1000 * 1000:
            time_last_fsm = time.time_ns()
            fsm_main.update()
            # msg = MSG_HOST_IN_CONTINIUOS(global_values["tick"], robot)
            # send_msg_to_host(msg)

        if (time.time_ns() - time_last_msg) > 100 * 1000 * 1000 and (
                fsm_main.state == FSM_STATE.IDLE or fsm_main.state == FSM_STATE.ACTIVE):
            time_last_msg = time.time_ns()
            msg = MSG_HOST_IN_CONTINIUOS(global_values["tick"], robot)
            send_msg_to_host(msg)
    exit_comm = True




if __name__ == '__main__':
    main()



