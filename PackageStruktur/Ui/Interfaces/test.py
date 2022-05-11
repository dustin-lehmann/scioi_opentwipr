"""
Test file -> delete later
"""

import cobs.cobs as cobs
from datetime import datetime
import queue

from Communication import core_messages


def bytes_to_string(data, pos=False):
    """
    convert bytes to string
    :param pos: If true print out the Byte number after each byte -> useful for debugging
    :return: formatted string
    """
    if pos:
        return " ".join("0x{:02X}({:d})".format(b, i) for (i, b) in enumerate(data))
    else:
        return " ".join("0x{:02X}".format(b) for b in data)


def chop_bytes(hex_string: str, delimiter=0x00):
    """
    chop the by cobs encoded bytestrings into separate messages return, bytearray
    :param hex_string: bytestring that is supposed to be chopped int separate messages
    :return: bytearray, that consists of separate messages
    """
    chopped_msgs = {}
    # start position of each byte
    start = 0
    # index used to navigate in chopped messages
    index = 0

    for i in range(len(hex_string)):
        # check if one byte is 0
        # if bytestring[i] == 0x00 or 'b\x00':
        if hex_string[i] == delimiter:
            # save each byte in array
            chopped_msgs[index] = hex_string[start: i - 1]

            start = i + 1
            index += 1

    return chopped_msgs


myMessage = core_messages.SetLEDMessage(2, 5)

myTransMsg = core_messages.translate_msg_tx(myMessage)

myTransMsg = cobs.encode(myTransMsg)

myTransMsg = myTransMsg.__add__(b'\x00')

myTransMsg = bytes_to_string(myTransMsg)

hexstring = myTransMsg+ ' ' + myTransMsg + ' ' + myTransMsg

byte_array = chop_bytes(hexstring)

print("ende")
