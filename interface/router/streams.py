from asyncio import streams
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import threading
import struct
import pickle
import threading
from collections import deque

from base.singleton import Singleton
from interface.socket.server import Socket


router = APIRouter(prefix="/streams", tags=["streams"])


class StreamsDB(Singleton, dict):
    def new_stream(self, key):
        self[key] = deque()
        self[key].append(b"")

    def append_frame(self, key, frame):
        self[key].append(frame)
        if len(self[key]) > 300:
            self[key].popleft()

    def get_a_frame_for_stream(self, key):
        if key in self:
            return self[key][-1]
        else:
            return b""


streams_db = StreamsDB()
thread_count = 0


# connection 하나 당 thread 하나
class ConnectionWithThread(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.client_socket = connection
        self.buffer = b""
        self.len_size = struct.calcsize("<L")

    def run(self):
        global thread_count
        while True:
            while len(self.buffer) < self.len_size:
                recved = self.client_socket.recv(4096)
                if not recved:
                    self.client_socket.close()
                    thread_count -= 1
                    print("thread_count = " + str(thread_count))
                    return
                self.buffer += recved

            packed_bin_size = self.buffer[: self.len_size]
            self.buffer = self.buffer[self.len_size :]

            bin_size = struct.unpack("<L", packed_bin_size)[0]

            while len(self.buffer) < bin_size:
                recved = self.client_socket.recv(4096)
                self.buffer += recved

            bin = self.buffer[:bin_size]
            self.buffer = self.buffer[bin_size:]

            car_idBin = bin[:32]
            jpgBin = bin[32:]

            car_id = car_idBin.decode("utf-8")
            jpgImg = pickle.loads(jpgBin)

            if not car_id in streams_db:
                streams_db.new_stream(car_id)

            streams_db.append_frame(car_id, jpgImg.tobytes())


# 클라이언트가 보내는 데이터를 수신함
class ReceiveCapFromClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.socket = Socket("0.0.0.0", 9999)

    def run(self):
        global thread_count
        while True:
            try:
                client_socket, client_address = self.socket.accept()
                C = ConnectionWithThread(client_socket)
                C.start()
                thread_count += 1
                print("thread_count = " + str(thread_count))

            except:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="client connection failed",
                )


@router.on_event("startup")
async def router_startup_event():
    f = ReceiveCapFromClient()
    f.start()


def get_camera_stream(car_id):
    while True:
        yield (
            b"--PNPframe\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + bytearray(streams_db.get_a_frame_for_stream(car_id))
            + b"\r\n"
        )


# car_id = e208d83305274b1daa97e4465cb57c8b
@router.get("/{car_id}")
async def stream(car_id: str):
    return StreamingResponse(
        get_camera_stream(car_id),
        media_type="multipart/x-mixed-replace; boundary=PNPframe",
    )
