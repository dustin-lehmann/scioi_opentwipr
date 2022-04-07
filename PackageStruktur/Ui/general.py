from PyQt5 import QtCore, QtGui, QtWidgets, Qt


class TerminalLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.func_key_up = None
        self.func_key_down = None
        self.func_key_esc = None
        self.func_key_f1 = None
        self.func_key_f2 = None

    def set_functions(self, func1, func2, func3, func4, func5):
        self.set_func_key_up(func1)
        self.set_func_key_down(func2)
        self.set_func_key_esc(func3)
        self.set_func_key_f1(func4)
        self.set_func_key_f2(func5)

    def set_func_key_up(self, func):
        self.func_key_up = func

    def set_func_key_down(self, func):
        self.func_key_down = func

    def set_func_key_esc(self, func):
        self.func_key_esc = func

    def set_func_key_f1(self, func):
        self.func_key_f1 = func

    def set_func_key_f2(self, func):
        self.func_key_f2 = func

    def keyPressEvent(self, event):
        # call the respective function in the QLineEdit
        if event.key() == QtCore.Qt.Key_Up:
            self.func_key_up()
        elif event.key() == QtCore.Qt.Key_Down:
            self.func_key_down()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.func_key_esc()
        elif event.key() == QtCore.Qt.Key_F1:
            self.func_key_f1()
        elif event.key() == QtCore.Qt.Key_F2:
            self.func_key_f2()
        else:
            # keyPressEvent of the base class has to be called if no key is pressed (Qt Docs)
            super().keyPressEvent(event)