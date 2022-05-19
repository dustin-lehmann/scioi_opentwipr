# PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtNetwork import *

# Type hints
from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, Any

# Plotting
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from datetime import datetime
import time

# my imports
from Communication.general import *
from Communication.gcode_parser import gcode_parser
from Ui.general import TerminalLineEdit
from Ui.robot_plots import *
from Robot.data import *
from IO.file_handlers import txt_handler
from Experiment.experiment import experiment_handler, sequence_handler


class RobotUi:
    """
    RobotUi is the user interface class that is responsible for interaction with the robots.
    The robot user interface is located in the lower half of the screen and it is created for
    every connected TWIPR.
    """

    joystick_instance_id: int
    joystick_enable: bool

    def __init__(self, main_ui_object, client_index):
        # pass main ui object and index of client
        self.main_ui_object = main_ui_object
        self.client_index = client_index
        self.client_name = "TWIPR_" + str(self.client_index)
        
        # settings for detecting TWIPR death
        self.check_heartbeat_interval = int(10/0.1)  # check every 10 seconds
        self.check_heartbeat_counter = 0
        self.check_heartbeat_flag = 0

        # hack to avoid a flashing checkbox when changing ctrl states (gb3/gb4 in robot ui)
        self.update_checkboxes_flag = True

        # command history for repeating previously used commands in the robot terminal
        self.cmd_history_limit = 10
        self.cmd_history = []
        self.cmd_history_reading_index = 0

        # container for robot data
        self.robot = Robot(self.main_ui_object.refresh_time_ms)

        # instance id of assigned joystick and joystick button enable
        self.joystick_instance_id = -1
        self.joystick_enable = False

        # PLOT REFERENCES
        # gb1 robot map
        self.gb1_plot_ref = None

        # (2) fill out the robot ui
        # make a new list widget item object for the list "Connections" and insert it
        # create the key for the respective ui dictionary
        self.gb21_list_item_object_name = "gb21_list_item" + str(self.client_index)
        self.main_ui_object.gb21_list_item_dict[self.gb21_list_item_object_name] = QtWidgets.QListWidgetItem()
        self.main_ui_object.gb21_list_item_dict[self.gb21_list_item_object_name].setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        self.main_ui_object.gb21_list_item_dict[self.gb21_list_item_object_name].setText(self.client_name)
        self.main_ui_object.gb21_list.addItem(self.main_ui_object.gb21_list_item_dict[self.gb21_list_item_object_name])
        # add a new item to gb22_combo (this is the drop-down menu of the main terminal)
        self.main_ui_object.gb22_combo.addItem(self.client_name)
        # make a new tab page object
        # create the key for the respective ui dictionary
        self.tab_object_name = "tab_" + str(self.client_index)
        self.main_ui_object.tab_dict[self.tab_object_name] = QtWidgets.QWidget()
        self.main_ui_object.tab_dict[self.tab_object_name].setObjectName(self.tab_object_name)
        self.tab_index = self.main_ui_object.gb3_tabwidget.insertTab(self.client_index+1, self.main_ui_object.tab_dict[self.tab_object_name], "")
        # self.main_ui_object.gb3_tabwidget.setCurrentIndex(self.tab_index)

        # create key for respective tab and make a reference to the tab object
        # self.tab_object_name = "tab_" + str(self.client_index)
        self.tab_object = self.main_ui_object.tab_dict[self.tab_object_name]

        # create a dictionary that will hold all pages of the gb2 tabwidget
        self.keys = ['tab_0', 'tab_1', 'tab_2', 'tab_3', 'tab_4']
        self.gb2_tab_dict = {}

        # ============================================================================================================================================
        # fill respective robot tab with robot ui
        # !!! if something has to be added or changed !!!
        # (1) replace the referencing tab of the 4 GBs with "self.tab_object"
        # (2) 10 widgets ahve been added to gb3 tabwidget already, so do not more (only if you know what you are doing)
        # (3) centralwidget is from main ui class
        # (4) gb3_tabwidget is from main ui class
        # (5) set tab index at the end !!!!! otherwise the ui will not show up
        # >>> that's it I would say, nothing more to know when changing code in this section here
        self.main_ui_object.gb3_tabwidget.setTabText(self.client_index+1, self.client_name)

        # gb3_tabwidget_gb1
        self.gb3_tabwidget_tab_twipr_gb1 = QtWidgets.QGroupBox(self.tab_object)
        self.gb3_tabwidget_tab_twipr_gb1.setEnabled(True)
        self.gb3_tabwidget_tab_twipr_gb1.setGeometry(QtCore.QRect(12, 11, 711, 451))
        self.gb3_tabwidget_tab_twipr_gb1.setObjectName("gb3_tabwidget_tab_twipr_gb1")
        # gb3_tabwidget_gb11
        self.gb3_tabwidget_tab_twipr_gb11 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb1)
        self.gb3_tabwidget_tab_twipr_gb11.setGeometry(QtCore.QRect(10, 20, 691, 91))
        self.gb3_tabwidget_tab_twipr_gb11.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb11.setObjectName("gb3_tabwidget_tab_twipr_gb11")
        self.layoutWidget1 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb11)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 20, 671, 65))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget1)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.gb3_tabwidget_tab_twipr_gb11_label1 = QtWidgets.QLabel(self.layoutWidget1)
        self.gb3_tabwidget_tab_twipr_gb11_label1.setObjectName("gb3_tabwidget_tab_twipr_gb11_label1")
        self.gridLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb11_label1, 0, 0, 1, 1)
        self.line_17 = QtWidgets.QFrame(self.layoutWidget1)
        self.line_17.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_17.setLineWidth(1)
        self.line_17.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_17.setObjectName("line_17")
        self.gridLayout.addWidget(self.line_17, 0, 1, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb11_label2 = QtWidgets.QLabel(self.layoutWidget1)
        self.gb3_tabwidget_tab_twipr_gb11_label2.setObjectName("gb3_tabwidget_tab_twipr_gb11_label2")
        self.gridLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb11_label2, 0, 5, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb11_but1 = QtWidgets.QPushButton(self.layoutWidget1)
        self.gb3_tabwidget_tab_twipr_gb11_but1.setObjectName("gb3_tabwidget_tab_twipr_gb11_but1")
        self.gb3_tabwidget_tab_twipr_gb11_but1.setStyleSheet("background-color : rgb(240, 240, 240)")
        self.gridLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb11_but1, 1, 2, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb11_but2 = QtWidgets.QPushButton(self.layoutWidget1)
        self.gb3_tabwidget_tab_twipr_gb11_but2.setObjectName("gb3_tabwidget_tab_twipr_gb11_but2")
        self.gb3_tabwidget_tab_twipr_gb11_but2.setStyleSheet("background-color : rgb(240, 240, 240)")
        self.gridLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb11_but2, 1, 5, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb11_label3 = QtWidgets.QLabel(self.layoutWidget1)
        self.gb3_tabwidget_tab_twipr_gb11_label3.setObjectName("gb3_tabwidget_tab_twipr_gb11_label3")
        self.gridLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb11_label3, 0, 2, 1, 1)
        self.line_18 = QtWidgets.QFrame(self.layoutWidget1)
        self.line_18.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_18.setLineWidth(1)
        self.line_18.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_18.setObjectName("line_18")
        self.gridLayout.addWidget(self.line_18, 1, 1, 1, 1)
        self.line_20 = QtWidgets.QFrame(self.layoutWidget1)
        self.line_20.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_20.setLineWidth(1)
        self.line_20.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_20.setObjectName("line_20")
        self.gridLayout.addWidget(self.line_20, 0, 3, 1, 1)
        self.line_21 = QtWidgets.QFrame(self.layoutWidget1)
        self.line_21.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_21.setLineWidth(1)
        self.line_21.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_21.setObjectName("line_21")
        self.gridLayout.addWidget(self.line_21, 1, 3, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb11_but3 = QtWidgets.QPushButton(self.layoutWidget1)
        self.gb3_tabwidget_tab_twipr_gb11_but3.setObjectName("gb3_tabwidget_tab_twipr_gb11_but3")
        self.gridLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb11_but3, 1, 0, 1, 1)
        
        # gb3_tabwidget_gb12
        self.gb3_tabwidget_tab_twipr_gb12 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb1)
        self.gb3_tabwidget_tab_twipr_gb12.setGeometry(QtCore.QRect(10, 120, 691, 321))
        self.gb3_tabwidget_tab_twipr_gb12.setObjectName("gb3_tabwidget_tab_twipr_gb12")
        self.layoutWidget_2 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb12)
        self.layoutWidget_2.setGeometry(QtCore.QRect(10, 20, 671, 291))
        self.layoutWidget_2.setObjectName("layoutWidget_2")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.layoutWidget_2)
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.gb3_tabwidget_tab_twipr_gb12_list = QtWidgets.QListWidget(self.layoutWidget_2)
        self.gb3_tabwidget_tab_twipr_gb12_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
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
        self.gb3_tabwidget_tab_twipr_gb12_list.setPalette(palette)
        self.gb3_tabwidget_tab_twipr_gb12_list.setObjectName("gb3_tabwidget_tab_twipr_gb12_list")
        self.verticalLayout_13.addWidget(self.gb3_tabwidget_tab_twipr_gb12_list)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.gb3_tabwidget_tab_twipr_gb12_line = TerminalLineEdit(self.layoutWidget_2)
        self.gb3_tabwidget_tab_twipr_gb12_line.set_functions(self.read_from_cmd_history_key_up,
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
        self.gb3_tabwidget_tab_twipr_gb12_line.setPalette(palette)
        self.gb3_tabwidget_tab_twipr_gb12_line.setObjectName("gb3_tabwidget_tab_twipr_gb12_line")
        self.gb3_tabwidget_tab_twipr_gb12_line.setPlaceholderText("Enter command")
        self.horizontalLayout_3.addWidget(self.gb3_tabwidget_tab_twipr_gb12_line)
        self.verticalLayout_13.addLayout(self.horizontalLayout_3)

        # gb3_tabwidget_gb4
        self.gb3_tabwidget_tab_twipr_gb4 = QtWidgets.QGroupBox(self.tab_object)
        self.gb3_tabwidget_tab_twipr_gb4.setEnabled(True)
        self.gb3_tabwidget_tab_twipr_gb4.setGeometry(QtCore.QRect(1370, 260, 491, 201))
        self.gb3_tabwidget_tab_twipr_gb4.setCheckable(True)
        self.gb3_tabwidget_tab_twipr_gb4.setChecked(False)
        self.gb3_tabwidget_tab_twipr_gb4.setObjectName("gb3_tabwidget_tab_twipr_gb4")
        self.gb3_tabwidget_tab_twipr_gb41 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb4)
        self.gb3_tabwidget_tab_twipr_gb41.setGeometry(QtCore.QRect(10, 20, 471, 51))
        self.gb3_tabwidget_tab_twipr_gb41.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb41.setObjectName("gb3_tabwidget_tab_twipr_gb41")
        self.layoutWidget_7 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb41)
        self.layoutWidget_7.setGeometry(QtCore.QRect(10, 20, 451, 21))
        self.layoutWidget_7.setObjectName("layoutWidget_7")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.layoutWidget_7)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.verticalLayout_18 = QtWidgets.QVBoxLayout()
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.gb3_tabwidget_tab_twipr_gb41_label1 = QtWidgets.QLabel(self.layoutWidget_7)
        self.gb3_tabwidget_tab_twipr_gb41_label1.setObjectName("gb3_tabwidget_tab_twipr_gb41_label1")
        self.verticalLayout_18.addWidget(self.gb3_tabwidget_tab_twipr_gb41_label1)
        self.horizontalLayout_7.addLayout(self.verticalLayout_18)
        self.line_7 = QtWidgets.QFrame(self.layoutWidget_7)
        self.line_7.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_7.setLineWidth(1)
        self.line_7.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_7.setObjectName("line_7")
        self.horizontalLayout_7.addWidget(self.line_7)
        self.verticalLayout_19 = QtWidgets.QVBoxLayout()
        self.verticalLayout_19.setObjectName("verticalLayout_19")
        self.gb3_tabwidget_tab_twipr_gb41_label2 = QtWidgets.QLabel(self.layoutWidget_7)
        self.gb3_tabwidget_tab_twipr_gb41_label2.setObjectName("gb3_tabwidget_tab_twipr_gb41_label2")
        self.verticalLayout_19.addWidget(self.gb3_tabwidget_tab_twipr_gb41_label2)
        self.horizontalLayout_7.addLayout(self.verticalLayout_19)
        self.gb3_tabwidget_tab_twipr_gb42 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb4)
        self.gb3_tabwidget_tab_twipr_gb42.setGeometry(QtCore.QRect(10, 70, 471, 121))
        self.gb3_tabwidget_tab_twipr_gb42.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb42.setObjectName("gb3_tabwidget_tab_twipr_gb42")
        self.layoutWidget2 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb42)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 50, 451, 28))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.layoutWidget2)
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_31 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_31.setObjectName("label_31")
        self.gridLayout_3.addWidget(self.label_31, 0, 0, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb42_line1 = QtWidgets.QLineEdit(self.layoutWidget2)
        self.gb3_tabwidget_tab_twipr_gb42_line1.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.gb3_tabwidget_tab_twipr_gb42_line1.setObjectName("gb3_tabwidget_tab_twipr_gb42_line1")
        self.gridLayout_3.addWidget(self.gb3_tabwidget_tab_twipr_gb42_line1, 0, 1, 1, 1)
        self.label_29 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_29.setObjectName("label_29")
        self.gridLayout_3.addWidget(self.label_29, 0, 2, 1, 1)
        self.horizontalLayout_8.addLayout(self.gridLayout_3)
        self.line_10 = QtWidgets.QFrame(self.layoutWidget2)
        self.line_10.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_10.setLineWidth(1)
        self.line_10.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_10.setObjectName("line_10")
        self.horizontalLayout_8.addWidget(self.line_10)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label_32 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_32.setObjectName("label_32")
        self.gridLayout_4.addWidget(self.label_32, 0, 0, 1, 1)
        self.gb3_tabwidget_tab_twipr_gb42_line2 = QtWidgets.QLineEdit(self.layoutWidget2)
        self.gb3_tabwidget_tab_twipr_gb42_line2.setText("")
        self.gb3_tabwidget_tab_twipr_gb42_line2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.gb3_tabwidget_tab_twipr_gb42_line2.setObjectName("gb3_tabwidget_tab_twipr_gb42_line2")
        self.gridLayout_4.addWidget(self.gb3_tabwidget_tab_twipr_gb42_line2, 0, 1, 1, 1)
        self.label_30 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_30.setObjectName("label_30")
        self.gridLayout_4.addWidget(self.label_30, 0, 2, 1, 1)
        self.horizontalLayout_8.addLayout(self.gridLayout_4)
        self.layoutWidget_8 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb42)
        self.layoutWidget_8.setGeometry(QtCore.QRect(10, 20, 451, 21))
        self.layoutWidget_8.setObjectName("layoutWidget_8")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.layoutWidget_8)
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.verticalLayout_20 = QtWidgets.QVBoxLayout()
        self.verticalLayout_20.setObjectName("verticalLayout_20")
        self.gb3_tabwidget_tab_twipr_gb42_label1 = QtWidgets.QLabel(self.layoutWidget_8)
        self.gb3_tabwidget_tab_twipr_gb42_label1.setObjectName("gb3_tabwidget_tab_twipr_gb42_label1")
        self.verticalLayout_20.addWidget(self.gb3_tabwidget_tab_twipr_gb42_label1)
        self.horizontalLayout_9.addLayout(self.verticalLayout_20)
        self.line_8 = QtWidgets.QFrame(self.layoutWidget_8)
        self.line_8.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_8.setLineWidth(1)
        self.line_8.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_8.setObjectName("line_8")
        self.horizontalLayout_9.addWidget(self.line_8)
        self.verticalLayout_21 = QtWidgets.QVBoxLayout()
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.gb3_tabwidget_tab_twipr_gb42_label2 = QtWidgets.QLabel(self.layoutWidget_8)
        self.gb3_tabwidget_tab_twipr_gb42_label2.setObjectName("gb3_tabwidget_tab_twipr_gb42_label2")
        self.verticalLayout_21.addWidget(self.gb3_tabwidget_tab_twipr_gb42_label2)
        self.horizontalLayout_9.addLayout(self.verticalLayout_21)
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb42)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(9, 80, 451, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gb3_tabwidget_tab_twipr_gb42_but1 = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.gb3_tabwidget_tab_twipr_gb42_but1.setObjectName("gb3_tabwidget_tab_twipr_gb42_but1")
        self.horizontalLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb42_but1)
        self.gb3_tabwidget_tab_twipr_gb42_but2 = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.gb3_tabwidget_tab_twipr_gb42_but2.setObjectName("gb3_tabwidget_tab_twipr_gb42_but2")
        self.horizontalLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb42_but2)
        self.gb3_tabwidget_tab_twipr_gb42_but3 = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.gb3_tabwidget_tab_twipr_gb42_but3.setObjectName("gb3_tabwidget_tab_twipr_gb42_but3")
        self.horizontalLayout.addWidget(self.gb3_tabwidget_tab_twipr_gb42_but3)

        # gb3_tabwidget_gb3
        self.gb3_tabwidget_tab_twipr_gb3 = QtWidgets.QGroupBox(self.tab_object)
        self.gb3_tabwidget_tab_twipr_gb3.setEnabled(True)
        self.gb3_tabwidget_tab_twipr_gb3.setGeometry(QtCore.QRect(1370, 10, 491, 241))
        self.gb3_tabwidget_tab_twipr_gb3.setCheckable(True)
        self.gb3_tabwidget_tab_twipr_gb3.setChecked(False)
        self.gb3_tabwidget_tab_twipr_gb3.setObjectName("gb3_tabwidget_tab_twipr_gb3")
        self.gb3_tabwidget_tab_twipr_gb31 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb3)
        self.gb3_tabwidget_tab_twipr_gb31.setGeometry(QtCore.QRect(10, 20, 471, 51))
        self.gb3_tabwidget_tab_twipr_gb31.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb31.setObjectName("gb3_tabwidget_tab_twipr_gb31")
        self.layoutWidget_16 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb31)
        self.layoutWidget_16.setGeometry(QtCore.QRect(10, 20, 451, 21))
        self.layoutWidget_16.setObjectName("layoutWidget_16")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.layoutWidget_16)
        self.horizontalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.verticalLayout_24 = QtWidgets.QVBoxLayout()
        self.verticalLayout_24.setObjectName("verticalLayout_24")
        self.gb3_tabwidget_tab_twipr_gb31_label1 = QtWidgets.QLabel(self.layoutWidget_16)
        self.gb3_tabwidget_tab_twipr_gb31_label1.setObjectName("gb3_tabwidget_tab_twipr_gb31_label1")
        self.verticalLayout_24.addWidget(self.gb3_tabwidget_tab_twipr_gb31_label1)
        self.horizontalLayout_13.addLayout(self.verticalLayout_24)
        self.line_13 = QtWidgets.QFrame(self.layoutWidget_16)
        self.line_13.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_13.setLineWidth(1)
        self.line_13.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_13.setObjectName("line_13")
        self.horizontalLayout_13.addWidget(self.line_13)
        self.verticalLayout_25 = QtWidgets.QVBoxLayout()
        self.verticalLayout_25.setObjectName("verticalLayout_25")
        self.gb3_tabwidget_tab_twipr_gb31_label2 = QtWidgets.QLabel(self.layoutWidget_16)
        self.gb3_tabwidget_tab_twipr_gb31_label2.setObjectName("gb3_tabwidget_tab_twipr_gb31_label2")
        self.verticalLayout_25.addWidget(self.gb3_tabwidget_tab_twipr_gb31_label2)
        self.horizontalLayout_13.addLayout(self.verticalLayout_25)
        self.gb3_tabwidget_tab_twipr_gb32 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb3)
        self.gb3_tabwidget_tab_twipr_gb32.setGeometry(QtCore.QRect(10, 70, 471, 51))
        self.gb3_tabwidget_tab_twipr_gb32.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb32.setObjectName("gb3_tabwidget_tab_twipr_gb32")
        self.layoutWidget_17 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb32)
        self.layoutWidget_17.setGeometry(QtCore.QRect(10, 20, 451, 20))
        self.layoutWidget_17.setObjectName("layoutWidget_17")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.layoutWidget_17)
        self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.verticalLayout_28 = QtWidgets.QVBoxLayout()
        self.verticalLayout_28.setObjectName("verticalLayout_28")
        self.gb3_tabwidget_tab_twipr_gb32_label1 = QtWidgets.QLabel(self.layoutWidget_17)
        self.gb3_tabwidget_tab_twipr_gb32_label1.setObjectName("gb3_tabwidget_tab_twipr_gb32_label1")
        self.verticalLayout_28.addWidget(self.gb3_tabwidget_tab_twipr_gb32_label1)
        self.horizontalLayout_15.addLayout(self.verticalLayout_28)
        self.line_16 = QtWidgets.QFrame(self.layoutWidget_17)
        self.line_16.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_16.setLineWidth(1)
        self.line_16.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_16.setObjectName("line_16")
        self.horizontalLayout_15.addWidget(self.line_16)
        self.verticalLayout_29 = QtWidgets.QVBoxLayout()
        self.verticalLayout_29.setObjectName("verticalLayout_29")
        self.gb3_tabwidget_tab_twipr_gb32_label2 = QtWidgets.QLabel(self.layoutWidget_17)
        self.gb3_tabwidget_tab_twipr_gb32_label2.setObjectName("gb3_tabwidget_tab_twipr_gb32_label2")
        self.verticalLayout_29.addWidget(self.gb3_tabwidget_tab_twipr_gb32_label2)
        self.horizontalLayout_15.addLayout(self.verticalLayout_29)
        self.gb3_tabwidget_tab_twipr_gb33 = QtWidgets.QGroupBox(self.gb3_tabwidget_tab_twipr_gb3)
        self.gb3_tabwidget_tab_twipr_gb33.setGeometry(QtCore.QRect(10, 120, 471, 111))
        self.gb3_tabwidget_tab_twipr_gb33.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb33.setObjectName("gb3_tabwidget_tab_twipr_gb33")
        self.layoutWidget_18 = QtWidgets.QWidget(self.gb3_tabwidget_tab_twipr_gb33)
        self.layoutWidget_18.setGeometry(QtCore.QRect(10, 20, 451, 81))
        self.layoutWidget_18.setObjectName("layoutWidget_18")
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout(self.layoutWidget_18)
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_17.addItem(spacerItem)
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.horizontalLayout_17.addLayout(self.gridLayout_5)
        self.gb3_tabwidget_tab_twipr_gb33_slider = QtWidgets.QSlider(self.layoutWidget_18)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setMinimum(-200)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setMaximum(200)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setSingleStep(25)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setPageStep(50)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setOrientation(QtCore.Qt.Vertical)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setTickInterval(100)
        self.gb3_tabwidget_tab_twipr_gb33_slider.setObjectName("gb3_tabwidget_tab_twipr_gb33_slider")
        self.horizontalLayout_17.addWidget(self.gb3_tabwidget_tab_twipr_gb33_slider)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_17.addItem(spacerItem1)
        self.line_19 = QtWidgets.QFrame(self.layoutWidget_18)
        self.line_19.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_19.setLineWidth(1)
        self.line_19.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_19.setObjectName("line_19")
        self.horizontalLayout_17.addWidget(self.line_19)
        spacerItem2 = QtWidgets.QSpacerItem(58, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_17.addItem(spacerItem2)
        self.gb3_tabwidget_tab_twipr_gb33_dial = QtWidgets.QDial(self.layoutWidget_18)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setMinimum(-360)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setMaximum(360)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setSingleStep(20)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setPageStep(60)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setProperty("value", 0)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setNotchTarget(60.0)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setNotchesVisible(True)
        self.gb3_tabwidget_tab_twipr_gb33_dial.setObjectName("gb3_tabwidget_tab_twipr_gb33_dial")
        self.horizontalLayout_17.addWidget(self.gb3_tabwidget_tab_twipr_gb33_dial)
        spacerItem3 = QtWidgets.QSpacerItem(59, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_17.addItem(spacerItem3)

        # gb3_tabwidget_gb2
        self.gb3_tabwidget_tab_twipr_gb2 = QtWidgets.QGroupBox(self.tab_object)
        self.gb3_tabwidget_tab_twipr_gb2.setEnabled(True)
        self.gb3_tabwidget_tab_twipr_gb2.setGeometry(QtCore.QRect(730, 10, 631, 451))
        self.gb3_tabwidget_tab_twipr_gb2.setFlat(False)
        self.gb3_tabwidget_tab_twipr_gb2.setCheckable(False)
        self.gb3_tabwidget_tab_twipr_gb2.setChecked(False)
        self.gb3_tabwidget_tab_twipr_gb2.setObjectName("gb3_tabwidget_tab_twipr_gb2")
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget = QtWidgets.QTabWidget(self.gb3_tabwidget_tab_twipr_gb2)
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setGeometry(QtCore.QRect(10, 20, 611, 421))
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setObjectName("gb3_tabwidget_tab_twipr_gb2_tabwidget")

        # =================================================================================
        # create the tabwidget that will hold the respective plots on each of its pages
        # =================================================================================
        # tab_0 (s, theta, psi)
        self.tab_0 = QtWidgets.QWidget()
        self.tab_0.setObjectName("tab_0")
        self.gb2_tab_dict["tab_0"] = RobotPlot(self.main_ui_object,
                                               self,
                                               tab_page=self.tab_0,
                                               plot_index=0,
                                               x_lim=[0, 5],
                                               y_lim=[-3.2, 3.2],
                                               y_twin_lim=[],
                                               axes_labels=["$\Delta$t [s]", "$θ$, $ψ$ [rad]"],
                                               artists_num=2,
                                               artists_labels=["$θ$", "$ψ$"])
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.addTab(self.tab_0, "")
        # =================================================================================
        # tab_1 (xdot, thetadot, psidot, xdot_cmd, psidot_cmd)
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.gb2_tab_dict["tab_1"] = RobotPlot(self.main_ui_object,
                                               self,
                                               tab_page=self.tab_1,
                                               plot_index=1,
                                               x_lim=[0, 5],
                                               y_lim=[-5, 5],
                                               y_twin_lim=[-10, 10],
                                               axes_labels=["$\Delta$t [s]",
                                                            "$\dot x$, $\dot x_{set}$ [m/s]"],
                                               y_twin_label="$\dot θ$, $\dot ψ$, $\dot ψ_{set}$ [rad/s]",
                                               artists_num=5,
                                               artists_labels=["$\dot x$", "$\dot θ$", "$\dot ψ$", "$\dot x_{set}$", "$\dot ψ_{set}$"])
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.addTab(self.tab_1, "")
        # =================================================================================
        # tab_2 (x, y, x_cmd, y_cmd)
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gb2_tab_dict["tab_2"] = RobotPlot(self.main_ui_object,
                                               self,
                                               tab_page=self.tab_2,
                                               plot_index=2,
                                               x_lim=[-5, 5],
                                               y_lim=[-5, 5],
                                               y_twin_lim=[],
                                               axes_labels=["X [m]", "Y [m]"],
                                               artists_num=2,
                                               artists_labels=["set", "now"])
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.addTab(self.tab_2, "")
        # =================================================================================
        # tab_3 (u_l, u_r, omega_l, omega_r)
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gb2_tab_dict["tab_3"] = RobotPlot(self.main_ui_object,
                                               self,
                                               tab_page=self.tab_3,
                                               plot_index=3,
                                               x_lim=[0, 5],
                                               y_lim=[-1, 1],
                                               y_twin_lim=[-85, 85],
                                               axes_labels=["$\Delta$t [s]", "$u$ [Nm]"],
                                               y_twin_label="$ω$ [rad/s]",
                                               artists_num=4,
                                               artists_labels=["$u_{l}$", "$u_{r}$", "$ω_{l}$", "$ω_{r}$"])
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.addTab(self.tab_3, "")
        # =================================================================================
        # tab_4 (wx, wy, wz, ax, ay, az)
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.gb2_tab_dict["tab_4"] = RobotPlot(self.main_ui_object,
                                               self,
                                               tab_page=self.tab_4,
                                               plot_index=4,
                                               x_lim=[0, 5],
                                               y_lim=[-15, 15],
                                               y_twin_lim=[-465, 465],
                                               axes_labels=["$\Delta$t [s]", "$a$ [m/$s^2$]"],
                                               y_twin_label="$w$ [rad/s]",
                                               artists_num=6,
                                               artists_labels=["$wx$", "$wy$", "$wz$", "$ax$", "$ay$", "$az$"])
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.addTab(self.tab_4, "")
        # =================================================================================

        self.layoutWidget3 = QtWidgets.QWidget(self.main_ui_object.centralwidget)
        self.layoutWidget3.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget3.setObjectName("layoutWidget3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.layoutWidget4 = QtWidgets.QWidget(self.main_ui_object.centralwidget)
        self.layoutWidget4.setGeometry(QtCore.QRect(0, 0, 2, 2))
        self.layoutWidget4.setObjectName("layoutWidget4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.layoutWidget4)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        # set index to his tab
        # self.main_ui_object.gb3_tabwidget.setCurrentIndex(self.client_index+1)
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setCurrentIndex(0)

        # translate function
        self.gb3_tabwidget_tab_twipr_gb1.setTitle("General")
        # gb3_tabwidget_gb11
        self.gb3_tabwidget_tab_twipr_gb11.setTitle("Controls")
        self.gb3_tabwidget_tab_twipr_gb11_label1.setText("FSM_STATE:")
        self.gb3_tabwidget_tab_twipr_gb11_label2.setText("TICK:")
        self.gb3_tabwidget_tab_twipr_gb11_but1.setText("IDLE")
        self.gb3_tabwidget_tab_twipr_gb11_but2.setText("ERROR")
        self.gb3_tabwidget_tab_twipr_gb11_but3.setText("JOYSTICK")
        self.gb3_tabwidget_tab_twipr_gb11_label3.setText("CTRL_STATE:")

        self.gb3_tabwidget_tab_twipr_gb12.setTitle("Terminal")

        # gb4
        self.gb3_tabwidget_tab_twipr_gb4.setTitle("Position Control")
        self.gb3_tabwidget_tab_twipr_gb41.setTitle("Actual")
        self.gb3_tabwidget_tab_twipr_gb41_label1.setText("X =")
        self.gb3_tabwidget_tab_twipr_gb41_label2.setText("Y =")
        self.gb3_tabwidget_tab_twipr_gb42.setTitle("Target")
        self.label_31.setText("X =")
        self.gb3_tabwidget_tab_twipr_gb42_line1.setPlaceholderText("Enter X")
        self.label_29.setText("m")
        self.label_32.setText("Y =")
        self.gb3_tabwidget_tab_twipr_gb42_line2.setPlaceholderText("Enter Y")
        self.label_30.setText("m")
        self.gb3_tabwidget_tab_twipr_gb42_label1.setText("X =")
        self.gb3_tabwidget_tab_twipr_gb42_label2.setText("Y =")
        self.gb3_tabwidget_tab_twipr_gb42_but1.setText("Update X-Target")
        self.gb3_tabwidget_tab_twipr_gb42_but2.setText("Update Targets")
        self.gb3_tabwidget_tab_twipr_gb42_but3.setText("Update Y-Target")

        # gb3
        self.gb3_tabwidget_tab_twipr_gb3.setTitle("Velocity Control")
        self.gb3_tabwidget_tab_twipr_gb31.setTitle("Actual")
        self.gb3_tabwidget_tab_twipr_gb31_label1.setText("x_d =")
        self.gb3_tabwidget_tab_twipr_gb31_label2.setText("ψ_d =")
        self.gb3_tabwidget_tab_twipr_gb32.setTitle("Target")
        self.gb3_tabwidget_tab_twipr_gb32_label1.setText("x_d =")
        self.gb3_tabwidget_tab_twipr_gb32_label2.setText("ψ_d =")
        self.gb3_tabwidget_tab_twipr_gb33.setTitle("Target Controls")

        # gb2
        self.gb3_tabwidget_tab_twipr_gb2.setTitle("Plots")
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setTabText(self.gb3_tabwidget_tab_twipr_gb2_tabwidget.indexOf(self.tab_0), "θ, ψ")
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setTabText(self.gb3_tabwidget_tab_twipr_gb2_tabwidget.indexOf(self.tab_1), "x_d, θ_d, ψ_d")
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setTabText(self.gb3_tabwidget_tab_twipr_gb2_tabwidget.indexOf(self.tab_2), "X, Y")
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setTabText(self.gb3_tabwidget_tab_twipr_gb2_tabwidget.indexOf(self.tab_3), "Motor")
        self.gb3_tabwidget_tab_twipr_gb2_tabwidget.setTabText(self.gb3_tabwidget_tab_twipr_gb2_tabwidget.indexOf(self.tab_4), "IMU")
        
        # signal and slots
        self.gb3_tabwidget_tab_twipr_gb11_but1.clicked.connect(self.idle_but_clicked)
        self.gb3_tabwidget_tab_twipr_gb11_but2.clicked.connect(self.error_but_clicked)
        self.gb3_tabwidget_tab_twipr_gb11_but3.clicked.connect(self.joystick_but_clicked)
        self.gb3_tabwidget_tab_twipr_gb3.clicked.connect(self.gb3_clicked)
        self.gb3_tabwidget_tab_twipr_gb4.clicked.connect(self.gb4_clicked)
        self.gb3_tabwidget_tab_twipr_gb33_slider.valueChanged.connect(self.slider_value_changed)
        self.gb3_tabwidget_tab_twipr_gb33_dial.valueChanged.connect(self.dial_value_changed)
        self.gb3_tabwidget_tab_twipr_gb42_but1.clicked.connect(self.update_set_x_coordinate)
        self.gb3_tabwidget_tab_twipr_gb42_but2.clicked.connect(self.update_set_coordinates)
        self.gb3_tabwidget_tab_twipr_gb42_but3.clicked.connect(self.update_set_y_coordinate)
        self.gb3_tabwidget_tab_twipr_gb12_line.returnPressed.connect(self.process_input_from_robot_terminal)

        QtCore.QMetaObject.connectSlotsByName(self.main_ui_object.main_window)

        # render robot user interface for the first time
        self.update_gb1()
        self.update_gb3()
        self.update_gb4()
        self.update_checkboxes()

        # ui initialization completed successfully
        string = "Robot \"" + self.client_name + "\" has connected to HOST! Please adjust the settings in the respective tab below!"
        self.main_ui_object.write_message_to_main_terminal(string, "G")
        string = "Robot \"" + self.client_name + "\" has connected to HOST!"
        self.write_message_to_robot_terminal(string, "G")

    def write_message_to_robot_terminal(self, string, color):
        # write message to main terminal that robot has been connected
        item = QtWidgets.QListWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

        time_now = datetime.now().strftime("%H:%M:%S") + ": "
        item.setText(time_now + string)
        # check color
        if color == "G":  # new client, new joystick, new message, ...
            item.setForeground(QtCore.Qt.green)
        elif color == "R":  # error messages, robot disconnect, joystick disconnect, ... (opposite of 'G')
            item.setForeground(QtCore.Qt.red)
        elif color == "Y":  # sent messages
            item.setForeground(QtCore.Qt.yellow)
        elif color == "B":  # G-Code documentation
            item.setForeground(QtCore.Qt.cyan)
        self.gb3_tabwidget_tab_twipr_gb12_list.addItem(item)
        # auto scroll
        self.gb3_tabwidget_tab_twipr_gb12_list.scrollToBottom()

    def write_received_msg_to_robot_terminal(self, client_index, string, color):
        string = "[R] " + string
        self.write_message_to_robot_terminal(string, color)

    def write_sent_command_to_robot_terminal(self, client_index, string, color):
        string = "[S] " + string
        self.write_message_to_robot_terminal(string, color)

    def read_from_cmd_history_key_up(self):
        if self.cmd_history:
            if self.cmd_history_reading_index == 0:
                self.cmd_history_reading_index = len(self.cmd_history) - 1
            else:
                self.cmd_history_reading_index -= 1
            cmd = self.cmd_history[self.cmd_history_reading_index]
            self.gb3_tabwidget_tab_twipr_gb12_line.setText(cmd)
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
            self.gb3_tabwidget_tab_twipr_gb12_line.setText(cmd)
        else:
            pass

    def read_from_cmd_history_key_esc(self):
        cmd = 'M62'
        self.gb3_tabwidget_tab_twipr_gb12_line.setText(cmd)

    def read_from_cmd_history_key_f1(self):
        cmd = 'M61'
        self.gb3_tabwidget_tab_twipr_gb12_line.setText(cmd)

    def read_from_cmd_history_key_f2(self):
        # just an example
        pass

    def add_cmd_to_history(self, cmd):
        # add valid command to history of the robot and main terminal
        self.write_to_cmd_history(cmd)
        self.main_ui_object.write_to_cmd_history(cmd)

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

    def gcode_execution_from_file(self, filename: str) -> None:
        self.clear_robot_terminal_line_edit()

        # open and read config file
        err = txt_handler.open('Miscellaneous/{}.gcode'.format(filename))
        if err:
            self.main_ui_object.write_message_to_terminals(self.client_index, err, 'R')
            # self.popup_invalid_input_robot_terminal(err)
            return

        for processed_line in txt_handler.read():
            if not processed_line:
                # yields zero in this case
                err = "Configuration file empty!"
                self.main_ui_object.write_message_to_terminals(self.client_index, err, 'R')
                # self.popup_invalid_input_robot_terminal(err)
                break

            self.gb3_tabwidget_tab_twipr_gb12_line.setText(processed_line)
            self.process_input_from_robot_terminal()

        err = txt_handler.close()
        if err:
            self.main_ui_object.write_message_to_terminals(self.client_index, err, 'R')
            # self.popup_invalid_input_robot_terminal(err)
            return

    def write_gcode_documentation_to_terminal(self) -> None:
        self.clear_robot_terminal_line_edit()
        # open and read g-code documentation file
        err = txt_handler.open('Communication/gcode_documentation.txt')
        if err:
            self.write_message_to_robot_terminal(err, 'R')
            # self.popup_invalid_input_robot_terminal(err)
            return

        for processed_line in txt_handler.read():
            if not processed_line:
                # yields zero in this case
                err = "G-code documentation file empty!"
                self.write_message_to_robot_terminal(err, 'R')
                # self.popup_invalid_input_robot_terminal(err)
                break

            self.write_message_to_robot_terminal(processed_line, 'B')

        err = txt_handler.close()
        if err:
            self.main_ui_object.write_message_to_terminals(self.client_index, err, 'R')
            # self.popup_invalid_input_robot_terminal(err)
            return

    def enter_cmd_into_robot_terminal(self, cmd: str, write_to_terminal: bool = True) -> None:
        # this function is accessed by the joystick_handler to transfer commands from there
        self.gb3_tabwidget_tab_twipr_gb12_line.setText(cmd)
        self.process_input_from_robot_terminal(write_to_terminal=write_to_terminal)

    def invalid_gcode(self, user_input: str) -> None:
        string = "Invalid G-code! Please refer to the documentation for further information! (F1)"
        self.main_ui_object.write_message_to_terminals(self.client_index, user_input, 'W')
        self.main_ui_object.write_message_to_terminals(self.client_index, string, 'R')
        # self.popup_invalid_input_robot_terminal(string)

    def process_input_from_robot_terminal(self, write_to_terminal=True):
        # read text from line edit "gb22" and make a list
        line_text = self.gb3_tabwidget_tab_twipr_gb12_line.text()
        if not line_text:
            self.popup_invalid_input_robot_terminal("Please enter a command!")
            return

        self.clear_robot_terminal_line_edit()

        # parse input from line edit, the output of the parser is a either a msg for ML/LL or
        # a list of strings containing g-codes that are meant for the HL (internal call)
        gcode_parser_output = gcode_parser.parse(line_text)

        if type(gcode_parser_output) == list:
            # validity check
            if gcode_parser_output[0]['type'] == 'M60':
                self.invalid_gcode(line_text)
                return

            self.execute_internal_call(gcode_parser_output, write_to_terminal, line_text)  # HL -> HL
        else:
            if write_to_terminal:
                self.main_ui_object.write_message_to_all_terminals(line_text, 'W')
            self.send_message_from_robot_terminal(gcode_parser_output, write_to_terminal, line_text)  # HL -> ML/LL

        self.add_cmd_to_history(line_text)

    def execute_internal_call(self, cmd_list: List[Dict[str, Any]], write_to_terminal: bool, line_text: str) -> None:
        # the cmd list comprises dictionaries containing a g-code and its arguments respectively
        for gcode in cmd_list:
            if gcode['type'] == 'M61':
                self.write_message_to_robot_terminal(line_text, 'W')
                self.write_gcode_documentation_to_terminal()

            elif gcode['type'] == 'M62':
                self.write_message_to_robot_terminal(line_text, 'W')
                self.clear_robot_terminal()

            elif gcode['type'] == 'M63':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')
                self.gcode_execution_from_file(gcode['filename'])

            elif gcode['type'] == 'M64':
                self.write_message_to_robot_terminal(line_text, 'W')
                self.display_robot_data()

            elif gcode['type'] == 'M65':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg = experiment_handler.load_experiment(gcode['filename'])
                if not msg:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed loading experiment!", "R")
                    return
                self.send_message_from_robot_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M66':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg, start_gcodes = experiment_handler.start_experiment(gcode['filename'])
                # execute commands before starting the experiment
                for cmd in start_gcodes:
                    self.enter_cmd_into_robot_terminal(cmd)
                # then start experiment
                self.send_message_from_robot_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M67':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg_load, msg_start = experiment_handler.load_and_start_experiment(gcode['filename'])
                if not msg_load:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed loading experiment!", "R")
                    return
                self.send_message_from_robot_terminal(msg_load, write_to_terminal, line_text)
                self.send_message_from_robot_terminal(msg_start, False, line_text)

            elif gcode['type'] == 'M68':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg = experiment_handler.end_experiment(gcode['filename'])
                self.send_message_from_robot_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M69':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg = sequence_handler.load_sequence(gcode['filename'])
                if not msg:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed loading sequence!", "R")
                    return
                self.send_message_from_robot_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M70':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg = sequence_handler.start_sequence(gcode['filename'])
                self.send_message_from_robot_terminal(msg, write_to_terminal, line_text)

            elif gcode['type'] == 'M71':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg_load, msg_start = sequence_handler.load_and_start_sequence(gcode['filename'])
                if not msg_load:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed loading sequence!", "R")
                    return
                self.send_message_from_robot_terminal(msg_load, write_to_terminal, line_text)
                self.send_message_from_robot_terminal(msg_start, False, line_text)

            elif gcode['type'] == 'M72':
                self.main_ui_object.write_message_to_terminals(self.client_index, line_text, 'W')

                msg = sequence_handler.end_sequence(gcode['filename'])
                self.send_message_from_robot_terminal(msg, write_to_terminal, line_text)

            else:
                pass

    def send_message_from_robot_terminal(self, msg, write_to_terminal, line_text):
        # request message transmission from main ui backend
        if self.main_ui_object.send_message(self.client_index, msg):
            # write sent command to terminal
            if write_to_terminal:
                self.main_ui_object.write_sent_command_to_terminals(self.client_index, line_text, "Y")
        else:
            # write error message to terminals
            if write_to_terminal:
                self.main_ui_object.write_sent_command_to_terminals(self.client_index, line_text, "R")
            self.main_ui_object.write_message_to_terminals(self.client_index, "Failed to sent message!", "R")

        self.clear_robot_terminal_line_edit()

    def clear_robot_terminal(self):
        self.clear_robot_terminal_list_view()
        self.clear_robot_terminal_line_edit()
        
    def clear_robot_terminal_list_view(self):
        # clear command window (clc)
        self.gb3_tabwidget_tab_twipr_gb12_list.clear()

    def clear_robot_terminal_line_edit(self):
        # clear the line edit
        self.gb3_tabwidget_tab_twipr_gb12_line.setText('')

    def popup_invalid_input_robot_terminal(self, e):
        self.clear_robot_terminal_line_edit()
        # and send warning popup
        self.popup_invalid_input(e)

    def display_robot_data(self):
        # M64
        # create a string with relevant robot data
        string = self.get_robot_data_string()
        # write to respective robot terminal
        self.write_message_to_robot_terminal(string, 'W')

    def get_robot_data_string(self) -> str:
        string = "TWIPR_{}: xdot={:.2f}, theta={:.2f}, thetadot={:.2f}, psi={:.2f}, psidot={:.2f}, \n" \
                 "gyr_x={:.2f}, gyr_y={:.2f}, gyr_z={:.2f}, acc_x={:.2f}, acc_y={:.2f}, acc_z={:.2f}, \n" \
                 "omega_l={:.2f}, omega_r={:.2f}, torque_l={:.2f}, torque_r={:.2f}, \n" \
                 "u_l={:.2f}, u_r={:.2f}, xdot_cmd={:.2f}, psidot_cmd={:.2f}".format(self.client_index,
                                                                                     self.robot.state.sdot,
                                                                                     self.robot.state.theta,
                                                                                     self.robot.state.thetadot,
                                                                                     self.robot.state.psi,
                                                                                     self.robot.state.psidot,
                                                                                     self.robot.sensors.imu.gyr[0],
                                                                                     self.robot.sensors.imu.gyr[1],
                                                                                     self.robot.sensors.imu.gyr[2],
                                                                                     self.robot.sensors.imu.acc[0],
                                                                                     self.robot.sensors.imu.acc[1],
                                                                                     self.robot.sensors.imu.acc[2],
                                                                                     self.robot.sensors.encoder_left.omega,
                                                                                     self.robot.sensors.encoder_right.omega,
                                                                                     self.robot.drive.torque_left,
                                                                                     self.robot.drive.torque_right,
                                                                                     self.robot.controller.u[0],
                                                                                     self.robot.controller.u[1],
                                                                                     self.robot.controller.xdot_cmd,
                                                                                     self.robot.controller.psidot_cmd)

        return string

    def timeout(self):
        # gb11
        self.update_gb1()
        # gb2
        self.update_gb2()
        # gb3
        self.update_gb3()
        # gb4 (not in use currently)
        # self.update_gb4()
        # update checkboxes (gb3/gb4)
        if self.update_checkboxes_flag:  # hack to avoid a flashing checkbox when changing ctrl states (gb3/gb4)
            self.update_checkboxes()
        # check TWIPR heartbeat
        # self.check_heartbeat()
        
    def check_heartbeat(self):
        if self.check_heartbeat_flag == 0:
            self.check_heartbeat_flag = 1
            self.robot.tick_last = self.robot.tick
        if self.check_heartbeat_counter == self.check_heartbeat_interval:
            self.check_heartbeat_counter = 0
            self.check_heartbeat_flag = 0
            if self.robot.tick - self.robot.tick_last == 0:  # TWIPR dies in the unlikely event of a blackout
                self.main_ui_object.close_socket(self.client_index)
                self.popup_critical("TWIPR_{} died!".format(self.client_index))
        else:
            self.check_heartbeat_counter += 1

    def update_gb1(self):
        # gb11
        # ---- (1) FSM_STATE
        string = "FSM_STATE: {} ({})".format(self.robot.fsm_state.name, self.robot.fsm_state.value)
        self.gb3_tabwidget_tab_twipr_gb11_label1.setText(string)
        # ---- (2) CTRL_STATE
        string = "CTRL_STATE: {} ({})".format(self.robot.controller.state.name, self.robot.controller.state.value)
        self.gb3_tabwidget_tab_twipr_gb11_label3.setText(string)
        # ---- (3) TICKS FROM LL
        string = "TICK: {}".format(self.robot.tick)
        self.gb3_tabwidget_tab_twipr_gb11_label2.setText(string)
        # ---- (4) JOYSTICK BUTTON COLOR
        if self.joystick_enable:
            # set to green color
            self.gb3_tabwidget_tab_twipr_gb11_but3.setStyleSheet("background-color : rgb(0, 180, 0); color : rgb(255, 255, 255)")
        else:
            # set to standard color
            self.gb3_tabwidget_tab_twipr_gb11_but3.setStyleSheet("background-color : rgb(240, 240, 240)")

    def update_gb2(self):
        # return the index of the plot that is opened currently
        tab_index = self.gb3_tabwidget_tab_twipr_gb2_tabwidget.currentIndex()
        # update the shown plot
        key = "tab_{}".format(tab_index)
        self.gb2_tab_dict[key].update_plot()

    def update_gb3(self):
        # gb3
        # ---- (1) actual velocities
        string = "x_d = " + str(round(self.robot.state.sdot, 2)) + " m/s"
        self.gb3_tabwidget_tab_twipr_gb31_label1.setText(string)
        # self.gb3_tabwidget_tab_twipr_gb31_label1.repaint()
        string = "ψ_d = " + str(round(self.robot.state.psidot, 2)) + " rad/s"
        self.gb3_tabwidget_tab_twipr_gb31_label2.setText(string)
        # ---- (2) target velocities
        string = "x_d = " + str(round(self.robot.controller.xdot_cmd, 2)) + " m/s"
        self.gb3_tabwidget_tab_twipr_gb32_label1.setText(string)
        string = "ψ_d = " + str(round(self.robot.controller.psidot_cmd, 2)) + " rad/s"
        self.gb3_tabwidget_tab_twipr_gb32_label2.setText(string)
    
    def update_gb4(self):
        # gb4
        # ---- (1) actual position
        string = "X = " + str(round(self.robot.state.x, 2)) + " m"
        self.gb3_tabwidget_tab_twipr_gb41_label1.setText(string)
        string = "Y = " + str(round(self.robot.state.y, 2)) + " m"
        self.gb3_tabwidget_tab_twipr_gb41_label2.setText(string)
        # ---- (2) target position
        string = "X = " + str(round(self.robot.controller.x_cmd, 2)) + " m"
        self.gb3_tabwidget_tab_twipr_gb42_label1.setText(string)
        string = "Y = " + str(round(self.robot.controller.y_cmd, 2)) + " m"
        self.gb3_tabwidget_tab_twipr_gb42_label2.setText(string)

    def update_checkboxes(self):
        # is called every 100 ms
        if self.robot.fsm_state == FSM_STATE.ACTIVE:
            if self.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                self.gb3_tabwidget_tab_twipr_gb3.setEnabled(True)
                self.gb3_tabwidget_tab_twipr_gb4.setEnabled(False)
                self.gb3_tabwidget_tab_twipr_gb3.setChecked(False)
                self.gb3_tabwidget_tab_twipr_gb4.setChecked(False)
            elif self.robot.controller.state == CTRL_STATE.VELOCITY:
                self.gb3_tabwidget_tab_twipr_gb3.setChecked(True)
                self.gb3_tabwidget_tab_twipr_gb4.setChecked(False)
            # elif self.robot.controller.state == CTRL_STATE.POSITION:
            #     self.gb3_tabwidget_tab_twipr_gb3.setChecked(False)
            #     self.gb3_tabwidget_tab_twipr_gb4.setChecked(True)
            else:
                self.gb3_tabwidget_tab_twipr_gb3.setEnabled(False)
                self.gb3_tabwidget_tab_twipr_gb4.setEnabled(False)
                self.gb3_tabwidget_tab_twipr_gb3.setChecked(False)
                self.gb3_tabwidget_tab_twipr_gb4.setChecked(False)
        else:
            self.gb3_tabwidget_tab_twipr_gb3.setEnabled(False)
            self.gb3_tabwidget_tab_twipr_gb4.setEnabled(False)
            self.gb3_tabwidget_tab_twipr_gb3.setChecked(False)
            self.gb3_tabwidget_tab_twipr_gb4.setChecked(False)

    def gb3_clicked(self):
        self.update_checkboxes_flag = False
        if self.gb3_tabwidget_tab_twipr_gb3.isChecked():
            # (1) uncheck gb4
            self.gb3_tabwidget_tab_twipr_gb4.setChecked(False)
            # (2) demand CTRL_STATE == VELOCITY
            self.gb3_tabwidget_tab_twipr_gb12_line.setText("M2 S3")
            self.process_input_from_robot_terminal()
        elif not self.gb3_tabwidget_tab_twipr_gb3.isChecked() and not self.gb3_tabwidget_tab_twipr_gb4.isChecked():
            # only if gb3 and gb4 not checked -> demand CTRL_STATE == VELOCITY
            self.gb3_tabwidget_tab_twipr_gb12_line.setText("M2 S2")
            self.process_input_from_robot_terminal()

    def gb4_clicked(self):
        # copy from gb3_clicked
        pass

    def slider_value_changed(self):
        value = self.gb3_tabwidget_tab_twipr_gb33_slider.value()
        # calculate real "set_x_dot"
        value /= 100
        # send target xdot
        self.gb3_tabwidget_tab_twipr_gb12_line.setText("G1 X{}".format(value))
        self.process_input_from_robot_terminal(write_to_terminal=False)

    def dial_value_changed(self):
        value = self.gb3_tabwidget_tab_twipr_gb33_dial.value()
        # calculate real "set_psi_dot"
        value = value * np.pi / 180
        # send target psidot
        self.gb3_tabwidget_tab_twipr_gb12_line.setText("G1 P{}".format(value))
        self.process_input_from_robot_terminal(write_to_terminal=False)

    def update_set_x_coordinate(self):
        text = self.gb3_tabwidget_tab_twipr_gb42_line1.text()
        if text == "":
            string = "Please enter a target coordinate!"
            self.invalid_input_target_coordinates(string)
        else:
            try:
                value = float(text)
                # send target x coordinate
                msg = 0  # MSG_HOST_OUT_CTRL_INPUT(0, (0, 0), 0, 0, value, self.robot.controller.y_cmd)
                if self.main_ui_object.send_message(self.client_index, msg) == 1:
                    pass
                else:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed to sent message!", "R")
                self.gb3_tabwidget_tab_twipr_gb42_line1.setText("")
                self.gb3_tabwidget_tab_twipr_gb42_line2.setText("")
            except ValueError as e:
                self.invalid_input_target_coordinates(e)

    def update_set_coordinates(self):
        text1 = self.gb3_tabwidget_tab_twipr_gb42_line1.text()
        text2 = self.gb3_tabwidget_tab_twipr_gb42_line2.text()
        if text1 == "" or text2 == "":
            string = "Please enter target coordinates!"
            self.invalid_input_target_coordinates(string)
        else:
            try:
                value1 = float(text1)
                value2 = float(text2)
                # send target x coordinate
                msg = 0  # MSG_HOST_OUT_CTRL_INPUT(0, (0, 0), 0, 0, value1, value2)
                if self.main_ui_object.send_message(self.client_index, msg) == 1:
                    pass
                else:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed to sent message!", "R")
                self.gb3_tabwidget_tab_twipr_gb42_line1.setText("")
                self.gb3_tabwidget_tab_twipr_gb42_line2.setText("")
            except ValueError as e:
                self.invalid_input_target_coordinates(e)

    def update_set_y_coordinate(self):
        text = self.gb3_tabwidget_tab_twipr_gb42_line2.text()
        if text == "":
            string = "Please enter a target coordinate!"
            self.invalid_input_target_coordinates(string)
        else:
            try:
                value = float(text)
                # send target x coordinate
                msg = 0  # MSG_HOST_OUT_CTRL_INPUT(0, (0, 0), 0, 0, self.robot.controller.x_cmd, value)
                if self.main_ui_object.send_message(self.client_index, msg) == 1:
                    pass
                else:
                    self.main_ui_object.write_message_to_terminals(self.client_index, "Failed to sent message!", "R")
                self.gb3_tabwidget_tab_twipr_gb42_line1.setText("")
                self.gb3_tabwidget_tab_twipr_gb42_line2.setText("")
            except ValueError as e:
                self.invalid_input_target_coordinates(e)

    def invalid_input_target_coordinates(self, e):
        # clear the line edits
        self.gb3_tabwidget_tab_twipr_gb42_line1.setText("")
        self.gb3_tabwidget_tab_twipr_gb42_line2.setText("")
        # and send warning popup
        self.popup_invalid_input(e)

    @staticmethod
    def popup_invalid_input(error_message: str) -> None:
        # popup with detail text "e"
        popup = QtWidgets.QMessageBox()
        popup.setWindowTitle("TWIPR Dashboard")
        popup.setText("Invalid user input!")
        popup.setIcon(QtWidgets.QMessageBox.Warning)
        popup.setDetailedText(str(error_message))
        popup.setWindowIcon(QtGui.QIcon("Icons/icon_256.png"))
        x = popup.exec_()

    @staticmethod
    def popup_critical(error_message: str) -> None:
        # popup with detail text "e"
        popup = QtWidgets.QMessageBox()
        popup.setWindowTitle("TWIPR Dashboard")
        popup.setText("Critical Error occurred!")
        popup.setIcon(QtWidgets.QMessageBox.Critical)
        popup.setDetailedText(str(error_message))
        popup.setWindowIcon(QtGui.QIcon("Icons/icon_256.png"))
        x = popup.exec_()

    def idle_but_clicked(self):
        terminal_txt = 'Requesting state IDLE!'
        self.main_ui_object.write_sent_command_to_terminals(self.client_index, terminal_txt, "W")
        # send cmd
        self.gb3_tabwidget_tab_twipr_gb12_line.setText("M1 S1")
        self.process_input_from_robot_terminal()

    def error_but_clicked(self):
        terminal_txt = 'Requesting state ERROR!'
        self.main_ui_object.write_sent_command_to_terminals(self.client_index, terminal_txt, "W")
        # send cmd
        self.gb3_tabwidget_tab_twipr_gb12_line.setText("M1 S3")
        self.process_input_from_robot_terminal()

    def joystick_but_clicked(self) -> None:
        if self.joystick_instance_id == -1:
            self.popup_invalid_input("Please connect a game controller!")
            return

        self.joystick_enable ^= True
        if self.joystick_enable:
            terminal_txt = "Joystick {} activated!".format(self.joystick_instance_id)
            self.main_ui_object.write_message_to_terminals(self.client_index, terminal_txt, "G")
            # # set to green color
            # self.gb3_tabwidget_tab_twipr_gb11_but3.setStyleSheet("background-color : rgb(0, 180, 0); color : rgb(255, 255, 255)")
        else:
            terminal_txt = "Joystick {} deactivated!".format(self.joystick_instance_id)
            self.main_ui_object.write_message_to_terminals(self.client_index, terminal_txt, "R")
            # # set to standard color
            # self.gb3_tabwidget_tab_twipr_gb11_but3.setStyleSheet("background-color : rgb(240, 240, 240)")
