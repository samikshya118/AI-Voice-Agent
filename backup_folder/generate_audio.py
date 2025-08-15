from murf import Murf

client = Murf(api_key="ap2_d8202915-9586-49ec-b1c4-ec317860390f")

res = client.text_to_speech.generate(
    text="Hello, this is a test from Murf AI",
    voice_id="en-US-terrell"  # Use a valid voice_id
)

print("🎧 Audio URL:", res.audio_file)

