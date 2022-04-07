from Experiment.experiment import sequence_handler, experiment_handler
from Ui.general import TerminalLineEdit

#PyQt
from PyQt5 import QtWidgets, QtCore, QtGui

#Plotting
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

#GCode
from Communication.gcode_parser import gcode_parser


import sys
from IO.file_handlers import txt_handler
from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, Any


class Command_Ui:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setWindowIcon(QtGui.QIcon("Icons/TU_Logo_kurz_RGB_rot.jpg"))
        self.main_window.showMaximized()
        self.main_window.show()

        # delta for timer thread
        self.refresh_time_ms = 100
        self.time_point = 0

        # command history for repeating previously used commands in the main terminal
        self.cmd_history_limit = 10
        self.cmd_history = []
        self.cmd_history_reading_index = 0
        self.setup_main_ui()

    def setup_main_ui(self):
        self.main_window.setObjectName("self.main_window")
        self.main_window.resize(1945, 1089)
        self.main_window.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.centralwidget = QtWidgets.QWidget(self.main_window)
        self.centralwidget.setObjectName("centralwidget")

        # timer for refreshing the plot
        self.ui_timer = QtCore.QTimer()
        self.ui_timer.setInterval(self.refresh_time_ms)
        self.ui_timer.timeout.connect(self.timeout)

        # gb2
        self.gb2 = QtWidgets.QGroupBox(self.centralwidget)
        self.gb2.setGeometry(QtCore.QRect(750, 10, 1161, 471))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.gb2.setPalette(palette)
        self.gb2.setObjectName("gb2")
        self.gb21 = QtWidgets.QGroupBox(self.gb2)
        self.gb21.setGeometry(QtCore.QRect(10, 20, 121, 439))
        self.gb21.setObjectName("gb21")
        self.gb21_list = QtWidgets.QListWidget(self.gb21)
        self.gb21_list.setEnabled(True)
        self.gb21_list.setGeometry(QtCore.QRect(10, 20, 101, 411))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.gb21_list.setFont(font)
        self.gb21_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.gb21_list.setObjectName("gb21_list")
        self.gb22 = QtWidgets.QGroupBox(self.gb2)
        self.gb22.setGeometry(QtCore.QRect(140, 20, 1011, 439))
        self.gb22.setObjectName("gb22")
        self.layoutWidget = QtWidgets.QWidget(self.gb22)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 20, 991, 411))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gb22_horlay = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.gb22_horlay.setContentsMargins(0, 0, 0, 0)
        self.gb22_horlay.setObjectName("gb22_horlay")
        self.gb22_list = QtWidgets.QListWidget(self.layoutWidget)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        self.gb22_list.setPalette(palette)
        self.gb22_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.gb22_list.setObjectName("gb22_list")
        # write to main terminal
        #string = "Please activate a TWIPR and connect to the HL! HL is listening on {}:{}!".format(SERVER_ADDRESS,
        #                                                                                           SERVER_PORT)
        #self.write_message_to_main_terminal(string, "W")

        self.gb22_horlay.addWidget(self.gb22_list)
        self.gb22_verlay = QtWidgets.QHBoxLayout()
        self.gb22_verlay.setObjectName("gb22_verlay")
        self.gb22_line = TerminalLineEdit(self.layoutWidget)
        self.gb22_line.set_functions(self.read_from_cmd_history_key_up,
                                     self.read_from_cmd_history_key_down,
                                     self.read_from_cmd_history_key_esc,
                                     self.read_from_cmd_history_key_f1,
                                     self.read_from_cmd_history_key_f2)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        self.gb22_line.setPalette(palette)
        self.gb22_line.setObjectName("gb22_line")
        self.gb22_line.setPlaceholderText("Enter command")
        self.gb22_verlay.addWidget(self.gb22_line)
        self.gb22_combo = QtWidgets.QComboBox(self.layoutWidget)
        self.gb22_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.gb22_combo.setObjectName("gb22_combo")
        self.gb22_combo.addItem("All")
        self.gb22_verlay.addWidget(self.gb22_combo)
        self.gb22_horlay.addLayout(self.gb22_verlay)
        self.gb3 = QtWidgets.QGroupBox(self.centralwidget)
        self.gb3.setGeometry(QtCore.QRect(10, 490, 1901, 541))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(236, 236, 236))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.gb3.setPalette(palette)
        self.gb3.setObjectName("gb3")
        self.gb3_tabwidget = QtWidgets.QTabWidget(self.gb3)
        self.gb3_tabwidget.setEnabled(True)
        self.gb3_tabwidget.setGeometry(QtCore.QRect(10, 20, 1881, 511))
        self.gb3_tabwidget.setObjectName("gb3_tabwidget")

        # creating about tab
        self.tab_About = QtWidgets.QWidget()
        self.tab_About.setObjectName("tab_About")
        self.gb3_tabwidget_tab_About_gb1 = QtWidgets.QGroupBox(self.tab_About)
        self.gb3_tabwidget_tab_About_gb1.setGeometry(QtCore.QRect(10, 10, 321, 281))
        self.gb3_tabwidget_tab_About_gb1.setObjectName("gb3_tabwidget_tab_About_gb1")
        self.gb3_tabwidget_tab_About_gb1_text = QtWidgets.QTextBrowser(self.gb3_tabwidget_tab_About_gb1)
        self.gb3_tabwidget_tab_About_gb1_text.setGeometry(QtCore.QRect(15, 30, 291, 231))
        self.gb3_tabwidget_tab_About_gb1_text.setObjectName("gb3_tabwidget_tab_About_gb1_text")
        self.gb3_tabwidget_tab_About_gb2 = QtWidgets.QGroupBox(self.tab_About)
        self.gb3_tabwidget_tab_About_gb2.setGeometry(QtCore.QRect(340, 10, 1521, 281))
        self.gb3_tabwidget_tab_About_gb2.setObjectName("gb3_tabwidget_tab_About_gb2")
        self.gb3_tabwidget_tab_About_gb2_text = QtWidgets.QTextBrowser(self.gb3_tabwidget_tab_About_gb2)
        self.gb3_tabwidget_tab_About_gb2_text.setGeometry(QtCore.QRect(20, 30, 1481, 231))
        self.gb3_tabwidget_tab_About_gb2_text.setObjectName("gb3_tabwidget_tab_About_gb2_text")
        self.gb3_tabwidget.addTab(self.tab_About, "About")

        self.main_window.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(self.main_window)
        self.statusbar.setObjectName("statusbar")
        self.main_window.setStatusBar(self.statusbar)
        self.actionSave = QtWidgets.QAction(self.main_window)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QtWidgets.QAction(self.main_window)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionBig = QtWidgets.QAction(self.main_window)
        self.actionBig.setObjectName("actionBig")
        self.actionSmall = QtWidgets.QAction(self.main_window)
        self.actionSmall.setObjectName("actionSmall")

        self.main_window.setWindowTitle("TWIPR Dashboard")



        # gb2
        self.gb2.setTitle("Overview")
        self.gb21.setTitle("Connections")

        # gb21_list
        # __sortingEnabled = self.gb21_list.isSortingEnabled()
        # self.gb21_list.setSortingEnabled(__sortingEnabled)

        # gb22
        self.gb22.setTitle("Terminal")
        # gb
        self.gb3.setTitle("Settings")
        self.gb3_tabwidget_tab_About_gb1.setTitle("What is this?")
        self.gb3_tabwidget_tab_About_gb1_text.setHtml(
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">A small explanation.</p>\n"
            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.gb3_tabwidget_tab_About_gb2.setTitle("What should I do?")
        self.gb3_tabwidget_tab_About_gb2_text.setHtml(
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">A guide explaining how to use this application and the robots in the laboratory.</p>\n"
            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">...</p>\n"
            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>")
        self.actionSave.setText("Save")
        self.actionSave.setShortcut("esc+S")
        self.actionSave_As.setText("Save As")
        self.actionBig.setText("Big")
        self.actionSmall.setText("Small")

        # signal and slots
        self.gb22_line.returnPressed.connect(self.process_input_from_main_terminal)

        QtCore.QMetaObject.connectSlotsByName(self.main_window)

    def toggle_gb1_but_flag(self):
        # handle unwanted user behaviour
        if self.clients_number == 0 and not self.gb1_but_flag_stop:
            # send warning popup
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("TWIPR Dashboard")
            popup.setText("Plot empty!")
            popup.setIcon(QtWidgets.QMessageBox.Warning)
            popup.setDetailedText("Please connect a client!")
            popup.setWindowIcon(QtGui.QIcon("Icons/icon_256.png"))
            x = popup.exec_()
        else:
            # change flag to signal plotting stop
            self.gb1_but_flag_stop = not self.gb1_but_flag_stop
            # change color of button to red if plotting has been stopped by the user
            if self.gb1_but_flag_stop:
                self.gb1_but.setStyleSheet("background-color : rgb(180, 0, 0); color : rgb(255, 255, 255)")
            else:
                # set to standard color
                self.gb1_but.setStyleSheet("background-color : rgb(240, 240, 240)")

    def read_from_cmd_history_key_up(self):
        if self.cmd_history:
            if self.cmd_history_reading_index == 0:
                self.cmd_history_reading_index = len(self.cmd_history) - 1
            else:
                self.cmd_history_reading_index -= 1
            cmd = self.cmd_history[self.cmd_history_reading_index]
            self.gb22_line.setText(cmd)
        else:
            pass

    def read_from_cmd_history_key_down(self):
        if self.cmd_history:
            if self.cmd_history_reading_index == len(self.cmd_history):
                self.cmd_history_reading_index = len(self.cmd_history) - 1
            elif self.cmd_history_reading_index == len(self.cmd_history) - 1:
                self.cmd_history_reading_index = 0
            else:
                self.cmd_history_reading_index += 1
            cmd = self.cmd_history[self.cmd_history_reading_index]
            self.gb22_line.setText(cmd)
        else:
            pass

    def read_from_cmd_history_key_esc(self):
        cmd = 'M62'
        self.gb22_line.setText(cmd)

    def read_from_cmd_history_key_f1(self):
        cmd = 'M61'
        self.gb22_line.setText(cmd)

    def read_from_cmd_history_key_f2(self):
        # just an example
        pass

    def add_cmd_to_history(self, cmd):
        # add valid command to history of the main terminal (and all the robot terminals)
        self.write_to_cmd_history(cmd)
        for client_index in range(self.clients_max):
            if self.client_ui_list[client_index] != 0:
                self.client_ui_list[client_index].write_to_cmd_history(cmd)

    def write_to_cmd_history(self, cmd):
        if len(self.cmd_history) < self.cmd_history_limit:
            if len(self.cmd_history) == 0:
                self.cmd_history.append(cmd)
            else:
                if cmd not in self.cmd_history:
                    self.cmd_history.append(cmd)
                else:
                    cmd_index = self.cmd_history.index(cmd)
                    self.cmd_history.pop(cmd_index)
                    self.cmd_history.append(cmd)
        else:
            if cmd not in self.cmd_history:
                self.cmd_history.pop(0)
                self.cmd_history.append(cmd)
            else:
                cmd_index = self.cmd_history.index(cmd)
                self.cmd_history.pop(cmd_index)
                self.cmd_history.append(cmd)
        self.cmd_history_reading_index = len(self.cmd_history)

    def gcode_execution_from_file(self, filename):
        self.clear_main_terminal_line_edit()

        if self.clients_number > 0:
            # open and read config file
            err = txt_handler.open('Miscellaneous/{}.gcode'.format(filename))
            if err:
                self.write_message_to_all_terminals(err, 'R')
                # self.popup_invalid_input_main_terminal(err)
                return

            for processed_line in txt_handler.read():
                if not processed_line:
                    # yields zero in this case
                    self.popup_invalid_input_main_terminal("Configuration file empty!")
                    break

                self.gb22_line.setText(processed_line)
                self.process_input_from_main_terminal()

            err = txt_handler.close()
            if err:
                self.write_message_to_all_terminals(err, 'R')
                # self.popup_invalid_input_main_terminal(err)
                return
        else:
            self.write_message_to_main_terminal("Please connect a client!", 'R')

    def write_gcode_documentation_to_terminal(self) -> None:
        self.clear_main_terminal_line_edit()
        # open and read g-code documentation file
        err = txt_handler.open('Communication/gcode_documentation.txt')
        if err:
            self.write_message_to_all_terminals(err, 'R')
            # self.popup_invalid_input_main_terminal(err)
            return

        for processed_line in txt_handler.read():
            if not processed_line:
                # yields zero in this case
                self.popup_invalid_input_main_terminal("G-code documentation file empty!")
                break

            self.write_message_to_main_terminal(processed_line, 'B')

        err = txt_handler.close()
        if err:
            self.write_message_to_all_terminals(err, 'R')
            # self.popup_invalid_input_main_terminal(err)
            return

    def enter_cmd_into_main_terminal(self, cmd: str, write_to_terminal: bool = True) -> None:
        # this function is used to externally execute g-codes
        self.gb22_line.setText(cmd)
        self.process_input_from_main_terminal(write_to_terminal=write_to_terminal)

    def invalid_gcode(self, user_input: str) -> None:
        string = "Invalid G-code! Please refer to the documentation for further information! (F1)"
        self.write_message_to_all_terminals(user_input, 'W')
        self.write_message_to_all_terminals(string, 'R')
        # self.popup_invalid_input_main_terminal(string)

    def process_input_from_main_terminal(self, write_to_terminal=True):
        # read text from line edit "gb22" and make a list
        line_text = self.gb22_line.text()
        if not line_text:
            self.popup_invalid_input_main_terminal("Please enter a command!")
            return

        self.clear_main_terminal_line_edit()

        # parse input from line edit, the output of the parser is a either a msg for ML/LL or
        # a list of strings containing g-codes that are meant for the HL (internal call)
        gcode_parser_output = gcode_parser.parse(line_text)

        # get the recipient
        combo_text = self.gb22_combo.currentText()

        if type(gcode_parser_output) == list:
            # validity check
            if gcode_parser_output[0]['type'] == 'M60':
                self.invalid_gcode(line_text)
                return

            self.execute_internal_call(gcode_parser_output, write_to_terminal, line_text)  # HL -> HL
        else:
            if write_to_terminal:
                self.write_message_to_all_terminals(line_text, 'W')
            self.send_message_from_main_terminal(gcode_parser_output, write_to_terminal, line_text)  # HL -> ML/LL

        self.add_cmd_to_history(line_text)

    def send_message_from_main_terminal(self, msg, write_to_terminal, line_text):
        # get the respective receivers first
        combo_text = self.gb22_combo.currentText()
        if self.clients_number > 0:
            if combo_text == "All":
                for client_index in range(self.clients_max):
                    if self.client_list[client_index] != 0:
                        if self.send_message(client_index, msg) == 1:
                            # write sent command to terminal
                            if write_to_terminal:
                                self.write_sent_command_to_terminals(client_index, line_text, "Y")
                        else:
                            # write error message to terminals
                            self.write_sent_command_to_terminals(client_index, line_text, "R")
                            self.write_message_to_terminals(client_index, "Failed to sent message!", "R")
            else:
                for client_index in range(self.clients_max):
                    string = "TWIPR_" + str(client_index)
                    if combo_text == string:
                        if self.client_list[client_index] != 0:  # don't send if client has disconnected
                            if self.send_message(client_index, msg) == 1:
                                # write sent command to terminal
                                if write_to_terminal:
                                    self.write_sent_command_to_terminals(client_index, line_text, "Y")
                            else:
                                # write error message to terminals
                                self.write_sent_command_to_terminals(client_index, line_text, "R")
                                self.write_message_to_terminals(client_index, "Failed to sent message!", "R")
                        else:
                            self.popup_invalid_input_main_terminal("{} not connected!".format(combo_text))
            # clear the line edit
            self.gb22_line.setText("")
        else:
            # warning popup
            self.popup_invalid_input_main_terminal("Please connect a client!")

    def execute_internal_call(self, cmd_list: List[Dict[str, Any]], write_to_terminal: bool, line_text: str) -> None:
        # the cmd list comprises dictionaries containing a g-code and its arguments respectively
        for gcode in cmd_list:
            if gcode['type'] == 'M61':
                # command limited to main terminal
                self.write_message_to_main_terminal(line_text, 'W')
                self.write_gcode_documentation_to_terminal()

            elif gcode['type'] == 'M62':
                self.write_message_to_main_terminal(line_text, 'W')
                self.clear_main_terminal()

            elif gcode['type'] == 'M63':
                # command can affect all clients, therefore, write to all terminals
                self.write_message_to_all_terminals(line_text, 'W')
                self.gcode_execution_from_file(gcode['filename'])

            elif gcode['type'] == 'M64':
                self.write_message_to_main_terminal(line_text, 'W')
                self.display_robot_data()

            # TODO: TEST START
            elif gcode['type'] == 'M65':
                self.write_message_to_all_terminals(line_text, 'W')

                # connection guard
                if not self.clients_number > 0:
                    self.write_message_to_main_terminal("Please connect a client!", 'R')
                    return

                msg = experiment_handler.load_experiment(gcode['filename'])
                if not msg:
                    self.write_message_to_main_terminal("Failed loading experiment!", "R")
                    return
                self.send_message_from_main_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M66':
                msg, start_gcodes = experiment_handler.start_experiment(gcode['filename'])
                # execute commands before starting the experiment
                for cmd in start_gcodes:
                    self.enter_cmd_into_main_terminal(cmd)
                # then start experiment
                self.send_message_from_main_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M67':
                msg_load, msg_start = experiment_handler.load_and_start_experiment(gcode['filename'])
                if not msg_load:
                    self.write_message_to_main_terminal("Failed loading experiment!", "R")
                    return
                self.send_message_from_main_terminal(msg_load, write_to_terminal, line_text)
                self.send_message_from_main_terminal(msg_start, False, line_text)

            elif gcode['type'] == 'M68':
                msg = experiment_handler.end_experiment(gcode['filename'])
                self.send_message_from_main_terminal(msg, write_to_terminal, line_text)
            # TODO: TEST END

            elif gcode['type'] == 'M69':
                self.write_message_to_all_terminals(line_text, 'W')

                # connection guard
                if not self.clients_number > 0:
                    self.write_message_to_main_terminal("Please connect a client!", 'R')
                    return

                msg = sequence_handler.load_sequence(gcode['filename'])
                if not msg:
                    self.write_message_to_main_terminal("Failed loading sequence!", "R")
                    return
                self.send_message_from_main_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M70':
                self.write_message_to_all_terminals(line_text, 'W')

                # connection guard
                if not self.clients_number > 0:
                    self.write_message_to_main_terminal("Please connect a client!", 'R')
                    return

                msg = sequence_handler.start_sequence(gcode['filename'])
                self.send_message_from_main_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M71':
                self.write_message_to_all_terminals(line_text, 'W')

                # connection guard
                if not self.clients_number > 0:
                    self.write_message_to_main_terminal("Please connect a client!", 'R')
                    return

                msg_load, msg_start = sequence_handler.load_and_start_sequence(gcode['filename'])
                if not msg_load:
                    self.write_message_to_main_terminal("Failed loading sequence!", "R")
                    return
                self.send_message_from_main_terminal(msg_load, write_to_terminal, line_text)
                self.send_message_from_main_terminal(msg_start, False, line_text)

            elif gcode['type'] == 'M72':
                self.write_message_to_all_terminals(line_text, 'W')

                # connection guard
                if not self.clients_number > 0:
                    self.write_message_to_main_terminal("Please connect a client!", 'R')
                    return

                msg = sequence_handler.end_sequence(gcode['filename'])
                self.send_message_from_main_terminal(msg, write_to_terminal, line_text)

            else:
                pass

    def write_message_to_all_terminals(self, line_text, color):
        if self.clients_number == 0:
            # if no client connected, just write to the main terminal
            self.write_message_to_main_terminal(line_text, color)
        else:
            # write to all terminal windows correctly
            client_indices = self.get_client_indices_from_combo_box()
            for client_index in client_indices:
                self.write_message_to_terminals(client_index, line_text, color)

    def get_robot_ui_objects_from_combo_box(self):
        client_indices = self.get_client_indices_from_combo_box()
        robot_ui_objects = []
        for index in client_indices:
            robot_ui_objects.append(self.client_ui_list[index])

        return robot_ui_objects

    def get_client_indices_from_combo_box(self):
        combo_text = self.get_combo_text()
        if combo_text == 'All':
            client_indices = self.get_all_client_indices()
        else:
            client_indices = [int(combo_text[-1])]

        return client_indices

    def get_combo_text(self):
        return self.gb22_combo.currentText()

    def get_all_client_indices(self):
        client_indices = []
        for client in self.client_ui_list:
            if client:
                client_indices.append(client.client_index)

        return client_indices

    def clear_main_terminal(self):
        self.clear_main_terminal_list_view()
        self.clear_main_terminal_line_edit()

    def clear_main_terminal_list_view(self):
        # clear command window (clc)
        self.gb22_list.clear()

    def clear_main_terminal_line_edit(self):
        # clear the line edit
        self.gb22_line.setText('')

    def popup_invalid_input_main_terminal(self, e):
        # clear the line edit
        self.gb22_line.setText("")
        # and send warning popup
        popup = QtWidgets.QMessageBox()
        popup.setWindowTitle("TWIPR Dashboard")
        popup.setText("Invalid user input!")
        popup.setIcon(QtWidgets.QMessageBox.Warning)
        popup.setDetailedText(str(e))
        popup.setWindowIcon(QtGui.QIcon("Icons/icon_256.png"))
        x = popup.exec_()

    def display_robot_data(self) -> None:
        # M64
        self.clear_main_terminal_line_edit()

        if self.clients_number > 0:
            robot_ui_objects = self.get_robot_ui_objects_from_combo_box()
            for robot_ui in robot_ui_objects:
                string = robot_ui.get_robot_data_string()
                self.write_message_to_main_terminal(string, 'W')
        else:
            self.write_message_to_main_terminal("Please connect a client!", 'R')

    def get_all_client_ui_object(self):
        client_ui_objects = []
        for client in self.client_ui_list:
            if client:
                client_ui_objects.append(client)

    def write_message_to_terminals(self, client_index, string, color):
        main_terminal_string = "TWIPR_{} - {}".format(client_index, string)
        self.write_message_to_main_terminal(main_terminal_string, color)
        self.client_ui_list[client_index].write_message_to_robot_terminal(string, color)

    def write_message_to_main_terminal(self, string, color):
        # write message to main terminal that robot has been connected
        item = QtWidgets.QListWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

        time_now = datetime.now().strftime("%H:%M:%S") + ": "
        item.setText(time_now + string)
        # check color
        if color == "G":  # new client, new message, ...
            item.setForeground(QtCore.Qt.green)
        elif color == "R":  # error messages
            item.setForeground(QtCore.Qt.red)
        elif color == "Y":  # sent messages
            item.setForeground(QtCore.Qt.yellow)
        elif color == "B":  # G-Code documentation
            item.setForeground(QtCore.Qt.cyan)
        self.gb22_list.addItem(item)
        # auto scroll
        self.gb22_list.scrollToBottom()

    def write_sent_command_to_terminals(self, client_index, string, color):
        self.write_sent_command_to_main_terminal(client_index, string, color)
        self.client_ui_list[client_index].write_sent_command_to_robot_terminal(client_index, string, color)

    def write_sent_command_to_main_terminal(self, client_index, string, color):
        string = "[S] TWIPR_" + str(client_index) + " - " + string
        self.write_message_to_main_terminal(string, color)

    def write_received_msg_to_terminals(self, client_index, string, color):
        self.write_received_msg_to_main_terminal(client_index, string, color)
        self.client_ui_list[client_index].write_received_msg_to_robot_terminal(client_index, string, color)

    def write_received_msg_to_main_terminal(self, client_index, string, color):
        string = "[R] TWIPR_" + str(client_index) + " - " + string
        self.write_message_to_main_terminal(string, color)

    def calculate_coordinates(self, client_index):
        delta_x = self.client_ui_list[client_index].data.x - self.client_ui_list[client_index].data.last_x

        self.client_ui_list[client_index].data.x_coordinate = delta_x * np.sin(
            self.client_ui_list[client_index].data.psi) + self.client_ui_list[client_index].data.x_coordinate
        self.client_ui_list[client_index].data.y_coordinate = delta_x * np.cos(
            self.client_ui_list[client_index].data.psi) + self.client_ui_list[client_index].data.y_coordinate

    def plot_robot_map(self):
        if self.gb1_cached_bg is None:
            # cache background
            self.gb1_cached_bg = self.gb1_canvas.copy_from_bbox(self.gb1_figure.bbox)
        elif self.clients_number > 0:
            # check if plot reference has been created already
            for i in range(self.clients_max):
                if self.client_ui_list[i] != 0:
                    if self.client_ui_list[i].gb1_plot_ref is None:
                        # unpack returned line list
                        self.client_ui_list[i].gb1_plot_ref, = self.gb1_ax.plot(self.client_ui_list[i].robot.state.x,
                                                                                self.client_ui_list[i].robot.state.y,
                                                                                marker=".",
                                                                                markersize=10,
                                                                                label="TWIPR_" + str(
                                                                                    self.client_ui_list[
                                                                                        i].client_index),
                                                                                animated=True)
                        # update legend and draw everything
                        self.gb1_legend = self.gb1_ax.legend(loc="upper right", fontsize="x-small")
                        self.gb1_canvas.draw()
                        # adjust background
                        self.gb1_cached_bg = self.gb1_canvas.copy_from_bbox(self.gb1_figure.bbox)
                        # add artist to list for plotting
                        self.gb1_artists.append(self.client_ui_list[i].gb1_plot_ref)
                    else:
                        # update data if reference is available and if stop button has not been pressed
                        if not self.gb1_but_flag_stop:
                            self.client_ui_list[i].gb1_plot_ref.set_xdata(self.client_ui_list[i].robot.state.x)
                            self.client_ui_list[i].gb1_plot_ref.set_ydata(self.client_ui_list[i].robot.state.y)
                            # bring back cached background
                            self.gb1_canvas.restore_region(self.gb1_cached_bg)
                        # draw artists only
                        for a in self.gb1_artists:
                            self.gb1_figure.draw_artist(a)
            # show on screen
            self.gb1_canvas.blit(self.gb1_figure.bbox)
            # process pending tasks from matplotlib event loop
            self.gb1_canvas.flush_events()

    def timeout(self):
        # print("Time elapsed between timeouts: {:.5} ms".format(time.perf_counter_ns()/1000/1000-self.time_point))
        # (0) log the data
        count = 0
        for i in range(self.clients_max):
            if self.client_ui_list[i] != 0:
                self.client_ui_list[i].robot.data_logs.log()
                count += 1
                if count == self.clients_number:
                    break
        # (1) update upper part of ui (robot map)
        self.plot_robot_map()
        # (2) update lower part of ui (in the respective robot tab)
        # ---- check the tab that is opened in the main tabwidget currently
        tab_name = self.check_robot_tab()
        self.robot_timeout(tab_name)
        # self.time_point = time.perf_counter_ns() / 1000 / 1000  # ms

        # (3) process events
        self.joystick_handler.process_events()

    def check_robot_tab(self):
        # return the index of the robot that is opened currently
        tab_index = self.gb3_tabwidget.currentIndex()
        if tab_index == 0:
            # constant index
            return "About"
        else:
            # indices of robot tabs above zero could be interchanged
            # >>> check which robot has which page index
            # (0) get page object
            tab_object = self.gb3_tabwidget.widget(tab_index)
            # (1) loop through following dictionary to get the client index of the respective robot
            for key, value in self.tab_dict.items():
                if tab_object == value:
                    # (2) extract the client index from the string
                    client_index = key[-1]
            client_name = "TWIPR_" + client_index
            return client_name

    def robot_timeout(self, tab_name):
        if tab_name == "About":
            pass
        elif tab_name == "TWIPR_0":
            self.client_ui_list[0].timeout()
        elif tab_name == "TWIPR_1":
            self.client_ui_list[1].timeout()
        elif tab_name == "TWIPR_2":
            self.client_ui_list[2].timeout()
        elif tab_name == "TWIPR_3":
            self.client_ui_list[3].timeout()
        elif tab_name == "TWIPR_4":
            self.client_ui_list[4].timeout()
        elif tab_name == "TWIPR_5":
            self.client_ui_list[5].timeout()
        elif tab_name == "TWIPR_6":
            self.client_ui_list[6].timeout()
        elif tab_name == "TWIPR_7":
            self.client_ui_list[7].timeout()
        elif tab_name == "TWIPR_8":
            self.client_ui_list[8].timeout()
        elif tab_name == "TWIPR_9":
            self.client_ui_list[9].timeout()

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    Ui = Command_Ui()
    sys.exit(app.exec())
    Ui = Command_Ui()
