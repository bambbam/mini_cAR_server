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

    frame_rate : int = 30

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
