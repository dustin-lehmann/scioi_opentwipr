import os
from typing import List, Dict, Tuple, Set, Optional, Union, Callable, Iterable, Iterator, Any

# host files
from Communication.messages import *
from Communication.gcode_parser import gcode_parser
from IO.file_handlers import csv_handler, yaml_handler, file_handler
from params import *

# CONSTANTS
MAX_NUMBER_INPUT = 2000


class Operator(IntEnum):
    PASS = 0
    NOT = 1
    GEQ = 2
    LEQ = 3


class AbstractStructure:
    """ Abstract base for class Experiment and Sequence. """

    name: str
    sequence: List[Dict[str, float]]
    sequence_length: int

    def __init__(self, name, sequence) -> None:
        self.name = name
        self.sequence = sequence
        self.sequence_length = len(sequence)

    def __str__(self) -> str:
        return self.name


class Experiment(AbstractStructure):
    """ An object of this class holds all relevant information about an experiment. """

    configuration: Dict[str, Any]

    def __init__(self, name, sequence, dictionary) -> None:
        super(Experiment, self).__init__(name, sequence)
        self.configuration = dictionary


class Sequence(AbstractStructure):
    """ An object of this class holds all relevant information about a sequence. """

    ctrl_state: int

    def __init__(self, name, sequence, ctrl_state) -> None:
        super(Sequence, self).__init__(name, sequence)
        self.ctrl_state = ctrl_state


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


class AbstractHandler:
    """ Base class for ExperimentHandler and SequenceHandler. """

    loaded_elements: List[Union[Experiment, Sequence]]
    active_element: Union[Experiment, Sequence]
    valid_field_name_combinations: List[List[str]]
    
    def __init__(self) -> None:
        self.loaded_elements = []
        self.valid_field_name_combinations = [['u1', 'u2'], ['xdot', 'psidot']]
        
    def get_element(self, element_name) -> Union[Experiment, Sequence]:
        # find element in loaded elements and activate it
        for element in self.loaded_elements:
            if element.name == element_name:
                return element


class ExperimentHandler(AbstractHandler):
    """
    This class features an interface capable of reading experiment configuration files,
    loading experiments to the ML and supervising robot experiments.
    """

    exp_ctrl_states: Dict[str, int]
    main_keys: List[str]
    prerequisites_keys: List[str]
    logging_keys: List[str]
    error_conditions_list: List[str]
    checklist: Dict[str, Any]

    def __init__(self) -> None:
        super(ExperimentHandler, self).__init__()

        # the following is used for checking the .yaml file containing the experiment configuration
        self.exp_ctrl_states = {'SF': 2, 'VEL': 3}
        self.main_keys = ['id', 'sampling_frequency', 'duration', 'prerequisites', 'logging', 'input', 
                          'error_conditions', 'start_gcodes', 'error_gcodes', 'end_gcodes']
        self.prerequisites_keys = ['hardware_version', 'software_version', 'ctrl_state']
        self.logging_keys = ['active', 'filename']
        self.error_conditions_list = ['fsm_state', 'ctrl_state', 'x', 'y', 'x_dot', 'theta', 'theta_dot', 'psi',
                                      'psi_dot', 'gyr_x', 'gyr_y', 'gyr_z', 'acc_x', 'acc_y', 'acc_z', 'torque_left',
                                      'omega_left', 'torque_right', 'omega_right', 'u1', 'u2', 'abs_x', 'abs_y',
                                      'abs_x_dot', 'abs_theta', 'abs_theta_dot', 'abs_psi', 'abs_psi_dot', 'abs_gyr_x',
                                      'abs_gyr_y', 'abs_gyr_z', 'abs_acc_x', 'abs_acc_y', 'abs_acc_z',
                                      'abs_torque_left', 'abs_omega_left', 'abs_torque_right', 'abs_omega_right',
                                      'abs_u1', 'abs_u2']
        self.checklist = {'sampling_frequency_min': 50,
                          'sampling_frequency_max': 100,
                          'duration_min': 1,
                          'duration_max': 20,
                          'hardware_version_min': 1,
                          'software_version_min': 1}

    def load_experiment(self, filename: Optional[str] = None) -> Optional[MSG_HOST_OUT_LOAD_EXPERIMENT]:
        # this function is called after the user sent the respective G-code for
        # loading the experiment, if called without arguments, the default experiment
        # configuration file is read and processed
        if not filename:
            filename = 'experiment'
        filepath = 'Miscellaneous/' + filename + '.yaml'

        # the function should request reading a.yaml file
        # from the yaml_handler, after receiving a dictionary-like object
        dictionary = yaml_handler.get_dictionary(filepath)
        if not dictionary:
            return None
        # the experiment_handler moves on to processing the experiment configuration from the dictionary with
        # process_yaml() also include reading a csv file with csv handler
        validated_experiment = self.validate_experiment_configuration(dictionary)
        if not validated_experiment:
            return None
        # -> error: return None
        # if no errors occurs, create an obj from Experiment and add to list
        experiment = self.add_experiment(validated_experiment)
        # and return MSG_HOST_OUT_LOAD_EXPERIMENT
        msg = self.generate_message_for_loading_experiment(experiment)

        return msg

    def load_and_start_experiment(self, filename: Optional[str] = None) -> Optional[Tuple[MSG_HOST_OUT_LOAD_EXPERIMENT,
                                                                                          MSG_HOST_OUT_START_EXPERIMENT]]:
        msg_load = self.load_experiment(filename)
        msg_start, start_gcodes = self.start_experiment(filename)

        if not msg_load:
            return

        return msg_load, msg_start

    def validate_experiment_configuration(self, experiment_config: Dict[str, Any]) -> Optional[Tuple[str,
                                                                                               Dict[str, Any],
                                                                                               List[Dict[str, float]]]]:
        # this function just scans the configuration from the read yaml file
        # check all points of the example yaml file from dustin, for example
        # the file containing the sequence should exist, g-codes should be valid too etc.

        # ============================================================================================================= #
        # check basic structure of the configuration file
        for key in self.main_keys:
            if key not in list(experiment_config.keys()):
                return None

        for key in self.prerequisites_keys:
            if key not in list(experiment_config['prerequisites'].keys()):
                return None

        for key in self.logging_keys:
            if key not in list(experiment_config['logging'].keys()):
                return None

        # ============================================================================================================= #
        # check id
        name = experiment_config['id']
        if type(name) is not str or not name:
            return None

        # ============================================================================================================= #
        # check sampling frequency
        sampling_frequency = experiment_config['sampling_frequency']
        valid = self.checklist['sampling_frequency_min'] <= \
                sampling_frequency <= \
                self.checklist['sampling_frequency_max']
        if type(sampling_frequency) is not int or not valid:
            return None

        # ============================================================================================================= #
        # check duration
        duration = experiment_config['duration']
        valid = self.checklist['duration_min'] <= \
                duration <= \
                self.checklist['duration_max']
        if type(duration) is not int or not valid:
            return None

        # ============================================================================================================= #
        # check prerequisites
        hardware_version = experiment_config['prerequisites']['hardware_version']
        valid = self.checklist['hardware_version_min'] <= hardware_version
        if type(hardware_version) is not float or not valid:
            return None

        software_version = experiment_config['prerequisites']['software_version']
        valid = self.checklist['software_version_min'] <= software_version
        if type(software_version) is not float or not valid:
            return None

        # ctrl_state is not checked at this point, it will be checked after a MSG_HOST_OUT_START_EXPERIMENT
        # has been received from the ML

        # ============================================================================================================= #
        # check logging
        logging_requested = experiment_config['logging']['active']
        if type(logging_requested) is not bool:
            return None

        log_filename = experiment_config['logging']['filename']
        if logging_requested and (type(log_filename) is not str or not log_filename):
            return None

        # ============================================================================================================= #
        # check input
        input_filepath = experiment_config['input']
        if type(input_filepath) is not str or not input_filepath:
            return None

        # now read the input file and check the structure as well as the number of rows
        # check for error because input file could be formatted incorrectly
        input_data = csv_handler.read(input_filepath, self.valid_field_name_combinations)
        if not input_data:
            return None

        # also, check if sampling frequency, duration meet the number of data rows in csv, else -> error
        required_number_of_samples = experiment_config['sampling_frequency'] * experiment_config['duration']
        if required_number_of_samples is not len(input_data):
            return None

        # check if ctrl_state and input commands match each other
        ctrl_state = experiment_config['prerequisites']['ctrl_state']
        fieldnames = list(input_data[0].keys())
        if ctrl_state is 'SF' and fieldnames is not self.valid_field_name_combinations[0]:
            return None
        if ctrl_state is 'VEL' and fieldnames is not self.valid_field_name_combinations[1]:
            return None

        # ... at this point, the input file seems to be correctly formatted

        # ============================================================================================================= #
        # check error conditions
        error_dictionary = experiment_config['error_conditions']
        for key, array in error_dictionary.items():
            if key not in self.error_conditions_list:
                return None
            if len(array) is not 2:
                return None
            if type(array[0]) is not str and array[0] not in ('GEQ', 'LEQ'):
                return None
            if type(array[1]) not in (int, float):
                return None

        # ============================================================================================================= #
        # check start, end and error g-codes
        commands = experiment_config['error_gcodes'] + \
                   experiment_config['start_gcodes'] + \
                   experiment_config['end_gcodes']

        for cmd in commands:
            gcode_parser_output = gcode_parser.parse(cmd)

            if type(gcode_parser_output) == list:
                if gcode_parser_output[0]['type'] == 'M60':
                    return None

        # at this point, the experiment configuration is valid, because it passed all tests defined above
        # return name of experiment, configuration dictionary as well as the input data as a list
        return experiment_config['id'], experiment_config, input_data

    def add_experiment(self, validated_experiment: Tuple[str, Dict[str, Any], List[Dict[str, float]]]) -> Experiment:
        # unpack tuple
        name, dictionary, input_data = validated_experiment
        # transfer experiment configuration to an object of class Experiment
        experiment = Experiment(name, input_data, dictionary)
        # add to list
        self.loaded_elements.append(experiment)

        return experiment

    def remove_experiment(self, experiment_name: str) -> Tuple[List[str], List[str]]:
        experiment = self.get_element(experiment_name)
        self.loaded_elements.remove(experiment)

        return experiment.configuration['error_gcodes'], experiment.configuration['end_gcodes']

    def generate_message_for_loading_experiment(self, experiment: Experiment) -> MSG_HOST_OUT_LOAD_EXPERIMENT:
        # some processing to fit everything into the message object correctly
        payload = self.prepare_message_data(experiment)

        # create message object
        msg = MSG_HOST_OUT_LOAD_EXPERIMENT(payload[0], payload[1], payload[2], payload[3], payload[4],
                                           payload[5], payload[6], payload[7], payload[8],

                                           payload[9], payload[10], payload[11],

                                           payload[12], payload[13],
                                           payload[14], payload[15],

                                           payload[16], payload[17], payload[18], payload[19], payload[20],
                                           payload[21], payload[22], payload[23], payload[24], payload[25],
                                           payload[26], payload[27], payload[28], payload[29], payload[30],
                                           payload[31], payload[32], payload[33], payload[34], payload[35],
                                           payload[36], payload[37], payload[38], payload[39], payload[40],
                                           payload[41], payload[42], payload[43], payload[44], payload[45],
                                           payload[46], payload[47], payload[48], payload[49], payload[50],
                                           payload[51], payload[52], payload[53],

                                           payload[54], payload[55], payload[56], payload[57], payload[58],
                                           payload[59], payload[60], payload[61], payload[62], payload[63],
                                           payload[64], payload[65], payload[66], payload[67], payload[68],
                                           payload[69], payload[70], payload[71], payload[72], payload[73],
                                           payload[74], payload[75], payload[76], payload[77], payload[78],
                                           payload[79], payload[80], payload[81], payload[82], payload[83],
                                           payload[84], payload[85], payload[86], payload[87], payload[88],
                                           payload[89], payload[90], payload[91])

        return msg

    def prepare_message_data(self, experiment: Experiment) -> List[Union[int, float]]:
        # the data prepared here, will be transferred to the constructor of
        # MSG_HOST_OUT_LOAD_EXPERIMENT directly

        ctrl_state = self.exp_ctrl_states[experiment.configuration['ctrl_state']]  # str -> c_uint8

        data = [0,
                experiment.name,
                experiment.configuration['sampling_frequency'],
                experiment.configuration['duration'],
                experiment.configuration['hardware_version'],
                experiment.configuration['software_version'],
                ctrl_state,
                experiment.configuration['active'],
                experiment.configuration['filename']]

        # get correctly formatted input tuple
        input1, input2 = create_input_array(experiment.sequence)
        if len(experiment.sequence) < MAX_NUMBER_INPUT:
            input1 += [0] * (MAX_NUMBER_INPUT - experiment.sequence_length)
            input1 += [0] * (MAX_NUMBER_INPUT - experiment.sequence_length)
        data += experiment.sequence_length + tuple(input1) + tuple(input2)

        # loop through optional error conditions
        err_arr = []
        for error_condition in self.error_conditions_list:
            ret_arr = experiment.configuration['error_conditions'].get(error_condition)
            if not ret_arr:
                err_arr += [Operator.PASS.value, 0]  # no condition, no threshold, just fill the data with zeros at this point

            # the first element sets the comparison operator
            # no error condition: 0, not threshold: 1, greater or equal: 2, less or equal: 3
            if ret_arr[0] == 'NOT':
                ret_arr[0] = Operator.NOT.value
            elif ret_arr[0] == 'GEQ':
                ret_arr[0] = Operator.GEQ.value
            elif ret_arr[0] == 'LEQ':
                ret_arr[0] = Operator.LEQ.value
            else:
                pass

            err_arr += ret_arr

        data += err_arr

        return data

    def start_experiment(self, name: str = None) -> Tuple[MSG_HOST_OUT_START_EXPERIMENT, List[str]]:
        if not name:
            name = 'experiment'

        # execute G-codes before starting experiment
        # currently, the HL will execute these G-codes before the HL message handler starts blocking
        # after executing these g-codes, it is possible, that the LL will throw ERROR_CANNOT_START_EXPERIMENT
        start_commands = self.get_start_gcodes(name)
        
        msg = MSG_HOST_OUT_START_EXPERIMENT(0, name)
        
        return msg, start_commands

    @staticmethod
    def end_experiment(name: str = None) -> MSG_HOST_OUT_END_EXPERIMENT:
        if not name:
            name = 'experiment'

        msg = MSG_HOST_OUT_END_EXPERIMENT(0, name)
        return msg

    def get_start_gcodes(self, experiment_name: str) -> List[str]:
        # executed before HL message handler block (before sending MSG_HOST_OUT_START_EXPERIMENT)
        experiment = self.get_element(experiment_name)
        
        commands = experiment.configuration['start_gcodes']

        return commands


class SequenceHandler(AbstractHandler):
    """
    This class is designed to for automatic execution of robot command sequences.
    It is able to extract and check input data from a csv file as well as loading
    it into the ML.
    """

    def __init__(self) -> None:
        super(SequenceHandler, self).__init__()

    def load_sequence(self, filename: Optional[str] = None) -> Optional[MSG_HOST_OUT_LOAD_SEQUENCE]:
        # this function requests reading a csv file containing input data for the robot
        if not filename:
            filename = 'sequence'
        filepath = 'Miscellaneous/' + filename + '.csv'

        # csv handler reads and executes a short validity check with the
        # given field name combinations, outputs a nice list with respective mappings
        input_data = csv_handler.read(filepath, self.valid_field_name_combinations)
        if not input_data:
            return None

        # check if it exceeds max size, which is: 100 Hz * 20 s = 2000 samples
        if len(input_data) > 2000:
            return None

        # create sequence and add to loaded_elements
        filename = os.path.split(filepath)[-1].rstrip('.csv')
        sequence = self.add_sequence(filename, input_data)

        msg = self.generate_message_for_loading_sequence(sequence)

        return msg

    def load_and_start_sequence(self, filename: Optional[str] = None) -> Optional[Tuple[MSG_HOST_OUT_LOAD_SEQUENCE,
                                                                                        MSG_HOST_OUT_START_SEQUENCE]]:
        msg_load = self.load_sequence(filename)
        msg_start = self.start_sequence(filename)

        if not msg_load:
            return

        return msg_load, msg_start

    def add_sequence(self, filename: str, input_data: List[Dict[str, float]]) -> Sequence:
        # get the controller state of sequence
        # if you want to execute torque commands during DIRECT mode,
        # just load like for SF ('u1', 'u2') and start sequence in DIRECT
        if tuple(input_data[0].keys())[0] == 'u1':
            ctrl_state = CTRL_STATE.STATE_FEEDBACK
        else:
            ctrl_state = CTRL_STATE.VELOCITY

        sequence = Sequence(filename, input_data, ctrl_state.value)

        self.loaded_elements.append(sequence)

        return sequence

    def remove_sequence(self, sequence_name: str) -> None:
        sequence = self.get_element(sequence_name)
        self.loaded_elements.remove(sequence)

    @staticmethod
    def generate_message_for_loading_sequence(sequence: Sequence) -> MSG_HOST_OUT_LOAD_SEQUENCE:
        input1, input2 = create_input_array(sequence.sequence)

        msg = MSG_HOST_OUT_LOAD_SEQUENCE(0,
                                         sequence.name,
                                         sequence.ctrl_state,
                                         sequence.sequence_length,
                                         input1,
                                         input2)

        return msg

    @staticmethod
    def start_sequence(name: str = None) -> MSG_HOST_OUT_START_SEQUENCE:
        if not name:
            name = 'sequence'

        msg = MSG_HOST_OUT_START_SEQUENCE(0, name)
        return msg

    @staticmethod
    def end_sequence(name: str = None) -> MSG_HOST_OUT_END_SEQUENCE:
        if not name:
            name = 'sequence'

        msg = MSG_HOST_OUT_END_SEQUENCE(0, name)
        return msg


experiment_handler = ExperimentHandler()
sequence_handler = SequenceHandler()

# ################################################################################################################### #
# NOTES:

# CHECK !
# >>> G-code LOAD EXP
# gcode for prepping an experiment
# experiment handler asks yaml_handler to read yaml file -> read_yaml() -> process_yaml()
# an object EXPERIMENT is created holding all the relevant data from the yaml file
# the data from the read file is thoroughly checked -> an error is raised (processed)
# if alright, do the following:
# we need to send a message PREPARE EXP with all the relevant data to the ML
# after receiving the PREP MSG the ML client msg handler activates the experiment handler
# and creates an EXP obj from the received data
# after which this object is signed as READY in the experiment handler of the ML and HL

# CHECK !
# >>> G-code LOAD SEQ (ml queue with elements in the following form: dict{type, ul ur or x or psi})
# sequence handler reads csv file
# processes the file and checks for errors, maybe only 1 column and its ul -> error load seq
# error or move checked seqeuence to prepped sequences and
# send the processed seq to the ML sequence handler
# ML sequence handler adds the seq dict to the internal queue

# >>> G-code START EXP
# M65 Start Experiment -> G-Code parser should output MSG_HOST_START_EXPERIMENT
# ML checks if requested exp is loaded first -> if not error msg CANNOT_START_EXPERIMENT with overview of loaded exps
# after receiving the STArT EXP MSG the exp handler selects the correct experiment object from
# its memory and executes the start exp routine that includes
# ---- request sequence handling from seq handler and load exp sequence into sequence handler
# ---- if currently executing a seq, return CANNOT START EXP, if not then
# ---- ---- self.load_sequence(exp_data)
# ---- ---- -> the sequences are stored as dicts too (type, content with buffers etc.)
# ---- ---- -> is moved to active_sequence and a ML->LL MSG is sent (LOAD SEQ)

# MSG LOAD SEQ contains a 75 sample big seq buffer and, the LL can interpret by just reading
# the content of 0xFF then its empty, if the LL found the correct buffer, it understands and
# writes the buffer to the global buffer where sequences of the respective cmds are stored
# after that it sets a flag FROM_SEQUENCE which tells the respective controller from where to
# read commands -> a counter should be incremented after every control cycle if the flag
# FROM_SEQUENCE is set, after using 50 samples RELOAD MSG is sent
# LL needs a global sequence_handler that
# ---- is activated when loading the sequence
# ---- that sets the ACTIVE_SEQUENCE
# ---- processes controller requests for the next sample
# ---- controls the read position and is responsible for incrementing reading position
# ---- after a control cycle, the reading position has to be checked in case a reload should be
# requested from ML
# TODO:
# error handling ? stopping? think thorugh the whole reload thing first (2)

# TODO: PRIO SEC: then go over to start exp / seq


