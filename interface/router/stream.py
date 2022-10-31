from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import threading
import struct
import pickle
import threading
from collections import deque

from interface.socket.server import Socket

router = APIRouter(prefix="/stream", tags=["stream"])

stream_db = deque()
stream_db.append(b"")

# 클라이언트가 보내는 데이터를 수신함
# 멀티스레드 적용
class ReceiveCapFromClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.socket = Socket("0.0.0.0", 9999)
        self.buffer = b""
        self.len_size = struct.calcsize("<L")

    def run(self):
        while True:
            try:
                with self.socket.connect() as client_socket:
                    while True:
                        while len(self.buffer) < self.len_size:
                            recved = client_socket.recv(4096)
                            self.buffer += recved

                        packed_bin_size = self.buffer[: self.len_size]
                        self.buffer = self.buffer[self.len_size :]

                        bin_size = struct.unpack("<L", packed_bin_size)[0]

                        while len(self.buffer) < bin_size:
                            recved = client_socket.recv(4096)
                            self.buffer += recved

                        bin = self.buffer[:bin_size]
                        self.buffer = self.buffer[bin_size:]

                        car_idBin = bin[:32]
                        jpgBin = bin[32:]

                        car_id = car_idBin.decode("utf-8")
                        jpgImg = pickle.loads(jpgBin)

                        stream_db.append(jpgImg.tobytes())
                        if len(stream_db) > 300:
                            stream_db.popleft()

            except:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="server is not watching",
                )


@router.on_event("startup")
async def router_startup_event():
    f = ReceiveCapFromClient()
    f.start()


def get_camera_stream():
    while True:
        yield (
            b"--PNPframe\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(stream_db[-1]) + b"\r\n"
        )


@router.get("/")
async def stream():
    return StreamingResponse(
        get_camera_stream(), media_type="multipart/x-mixed-replace; boundary=PNPframe"
    )
