import os
import asyncio
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.stt_service import stream_transcription
from asyncio import Queue
from dotenv import load_dotenv

# Load env
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    raise ValueError("⚠️ ASSEMBLYAI_API_KEY not found. Please set it in your .env")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_queue: Queue = Queue()

    async def receive_audio():
        try:
            while True:
                data = await websocket.receive_bytes()
                await audio_queue.put(data)
        except Exception as e:
            print("Client disconnected:", e)
        finally:
            await audio_queue.put(None)

    transcriber_task = asyncio.create_task(
        stream_transcription(websocket, audio_queue, ASSEMBLYAI_API_KEY)
    )

    await asyncio.gather(receive_audio(), transcriber_task)
