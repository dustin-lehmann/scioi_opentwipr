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
        """
        self.Terminal.set_functions(self.read_from_cmd_history_key_up,
                                     self.read_from_cmd_history_key_down,
                                     self.read_from_cmd_history_key_esc,
                                     self.read_from_cmd_history_key_f1,
                                     self.read_from_cmd_history_key_f2)
        """
        self.Terminal.returnPressed.connect(self.process_input_from_main_terminal)

        self.setGeometry(50, 50, 1000, 500)
        self.setWindowTitle("My first GUI")
        self.show()

    def gedrueckt(self):
        print("Button gedrueckt")

#Terminal commands

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
        read the text from line edit(terminal) and make a list
        :param write_to_terminal:
        :return:
        """
        line_text = self.Terminal.text()
        if not line_text:
            self.popup_invalid_input_main_terminal("Please enter a command!")
            return

        self.clear_main_terminal_line_edit()

        # parse input from line edit, the output of the parser is a either a msg for ML/LL or
        # a list of strings containing g-codes that are meant for the HL (internal call)
        gcode_parser_output = gcode_parser.parse(line_text)

        # get the recipient
#        combo_text = self.gb22_combo.currentText() # Nicht nötig, da momentan nur 1 Robot connected #todo: uncomment und

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

    def clear_main_terminal_line_edit(self):
        """
        clear the input line of terminal so user can type in next command
        :return:
        """
        self.Terminal.setText('')

    def invalid_gcode(self, user_input: str) -> None:
        string = "Invalid G-code! Please refer to the documentation for further information! (F1)"
        print(string)

app = QtWidgets.QApplication(sys.argv)


w = Fenster()

sys.exit(app.exec_())