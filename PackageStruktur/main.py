from Communication.host_server import HostServer
from Ui.terminalinterface import TerminalInterface
import sys
import PyQt5.QtWidgets


def main():
    """
    1. Initialize Server -> Server Init.py
    2. register CLients  -> Server Init.py
    3 start thread for incoming queue from main -> Routine in Queue.py
    4 start thread for outgoing queue -> Routine in Queue.py
    5 Queue.py works with the messages defined in messages.py


    :return: Nothing
    """
    # pass sys.arg to allow command line arguments
    app = PyQt5.QtWidgets.QApplication(sys.argv)

    # create Host Server and start a thread that broadcasts the Sever-Ip via Udp
    my_host_server = HostServer()

    # create Terminal Interface and pass the Host Server that is used
    TerminalInterface(my_host_server)

    #
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
