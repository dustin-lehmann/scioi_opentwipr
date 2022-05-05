import sys
from PyQt5.QtWidgets import QApplication

from Ui.user_io import UserIO
from Communication.core_messages import SetLEDMessage

import time



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
    user_io = UserIO()

    #Create HostServerThread, add to the user io object
    # host_server_thread = HostServer()
    # user_io.add_host_server_thread(host_server_thread)

    def test_function():
        while 1:
            pass
            if len(user_io.host_server.host.clients) < 1:
                continue

            client = user_io.host_server.clients[0]
            user_io.host_server.host.send([1, 2, 3, 4, 5], client=client)
            client.send([1, 2, 3, 4, 5])
            server.host.send([1, 2, 3, 4, 5], client='green_robot')
            time.sleep(1)


    sys.exit(app.exec())


if __name__ == "__main__":
    main()

