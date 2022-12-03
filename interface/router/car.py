import asyncio
import threading
import struct
import pickle
from enum import Enum
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from base.singleton import Singleton
from collections import defaultdict, deque

from sqlalchemy.orm import Session
from infrastructure.repository.base import get_db
from infrastructure.repository import schemas, model
from interface.router.auth import get_current_user


router = APIRouter(prefix="/car", tags=["car"])

DEFAULT_CAR_ID = "e208d83305274b1daa97e4465cb57c8b"

class CarCache(Singleton):
    def __init__(self):
        self.cache = {}

    def add(self, id, move):
        self.cache[id] = move

    def get(self, id):
        if id in self.cache:
            ret = self.cache[id]
            self.cache.pop(id,None)
            return ret
        else:
            return None

class Movement(Enum):
    nothing = 0
    forward = 1
    right = 2
    left = 3
    backward = 4
    stop = 5
    beep = 6
    speedup = 7
    speeddown = 8
    

class movement(BaseModel):
    dir : Movement

@router.post("/")
async def move(move:movement, user = Depends(get_current_user), db: Session = Depends(get_db)):
    car_user = db.query(model.User).join(model.Car) \
                    .filter(model.User.email == user["user"]) \
                    .first()
    if not car_user:
        raise HTTPException(status_code=400, detail="사용자에 자동차가 등록되지 않았습니다.")
    CarCache().add(car_user.car_id, move.dir)

class Register(BaseModel):
    car_id : str

@router.post("/register")
async def register(info : Register, db: Session = Depends(get_db)):
    car = db.query(model.Car) \
                .filter(model.Car.id == info.car_id) \
                .first()
    if car:
        raise HTTPException(status_code=400, detail="이미 존재하는 자동차입니다.")
    created_car = model.Car(id=info.car_id)
    db.add(created_car)
    db.commit()


class Message(BaseModel):
    message: str


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


async def handle(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    car_cache = CarCache()
    rio_reader = Reader(reader)
    while True:
        movement = car_cache.get(DEFAULT_CAR_ID)
        movement = movement if movement is not None else Movement.nothing
        writer.write(struct.pack("<L", movement.value))
        await writer.drain()

        bin = await rio_reader.read()
        #income = Message.parse_raw(pickle.loads(bin))
        
        if bin==None:
            break
    writer.close()
        

def start_async_server():
    async def start():
        server = await asyncio.start_server(handle, "0.0.0.0",9998)
        async with server:
            await server.serve_forever()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(start())


@router.on_event("startup")
async def router_startup_event():
    t = threading.Thread(target=start_async_server)
    t.start()