import socket

class GetHostIP:

    def gethostip(self):
        """
        receive host-ip via UDP
        :return: ip-Address of host to establish connection
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("", 37020))
        data, addr = client.recvfrom(1024)

        #decode received data to string
        data =(data.decode('utf-8'))

        #set host address to received data
        self.host_address = data
        print("received Host-Ip: %s"%data)
        return self.host_address


if __name__ == "__main__":
    Host = GetHostIP()
    ip = Host.host_address
    print(ip)

