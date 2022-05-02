from Communication.communication import *
from params import *
from estimation.positionestimation import *
from estimation.mocap import *
from robot import *
from get_host_ip import GetHostIP

from ctypes import Structure
import crc8

client_incoming_queue = Queue()
client_outgoing_queue = Queue()
server_incoming_queue = Queue()
server_outgoing_queue = Queue()


#client = Socket("Client", HOST_ADDRESS, HOST_PORT)
client = Socket("Client")

position_estimator = PositionEstimator(FSM_LOOP_TIME / 1000, IMU_X_POS, IMU_Y_POS, IMU_Z_POS, GRAVITY,
                                       RADIUS_RIGHT_WHEEL, RADIUS_LEFT_WHEEL, WHEELBASE)

robot = Robot()
mocap = Mocap()


class Message:
    id: int
    len: int
    raw_data: bytes
    crc8: int

    def __init__(self):
        self.len = -1
        self.id = -1
        self.raw_data = bytearray(0)
        self.crc8 = -1

    def handler(self):
        pass


def crc_check(msg: bytes):
    # create a new CRC8 object
    crc_object = crc8.crc8()
    crc_object.update(msg)
    crc_byte = crc_object.digest()
    # and check the received message
    if crc_byte == b'\x00':
        return 1
    else:
        return 0


def msg_parser(bytes_received):
    msg = Message()
    msg.len, _ = get_msg_len(bytes_received[:5])
    msg.id = bytes_received[4]
    msg.raw_data = bytes_received[5:-1]
    msg.crc8 = bytes_received[-1]

    return msg


def crc_generate(payload):
    # create a new CRC8 object
    crc_object = crc8.crc8()
    crc_object.update(payload)
    crc_byte = crc_object.digest()
    crc_byte = int.from_bytes(crc_byte, "big")
    return crc_byte


def msg_builder(msg: Message):
    payload_size = len(msg.raw_data)
    msg_length = HEADER_SIZE + payload_size + TAIL_SIZE
    buffer = bytearray(msg_length)

    buffer[0] = HEADER_0
    buffer[1] = HEADER_1
    buffer[2] = msg_length.to_bytes(2, 'big')[0]
    buffer[3] = msg_length.to_bytes(2, 'big')[1]
    buffer[4] = msg.id
    buffer[5:5 + payload_size] = msg.raw_data
    buffer[-1] = crc_generate(buffer[:-1])

    return buffer


def send_msg_to_host(msg):
    if client.state == SocketState.CONNECTED:
        client_outgoing_queue.put_nowait(msg_builder(msg))
        return 1
    else:
        return 0


def send_msg_to_ll(msg):
    if server.state == SocketState.CONNECTED:
        server_outgoing_queue.put_nowait(msg_builder(msg))
        return 1
    else:
        return 0


global_values = {"flag_fsm_state_change": -1, "flag_ctrl_state_change": -1, "tick": 0}
