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


# ----------------------------------------------------------------------------------------------------------------------

class ClientCommThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        client.connect()
        while not exit_comm:
            client.tick()
        print("Exit Client")


class ServerCommThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        server.connect()
        while not exit_comm:
            server.tick()
        print("Exit Server")


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
    # Communication with the C++ Program
    server.outgoing_queue = server_outgoing_queue
    server.incoming_queue = server_incoming_queue
    server_thread = ServerCommThread()
    server.debug_mode = True
    server_thread.start()

    # xdot_cmd = random.sample(range(0, 1000), 100)
    # psidot_cmd = random.sample(range(0, 1000), 100)

    # while (1):
    #     if server.state == SocketState.CONNECTED:
    #         # msg = MSG_LL_IN_DEBUG(0, "ABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDE")
    #         msg1 = MSG_LL_IN_CTRL_INPUT_BUFFER_VEL(0, xdot_cmd, psidot_cmd)
    #         # msg2 = MSG_LL_IN_CTRL_INPUT(0, [1, 2], 4, 5)
    #         send_msg_to_ll(msg1)
    #         # send_msg_to_ll(msg2)
    #     time.sleep(1)

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

    # Start BBB_C
    # os.chdir("/home/lehmann/Software/c")
    # subprocess.run(["chmod", "a+x", "BBB_C"])
    # subprocess.run(["./BBB_C"])
    # os.chdir("/home/lehmann/Software/py")

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
