class RobotUi:
    """
    RobotUi is the user interface class that is responsible for interaction with the robots.
    The robot user interface is located in the lower half of the screen and it is created for
    every connected TWIPR.
    """

    joystick_instance_id: int
    joystick_enable: bool

    def __init__(self, main_ui_object, client_index):
        # pass main ui object and index of client
        self.main_ui_object = main_ui_object
        self.client_index = client_index
        self.client_name = "TWIPR_" + str(self.client_index)

        # settings for detecting TWIPR death
        self.check_heartbeat_interval = int(10 / 0.1)  # check every 10 seconds
        self.check_heartbeat_counter = 0
        self.check_heartbeat_flag = 0