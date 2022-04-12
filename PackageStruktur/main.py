from Communication.host_server import HostServer
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
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    HostServer()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
