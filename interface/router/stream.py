from typing import Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import threading
import struct
import pickle
import threading
from collections import defaultdict, deque

import pydantic

from interface.socket.server import Reader, Socket

router = APIRouter(prefix="/stream", tags=["stream"])



stream_db = defaultdict(lambda: deque(b"")) #여러개에 대해서 수신 가능하도록 변경
DEFAULT_CAR_ID = "e208d83305274b1daa97e4465cb57c8b"

# 클라이언트에게 들어오는 데이터 포맷
class Income(pydantic.BaseModel):
    car_id : str
    jpgImg : list

# 클라이언트가 보내는 데이터를 수신함
# 멀티스레드 적용
class ReceiveCapFromClient(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
            try:
                with self.socket.connect() as client_socket:
                    reader = Reader(client_socket) 
                    while True:
                        bin = reader.read() # read하는 로직이 길어서 Reader로 뺌
                        income = Income.parse_raw(pickle.loads(bin))
                        stream_db[income.car_id].append(bytes(income.jpgImg)) 
                        if len(stream_db[income.car_id]) > 300:
                            stream_db[income.car_id].popleft()

            except:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="server is not watching",
                )


@router.on_event("startup")
async def router_startup_event():
    socket = Socket("0.0.0.0", 9999) # socket 서버라서 아마 쓰레드 여러개에 대해서 소켓 하나만 있으면 될거 같다는 의견
    f = ReceiveCapFromClient(socket) 
    f.start()


def get_camera_stream():
    while True:
        yield (
            b"--PNPframe\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(stream_db[DEFAULT_CAR_ID][-1]) + b"\r\n"
        )


@router.get("/")
async def stream():
    return StreamingResponse(
        get_camera_stream(), media_type="multipart/x-mixed-replace; boundary=PNPframe"
    )
