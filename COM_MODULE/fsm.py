from enum import Enum
from global_objects import *
from Communication.messages import *


class FSM:
    state: FSM_STATE

    def __init__(self):
        self.state = FSM_STATE.INITIALIZING

    def update(self):
        # Execute a function depending on the current state
        if self.state == FSM_STATE.INITIALIZING:
            self.state_initializing()
        elif self.state == FSM_STATE.IDLE:
            self.state_idle()
        elif self.state == FSM_STATE.ACTIVE:
            self.state_active()
        elif self.state == FSM_STATE.CALIBRATING:
            self.state_calibrating()
        elif self.state == FSM_STATE.ERROR:
            self.state_error()

        # Increment the state counter
        global_values["tick"] = global_values["tick"] + 1

    def state_initializing(self):
        pass
        # wait for the server socket to connect
        #while server.state is not SocketState.CONNECTED:
        #    pass

        #self.state = robot.ll_fsm_state

        # Read the configuration files
        # TODO

        # Init the Estimator
        # TODO

    def state_idle(self):
        # Check for requested state transitions
        if global_values["flag_fsm_state_change"] is not -1:
            msg = MSG_LL_IN_FSM(global_values["tick"], global_values["flag_fsm_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_fsm_state_change"] = -1

        if global_values["flag_ctrl_state_change"] is not -1:
            msg = MSG_LL_IN_CTRL_STATE(global_values["tick"], global_values["flag_ctrl_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_ctrl_state_change"] = -1

        self.state = robot.ll_fsm_state

    def state_active(self):
        # Check for requested state transitions
        if global_values["flag_fsm_state_change"] is not -1:
            msg = MSG_LL_IN_FSM(global_values["tick"], global_values["flag_fsm_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_fsm_state_change"] = -1

        if global_values["flag_ctrl_state_change"] is not -1:
            msg = MSG_LL_IN_CTRL_STATE(global_values["tick"], global_values["flag_ctrl_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_ctrl_state_change"] = -1

        self.state = robot.ll_fsm_state

    def state_error(self):
        # Check for requested state transitions
        if global_values["flag_fsm_state_change"] is not -1:
            msg = MSG_LL_IN_FSM(global_values["tick"], global_values["flag_fsm_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_fsm_state_change"] = -1

        if global_values["flag_ctrl_state_change"] is not -1:
            msg = MSG_LL_IN_CTRL_STATE(global_values["tick"], global_values["flag_ctrl_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_ctrl_state_change"] = -1

        self.state = robot.ll_fsm_state

    def state_calibrating(self):
        # Check for requested state transitions
        if global_values["flag_fsm_state_change"] is not -1:
            msg = MSG_LL_IN_FSM(global_values["tick"], global_values["flag_fsm_state_change"])
            if not send_msg_to_ll(msg):
                msg = MSG_HOST_IN_ERROR(global_values["tick"], ERROR_LL_NOT_CONNECTED, "Failed to send message to LL!")
                if not send_msg_to_host(msg):
                    print("Failed to send message to HOST!")
            global_values["flag_fsm_state_change"] = -1

        self.state = robot.ll_fsm_state

# =========================================== DUSTIN ====================================================================
# class FSM:
#     state: FSM_STATE
#
#     def __init__(self):
#         self.state = FSM_STATE.INITIALIZING
#         self.c_prog = 0
#         self.flag_fsm_change = -1
#
#     def update(self):
#         # Check for messages
#         # msg_hndlr.update()
#
#         if self.state == FSM_STATE.INITIALIZING:
#             self.state_initializing()
#         elif self.state == FSM_STATE.IDLE:
#             self.state_idle()
#         elif self.state == FSM_STATE.ACTIVE:
#             self.state_active()
#         elif self.state == FSM_STATE.CALIBRATING:
#             self.state_calibrating()
#         elif self.state == FSM_STATE.ERROR:
#             self.state_error()
#
#     def state_initializing(self):
#         global exit_main
#         print("HL: Start init!")
#         # Start communication with the Host
#
#         # Start Communication with the LL Side
#         msg = msg_hndlr.wait_for_message(ID_MSG_LL_OUT_GENERAL, 10000)
#         if msg == -1:
#             self.state = FSM_STATE.ERROR
#             print("ERROR: Low-Level side not responding")
#             exit_main = True
#             return
#         else:
#             msg = MSG_LL_IN_DEBUG(0, 1, 2, 3, 4)
#             server.send_msg(msg)
#         print("Low-level side responding!")
#
#         # Wait for the LL Side to finish configuration
#         msg = MSG_LL_OUT_GENERAL(msg_hndlr.wait_for_message(ID_MSG_LL_OUT_GENERAL, 10000, execute=True))
#
#         if msg.data.fsm_state == LL_FSM_STATE.IDLE:
#             print("LL successfully initialized")
#         elif msg.data.fsm_state == LL_FSM_STATE.ERROR:
#             print("Error in LL initialization")
#             self.state = FSM_STATE.ERROR
#             return
#
#         # Check for configuration files
#
#         # Upload the configuration. Read configuration.g
#
#         # initialize the position estimator
#
#         self.state = FSM_STATE.IDLE
#
#     def state_idle(self):
#         pass
#
#     def state_active(self):
#         # sensor data validity check
#         # TODO
#
#         # particle filter
#         hl.position_state, hl.optical_data_available = position_estimator.update(ll.sensor_data.imu.acc,
#                                                                                  ll.sensor_data.imu.gyr,
#                                                                                  ll.sensor_data.encoder_right.omega,
#                                                                                  ll.sensor_data.encoder_left.omega,
#                                                                                  ll.dynamic_state[2], mocap_data.x,
#                                                                                  mocap_data.y)
#
#         # Log data
#
#         # Send messages
#
#         # To Host
#
#         # General
#         # Dynamic state
#         # Measurements
#
#         # To LL
#         # General
#         # Controller inputs
#
#     def state_calibrating(self):
#         pass
#
#     def state_error(self):
#         pass
