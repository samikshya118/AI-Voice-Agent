from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, shutil, uuid, requests, logging

import assemblyai as aai
from murf import Murf
from google import genai  # ✅ correct import for new SDK

# ---------------- Logging ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Load API Keys ---------------- #
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Create Gemini client once (if key exists)
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ---------------- FastAPI Setup ---------------- #
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Directories ---------------- #
UPLOAD_DIR = "uploads"
GENERATED_DIR = "generated"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"

for d in [UPLOAD_DIR, GENERATED_DIR, STATIC_DIR, TEMPLATES_DIR]:
    os.makedirs(d, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# ---------------- Helper Functions ---------------- #
def download_audio(url: str) -> str:
    try:
        r = requests.get(url)
        r.raise_for_status()
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join(GENERATED_DIR, filename)
        with open(path, "wb") as f:
            f.write(r.content)
        return f"/generated/{filename}"
    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        return "/static/fallback.mp3"

def error(message, details=""):
    # Always include fallback audio in error responses
    return JSONResponse(
        status_code=400,
        content={
            "error": message,
            "details": details,
            "audio_url": "/static/fallback.mp3"
        }
    )

def validate_api_keys(required_keys):
    missing = []
    if "assemblyai" in required_keys and not ASSEMBLYAI_API_KEY:
        missing.append("AssemblyAI API key")
    if "murf" in required_keys and not MURF_API_KEY:
        missing.append("Murf API key")
    if "gemini" in required_keys and not GEMINI_API_KEY:
        missing.append("Gemini API key")
    if missing:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Missing API Key(s): {' and '.join(missing)}",
                "details": "Please add the missing key(s) to your .env file and restart the server.",
                "audio_url": "/static/fallback.mp3"
            }
        )
    return None


chat_history = {}

# ---------------- Routes ---------------- #
@app.get("/")
async def index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

@app.post("/generate-audio")
async def generate_audio(payload: dict):
    key_err = validate_api_keys(["murf"])
    if key_err: return key_err

    text = payload.get("text", "").strip()
    if not text:
        return error("No text provided.", "Please type something to convert to speech.")
    try:
        murf_client = Murf(api_key=MURF_API_KEY)
        res = murf_client.text_to_speech.generate(text=text, voice_id="en-US-terrell")
        return {"audio_url": download_audio(res.audio_file)}
    except Exception as e:
        logger.error(f"TTS Error: {e}", exc_info=True)
        return error("Text-to-speech failed.", str(e))

@app.post("/tts/echo")
async def tts_echo(audio: UploadFile = File(...)):
    key_err = validate_api_keys(["assemblyai", "murf"])
    if key_err: return key_err

    try:
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        murf_client = Murf(api_key=MURF_API_KEY)

        path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{audio.filename}")
        with open(path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        transcript = transcriber.transcribe(path)
        if transcript.status == aai.TranscriptStatus.error:
            return error("Speech-to-text failed.", transcript.error)

        res = murf_client.text_to_speech.generate(text=transcript.text, voice_id="en-US-natalie")
        return {"transcription": transcript.text, "audio_url": download_audio(res.audio_file)}
    except Exception as e:
        logger.error(f"Echo Error: {e}", exc_info=True)
        return error("Echo bot failed.", str(e))

@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str, audio: UploadFile = File(...)):
    key_err = validate_api_keys(["assemblyai", "murf", "gemini"])
    if key_err: 
        return key_err

    try:
        # Init clients
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        murf_client = Murf(api_key=MURF_API_KEY)

        path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{audio.filename}")
        with open(path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        # Speech-to-text
        transcript = transcriber.transcribe(path)
        if transcript.status == aai.TranscriptStatus.error:
            return error("Speech-to-text failed.", transcript.error)

        user_text = transcript.text.strip()
        if not user_text:
            return error("No speech detected.", "Please speak clearly into the microphone.")

        # Chat history
        history = chat_history.get(session_id, [])
        history.append({"role": "user", "content": user_text})
        while sum(len(m["content"]) for m in history) > 2900:
            history.pop(0)

        # Gemini response
        assistant_text = "I'm having trouble responding right now."
        try:
            llm_res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="\n".join(
                    [f"User: {m['content']}" if m["role"] == "user" 
                     else f"Assistant: {m['content']}" for m in history]
                )
            )
            if hasattr(llm_res, "text") and llm_res.text:
                assistant_text = llm_res.text.strip()
        except Exception as e:
            logger.error(f"Gemini Error: {e}", exc_info=True)

        history.append({"role": "assistant", "content": assistant_text})
        chat_history[session_id] = history

        # TTS
        audio_url = "/static/fallback.mp3"
        try:
            tts_res = murf_client.text_to_speech.generate(
                text=assistant_text, 
                voice_id="en-US-natalie"
            )
            audio_url = download_audio(tts_res.audio_file)
        except Exception as e:
            logger.error(f"TTS Error: {e}", exc_info=True)

        return {
            "user_transcription": user_text,
            "llm_response": assistant_text,
            "audio_url": audio_url
        }

    except Exception as e:
        logger.error(f"Agent Error: {e}", exc_info=True)
        return error("Agent chat failed.", str(e))
