import sys
from PyQt5.QtWidgets import QApplication
from Ui.user_io import UserIO
from Communication.host_server_thread import HostServerThread


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

    # HostServerThread:
    host_server_thread = HostServerThread()
    user_io.add_host_server_thread(host_server_thread)


    #Todo: remove since not needed?
    host_server_thread.finished.connect(user_io.host_server_ended)


    sys.exit(app.exec())



if __name__ == "__main__":
    main()
