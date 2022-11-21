from infrastructure.repository.base import Base

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy import types
from sqlalchemy.dialects.mysql.base import MSBinary
from sqlalchemy.schema import Column
import uuid


class User(Base):
    __tablename__ = "user"
    id = Column(String(255), primary_key=True, default=str(uuid.uuid4))
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255), nullable=False)
    car_id = Column(String(255), ForeignKey("car.id"))
    car = relationship("Car", back_populates="user")


class Car(Base):
    __tablename__ = "car"
    id = Column(String(255), primary_key=True, default=str(uuid.uuid4))
    user = relationship("User", back_populates="car", uselist=False)
