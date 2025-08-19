
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# New imports for POST endpoint
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv



# FastAPI app instance
app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Existing GET endpoint for UI
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Load .env file
load_dotenv()
print("Murf API key loaded:", os.getenv("MURF_API_KEY"))
# ✅ New POST endpoint for Murf TTS
MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_API_URL = "https://api.murf.ai/v1/speech/generate"

class TextInput(BaseModel):
    text: str

@app.post("/generate-audio/")
async def generate_audio(input: TextInput):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "api-key": MURF_API_KEY
    }
    payload = {
        "text": input.text,
        "voice": "en-US-Wavenet-D",  # You can choose a different voice
        "format": "mp3"
    }

    response = requests.post(MURF_API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return {"audio_url": response.json().get("audioUrl")}
    else:
        return {"error": response.text}
