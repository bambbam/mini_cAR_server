from typing import Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import threading
import struct
import pickle
import threading
from collections import defaultdict, deque

import asyncio

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

async def handle(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    buffer = b""
    len_size = struct.calcsize("<L")
    while True:
        while len(buffer) < len_size:
            recved = await reader.read(4096)
            buffer += recved

        packed_bin_size = buffer[: len_size]
        buffer = buffer[len_size :]

        bin_size = struct.unpack("<L", packed_bin_size)[0]

        while len(buffer) < bin_size:
            recved = await reader.read(4096)
            buffer += recved

        bin = buffer[:bin_size]
        buffer = buffer[bin_size:]
        
        income = Income.parse_raw(pickle.loads(bin))
        stream_db[income.car_id].append(bytes(income.jpgImg)) 
        while len(stream_db[income.car_id]) > 300:
            stream_db[income.car_id].popleft()



async def f():
    server = await asyncio.start_server(handle, "0.0.0.0",9999)
    async with server:
        await server.serve_forever()

def start_async_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(f())





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
