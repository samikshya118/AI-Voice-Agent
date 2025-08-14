from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get the Murf API key from environment
MURF_API_KEY = os.getenv("MURF_API_KEY")

# Start FastAPI app
app = FastAPI()

# Define the expected input JSON format
class TextInput(BaseModel):
    text: str

# Define the endpoint
@app.post("/generate-audio/")
def generate_audio(data: TextInput):
    try:
        # Prepare and send the request to Murf API
        response = requests.post(
            "https://api.murf.ai/v1/speech/generate",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "api-key": MURF_API_KEY
            },
            json={
                "voice": "en-US-Wesley",  # You can replace this with any valid Murf voice ID
                "text": data.text
            }
        )

        # Handle error response
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Murf TTS failed")

        # Get the audio URL
        result = response.json()
        return { "audio_url": result.get("audio_url") }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
