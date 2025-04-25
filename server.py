from flask import Flask, request, jsonify
from flask_cors import CORS
from avatar import get_llm, build_or_load_index
from llama_index.core.memory import ChatMemoryBuffer

# === Initialize Flask ===
app = Flask(__name__)
CORS(app)  # Enable CORS so frontend can call backend

# === Load LLM + Index once on startup ===
llm = get_llm("mistral-large-instruct")  # or dynamically choose
index = build_or_load_index(llm)
memory = ChatMemoryBuffer.from_defaults(token_limit=2000)
chat_engine = index.as_chat_engine(chat_mode="context", memory=memory)
print('LLM initialized.')

@app.route("/api/chat", methods=["POST"])
def chat():
    print('Chat request recieved.')
    data = request.get_json()
    prompt = data.get("prompt", "")

    if prompt == "__INIT__":
        prompt = "Hallo"  # Use this as the initial system-opening input

    if not prompt:
        return jsonify({"reply": "Please say something."}), 400

    print('User message: ', prompt)

    response = chat_engine.chat(prompt)

    print('Avatar response: ', response.response)

    return jsonify({"reply": response.response})

if __name__ == "__main__":
    app.run(debug=True)

