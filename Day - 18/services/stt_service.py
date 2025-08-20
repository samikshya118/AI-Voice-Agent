import asyncio
import json
import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingError,
    TurnEvent,
    TerminationEvent,
    BeginEvent,
    StreamingParameters,
)

async def stream_transcription(websocket, audio_queue: asyncio.Queue, api_key: str):
    aai.settings.api_key = api_key

    client = StreamingClient(
        StreamingClientOptions(api_key=api_key, api_host="streaming.assemblyai.com")
    )

    transcripts_queue: asyncio.Queue = asyncio.Queue()

    def on_begin(c, event: BeginEvent):
        print(f"🔵 Session started: {event.id}")

    def on_turn(c, event: TurnEvent):
        if event.transcript.strip():
            # send transcript with end_of_turn if final
            data = {
                "transcript": event.transcript,
                "end_of_turn": getattr(event, "is_final", False)
            }
            transcripts_queue.put_nowait(json.dumps(data))
            print(f"📝 Transcript: {event.transcript}")

    def on_terminated(c, event: TerminationEvent):
        print(f"🔴 Session terminated: {event.audio_duration_seconds} sec")

    def on_error(c, error: StreamingError):
        print(f"❌ Error: {error}")

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    client.connect(StreamingParameters(sample_rate=16000, format_turns=True))
    print("🔌 Connected to AssemblyAI Streaming API")

    async def send_transcriptions():
        try:
            while True:
                transcript = await transcripts_queue.get()
                await websocket.send_text(transcript)
        except asyncio.CancelledError:
            pass

    sender_task = asyncio.create_task(send_transcriptions())

    try:
        while True:
            data = await audio_queue.get()
            if data is None:
                client.disconnect(terminate=True)
                break
            client.stream(data)
    finally:
        sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass
