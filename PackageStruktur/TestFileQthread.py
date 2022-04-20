from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from time import *
from sys import exit, argv


class IOThread(QObject):

    finished = pyqtSignal()
    progress = pyqtSignal(int)
    # signal that is send to main thread
    test_signal = pyqtSignal(int)


    def run(self):
        while not exit_io:
            self.testnumber = 5
            print("Worker thread is alive!")

            self.test_signal.emit(self.testnumber)

            sleep(1)
        self.finished.emit()


class UserIO:

    def __init__(self):
        self.app = QApplication(argv)
        self.MainWindow = QMainWindow()
        #self.ui = Ui_MainWindow()
        #self.ui.setupUi(self.MainWindow)
        self.MainWindow.show()
        self.testnumber = 1000

    def add_thread(self, worker):
        self.worker = worker
        self.thread = QThread()
        worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def test(self, testnumber):
        string = "Testnumber = {}".format(testnumber)
        print(string)


def main():

    global exit_io
    exit_io = False
    print("Start of execution")
    # create main object
    user_io = UserIO()
    # create user thread that send signal
    io_thread = IOThread()
    # add thread to user_io and start running it
    user_io.add_thread(io_thread)

    # Connect all GUI signals
    io_thread.test_signal.connect(user_io.test)

    user_io.app.exec()
    print("Exit UI")

    #end worker thread
    exit_io = True

    exit()

if __name__ == "__main__":
    main()


