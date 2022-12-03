from pydantic import BaseModel
from typing import Union
from uuid import UUID
from datetime import datetime

class Car(BaseModel):
    id: str

    class Config:
        orm_mode = True


class User(BaseModel):
    id: str
    email: str
    password: str

    class Config:
        orm_mode = True


class Gallery(BaseModel):
    id: str
    key: str
    type: str
    created_date: datetime
    
    class Config:
        orm_mode = True