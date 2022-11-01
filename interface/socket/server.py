import socket

from base.singleton import Singleton


class Socket(Singleton):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()

    def accept(self):
        connection, address = self.socket.accept()
        return connection, address

    def close(self):
        self.socket.close()
