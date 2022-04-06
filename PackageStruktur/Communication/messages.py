# General
from ctypes import c_float
from typing import *

import ctypes
import numpy as np
import time
from ctypes import *
from queue import Queue
from params import *

# My Imports
from Robot.data import *
from general import *


class MessageHandler:
    def __init__(self):
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.host_in_dictionary = {}
        self.wait_list = []

    def handler(self, msg):
        if msg.id in self.host_in_dictionary:
            msg_cast = self.host_in_dictionary[msg.id](msg)
            msg_cast.handler()
        else:
            print("received a message with unknown id 0x{:02X}".format(msg.id))

    def update(self):
        if self.incoming_queue.qsize() > 0:
            raw_string = self.incoming_queue.get_nowait()
            msg = msg_parser(raw_string)
            if msg is not -1:
                # print("Received a msg with id {0}".format(msg.id))
                if msg.id not in self.wait_list:
                    self.handler(msg)

    def wait_for_message(self, msg_id, timeout_ms, execute=False):
        time_start = time.time_ns()
        self.wait_list.append(msg_id)
        while (time.time_ns() - time_start) < (timeout_ms * 1000 * 1000):
            if self.incoming_queue.qsize() > 0:
                msg = msg_parser(self.incoming_queue.get_nowait())
                if msg is not -1:
                    if msg.id == msg_id:
                        if execute:
                            self.handler(msg)
                        self.wait_list.remove(msg_id)
                        return msg
                    else:
                        self.handler(msg)
        return -1


# =====================================================================================================
# =====================================================================================================
# ======================================================================================================================
# HOST IN

class MSG_HOST_IN_DEBUG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("string", c_char * 40)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "DEBUG: {} (tick={})".format(self.data.string.decode().rstrip("0"),
                                              str(self.data.tick))
        string = string.rstrip("0")
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CONTINIUOS(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8), ("x", c_float), ("y", c_float), ("v", c_float),
                    ("theta", c_float),
                    ("theta_dot", c_float), ("psi", c_float), ("psi_dot", c_float), ("gyr", c_float * 3),
                    ("acc", c_float * 3),
                    ("torque_left", c_float), ("omega_left", c_float), ("torque_right", c_float),
                    ("omega_right", c_float), ("ctrl_state", c_uint8), ("u", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)
                    ]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        # hack to avoid a flashing checkbox when changing ctrl states (gb3/gb4 in robot ui)
        if robot_ui_object.robot.controller.state == CTRL_STATE.STATE_FEEDBACK and \
                CTRL_STATE(self.data.ctrl_state) == CTRL_STATE.VELOCITY:
            robot_ui_object.update_checkboxes_flag = True
        elif robot_ui_object.robot.controller.state == CTRL_STATE.VELOCITY and \
                CTRL_STATE(self.data.ctrl_state) == CTRL_STATE.STATE_FEEDBACK:
            robot_ui_object.update_checkboxes_flag = True

        # update data
        robot_ui_object.robot.tick = self.data.tick
        robot_ui_object.robot.fsm_state = FSM_STATE(self.data.fsm_state)
        robot_ui_object.robot.state.x = self.data.x
        robot_ui_object.robot.state.y = self.data.y
        robot_ui_object.robot.state.sdot = self.data.v
        robot_ui_object.robot.state.theta = self.data.theta  # *180/3.14159  # °
        robot_ui_object.robot.state.thetadot = self.data.theta_dot  # rad/s
        robot_ui_object.robot.state.psi = self.data.psi  # *180/3.14159  # °
        robot_ui_object.robot.state.psidot = self.data.psi_dot  # rad/s
        robot_ui_object.robot.sensors.imu.gyr = list(self.data.gyr)
        robot_ui_object.robot.sensors.imu.acc = list(self.data.acc)
        robot_ui_object.robot.sensors.encoder_left.omega = self.data.omega_left  # rad/s
        robot_ui_object.robot.sensors.encoder_right.omega = self.data.omega_right  # rad/s
        robot_ui_object.robot.drive.torque_left = self.data.torque_left
        robot_ui_object.robot.drive.torque_right = self.data.torque_right
        robot_ui_object.robot.controller.state = CTRL_STATE(self.data.ctrl_state)
        robot_ui_object.robot.controller.u = list(self.data.u)
        robot_ui_object.robot.controller.xdot_cmd = self.data.xdot_cmd
        robot_ui_object.robot.controller.psidot_cmd = self.data.psidot_cmd

    def get_string(self):
        string = ''
        return string

    def get_color(self):
        color = None
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_DYNAMICS(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("x", c_float), ("y", c_float), ("v", c_float), ("theta", c_float),
                    ("theta_dot", c_float), ("psi", c_float), ("psi_dot", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.state.x = self.data.x
        robot_ui_object.robot.state.y = self.data.y
        robot_ui_object.robot.state.sdot = self.data.v
        robot_ui_object.robot.state.theta = self.data.theta
        robot_ui_object.robot.state.thetadot = self.data.theta_dot
        robot_ui_object.robot.state.psi = self.data.psi
        robot_ui_object.robot.state.psidot = self.data.psi_dot

    def get_string(self):
        string = ''
        return string

    def get_color(self):
        color = None
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_FSM(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.fsm_state = FSM_STATE(self.data.fsm_state)

        if robot_ui_object.robot.fsm_state == FSM_STATE.IDLE:
            # rumble so that you know that you have entered the IDLE state again (after successfully initializing)
            if robot_ui_object.joystick_enable:
                iid = robot_ui_object.joystick_instance_id
                robot_ui_object.main_ui_object.joystick_handler.rumble(iid, rumble_type='strong')

    def get_string(self):
        string = "Robot transitioned to state {}!".format(FSM_STATE(self.data.fsm_state).name)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_IMU(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("gyr", c_float * 3), ("acc", c_float * 3)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.sensors.imu.gyr = list(self.data.gyr)
        robot_ui_object.robot.sensors.imu.acc = list(self.data.acc)

    def get_string(self):
        string = ''
        return string

    def get_color(self):
        color = None
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_DRIVE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("state_left", c_uint8), ("torque_left", c_float), ("omega_left", c_float),
                    ("angle_left", c_float), ("state_right", c_uint8), ("torque_right", c_float),
                    ("omega_right", c_float),
                    ("angle_right", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.sensors.encoder_left.omega = self.data.omega_left
        robot_ui_object.robot.sensors.encoder_right.omega = self.data.omega_right
        robot_ui_object.robot.sensors.encoder_left.angle = self.data.angle_left
        robot_ui_object.robot.sensors.encoder_right.angle = self.data.angle_right
        robot_ui_object.robot.drive.torque_left = self.data.torque_left
        robot_ui_object.robot.drive.torque_right = self.data.torque_right

    def get_string(self):
        string = ''
        return string

    def get_color(self):
        color = None
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CTRL_STATE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("external_torque", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.state = CTRL_STATE(self.data.ctrl_state)
        robot_ui_object.robot.controller.external_torque = self.data.external_torque
        robot_ui_object.robot.controller.xdot_cmd = self.data.xdot_cmd
        robot_ui_object.robot.controller.psidot_cmd = self.data.psidot_cmd

    def get_string(self):
        string = "Robot transitioned to state {}!\n" \
                 "u_l={:.2f}, u_r={:.2f}, xdot_cmd={:.2f}, psidot_cmd={:.2f}".format(CTRL_STATE(self.data.ctrl_state).name,
                                                                                       self.data.external_torque[0],
                                                                                       self.data.external_torque[1],
                                                                                       self.data.xdot_cmd,
                                                                                       self.data.psidot_cmd)
        return string

    def get_color(self):
        color = 'G'
        return color


class MSG_HOST_IN_CTRL_INPUT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("external_torque", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.state = CTRL_STATE(self.data.ctrl_state)
        robot_ui_object.robot.controller.external_torque = self.data.external_torque
        robot_ui_object.robot.controller.xdot_cmd = self.data.xdot_cmd
        robot_ui_object.robot.controller.psidot_cmd = self.data.psidot_cmd

    def get_string(self):
        string = ''
        # FEEDBACK DEACTIVATED CURRENTLY
        # string = "Control input changed successfully!\n" \
        #          "u_l={:.2f}, u_r={:.2f}, xdot_cmd={:.2f}, psidot_cmd={:.2f}".format(self.data.external_torque[0],
        #                                                                              self.data.external_torque[1],
        #                                                                              self.data.xdot_cmd,
        #                                                                              self.data.psidot_cmd)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CTRL_SF_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("K", c_float * 12)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.state_feedback.K = np.reshape(self.data.K, (2, 6))

    def get_string(self):
        string = "State Feedback has been configured successfully! \n" \
                 "K={}".format(np.reshape(self.data.K, (2, 6)))
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CTRL_SC_X_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.xdot_ctrl.P = self.data.P
        robot_ui_object.robot.controller.xdot_ctrl.I = self.data.I
        robot_ui_object.robot.controller.xdot_ctrl.D = self.data.D
        robot_ui_object.robot.controller.xdot_ctrl.enable_limit = self.data.enable_limit
        robot_ui_object.robot.controller.xdot_ctrl.max = self.data.v_max
        robot_ui_object.robot.controller.xdot_ctrl.min = self.data.v_min
        robot_ui_object.robot.controller.xdot_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot_ui_object.robot.controller.xdot_ctrl.dmax = self.data.vdot_max
        robot_ui_object.robot.controller.xdot_ctrl.dmin = self.data.vdot_min

    def get_string(self):
        string = "Speed Controller (XDOT) has been configured successfully! \n" \
                 "P={:.5}, I={:.5f}, D={:.5f}, enable_limit={:d}, v_max={:.2f}, v_min={:.2f}, \n" \
                 "enable_rate_limit={:d}, vdot_max={:.2f}, vdot_min={:.2f}".format(self.data.P,
                                                                                   self.data.I,
                                                                                   self.data.D,
                                                                                   self.data.enable_limit,
                                                                                   self.data.v_max,
                                                                                   self.data.v_min,
                                                                                   self.data.enable_rate_limit,
                                                                                   self.data.vdot_max,
                                                                                   self.data.vdot_min)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CTRL_SC_PSI_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.psidot_ctrl.P = self.data.P
        robot_ui_object.robot.controller.psidot_ctrl.I = self.data.I
        robot_ui_object.robot.controller.psidot_ctrl.D = self.data.D
        robot_ui_object.robot.controller.psidot_ctrl.enable_limit = self.data.enable_limit
        robot_ui_object.robot.controller.psidot_ctrl.max = self.data.v_max
        robot_ui_object.robot.controller.psidot_ctrl.min = self.data.v_min
        robot_ui_object.robot.controller.psidot_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot_ui_object.robot.controller.psidot_ctrl.dmax = self.data.vdot_max
        robot_ui_object.robot.controller.psidot_ctrl.dmin = self.data.vdot_min

    def get_string(self):
        string = "Speed Controller (PSIDOT) has been configured successfully! \n" \
                 "P={:.5f}, I={:.5f}, D={:.5f}, enable_limit={:d}, v_max={:.2f}, v_min={:.2f}, \n" \
                 "enable_rate_limit={:d}, vdot_max={:.2f}, vdot_min={:.2f}".format(self.data.P,
                                                                                   self.data.I,
                                                                                   self.data.D,
                                                                                   self.data.enable_limit,
                                                                                   self.data.v_max,
                                                                                   self.data.v_min,
                                                                                   self.data.enable_rate_limit,
                                                                                   self.data.vdot_max,
                                                                                   self.data.vdot_min)
        return string

    def get_color(self):
        color = 'G'
        return color

# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CTRL_PC_DISTANCE_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.distance_ctrl.P = self.data.P
        robot_ui_object.robot.controller.distance_ctrl.I = self.data.I
        robot_ui_object.robot.controller.distance_ctrl.D = self.data.D
        robot_ui_object.robot.controller.distance_ctrl.enable_limit = self.data.enable_limit
        robot_ui_object.robot.controller.distance_ctrl.max = self.data.v_max
        robot_ui_object.robot.controller.distance_ctrl.min = self.data.v_min
        robot_ui_object.robot.controller.distance_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot_ui_object.robot.controller.distance_ctrl.dmax = self.data.vdot_max
        robot_ui_object.robot.controller.distance_ctrl.dmin = self.data.vdot_min

    def get_string(self):
        string = str(self.data.P) + " " \
                 + str(self.data.I) + " " \
                 + str(self.data.D) + " " \
                 + str(self.data.enable_limit) + " " \
                 + str(self.data.v_max) + " " \
                 + str(self.data.v_min) + " " \
                 + str(self.data.enable_rate_limit) + " " \
                 + str(self.data.vdot_max) + " " \
                 + str(self.data.vdot_min)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_CTRL_PC_ANGLE_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.controller.angle_ctrl.P = self.data.P
        robot_ui_object.robot.controller.angle_ctrl.I = self.data.I
        robot_ui_object.robot.controller.angle_ctrl.D = self.data.D
        robot_ui_object.robot.controller.angle_ctrl.enable_limit = self.data.enable_limit
        robot_ui_object.robot.controller.angle_ctrl.max = self.data.v_max
        robot_ui_object.robot.controller.angle_ctrl.min = self.data.v_min
        robot_ui_object.robot.controller.angle_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot_ui_object.robot.controller.angle_ctrl.dmax = self.data.vdot_max
        robot_ui_object.robot.controller.angle_ctrl.dmin = self.data.vdot_min

    def get_string(self):
        string = str(self.data.P) + " " \
                 + str(self.data.I) + " " \
                 + str(self.data.D) + " " \
                 + str(self.data.enable_limit) + " " \
                 + str(self.data.v_max) + " " \
                 + str(self.data.v_min) + " " \
                 + str(self.data.enable_rate_limit) + " " \
                 + str(self.data.vdot_max) + " " \
                 + str(self.data.vdot_min)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_ERROR(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("error_id", c_uint8), ("data", c_char * 80)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        # signal error message if joystick is enabled
        if robot_ui_object.joystick_enable:
            iid = robot_ui_object.joystick_instance_id
            robot_ui_object.main_ui_object.joystick_handler.rumble(iid, rumble_type='strong')

    def get_string(self):
        error_data = self.data.data.decode().rstrip("0")
        string = "Error 0x{:02X}: {:s}".format(self.data.error_id, error_data)
        return string

    def get_color(self):
        color = 'R'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("running", c_uint8), ("file", c_char * 40)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass
        # file_string = self.data.data.decode("ascii").rstrip("0")
        # debug_str = "Received an experiment msg"
        # io_msg_queue.put_nowait((debug_str, "response"))

    def get_string(self):
        string = str(self.data.tick) + " " \
                 + str(self.data.running) + " " \
                 + self.data.file.decode().rstrip("0")
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_LOGGING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("running", c_uint8), ("file", c_char * 40)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.logging.running = self.data.running
        robot_ui_object.robot.logging.file = self.data.file.decode().rstrip("0")

    def get_string(self):
        if self.data.running:
            filename = self.data.file.decode().rstrip("0")
            string = 'ML started logging! ({})'.format(filename)
        else:
            filename = self.data.file.decode().rstrip("0")
            string = 'ML stopped logging! ({})'.format(filename)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_INFO(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("data", c_char * 60)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass
        # info_string = self.data.data.decode("ascii")
        # info_string = info_string.rstrip("0")
        # io_msg_queue.put_nowait((info_string, "response"))

    def get_string(self):
        string = self.data.data.decode().rstrip("0")
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_SV_CTRL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("sv_number", c_uint8), ("sv_enable_list", c_uint8 * 9)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        robot_ui_object.robot.supervisor.sv_enable_list = list(self.data.sv_enable_list)
        robot_ui_object.robot.sv_number = self.data.sv_number

    def get_string(self):
        string = "Supervisor settings changed successfully!\n" \
                 "sv_number={}, sv_enable_list={}".format(self.data.sv_number, list(self.data.sv_enable_list))
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_RESET_STATE_VEC(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "State vector was reset successfully!"
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_DELAY(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("delay", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "ML message handling delayed for {:.2f} seconds successfully!".format(self.data.delay)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_LOAD_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ('ctrl_state', c_uint8), ('input_length', c_uint16)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "Loaded experiment '{}' successfully! \n" \
                 "ctrl_state={}, input_length={}".format(self.data.name.decode().rstrip("0"),
                                                         CTRL_STATE(self.data.ctrl_state).name,
                                                         self.data.input_length)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_START_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "Experiment '{}' started successfully! \n" \
                 "ctrl_state={}, sequence_length={}".format(self.data.name.decode().rstrip("0"),
                                                            CTRL_STATE(self.data.ctrl_state).name,
                                                            self.data.sequence_length)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_END_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32),
                    ("sequence_counter", c_uint32), ("success", c_uint8)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        # remove from loaded elements
        error_gcodes, end_gcodes = experiment_handler.remove_experiment(self.data.name.decode().rstrip("0"))

        # execute commands after ending the experiment, including the exit code
        if self.data.success:
            for cmd in end_gcodes:
                robot_ui_object.enter_cmd_into_robot_terminal(cmd)
        else:
            for cmd in error_gcodes:
                robot_ui_object.enter_cmd_into_robot_terminal(cmd)

    def get_string(self):
        string = "Experiment '{}' ended with success={}! \n" \
                 "ctrl_state={}, sequence_length={}, sequence_counter={}".format(self.data.name.decode().rstrip("0"),
                                                                                 self.data.success,
                                                                                 CTRL_STATE(self.data.ctrl_state).name,
                                                                                 self.data.sequence_length,
                                                                                 self.data.sequence_counter)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_LOAD_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ('ctrl_state', c_uint8), ('input_length', c_uint16)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "Loaded sequence '{}' successfully! \n" \
                 "ctrl_state={}, input_length={}".format(self.data.name.decode().rstrip("0"),
                                                         CTRL_STATE(self.data.ctrl_state).name,
                                                         self.data.input_length)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_START_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        pass

    def get_string(self):
        string = "Sequence '{}' started successfully! \n" \
                 "ctrl_state={}, sequence_length={}".format(self.data.name.decode().rstrip("0"),
                                                            CTRL_STATE(self.data.ctrl_state).name,
                                                            self.data.sequence_length)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_END_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32),
                    ("sequence_counter", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self, robot_ui_object, experiment_handler, sequence_handler):
        # remove from loaded elements
        sequence_handler.remove_sequence(self.data.name.decode().rstrip("0"))

    def get_string(self):
        string = "Sequence '{}' ended successfully! \n" \
                 "ctrl_state={}, sequence_length={}, sequence_counter={}".format(self.data.name.decode().rstrip("0"),
                                                                                 CTRL_STATE(self.data.ctrl_state).name,
                                                                                 self.data.sequence_length,
                                                                                 self.data.sequence_counter)
        return string

    def get_color(self):
        color = 'G'
        return color


# ----------------------------------------------------------------------------------------------------------------------

# ======================================================================================================================
# HOST OUT


class MSG_HOST_OUT_DEBUG(Message):  # M0
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("string", c_char * 40)]

    def __init__(self, tick, debug_string):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_DEBUG
        by = bytes(debug_string, "utf-8")
        by += b"0" * (40 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_MOCAP(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("x", c_float), ("y", c_float), ("theta", c_float), ("psi", c_float)]

    def __init__(self, tick, x, y, theta, psi):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_MOCAP
        self.data = self.msg_structure(tick, x, y, theta, psi)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_FSM(Message):  # M1
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8)]

    def __init__(self, tick, fsm_state: FSM_STATE):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_FSM
        self.data = self.msg_structure(tick, fsm_state.value)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_STATE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8)]

    def __init__(self, tick, ctrl_state: CTRL_STATE):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_STATE
        self.data = self.msg_structure(tick, ctrl_state.value)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_INPUT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("external_torque", c_float * 2), ("xdot_cmd", c_float), ("psidot_cmd", c_float)]

    def __init__(self, tick, external_torque, xdot_cmd, psidot_cmd):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_INPUT
        self.data = self.msg_structure(tick, external_torque, xdot_cmd, psidot_cmd)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_SF_CONFIG(Message):  # M11
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("K", c_float * 12)]

    def __init__(self, tick, K: np.ndarray((2, 6))):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_SF_CONFIG
        self.data = self.msg_structure(tick, tuple(K.flatten()))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_SC_X_CONFIG(Message):  # M12
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_SC_X_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_SC_PSI_CONFIG(Message):  # M13
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_SC_PSI_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_PC_DISTANCE_CONFIG(Message):  # M17
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_PC_DISTANCE_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CTRL_PC_ANGLE_CONFIG(Message):  # M18
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CTRL_PC_ANGLE_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_SELFTEST(Message):  # M14
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, tick):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_SELFTEST
        self.data = self.msg_structure(tick)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_CALIBRATION(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, tick):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_CALIBRATION
        self.data = self.msg_structure(tick)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_LOGGING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("enable", c_uint8), ("file", c_char * 40)]

    def __init__(self, tick, running, file):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_LOGGING
        by = bytes(file, "utf-8")
        by += b"0" * (40 - len(by))
        self.data = self.msg_structure(tick, running, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("start", c_uint8), ("file", c_char * 40)]

    def __init__(self, tick, running, file):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_EXPERIMENT
        by = bytes(file, "utf-8")
        by += b"0" * (40 - len(by))
        self.data = self.msg_structure(tick, running, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_HEADING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("heading", c_float)]

    def __init__(self, tick, heading):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_HEADING
        self.data = self.msg_structure(tick, heading)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_MOVE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("xdot", c_float), ("psidot", c_float), ("time", c_float)]

    def __init__(self, tick, xdot, psidot, time):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_MOVE
        self.data = self.msg_structure(tick, xdot, psidot, time)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_SV_CTRL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("sv_number", c_uint8), ("sv_enable_list", c_uint8 * 9)]

    def __init__(self, tick, sv_number, sv_enable_list):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_SV_CTRL
        self.data = self.msg_structure(tick, sv_number, tuple(sv_enable_list))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_RESET_STATE_VEC(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, tick):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_RESET_STATE_VEC
        self.data = self.msg_structure(tick)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_DELAY(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("delay", c_float)]

    def __init__(self, tick, delay):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_DELAY
        self.data = self.msg_structure(tick, delay)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_LOAD_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [('tick', c_uint32), ('name', c_char * 30), ('sampling_frequency', c_uint8),
                    ('duration', c_uint8), ('hardware_version', c_float), ('software_version', c_float),
                    ('ctrl_state', c_uint8), ('logging_active', c_bool), ('filename', c_char * 20),

                    ('input_length', c_uint16), ('input1', c_float * 2000), ('input2', c_float * 2000),

                    ('fsm_state_condition', c_uint8), ('fsm_state_threshold', c_float),
                    ('ctrl_state_condition', c_uint8), ('ctrl_state_threshold', c_float),

                    ('x_condition', c_uint8), ('x_threshold', c_float),
                    ('y_condition', c_uint8), ('y_threshold', c_float),
                    ('x_dot_condition', c_uint8), ('x_dot_threshold', c_float),
                    ('theta_condition', c_uint8), ('theta_threshold', c_float),
                    ('theta_dot_condition', c_uint8), ('theta_dot_threshold', c_float),
                    ('psi_condition', c_uint8), ('psi_threshold', c_float),
                    ('psi_dot_condition', c_uint8), ('psi_dot_threshold', c_float),
                    ('gyr_x_condition', c_uint8), ('gyr_x_threshold', c_float),
                    ('gyr_y_condition', c_uint8), ('gyr_y_threshold', c_float),
                    ('gyr_z_condition', c_uint8), ('gyr_z_threshold', c_float),
                    ('acc_x_condition', c_uint8), ('acc_x_threshold', c_float),
                    ('acc_y_condition', c_uint8), ('acc_y_threshold', c_float),
                    ('acc_z_condition', c_uint8), ('acc_z_threshold', c_float),
                    ('torque_left_condition', c_uint8), ('torque_left_threshold', c_float),
                    ('omega_left_condition', c_uint8), ('omega_left_threshold', c_float),
                    ('torque_right_condition', c_uint8), ('torque_right_threshold', c_float),
                    ('omega_right_condition', c_uint8), ('omega_right_threshold', c_float),
                    ('u1_condition', c_uint8), ('u1_threshold', c_float),
                    ('u2_condition', c_uint8), ('u2_threshold', c_float),

                    ('abs_x_condition', c_uint8), ('abs_x_threshold', c_float),
                    ('abs_y_condition', c_uint8), ('abs_y_threshold', c_float),
                    ('abs_x_dot_condition', c_uint8), ('abs_x_dot_threshold', c_float),
                    ('abs_theta_condition', c_uint8), ('abs_theta_threshold', c_float),
                    ('abs_theta_dot_condition', c_uint8), ('abs_theta_dot_threshold', c_float),
                    ('abs_psi_condition', c_uint8), ('abs_psi_threshold', c_float),
                    ('abs_psi_dot_condition', c_uint8), ('abs_psi_dot_threshold', c_float),
                    ('abs_gyr_x_condition', c_uint8), ('abs_gyr_x_threshold', c_float),
                    ('abs_gyr_y_condition', c_uint8), ('abs_gyr_y_threshold', c_float),
                    ('abs_gyr_z_condition', c_uint8), ('abs_gyr_z_threshold', c_float),
                    ('abs_acc_x_condition', c_uint8), ('abs_acc_x_threshold', c_float),
                    ('abs_acc_y_condition', c_uint8), ('abs_acc_y_threshold', c_float),
                    ('abs_acc_z_condition', c_uint8), ('abs_acc_z_threshold', c_float),
                    ('abs_torque_left_condition', c_uint8), ('abs_torque_left_threshold', c_float),
                    ('abs_omega_left_condition', c_uint8), ('abs_omega_left_threshold', c_float),
                    ('abs_torque_right_condition', c_uint8), ('abs_torque_right_threshold', c_float),
                    ('abs_omega_right_condition', c_uint8), ('abs_omega_right_threshold', c_float),
                    ('abs_u1_condition', c_uint8), ('abs_u1_threshold', c_float),
                    ('abs_u2_condition', c_uint8), ('abs_u2_threshold', c_float)]

    def __init__(self, tick, name, sampling_frequency, duration, hardware_version, software_version, ctrl_state,
                 logging_active, filename, input_length, input1, input2, fsm_state_condition, fsm_state_threshold, ctrl_state_condition,
                 ctrl_state_threshold,  x_condition, x_threshold,  y_condition, y_threshold,  x_dot_condition, x_dot_threshold,
                 theta_condition, theta_threshold,  theta_dot_condition, theta_dot_threshold, psi_condition, psi_threshold,
                 psi_dot_condition, psi_dot_threshold, gyr_x_condition, gyr_x_threshold, gyr_y_condition, gyr_y_threshold,
                 gyr_z_condition, gyr_z_threshold, acc_x_condition, acc_x_threshold, acc_y_condition, acc_y_threshold,
                 acc_z_condition, acc_z_threshold, torque_left_condition, torque_left_threshold, omega_left_condition,
                 omega_left_threshold, torque_right_condition, torque_right_threshold, omega_right_condition,
                 omega_right_threshold, u1_condition, u1_threshold, u2_condition, u2_threshold, abs_x_condition,
                 abs_x_threshold, abs_y_condition, abs_y_threshold, abs_x_dot_condition, abs_x_dot_threshold,
                 abs_theta_condition, abs_theta_threshold, abs_theta_dot_condition, abs_theta_dot_threshold,
                 abs_psi_condition, abs_psi_threshold, abs_psi_dot_condition, abs_psi_dot_threshold,
                 abs_gyr_x_condition, abs_gyr_x_threshold, abs_gyr_y_condition, abs_gyr_y_threshold,
                 abs_gyr_z_condition, abs_gyr_z_threshold, abs_acc_x_condition, abs_acc_x_threshold,
                 abs_acc_y_condition, abs_acc_y_threshold, abs_acc_z_condition, abs_acc_z_threshold,
                 abs_torque_left_condition, abs_torque_left_threshold, abs_omega_left_condition,
                 abs_omega_left_threshold, abs_torque_right_condition, abs_torque_right_threshold,
                 abs_omega_right_condition, abs_omega_right_threshold, abs_u1_condition, abs_u1_threshold,
                 abs_u2_condition, abs_u2_threshold):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_LOAD_EXPERIMENT
        by1 = bytes(name, "utf-8")
        by1 += b"0" * (15 - len(by1))
        by2 = bytes(filename, "utf-8")
        by2 += b"0" * (20 - len(by2))
        if input_length < 2000 or input_length < 2000:
            input1 += [0] * (2000 - input_length)
            input2 += [0] * (2000 - input_length)
        self.data = self.msg_structure(tick, by1, sampling_frequency, duration, hardware_version, software_version, ctrl_state,
                                       logging_active, by2, input_length, input1, input2, fsm_state_condition, fsm_state_threshold, ctrl_state_condition,
                                       ctrl_state_threshold,  x_condition, x_threshold,  y_condition, y_threshold,  x_dot_condition, x_dot_threshold,
                                       theta_condition, theta_threshold,  theta_dot_condition, theta_dot_threshold, psi_condition, psi_threshold,
                                       psi_dot_condition, psi_dot_threshold, gyr_x_condition, gyr_x_threshold, gyr_y_condition, gyr_y_threshold,
                                       gyr_z_condition, gyr_z_threshold, acc_x_condition, acc_x_threshold, acc_y_condition, acc_y_threshold,
                                       acc_z_condition, acc_z_threshold, torque_left_condition, torque_left_threshold, omega_left_condition,
                                       omega_left_threshold, torque_right_condition, torque_right_threshold, omega_right_condition,
                                       omega_right_threshold, u1_condition, u1_threshold, u2_condition, u2_threshold, abs_x_condition,
                                       abs_x_threshold, abs_y_condition, abs_y_threshold, abs_x_dot_condition, abs_x_dot_threshold,
                                       abs_theta_condition, abs_theta_threshold, abs_theta_dot_condition, abs_theta_dot_threshold,
                                       abs_psi_condition, abs_psi_threshold, abs_psi_dot_condition, abs_psi_dot_threshold,
                                       abs_gyr_x_condition, abs_gyr_x_threshold, abs_gyr_y_condition, abs_gyr_y_threshold,
                                       abs_gyr_z_condition, abs_gyr_z_threshold, abs_acc_x_condition, abs_acc_x_threshold,
                                       abs_acc_y_condition, abs_acc_y_threshold, abs_acc_z_condition, abs_acc_z_threshold,
                                       abs_torque_left_condition, abs_torque_left_threshold, abs_omega_left_condition,
                                       abs_omega_left_threshold, abs_torque_right_condition, abs_torque_right_threshold,
                                       abs_omega_right_condition, abs_omega_right_threshold, abs_u1_condition, abs_u1_threshold,
                                       abs_u2_condition, abs_u2_threshold)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_START_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, tick, name):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_START_EXPERIMENT
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_END_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, tick, name):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_END_EXPERIMENT
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_LOAD_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ('ctrl_state', c_uint8),
                    ('input_length', c_uint16), ('input1', c_float * 2000), ('input2', c_float * 2000)]

    def __init__(self, tick, name, ctrl_state, input_length, input1, input2):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_LOAD_SEQUENCE
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        if input_length < 2000 or input_length < 2000:
            input1 += [0] * (2000 - input_length)
            input2 += [0] * (2000 - input_length)
        self.data = self.msg_structure(tick, by, ctrl_state, input_length, tuple(input1), tuple(input2))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_START_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, tick, name):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_START_SEQUENCE
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_OUT_END_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, tick, name):
        super().__init__()
        self.id = ID_MSG_HOST_OUT_END_SEQUENCE
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


msg_dictionary = {
    ID_MSG_HOST_IN_DEBUG: MSG_HOST_IN_DEBUG,
    ID_MSG_HOST_IN_DYNAMICS: MSG_HOST_IN_DYNAMICS,
    ID_MSG_HOST_IN_FSM: MSG_HOST_IN_FSM,
    ID_MSG_HOST_IN_IMU: MSG_HOST_IN_IMU,
    ID_MSG_HOST_IN_DRIVE: MSG_HOST_IN_DRIVE,
    ID_MSG_HOST_IN_CTRL_STATE: MSG_HOST_IN_CTRL_STATE,
    ID_MSG_HOST_IN_CTRL_INPUT: MSG_HOST_IN_CTRL_INPUT,
    ID_MSG_HOST_IN_CTRL_SF_CONFIG: MSG_HOST_IN_CTRL_SF_CONFIG,
    ID_MSG_HOST_IN_CTRL_SC_X_CONFIG: MSG_HOST_IN_CTRL_SC_X_CONFIG,
    ID_MSG_HOST_IN_CTRL_SC_PSI_CONFIG: MSG_HOST_IN_CTRL_SC_PSI_CONFIG,
    ID_MSG_HOST_IN_ERROR: MSG_HOST_IN_ERROR,
    ID_MSG_HOST_IN_LOGGING: MSG_HOST_IN_LOGGING,
    ID_MSG_HOST_IN_INFO: MSG_HOST_IN_INFO,
    ID_MSG_HOST_IN_CONT: MSG_HOST_IN_CONTINIUOS,
    ID_MSG_HOST_IN_SV_CTRL: MSG_HOST_IN_SV_CTRL,
    ID_MSG_HOST_IN_RESET_STATE_VEC: MSG_HOST_IN_RESET_STATE_VEC,
    ID_MSG_HOST_IN_DELAY: MSG_HOST_IN_DELAY,
    ID_MSG_HOST_IN_LOAD_EXPERIMENT: MSG_HOST_IN_LOAD_EXPERIMENT,
    ID_MSG_HOST_IN_START_EXPERIMENT: MSG_HOST_IN_START_EXPERIMENT,
    ID_MSG_HOST_IN_END_EXPERIMENT: MSG_HOST_IN_END_EXPERIMENT,
    ID_MSG_HOST_IN_LOAD_SEQUENCE: MSG_HOST_IN_LOAD_SEQUENCE,
    ID_MSG_HOST_IN_START_SEQUENCE: MSG_HOST_IN_START_SEQUENCE,
    ID_MSG_HOST_IN_END_SEQUENCE: MSG_HOST_IN_END_SEQUENCE}
