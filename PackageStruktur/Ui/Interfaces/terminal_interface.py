############################################################################
##                                                                        ##
## Supervisor:          Dustin Lehmann                                    ##
## Author:              David Stoll                                       ##
## Creation Date:       12.04.2022                                        ##
## Description:         Terminal Interface                                ##
##                                                                        ##
##                                                                        ##
############################################################################
import string

import numpy as np

from Experiment.experiment import sequence_handler, experiment_handler
from Ui.general import TerminalLineEdit

# PyQt
from PyQt5 import QtWidgets, QtCore, QtGui


import sys
from IO.file_handlers import txt_handler

from datetime import datetime


class TerminalInterface(QtWidgets.QWidget):

    # -------------------------------------------------------Signals-------------------------------------------------

    # define the signals that are used to communicate with the HostServer
    user_gcode_input_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_terminal()

    def init_terminal(self):
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setWindowIcon(QtGui.QIcon("Icons/TU_Logo_kurz_RGB_rot.jpg"))
        self.main_window.showMaximized()
        self.main_window.show()

        self.main_window.setObjectName("self.main_window")
        self.main_window.resize(1945, 500)
        self.main_window.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.centralwidget = QtWidgets.QWidget(self.main_window)
        self.centralwidget.setObjectName("centralwidget")

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
        text_string = "Please activate a TWIPR and connect to the HL! HL is listening on {}:{}!".format(0,
                                                                                                   0)

        self.write_message_to_main_terminal(text_string, "W")

        self.gb22_horlay.addWidget(self.gb22_list)
        self.gb22_verlay = QtWidgets.QHBoxLayout()
        self.gb22_verlay.setObjectName("gb22_verlay")
        self.gb22_line = TerminalLineEdit(self.layoutWidget)
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

        #signals
        self.gb22_line.returnPressed.connect(self.process_input_from_terminal) #todo: hier wird terminal command abgearbeitet

        self.main_window.setCentralWidget(self.centralwidget)

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

    def process_input_from_terminal(self, write_to_terminal=True):
        """
        -read text from line edit "gb22" and make a list
        -this function is used as a slot to connected with the Signal that is emitted once return is pressed in Terminal
        -the function emits another Signal with the read line text, this signal is connected to the HostServer instance
            where the input is handled
        :param write_to_terminal: determines if command handling is displayed on the Terminal
        :return: nothing
        """

        line_text = self.gb22_line.text()
        if not line_text:
            self.popup_invalid_input_main_terminal("Please enter a command!")
            return
        self.user_gcode_input_signal.emit(line_text)

        self.clear_main_terminal_line_edit()

    def write_message_to_all_terminals(self, line_text, color):
        if self.clients_number == 0:
            # if no client connected, just write to the main terminal
            self.write_message_to_main_terminal(line_text, color)
        else:
            # write to all terminal windows correctly
            client_indices = self.get_client_indices_from_combo_box()
            for client_index in client_indices:
                self.write_message_to_terminals(client_index, line_text, color)


    def get_client_indices_from_combo_box(self):
        """
        get from combo Box to which client a Message is supposed to be sent
        #todo: not implemented yet since I dont use a Combo box with my terminal
        :return: index of client
        """
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
        """
        clear the input-line of main Terminal
        :return: nothing
        """
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

    # Interface specific Signal connections:
    def new_connection(self, peer_address, peer_port):
        string = "New Connection from {}, on Port: {}".format(peer_address, peer_port)
        self.write_message_to_main_terminal(string, "G")


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    w = TerminalInterface()
    w.write_message_to_main_terminal("Hallo", "R")

    sys.exit(app.exec_())
