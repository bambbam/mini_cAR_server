from fastapi import APIRouter, Depends
from infrastructure.repository.base import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, status, Depends
from interface.router.auth import get_current_user
from infrastructure.repository import schemas, model
from pydantic import BaseModel


router = APIRouter(prefix="/gallery", tags=["gallery"])

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