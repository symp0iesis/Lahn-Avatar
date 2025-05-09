from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from avatar import get_llm, build_or_load_index
from llama_index.core.memory import ChatMemoryBuffer

# === Initialize Flask ===
app = Flask(__name__)
CORS(app, supports_credentials=True)

UPLOAD_DIR = "data/uploaded_experiences"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Load LLM once at startup ===
llm = get_llm("mistral-large-instruct")
index = build_or_load_index(llm)
memory = ChatMemoryBuffer.from_defaults(token_limit=2000)
chat_engine = index.as_chat_engine(chat_mode="context", memory=memory)
print('LLM initialized.')

# === Lazy Whisper model loading ===
whisper_model = None
whisper_processor = None
whisper_device = None

def transcribe_audio(file_path):
    global whisper_model, whisper_processor, whisper_device

    if whisper_model is None or whisper_processor is None:
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        import torch

        whisper_device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔄 Loading Whisper model on {whisper_device}...")
        whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-small")
        whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small").to(whisper_device)
        print("✅ Whisper model loaded.")

    import torchaudio
    import torch

    # Load and preprocess audio
    speech, sr = torchaudio.load(file_path)
    if sr != 16000:
        speech = torchaudio.functional.resample(speech, sr, 16000)
    input_features = whisper_processor(speech.squeeze(), sampling_rate=16000, return_tensors="pt").input_features.to(whisper_device)

    # Transcribe
    predicted_ids = whisper_model.generate(input_features)
    transcription = whisper_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription

@app.route("/api/chat", methods=["POST"])
def chat():
    print('Chat request received.')
    data = request.get_json()
    prompt = data.get("prompt", "")

    if prompt == "__INIT__":
        prompt = "Hallo"

    if not prompt:
        return jsonify({"reply": "Please say something."}), 400

    print('User message:', prompt)
    response = chat_engine.chat(prompt)
    print('Avatar response:', response.response)

    return jsonify({"reply": response.response})

@app.route("/api/experience-upload", methods=["POST"])
def experience_upload():
    print("Experience upload received.")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")

    os.makedirs(UPLOAD_DIR+'/text', exist_ok=True)
    # Save the text message (if any)
    text = request.form.get("text", "")
    if text.strip():
        with open(os.path.join(UPLOAD_DIR+'/text', f"{timestamp}_message.txt"), "w", encoding="utf-8") as f:
            f.write(text.strip())

    # Save and transcribe the uploaded audio file
    if "audio" in request.files:
        audio_file = request.files["audio"]
        if audio_file and audio_file.filename:
            safe_name = secure_filename(audio_file.filename)
            file_ext = os.path.splitext(safe_name)[1]
            audio_path = os.path.join(UPLOAD_DIR, f"{timestamp}_audio{file_ext}")
            audio_file.save(audio_path)

            try:
                transcript = transcribe_audio(audio_path)
                with open(os.path.join(UPLOAD_DIR+'/text', f"{timestamp}_transcript.txt"), "w", encoding="utf-8") as f:
                    f.write(transcript.strip())
                print("📝 Transcription saved.")
            except Exception as e:
                print("❌ Failed to transcribe:", e)
                return jsonify({"status": "error", "message": "Audio saved, but transcription failed."}), 500

    return jsonify({"status": "success", "message": "Experience saved."})

if __name__ == "__main__":
    app.run(debug=True)
