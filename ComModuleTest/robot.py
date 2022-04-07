from enum import IntEnum
import numpy as np


# Low-Level States
class FSM_STATE(IntEnum):
    NOT_CONNECTED = -1
    INITIALIZING = 0
    IDLE = 1
    ACTIVE = 2
    ERROR = 3
    CALIBRATING = 4
    EXPERIMENT = 5


class CTRL_STATE(IntEnum):
    OFF = 0
    DIRECT = 1
    STATE_FEEDBACK = 2
    VELOCITY = 3


class Imu:
    gyr: list
    acc: list

    def __init__(self):
        self.gyr = [0, 0, 0]
        self.acc = [0, 0, 0]
        pass


class Encoder:
    omega: float
    angle: float

    def __init__(self):
        self.omega = 0
        self.angle = 0


class MocapData:
    x: float
    y: float
    theta: float
    psi: float
    enabled: bool

    def __init__(self):
        self.x = 0
        self.y = 0
        self.theta = 0
        self.psi = 0
        self.enabled = False


class RobotSensors:
    imu: Imu
    encoder_left: Encoder
    encoder_right: Encoder

    def __init__(self):
        self.imu = Imu()
        self.encoder_right = Encoder()
        self.encoder_left = Encoder()
        pass


class PID_Controller:
    P: float = 0
    I: float = 0
    D: float = 0
    enable_limit: bool = False
    max: float = 0
    min: float = 0
    enable_rate_limit: bool = False
    dmax: float = 0
    dmin: float = 0


class StateFeedbackController:
    K: np.ndarray((2, 6)) = np.zeros((2, 6))


class RobotController:
    state: CTRL_STATE = CTRL_STATE(0)
    xdot_cmd: float = 0
    psidot_cmd: float = 0
    external_torque: list = [0, 0]
    u: list = [0, 0]
    xdot_ctrl: PID_Controller = PID_Controller()
    psidot_ctrl: PID_Controller = PID_Controller()
    state_feedback: StateFeedbackController = StateFeedbackController()


class RobotDriveSystem:
    torque_left: float = 0
    torque_right: float = 0


class RobotState:
    x: float
    y: float
    s: float
    sdot: float
    theta: float
    thetadot: float
    psi: float
    psidot: float

    def __init__(self):
        self.x = 0
        self.y = 0
        self.s = 0
        self.sdot = 0
        self.theta = 0
        self.thetadot = 0
        self.psi = 0
        self.psidot = 0


class RobotExperiment:
    running: bool = 0
    file: str = ""


class DataLoggingState:
    running: bool = False
    file: str = ""

    def activate_logging(self, filename: str, enable: bool = True) -> None:
        self.running = enable
        self.file = filename

    def deactivate_logging(self, enable: bool = False, filename: str = '') -> None:
        self.running = enable
        self.file = filename


class Supervisor:
    sv_enable_list: list

    def __init__(self):
        self.sv_enable_list = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.sv_number = 9


class Robot:
    connected: bool
    ctrl_state: CTRL_STATE
    ll_fsm_state: FSM_STATE
    hl_fsm_state: FSM_STATE
    sensors: RobotSensors
    state: RobotState
    controller: RobotController
    drive: RobotDriveSystem
    experiment: RobotExperiment
    logging: DataLoggingState
    supervisor: Supervisor

    def __init__(self):
        self.connected = False
        self.ctrl_state = CTRL_STATE(0)
        self.ll_fsm_state = FSM_STATE(0)
        self.hl_fsm_state = FSM_STATE(0)
        self.sensors = RobotSensors()
        self.state = RobotState()
        self.controller = RobotController()
        self.drive = RobotDriveSystem()
        self.experiment = RobotExperiment()
        self.logging = DataLoggingState()
        self.supervisor = Supervisor()
