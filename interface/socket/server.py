import socket
import struct

from base.singleton import Singleton


class Socket(Singleton):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()

    def connect(self):
        return Connection(self.socket)

    def close(self):
        self.socket.close()


class Connection:
    def __init__(self, socket):
        self.socket = socket

    def __enter__(self):
        self.connection, self.address = self.socket.accept()
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()

class Reader:
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.buffer = b""
        self.len_size = struct.calcsize("<L")

    def read(self):
        while len(self.buffer) < self.len_size:
            recved = self.client_socket.recv(4096)
            self.buffer += recved

        packed_bin_size = self.buffer[: self.len_size]
        self.buffer = self.buffer[self.len_size :]

        bin_size = struct.unpack("<L", packed_bin_size)[0]

        while len(self.buffer) < bin_size:
            recved = self.client_socket.recv(4096)
            self.buffer += recved

        bin = self.buffer[:bin_size]
        self.buffer = self.buffer[bin_size:]
        return bin
