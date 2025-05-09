from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from avatar import get_llm, build_or_load_index
from llama_index.core.memory import ChatMemoryBuffer

# === Initialize Flask ===
app = Flask(__name__)
CORS(app)

# === Create directory if it doesn't exist ===
UPLOAD_DIR = "data/uploaded_experiences"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Load LLM + Index once on startup ===
llm = get_llm("mistral-large-instruct")
index = build_or_load_index(llm)
memory = ChatMemoryBuffer.from_defaults(token_limit=2000)
chat_engine = index.as_chat_engine(chat_mode="context", memory=memory)
print('LLM initialized.')

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

    # Generate a timestamp-based unique ID for storage
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")

    # Save the text message (if any)
    text = request.form.get("text", "")
    if text.strip():
        with open(os.path.join(UPLOAD_DIR, f"{timestamp}_message.txt"), "w", encoding="utf-8") as f:
            f.write(text.strip())

    # Save the uploaded audio file (if any)
    if "audio" in request.files:
        audio_file = request.files["audio"]
        if audio_file and audio_file.filename:
            safe_name = secure_filename(audio_file.filename)
            file_ext = os.path.splitext(safe_name)[1]
            audio_path = os.path.join(UPLOAD_DIR, f"{timestamp}_audio{file_ext}")
            audio_file.save(audio_path)

    return jsonify({"status": "success", "message": "Experience saved."})

if __name__ == "__main__":
    app.run(debug=True)
