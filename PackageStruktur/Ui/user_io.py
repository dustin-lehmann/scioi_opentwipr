from PyQt5.QtCore import QThread
from Ui.Interfaces.terminal_interface import TerminalInterface
from Ui.Interfaces.file_exectuion_interface import FileExecutionInterface
from Communication import host_server


class UserIO:
    """
    base-Class used to create an object which is handling input/ output:

    creates the user interface which happens to be a terminal for now and provides the add_thread
    function that is used to add new QThreads to the main thread
    """

    def __init__(self):
        self.user_interface = None
        # select the user interface
        # self.user_interface = TerminalInterface()
        # self.user_interface = FileExecutionInterface()
        self.host_server = host_server.host
        self.add_host_server_thread(self.host_server)
        self.host_server.start_host_server()
        self.thread = None

    def add_host_server_thread(self, host_server: host_server.HostServer):
        """
        -add a HostServer-Instance as a thread to the UserIo-Instance
        - start a new QThread and move HostServer-instance
        :param host_server: already existing host-server that is moved to the newly created thread
        :return: nothing
        """

        # create new QThread
        self.thread = QThread()
        # move the host_server to the new thread
        host_server.moveToThread(self.thread)

        # connect Signals:

        # Basic Signals (always do the same not dependent on the used interface):
        self.thread.started.connect(host_server.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.connect_signals_of_ui()

        # Signals to call specific functions depending on which interface is currently used (Terminal, full GUI, ...):

    def connect_signals_of_ui(self):

        if self.user_interface is not None:
            # connect Signals from interface to host server, because otherwise it does not work -> TODO?
            self.user_interface.send_byte_message_signal.connect(self.host_server.send_message)
            self.user_interface.user_gcode_input_signal.connect(self.host_server.process_user_input_gcode)

            # Signals from Host Server to Client
            self.host_server.new_client_accepted_signal.connect(self.user_interface)

            # Signals from host_server to interface
            try:
                self.host_server.new_client_accepted_signal.connect(self.user_interface.new_client_accepted)
            except AttributeError:
                pass




