from typing import Literal, Union


from fastapi import APIRouter, Depends
from infrastructure.repository.base import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, status, Depends
from interface.router.auth import get_current_user
from infrastructure.repository import schemas, model
from pydantic import BaseModel


router = APIRouter(prefix="/gallery", tags=["gallery"])

class MediaData(BaseModel):
    car_id : str
    type: Literal["img", "video"]
    key : str

@router.post("/")
def put_data(data:MediaData, db: Session = Depends(get_db) ):
    cur_car = db.query(model.Car) \
                .filter(model.Car.id == data.car_id) \
                .first()
    if cur_car is None:
        raise HTTPException(status_code= 400, detail="잘못된 자동차 번호입니다.")
    
    media = db.query(model.Media) \
                .filter(model.Media.car_id == data.car_id) \
                .filter(model.Media.key == data.key) \
                .first()
    if media:
        raise HTTPException(status_code= 400, detail="이미 존재하는 key입니다.")
    
    created_media = model.Media(key=data.key, type=data.type, car_id=data.car_id)
    db.add(created_media)
    db.commit()
    return created_media


@router.get("/")
def get_media_list(user = Depends(get_current_user), db: Session = Depends(get_db) ):
    media_list = db.query(model.Media) \
                    .join(model.Car) \
                    .join(model.User) \
                    .filter(model.User.email == user["user"]) \
                    .all()
    result = []
    for media in media_list:
        m = media.__dict__
        m.pop('_sa_instance_state', None)
        result.append(m)
    return result