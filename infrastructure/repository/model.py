from infrastructure.repository.base import Base

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sqlalchemy import types
from sqlalchemy.dialects.mysql.base import MSBinary
from sqlalchemy.schema import Column
import datetime
import uuid


def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "user"
    id = Column(String(255), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255), nullable=False)
    car_id = Column(String(255), ForeignKey("car.id"))
    car = relationship("Car", back_populates="user")
    

class Car(Base):
    __tablename__ = "car"
    id = Column(String(255), primary_key=True, default=generate_uuid)
    user = relationship("User", back_populates="car", uselist=False)
    media = relationship("Media", back_populates="car")

class Media(Base):
    __tablename__ = "media"
    id = Column(String(255), primary_key=True, default=generate_uuid)
    key = Column(String(255))
    type = Column(String(255))
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    car_id = Column(String(255), ForeignKey("car.id"))
    
    car = relationship("Car", back_populates="media")
    