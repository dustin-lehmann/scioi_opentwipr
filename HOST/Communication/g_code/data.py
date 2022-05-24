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
    x_cmd: float = 0
    y_cmd: float = 0
    external_torque: list = [0, 0]
    u: list = [0, 0]
    distance_ctrl: PID_Controller = PID_Controller()
    angle_ctrl: PID_Controller = PID_Controller()
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
    running: int = 0
    file: str = ""


class DataLoggingState:
    running: int = 0
    file: str = ""


class Supervisor:
    sv_enable_list: list

    def __init__(self):
        self.sv_enable_list = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.sv_number = 9


class DataLogs:
    def __init__(self, robot, refresh_time_ms):
        self.robot = robot
        # time settings for logs and plots
        self.t = refresh_time_ms / 1000  # convert to seconds
        self.t_max = 5  # maximum number of seconds to be displayed on the x axis of the TWIPR plots
        self.n_max = int(self.t_max / self.t)  # >>> n_max == 500

        # logs to plot

        # x axis
        self.log_t = np.linspace(0, self.n_max - 1, self.n_max) * self.t  # constant

        # respective y axes
        # ---- 1. Plot: theta, psi
        self.log_theta = [0] * self.n_max
        self.log_psi = [0] * self.n_max
        # ---- 2. Plot: x_dot, theta_dot, psi_dot, set_x_dot, set_psi_dot
        self.log_sdot = [0] * self.n_max
        self.log_thetadot = [0] * self.n_max
        self.log_psidot = [0] * self.n_max
        self.log_xdot_cmd = [0] * self.n_max
        self.log_psidot_cmd = [0] * self.n_max
        # ---- 4. Plot: IMU
        self.log_imu_wx = [0] * self.n_max
        self.log_imu_wy = [0] * self.n_max
        self.log_imu_wz = [0] * self.n_max
        self.log_imu_ax = [0] * self.n_max
        self.log_imu_ay = [0] * self.n_max
        self.log_imu_az = [0] * self.n_max
        # ---- 5. Plot: Encoder
        self.log_left_omega = [0] * self.n_max
        self.log_right_omega = [0] * self.n_max
        # ---- 6. Plot: Torque + U
        self.log_left_torque = [0] * self.n_max
        self.log_right_torque = [0] * self.n_max
        self.log_left_u = [0] * self.n_max
        self.log_right_u = [0] * self.n_max
        # ---- 7. Plot: U + cmds

        # 3. Plot: X & Y coordinate + CMDs
        self.log_x = [0] * self.n_max
        self.log_y = [0] * self.n_max
        self.log_x_cmd = [0] * self.n_max
        self.log_y_cmd = [0] * self.n_max

    def log(self):
        self.update_array(self.log_theta, self.robot.state.theta)
        self.update_array(self.log_psi, self.robot.state.psi)
        self.update_array(self.log_sdot, self.robot.state.sdot)
        self.update_array(self.log_thetadot, self.robot.state.thetadot)
        self.update_array(self.log_psidot, self.robot.state.psidot)
        self.update_array(self.log_xdot_cmd, self.robot.controller.xdot_cmd)
        self.update_array(self.log_psidot_cmd, self.robot.controller.psidot_cmd)
        self.update_array(self.log_imu_wx, self.robot.sensors.imu.gyr[0])
        self.update_array(self.log_imu_wy, self.robot.sensors.imu.gyr[1])
        self.update_array(self.log_imu_wz, self.robot.sensors.imu.gyr[2])
        self.update_array(self.log_imu_ax, self.robot.sensors.imu.acc[0])
        self.update_array(self.log_imu_ay, self.robot.sensors.imu.acc[1])
        self.update_array(self.log_imu_az, self.robot.sensors.imu.acc[2])
        self.update_array(self.log_left_omega, self.robot.sensors.encoder_left.omega)
        self.update_array(self.log_right_omega, self.robot.sensors.encoder_right.omega)
        self.update_array(self.log_left_torque, self.robot.drive.torque_left)
        self.update_array(self.log_right_torque, self.robot.drive.torque_right)
        self.update_array(self.log_left_u, self.robot.controller.u[0])
        self.update_array(self.log_right_u, self.robot.controller.u[1])
        self.update_array(self.log_x, self.robot.state.x)
        self.update_array(self.log_y, self.robot.state.y)
        self.update_array(self.log_x_cmd, self.robot.state.x)
        self.update_array(self.log_y_cmd, self.robot.state.y)

    def update_array(self, arr, data_point):
        arr.pop(0)
        arr.append(data_point)


class Robot:
    connected: bool
    ctrl_state: CTRL_STATE
    fsm_state: FSM_STATE
    sensors: RobotSensors
    state: RobotState
    controller: RobotController
    drive: RobotDriveSystem
    experiment: RobotExperiment
    logging: DataLoggingState
    supervisor: Supervisor
    logs: DataLogs

    def __init__(self, refresh_time_ms):
        self.connected = False
        self.ctrl_state = CTRL_STATE(0)
        self.fsm_state = FSM_STATE(0)
        self.sensors = RobotSensors()
        self.state = RobotState()
        self.controller = RobotController()
        self.drive = RobotDriveSystem()
        self.experiment = RobotExperiment()
        self.logging = DataLoggingState()
        self.supervisor = Supervisor()

        # data logging for plots
        self.data_logs = DataLogs(self, refresh_time_ms)

        # ticks for TWIPR heartbeat
        self.tick = 0
        self.tick_last = 0