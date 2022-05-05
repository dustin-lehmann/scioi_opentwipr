import numpy as np
from params import *
from ctypes import *
import time
from typing import List, Dict, Tuple, Optional, Union

from global_objects import crc_check, msg_parser, msg_builder, robot, send_msg_to_ll, send_msg_to_host, global_values, Message, client
from Communication.communication import *
from robot import FSM_STATE, CTRL_STATE, Robot
from Experiment.experiment import logger, experiment_handler, sequence_handler

time_last = time.time_ns()
counter = 0


class MessageHandler:

    def __init__(self, handler_type):
        self.handler_type = handler_type  # either 'HL' msg handler (for HL OUT) or 'LL' msg handler (for LL OUT)
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.msg_dictionary = {}
        self.wait_list = []
        self.wait_msg = Message()
        self.flag_waiting = False
        self.block = False  # for now, only messages received from the host are blocked
        self.list_of_allowed_messages = []

    def start_blocking(self):
        self.block = True

    def stop_blocking(self):
        self.block = False

    def handler(self, msg):
        if msg.id in self.msg_dictionary:
            msg_cast = self.msg_dictionary[msg.id](msg)
            msg_cast.handler()
        else:
            print("Received a message with unknown id! ({:X})".format(msg.id))

    def update(self):
        if self.incoming_queue.qsize() > 0:
            received_bytes = self.incoming_queue.get_nowait()
            if not crc_check(received_bytes):
                print('Invalid CRC8 byte!')
                msg = MSG_HOST_IN_ERROR(global_values['tick'], ERROR_MSG_CORRUPTED,
                                        "HL received message with invalid CRC8 byte! Please try again!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HL!")
            else:
                msg = msg_parser(received_bytes)
                # check if messages in waiting queue
                if msg.id in self.wait_list:
                    self.wait_list.remove(msg.id)
                    if msg.id in self.msg_dictionary:
                        self.wait_msg = self.msg_dictionary[msg.id](msg)
                # block messages if necessary
                if self.block:
                    # some messages are allowed in blocking state
                    if self.allowed(msg.id):
                        self.handler(msg)
                        return
                    # inform HL every time a message was blocked
                    if self.handler_type == 'HL':
                        # send error message to HL
                        print("Blocked message from HL! (id={})".format(hex(msg.id)))
                        msg = MSG_HOST_IN_ERROR(global_values['tick'], ERROR_HL_MSG_HANDLER_BLOCK,
                                                "HL message handler in blocking state!")
                        if not send_msg_to_host(msg):
                            print("Failed to send message to HL!")
                    else:
                        # when blocking outgoing messages from LL (not in use currently)
                        print("Blocked message from LL! (id={})".format(hex(msg.id)))
                        msg = MSG_HOST_IN_ERROR(global_values['tick'], ERROR_LL_MSG_HANDLER_BLOCK,
                                                "LL message handler in blocking state!")
                        if not send_msg_to_host(msg):
                            print("Failed to send message to HL!")
                else:
                    self.handler(msg)
                    # show incoming HL messages
                    # if self.handler_type == 'HL':
                    #     print(received_bytes.hex())

    def allowed(self, msg_id: int) -> int:
        if msg_id in self.list_of_allowed_messages:
            return 1
        return 0


# TODO: clean up import structure, danger of cyclic imports
msg_hndlr_ll = MessageHandler('LL')
msg_hndlr_host = MessageHandler('HL')


def wait_for_msg(msg_handler: MessageHandler, msg_id, timeout_ms):
    msg_handler.wait_list.append(msg_id)
    time_start = time.time_ns()
    while (time.time_ns() - time_start) < (timeout_ms * 1000 * 1000):
        if msg_id not in msg_handler.wait_list:
            return msg_handler.wait_msg
        time.sleep(0.01)
    return None


# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
# LL IN

class MSG_LL_IN_FSM(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8)]

    def __init__(self, tick, fsm_state: FSM_STATE):
        super().__init__()
        self.id = ID_MSG_LL_IN_FSM
        self.data = self.msg_structure(tick, fsm_state.value)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_CTRL_STATE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8)]

    def __init__(self, tick, fsm_state: FSM_STATE):
        super().__init__()
        self.id = ID_MSG_LL_IN_CTRL_STATE
        self.data = self.msg_structure(tick, fsm_state.value)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_CTRL_INPUT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("external_torque", c_float * 2), ("xdot_cmd", c_float), ("psidot_cmd", c_float)]

    def __init__(self, tick, external_torque: list, xdot_cmd: float, psidot_cmd: float):
        super().__init__()
        self.id = ID_MSG_LL_IN_CTRL_INPUT
        self.data = self.msg_structure(tick, (c_float * 2)(*external_torque), xdot_cmd, psidot_cmd)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_CTRL_INPUT_BUFFER_VEL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("xdot_cmd", c_float * 100), ("psidot_cmd", c_float * 100)]

    def __init__(self, tick, xdot_cmd: list, psidot_cmd: list):
        super().__init__()
        self.id = ID_MSG_LL_IN_CTRL_INPUT_BUFFER_VEL
        # xdot_cmd = xdot_cmd + (100 - len(xdot_cmd)) * [0]
        # psidot_cmd = psidot_cmd + (100 - len(psidot_cmd)) * [0]
        self.data = self.msg_structure(tick, (c_float*100)(*xdot_cmd), (c_float*100)(*psidot_cmd))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_CTRL_SF_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("K", c_float * 12)]

    def __init__(self, tick, K: np.ndarray((2, 6))):
        super().__init__()
        self.id = ID_MSG_LL_IN_SF_CONFIG
        self.data = self.msg_structure(tick, tuple(K.flatten()))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_CTRL_SC_X_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_LL_IN_CTRL_SC_X_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------
class MSG_LL_IN_CTRL_SC_PSI_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_LL_IN_CTRL_SC_PSI_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_CALIBRATION_VALS(Message):
    pass


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_DEBUG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("string", c_char * 40)]

    def __init__(self, tick, debug_string):
        super().__init__()
        self.id = ID_MSG_LL_IN_DEBUG
        by = bytes(debug_string, "utf-8")
        by += b"0" * (40 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_HANDSHAKE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, tick):
        super().__init__()
        self.id = ID_MSG_LL_IN_HANDSHAKE
        self.data = self.msg_structure(tick)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_HEADING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("heading", c_float)]

    def __init__(self, tick, heading):
        super().__init__()
        self.id = ID_MSG_LL_IN_HEADING
        self.data = self.msg_structure(tick, heading)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_SV_CTRL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("sv_number", c_uint8), ("sv_enable_list", c_uint8 * 9)]

    def __init__(self, tick, sv_number, sv_enable_list):
        super().__init__()
        self.id = ID_MSG_LL_IN_SV_CTRL
        self.data = self.msg_structure(tick, sv_number, tuple(sv_enable_list))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_RESET_STATE_VEC(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, tick):
        super().__init__()
        self.id = ID_MSG_LL_IN_RESET_STATE_VEC
        self.data = self.msg_structure(tick)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_START_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("sequence_length", c_uint32),
                    ("input1", c_float * SEQUENCE_BUFFER_LENGTH), ("input2", c_float * SEQUENCE_BUFFER_LENGTH)]

    def __init__(self, tick, ctrl_state, sequence_length, input1, input2):
        super().__init__()
        self.id = ID_MSG_LL_IN_START_SEQUENCE
        if len(input1) < SEQUENCE_BUFFER_LENGTH or len(input2) < SEQUENCE_BUFFER_LENGTH:
            input1 += [0] * (SEQUENCE_BUFFER_LENGTH - len(input1))
            input2 += [0] * (SEQUENCE_BUFFER_LENGTH - len(input2))
        self.data = self.msg_structure(tick, ctrl_state, sequence_length, tuple(input1), tuple(input2))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_RELOAD(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("input1", c_float * RELOAD_NUMBER),
                    ("input2", c_float * RELOAD_NUMBER)]

    def __init__(self, tick, ctrl_state, input1, input2):
        super().__init__()
        self.id = ID_MSG_LL_IN_RELOAD
        if len(input1) < RELOAD_NUMBER or len(input2) < RELOAD_NUMBER:
            input1 += [0] * (RELOAD_NUMBER - len(input1))
            input2 += [0] * (RELOAD_NUMBER - len(input2))
        self.data = self.msg_structure(tick, ctrl_state, tuple(input1), tuple(input2))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_IN_END_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8)]

    def __init__(self, tick, ctrl_state):
        super().__init__()
        self.id = ID_MSG_LL_IN_END_SEQUENCE
        self.data = self.msg_structure(tick, ctrl_state)
        self.raw_data = bytes(self.data)


# ======================================================================================================================
# HOST IN

class MSG_HOST_IN_DEBUG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("string", c_char * 40)]

    def __init__(self, tick, debug_string):
        super().__init__()
        self.id = ID_MSG_HOST_IN_DEBUG
        by = bytes(debug_string, "utf-8")
        by += b"0" * (40 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


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
                    ("psidot_cmd", c_float)]

    def __init__(self, tick, robot: Robot):
        super().__init__()
        self.id = ID_MSG_HOST_IN_CONT
        self.data = self.msg_structure(tick, c_uint8(robot.ll_fsm_state), robot.state.x, robot.state.y, robot.state.sdot,
                                       robot.state.theta, robot.state.thetadot, robot.state.psi, robot.state.psidot,
                                       (c_float * 3)(*robot.sensors.imu.gyr), (c_float * 3)(*robot.sensors.imu.acc),
                                       robot.drive.torque_left, robot.sensors.encoder_left.omega, robot.drive.torque_right,
                                       robot.sensors.encoder_right.omega,
                                       c_uint8(robot.controller.state), (c_float * 2)(*robot.controller.u),
                                       robot.controller.xdot_cmd, robot.controller.psidot_cmd)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_DYNAMICS(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("x", c_float), ("y", c_float), ("v", c_float), ("theta", c_float),
                    ("theta_dot", c_float), ("psi", c_float), ("psi_dot", c_float)]

    def __init__(self, tick, x, y, v, theta, theta_dot, psi, psi_dot):
        super().__init__()
        self.id = ID_MSG_HOST_IN_DYNAMICS
        self.data = self.msg_structure(tick, x, y, v, theta, theta_dot, psi, psi_dot)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_FSM(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8)]

    def __init__(self, tick, fsm_state):
        super().__init__()
        self.id = ID_MSG_HOST_IN_FSM
        self.data = self.msg_structure(tick, c_uint8(fsm_state))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------


class MSG_HOST_IN_IMU(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("gyr", c_float * 3), ("acc", c_float * 3)]

    def __init__(self, tick, gyr, acc):
        super().__init__()
        self.id = ID_MSG_HOST_IN_IMU
        self.data = self.msg_structure(tick, (c_float * 3)(*gyr), (c_float * 3)(*acc))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_DRIVE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("state_left", c_uint8), ("torque_left", c_float), ("omega_left", c_float),
                    ("angle_left", c_float), ("state_right", c_uint8), ("torque_right", c_float),
                    ("omega_right", c_float),
                    ("angle_right", c_float)]

    def __init__(self, tick, state_left, torque_left, omega_left, angle_left, state_right, torque_right, omega_right,
                 angle_right):
        super().__init__()
        self.id = ID_MSG_HOST_IN_DRIVE
        self.data = self.msg_structure(tick, state_left, torque_left, omega_left, angle_left, state_right, torque_right,
                                       omega_right, angle_right)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_CTRL_STATE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("external_torque", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, tick, ctrl_state, external_torque, xdot_cmd, psidot_cmd):
        super().__init__()
        self.id = ID_MSG_HOST_IN_CTRL_STATE
        self.data = self.msg_structure(tick, ctrl_state, external_torque, xdot_cmd, psidot_cmd)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_CTRL_INPUT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("external_torque", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, tick, ctrl_state, external_torque, xdot_cmd, psidot_cmd):
        super().__init__()
        self.id = ID_MSG_HOST_IN_CTRL_INPUT
        self.data = self.msg_structure(tick, ctrl_state, external_torque, xdot_cmd, psidot_cmd)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_CTRL_SF_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("K", c_float * 12)]

    def __init__(self, tick, K: np.ndarray((2, 6))):
        super().__init__()
        self.id = ID_MSG_HOST_IN_CTRL_SF_CONFIG
        self.data = self.msg_structure(tick, tuple(K.flatten()))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_CTRL_SC_X_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_HOST_IN_CTRL_SC_X_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_CTRL_SC_PSI_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min):
        super().__init__()
        self.id = ID_MSG_HOST_IN_CTRL_SC_PSI_CONFIG
        self.data = self.msg_structure(tick, P, I, D, enable_limit, v_max, v_min, enable_rate_limit, vdot_max, vdot_min)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_ERROR(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("error_id", c_uint8), ("data", c_char * 80)]

    def __init__(self, tick, error_id, error_string):
        super().__init__()
        self.id = ID_MSG_HOST_IN_ERROR
        by = bytes(error_string, "utf-8")
        by += b"0" * (80 - len(by))
        self.data = self.msg_structure(tick, error_id, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_LOGGING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("running", c_uint8), ("file", c_char * 40)]

    def __init__(self, tick, running, file):
        super().__init__()
        self.id = ID_MSG_HOST_IN_LOGGING
        by = bytes(file, "utf-8")
        by += b"0" * (40 - len(by))
        self.data = self.msg_structure(tick, running, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_INFO(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("data", c_char * 60)]

    def __init__(self, tick, info_string):
        super().__init__()
        self.id = ID_MSG_HOST_IN_INFO
        by = bytes(info_string, "utf-8")
        by += b"0" * (60 - len(by))
        self.data = self.msg_structure(tick, by)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_SV_CTRL(Message):#MSG_LL_IN_RESET_STATE_VEC
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("sv_number", c_uint8), ("sv_enable_list", c_uint8 * 9)]

    def __init__(self, tick, sv_number, sv_enable_list):
        super().__init__()
        self.id = ID_MSG_HOST_IN_SV_CTRL
        self.data = self.msg_structure(tick, sv_number, tuple(sv_enable_list))
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_RESET_STATE_VEC(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, tick):
        super().__init__()
        self.id = ID_MSG_HOST_IN_RESET_STATE_VEC
        self.data = self.msg_structure(tick)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_DELAY(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("delay", c_float)]

    def __init__(self, tick, delay):
        super().__init__()
        self.id = ID_MSG_HOST_IN_DELAY
        self.data = self.msg_structure(tick, delay)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_LOAD_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ('ctrl_state', c_uint8), ('input_length', c_uint16)]

    def __init__(self, tick, name, ctrl_state, input_length):
        super().__init__()
        self.id = ID_MSG_HOST_IN_LOAD_EXPERIMENT
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by, ctrl_state, input_length)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_START_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32)]

    def __init__(self, tick, name, ctrl_state, sequence_length):
        super().__init__()
        self.id = ID_MSG_HOST_IN_START_EXPERIMENT
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by, ctrl_state, sequence_length)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_END_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32),
                    ("sequence_counter", c_uint32), ("success", c_uint8)]

    def __init__(self, tick, name, ctrl_state, sequence_length, sequence_counter, success):
        super().__init__()
        self.id = ID_MSG_HOST_IN_END_EXPERIMENT
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by, ctrl_state, sequence_length, sequence_counter, success)
        self.raw_data = bytes(self.data)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_LOAD_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ('ctrl_state', c_uint8), ('input_length', c_uint16)]

    def __init__(self, tick, name, ctrl_state, input_length):
        super().__init__()
        self.id = ID_MSG_HOST_IN_LOAD_SEQUENCE
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by, ctrl_state, input_length)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_START_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32)]

    def __init__(self, tick, name, ctrl_state, sequence_length):
        super().__init__()
        self.id = ID_MSG_HOST_IN_START_SEQUENCE
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by, ctrl_state, sequence_length)
        self.raw_data = bytes(self.data)

# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_IN_END_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ("ctrl_state", c_uint8), ("sequence_length", c_uint32),
                    ("sequence_counter", c_uint32)]

    def __init__(self, tick, name, ctrl_state, sequence_length, sequence_counter):
        super().__init__()
        self.id = ID_MSG_HOST_IN_END_SEQUENCE
        by = bytes(name, "utf-8")
        by += b"0" * (30 - len(by))
        self.data = self.msg_structure(tick, by, ctrl_state, sequence_length, sequence_counter)
        self.raw_data = bytes(self.data)


# ======================================================================================================================
# HOST OUT

class MSG_HOST_OUT_DEBUG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("string", c_char * 40)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        string = 'Tick: {} String: "{}"'.format(self.data.tick, self.data.string.decode().rstrip("0"))
        print(string)
        msg = MSG_HOST_IN_DEBUG(global_values['tick'], self.data.string.decode().rstrip("0"))
        send_msg_to_host(msg)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_MOCAP(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("x", c_float), ("y", c_float), ("theta", c_float), ("psi", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        mocap.x = self.data.x
        mocap.y = self.data.y
        mocap.theta = self.data.theta
        mocap.psi = self.data.psi


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_FSM(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        global_values["flag_fsm_state_change"] = FSM_STATE(self.data.fsm_state)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_CTRL_STATE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        global_values["flag_ctrl_state_change"] = CTRL_STATE(self.data.ctrl_state)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_CTRL_INPUT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("external_torque", c_float * 2), ("xdot_cmd", c_float), ("psidot_cmd", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.external_torque = self.data.external_torque
        robot.controller.xdot_cmd = self.data.xdot_cmd
        robot.controller.psidot_cmd = self.data.psidot_cmd

        msg = MSG_LL_IN_CTRL_INPUT(global_values["tick"], self.data.external_torque, self.data.xdot_cmd, self.data.psidot_cmd)
        if not send_msg_to_ll(msg):
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_CTRL_SF_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("K", c_float * 12)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.state_feedback.K = np.reshape(self.data.K, (2, 6))

        msg = MSG_LL_IN_CTRL_SF_CONFIG(global_values["tick"], robot.controller.state_feedback.K)
        if not send_msg_to_ll(msg):
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_CTRL_SC_X_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.xdot_ctrl.P = self.data.P
        robot.controller.xdot_ctrl.I = self.data.I
        robot.controller.xdot_ctrl.D = self.data.D
        robot.controller.xdot_ctrl.enable_limit = self.data.enable_limit
        robot.controller.xdot_ctrl.max = self.data.v_max
        robot.controller.xdot_ctrl.min = self.data.v_min
        robot.controller.xdot_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot.controller.xdot_ctrl.dmax = self.data.vdot_max
        robot.controller.xdot_ctrl.dmin = self.data.vdot_min

        msg = MSG_LL_IN_CTRL_SC_X_CONFIG(global_values["tick"], self.data.P, self.data.I, self.data.D,
                                         self.data.enable_limit,
                                         self.data.v_max, self.data.v_min, self.data.enable_rate_limit,
                                         self.data.vdot_max,
                                         self.data.vdot_min)
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_CTRL_SC_PSI_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.psidot_ctrl.P = self.data.P
        robot.controller.psidot_ctrl.I = self.data.I
        robot.controller.psidot_ctrl.D = self.data.D
        robot.controller.psidot_ctrl.enable_limit = self.data.enable_limit
        robot.controller.psidot_ctrl.max = self.data.v_max
        robot.controller.psidot_ctrl.min = self.data.v_min
        robot.controller.psidot_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot.controller.psidot_ctrl.dmax = self.data.vdot_max
        robot.controller.psidot_ctrl.dmin = self.data.vdot_min

        msg = MSG_LL_IN_CTRL_SC_PSI_CONFIG(global_values["tick"], self.data.P, self.data.I, self.data.D,
                                           self.data.enable_limit,
                                           self.data.v_max, self.data.v_min, self.data.enable_rate_limit,
                                           self.data.vdot_max,
                                           self.data.vdot_min)
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_SELFTEST(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_MSG_NOT_IMPLEMENTED, "Selftest not implemented!")
        send_msg_to_host(msg)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_CALIBRATION(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_HOST_IN_INFO(global_values["tick"], "Calibration requested...")
        send_msg_to_host(msg)
        global_values["flag_fsm_state_change"] = FSM_STATE.CALIBRATING


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_LOGGING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("enable", c_uint8), ("file", c_char * 40)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        if self.data.enable:
            if logger.active:
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LOGGING_ACTIVATED,
                                        "Logging activated! ({})".format(logger.log_filename))
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            else:
                err = logger.start_logging(self.data.file.decode().rstrip("0"))
                if err:
                    msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_START_LOGGING, err)
                    if not send_msg_to_host(msg):
                        print("Failed to send message to HOST!")
                else:
                    msg = MSG_HOST_IN_LOGGING(global_values["tick"], logger.active, logger.log_filename)
                    if not send_msg_to_host(msg):
                        print("Failed to send message to HOST!")
        else:
            if logger.active:
                logged_rows, filename = logger.stop_logging()

                if logged_rows:
                    msg = MSG_HOST_IN_INFO(global_values['tick'], 'ML logged buffered data! ({} rows)'.format(logged_rows))
                    if not send_msg_to_host(msg):
                        print("Failed to send message to HOST!")

                msg = MSG_HOST_IN_LOGGING(global_values["tick"], logger.active, filename)
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            else:
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LOGGING_DEACTIVATED,
                                        "Logging deactivated!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_HEADING(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("heading", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.state.psi = self.data.heading
        # msg = MSG_LL_IN_HEADING(global_values["tick"], self.data.heading)
        # send_msg_to_ll(msg)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_MOVE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("xdot", c_float), ("psidot", c_float), ("time", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_MSG_NOT_IMPLEMENTED, "Move System not implemented!")
        send_msg_to_host(msg)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_SV_CTRL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("sv_number", c_uint8), ("sv_enable_list", c_uint8 * 9)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.supervisor.sv_enable_list = list(self.data.sv_enable_list)

        msg = MSG_LL_IN_SV_CTRL(global_values['tick'], self.data.sv_number, self.data.sv_enable_list)
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_RESET_STATE_VEC(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_LL_IN_RESET_STATE_VEC(global_values['tick'])
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")

# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_DELAY(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("delay", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # delay ML message handling for the requested amount of time
        t1 = time.monotonic()
        time.sleep(self.data.delay)
        t2 = time.monotonic()
        delta = t2 - t1

        # confirm execution of the delay
        msg = MSG_HOST_IN_DELAY(global_values['tick'], delta)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


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

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg_data = experiment_handler.load_experiment_from_data(self.data)

        # acknowledgement
        msg = MSG_HOST_IN_LOAD_EXPERIMENT(msg_data[0],
                                          msg_data[1],
                                          msg_data[2],
                                          msg_data[3])
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_START_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        experiment_name = self.data.name.decode().rstrip("0")

        # check sequence handler status, is active during experiment or sequence
        # no need for checking experiment handler status,
        # because its directly connected to the sequence handler
        # the sequence handler is always on during an experiment
        if not sequence_handler.idle():
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_START_EXPERIMENT, "Sequence handler active!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # check if experiment exists
        if not experiment_handler.element_loaded(experiment_name):
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_START_EXPERIMENT, "Experiment not loaded!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # if handler idle and experiment exists, start execution
        msg_data = experiment_handler.start_experiment(experiment_name)
        msg = MSG_LL_IN_START_SEQUENCE(msg_data[0],
                                       msg_data[1],
                                       msg_data[2],
                                       msg_data[3],
                                       msg_data[4])
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_END_EXPERIMENT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        experiment_name = self.data.name.decode().rstrip("0")

        # check sequence_handler status (sequence handler is always involved, during an experiment too)
        if sequence_handler.idle():
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_END_EXPERIMENT, "Sequence handler idle!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # check if sequence currently marked as active element
        if not experiment_handler.element_activated(experiment_name):
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_END_EXPERIMENT, "Experiment not activated!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # if sequence handler is executing the named sequence from the experiment, end this sequence
        msg_data = experiment_handler.end_experiment(experiment_name)
        msg = MSG_LL_IN_END_SEQUENCE(msg_data[0],
                                     msg_data[1])
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_LOAD_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30), ('ctrl_state', c_uint8),
                    ('input_length', c_uint16), ('input1', c_float * 2000), ('input2', c_float * 2000)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg_data = sequence_handler.load_sequence_from_data(self.data)

        # acknowledgement for HL
        msg = MSG_HOST_IN_LOAD_SEQUENCE(msg_data[0],
                                        msg_data[1],
                                        msg_data[2],
                                        msg_data[3])
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")

    
# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_START_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        sequence_name = self.data.name.decode().rstrip("0")

        # check sequence_handler status
        if not sequence_handler.idle():
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_START_SEQUENCE, "Sequence handler active!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # check if sequence exists
        if not sequence_handler.element_loaded(sequence_name):
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_START_SEQUENCE, "Sequence not loaded!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # if handler idle and sequence exists, start execution and send message to LL
        msg_data = sequence_handler.start_sequence(sequence_name)
        msg = MSG_LL_IN_START_SEQUENCE(msg_data[0],
                                       msg_data[1],
                                       msg_data[2],
                                       msg_data[3],
                                       msg_data[4])
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_HOST_OUT_END_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ('name', c_char * 30)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        sequence_name = self.data.name.decode().rstrip("0")

        # check sequence_handler status
        if sequence_handler.idle():
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_END_SEQUENCE, "Sequence handler idle!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # check if sequence currently marked as active element
        if not sequence_handler.element_activated(sequence_name):
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_CANNOT_END_SEQUENCE, "Sequence not activated!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
            return

        # if sequence handler is executing the named sequence, end sequence
        msg_data = sequence_handler.end_sequence()
        msg = MSG_LL_IN_END_SEQUENCE(msg_data[0],
                                     msg_data[1])
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ======================================================================================================================
# LL OUT

class MSG_LL_OUT_FSM(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # on error
        # if self.data.fsm_state == FSM_STATE.ERROR:
        #     # stop logging
        #     if logger.active:
        #         logged_rows, filename = logger.stop_logging()
        #
        #         if logged_rows:
        #             msg = MSG_HOST_IN_INFO(global_values['tick'],
        #                                    'ML logged buffered data! ({} rows)'.format(logged_rows))
        #             if not send_msg_to_host(msg):
        #                 print("Failed to send message to HOST!")
        #
        #         msg = MSG_HOST_IN_LOGGING(global_values["tick"], logger.active, filename)
        #         if not send_msg_to_host(msg):
        #             print("Failed to send message to HOST!")

        robot.ll_fsm_state = FSM_STATE(self.data.fsm_state)
        print("Robot is now in state {:d}".format(robot.ll_fsm_state))

        msg = MSG_HOST_IN_FSM(global_values["tick"], self.data.fsm_state)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------
class MSG_LL_OUT_CONTINIUOUS(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("fsm_state", c_uint8), ("s", c_float), ("v", c_float), ("theta", c_float),
                    ("theta_dot", c_float), ("psi", c_float), ("psi_dot", c_float), ("gyr", c_float * 3),
                    ("acc", c_float * 3),
                    ("torque_left", c_float), ("omega_left", c_float), ("torque_right", c_float),
                    ("omega_right", c_float), ("ctrl_state", c_uint8), ("u", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # (1) ROBOT DATA OBJECT
        robot.ll_fsm_state = FSM_STATE(self.data.fsm_state)
        robot.state.s = self.data.s
        robot.state.sdot = self.data.v
        robot.state.theta = self.data.theta
        robot.state.thetadot = self.data.theta_dot
        robot.state.psi = self.data.psi
        robot.state.psidot = self.data.psi_dot
        robot.sensors.imu.gyr = list(self.data.gyr)
        robot.sensors.imu.acc = list(self.data.acc)
        robot.sensors.encoder_left.omega = self.data.omega_left
        robot.sensors.encoder_right.omega = self.data.omega_right
        robot.drive.torque_left = self.data.torque_left
        robot.drive.torque_right = self.data.torque_right
        robot.controller.state = CTRL_STATE(self.data.ctrl_state)
        robot.controller.u = list(self.data.u)
        robot.controller.xdot_cmd = self.data.xdot_cmd
        robot.controller.psidot_cmd = self.data.psidot_cmd
        # print("Tick: {:d}, ctrl_state={}".format(self.data.tick,
        #                                          robot.controller.state))

        # (2) LOGGER
        if logger.active:
            data = [self.data.tick, self.data.fsm_state, self.data.s, self.data.v, self.data.theta, self.data.theta_dot,
                    self.data.psi, self.data.psi_dot, self.data.gyr[0], self.data.gyr[1], self.data.gyr[2],
                    self.data.acc[0], self.data.acc[1], self.data.acc[2], self.data.torque_left, self.data.omega_left,
                    self.data.torque_right, self.data.omega_right, self.data.ctrl_state, self.data.u[0], self.data.u[1],
                    self.data.xdot_cmd, self.data.psidot_cmd]
            logged_rows = logger.buffer_data(data)
            if logged_rows:
                msg = MSG_HOST_IN_INFO(global_values['tick'], 'ML logged buffered data! ({} rows)'.format(logged_rows))
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")

        # (3) EXPERIMENT HANDLER
        if not experiment_handler.idle():
            error_id, error_string = experiment_handler.check_robot()

            if error_id:
                msg = MSG_HOST_IN_ERROR(global_values["tick"], error_id, error_string)
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")

                # set error flag in experiment handler and prepare message for LL
                msg_data = experiment_handler.end_experiment(error_condition=True)
                msg = MSG_LL_IN_END_SEQUENCE(msg_data[0],
                                             msg_data[1])
                if not send_msg_to_ll(msg):
                    print("Failed to send message to LL!")
                    msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED,
                                            "Failed to send message to LL!")
                    if not send_msg_to_host(msg):
                        print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_DYNAMICS(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("s", c_float), ("v", c_float), ("theta", c_float),
                    ("theta_dot", c_float), ("psi", c_float), ("psi_dot", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.state.s = self.data.s
        robot.state.sdot = self.data.v
        robot.state.theta = self.data.theta
        robot.state.thetadot = self.data.theta_dot
        robot.state.psidot = self.data.psi_dot


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_IMU(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("gyr", c_float * 3), ("acc", c_float * 3)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.sensors.imu.gyr = list(self.data.gyr)
        robot.sensors.imu.acc = list(self.data.acc)


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_DRIVE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("state_left", c_uint8), ("torque_left", c_float), ("omega_left", c_float),
                    ("angle_left", c_float), ("state_right", c_uint8), ("torque_right", c_float),
                    ("omega_right", c_float),
                    ("angle_right", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.sensors.encoder_left.omega = self.data.omega_left
        robot.sensors.encoder_left.angle = self.data.angle_left
        robot.sensors.encoder_right.omega = self.data.omega_right
        robot.sensors.encoder_right.angle = self.data.angle_right
        robot.drive.torque_left = self.data.torque_left
        robot.drive.torque_right = self.data.torque_right


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_CTRL_STATE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("external_torque", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.state = CTRL_STATE(self.data.ctrl_state)
        robot.controller.external_torque = self.data.external_torque
        robot.controller.xdot_cmd = self.data.xdot_cmd
        robot.controller.psidot_cmd = self.data.psidot_cmd

        msg = MSG_HOST_IN_CTRL_STATE(global_values["tick"], self.data.ctrl_state, tuple(self.data.external_torque), self.data.xdot_cmd,
                               self.data.psidot_cmd)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_CTRL_INPUT(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("external_torque", c_float * 2), ("xdot_cmd", c_float),
                    ("psidot_cmd", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.state = CTRL_STATE(self.data.ctrl_state)
        robot.controller.external_torque = self.data.external_torque
        robot.controller.xdot_cmd = self.data.xdot_cmd
        robot.controller.psidot_cmd = self.data.psidot_cmd

        msg = MSG_HOST_IN_CTRL_INPUT(global_values["tick"], self.data.ctrl_state, tuple(self.data.external_torque), self.data.xdot_cmd,
                               self.data.psidot_cmd)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_CTRL_SF_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("K", c_float * 12)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.state_feedback.K = np.reshape(self.data.K, (2, 6))

        msg = MSG_HOST_IN_CTRL_SF_CONFIG(global_values["tick"], np.reshape(self.data.K, (2, 6)))
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_CTRL_SC_X_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.xdot_ctrl.P = self.data.P
        robot.controller.xdot_ctrl.I = self.data.I
        robot.controller.xdot_ctrl.D = self.data.D
        robot.controller.xdot_ctrl.enable_limit = self.data.enable_limit
        robot.controller.xdot_ctrl.max = self.data.v_max
        robot.controller.xdot_ctrl.min = self.data.v_min
        robot.controller.xdot_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot.controller.xdot_ctrl.dmax = self.data.vdot_max
        robot.controller.xdot_ctrl.dmin = self.data.vdot_min

        msg = MSG_HOST_IN_CTRL_SC_X_CONFIG(global_values["tick"], self.data.P, self.data.I, self.data.D,
                                           self.data.enable_limit, self.data.v_max, self.data.v_min,
                                           self.data.enable_rate_limit, self.data.vdot_max, self.data.vdot_min)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_CTRL_SC_PSI_CONFIG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("P", c_float), ("I", c_float), ("D", c_float), ("enable_limit", c_uint8),
                    ("v_max", c_float), ("v_min", c_float), ("enable_rate_limit", c_uint8), ("vdot_max", c_float),
                    ("vdot_min", c_float)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.controller.psidot_ctrl.P = self.data.P
        robot.controller.psidot_ctrl.I = self.data.I
        robot.controller.psidot_ctrl.D = self.data.D
        robot.controller.psidot_ctrl.enable_limit = self.data.enable_limit
        robot.controller.psidot_ctrl.max = self.data.v_max
        robot.controller.psidot_ctrl.min = self.data.v_min
        robot.controller.psidot_ctrl.enable_rate_limit = self.data.enable_rate_limit
        robot.controller.psidot_ctrl.dmax = self.data.vdot_max
        robot.controller.psidot_ctrl.dmin = self.data.vdot_min

        msg = MSG_HOST_IN_CTRL_SC_PSI_CONFIG(global_values["tick"], self.data.P, self.data.I, self.data.D,
                                           self.data.enable_limit, self.data.v_max, self.data.v_min,
                                           self.data.enable_rate_limit, self.data.vdot_max, self.data.vdot_min)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_ERROR(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("error_id", c_uint8), ("data", c_char * 80)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # pass error message to HL
        msg = MSG_HOST_IN_ERROR(global_values["tick"], self.data.error_id, self.data.data.decode())
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_DEBUG(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("string", c_char * 40)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_HOST_IN_DEBUG(global_values["tick"], self.data.string.decode().rstrip("0"))
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_INPUT_BUFFER_VEL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("buffer_length", c_uint16)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        pass


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_HANDSHAKE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_HOST_IN_INFO(self.data.tick, "LL reaches out hand, HL responds...")
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")

        msg = MSG_LL_IN_HANDSHAKE(self.data.tick)
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_SV_CTRL(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("sv_number", c_uint8), ("sv_enable_list", c_uint8 * 9)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        robot.supervisor.sv_enable_list = list(self.data.sv_enable_list)
        robot.supervisor.sv_number = self.data.sv_number

        msg = MSG_HOST_IN_SV_CTRL(global_values['tick'], self.data.sv_number, self.data.sv_enable_list)
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_RESET_STATE_VEC(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        msg = MSG_HOST_IN_RESET_STATE_VEC(global_values['tick'])
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_START_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("sequence_length", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # put HL message handler into blocking state
        msg_hndlr_host.start_blocking()
        msg = MSG_HOST_IN_INFO(global_values['tick'], "HL message handler now in blocking state!")
        if not send_msg_to_host(msg):
            print("Failed to send message to HL!")

        # process acknowledgement "started sequence" from LL correctly
        if experiment_handler.cached_element:
            # if an experiment has been cached, the LL sequence handler
            # received a sequence from an experiment
            experiment = experiment_handler.activate_cached_element()
            # pass correct acknowledgement to HL
            msg = MSG_HOST_IN_START_EXPERIMENT(global_values['tick'], experiment.name, self.data.ctrl_state,
                                               self.data.sequence_length)
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
        else:
            sequence = sequence_handler.activate_cached_element()
            # pass correct acknowledgement to HL
            msg = MSG_HOST_IN_START_SEQUENCE(global_values['tick'], sequence.name, self.data.ctrl_state,
                                             self.data.sequence_length)
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")


# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_RELOAD(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("received_samples", c_uint32), ("reload_number", c_uint8)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # trigger reload
        msg_data = sequence_handler.reload(self.data.received_samples, self.data.reload_number)
        msg = MSG_LL_IN_RELOAD(msg_data[0],
                               msg_data[1],
                               msg_data[2],
                               msg_data[3])
        if not send_msg_to_ll(msg):
            print("Failed to send message to LL!")
            msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
            if not send_msg_to_host(msg):
                print("Failed to send message to HOST!")

        # inform HL about reload request
        msg = MSG_HOST_IN_INFO(global_values["tick"], "LL requested reload from ML!")
        if not send_msg_to_host(msg):
            print("Failed to send message to HOST!")

# ----------------------------------------------------------------------------------------------------------------------

class MSG_LL_OUT_END_SEQUENCE(Message):
    class msg_structure(Structure):
        _pack_ = 1
        _fields_ = [("tick", c_uint32), ("ctrl_state", c_uint8), ("sequence_length", c_uint32),
                    ("sequence_counter", c_uint32)]

    def __init__(self, msg: Message):
        super().__init__()
        self.data = self.msg_structure.from_buffer_copy(msg.raw_data)

    def handler(self):
        # process acknowledgement "ended sequence" from LL correctly
        if not experiment_handler.idle():
            # the sequence that was ended right now is a sequence from an experiment,
            # because the experiment handler is activated
            # please deactivate the experiment (also sequence) and inform HL about successful ending
            experiment, success = experiment_handler.deactivate_element()

            msg = MSG_HOST_IN_END_EXPERIMENT(global_values['tick'], experiment.name, self.data.ctrl_state,
                                             self.data.sequence_length, self.data.sequence_counter, success)
            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")
        else:
            # deactivate sequence
            sequence = sequence_handler.deactivate_element()

            # inform HL about end of sequence
            msg = MSG_HOST_IN_END_SEQUENCE(global_values['tick'], sequence.name, self.data.ctrl_state,
                                           self.data.sequence_length, self.data.sequence_counter)

            if not send_msg_to_host(msg):
                print("Failed to send message to HL!")

        # put HL message handler out of blocking state
        msg_hndlr_host.stop_blocking()
        msg = MSG_HOST_IN_INFO(global_values['tick'], "HL message handler is now available!")
        if not send_msg_to_host(msg):
            print("Failed to send message to HL!")


# ----------------------------------------------------------------------------------------------------------------------

msg_dictionary_ll = {ID_MSG_LL_OUT_DYNAMIC_STATE: MSG_LL_OUT_DYNAMICS,
                     ID_MSG_LL_OUT_IMU: MSG_LL_OUT_IMU,
                     ID_MSG_LL_OUT_DRV: MSG_LL_OUT_DRIVE,
                     ID_MSG_LL_OUT_CTRL_STATE: MSG_LL_OUT_CTRL_STATE,
                     ID_MSG_LL_OUT_CTRL_INPUT: MSG_LL_OUT_CTRL_INPUT,
                     ID_MSG_LL_OUT_FSM: MSG_LL_OUT_FSM,
                     ID_MSG_LL_OUT_CTRL_SF_CONFIG: MSG_LL_OUT_CTRL_SF_CONFIG,
                     ID_MSG_LL_OUT_CTRL_SC_X_CONFIG: MSG_LL_OUT_CTRL_SC_X_CONFIG,
                     ID_MSG_LL_OUT_CTRL_SC_PSI_CONFIG: MSG_LL_OUT_CTRL_SC_PSI_CONFIG,
                     ID_MSG_LL_OUT_ERROR: MSG_LL_OUT_ERROR,
                     ID_MSG_LL_OUT_DEBUG: MSG_LL_OUT_DEBUG,
                     ID_MSG_LL_OUT_INPUT_BUFFER_VEL: MSG_LL_OUT_INPUT_BUFFER_VEL,
                     ID_MSG_LL_OUT_CONTINIUOUS: MSG_LL_OUT_CONTINIUOUS,
                     ID_MSG_LL_OUT_HANDSHAKE: MSG_LL_OUT_HANDSHAKE,
                     ID_MSG_LL_OUT_SV_CTRL: MSG_LL_OUT_SV_CTRL,
                     ID_MSG_LL_OUT_RESET_STATE_VEC: MSG_LL_OUT_RESET_STATE_VEC,
                     ID_MSG_LL_OUT_START_SEQUENCE: MSG_LL_OUT_START_SEQUENCE,
                     ID_MSG_LL_OUT_RELOAD: MSG_LL_OUT_RELOAD,
                     ID_MSG_LL_OUT_END_SEQUENCE: MSG_LL_OUT_END_SEQUENCE}

msg_dictionary_host = {ID_MSG_HOST_OUT_DEBUG: MSG_HOST_OUT_DEBUG,
                       ID_MSG_HOST_OUT_MOCAP: MSG_HOST_OUT_MOCAP,
                       ID_MSG_HOST_OUT_FSM: MSG_HOST_OUT_FSM,
                       ID_MSG_HOST_OUT_CTRL_STATE: MSG_HOST_OUT_CTRL_STATE,
                       ID_MSG_HOST_OUT_CTRL_INPUT: MSG_HOST_OUT_CTRL_INPUT,
                       ID_MSG_HOST_OUT_CTRL_SF_CONFIG: MSG_HOST_OUT_CTRL_SF_CONFIG,
                       ID_MSG_HOST_OUT_CTRL_SC_X_CONFIG: MSG_HOST_OUT_CTRL_SC_X_CONFIG,
                       ID_MSG_HOST_OUT_CTRL_SC_PSI_CONFIG: MSG_HOST_OUT_CTRL_SC_PSI_CONFIG,
                       ID_MSG_HOST_OUT_SELFTEST: MSG_HOST_OUT_SELFTEST,
                       ID_MSG_HOST_OUT_CALIBRATION: MSG_HOST_OUT_CALIBRATION,
                       ID_MSG_HOST_OUT_LOGGING: MSG_HOST_OUT_LOGGING,
                       ID_MSG_HOST_OUT_HEADING: MSG_HOST_OUT_HEADING,
                       ID_MSG_HOST_OUT_MOVE: MSG_HOST_OUT_MOVE,
                       ID_MSG_HOST_OUT_SV_CTRL: MSG_HOST_OUT_SV_CTRL,
                       ID_MSG_HOST_OUT_RESET_STATE_VEC: MSG_HOST_OUT_RESET_STATE_VEC,
                       ID_MSG_HOST_OUT_DELAY: MSG_HOST_OUT_DELAY,
                       ID_MSG_HOST_OUT_LOAD_EXPERIMENT: MSG_HOST_OUT_LOAD_EXPERIMENT,
                       ID_MSG_HOST_OUT_START_EXPERIMENT: MSG_HOST_OUT_START_EXPERIMENT,
                       ID_MSG_HOST_OUT_END_EXPERIMENT: MSG_HOST_OUT_END_EXPERIMENT,
                       ID_MSG_HOST_OUT_LOAD_SEQUENCE: MSG_HOST_OUT_LOAD_SEQUENCE,
                       ID_MSG_HOST_OUT_START_SEQUENCE: MSG_HOST_OUT_START_SEQUENCE,
                       ID_MSG_HOST_OUT_END_SEQUENCE: MSG_HOST_OUT_END_SEQUENCE}

hl_allowed_message_ids = [ID_MSG_HOST_OUT_END_SEQUENCE,
                          ID_MSG_HOST_OUT_END_EXPERIMENT,
                          ID_MSG_HOST_OUT_DELAY,
                          ID_MSG_HOST_OUT_LOGGING]

ll_allowed_message_ids = []
