from signal import signal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sys
import signal
import uvicorn

from interface.router.stream import router as stream_router
from interface.router.car import router as car_router
from interface.router.user import router as user_router
from interface.router.gallery import router as gallery_router


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:4000",
    "http://127.0.0.1",
    "http://127.0.0.1:4000",
    "http://0.0.0.0:4000" # for docker bridge network,
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)
app.include_router(car_router)
app.include_router(user_router)
app.include_router(gallery_router)

@app.get("/")
async def root():
    return {"message": "hello"}


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    return FileResponse("favicon.ico")


def signal_handler(signum, frame):
    sys.exit()


@app.on_event("startup")
async def startup_event():
    signal.signal(signal.SIGINT, signal_handler)


def main():
    uvicorn.run("server.app:app", reload=True, host="0.0.0.0")
