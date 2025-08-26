# main.py
from fastapi import FastAPI, Request, UploadFile, File, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any, Type
import logging
from pathlib import Path as PathLib
from uuid import uuid4
import asyncio
import base64
import re

# Import services
import config
from services import stt, llm, tts

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chat_history: List[Dict[str, Any]] = []  # shared history for all sessions



@app.get("/")
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connection for real-time transcription and voice response."""
    await websocket.accept()
    logging.info("WebSocket client connected.")

    # ✅ Persona comes from frontend dropdown
    persona = websocket.query_params.get("persona", "friendly_teacher")
    logging.info(f"Persona selected: {persona}")

    try:
        while True:
            data = await websocket.receive_json()
            logging.info(f"Received from client: {data}")

            if "transcript" in data:
                text = data["transcript"].strip()
                if text:
                    logging.info(f"Transcript received: {text}")
                    await handle_transcript(websocket, text, persona)
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected.")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close()


async def handle_transcript(websocket: WebSocket, text: str, persona: str):
    """Handles transcript -> LLM -> persona-based TTS with structured responses."""

    global chat_history
    loop = asyncio.get_event_loop()

    try:
        # ✅ Send the raw user transcript to frontend
        await websocket.send_json({"type": "final", "text": text})

        # ✅ Pass persona into LLM
        full_response, updated_history = llm.get_llm_response(
            text, chat_history, persona=persona
        )
        chat_history = updated_history

        logging.info(f"LLM Response: {full_response}")

        # ✅ Send assistant's full response in both formats
        await websocket.send_json({"type": "assistant", "text": full_response})
        await websocket.send_json({"response": full_response})  # old format support

        # ✅ More robust sentence splitting
        sentences = re.split(r'(?<=[.?!])\s+', full_response.strip())

        # ✅ Persona-based TTS
        for sentence in sentences:
            if sentence.strip():
                audio_bytes = await loop.run_in_executor(
                    None, tts.speak, sentence.strip(), persona
                )

                if audio_bytes:
                    # Send raw audio bytes
                    await websocket.send_bytes(audio_bytes)

                    # Also send base64 audio (structured JSON)
                    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    await websocket.send_json({"type": "audio", "b64": b64_audio})

    except Exception as e:
        logging.error(f"Error in LLM/TTS pipeline: {e}")
        await websocket.send_json(
            {"type": "error", "text": "Sorry, I encountered an error."}
        )



@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    uploads_dir = PathLib(__file__).resolve().parent / "uploads"
    file_path = uploads_dir / filename
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse(content={"error": "File not found"}, status_code=404)
