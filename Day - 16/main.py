from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static (for script.js, css, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates (for index.html)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# --- WebSocket for audio streaming ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Client connected")

    filename = "recorded_audio.webm"
    if os.path.exists(filename):
        os.remove(filename)
        print(f"🗑️ Old {filename} removed")

    with open(filename, "ab") as f:
        try:
            while True:
                data = await websocket.receive_bytes()
                print(f"🎤 Received {len(data)} bytes")
                f.write(data)
        except Exception as e:
            print("❌ WebSocket closed:", e)
        finally:
            print(f"💾 Audio saved to {filename}")
