from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/car", tags=["car"])

class movement(BaseModel):
    dir : int

@router.post("/")
async def move(move:movement):
    print(move.dir)

@router.on_event("startup")
async def router_startup_event():
    ...