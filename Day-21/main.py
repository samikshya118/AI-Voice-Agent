# main.py
from fastapi import FastAPI, Request, UploadFile, File, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any, Type
import logging
from pathlib import Path as PathLib
from uuid import uuid4
import json
import asyncio
import time
import threading
import queue # Import the thread-safe queue

# Import the config file FIRST to load dotenv and configure APIs
import config
from services import stt, llm, tts
from schemas import TTSRequest

# AssemblyAI streaming imports
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)

# Configure logging - Set to WARNING to reduce clutter
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# Mount static for CSS/JS and templates for HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory store for chat histories.
chat_histories: Dict[str, List[Dict[str, Any]]] = {}

# Base directory and uploads folder
BASE_DIR = PathLib(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@app.get("/")
async def home(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/agent/chat/{session_id}")
async def agent_chat(
    session_id: str = Path(..., description="The unique ID for the chat session."),
    audio_file: UploadFile = File(...)
):
    """
    Handles a turn in the conversation, including history.
    STT -> Add to History -> LLM -> Add to History -> TTS
    """
    fallback_audio_path = "static/fallback.mp3"

    # Check for keys by importing them from the config module
    if not all([config.GEMINI_API_KEY, config.ASSEMBLYAI_API_KEY, config.MURF_API_KEY]):
        print("API keys not configured. Returning fallback audio.")
        return FileResponse(fallback_audio_path, media_type="audio/mpeg", headers={"X-Error": "true"})

    try:
        # Step 1: Transcribe audio to text
        user_query_text = stt.transcribe_audio(audio_file)
        print(f"User: {user_query_text}")

        # Step 2: Retrieve history and get a response from the LLM
        session_history = chat_histories.get(session_id, [])
        llm_response_text, updated_history = llm.get_llm_response(user_query_text, session_history)
        print(f"Assistant: {llm_response_text}")

        # Step 3: Update the chat history
        chat_histories[session_id] = updated_history

        # Step 4: Convert the LLM's text response to speech
        audio_url = tts.convert_text_to_speech(llm_response_text)

        if audio_url:
            return JSONResponse(content={"audio_url": audio_url})
        else:
            raise Exception("TTS service did not return an audio file.")

    except Exception as e:
        print(f"Error in session {session_id}: {e}")
        return FileResponse(fallback_audio_path, media_type="audio/mpeg", headers={"X-Error": "true"})


@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    """Endpoint for the simple Text-to-Speech utility."""
    try:
        audio_url = tts.convert_text_to_speech(request.text, request.voiceId)
        if audio_url:
            return JSONResponse(content={"audio_url": audio_url})
        else:
            return JSONResponse(status_code=500, content={"error": "No audio URL in the API response."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"TTS generation failed: {e}"})


@app.get("/voices")
async def get_voices():
    """Fetches the list of available voices from Murf AI."""
    try:
        voices = tts.get_available_voices()
        return JSONResponse(content={"voices": voices})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to fetch voices: {e}"})


@app.websocket("/ws")
async def websocket_audio_streaming(websocket: WebSocket):
    """Receive PCM audio chunks from client and transcribe in real-time using AssemblyAI with turn detection."""
    await websocket.accept()
    file_id = uuid4().hex
    file_path = UPLOADS_DIR / f"streamed_{file_id}.pcm"

    # Check for keys
    if not all([config.ASSEMBLYAI_API_KEY, config.GEMINI_API_KEY, config.MURF_API_KEY]):
        missing_keys = [key for key, value in {
            "AssemblyAI": config.ASSEMBLYAI_API_KEY,
            "Gemini": config.GEMINI_API_KEY,
            "Murf": config.MURF_API_KEY
        }.items() if not value]
        error_msg = f"{', '.join(missing_keys)} API key(s) not configured"
        await websocket.send_text(json.dumps({"type": "error", "message": error_msg}))
        await websocket.close(code=1000, reason=error_msg)
        return

    # Create queues
    transcription_queue = asyncio.Queue()
    audio_queue = queue.Queue()
    
    session_history = []
    processed_turns = set()
    last_turn_time = 0

    client = StreamingClient(
        StreamingClientOptions(
            api_key=config.ASSEMBLYAI_API_KEY,
            api_host="streaming.assemblyai.com",
        )
    )

    async def process_llm_with_murf_async(transcript_text: str, audio_q: queue.Queue):
        nonlocal session_history
        try:
            _, updated_history, audio_chunks = await llm.get_llm_streaming_response_with_murf(transcript_text, session_history)
            session_history = updated_history
            print()
            print(f"\nReceived {len(audio_chunks)} audio chunks from Murf. Queueing for client...")
            for chunk in audio_chunks:
                audio_q.put({"type": "audio", "data": chunk})
        except Exception as e:
            print(f"\nError in LLM/Murf integration: {e}")

    def process_llm_with_murf_sync(transcript_text: str, audio_q: queue.Queue):
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_llm_with_murf_async(transcript_text, audio_q))
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()

    def on_begin(self: Type[StreamingClient], event: BeginEvent):
        print("Transcription session started")

    def on_turn(self: Type[StreamingClient], event: TurnEvent):
        nonlocal processed_turns, last_turn_time
        transcript_text = event.transcript.strip()
        current_time = time.time()
        normalized_transcript = ' '.join(transcript_text.lower().split())
        
        if (event.end_of_turn and transcript_text and len(transcript_text) > 3 and
            normalized_transcript not in processed_turns and
            current_time - last_turn_time > 2.0):
            
            processed_turns.add(normalized_transcript)
            last_turn_time = current_time
            print(f"\nUser: {transcript_text}")
            
            try:
                transcription_queue.put_nowait({
                    "type": "transcription", "text": transcript_text,
                    "is_final": True, "end_of_turn": True
                })
                transcription_queue.put_nowait({
                    "type": "turn_end", "message": "User stopped talking"
                })
                print("Assistant: ", end="", flush=True)
                process_llm_with_murf_sync(transcript_text, audio_queue)
            except asyncio.QueueFull:
                print("Transcription queue is full")

    def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
        print(f"Session ended - {event.audio_duration_seconds:.1f}s processed")

    def on_error(self: Type[StreamingClient], error: StreamingError):
        print(f"Transcription error: {error}")
        try:
            transcription_queue.put_nowait({"type": "error", "message": str(error)})
        except asyncio.QueueFull:
            pass

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    async def send_transcriptions():
        while True:
            try:
                message = await asyncio.wait_for(transcription_queue.get(), timeout=0.1)
                await websocket.send_text(json.dumps(message))
                transcription_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except (asyncio.CancelledError, WebSocketDisconnect):
                break

    async def send_audio():
        while True:
            try:
                message = audio_queue.get_nowait()
                await websocket.send_text(json.dumps(message))
                audio_queue.task_done()
            except queue.Empty:
                await asyncio.sleep(0.01)
            except (asyncio.CancelledError, WebSocketDisconnect):
                break

    sender_task = asyncio.create_task(send_transcriptions())
    audio_sender_task = asyncio.create_task(send_audio())

    try:
        client.connect(StreamingParameters(sample_rate=16000, format_turns=True))
        await websocket.send_text(json.dumps({
            "type": "status", "message": "Connected to transcription service"
        }))

        with open(file_path, "wb") as f:
            while True:
                message = await websocket.receive()
                
                if "bytes" in message:
                    pcm_data = message["bytes"]
                    f.write(pcm_data)
                    client.stream(pcm_data)
                elif message.get("text") == "EOF":
                    print("Recording finished. Waiting for audio generation to complete...")
                    # *** THE KEY CHANGE IS HERE ***
                    # Wait for the audio queue to be fully processed before breaking
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, audio_queue.join)
                    print("Audio generation complete. Closing connection.")
                    break

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        sender_task.cancel()
        audio_sender_task.cancel()
        try:
            client.disconnect(terminate=True)
        except Exception as e:
            print(f"Error disconnecting AssemblyAI: {e}")
        try:
            if websocket.client_state != "DISCONNECTED":
                await websocket.close()
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    print("Starting AI Voice Agent Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)