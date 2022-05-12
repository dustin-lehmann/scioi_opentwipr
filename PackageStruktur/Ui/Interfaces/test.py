"""
Test file -> delete later
"""


def bytes_to_string(data, pos=False):
    """
    convert bytes to string
    :param data:
    :param pos: If true print out the Byte number after each byte -> useful for debugging
    :return: formatted string
    """
    if pos:
        return " ".join("0x{:02X}({:d})".format(b, i) for (i, b) in enumerate(data))
    else:
        return " ".join("0x{:02X}".format(b) for b in data)


def chop_bytes(bytestring, delimiter=0x00):
    """
    chop the by cobs encoded bytestrings into separate messages return, bytearray
    :param bytestring: bytestring that is supposed to be chopped int separate messages
    :return: bytearray, that consists of separate messages
    """
    #empty list to append the messages later on
    chopped_bytes = []
    # # start position of each byte
    start_byte = 0



    data_list = list(bytestring)
    for x in range(len(data_list)):
        if data_list[x] == delimiter:
            chopped_bytes.append(data_list[start_byte:(x-1)])
            start_byte = x+1

    return chopped_bytes

    # return chopped_msgs


list1[1,2,3,4,5]






print("ende")
