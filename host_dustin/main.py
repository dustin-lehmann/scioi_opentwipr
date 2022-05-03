import time
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread

import communication.server as server

import threading


def test_function():
    while 1:
        pass
        if len(server.host.clients) < 1:
            continue

        client = server.host.clients[0]
        server.host.send([1, 2, 3, 4, 5], client=client)
        client.send([1, 2, 3, 4, 5])
        server.host.send([1, 2, 3, 4, 5], client='green_robot')
        time.sleep(1)


def main():
    app = QApplication(sys.argv)

    server.host.start()

    test_thread = threading.Thread(target=test_function)
    test_thread.start()

    sys.exit(app.exec())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
