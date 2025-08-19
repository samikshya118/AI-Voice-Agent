from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import shutil
import uuid
import requests
import tempfile
import assemblyai as aai

# ✅ Load environment variables
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")

# ✅ AssemblyAI setup
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()

# ✅ Initialize FastAPI
app = FastAPI()

# Uploads folder
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ===== Pydantic Models =====
class TextInput(BaseModel):
    text: str


# ===== Routes =====
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate_audio")
async def generate_audio(input: TextInput):
    """Fake TTS endpoint — replace with Murf integration."""
    return {"audio_url": "https://example.com/audio.mp3"}


@app.post("/upload")
async def upload_audio(audio: UploadFile = File(...)):
    """Save uploaded audio file."""
    file_location = os.path.join(UPLOAD_DIR, audio.filename)
    content = await audio.read()

    with open(file_location, "wb") as f:
        f.write(content)

    return JSONResponse({
        "name": audio.filename,
        "content_type": audio.content_type,
        "size": len(content)
    })


@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Serve uploaded audio file."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    return FileResponse(file_path, media_type="audio/webm")


@app.post("/transcribe/file")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file using AssemblyAI."""
    try:
        # Save temporary file
        audio_bytes = await audio.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name

        # Transcribe
        transcript = transcriber.transcribe(temp_path)
        os.remove(temp_path)  # Cleanup

        return {"transcription": transcript.text}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/echo")
async def echo(audio: UploadFile = File(...)):
    """
    Record → Transcribe with AssemblyAI → Convert to voice with Murf API → Return audio URL.
    """
    try:
        # Save uploaded file
        unique_filename = f"{uuid.uuid4()}_{audio.filename}"
        audio_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Transcribe with AssemblyAI
        transcript = transcriber.transcribe(audio_path)

        if transcript.status == aai.TranscriptStatus.error:
            return JSONResponse(status_code=500, content={"error": transcript.error})

        transcription_text = transcript.text

        # Generate audio with Murf API
        murf_url = "https://api.murf.ai/v1/speech/generate"
        murf_headers = {
            "Authorization": f"Bearer {MURF_API_KEY}",
            "Content-Type": "application/json"
        }
        murf_payload = {
            "voice": "natalie",  # ✅ Replace with actual Murf voice ID
            "text": transcription_text,
            "format": "mp3"
        }

        murf_resp = requests.post(murf_url, headers=murf_headers, json=murf_payload)

        if murf_resp.status_code != 200:
            return JSONResponse(status_code=500, content={
                "error": "Murf TTS failed",
                "details": murf_resp.text
            })

        audio_url = murf_resp.json().get("audio_url")

        return {
            "transcription": transcription_text,
            "audio_url": audio_url
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
