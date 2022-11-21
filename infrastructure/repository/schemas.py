from pydantic import BaseModel
from typing import Union
from uuid import UUID
class Car(BaseModel):
    id: str
    class Config:
        orm_mode = True

class User(BaseModel):
    id: str
    email: str
    password : str

    class Config:
        orm_mode = True

