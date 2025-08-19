from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, shutil, uuid, requests

import assemblyai as aai
from murf import Murf
from google import genai

# --- Load API keys ---
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Init SDKs ---
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()

murf_client = Murf(api_key=MURF_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

# --- FastAPI setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Directories ---
UPLOAD_DIR = "uploads"
GENERATED_DIR = "generated"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# --- Serve static and generated files ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# --- Chat memory ---
chat_history = {}

def download_audio_from_url(url: str) -> str:
    """Download Murf-generated audio to /generated and return relative path."""
    res = requests.get(url)
    res.raise_for_status()
    filename = f"{uuid.uuid4()}.mp3"
    path = os.path.join(GENERATED_DIR, filename)
    with open(path, "wb") as f:
        f.write(res.content)
    return f"/generated/{filename}"

# --- Serve index.html ---
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

# --- Text to speech ---
@app.post("/generate-audio")
async def generate_audio(payload: dict):
    try:
        text = payload.get("text", "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"error": "No text provided"})

        voice_id = payload.get("voice", "en-US-terrell")
        murf_res = murf_client.text_to_speech.generate(text=text, voice_id=voice_id)
        murf_audio_url = murf_res.audio_file
        local_path = download_audio_from_url(murf_audio_url)
        return {"audio_url": local_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Echo bot ---
@app.post("/tts/echo")
async def tts_echo(audio: UploadFile = File(...)):
    try:
        fname = f"{uuid.uuid4()}_{audio.filename}"
        path = os.path.join(UPLOAD_DIR, fname)
        with open(path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        transcript = transcriber.transcribe(path)
        if transcript.status == aai.TranscriptStatus.error:
            return JSONResponse(status_code=500, content={"error": transcript.error})

        transcription_text = transcript.text
        murf_res = murf_client.text_to_speech.generate(
            text=transcription_text,
            voice_id="en-US-natalie"
        )
        murf_audio_url = murf_res.audio_file
        local_path = download_audio_from_url(murf_audio_url)

        return {"transcription": transcription_text, "audio_url": local_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Agent with session memory ---
@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str, audio: UploadFile = File(...)):
    try:
        audio_filename = f"{uuid.uuid4()}_{audio.filename}"
        audio_path = os.path.join(UPLOAD_DIR, audio_filename)
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        transcript = transcriber.transcribe(audio_path)
        if transcript.status == aai.TranscriptStatus.error:
            return JSONResponse(status_code=500, content={"error": transcript.error})
        user_text = (transcript.text or "").strip()
        if not user_text:
            return JSONResponse(status_code=400, content={"error": "No speech detected"})

        history = chat_history.get(session_id, [])
        history.append({"role": "user", "content": user_text})

        MAX_CHARS = 2900
        while sum(len(m["content"]) for m in history) > MAX_CHARS:
            history.pop(0)

        conversation_text = "\n".join(
            [f"User: {m['content']}" if m["role"] == "user" else f"Assistant: {m['content']}"
             for m in history]
        )

        llm_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation_text
        )
        assistant_text = (llm_resp.text or "Sorry, I couldn't generate a response.").strip()

        history.append({"role": "assistant", "content": assistant_text})
        chat_history[session_id] = history

        murf_res = murf_client.text_to_speech.generate(
            text=assistant_text,
            voice_id="en-US-natalie"
        )
        murf_audio_url = murf_res.audio_file
        local_audio_path = download_audio_from_url(murf_audio_url)

        return {
            "user_transcription": user_text,
            "llm_response": assistant_text,
            "audio_url": local_audio_path
        }
    except requests.exceptions.HTTPError as re:
        return JSONResponse(status_code=500, content={"error": f"HTTP error: {str(re)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
