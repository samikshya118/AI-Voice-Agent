 from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
import os

load_dotenv()  
api_key = os.getenv("MURF_API_KEY")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class TextInput(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate_audio")
async def generate_audio(input: TextInput):
    try:
        client = Murf(api_key=api_key)
        res = client.text_to_speech.generate(
            text=input.text,
            voice_id="en-US-terrell"  # Use a valid voice_id from Murf docs
        )
        return {"audio_url": res.audio_file}
    except Exception as e:
        return {"error": str(e)}
