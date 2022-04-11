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




class Fenster(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initMe()

    def initMe(self):


        self.Terminal = TerminalLineEdit(self)
        self.Terminal.set_functions(self.read_from_cmd_history_key_up,
                                     self.read_from_cmd_history_key_down,
                                     self.read_from_cmd_history_key_esc,
                                     self.read_from_cmd_history_key_f1,
                                     self.read_from_cmd_history_key_f2)

        self.Terminal.returnPressed.connect(self.process_input_from_main_terminal)

        self.setGeometry(50, 50, 1000, 500)
        self.setWindowTitle("My first GUI")
        self.show()

    def gedrueckt(self):
        print("Button gedrueckt")

#Terminal commands

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


app = QtWidgets.QApplication(sys.argv)


w = Fenster()

sys.exit(app.exec_())