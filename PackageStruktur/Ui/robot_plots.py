# PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets

# Plotting
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class RobotPlot:
    def __init__(self, main_ui_object, robot_ui_object, **settings):  # settings is a dictionary
        self.main_ui_object = main_ui_object
        self.robot_ui_object = robot_ui_object
        self.main_window = self.main_ui_object.main_window
        self.tab_page = settings['tab_page']

        # (0) save the labels for the respective lines and plot index
        self.plot_index = settings['plot_index']
        self.artists_num = settings['artists_num']
        self.artists_labels = settings['artists_labels']
        self.artists_colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
                               'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']

        # (1) initialize line reference
        self.plot_ref_list = [None] * self.artists_num

        # (2) create plot and adjust settings for it
        # self.figure = plt.figure(tight_layout=True)
        self.figure = plt.figure(constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.main_window)
        self.but = QtWidgets.QPushButton("Stop")
        self.but.setObjectName("but")
        self.but.setStyleSheet("background-color : rgb(240, 240, 240)")
        # ---- stop/start flag
        self.but_flag_stop = False
        self.layout = QtWidgets.QWidget(self.tab_page)
        self.layout.setGeometry(QtCore.QRect(0, 0, 604, 397))
        self.layout.setObjectName("layout")
        self.vlay = QtWidgets.QVBoxLayout(self.layout)
        self.vlay.setObjectName("vlay")
        self.vlay.addWidget(self.toolbar)
        self.vlay.addWidget(self.canvas)
        self.vlay.addWidget(self.but)
        # ---- define axes
        self.ax = self.figure.add_subplot(111)
        # cached background
        self.cached_bg = None
        self.artists = []
        # plot settings
        self.x_lim_low, self.x_lim_high = settings['x_lim']
        self.y_lim_low, self.y_lim_high = settings['y_lim']
        # ---- adjust axes
        self.x_label, self.y_label = settings['axes_labels']
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        self.ax.set_xlim(self.x_lim_low, self.x_lim_high)
        self.ax.set_ylim(self.y_lim_low, self.y_lim_high)
        self.ax.grid(which="major", color="gray", linestyle="-")
        self.ax.grid(which="minor", color="whitesmoke", linestyle="--")
        self.ax.minorticks_on()
        # ---- plot settings for additional scale
        if self.plot_index in [1, 3, 4]:
            self.ax_twin = self.ax.twinx()  # used for plots with different scales
            self.y_twin_lim_low, self.y_twin_lim_high = settings['y_twin_lim']
            self.y_twin_label = settings['y_twin_label']
            self.ax_twin.set_ylabel(self.y_twin_label)
            self.ax_twin.set_ylim(self.y_twin_lim_low, self.y_twin_lim_high)
        # signal and slots
        self.but.clicked.connect(self.toggle_but_flag)

    def toggle_but_flag(self):
        # handle unwanted user behaviour
        if self.main_ui_object.clients_number == 0 and not self.but_flag_stop:
            # send warning popup
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("TWIPR Dashboard")
            popup.setText("Plot empty!")
            popup.setIcon(QtWidgets.QMessageBox.Warning)
            popup.setDetailedText("Please connect a client!")
            popup.setWindowIcon(QtGui.QIcon("Footage/TU_Logo_kurz_RGB_rot.jpg"))
            x = popup.exec_()
        else:
            # change flag to signal plotting stop
            self.but_flag_stop = not self.but_flag_stop
            # change color of button to red if plotting has been stopped by the user
            if self.but_flag_stop:
                self.but.setStyleSheet("background-color : rgb(180, 0, 0); color : rgb(255, 255, 255)")
            else:
                # set to standard color
                self.but.setStyleSheet("background-color : rgb(240, 240, 240)")

    def update_plot(self):
        # check plot_index (which tab page are we on? >>> important for making the respective plot)
        if self.plot_index == 0:
            # check if plot reference has been created already
            if self.plot_ref_list[0] is None:
                # unpack returned line list
                self.plot_ref_list[0], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_theta,
                                                      label=self.artists_labels[0],
                                                      animated=True,
                                                      color=self.artists_colors[0])
                self.plot_ref_list[1], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_psi,
                                                      label=self.artists_labels[1],
                                                      animated=True,
                                                      color=self.artists_colors[1])
                # update legend and draw everything
                self.ax.legend(loc="upper right", fontsize="xx-small")
                # render everything out
                self.canvas.draw()
                # adjust background
                self.cached_bg = self.canvas.copy_from_bbox(self.figure.bbox)
                # add artists to list for plotting
                self.artists.append(self.plot_ref_list[0])
                self.artists.append(self.plot_ref_list[1])
            else:
                # update data if reference is available and if stop button has not been pressed
                if not self.but_flag_stop:
                    self.plot_ref_list[0].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[0].set_ydata(self.robot_ui_object.robot.data_logs.log_theta)
                    self.plot_ref_list[1].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[1].set_ydata(self.robot_ui_object.robot.data_logs.log_psi)
                    # bring back cached background
                    self.canvas.restore_region(self.cached_bg)
                    # draw artists only
                    for a in self.artists:
                        self.figure.draw_artist(a)
        elif self.plot_index == 1:
            # check if plot reference has been created already
            if self.plot_ref_list[0] is None:
                # unpack returned line list
                self.plot_ref_list[0], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_sdot,
                                                      label=self.artists_labels[0],
                                                      animated=True,
                                                      color=self.artists_colors[0])
                self.plot_ref_list[1], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_thetadot,
                                                           label=self.artists_labels[1],
                                                           animated=True,
                                                           color=self.artists_colors[1])
                self.plot_ref_list[2], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_psidot,
                                                           label=self.artists_labels[2],
                                                           animated=True,
                                                           color=self.artists_colors[2])
                self.plot_ref_list[3], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_xdot_cmd,
                                                           label=self.artists_labels[3],
                                                           animated=True,
                                                           color=self.artists_colors[3])
                self.plot_ref_list[4], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_psidot_cmd,
                                                           label=self.artists_labels[4],
                                                           animated=True,
                                                           color=self.artists_colors[4])
                # update legend and draw everything
                lines = [self.plot_ref_list[0], self.plot_ref_list[1], self.plot_ref_list[2],
                         self.plot_ref_list[3], self.plot_ref_list[4]]
                labels = [line.get_label() for line in lines]
                self.ax.legend(lines, labels, loc="upper right", fontsize="xx-small")
                self.canvas.draw()
                # adjust background
                self.cached_bg = self.canvas.copy_from_bbox(self.figure.bbox)
                # add artists to list for plotting
                self.artists.append(self.plot_ref_list[0])
                self.artists.append(self.plot_ref_list[1])
                self.artists.append(self.plot_ref_list[2])
                self.artists.append(self.plot_ref_list[3])
                self.artists.append(self.plot_ref_list[4])
            else:
                # update data if reference is available and if stop button has not been pressed
                if not self.but_flag_stop:
                    self.plot_ref_list[0].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[0].set_ydata(self.robot_ui_object.robot.data_logs.log_sdot)
                    self.plot_ref_list[1].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[1].set_ydata(self.robot_ui_object.robot.data_logs.log_thetadot)
                    self.plot_ref_list[2].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[2].set_ydata(self.robot_ui_object.robot.data_logs.log_psidot)
                    self.plot_ref_list[3].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[3].set_ydata(self.robot_ui_object.robot.data_logs.log_xdot_cmd)
                    self.plot_ref_list[4].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[4].set_ydata(self.robot_ui_object.robot.data_logs.log_psidot_cmd)
                    # bring back cached background
                    self.canvas.restore_region(self.cached_bg)
                    # draw artists only
                    for a in self.artists:
                        self.figure.draw_artist(a)
        elif self.plot_index == 2:
            # check if plot reference has been created already
            if self.plot_ref_list[0] is None:
                self.plot_ref_list[0], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_x_cmd,
                                                      self.robot_ui_object.robot.data_logs.log_y_cmd,
                                                      marker=".",
                                                      markersize=5,
                                                      label=self.artists_labels[0],
                                                      animated=True,
                                                      color=self.artists_colors[0])
                self.plot_ref_list[1], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_x,
                                                      self.robot_ui_object.robot.data_logs.log_y,
                                                      marker=".",
                                                      markersize=5,
                                                      label=self.artists_labels[1],
                                                      animated=True,
                                                      color=self.artists_colors[1])
                # update legend and draw everything
                self.ax.legend(loc="upper right", fontsize="xx-small")
                self.canvas.draw()
                # adjust background
                self.cached_bg = self.canvas.copy_from_bbox(self.figure.bbox)
                # add artists to list for plotting
                self.artists.append(self.plot_ref_list[0])
                self.artists.append(self.plot_ref_list[1])
            else:
                # update data if reference is available and if stop button has not been pressed
                if not self.but_flag_stop:
                    self.plot_ref_list[0].set_xdata(self.robot_ui_object.robot.data_logs.log_x_cmd)
                    self.plot_ref_list[0].set_ydata(self.robot_ui_object.robot.data_logs.log_y_cmd)
                    self.plot_ref_list[1].set_xdata(self.robot_ui_object.robot.data_logs.log_x)
                    self.plot_ref_list[1].set_ydata(self.robot_ui_object.robot.data_logs.log_y)
                    # bring back cached background
                    self.canvas.restore_region(self.cached_bg)
                    # draw artists only
                    for a in self.artists:
                        self.figure.draw_artist(a)
        elif self.plot_index == 3:
            # check if plot reference has been created already
            if self.plot_ref_list[0] is None:
                self.plot_ref_list[0], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_left_torque,
                                                      label=self.artists_labels[0],
                                                      animated=True,
                                                      color=self.artists_colors[0])
                self.plot_ref_list[1], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_right_torque,
                                                      label=self.artists_labels[1],
                                                      animated=True,
                                                      color=self.artists_colors[1])
                self.plot_ref_list[2], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_left_omega,
                                                           label=self.artists_labels[2],
                                                           animated=True,
                                                           color=self.artists_colors[2])
                self.plot_ref_list[3], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_right_omega,
                                                           label=self.artists_labels[3],
                                                           animated=True,
                                                           color=self.artists_colors[3])
                # update legend and draw everything
                lines = [self.plot_ref_list[0], self.plot_ref_list[1], self.plot_ref_list[2],
                         self.plot_ref_list[3]]
                labels = [line.get_label() for line in lines]
                self.ax.legend(lines, labels, loc="upper right", fontsize="xx-small")
                self.canvas.draw()
                # adjust background
                self.cached_bg = self.canvas.copy_from_bbox(self.figure.bbox)
                # add artists to list for plotting
                self.artists.append(self.plot_ref_list[0])
                self.artists.append(self.plot_ref_list[1])
                self.artists.append(self.plot_ref_list[2])
                self.artists.append(self.plot_ref_list[3])
            else:
                # update data if reference is available and if stop button has not been pressed
                if not self.but_flag_stop:
                    self.plot_ref_list[0].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[0].set_ydata(self.robot_ui_object.robot.data_logs.log_left_torque)
                    self.plot_ref_list[1].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[1].set_ydata(self.robot_ui_object.robot.data_logs.log_right_torque)
                    self.plot_ref_list[2].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[2].set_ydata(self.robot_ui_object.robot.data_logs.log_left_omega)
                    self.plot_ref_list[3].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[3].set_ydata(self.robot_ui_object.robot.data_logs.log_right_omega)
                    # bring back cached background
                    self.canvas.restore_region(self.cached_bg)
                    # draw artists only
                    for a in self.artists:
                        self.figure.draw_artist(a)
        elif self.plot_index == 4:
            # check if plot reference has been created already
            if self.plot_ref_list[0] is None:
                self.plot_ref_list[0], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_imu_wx,
                                                           label=self.artists_labels[0],
                                                           animated=True,
                                                           color=self.artists_colors[0])
                self.plot_ref_list[1], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_imu_wy,
                                                           label=self.artists_labels[1],
                                                           animated=True,
                                                           color=self.artists_colors[1])
                self.plot_ref_list[2], = self.ax_twin.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                           self.robot_ui_object.robot.data_logs.log_imu_wz,
                                                           label=self.artists_labels[2],
                                                           animated=True,
                                                           color=self.artists_colors[2])
                self.plot_ref_list[3], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_imu_ax,
                                                      label=self.artists_labels[3],
                                                      animated=True,
                                                      color=self.artists_colors[3])
                self.plot_ref_list[4], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_imu_ay,
                                                      label=self.artists_labels[4],
                                                      animated=True,
                                                      color=self.artists_colors[4])
                self.plot_ref_list[5], = self.ax.plot(self.robot_ui_object.robot.data_logs.log_t,
                                                      self.robot_ui_object.robot.data_logs.log_imu_az,
                                                      label=self.artists_labels[5],
                                                      animated=True,
                                                      color=self.artists_colors[5])
                # update legend and draw everything

                lines = [self.plot_ref_list[0], self.plot_ref_list[1], self.plot_ref_list[2],
                         self.plot_ref_list[3], self.plot_ref_list[4], self.plot_ref_list[5]]
                labels = [line.get_label() for line in lines]
                self.ax.legend(lines, labels, loc="upper right", fontsize="xx-small")
                self.canvas.draw()
                # adjust background
                self.cached_bg = self.canvas.copy_from_bbox(self.figure.bbox)
                # add artists to list for plotting
                self.artists.append(self.plot_ref_list[0])
                self.artists.append(self.plot_ref_list[1])
                self.artists.append(self.plot_ref_list[2])
                self.artists.append(self.plot_ref_list[3])
                self.artists.append(self.plot_ref_list[4])
                self.artists.append(self.plot_ref_list[5])
            else:
                # update data if reference is available and if stop button has not been pressed
                if not self.but_flag_stop:
                    self.plot_ref_list[0].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[0].set_ydata(self.robot_ui_object.robot.data_logs.log_imu_wx)
                    self.plot_ref_list[1].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[1].set_ydata(self.robot_ui_object.robot.data_logs.log_imu_wy)
                    self.plot_ref_list[2].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[2].set_ydata(self.robot_ui_object.robot.data_logs.log_imu_wz)
                    self.plot_ref_list[3].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[3].set_ydata(self.robot_ui_object.robot.data_logs.log_imu_ax)
                    self.plot_ref_list[4].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[4].set_ydata(self.robot_ui_object.robot.data_logs.log_imu_ay)
                    self.plot_ref_list[5].set_xdata(self.robot_ui_object.robot.data_logs.log_t)
                    self.plot_ref_list[5].set_ydata(self.robot_ui_object.robot.data_logs.log_imu_az)
                    # bring back cached background
                    self.canvas.restore_region(self.cached_bg)
                    # draw artists only
                    for a in self.artists:
                        self.figure.draw_artist(a)
        else:
            pass
        # show on screen and update image
        self.canvas.blit(self.figure.bbox)
        # process pending tasks from matplotlib event loop
        self.canvas.flush_events()