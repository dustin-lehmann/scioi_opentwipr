import sys
import threading
from PyQt5.QtWidgets import QApplication

from Communication import host_server
from Communication.core_communication import core_messages

import time


def test_function():
    while 1:
        pass
        if len(host_server.host.clients) < 1:
            continue
        msg = core_messages.SetLEDMessage(1, 0)
        client = host_server.host.clients[0]
        # host_server.host.send_message([1, 2, 3, 4, 6])
        # host_server.host.send_message(msg.raw_data)
        # host_server.host.send_message(msg, 0)
        # client.send_message([1, 2, 3, 4, 5])
        # host_server.host.send_message([1, 2, 3, 4, 5])
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

    host_server.host.start()

    test_thread = threading.Thread(target=test_function)
    test_thread.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
