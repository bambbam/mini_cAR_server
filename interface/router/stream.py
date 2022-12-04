from typing import Any
from fastapi import APIRouter, Depends, WebSocket
import threading
import struct
import pickle
from enum import Enum
from pydantic import BaseModel
from collections import defaultdict, deque
from infrastructure.repository.base import get_db
from infrastructure.repository.model import User

from sqlalchemy.orm import Session
import asyncio
import asyncio_dgram
import uvloop


router = APIRouter(prefix="/stream", tags=["stream"])

stream_db = defaultdict(lambda: deque(b""))  # 여러개에 대해서 수신 가능하도록 변경
DEFAULT_CAR_ID = "e208d83305274b1daa97e4465cb57c8b"


async def async_server():
    buffer = b""
    len_size = struct.calcsize("<L")

    stream = await asyncio_dgram.bind(("0.0.0.0", 9999))

    while True:
        # iter 마다 하나의 datagram 수신
        recved, remote_addr = await stream.recv()

        # 받은 datagram이 car_id이면 패스
        if len(recved) == 32:
            try:
                car_id = recved.decode("utf-8")
            except:
                print("udp issue: car_id")
                pass
            continue
        
        # 받은 datagram이 jpgImg fragment이면 buffer에 저장
        buffer += recved[1:]

        try:
            num_of_fragments = struct.unpack("B", recved[0:1])[0]
        except:
            print("udp issue: num_of_fragments")
            pass

        # 받은 datagram이 마지막 fragment이면 그동안 buffer에 모은 bytes를 이미지로 바꾸고 buffer 비움
        if num_of_fragments == 1:
            try:
                jpgImg = pickle.loads(buffer)
            except:
                print("udp issue: jpgImg")
                pass
            stream_db[car_id].append(bytes(jpgImg))
            while len(stream_db[car_id]) > 300:
                stream_db[car_id].popleft()
            buffer=b""


def start_async_server():
    #use asyncio coroutine
    #loop = asyncio.new_event_loop()

    #use uvloop libuv
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(async_server())


@router.on_event("startup")
async def router_startup_event():
    t = threading.Thread(target=start_async_server)
    t.start()


def get_camera_stream(car_id):
    while True:
        yield (
            b"--PNPframe\r\n"
            + b"Content-Type: image/jpeg\r\n\r\n"
            + bytearray(stream_db[car_id][-1])
            + b"\r\n"
        )

@router.websocket("/{user_id}/ws")
async def stream_ws(websocket: WebSocket, user_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    #await websocket.send_text("connected")
    user = db.query(User).filter(User.email == user_id).first()
    print(user.car_id)
    while True:
        await websocket.send_bytes(bytearray(stream_db[user.car_id][-1]))
        await asyncio.sleep(1 / 30)


class CameraControl(Enum):
    getphoto = 0
    videostart = 1
    videostop = 2

class cameracontrol(BaseModel):
    dir : CameraControl

@router.post("/")
async def camera_control(ctrl:cameracontrol):
    if ctrl.dir == CameraControl.getphoto:
        ## TODO
        print("0")
    elif ctrl.dir == CameraControl.videostart:
        ## TODO
        print("1")
    elif ctrl.dir == CameraControl.videostop:
        ## TODO
        print("2")