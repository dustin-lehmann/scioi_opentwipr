
from Communication.client import client
from Communication.pr_layer import ProtocolLayer
from Communication.msg_layer import MessageLayer
from layer_core_communication.core_messages import SetLEDMessage

from time import sleep
import threading


def main():

    def example_cm():
        example_msg = SetLEDMessage(1,1)
        message_layer.send_msg(example_msg)
        while(True):
            client.pl_ml_tx_queue.put_nowait(example_msg)
            sleep(0.1)


    # Thread responsible for receiving and sending data (HL)
    client.start()
    # PL
    protocol_layer = ProtocolLayer(client)
    # ML
    message_layer = MessageLayer(client)

    # thread that executes example
    demo_thread_cm = threading.Thread(target=example_cm)
    demo_thread_cm.start()

    # todo hier auch sys.exit(app.exec)?
    while True:
        sleep(1)


if __name__ == '__main__':
    main()
