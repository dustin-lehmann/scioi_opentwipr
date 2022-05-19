import sys
import threading
from PyQt5.QtWidgets import QApplication

from Communication.hardware_layer import host_server
from Communication.core_communication import core_messages
from Communication.protocol_layer.protocol_layer import ProtocolLayer

import time


def test_function():
    while 1:
        pass
        if len(host_server.host.clients) < 1:
            continue
        msg = core_messages.SetLEDMessage(1, 0)
        host_server.host.clients[0].pl_ml_tx_queue.put_nowait(msg)
        time.sleep(1)


def main():
    """
    1. create the Server via Qthread that emits a signal every 100ms which delivers used information
        Signals:
                connections
                ...
    2. create the terminal that displays the actual information of the server and its clients


    :return: Nothing
    """

    # pass sys.arg to allow command line arguments
    app = QApplication(sys.argv)

    # Host Server
    host_server.host.start()

    # Protocol Layer
    protocol_layer = ProtocolLayer(host_server.host)

    test_thread = threading.Thread(target=test_function)
    test_thread.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
