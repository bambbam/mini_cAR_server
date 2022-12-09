from functools import lru_cache
from pydantic import BaseSettings
from typing import Union
import enum

class ProductionMode(enum.Enum):
    PRODUCTION = "prod"
    DEVELOPMENT = "dev"


class Settings(BaseSettings):
    mode : ProductionMode = ProductionMode.DEVELOPMENT
    
    dev_db_url : str
    prod_db_url : str

    # for streaming in start_async_server
    frame_rate : int = 30

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_bucket_name: str

    # for camera in camera_thread
    fps: int
    width: int
    height: int
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
