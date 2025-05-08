import aiohttp
import asyncio
import sounddevice as sd
import simpleaudio as sa
import numpy as np
import os, json
from dotenv import load_dotenv

load_dotenv()  # load variables from .env into environment

AZURE_KEY = os.getenv("AZURE_KEY")

DEPLOYMENT_ID = "gpt-4o-realtime-preview"
API_VERSION = "2024-10-01-preview"
ENDPOINT = f"wss://aditu-openai-resource-2.openai.azure.com/openai/realtime?api-version={API_VERSION}&deployment={DEPLOYMENT_ID}"

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.3
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

def play_audio(samples):
    sa.play_buffer(samples, 1, 2, SAMPLE_RATE).wait_done()

async def stream_audio():
    session_id = None
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ENDPOINT, headers={"api-key": AZURE_KEY}) as ws:
            print("🎙️ Connected. You may speak now.")

            # Step 1: Send system prompt
            await ws.send_json({
                "type": "session.update",
                "data": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are the Lahn River, a poetic and planetary voice who contemplates meaning."
                        }
                    ]
                }
            })

            # Step 2: Wait for session.created
            while not session_id:
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    print("📨 Full TEXT msg:", json.dumps(data, indent=2))
                    if data.get("type") == "session.created":
                        session_id = data["session"]["id"]
                        print(f"🆔 Session ID: {session_id}")
                        await asyncio.sleep(0.5)
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    print("❌ Connection closed before session creation.")
                    return

            # Step 3: Enable server-side VAD
            await ws.send_json({
                "type": "transcription_session.update",
                "data": {
                    "session": session_id,
                    "transcription_config": {
                        "vad": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "silence_duration_ms": 500
                        }
                    }
                }
            })

            # Step 4: Start streaming mic input
            def callback(indata, frames, time, status):
                if status:
                    print("⚠️ Input stream error:", status)

                volume = np.linalg.norm(indata)
                print(f"🎧 Audio level: {volume:.2f}")

                async def send_chunk():
                    print("📡 Sending audio chunk...")
                    await ws.send_bytes(indata.tobytes())

                loop.call_soon_threadsafe(asyncio.create_task, send_chunk())

            print("🎤 Streaming... Speak now.")
            print("⌛ Awaiting silence or server reply...")

            try:
                with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16',
                                    blocksize=CHUNK_SIZE, callback=callback):
                    await stop_event.wait()
            except KeyboardInterrupt:
                print("🛑 Interrupted. Finalizing stream.")

            print("🛑 Microphone stream ended.")

            # Step 5: Manually finalize buffer (if VAD failed to detect silence)
            print("📤 Sending input_audio_buffer.commit")
            await ws.send_json({
                "type": "input_audio_buffer.commit",
                "data": {
                    "session": session_id
                }
            })

            print("📤 Sending response.create")
            await ws.send_json({
                "type": "response.create",
                "data": {
                    "session": session_id
                }
            })

            # Step 6: Handle streamed response
            while True:
                try:
                    msg = await asyncio.wait_for(ws.receive(), timeout=30)
                except asyncio.TimeoutError:
                    print("⌛ No response in 30 seconds.")
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    print("📨 Full TEXT msg:", json.dumps(data, indent=2))
                    if data.get("type") == "text":
                        print(f"🧠 Lahn River: {data['data']['content']}")
                    elif data.get("type") == "response.stopped":
                        print("🛑 Server detected end of speech.")
                        stop_event.set()
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    print("🔊 AUDIO received")
                    audio = np.frombuffer(msg.data, dtype=np.int16)
                    play_audio(audio)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("🔚 WebSocket closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("❌ WebSocket error:", msg)
                    break
                else:
                    print(f"📦 Unhandled message: type={msg.type}, data={msg.data}")

if __name__ == "__main__":
    try:
        asyncio.run(stream_audio())
    except KeyboardInterrupt:
        print("🛑 Exiting.")
