
from Communication.client import client
from Communication.pr_layer import ProtocolLayer
from Communication.msg_layer import MessageLayer
from layer_core_communication.core_messages import SetLEDMessage

from time import sleep


def main():
    # Thread responsible for receiving and sending data (HL)
    client.start()
    # PL
    protocol_layer = ProtocolLayer(client)
    # ML
    message_layer = MessageLayer(client)

    example_msg = SetLEDMessage(1,1)

    # todo hier auch sys.exit(app.exec)?
    while True:
        # message_layer.send_msg(example_msg)
        client.pl_ml_tx_queue.put_nowait(example_msg)
        sleep(1)

if __name__ == '__main__':
    main()
