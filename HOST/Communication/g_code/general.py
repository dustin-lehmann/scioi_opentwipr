# General
import crc8
from ctypes import *
from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, Any

# My Imports
from params import *


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


def check_header(header):
    if not (header[0] == HEADER_0 and header[1] == HEADER_1):
        print("Failed to read header!")
        return 0
    return 1


def get_msg_len(header):
    msb = header[2] << 8  # shift two hex points to the left
    msg_len = msb + header[3]
    rest_len = msg_len - HEADER_SIZE
    return msg_len, rest_len


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

    # print(buffer.hex())

    return buffer
