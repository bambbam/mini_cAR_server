from signal import signal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import sys
import signal
import uvicorn

from interface.router.streams import router as stream_router
from interface.socket.server import Socket

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:4000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(stream_router)


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
    uvicorn.run("server.app:app", reload=True)
