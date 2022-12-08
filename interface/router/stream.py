from typing import Any, Literal
from fastapi import APIRouter, Depends, WebSocket, HTTPException
import threading
import multiprocessing
import struct
import pickle
from enum import Enum
from pydantic import BaseModel
from collections import defaultdict, deque
from infrastructure.repository.base import get_db
from infrastructure.repository.model import User
from infrastructure.repository import schemas, model
from infrastructure.repository.s3 import get_S3, S3

from sqlalchemy.orm import Session
import asyncio
import config
import os 
import asyncio_dgram
import uvloop
import cv2
from datetime import datetime

router = APIRouter(prefix="/stream", tags=["stream"])

stream_db = defaultdict(lambda: deque(b""))  # 여러개에 대해서 수신 가능하도록 변경
DEFAULT_CAR_ID = "e208d83305274b1daa97e4465cb57c8b"


video_buffer = defaultdict(lambda: list())  # 여러개에 대해서 수신 가능하도록 변경
video_started = set()
def add_stream(car_id, data):
    stream_db[car_id].append(bytes(data))
    while len(stream_db[car_id]) > 300:
        stream_db[car_id].popleft()

    for video in video_started:
        video_buffer[video].append(data)
    
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
            add_stream(car_id, jpgImg)    
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


@router.websocket("/{user_id}/ws")
async def stream_ws(websocket: WebSocket, user_id: str, db: Session = Depends(get_db), setting: config.Settings = Depends(config.get_settings)):
    await websocket.accept()
    #await websocket.send_text("connected")
    user = db.query(User).filter(User.email == user_id).first()
    print(user.car_id)
    while True:
        await websocket.send_bytes(bytearray(stream_db[user.car_id][-1]))
        await asyncio.sleep(1 / setting.frame_rate)


class CameraControl(Enum):
    getphoto = 0
    videostart = 1
    videostop = 2

def generate_key():
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
    return dt_string


class MediaData(BaseModel):
    ctrl: CameraControl
    car_id : str
#    type: Literal["img", "video"]


def upload_img(key, car_id, image, db : Session, s3 : S3):
    created_media = model.Media(key=key, type="img", car_id=car_id)
    is_error = False
    try:
        s3.upload(car_id, key, image)
    except:
        is_error = True
    if not is_error:
        db.add(created_media)
        db.commit()
        print("upload_complete")

def upload_video(key, car_id, label, db, s3):
    os.system(f"ffmpeg -i {f'{label}'} -vcodec libx264 {f'{label}_out.mp4'}")    
    success = False
    try:
        s3.upload_video(f'{label}_out.mp4', car_id, key+".mp4")    
        success = True
    except:
        raise HTTPException(status_code=500, detail="s3 에러")
    finally:
        os.remove(label)
        os.remove(f'{label}_out.mp4')

    if success:
        created_media = model.Media(key=f'{key}.mp4', type="video", car_id=car_id)
        db.add(created_media)
        db.commit()
        print("upload_complete")
    

@router.post("/")
async def camera_control(data:MediaData, db: Session = Depends(get_db), s3: S3 = Depends(get_S3), setting: config.Settings = Depends(config.get_settings)):
    cur_car = db.query(model.Car) \
                .filter(model.Car.id == data.car_id) \
                .first()
    if cur_car is None:
        raise HTTPException(status_code=400, detail="잘못된 자동차 번호입니다.")
    key = generate_key()
    if data.ctrl == CameraControl.getphoto:
        key = key + ".png"
        created_media = model.Media(key=key, type="img", car_id=data.car_id)
        is_error = False
        try:
            s3.upload(data.car_id, key, stream_db[data.car_id][-1])
        except:
            is_error = True
        if not is_error:
            db.add(created_media)
            db.commit()
            print("upload_complete")
            
    elif data.ctrl == CameraControl.videostart:
        video_started.add(data.car_id)
    elif data.ctrl == CameraControl.videostop:
        if data.car_id in video_started:
            video_started.remove(data.car_id)
            video_list = video_buffer[data.car_id]
            fourcc = cv2.VideoWriter_fourcc(*"X264")
            fps = setting.fps
            width = setting.width
            height = setting.height
            
            label = f"./tmp/{data.car_id}_{key}.mp4"
            out = cv2.VideoWriter(label, fourcc, fps, (width, height) )
            for video in video_list:
                video = cv2.imdecode(video, cv2.IMREAD_COLOR)
                out.write(video)
            out.release()
            video_buffer.pop(data.car_id, None)
            os.system(f"ffmpeg -i {f'{label}'} -vcodec libx264 {f'{label}_out.mp4'}")
            
            success = False
            try:
                s3.upload_video(f'{label}_out.mp4', data.car_id, key+".mp4")    
                success = True
            except:
                raise HTTPException(status_code=500, detail="s3 에러")
            finally:
                os.remove(label)
                os.remove(f'{label}_out.mp4')

            if success:
                created_media = model.Media(key=f'{key}.mp4', type="video", car_id=data.car_id)
                db.add(created_media)
                db.commit()
                print("upload_complete")
                
            


