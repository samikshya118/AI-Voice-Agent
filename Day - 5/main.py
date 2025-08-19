from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
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

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ✅ Ensure upload folder exists

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
            voice_id="en-US-terrell"
        )
        return {"audio_url": res.audio_file}
    except Exception as e:
        return {"error": str(e)}

# ✅ New endpoint to receive audio files
@app.post("/upload")
async def upload_audio(audio: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_FOLDER, audio.filename)

    with open(file_location, "wb") as f:
        content = await audio.read()
        f.write(content)

    return JSONResponse({
        "name": audio.filename,
        "content_type": audio.content_type,
        "size": len(content)
    })
