import numpy as np
import estimation.quaternions as qt
from estimation.particlefilter import ParticleFilter


def check_slip_one(head_rate_gyro, head_rate_odometry):
    if abs(head_rate_gyro - head_rate_odometry) >= 0.2:
        return True
    else:
        return False


class PositionEstimator:
    """
    A class to estimate position
    ...
    Attributes
    -----------
    ts : float
        sampling time
    pitch : float
        pitch angle of the robot
    r_imu : list
        coordinates of the IMU given in the body reference frame
    gravity : float
        magnitude of gravity field
    velocity : float
        velocity of the robot
    alpha_vel : float
        coefficient of the complementary filter used to estimate velocity
    alpha_head_rate : float
        coefficient of the complementary filter used to estimate heading rate

    Methods
    -------
    update
        performs the propagation of the state and updates the weights
    """

    def __init__(self, ts, rx, ry, rz, gravity, right_wheel, left_wheel, wheelbase ):

        self.ts = ts
        self.pitch = 0
        self.r_imu = np.array([rx, ry, rz])
        self.gravity = gravity
        self.velocity = 0
        self.alpha_vel = 0.5
        self.alpha_head_rate = 0.5
        self.gyro_n = np.array([0, 0, 0])
        self.odometry = self.Odometry(right_wheel, left_wheel, wheelbase)
        self.pf = ParticleFilter([0, 0, 0], 200, sigma_h=0.008, sigma_v=0.008)
        self.state = [0,0,0] # x,y,psi

        self.last_optical_data = [0,0]

    class Odometry:
        """
        A class to estimate position
        ...
        Attributes
        -----------
        right_radius : float
            radius of the right wheel
        left_radius : float
            radius of the left wheel
        wheelbase : float
            distance between the two wheels
        """

        def __init__(self, right_radius, left_radius, wheelbase):
            self.right_radius = right_radius
            self.left_radius = left_radius
            self.wheelbase = wheelbase

        def get_velocity(self, enc_right, enc_left):
            vel = (self.left_radius * enc_left + self.right_radius * enc_right) / 2

            return vel

        def get_heading_rate(self, enc_right, enc_left):
            head_rate = (self.right_radius * enc_right - self.left_radius * enc_left) / self.wheelbase

            return head_rate

    def update(self, acc, gyro, enc_right, enc_left, pitch, position_x, position_y):
        """
        performs the propagation of the particles and updates its weights

        Parameters
        ----------
        acc : list
            acceleration vector measured by the accelerometer
        gyro : list
            angular velocity vector measured by the gyroscope
        enc_right : float
            encoder measurement from the right wheel
        enc_left : float
            encoder measurement from the left wheel
        pitch : float
            pitch angle of the robot
        position_x : float
            x coordinate of the robot measured by the motion capture system
        position_y : float
            y coordinate of the robot measured by the motion capture system

        Returns
        --------
        state : list
            estimated state composed of the x and y coordinates and the heading
        """

        optical_data_available = True
        if abs(position_x - self.last_optical_data[0]) < 1e-8 or abs(position_y - self.last_optical_data[1]) < 1e-8:
            optical_data_available = False

        # Computation of translational acceleration
        R_b_n = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                          [0, 1, 0],
                          [-np.sin(pitch), 0, np.cos(pitch)]])
        acc_n = R_b_n @ acc
        q_pitch = qt.quaternion(pitch, [0, 1, 0])
        gyro_n = qt.quaternion_rotate(q_pitch, gyro)
        gyro_n_dot = (gyro_n - self.gyro_n) / self.ts
        a_normal = np.cross(gyro_n, (np.cross(gyro_n, self.r_imu)))
        a_tangential = np.cross(gyro_n_dot, self.r_imu)
        a_T = acc_n - a_normal - a_tangential - np.array([0, 0, self.gravity])

        # Odometry
        velocity_odometry = self.odometry.get_velocity(enc_right, enc_left)
        heading_rate_odometry = self.odometry.get_heading_rate(enc_right, enc_left)

        # IMU
        heading_rate_imu = gyro_n[2]

        # Wheel-slip detection
        is_slipping = check_slip_one(heading_rate_imu, heading_rate_odometry)
        if not is_slipping:
            is_slipping = self.check_slip_two(a_T[0], self.velocity, velocity_odometry)

        # Complementary filters coefficient
        if is_slipping:
            self.alpha_vel = 0.99
            self.alpha_head_rate = 0.99
        else:
            self.alpha_vel = 0.5
            self.alpha_head_rate = 0.5

        # Velocity computation
        velocity = self.alpha_vel * (self.velocity + a_T[0] * self.ts) + (1 - self.alpha_vel) * velocity_odometry

        # Heading rate computation
        heading_rate = self.alpha_head_rate * heading_rate_imu + (1 - self.alpha_head_rate) * heading_rate_odometry

        # Input vector
        uk = np.array([heading_rate, velocity])

        # Measurement vector
        if not optical_data_available:
            yk = np.array([])
        else:
            yk = np.array([position_x, position_y])

        # Particle filter
        state = self.pf.particlefilter(uk, yk, self.ts, 'residual_resampling2')

        # Class attributes update
        self.velocity = velocity
        self.pitch = pitch
        self.gyro_n = gyro_n

        self.last_optical_data = [position_x,position_y]

        return state,optical_data_available

    def check_slip_two(self, acc, prev_velocity, velocity_odometry):
        vel_update_imu = prev_velocity + acc * self.ts
        if abs((vel_update_imu - velocity_odometry)) >= 0.1:
            return True
        else:
            return False
