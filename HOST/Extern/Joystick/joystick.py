from __future__ import annotations
from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator
import pygame
import os
import json
import time
import threading

# My Imports
# Rumble only works on Windows currently
try:
    from Extern.Joystick.rumble import RumbleHandlerThread, weak_rumble, strong_rumble
except OSError:
    print("Game controller rumble only works on Windows currently!")


    class RumbleHandlerThread(threading.Thread):
        def __init__(self) -> None:
            super().__init__()

        def run(self) -> None:
            pass

        @staticmethod
        def rumble(*args: any) -> None:
            pass

        def request_rumble(self, *args: any) -> None:
            pass

        def weak_rumble(self) -> None:
            pass

        def strong_rumble(self) -> None:
            pass


from Ui.robot_ui import RobotUi
from Robot.data import *


class JoystickHandler:
    robot_ui_list: List[Union[RobotUi, int]]
    robot_ui_list_len: int
    unassigned_joysticks: List[Joystick]
    assigned_joysticks: List[Joystick]
    rumble_handler_thread: RumbleHandlerThread
    count_joyaxismotion: int
    limit_joyaxismotion: int

    def __init__(self, client_ui_list: List[Union[RobotUi, int]]) -> None:
        # containing all the RobotUi objects currently in use
        self.robot_ui_list = client_ui_list
        self.robot_ui_list_len = len(self.robot_ui_list)
        # containers for the unassigned and assigned as well as initialized joysticks
        self.unassigned_joysticks = []
        self.assigned_joysticks = []
        # additional thread for activating the rumble feature
        self.rumble_handler_thread = RumbleHandlerThread()
        self.rumble_handler_thread.start()
        # initialize the pygame and pygame.joystick module
        pygame.init()
        # for optimization
        self.count_joyaxismotion = 0
        self.limit_joyaxismotion = 5

    def process_events(self) -> None:
        # event queue is processed regularly in the timer thread (currently, every 100 ms)
        for event in pygame.event.get():
            # print(event)
            if event.type == pygame.JOYDEVICEADDED:
                self.joystick_added(event)
            elif event.type == pygame.JOYDEVICEREMOVED:
                self.joystick_removed(event)
            # TODO: POLL AXES 0, 1, 2 & 3 INSTEAD OF USING THE JOYAXISMOTION EVENTS
            elif event.type == pygame.JOYAXISMOTION:
                if self.count_joyaxismotion < self.limit_joyaxismotion:
                    self.process_joystick_input(event)
                    self.count_joyaxismotion += 1
            elif event.type in (pygame.JOYBUTTONDOWN,
                                pygame.JOYBUTTONUP,
                                pygame.JOYHATMOTION):
                self.process_joystick_input(event)
        # reset flag
        if self.count_joyaxismotion == self.limit_joyaxismotion:
            self.count_joyaxismotion = 0

    def joystick_added(self, event: pygame.event.Event) -> None:
        # add joystick to internal list
        joystick = self.initialize_joystick(event)

        # assign joystick to the respective RobotUi object
        self.assign_joystick(joystick=joystick)

    def robot_added(self, robot_ui: RobotUi) -> None:
        self.assign_joystick(robot_ui=robot_ui)

    def initialize_joystick(self, event: pygame.event.Event) -> Joystick:
        j_id = event.device_index
        joystick = Joystick(self, pygame.joystick.Joystick(j_id))
        self.unassigned_joysticks.append(joystick)
        print("Joystick {} was initialized successfully!".format(joystick.information["instance_id"]))
        return joystick

    def reassign_joystick(self, joystick: Joystick) -> None:
        self.assign_joystick(joystick=joystick)

    def assign_joystick(self, robot_ui: Optional[RobotUi] = None, joystick: Optional[Joystick] = None) -> int:
        val = -1
        # if only a joystick is passed to the function and no RobotUi object is provided,
        # get the first RobotUi object that has no joystick assigned to it
        # and assign the passed joystick to the grabbed RobotUi object
        if joystick and robot_ui is None:
            if any(self.robot_ui_list):
                robot_ui_without_joystick = self.get_robot_ui_without_joystick()
                if not robot_ui_without_joystick:
                    val = -1
                val = self.complete_assignment(robot_ui_without_joystick, joystick)
        # if only a RobotUi object is passed to the function and no joystick is provided,
        # get the last unassigned joystick and assign it to the given RobotUi object
        elif robot_ui and joystick is None:
            if not self.unassigned_joysticks:
                val = -1
            else:
                joystick = self.unassigned_joysticks[0]
                val = self.complete_assignment(robot_ui, joystick)
        # assignment completed ?
        self.print_assignment_status(val)

        return val

    def get_robot_ui_without_joystick(self) -> Union[RobotUi, int]:
        for i in range(self.robot_ui_list_len):
            if self.robot_ui_list[i]:
                if self.robot_ui_list[i].joystick_instance_id == -1:
                    return self.robot_ui_list[i]
        return 0

    def complete_assignment(self, robot_ui: RobotUi, joystick: Joystick) -> int:
        # set instance id of joystick in RobotUi object and transfer joystick
        robot_ui_index = robot_ui.client_index
        robot_ui.joystick_instance_id = joystick.information["instance_id"]
        self.transfer_joystick(joystick)
        # write to main and robot terminal
        string = 'Joystick {} was assigned to "TWIPR_{}" successfully!'.format(robot_ui.joystick_instance_id,
                                                                               robot_ui.client_index)
        robot_ui.main_ui_object.write_message_to_terminals(robot_ui.client_index, string, 'G')
        # signal that joystick and robot have come together
        self.rumble(robot_ui.joystick_instance_id, rumble_type='weak')
        return robot_ui_index

    def print_assignment_status(self, robot_ui_index: int) -> None:
        # if assignment was not successful, the robot_ui_index is equal to -1
        if robot_ui_index == -1:
            print("No assignment possible!")
        else:
            robot_ui = self.robot_ui_list[robot_ui_index]
            print("Joystick with instance id {} was assigned to RobotUi object "
                  "with index {} successfully!".format(robot_ui.joystick_instance_id, robot_ui_index))

    def transfer_joystick(self, joystick: Joystick, was_unassigned: bool = True) -> None:
        # joystick transfer: unassigned -> assigned
        if was_unassigned:
            self.unassigned_joysticks.remove(joystick)
            self.assigned_joysticks.append(joystick)
            print("Joystick {}: unassigned -> assigned".format(joystick.information["instance_id"]))
        # joystick transfer: assigned -> unassigned
        else:
            self.assigned_joysticks.remove(joystick)
            self.unassigned_joysticks.append(joystick)
            print("Joystick {}: assigned -> unassigned".format(joystick.information["instance_id"]))

    def joystick_removed(self, event: pygame.event.Event) -> None:
        # unassign joystick from RobotUi object
        joystick = self.deallocate_joystick(event=event)

        # uninitialize joystick so that it's not able to push events to the pygame queue
        self.uninitialize_joystick(joystick)
    
    def robot_removed(self, robot_ui: RobotUi) -> None:
        self.robot_ui_list[robot_ui.client_index] = 0  # has to be removed for successful reassignment
        joystick = self.deallocate_joystick(robot_ui=robot_ui)

        # check for assignment to RobotUi object without joystick
        if joystick:
            self.reassign_joystick(joystick)

    def deallocate_joystick(self, robot_ui: Optional[RobotUi] = None, event: Optional[pygame.event.Event] = None) -> Union[Joystick, int]:
        # robot disconnect
        if robot_ui and event is None:
            if robot_ui.joystick_instance_id == -1:
                return 0
            joystick = self.complete_deallocation(robot_ui, joystick_removed=False)
            return joystick
        # joystick disconnect
        elif event and robot_ui is None:
            if not any(self.robot_ui_list):
                joystick, _ = self.get_joystick_from_instance_id(event.instance_id)
                return joystick
            for i in range(self.robot_ui_list_len):
                if self.robot_ui_list[i]:
                    if self.robot_ui_list[i].joystick_instance_id == event.instance_id:
                        joystick = self.complete_deallocation(self.robot_ui_list[i], joystick_removed=True)
                        return joystick

    def complete_deallocation(self, robot_ui: RobotUi, joystick_removed: bool) -> Joystick:
        iid = robot_ui.joystick_instance_id
        joystick, was_unassigned = self.get_joystick_from_instance_id(iid)
        if not was_unassigned:
            self.transfer_joystick(joystick, was_unassigned=was_unassigned)
        # write to console
        self.print_deallocation_status(robot_ui, iid)
        # write to main terminal
        self.write_deallocation_status_to_main_terminal(robot_ui, joystick_removed=joystick_removed)
        # if joystick was disconnected, write to robot terminal too and reset joystick button
        if joystick_removed:
            self.write_deallocation_status_to_robot_terminal(robot_ui)
            robot_ui.joystick_enable = False
        # signal joystick or robot loss
        self.rumble(iid, rumble_type='strong')
        robot_ui.joystick_instance_id = -1
        return joystick

    def get_joystick_from_instance_id(self, instance_id: int) -> Tuple[Joystick, bool]:
        # check in unassigned joysticks first
        for unassigned_joystick in self.unassigned_joysticks:
            if unassigned_joystick.information["instance_id"] == instance_id:
                return unassigned_joystick, True
        # now check in assigned joysticks
        for assigned_joystick in self.assigned_joysticks:
            if assigned_joystick.information["instance_id"] == instance_id:
                return assigned_joystick, False

    def uninitialize_joystick(self, joystick: Joystick) -> None:
        self.unassigned_joysticks.remove(joystick)
        print("Joystick {} deleted successfully!".format(joystick.information["instance_id"]))

    @staticmethod
    def write_deallocation_status_to_main_terminal(robot_ui: RobotUi, joystick_removed: bool):
        if joystick_removed:
            string = "Joystick {} deactivated!".format(robot_ui.joystick_instance_id)
            robot_ui.main_ui_object.write_message_to_main_terminal(string, 'R')
        string = "Joystick {} was deallocated from 'TWIPR_{}' successfully!".format(robot_ui.joystick_instance_id,
                                                                                    robot_ui.client_index)
        robot_ui.main_ui_object.write_message_to_main_terminal(string, 'R')

    @staticmethod
    def write_deallocation_status_to_robot_terminal(robot_ui: RobotUi):
        string = "Joystick {} deactivated!".format(robot_ui.joystick_instance_id)
        robot_ui.write_message_to_robot_terminal(string, 'R')
        string = "Joystick {} was deallocated from 'TWIPR_{}' successfully!".format(robot_ui.joystick_instance_id,
                                                                                    robot_ui.client_index)
        robot_ui.write_message_to_robot_terminal(string, 'R')

    @staticmethod
    def print_deallocation_status(robot_ui: RobotUi, instance_id: int) -> None:
        print("Joystick with instance id {} was deallocated from RobotUi object "
              "with index {} successfully!".format(instance_id, robot_ui.client_index))

    def rumble(self, instance_id: int, rumble_type: str = 'weak') -> None:
        joystick, _ = self.get_joystick_from_instance_id(instance_id)
        device_index = joystick.information['id']
        self.rumble_handler_thread.request_rumble(device_index, rumble_type=rumble_type)

    def process_joystick_input(self, event: pygame.event.Event) -> Union[None, str]:
        robot_ui, joystick_enable = self.check_joystick_enable(event.instance_id)

        # stop if joystick is not assigned
        if not robot_ui and not joystick_enable:
            return

        # events are only processed if the joystick is enabled for a specific robot, this saves resources
        # but if the axes are not flipped and R2 is triggered correctly the joystick should be enabled
        # this requires a mechanism that circumvents the blocking of event processing for that specific axis
        # (R2 in case axes are not flipped, else L2)
        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 5:  # -> self.mapping['R2']
                if robot_ui and not joystick_enable:
                    joystick_enable = True

        # process event if processing is enabled
        if joystick_enable:
            cmd, write_to_terminal = self.get_cmd(robot_ui, event)
            if cmd:
                self.push_cmd_to_robot_ui(robot_ui, cmd, write_to_terminal)
                return cmd

    def check_joystick_enable(self, instance_id: int) -> Tuple[Union[RobotUi, bool], bool]:
        robot_ui = self.get_robot_ui_from_instance_id(instance_id)
        if not robot_ui:
            return False, False
        else:
            return robot_ui, robot_ui.joystick_enable

    def get_robot_ui_from_instance_id(self, instance_id: int) -> Union[RobotUi, int]:
        # no RobotUi objects available
        if not any(self.robot_ui_list):
            return 0
        # search for a robot_ui with a joystick
        for r_ui in self.robot_ui_list:
            if r_ui:
                if r_ui.joystick_instance_id == instance_id:
                    return r_ui
        # no RobotUi object found with that joystick instance id
        return 0

    def get_cmd(self, robot_ui: RobotUi, event: pygame.event.Event) -> Tuple[str, bool]:
        joystick, _ = self.get_joystick_from_instance_id(event.instance_id)
        cmd, write_to_terminal = joystick.get_cmd(robot_ui, event)
        return cmd, write_to_terminal

    @staticmethod
    def push_cmd_to_robot_ui(robot_ui: RobotUi, cmd: str, write_to_terminal: bool) -> None:
        robot_ui.enter_cmd_into_robot_terminal(cmd, write_to_terminal=write_to_terminal)


class Joystick:
    joystick_handler: JoystickHandler
    joystick: pygame.joystick.Joystick
    information: Dict[str, Union[int, str]]
    mapping: Dict[str, int]
    analog_stick_limit: float
    dead_band: float
    axes_flipped: bool
    output_limits: Dict[str, float]
    velocity_steps: Dict[str, float]
    change_fsm_state: bool

    def __init__(self, joystick_handler: JoystickHandler, joystick: pygame.joystick.Joystick) -> None:
        # access to JoystickHandler object (needed for rumble())
        self.joystick_handler = joystick_handler
        # joystick object from pygame
        self.joystick = joystick
        # get joystick information
        self.information = {'id': self.joystick.get_id(),
                            'instance_id': self.joystick.get_instance_id(),
                            'guid': self.joystick.get_guid(),
                            'power_level': self.joystick.get_power_level(),
                            'name': self.joystick.get_name(),
                            'number_axes': self.joystick.get_numaxes(),
                            'number_balls': self.joystick.get_numballs(),
                            'number_buttons': self.joystick.get_numbuttons(),
                            'number_hats': self.joystick.get_numhats()}
        # mapping for the analog sticks and button
        self.mapping = {}
        # load correct mapping dependent on the name of the controller
        self.load_mapping()
        # for checking analog stick limits
        self.analog_stick_limit = 0.99
        # setting to adjust the sensitivity of the analog sticks
        self.dead_band = 0.15
        # for changing the gas pedal position (mode 0: R3 == gas, mode 1: L3 == gas)
        self.axes_flipped = False
        # limitations for torque, x_dot, psi_dot
        self.output_limits = {"min_torque": -0.79,
                              "max_torque": 0.79,
                              'min_x_dot': -2.0,
                              'max_x_dot': 2.0,
                              'min_psi_dot': -6.28,
                              'max_psi_dot': 6.28}
        # output increments
        self.output_steps = {"torque": 0.2,
                             'x_dot': 0.25,
                             'psi_dot': 0.78}  # PI/4
        # selection which state is to be change with L1 or R1
        self.change_fsm_state = True

    def print_joystick_information(self) -> None:
        print("  JOYSTICK INFORMATION  ".center(100, '='))
        for key, val in self.information.items():
            string = "{}= {}".format(key, val)
            print(string)

    def load_mapping(self) -> None:
        if self.information["name"] == "Xbox One S Controller":
            game_controller_name = "SN30_Pro_Plus"
            self.read_mapping_from_file(game_controller_name)
        elif self.information["name"] == "PS4 Controller":
            game_controller_name = "PS4"
            self.read_mapping_from_file(game_controller_name)
        elif self.information["name"] == "Xbox 360 Controller":
            game_controller_name = "SN30_Pro_Plus"
            self.read_mapping_from_file(game_controller_name)
        else:
            print("Unknown game controller! Failed to load mapping!")

    def read_mapping_from_file(self, game_controller_name: str) -> None:
        path = "Extern/Joystick/Mappings/mapping_{}.json".format(game_controller_name)
        try:
            with open(os.path.join(path), 'r+') as json_file:
                self.mapping = json.load(json_file)
                print("Mapping was read from file successfully!")
        except OSError:
            raise OSError("Failed to read mapping from file!")

    def rumble(self, rumble_type: str = 'weak', limit_reached: bool = False) -> None:
        if limit_reached:
            self.joystick_handler.rumble(self.information['instance_id'], rumble_type='strong')
        else:
            self.joystick_handler.rumble(self.information['instance_id'], rumble_type=rumble_type)

    def get_cmd(self, robot_ui: RobotUi, event: pygame.event.Event) -> Tuple[str, bool]:
        if self.information["name"] == "Xbox One S Controller":
            cmd, write_to_terminal = self.get_cmd_from_sn30_pro_plus(robot_ui, event)
            
            return cmd, write_to_terminal
        elif self.information["name"] == "Xbox 360 Controller":
            cmd, write_to_terminal = self.get_cmd_from_sn30_pro_plus(robot_ui, event)

            return cmd, write_to_terminal
        else:
            if self.information["name"] == "PS4 Controller":
                print("Input processing for this game controller has not been implemented yet!")
            else:
                print("Unknown game controller! Failed to process input!")
                
            return '', False

    def get_cmd_from_sn30_pro_plus(self, robot_ui: RobotUi, event: pygame.event.Event) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        # PROCESS BUTTON PRESS
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == self.mapping['A']:
                cmd, write_to_terminal = self.a_pressed(robot_ui)
            elif event.button == self.mapping['B']:
                cmd, write_to_terminal = self.b_pressed(robot_ui)
            elif event.button == self.mapping['X']:
                cmd, write_to_terminal = self.x_pressed(robot_ui)
            elif event.button == self.mapping['Y']:
                cmd, write_to_terminal = self.y_pressed(robot_ui)
            elif event.button == self.mapping['SELECT']:
                cmd, write_to_terminal = self.select_pressed(robot_ui)
            elif event.button == self.mapping['START']:
                cmd, write_to_terminal = self.start_pressed(robot_ui)
            elif event.button == self.mapping['L1']:
                cmd, write_to_terminal = self.l1_pressed(robot_ui)
            elif event.button == self.mapping['R1']:
                cmd, write_to_terminal = self.r1_pressed(robot_ui)
        # PROCESS BUTTON RELEASE
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == self.mapping['A']:
                cmd, write_to_terminal = self.a_released(robot_ui)
            elif event.button == self.mapping['B']:
                cmd, write_to_terminal = self.b_released(robot_ui)
            elif event.button == self.mapping['X']:
                cmd, write_to_terminal = self.x_released(robot_ui)
            elif event.button == self.mapping['Y']:
                cmd, write_to_terminal = self.y_released(robot_ui)
            elif event.button == self.mapping['SELECT']:
                cmd, write_to_terminal = self.select_released(robot_ui)
            elif event.button == self.mapping['START']:
                cmd, write_to_terminal = self.start_released(robot_ui)
            elif event.button == self.mapping['L1']:
                cmd, write_to_terminal = self.l1_released(robot_ui)
            elif event.button == self.mapping['R1']:
                cmd, write_to_terminal = self.r1_released(robot_ui)
        # PROCESS HAT MOTION
        elif event.type == pygame.JOYHATMOTION:
            if event.hat == self.mapping['HAT1']:
                cmd, write_to_terminal = self.hat1_motion(robot_ui, event.value)
        # PROCESS AXIS MOTION
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == self.mapping['L2']:
                cmd, write_to_terminal = self.l2_motion(robot_ui, event.value)
            elif event.axis == self.mapping['R2']:
                cmd, write_to_terminal = self.r2_motion(robot_ui, event.value)
            elif event.axis == self.mapping['L3_horizontal']:
                if not self.axes_flipped:
                    cmd, write_to_terminal = self.l3_horizontal_motion(robot_ui, event.value)
                else:
                    cmd, write_to_terminal = self.r3_horizontal_motion(robot_ui, event.value)
            elif event.axis == self.mapping['L3_vertical']:
                if not self.axes_flipped:
                    cmd, write_to_terminal = self.l3_vertical_motion(robot_ui, event.value)
                else:
                    cmd, write_to_terminal = self.r3_vertical_motion(robot_ui, event.value)
            elif event.axis == self.mapping['R3_horizontal']:
                if not self.axes_flipped:
                    cmd, write_to_terminal = self.r3_horizontal_motion(robot_ui, event.value)
                else:
                    cmd, write_to_terminal = self.l3_horizontal_motion(robot_ui, event.value)
            elif event.axis == self.mapping['R3_vertical']:
                if not self.axes_flipped:
                    cmd, write_to_terminal = self.r3_vertical_motion(robot_ui, event.value)
                else:
                    cmd, write_to_terminal = self.l3_vertical_motion(robot_ui, event.value)
        else:
            pass

        return cmd, write_to_terminal

    def get_cmd_from_xbox_controller(self, robot_ui: RobotUi, event: pygame.event.Event) -> Tuple[str, bool]:
        pass

    def get_cmd_from_ps_controller(self, robot_ui: RobotUi, event: pygame.event.Event) -> Tuple[str, bool]:
        pass

    # PROCESSING METHODS

    def a_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            self.rumble()
            cmd = "M4"
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                self.rumble('strong')  # NOT IMPLEMENTED
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                self.rumble()
                cmd = "M71 F\"sequence_joystick\""
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                self.rumble()
                cmd = "M71 F\"sequence_joystick\""
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                self.rumble()
                cmd = "M71 F\"sequence_joystick\""

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            self.rumble('strong')  # NOT IMPLEMENTED

        return cmd, write_to_terminal

    def b_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            self.rumble()
            cmd = "G0 E(0,0,0,0,0,0,0,0,0)"
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                self.rumble('strong')  # NOT IMPLEMENTED
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                self.rumble('strong')  # NOT IMPLEMENTED
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                self.rumble('strong')  # NOT IMPLEMENTED
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                self.rumble('strong')  # NOT IMPLEMENTED

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            self.rumble('strong')  # NOT IMPLEMENTED

        return cmd, write_to_terminal

    def x_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            cmd = "M1 S3"  # fsm_state -> ERROR
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            cmd = "M1 S3"  # fsm_state -> ERROR
            self.rumble()

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            cmd = "M1 S0"  # fsm_state -> INITIALIZING
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            cmd = "M1 S3"  # fsm_state -> ERROR
            self.rumble()

        return cmd, write_to_terminal

    def y_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.flip_axes(robot_ui)
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            self.flip_axes(robot_ui)
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            self.flip_axes(robot_ui)
            self.rumble()

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.flip_axes(robot_ui)
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            self.flip_axes(robot_ui)
            self.rumble()

        return cmd, write_to_terminal

    def select_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.toggle_state_selection_flag(robot_ui)
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            self.toggle_state_selection_flag(robot_ui)
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            self.toggle_state_selection_flag(robot_ui)
            self.rumble()

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.toggle_state_selection_flag(robot_ui)
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            self.toggle_state_selection_flag(robot_ui)
            self.rumble()

        return cmd, write_to_terminal

    def start_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            cmd = "M63 F\"joystick\""
            self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            cmd = "M63 F\"joystick\""
            self.rumble()

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            self.rumble('strong')  # NOT IMPLEMENTED

        return cmd, write_to_terminal

    def l1_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            state_selection, new_state, limit_reached = self.decrement_state(robot_ui)
            self.rumble(limit_reached=limit_reached)
            cmd = "M{} S{}".format(state_selection, new_state)
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            state_selection, new_state, limit_reached = self.decrement_state(robot_ui)
            self.rumble(limit_reached=limit_reached)
            cmd = "M{} S{}".format(state_selection, new_state)

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            state_selection, new_state, limit_reached = self.decrement_state(robot_ui)
            self.rumble(limit_reached=limit_reached)
            cmd = "M{} S{}".format(state_selection, new_state)

        return cmd, write_to_terminal

    def r1_pressed(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            state_selection, new_state, limit_reached = self.increment_state(robot_ui)
            self.rumble(limit_reached=limit_reached)
            cmd = "M{} S{}".format(state_selection, new_state)
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            state_selection, new_state, limit_reached = self.increment_state(robot_ui)
            self.rumble(limit_reached=limit_reached)
            cmd = "M{} S{}".format(state_selection, new_state)

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            state_selection, new_state, limit_reached = self.increment_state(robot_ui)
            self.rumble(limit_reached=limit_reached)
            cmd = "M{} S{}".format(state_selection, new_state)

        return cmd, write_to_terminal

    def a_released(self, robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                self.rumble()
                cmd = "M72 F\"sequence_joystick\""
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                self.rumble()
                cmd = "M72 F\"sequence_joystick\""
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                self.rumble()
                cmd = "M72 F\"sequence_joystick\""

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            pass

        return cmd, write_to_terminal

    @staticmethod
    def b_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    @staticmethod
    def x_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    @staticmethod
    def y_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    @staticmethod
    def select_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    @staticmethod
    def start_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    @staticmethod
    def l1_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    @staticmethod
    def r1_released(robot_ui: RobotUi) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True
        return cmd, write_to_terminal

    def hat1_motion(self, robot_ui: RobotUi, hat_value: Tuple[int, int]) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = True

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                self.rumble('strong')  # NOT IMPLEMENTED
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                u_l, u_r, limit_reached = self.interpret_hat_value(robot_ui, hat_value)
                if u_l is None and u_r is None and limit_reached is None:
                    pass
                else:
                    self.rumble(limit_reached=limit_reached)
                    cmd = "G1 U({:.2f},{:.2f})".format(u_l, u_r)
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                u_l, u_r, limit_reached = self.interpret_hat_value(robot_ui, hat_value)
                if u_l is None and u_r is None and limit_reached is None:
                    pass
                else:
                    self.rumble(limit_reached=limit_reached)
                    cmd = "G1 U({:.2f},{:.2f})".format(u_l, u_r)
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                vel_cmd, is_x_dot, limit_reached = self.interpret_hat_value(robot_ui, hat_value)
                if vel_cmd is None and is_x_dot is None and limit_reached is None:
                    pass
                else:
                    self.rumble(limit_reached=limit_reached)
                    if is_x_dot:
                        cmd = "G1 X{:.2f}".format(vel_cmd)
                    else:
                        cmd = "G1 P{:.2f}".format(vel_cmd)

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            self.rumble('strong')  # NOT IMPLEMENTED
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            self.rumble('strong')  # NOT IMPLEMENTED

        return cmd, write_to_terminal

    def l2_motion(self, robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            cmd, status_changed = self.change_logging_status(robot_ui, axis_value)
            if status_changed:
                self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            cmd, status_changed = self.change_logging_status(robot_ui, axis_value)
            if status_changed:
                self.rumble()

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            pass

        return cmd, write_to_terminal

    def r2_motion(self, robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            status_changed = self.enable(robot_ui, axis_value)
            if status_changed:
                self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            status_changed = self.enable(robot_ui, axis_value)
            if status_changed:
                self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:
            status_changed = self.enable(robot_ui, axis_value)
            if status_changed:
                self.rumble()

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            status_changed = self.enable(robot_ui, axis_value)
            if status_changed:
                self.rumble()
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            status_changed = self.enable(robot_ui, axis_value)
            if status_changed:
                self.rumble()

        return cmd, write_to_terminal

    def l3_horizontal_motion(self, robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                psi_dot, limit_reached = self.calc_psi_dot(axis_value)
                if limit_reached:
                    self.rumble(limit_reached=limit_reached)
                cmd = "G1 P{:.2f}".format(psi_dot)

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            pass

        return cmd, write_to_terminal

    def l3_vertical_motion(self, robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                torque, limit_reached = self.calc_torque(axis_value)
                if limit_reached:
                    self.rumble(limit_reached=limit_reached)
                cmd = "G1 U({:.2f},{:.2f})".format(torque, 0.0)
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
                torque, limit_reached = self.calc_torque(axis_value)
                if limit_reached:
                    self.rumble(limit_reached=limit_reached)
                cmd = "G1 U({:.2f},{:.2f})".format(torque, 0.0)
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            pass

        return cmd, write_to_terminal

    @staticmethod
    def r3_horizontal_motion(robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                pass

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            pass

        return cmd, write_to_terminal

    def r3_vertical_motion(self, robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        write_to_terminal = False

        if robot_ui.robot.fsm_state == FSM_STATE.INITIALIZING:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.IDLE:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.ACTIVE:

            if robot_ui.robot.controller.state == CTRL_STATE.OFF:
                pass
            elif robot_ui.robot.controller.state == CTRL_STATE.DIRECT:
                torque, limit_reached = self.calc_torque(axis_value)
                if limit_reached:
                    self.rumble(limit_reached=limit_reached)
                cmd = "G1 U({:.2f},{:.2f})".format(0.0, torque)
            elif robot_ui.robot.controller.state == CTRL_STATE.STATE_FEEDBACK:
                pass
                torque, limit_reached = self.calc_torque(axis_value)
                if limit_reached:
                    self.rumble(limit_reached=limit_reached)
                cmd = "G1 U({:.2f},{:.2f})".format(0.0, torque)
            elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
                x_dot, limit_reached = self.calc_x_dot(axis_value)
                if limit_reached:
                    self.rumble(limit_reached=limit_reached)
                cmd = "G1 X{:.2f}".format(x_dot)

        elif robot_ui.robot.fsm_state == FSM_STATE.ERROR:
            pass
        elif robot_ui.robot.fsm_state == FSM_STATE.CALIBRATING:
            pass

        return cmd, write_to_terminal

    # HELPER METHODS

    def dead_band_correction(self, axis_value: float) -> float:
        if abs(axis_value) <= self.dead_band:
            corrected_axis_value = 0.0
        else:
            corrected_axis_value = self.sign(axis_value) * ((abs(axis_value) - self.dead_band) / (1 - self.dead_band))
        return corrected_axis_value

    @staticmethod
    def sign(x: float) -> int:
        return (1, -1)[x < 0]

    @staticmethod
    def invert_axis(axis_value: float) -> float:
        return axis_value * (-1)

    @staticmethod
    def check_limit_reached(value: float, limit: float) -> bool:
        if abs(value) >= limit:
            limit_reached = True
        else:
            limit_reached = False

        return limit_reached

    def calc_torque(self, axis_value: float) -> Tuple[float, bool]:
        limit_reached = self.check_limit_reached(axis_value, self.analog_stick_limit)
        ax = self.dead_band_correction(axis_value)
        ax = self.invert_axis(ax)
        torque = self.output_limits['max_torque'] * ax

        return torque, limit_reached
    
    def calc_x_dot(self, axis_value: float) -> Tuple[float, bool]:
        limit_reached = self.check_limit_reached(axis_value, self.analog_stick_limit)
        ax = self.dead_band_correction(axis_value)
        ax = self.invert_axis(ax)
        x_dot = self.output_limits['max_x_dot'] * ax

        return x_dot, limit_reached
    
    def calc_psi_dot(self, axis_value: float) -> Tuple[float, bool]:
        limit_reached = self.check_limit_reached(axis_value, self.analog_stick_limit)
        ax = self.dead_band_correction(axis_value)
        ax = self.invert_axis(ax)
        psi_dot = self.output_limits['max_psi_dot'] * ax

        return psi_dot, limit_reached
    
    def flip_axes(self, robot_ui: RobotUi) -> None:
        # swap out L3 with R3
        self.axes_flipped ^= True
        # display info on both terminals
        string = "Joystick {}: Axes flipped successfully!".format(robot_ui.joystick_instance_id)
        robot_ui.main_ui_object.write_message_to_terminals(robot_ui.client_index, string, 'W')
        # acknowledgement
        self.joystick_handler.rumble(robot_ui.joystick_instance_id, rumble_type='weak')

    def toggle_state_selection_flag(self, robot_ui: RobotUi) -> None:
        # change which states you are going to change with L1 or R1 (fsm or ctrl)
        self.change_fsm_state ^= True
        # display info on both terminals
        string = "Joystick {}: change_fsm_state = {}!".format(robot_ui.joystick_instance_id, self.change_fsm_state)
        robot_ui.main_ui_object.write_message_to_terminals(robot_ui.client_index, string, 'W')
        # acknowledgement
        self.joystick_handler.rumble(robot_ui.joystick_instance_id, rumble_type='weak')

    def decrement_state(self, robot_ui: RobotUi) -> Tuple[int, int, bool]:
        if self.change_fsm_state:
            state_selection = 1
            current_state = robot_ui.robot.fsm_state.value
            new_state = current_state - 1
            if new_state == -1:
                limit_reached = True  # signal that lower limit was reached
                new_state += 1
            else:
                limit_reached = False  # acknowledgement
        else:
            state_selection = 2
            current_state = robot_ui.robot.controller.state.value
            new_state = current_state - 1
            if new_state == -1:
                limit_reached = True  # signal that lower limit was reached
                new_state += 1
            else:
                limit_reached = False  # acknowledgement

        return state_selection, new_state, limit_reached

    def increment_state(self, robot_ui: RobotUi) -> Tuple[int, int, bool]:
        if self.change_fsm_state:
            state_selection = 1
            current_state = robot_ui.robot.fsm_state.value
            new_state = current_state + 1
            if new_state == 5:
                limit_reached = True  # signal that upper limit was reached
                new_state -= 1
            else:
                limit_reached = False  # acknowledgement
        else:
            state_selection = 2
            current_state = robot_ui.robot.controller.state.value
            new_state = current_state + 1
            if new_state == 4:
                limit_reached = True  # signal that upper limit was reached
                new_state -= 1
            else:
                limit_reached = False  # acknowledgement

        return state_selection, new_state, limit_reached

    @staticmethod
    def limit_output(output: float, lower_limit: float, upper_limit: float) -> Tuple[float, bool]:
        limit_reached = False
        if output > upper_limit:
            output = upper_limit
            limit_reached = True
        elif output < lower_limit:
            output = lower_limit
            limit_reached = True

        return output, limit_reached

    def change_output_stepwise(self, output: float, output_type: str, increment: bool = True) -> Tuple[float, bool]:
        assert(output_type in self.output_steps.keys())
        if increment:
            output = output + self.output_steps[output_type]
        else:
            output = output - self.output_steps[output_type]
        # limit the output and return
        output, limit_reached = self.limit_output(output, self.output_limits['min_{}'.format(output_type)],
                                                  self.output_limits['max_{}'.format(output_type)])

        return output, limit_reached

    def change_torque_stepwise(self, robot_ui: RobotUi, which: str = 'both', increment: bool = True) -> Tuple[float, 
                                                                                                              float, 
                                                                                                              bool]:
        if which == 'left':
            current_torque_left = robot_ui.robot.controller.external_torque[0]
            current_torque_right = robot_ui.robot.controller.external_torque[1]
            new_torque, limit_reached = self.change_output_stepwise(current_torque_left, 'torque', increment=increment)

            return new_torque, current_torque_right, limit_reached

        elif which == 'right':
            current_torque_left = robot_ui.robot.controller.external_torque[0]
            current_torque_right = robot_ui.robot.controller.external_torque[1]
            new_torque, limit_reached = self.change_output_stepwise(current_torque_right, 'torque', increment=increment)

            return current_torque_left, new_torque, limit_reached

        elif which == 'both':
            current_torque_left = robot_ui.robot.controller.external_torque[0]
            current_torque_right = robot_ui.robot.controller.external_torque[1]
            new_torque_left, limit_reached_left = self.change_output_stepwise(current_torque_left, 
                                                                              'torque', increment=increment)
            new_torque_right, limit_reached_right = self.change_output_stepwise(current_torque_right, 
                                                                                'torque', increment=increment)

            limit_reached = False
            if limit_reached_left or limit_reached_right:
                limit_reached = True

            return new_torque_left, new_torque_right, limit_reached

        elif which == 'inverse':
            current_torque_left = robot_ui.robot.controller.external_torque[0]
            current_torque_right = robot_ui.robot.controller.external_torque[1]
            new_torque_left, limit_reached_left = self.change_output_stepwise(current_torque_left,
                                                                              'torque', increment=(not increment))
            new_torque_right, limit_reached_right = self.change_output_stepwise(current_torque_right,
                                                                                'torque', increment=increment)

            limit_reached = False
            if limit_reached_left or limit_reached_right:
                limit_reached = True

            return new_torque_left, new_torque_right, limit_reached

        else:
            print("Invalid function arguments!")
            return 0.0, 0.0, False

    def change_velocity_stepwise(self, robot_ui: RobotUi, is_x_dot: bool = True, increment: bool = True) -> Tuple[float,
                                                                                                                  bool]:
        if is_x_dot:
            current_velocity = robot_ui.robot.controller.xdot_cmd
            new_velocity, limit_reached = self.change_output_stepwise(current_velocity, 'x_dot', increment=increment)
        else:
            current_velocity = robot_ui.robot.controller.psidot_cmd
            new_velocity, limit_reached = self.change_output_stepwise(current_velocity, 'psi_dot', increment=increment)

        return new_velocity, limit_reached

    def interpret_hat_value(self, robot_ui: RobotUi, hat_value: Tuple[int, int]) -> Union[Tuple[float, float, bool],
                                                                                          Tuple[float, bool, bool],
                                                                                          Tuple[None, None, None]]:
        if robot_ui.robot.controller.state in (CTRL_STATE.DIRECT, CTRL_STATE.STATE_FEEDBACK):
            if hat_value == (-1, 0):  # LEFT
                u_l, u_r, limit_reached = self.change_torque_stepwise(robot_ui, 'inverse', increment=True)
            elif hat_value == (1, 0):  # RIGHT
                u_l, u_r, limit_reached = self.change_torque_stepwise(robot_ui, 'inverse', increment=False)
            elif hat_value == (0, -1):  # DOWN
                u_l, u_r, limit_reached = self.change_torque_stepwise(robot_ui, 'both', increment=False)
            elif hat_value == (0, 1):  # UP
                u_l, u_r, limit_reached = self.change_torque_stepwise(robot_ui, 'both', increment=True)
            else:  # CENTER
                return None, None, None

            return u_l, u_r, limit_reached

        elif robot_ui.robot.controller.state == CTRL_STATE.VELOCITY:
            if hat_value == (-1, 0):  # LEFT
                is_x_dot = False
                vel, limit_reached = self.change_velocity_stepwise(robot_ui, is_x_dot=False, increment=True)
            elif hat_value == (1, 0):  # RIGHT
                is_x_dot = False
                vel, limit_reached = self.change_velocity_stepwise(robot_ui, is_x_dot=False, increment=False)
            elif hat_value == (0, -1):  # DOWN
                is_x_dot = True
                vel, limit_reached = self.change_velocity_stepwise(robot_ui, is_x_dot=True, increment=False)
            elif hat_value == (0, 1):  # UP
                is_x_dot = True
                vel, limit_reached = self.change_velocity_stepwise(robot_ui, is_x_dot=True, increment=True)
            else:  # CENTER
                return None, None, None

            return vel, is_x_dot, limit_reached

    @staticmethod
    def change_logging_status(robot_ui: RobotUi, axis_value: float) -> Tuple[str, bool]:
        cmd = ''
        status_changed = False
        
        if robot_ui.robot.logging.running == 1 and axis_value < 0:
            # adjust logging status in Robot object
            robot_ui.robot.logging.running = 0
            cmd = "M3 E0"
            status_changed = True
        elif robot_ui.robot.logging.running == 0 and axis_value > 0:
            # adjust logging status in Robot object
            robot_ui.robot.logging.running = 1
            cmd = "M3 E1"
            status_changed = True

        return cmd, status_changed

    @staticmethod
    def enable(robot_ui: RobotUi, axis_value: float) -> int:
        if robot_ui.joystick_enable is False and axis_value > -0.8:
            # joystick button pressed routine
            terminal_txt = "Joystick {} activated!".format(robot_ui.joystick_instance_id)
            robot_ui.main_ui_object.write_message_to_terminals(robot_ui.client_index, terminal_txt, "G")
            robot_ui.joystick_enable = True
            return 1
        else:
            return 0


class JoystickTester:
    joystick_count: int
    joystick: pygame.joystick.Joystick
    joystick_information: Dict[str, Union[int, str]]
    mapping_buttons: Dict[str, int]
    mapping_analog_sticks: Dict[str, int]

    def __init__(self) -> None:
        # initialize the pygame.joystick module
        pygame.init()

        # if joysticks are connected, take the first one and initialize a joystick object
        self.joystick_count = pygame.joystick.get_count()
        if not self.joystick_count:
            print("\nJoystick not connected!\n")
            return
        self.joystick = pygame.joystick.Joystick(0)

        # get joystick information
        self.joystick_information = {'id': self.joystick.get_id(),
                                     'instance_id': self.joystick.get_instance_id(),
                                     'guid': self.joystick.get_guid(),
                                     'power_level': self.joystick.get_power_level(),
                                     'name': self.joystick.get_name(),
                                     'number_axes': self.joystick.get_numaxes(),
                                     'number_balls': self.joystick.get_numballs(),
                                     'number_buttons': self.joystick.get_numbuttons(),
                                     'number_hats': self.joystick.get_numhats()}
        for key, val in self.joystick_information.items():
            string = "{}= {}".format(key, val)
            print(string)

        # mappings for the buttons and analog sticks
        self.mapping_buttons = {}
        self.mapping_analog_sticks = {}

    def get_mapping_buttons(self) -> None:
        print("\n\n")
        print("  Button Mapping Configurator  ".center(120, '='))
        print("\nPlease follow the instructions below to configure the correct button mapping of your controller.\n\n"
              ">>> 1. Enter the name of the button you want to press next.\n"
              ">>> 2. Press and hold the button.\n"
              ">>> 3. Repeat the process with all the buttons on your controller.\n\n"
              "Type 'exit' to end the configuration and 'export <filename>' to write the mapping of the buttons to a file\n\n")

        button_count = 0
        while True:
            button_count += 1
            button_name = input("Please type the name of the {}. button you want to press. "
                                "Then press and hold the button. Now press enter."
                                "\n(or type 'exit', 'export <filename>'): ".format(button_count))
            button_name.lower()
            time.sleep(1)
            print(button_name)

            if button_name == "exit":
                print("\nExiting Configurator...\n")
                break
            elif button_name.find("export ") == 0:
                if not self.mapping_buttons:
                    print("\nExport failed! Exiting Configurator...\n")
                    break
                strings = button_name.split()
                self.write_mapping_to_file(strings[1])
                print("\nButton mapping was written to a file successfully!\n")
            # print("\nPlease press the button now.\n")
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pass
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.mapping_buttons[button_name] = event.button
                    print("You have successfully added button {} "
                          "(controller button = {}).\n\n".format(event.button,
                                                                 self.mapping_buttons[button_name]))

    def write_mapping_to_file(self, filename: str) -> None:
        file = filename + ".json"
        with open(file, 'w') as json_file:
            json.dump(self.mapping_buttons, json_file)


# live demo, just connect your game controller, and start doing stuff
def live_demo() -> None:
    pygame.init()

    joysticks: List[pygame.joystick.Joystick] = []
    joystick_index: int = 0
    dead_band: float = 0.15

    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                strong_rumble()
                print("BUTTON {} -> DOWN [{}]\n".format(event.button, event.instance_id))
            elif event.type == pygame.JOYBUTTONUP:
                weak_rumble()
                print("BUTTON {} -> UP [{}]\n".format(event.button, event.instance_id))
            elif event.type == pygame.JOYAXISMOTION:
                if abs(event.value) > dead_band:
                    print("AXIS {} -> VALUE {:.2f} [{}]\n".format(event.axis, event.value, event.instance_id))
            elif event.type == pygame.JOYHATMOTION:
                print("HAT {} -> VALUE {} [{}]\n".format(event.hat, event.value, event.instance_id))
            elif event.type == pygame.JOYBALLMOTION:
                print("BALL {} -> VALUE {} [{}]\n".format(event.ball, event.rel, event.instance_id))
            elif event.type == pygame.JOYDEVICEADDED:
                print("ADDED JOYSTICK -> {}\n".format(event.device_index))
                joysticks.append(pygame.joystick.Joystick(0))
                print(joysticks[0].get_name())
                print("joystick_index={}; id={}; instance_id={}".format(joystick_index,
                                                                        joysticks[joystick_index].get_id(),
                                                                        joysticks[joystick_index].get_instance_id()))
                joystick_index += 1
                weak_rumble()
            elif event.type == pygame.JOYDEVICEREMOVED:
                print("JOYSTICK REMOVED -> {}\n".format(event.instance_id))
                for joystick in joysticks:
                    if joystick.get_instance_id() == event.instance_id:
                        del joystick


if __name__ == "__main__":
    # joystick_tester = JoystickTester()
    # joystick_tester.get_mapping_buttons()

    live_demo()
