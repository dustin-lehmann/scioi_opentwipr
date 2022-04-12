############################################################################
##                                                                        ##
## Supervisor:          Dustin Lehmann                                    ##
## Author:              David Stoll                                       ##
## Creation Date:       12.02.2021                                        ##
## Description:         Host script that runs on a Windows Machine        ##
##                      with PyQt5 installed already                      ##
##                                                                        ##
############################################################################

from Experiment.experiment import sequence_handler, experiment_handler
from Ui.general import TerminalLineEdit

# PyQt
from PyQt5 import QtWidgets, QtCore, QtGui

# Plotting
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

# GCode
from Communication.gcode_parser import gcode_parser

import sys
from IO.file_handlers import txt_handler
from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, Any

from datetime import datetime


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_me()

    def init_me(self):

        self.Terminal = TerminalLineEdit(self)
        """
        self.Terminal.set_functions(self.read_from_cmd_history_key_up,
                                     self.read_from_cmd_history_key_down,
                                     self.read_from_cmd_history_key_esc,
                                     self.read_from_cmd_history_key_f1,
                                     self.read_from_cmd_history_key_f2)
        """
        self.Terminal.returnPressed.connect(self.process_input_from_main_terminal)

        #Liste
        self.gb22_list = QtWidgets.QListWidget(self.layoutWidget)
        self.gb22_list.setPalette(palette)
        self.gb22_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.gb22_list.setObjectName("gb22_list")
        self.gb22_horlay.addWidget(self.gb22_list)

        self.setGeometry(50, 50, 1000, 500)
        self.setWindowTitle("Terminal TestBed")
        self.show()

    def gedrueckt(self):
        print("Button gedrueckt")

    # Terminal commands

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

                self.Terminal.setText(processed_line)
                self.process_input_from_main_terminal()

            err = txt_handler.close()
            if err:
                self.write_message_to_all_terminals(err, 'R')
                # self.popup_invalid_input_main_terminal(err)
                return
        else:
            self.write_message_to_main_terminal("Please connect a client!", 'R')

    def process_input_from_main_terminal(self, write_to_terminal=True):
        """
        read the text from line edit (terminal) and make a list
        :param write_to_terminal: if not stated otherwise processing of the command is displayed on terminal
        :return: nothing
        """
        # get text from terminal
        line_text = self.Terminal.text()
        # check if there has been an input
        if not line_text:
            self.popup_invalid_input_main_terminal("Please enter a command!")
            return

        self.clear_main_terminal_line_edit()

        # parse input from line edit
        # the output of the parser is a either a msg for ML/LL or
        # a list of strings containing g-codes that are meant for the HL (internal call)
        gcode_parser_output = gcode_parser.parse(line_text)

        # get the recipient from combo box
        #        combo_text = self.gb22_combo.currentText() # Nicht nötig, da momentan nur 1 Robot connected #todo: uncomment + add possibility for multiple robots
        combo_text = 'all'
        # check if internal command
        if type(gcode_parser_output) == list:
            # validity check - if command is not in gcode-format the parser returns M60, the gcode is invalid
            if gcode_parser_output[0]['type'] == 'M60':
                self.invalid_gcode(line_text)
                return
            else:
                # validity check has been passed, execute command according to command list
                self.execute_internal_call(gcode_parser_output, write_to_terminal, line_text)  # HL -> HL

        # external command
        else:
            if write_to_terminal:
                self.write_message_to_all_terminals(line_text, 'W')
            self.send_message_from_main_terminal(gcode_parser_output, write_to_terminal, line_text)  # HL -> ML/LL

        self.add_cmd_to_history(line_text)

    def send_message_from_main_terminal(self, msg, write_to_terminal, line_text):
        """
        get the respective receivers first
        :param msg: parsed message (gcode)
        :param write_to_terminal: boolean, if true information is displayed on terminal
        :param line_text: text of input
        :return: nothing
        """

        combo_text = self.gb22_combo.currentText()
        if self.clients_number > 0:
            # send message to every client
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

            # send message to selected client (compare with combo_text)
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
            self.Terminal.setText("")
        else:
            # warning popup
            self.popup_invalid_input_main_terminal("Please connect a client!")

    def clear_main_terminal_line_edit(self):
        """
        clear the input line of terminal
        :return: nothing
        """
        self.Terminal.setText('')

    def invalid_gcode(self, user_input: str) -> None:
        """
        called when gcode is invalid, writes to console that used code is not valid
        :param user_input: the string the user has put in that is not a valid gcode
        :return: nothing
        """
        string = "Invalid G-code! Please refer to the documentation for further information! (F1)"
        print(string)

    def execute_internal_call(self, cmd_list: List[Dict[str, Any]], write_to_terminal: bool, line_text: str) -> None:
        """
        execute internal call (GCODE Mxx)
        :param cmd_list: comprises dictionaries containing a g-code and its arguments respectively
        :param write_to_terminal: boolean, if true information is displayed on terminal
        :param line_text: text of command
        :return: nothing
        """

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

    def write_message_to_main_terminal(self, string, color):
        """
        Write a message in a specific color to main terminal
        :param string: message
        :param color: color of the message displayed on terminal
        :return: nothing
        """
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


app = QtWidgets.QApplication(sys.argv)

w = Window()

sys.exit(app.exec_())
