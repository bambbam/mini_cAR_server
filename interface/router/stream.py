from typing import Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import threading
import struct
import pickle
import threading
from collections import defaultdict, deque
from interface.router.car import CarCache
import asyncio
from asyncio import Server

import pydantic


router = APIRouter(prefix="/stream", tags=["stream"])

stream_db = defaultdict(lambda: deque(b"")) #여러개에 대해서 수신 가능하도록 변경
DEFAULT_CAR_ID = "e208d83305274b1daa97e4465cb57c8b"

# 클라이언트에게 들어오는 데이터 포맷
class Income(pydantic.BaseModel):
    car_id : str
    jpgImg : list


class Reader:
    def __init__(self, reader):
        self.reader = reader
        self.buffer = b""
        self.len_size = struct.calcsize("<L")
    
    async def read(self):
        while len(self.buffer) < self.len_size:
            recved = await self.reader.read(4096)
            if len(recved)==0:
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
async def handle(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    
    car_id = None
    rio_reader = Reader(reader)
    while True:
        bin = await rio_reader.read()
        if bin is None:
            break
        income = Income.parse_raw(pickle.loads(bin))
        car_id = income.car_id
        stream_db[income.car_id].append(bytes(income.jpgImg)) 
        while len(stream_db[income.car_id]) > 300:
            stream_db[income.car_id].popleft()
    
    del stream_db[car_id]
    writer.close()



def start_async_server():
    async def start():
        server = await asyncio.start_server(handle, "0.0.0.0",9999)
        async with server:
            await server.serve_forever()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(start())


@router.on_event("startup")
async def router_startup_event():
    t = threading.Thread(target=start_async_server)
    t.start()

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
