from infrastructure.repository import base

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, ForeignKeyConstraint
from sqlalchemy.orm import relationship


import uuid

meta = base.Base.metadata
user = Table(
    "user",
    meta,
    Column("id", String(255), primary_key=True, default=str(uuid.uuid4)),
    Column("email", String(255), unique=True, index=True),
    Column("password", String(255), nullable=False),
    Column("car_id", String(255), ForeignKey("car.id")),
    ForeignKeyConstraint(["car_id"], ["car.id"]),
)

car = Table(
    "car",
    meta,
    Column("id", String(255), primary_key=True, default=str(uuid.uuid4)),
)

meta.create_all(base.engine)