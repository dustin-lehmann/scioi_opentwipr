from Communication.communication import *
from Communication.messages import *
import threading

from global_objects import *
from fsm import FSM, msg_hndlr_host, msg_hndlr_ll
from get_host_ip import GetHostIp, HostIpEvent
from queue import Queue

exit_comm = False
exit_main = False

fsm_main = FSM()

from time import sleep


# ----------------------------------------------------------------------------------------------------------------------
# class GetIpThread(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self)
#
#     def run(self):
#             host_address = GetHostIP().gethostip()



class ClientCommThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.host_ip_event = HostIpEvent()

    def run(self):
        """
        -start new thread that tries to obtain the Host-Ip
        :return:
        """
        get_ip_thread = threading.Thread(target=GetHostIp, args=(self.host_ip_event,), daemon= True)
        get_ip_thread.start()
        #wait until started thread triggers Event with timeout of 5seconds
        self.host_ip_event.wait(5)

        if get_ip_thread.is_alive():
            print("ending the thread did not work") #todo: thread can not be killed -> problem?

        client.address = self.host_ip_event.received_host_address

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


def main():

    # Communication with the Host
    client_thread = ClientCommThread()
    client.outgoing_queue = client_outgoing_queue
    client.incoming_queue = client_incoming_queue
    client.debug_mode = True
    client_thread.start()

    # Message Handler C++
    msg_hndlr_ll.msg_dictionary = msg_dictionary_ll
    # msg_hndlr_ll.incoming_queue = server_incoming_queue
    # msg_hndlr_ll.outgoing_queue = server_outgoing_queue
    msg_hndlr_ll.list_of_allowed_messages = ll_allowed_message_ids
    # Start Server Message Handler Thread
    # server_msghndlr_thread = ServerMessageHandlerThread()
    # server_msghndlr_thread.start()

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
        #todo: Test for sending message to host REMOVE
        # msg_test = MSG_HOST_IN_DEBUG(global_values["tick"], "test")
        # send_msg_to_host(msg_test)
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




