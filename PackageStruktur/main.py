import sys
import threading
from PyQt5.QtWidgets import QApplication

from Ui.Interfaces import terminal_interface, file_exectuion_interface
from Ui.user_io import UserIO
from Communication.core_messages import SetLEDMessage
from Communication import host_server

import time


def test_function():
    while 1:
        pass
        if len(host_server.host.clients) < 1:
            continue

        client = host_server.host.clients[0]
        host_server.host.send_message([1, 2, 3, 4, 5])
        client.send_message([1, 2, 3, 4, 5])
        host_server.host.send_message([1, 2, 3, 4, 5])
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


    # create UserIO-object
    # user_interface = terminal_interface

    #Create HostServerThread, add to the user io object
    # host_server_thread = HostServer()
    # user_io.add_host_server_thread(host_server_thread)


    host_server.host.start()
    # host_server_thread = threading.Thread(target = host_server.host.run)
    # host_server_thread.start()

    test_thread = threading.Thread(target=test_function)
    test_thread.start()

    sys.exit(app.exec())




if __name__ == '__main__':
    main()
