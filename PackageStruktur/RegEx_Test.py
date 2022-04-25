import re
from PyQt5.QtCore import QObject, pyqtSignal
#test_string = '123abc34565654abc34456564ABC'
#mylist = ["apple", "banan", "cherry"]

testsignal = pyqtSignal()


class Emitter(QObject):
    def __init__(self):
        super().__init__()

    while True:
        testsignal.emit()


class Receiver(QObject):
    def __init__(self):
        super().__init__()

    def print_fct(self, number):
            print(number)


