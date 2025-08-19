import os
import requests

def text_to_speech(text: str, session_id: str) -> str:
    murf_api_key = os.getenv("MURF_API_KEY")
    output_path = f"generated/{session_id}.mp3"

    # Example Murf API call
    # Replace with actual Murf endpoint and payload
    response = requests.post(
        "https://api.murf.ai/v1/speech",
        headers={"Authorization": f"Bearer {murf_api_key}"},
        json={"text": text, "voice": "en-US"}
    )

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
