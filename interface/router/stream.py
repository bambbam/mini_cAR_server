from typing import Any
from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import StreamingResponse
import threading
import struct
import pickle
import threading
from collections import defaultdict, deque
from interface.router.car import CarCache
from infrastructure.repository.base import get_db
from infrastructure.repository.model import User

from sqlalchemy.orm import Session
import asyncio


router = APIRouter(prefix="/stream", tags=["stream"])

stream_db = defaultdict(lambda: deque(b""))  # 여러개에 대해서 수신 가능하도록 변경
DEFAULT_CAR_ID = "e208d83305274b1daa97e4465cb57c8b"


class Reader:
    def __init__(self, reader):
        self.reader = reader
        self.buffer = b""
        self.len_size = struct.calcsize("<L")

    async def read(self):
        while len(self.buffer) < self.len_size:
            recved = await self.reader.read(4096)
            if len(recved) == 0:
                return None
            self.buffer += recved

        packed_bin_size = self.buffer[: self.len_size]
        self.buffer = self.buffer[self.len_size :]

        bin_size = struct.unpack("<L", packed_bin_size)[0]

        while len(self.buffer) < bin_size:
            recved = await self.reader.read(4096)
            if len(recved) == 0:
                return None
            self.buffer += recved

        bin = self.buffer[:bin_size]
        self.buffer = self.buffer[bin_size:]
        return bin


# 클라이언트가 보내는 데이터를 수신함
# 멀티스레드 적용
async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

    car_id = None
    rio_reader = Reader(reader)
    while True:
        bin = await rio_reader.read()
        if bin is None:
            break

        car_idBin = bin[:32]
        jpgBin = bin[32:]

        car_id = car_idBin.decode("utf-8")
        jpgImg = pickle.loads(jpgBin)

        stream_db[car_id].append(bytes(jpgImg))
        while len(stream_db[car_id]) > 300:
            stream_db[car_id].popleft()

    del stream_db[car_id]
    writer.close()


def start_async_server():
    async def start():
        server = await asyncio.start_server(handle, "0.0.0.0", 9999)
        async with server:
            await server.serve_forever()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(start())


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
    await websocket.send_text("connected")
    user = db.query(User).filter(User.email == user_id).first()
    print(user.car_id)
    while True:
        await websocket.send_bytes(bytearray(stream_db[user.car_id][-1]))
        await asyncio.sleep(1 / 30)
