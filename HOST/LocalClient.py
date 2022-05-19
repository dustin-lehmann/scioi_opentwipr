import socket
import time
from ctypes import *
import sys
import crc8
from threading import Thread


class MSG_Structure(Structure):
    _pack_ = 1
    _fields_ = [("tick", c_uint32), ("string", c_char * 40)]


class SendThread(Thread):
    def __init__(self):
        super().__init__()
        self.count = 0
    
    def run(self):
        while True:
            # sleep
            # print("Sleeping for 0.02 seconds!\n")
            time.sleep(30)
            try:
                header_bytes = b'\xaa\xbb\x6B'
                msg = MSG_Structure()
                msg.tick = self.count
                msg.string = "YOOOSOFAOAOf".encode()
                msg_bytes = bytes(msg)
                raw_bytes = header_bytes + msg_bytes

                # add crc8 byte
                crc_object = crc8.crc8()
                crc_object.update(raw_bytes)
                crc_byte = crc_object.digest()
                complete_msg = raw_bytes + crc_byte
                # print("The CRC8 byte", crc_byte, "has been added to the payload!\nMessage:", msg)
                # send message
                client.sendall(complete_msg)
                print("send message")
                # print("... 5 seconds over! Sending message!\n")
                # increment
                self.count += 1
            except socket.error or KeyboardInterrupt as e:
                print(e)
                print("\nClosing client socket in 5 seconds!\n")
                time.sleep(5)
                client.close()
                print("Client socket has been closed! Exiting ...\n")
                sys.exit(1)


class RecvThread(Thread):
    def __init__(self):
        super().__init__()
        self.count = 0

    def run(self):
        while True:
            try:
                msg = client.recv(1024)
                print(msg)
                # print("Client received following message:\n", msg)
            except socket.error or KeyboardInterrupt as e:
                print(e)
                print("\nClosing client socket in 5 seconds!\n")
                time.sleep(5)
                client.close()
                print("Client socket has been closed! Exiting ...\n")
                sys.exit(1)


buffer_size = 103

client = socket.socket()
# server_address = ('127.0.0.1', 6666)
# server_address = ('192.168.8.60', 6666)
server_address = ('127.0.0.1', 6666)
client.connect(server_address)
print("Connected to", server_address, "!\n")

client_send_thread = SendThread()
client_send_thread.start()

client_recv_thread = RecvThread()
client_recv_thread.start()

