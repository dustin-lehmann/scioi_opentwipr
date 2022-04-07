# FIXME: Make a clean refactor, because of the complex import structure
# >>> dear future user, when writing code for the ML, be aware of cyclic imports

from typing import List, Dict, Tuple, Set, Optional, Union, Callable, Iterable, Iterator, Any, TextIO
import csv
import os
import threading
from enum import IntEnum

# my imports
import global_objects
from params import *
from robot import FSM_STATE, CTRL_STATE, Robot


class Operator(IntEnum):
    PASS = 0
    NOT = 1
    GEQ = 2
    LEQ = 3


class Logger:
    """
    Class for logging incoming continuous messages from the LL. Received data
    is buffered and written to the csv file <filename> after the buffer has been filled.
    Logging will be activated after receiving the message MSG_HOST_OUT_LOGGING with active=True,
    and deactivated after receiving the same message with active=False. A lock is used
    for synchronization of the LL message handler and the HL message handler thread to
    avoid writing data to the csv file simultaneously. (race condition)
    """

    src: str
    dst: str
    active: bool
    buffer_size: int
    keys: List[str]
    buffer: List[Dict[str, float]]
    index: int
    log_filepath: str
    log_filename: str
    log_file: Union[str, TextIO]
    writer: Optional[csv.DictWriter]
    logged_rows: int
    lock: threading.Lock

    def __init__(self):
        self.src = '/home/lehmann/Software/py'
        self.dst = '/home/lehmann/Software/py/Logs'
        self.active = False
        self.buffer_size = 250  # buffer size: -> Ts == 20 ms, -> buffer for 5 seconds
        self.keys = ['tick', 'fsm_state', 's', 'v', 'theta', 'theta_dot', 'psi', 'psi_dot', 'gyr_x', 'gyr_y',
                     'gyr_z', 'acc_x', 'acc_y', 'acc_z', 'torque_left', 'omega_left', 'torque_right',
                     'omega_right', 'ctrl_state', 'u_left', 'u_right', 'xdot_cmd', 'psidot_cmd']
        self.buffer = [{}] * self.buffer_size
        self.index = 0  # tracks the amount of added elements in the buffer
        self.log_filepath_new = ''  # is used for moving the logfile to the directory 'Logs'
        self.log_filepath = ''  # src + filename
        self.log_filename = ''  # just the filename + suffix '.csv'
        self.log_file = ''  # csv file object
        self.writer = None  # writer object for handling csv
        self.logged_rows = 0  # tracks the amount of logged elements
        self.lock = threading.Lock()  # only one thread is allowed to write data to the csv file at any time

    def enable(self) -> None:
        self.active = True

    def disable(self) -> None:
        self.active = False

    def reset(self) -> str:
        # save as return value
        filename = self.log_filename

        self.reset_buffer()
        self.log_filepath_new = ''
        self.log_filepath = ''
        self.log_filename = ''
        self.log_file = ''
        self.writer = None
        self.logged_rows = 0

        return filename

    def reset_buffer(self) -> None:
        self.buffer = [{}] * self.buffer_size
        self.index = 0
        
    def start_logging(self, filename: str) -> Optional[str]:
        # cleanup
        self.reset()

        # initialize variables
        self.enable()
        global_objects.robot.logging.activate_logging(filename)  # update data in the robot object
        self.log_filename = filename + '.csv'  # create logfile with the respective filename
        self.log_filepath = "{}/{}".format(self.src, self.log_filename)
        self.log_filepath_new = '{}/{}'.format(self.dst, self.log_filename)

        # create a new csv file
        try:
            self.log_file = open(self.log_filepath, 'w')
        except OSError:
            string = "Failed to open {}!".format(self.log_filepath)
            return string

        # move the file to the directory "Logs" (overwrites automatically)
        try:
            os.rename(self.log_filepath, self.log_filepath_new)
        except OSError:
            string = "Failed to rename {}!".format(self.log_filepath_new)
            return string

        # create writer object for export of buffered data
        self.writer = csv.DictWriter(self.log_file, fieldnames=self.keys)
        self.writer.writeheader()

    def buffer_data(self, data) -> Optional[int]:
        # this method is called everytime a continuous message is received from the LL
        # create data dictionary
        data_dictionary = {}
        for i, key in enumerate(self.keys):
            data_dictionary[key] = data[i]
        # and buffer data
        self.buffer[self.index] = data_dictionary
        self.index += 1

        # check index and set buffer full flag and reset write position if limit has been reached
        if not self.index == self.buffer_size:
            return

        # acquire lock for writing to csv file or wait using the context manager
        with self.lock:
            logged_rows = self.write_to_file()

        return logged_rows

    def write_to_file(self) -> Optional[int]:
        # write all buffered data to the csv file if buffer filled
        if self.index:
            for data_dict in self.buffer:
                if data_dict:
                    self.writer.writerow(data_dict)
                    self.logged_rows += 1
            self.reset_buffer()

            return self.logged_rows

    def stop_logging(self) -> Tuple[Optional[int], str]:
        # stop logging and buffering of continuous data
        self.disable()
        # write the rest of the buffered data to the csv file
        with self.lock:
            logged_rows = self.write_to_file()
        # afterwards, close csv file manually
        self.log_file.close()
        # empty buffer and reset other variables
        filename = self.reset()
        # update data in the robot object
        global_objects.robot.logging.deactivate_logging()

        return logged_rows, filename


logger = Logger()


class AbstractStructure:
    """ Abstract base for class Experiment and Sequence. """

    name: str
    sequence: Tuple[List[float], List[float]]
    sequence_length: int

    def __init__(self, name, sequence) -> None:
        self.name = name
        self.sequence = sequence
        self.sequence_length = len(sequence[0])

    def __str__(self) -> str:
        return self.name


class Sequence(AbstractStructure):
    """ An object of this class holds all relevant information about a sequence. """

    ctrl_state: int

    def __init__(self, name, sequence, ctrl_state) -> None:
        super(Sequence, self).__init__(name, sequence)
        self.ctrl_state = ctrl_state


class Experiment(AbstractStructure):
    """ An object of this class holds all relevant information about an experiment. """

    configuration: Dict[str, Any]

    def __init__(self, name, sequence, dictionary) -> None:
        super(Experiment, self).__init__(name, sequence)
        self.configuration = dictionary


def create_input_array(sequence: List[Dict[str, float]]) -> Tuple[List[float],
                                                                  List[float]]:
    input1 = []
    input2 = []
    name1 = tuple(sequence[0].keys())[0]
    name2 = tuple(sequence[0].keys())[1]

    for cmd_dict in sequence:
        input1.append(cmd_dict[name1])
        input2.append(cmd_dict[name2])

    return input1, input2


def extract_input_data(input1: List[float], input2: List[float], input_length: int) -> Tuple[List[float], List[float]]:
    input_data = ([], [])
    for i in range(input_length):
        input_data[0].append(input1[i])  # input1 is either 'u_l' or 'xdot'
        input_data[1].append(input2[i])  # input2 is either 'u_r' or 'psidot'

    return input_data


class AbstractHandler:
    """ Base class for ExperimentHandler and SequenceHandler. """

    loaded_elements: List[Union[Experiment, Sequence]]
    active_element: Optional[Union[Experiment, Sequence]]
    cached_element: Optional[Union[Experiment, Sequence]]
    valid_field_name_combinations: List[List[str]]

    def __init__(self) -> None:
        self.loaded_elements = []
        self.active_element = None
        self.cached_element = None
        self.valid_field_name_combinations = [['u1', 'u2'],
                                              ['xdot', 'psidot']]

    def load_element(self, element: Union[Experiment, Sequence]) -> None:
        self.loaded_elements.append(element)

    def element_loaded(self, name: str) -> int:
        for element in self.loaded_elements:
            if element.name == name:
                return 1
        return 0

    def idle(self) -> int:
        if not self.active_element:
            return 1
        return 0

    def get_element(self, name: str) -> Union[Experiment, Sequence]:
        # find element in loaded elements and activate it
        for element in self.loaded_elements:
            if element.name == name:
                return element

    def cache_element(self, element: Union[Experiment, Sequence]) -> None:
        self.cached_element = element

    def activate_cached_element(self) -> Union[Experiment, Sequence]:
        element = self.activate_element(self.cached_element)
        self.cached_element = None

        return element

    def activate_element(self, element: Union[Experiment, Sequence]) -> Union[Experiment, Sequence]:
        self.loaded_elements.remove(element)
        self.active_element = element

        return self.active_element

    def element_activated(self, name: str) -> int:
        if self.active_element.name == name:
            return 1
        return 0

    def deactivate_element(self) -> Union[Experiment, Sequence]:
        deactivated_element = self.active_element
        self.active_element = None

        return deactivated_element

    @staticmethod
    def convert_experiment_to_sequence(experiment: Experiment) -> Sequence:
        sequence = Sequence(experiment.name,
                            experiment.sequence,
                            experiment.configuration['prerequisites']['ctrl_state'])

        return sequence


class SequenceHandler(AbstractHandler):
    """
    This class is designed to for automatic execution of robot command sequences.
    It is able to extract and check input data from a csv file as well as loading
    it into the ML.
    """

    def __init__(self) -> None:
        super(SequenceHandler, self).__init__()

    def load_sequence_from_data(self, data: Any) -> Tuple[int, str, int, int]:
        # reconstruct input data from received message
        input_data = extract_input_data(data.input1, data.input2, data.input_length)
        # complete loading
        sequence = self.add_sequence(data.name.decode().rstrip('0'), data.ctrl_state, input_data)

        # prepare acknowledgement message for HL
        msg_data = global_objects.global_values['tick'], sequence.name, sequence.ctrl_state, sequence.sequence_length

        return msg_data

    def add_sequence(self, filename: str, ctrl_state: int, input_data: Tuple[List[float], List[float]]) -> Sequence:
        # create sequence object
        sequence = Sequence(filename, input_data, ctrl_state)

        self.loaded_elements.append(sequence)

        return sequence

    def start_sequence(self, sequence_name: str) -> Tuple[int, int, int, List[float], List[float]]:
        # the client message handler receives MSG_HOST_OUT_START_EXPERIMENT and first checks
        # if requested sequence is loaded and if sequence handler is not actively involved in a session,
        # after checking, the client message handler calls this function which starts
        # the sequence handling

        sequence = self.get_element(sequence_name)
        self.cache_element(sequence)
        # generate message for LL to start sequence with first chunk of input commands
        input1, input2 = self.fetch(0, SEQUENCE_BUFFER_LENGTH, source=sequence)

        # prepare message data for LL
        msg_data = global_objects.global_values['tick'], sequence.ctrl_state, sequence.sequence_length, input1, input2

        return msg_data

    def end_sequence(self) -> Tuple[int, int]:
        # this function is called from the server message handler
        # after checking sequence handler status and after checking if sequence name
        # and the name of the active element are the same
        msg_data = global_objects.global_values['tick'], self.active_element.ctrl_state

        return msg_data

    def reload(self, received_samples: int, reload_number: int) -> Tuple[int, int, List[float], List[float]]:
        # fetches new input data after receiving MSG_LL_OUT_RELOAD
        input1, input2 = self.fetch(received_samples, reload_number)

        # prepare the reload message with the respective input commands
        msg_data = global_objects.global_values['tick'], self.active_element.ctrl_state, input1, input2

        return msg_data

    def fetch(self, index: int, samples: int, source: Sequence = None) -> Tuple[List[float], List[float]]:
        if not source:
            source = self.active_element

        if index + samples <= source.sequence_length:
            input1 = source.sequence[0][index:index + samples]
            input2 = source.sequence[1][index:index + samples]
        else:
            # fetch the last input commands
            # constructor of MSG_LL_IN_RELOAD is going to
            # fill the rest of the input data with zeros
            input1 = source.sequence[0][index:source.sequence_length]
            input2 = source.sequence[1][index:source.sequence_length]

        # print(index, samples)
        # print(input1, input2)

        return input1, input2


sequence_handler = SequenceHandler()


class ExperimentHandler(AbstractHandler):
    """
    This class features an interface capable of reading experiment configuration files,
    loading experiments to the ML and supervising robot experiments.
    """

    main_keys: List[str]
    prerequisites_keys: List[str]
    logging_keys: List[str]
    error_conditions_list: List[str]
    number_error_conditions: int
    error_occurred: bool
    checklist: Dict[str, Any]

    def __init__(self) -> None:
        super(ExperimentHandler, self).__init__()

        # the following is used for checking the .yaml file containing the experiment configuration
        self.main_keys = ['id', 'sampling_frequency', 'duration', 'prerequisites', 'logging', 'input',
                          'error_conditions', 'error_gcode', 'start_gcode', 'end_gcode']
        self.prerequisites_keys = ['hardware_version', 'software_version', 'ctrl_state']
        self.logging_keys = ['active', 'filename']
        self.error_conditions_list = ['fsm_state', 'ctrl_state', 'x_dot', 'theta', 'theta_dot', 'psi', 'psi_dot', 'gyr_x',
                                      'gyr_y', 'gyr_z', 'acc_x', 'acc_y', 'acc_z', 'torque_left', 'omega_left',
                                      'torque_right', 'omega_right', 'u1', 'u2', 'abs_x_dot', 'abs_theta',
                                      'abs_theta_dot', 'abs_psi', 'abs_psi_dot', 'abs_gyr_x', 'abs_gyr_y', 'abs_gyr_z',
                                      'abs_acc_x', 'abs_acc_y', 'abs_acc_z', 'abs_torque_left', 'abs_omega_left',
                                      'abs_torque_right', 'abs_omega_right', 'abs_u1', 'abs_u2']
        self.error_occurred = False
        self.checklist = {'sampling_frequency_min': 50,
                          'sampling_frequency_max': 100,
                          'duration_min': 1,
                          'duration_max': 20,
                          'hardware_version_min': 1,
                          'software_version_min': 1}

    def load_experiment_from_data(self, received_data: Any) -> Tuple[int, str, int, int]:
        # load received experiment configuration into experiment handler list
        reconstructed_exp_config = self.reconstruct_experiment_from_data(received_data)
        # the data is interpreted and converted to an Experiment object
        # the Experiment is then added to the list
        experiment = self.add_experiment(reconstructed_exp_config)

        # prepare acknowledgement message for HL
        msg_data = global_objects.global_values['tick'], experiment.name, \
                   experiment.configuration['prerequisites']['ctrl_state'], \
                   experiment.sequence_length

        return msg_data

    @staticmethod
    def reconstruct_experiment_from_data(data: Any) -> Tuple[str, Dict[str, Any], Tuple[List[float], List[float]]]:
        name = data.name.decode().rstrip('0')

        exp_config = {'id': name,
                      'sampling_frequency': data.sampling_frequency,
                      'duration': data.duration,
                      'prerequisites': {'hardware_version': data.hardware_version,
                                        'software_version': data.software_version,
                                        'ctrl_state': data.ctrl_state},
                      'logging': {'active': data.logging_active,
                                  'filename': data.filename},
                      'error_conditions': {'fsm_state': [Operator(data.fsm_state_condition), data.fsm_state_threshold],
                                           'ctrl_state': [Operator(data.ctrl_state_condition), data.ctrl_state_threshold],

                                           # 'x': [Operator(data.x_condition), data.x_threshold],
                                           # 'y': [Operator(data.y_condition), data.y_threshold],
                                           'x_dot': [Operator(data.x_dot_condition), data.x_dot_threshold],
                                           'theta': [Operator(data.theta_condition), data.theta_threshold],
                                           'theta_dot': [Operator(data.theta_dot_condition), data.theta_dot_threshold],
                                           'psi': [Operator(data.psi_condition), data.psi_threshold],
                                           'psi_dot': [Operator(data.psi_dot_condition), data.psi_dot_threshold],
                                           'gyr_x': [Operator(data.gyr_x_condition), data.gyr_x_threshold],
                                           'gyr_y': [Operator(data.gyr_y_condition), data.gyr_y_threshold],
                                           'gyr_z': [Operator(data.gyr_z_condition), data.gyr_z_threshold],
                                           'acc_x': [Operator(data.acc_x_condition), data.acc_x_threshold],
                                           'acc_y': [Operator(data.acc_y_condition), data.acc_y_threshold],
                                           'acc_z': [Operator(data.acc_z_condition), data.acc_z_threshold],
                                           'torque_left': [Operator(data.torque_left_condition), data.torque_left_threshold],
                                           'omega_left': [Operator(data.omega_left_condition), data.omega_left_threshold],
                                           'torque_right': [Operator(data.torque_right_condition), data.torque_right_threshold],
                                           'omega_right': [Operator(data.omega_right_condition), data.omega_right_threshold],
                                           'u1': [Operator(data.u1_condition), data.u1_threshold],
                                           'u2': [Operator(data.u2_condition), data.u2_threshold],

                                           'abs_x': [Operator(data.abs_x_condition), data.abs_x_threshold],
                                           'abs_y': [Operator(data.abs_y_condition), data.abs_y_threshold],
                                           'abs_x_dot': [Operator(data.abs_x_dot_condition), data.abs_x_dot_threshold],
                                           'abs_theta': [Operator(data.abs_theta_condition), data.abs_theta_threshold],
                                           'abs_theta_dot': [Operator(data.abs_theta_dot_condition), data.abs_theta_dot_threshold],
                                           'abs_psi': [Operator(data.abs_psi_condition), data.abs_psi_threshold],
                                           'abs_psi_dot': [Operator(data.abs_psi_dot_condition), data.abs_psi_dot_threshold],
                                           'abs_gyr_x': [Operator(data.abs_gyr_x_condition), data.abs_gyr_x_threshold],
                                           'abs_gyr_y': [Operator(data.abs_gyr_y_condition), data.abs_gyr_y_threshold],
                                           'abs_gyr_z': [Operator(data.abs_gyr_z_condition), data.abs_gyr_z_threshold],
                                           'abs_acc_x': [Operator(data.abs_acc_x_condition), data.abs_acc_x_threshold],
                                           'abs_acc_y': [Operator(data.abs_acc_y_condition), data.abs_acc_y_threshold],
                                           'abs_acc_z': [Operator(data.abs_acc_z_condition), data.abs_acc_z_threshold],
                                           'abs_torque_left': [Operator(data.abs_torque_left_condition), data.abs_torque_left_threshold],
                                           'abs_omega_left': [Operator(data.abs_omega_left_condition), data.abs_omega_left_threshold],
                                           'abs_torque_right': [Operator(data.abs_torque_right_condition), data.abs_torque_right_threshold],
                                           'abs_omega_right': [Operator(data.abs_omega_right_condition), data.abs_omega_right_threshold],
                                           'abs_u1': [Operator(data.abs_u1_condition), data.abs_u1_threshold],
                                           'abs_u2': [Operator(data.abs_u2_condition), data.abs_u2_threshold]}}

        # reconstruct input data to get the desired format
        input_data = extract_input_data(data.input1, data.input2, data.input_length)

        # return name, experiment configuration and input data
        return name, exp_config, input_data

    def add_experiment(self, reconstructed_exp_config: Tuple[
        str, Dict[str, Any], Tuple[List[float], List[float]]]) -> Experiment:
        # unpack tuple
        name, dictionary, input_data = reconstructed_exp_config
        # transfer experiment configuration to an object of class Experiment
        experiment = Experiment(name, input_data, dictionary)
        # add to list
        self.loaded_elements.append(experiment)

        return experiment

    def start_experiment(self, experiment_name: str) -> Tuple[int, int, int, List[float], List[float]]:
        # is called by the HL message handler after receiving MSG_HOST_OUT_START_EXPERIMENT
        # the goal is to prepare everything needed to start the experiment and then,
        # to return a MSG_LL_IN_START_SEQUENCE, because the LL only knows how to execute sequences

        # cache experiment, so that it can be activated after an receiving an
        # acknowledgement message from the LL
        experiment = self.get_element(experiment_name)
        self.cache_element(experiment)

        # request active session from sequence handler, using the converted sequence
        sequence = self.convert_experiment_to_sequence(experiment)
        sequence_handler.load_element(sequence)
        # prepare message data for LL
        msg_data = sequence_handler.start_sequence(sequence.name)

        return msg_data

    def activate_cached_element(self) -> Union[Experiment, Sequence]:
        # this function is called by the LL message handler after it received the "started sequence" acknowledgement
        activated_experiment = self.activate_element(self.cached_element)
        self.cached_element = None

        # sequence handler is active if experiment handler is active
        sequence_handler.activate_cached_element()

        # if logging is part of the experiment config, start logging process
        if activated_experiment.configuration['logging']['active']:
            logger.start_logging(activated_experiment.configuration['logging']['filename'])

        return activated_experiment

    def end_experiment(self, error_condition: bool = False) -> Tuple[int, int]:
        # this function requests ending the sequence currently handled by the sequence handler
        # if an acknowledgement is received from the LL,
        # the message handler will contact the experiment handler, so it can deactivate the active experiment
        # and sequence in both handlers
        msg_data = sequence_handler.end_sequence()

        # set error flag, so that message handler knows how to react on MSG_LL_OUT_END_SEQUENCE
        if error_condition:
            self.error_occurred = True

        return msg_data

    def deactivate_element(self) -> Tuple[Experiment, bool]:
        deactivated_experiment = self.active_element
        self.active_element = None

        # do not forget to deactivate currently active element in the sequence handler
        sequence_handler.deactivate_element()

        # if error flag is set, reset it
        success = not self.error_occurred
        if self.error_occurred:
            self.error_occurred = False

        # if logger is active, shut it down now
        if logger.active:
            logger.stop_logging()

        return deactivated_experiment, success

    def check_robot(self) -> Tuple[int, str]:
        # this function monitors the data from the global Robot object continuously
        # while comparing it the error conditions from the experiment configuration file
        # on error, it returns a tuple containing the error id as well as an individual string
        error_id = ERROR_DURING_EXPERIMENT
        error_string = ''

        error_conditions: Dict[str, List[Union[int, float]]] = self.active_element.configuration['error_conditions']
        # REMEMBER: arr[0] of for example error_conditions['fsm_state'] is encoded in the following way:
        # no error condition: 0, not threshold: 1, greater or equal: 2, less or equal: 3
        # if you do not understand, please have a look at the function reconstruct_experiment_from_data(), line 381
        # or try to understand the experiment configuration file (.yaml)
        # iterate iver keys of dictionary error_conditions
        for error_condition in error_conditions:
            if error_conditions[error_condition][0] is not Operator.PASS:
                error_string = self.check_error_condition(error_condition)

                if error_string:
                    break

        return error_id, error_string

    def check_error_condition(self, key: str) -> str:
        error_string = ''

        # get robot data for comparison
        var = self.get_robot_data_from_key(key)
        if not var:
            print("Failed to get robot data from key={}!".format(key))

        # and compare
        if self.active_element.configuration['error_conditions'][key][0] is Operator.NOT and \
                self.active_element.configuration['error_conditions'][key][1] != var:
            error_string = "EXPERIMENT ERROR (Operator.NOT): key={}".format(key)

        elif self.active_element.configuration['error_conditions'][key][0] is Operator.GEQ and \
                self.active_element.configuration['error_conditions'][key][1] <= var:
            error_string = "EXPERIMENT ERROR (Operator.GEQ): key={}".format(key)

        elif self.active_element.configuration['error_conditions'][key][0] is Operator.LEQ and \
                self.active_element.configuration['error_conditions'][key][1] >= var:
            error_string = "EXPERIMENT ERROR (Operator.LEQ): key={}".format(key)

        return error_string

    @staticmethod
    def get_robot_data_from_key(key: str) -> Optional[Union[int, float]]:
        if key == 'fsm_state':
            ret = global_objects.robot.ll_fsm_state.value
        elif key == 'ctrl_state':
            ret = global_objects.robot.controller.state.value

        elif key == 'x_dot':
            ret = global_objects.robot.state.sdot
        elif key == 'theta':
            ret = global_objects.robot.state.theta
        elif key == 'theta_dot':
            ret = global_objects.robot.state.thetadot
        elif key == 'psi':
            ret = global_objects.robot.state.psi
        elif key == 'psi_dot':
            ret = global_objects.robot.state.psidot
        elif key == 'gyr_x':
            ret = global_objects.robot.sensors.imu.gyr[0]
        elif key == 'gyr_y':
            ret = global_objects.robot.sensors.imu.gyr[1]
        elif key == 'gyr_z':
            ret = global_objects.robot.sensors.imu.gyr[2]
        elif key == 'acc_x':
            ret = global_objects.robot.sensors.imu.acc[0]
        elif key == 'acc_y':
            ret = global_objects.robot.sensors.imu.acc[1]
        elif key == 'acc_z':
            ret = global_objects.robot.sensors.imu.acc[2]
        elif key == 'torque_left':
            ret = global_objects.robot.drive.torque_left
        elif key == 'omega_left':
            ret = global_objects.robot.sensors.encoder_left.omega
        elif key == 'torque_right':
            ret = global_objects.robot.drive.torque_right
        elif key == 'omega_right':
            ret = global_objects.robot.sensors.encoder_right.omega
        elif key == 'u1':
            ret = global_objects.robot.controller.u[0]
        elif key == 'u2':
            ret = global_objects.robot.controller.u[1]

        elif key == 'abs_x_dot':
            ret = abs(global_objects.robot.state.sdot)
        elif key == 'abs_theta':
            ret = abs(global_objects.robot.state.theta)
        elif key == 'abs_theta_dot':
            ret = abs(global_objects.robot.state.thetadot)
        elif key == 'abs_psi':
            ret = abs(global_objects.robot.state.psi)
        elif key == 'abs_psi_dot':
            ret = abs(global_objects.robot.state.psidot)
        elif key == 'abs_gyr_x':
            ret = abs(global_objects.robot.sensors.imu.gyr[0])
        elif key == 'abs_gyr_y':
            ret = abs(global_objects.robot.sensors.imu.gyr[1])
        elif key == 'abs_gyr_z':
            ret = abs(global_objects.robot.sensors.imu.gyr[2])
        elif key == 'abs_acc_x':
            ret = abs(global_objects.robot.sensors.imu.acc[0])
        elif key == 'abs_acc_y':
            ret = abs(global_objects.robot.sensors.imu.acc[1])
        elif key == 'abs_acc_z':
            ret = abs(global_objects.robot.sensors.imu.acc[2])
        elif key == 'abs_torque_left':
            ret = abs(global_objects.robot.drive.torque_left)
        elif key == 'abs_omega_left':
            ret = abs(global_objects.robot.sensors.encoder_left.omega)
        elif key == 'abs_torque_right':
            ret = abs(global_objects.robot.drive.torque_right)
        elif key == 'abs_omega_right':
            ret = abs(global_objects.robot.sensors.encoder_right.omega)
        elif key == 'abs_u1':
            ret = abs(global_objects.robot.controller.u[0])
        elif key == 'abs_u2':
            ret = abs(global_objects.robot.controller.u[1])

        else:
            ret = None

        return ret


experiment_handler = ExperimentHandler()
