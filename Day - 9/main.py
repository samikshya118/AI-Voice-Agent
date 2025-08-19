from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import shutil
import uuid
import assemblyai as aai
import tempfile
import requests 
from murf import Murf  # ✅ Official Murf SDK
from google import genai
from pydantic import BaseModel


# ✅ Load environment variables
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()

# ✅ Initialize Murf client
murf_client = Murf(api_key=MURF_API_KEY)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# ✅ Initialize FastAPI
app = FastAPI()
UPLOAD_DIR = "uploads"
GENERATED_DIR = "generated"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/llm/query")
async def llm_query(audio: UploadFile = File(...)):
    try:
        # 1. Save uploaded audio
        unique_filename = f"{uuid.uuid4()}_{audio.filename}"
        audio_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 2. Transcribe with AssemblyAI
        transcript = transcriber.transcribe(audio_path)
        if transcript.status == aai.TranscriptStatus.error:
            return JSONResponse(status_code=500, content={"error": transcript.error})
        
        transcription_text = transcript.text

        # 3. Send to Gemini LLM
        llm_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=transcription_text
        )
        llm_text = llm_response.text

        # 4. Send LLM output to Murf
        murf_res = murf_client.text_to_speech.generate(
            text=llm_text,
            voice_id="en-US-terrell",  # can change
        )
        murf_audio_url = murf_res.audio_file

        # 5. Download Murf audio locally
        audio_data = requests.get(murf_audio_url).content
        murf_filename = f"{uuid.uuid4()}.mp3"
        murf_path = os.path.join(GENERATED_DIR, murf_filename)
        with open(murf_path, "wb") as f:
            f.write(audio_data)

        return {
            "user_transcription": transcription_text,
            "llm_response": llm_text,
            "audio_url": f"/generated/{murf_filename}"
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
