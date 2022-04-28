from PyQt5.QtCore import QThread
from Ui.Interfaces.terminal_interface import TerminalInterface


class UserIO:
    """
    base-Class used to create an object which is handling input/ output:

    creates the user interface which happens to be a terminal for now and provides the add_thread
    function that is used to add new QThreads to the main thread
    """

    def __init__(self):

        # select terminal as user interface
        self.user_interface = TerminalInterface()
        self.host_server = None
        self.thread = None

    def add_host_server_thread(self, host_server):
        """
        -add a HostServer-Instance as a thread to the UserIo-Instance
        - start a new QThread and move HostServer-instance
        :param host_server: already existing host-server that is moved to the newly created thread
        :return: nothing
        """

        self.host_server = host_server

        # connect Signals from interface to host server, because otherwise it does not work -> TODO?
        self.user_interface.user_gcode_input_signal.connect(self.host_server.process_user_input_gcode)

        # create new QThread
        self.thread = QThread()
        # move the host_server to the new thread
        host_server.moveToThread(self.thread)

        # connect Signals:

        # Basic Signals (always do the same not dependent on the used interface):
        self.thread.started.connect(self.host_server.run)
        self.host_server.finished.connect(self.thread.quit)
        self.host_server.finished.connect(self.host_server.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # Signals to call specific functions depending on which interface is currently used (Terminal, full GUI, ...):

        # Signals from host_server to interface
        self.host_server.new_connection_signal.connect(self.user_interface.new_connection)

        # Signals from interface to host Server

    def host_server_ended(self):
        """
        if signal gets emitted that the host server finished execution print to console
        :return: nothing
        """
        print("host_server execution ended")
