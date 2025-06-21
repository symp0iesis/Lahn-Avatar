from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, io, asyncio
from datetime import datetime

# from llama_index.core import Settings
from llama_index.core.tools.query_engine import QueryEngineTool

from utils.avatar import get_llm, build_index, build_or_load_index, fetch_system_prompt_from_gdoc
from utils.utils import whisper_processor, whisper_model, transcribe_audio, azure_speech_response_func, LahnSensorsTool

import os

# === Initialize Flask ===
app = Flask(__name__)
CORS(app, supports_credentials=True)

UPLOAD_DIR = "data/uploaded_experiences"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Load LLM once at startup ===
llm_choice = "gemma-3-27b-it" #"hrz-chat-small" #"gemma-3-27b-it" #"mistral-large-instruct" #"hrz-chat-small"

llm, system_prompt = get_llm('openai', llm_choice)

# print('LLM metadata model name: ', llm.metadata.model_name)

# agent=True
query_llm, _ = get_llm('gwdg', "hrz-chat-small", system_prompt= 'Provide an accurate response to the given query:')

api_tool = QueryEngineTool.from_defaults(
        query_engine=LahnSensorsTool(query_llm),
        name=LahnSensorsTool.name,
        description=LahnSensorsTool.description,
    )


def prepare_query_engine(refresh=False):
    global query_llm
    if refresh==True:
        index = build_index()
    else:
        index = build_or_load_index()

    # query_llm = get_llm('gwdg', "mistral-large-instruct", system_prompt= 'Provide an accurate response to the given query:')

    index_query_engine = index.as_query_engine(llm=query_llm,similarity_top_k=10)

    return index_query_engine


query_engine = prepare_query_engine()

debate_summary_llm, _= get_llm('gwdg', "mistral-large-instruct", system_prompt= '')
print('LLM initialized.')




@app.route("/api/refresh-prompt", methods=["POST"])
def refresh_prompt():
    global system_prompt, llm
    print('Refresh prompt request received.')
    fetch_system_prompt_from_gdoc()
    llm,  system_prompt = get_llm('openai', llm_choice)
    return 'Done.'



@app.route("/api/refresh-embeddings", methods=["POST"])
def refresh_embeddings():
    global query_engine
    print('Refresh embeddings request received.')
    query_engine = prepare_query_engine(refresh=True)
    return 'Done'



@app.route("/api/chat", methods=["POST"])
def chat():
    global llm, llm_choice, system_prompt
    print('Chat request received.')
    data = request.get_json()
    prompt = data.get("prompt", "")
    conversation = data.get("history", "")
    chat_history = []

    if prompt == "__INIT__":
        prompt = "Hallo"
        # chat_history=[{'role':'user', 'content':prompt}]

    elif not prompt: #Needed?
        return jsonify({"reply": "Please say something."}), 400


    else:
        chat_history = [
            {'role':"user" if m["sender"] == "user" else "assistant", 'content':m["text"]}
            for m in conversation
            ]

    chat_history.insert(0, {'role':'user', 'content':'Hallo'})
    chat_history.insert(0, {'role':'system', 'content':system_prompt})

    # print('Chat history: ', chat_history)

    # print('After adding system and user prompts: ', chat_history)

    # print('Chat history: ', chat_history)
    # print('model: ', llm_choice)



    chat_completion = llm.chat.completions.create(
          messages=chat_history,
          model= llm_choice,
          temperature=0.5
      )


    print('\nUser message:', prompt)
    response = chat_completion.choices[0].message.content
    print('Response: ', response)

    results = ''

    # if 'get_relevant_Lahn_context' in response:
    print('Obtaining information for the LLM...')
    # response = response[response.find('user_query="')+12:]
    query = prompt #response[:response.find('")')]
    # print('Query: ', query)
    context = query_engine.query(query).response
    print('Context: ', context)
    # results += '\nHere is the output of get_relevant_Lahn_context(): '+context

    chat_completion = llm.chat.completions.create(
          messages=chat_history+[{'role':'system', 'content':'Here is relevant information about the Lahn: '+context + ' . You can call get_relevant_Lahn_context() if environmental data readings are relevant to the user\'s query.'}],
          model= llm_choice,
      )

    response = chat_completion.choices[0].message.content



    # if 'get_relevant_Lahn_context' in response:
    #     print('Fetching relevant Lahn context...')
    #     response = response[response.find('user_query="')+12:]
    #     query = response[:response.find('")')]
    #     print('Query: ', query)
    #     context = query_engine.query(query).response
    #     print('Context: ', context)
    #     results += '\nHere is the output of get_relevant_Lahn_context(): '+context



    if 'analyze_sensor_data' in response:
        print('Analyzing sensor data...')
        response = response[response.find('user_query="')+12:]
        query = response[:response.find('")')]
        print('Query: ', query)
        analysis = str(api_tool(query))
        print('Analysis: ', analysis)
        results += '\nHere is the output of analyze_sensor_data(): '+analysis

    if len(results)>0:
        chat_completion = llm.chat.completions.create(
              messages=chat_history+[{'role':'system', 'content':results}],
              model= llm_choice,
          )

    response = chat_completion.choices[0].message.content

    print('Avatar response:', response)

    return jsonify({"reply": response})



@app.route("/api/debate-summary", methods=["POST"])
def debate_summary():
    print('Debate Summary request received.')
    data = request.get_json()
    conversation = data.get("history", "")
    topic = data.get("topic", "")
    summary = data.get("summary", "")

    formatted_history = format_history_as_string(conversation)

    prompt = f"""This is a debate between a human and an AI avatar for the Lahn river. Your job is to provide a summary outline in the format
            "Lahn:<Lahn's Central Perspective>\nPro:<Central Pro>\nCon:<Central Con of Lahn's perspective (deduced by you)>\n\nYou:<User's Central Perspective>\nPro:<Central Pro>\nCon:<Central Con of User's perspective (deduced by you)>", briefly outlining the Lahn's primary perspective, a pro and con of that perspective, the user's perspective
            and a pro and con of that as well. Keep all content very brief. You're summarizing, not re-iterating. You are provided with the most recent debate summary. If it already contains content, iterate on that content to reflect recent updates to the conversation.
            Topic being debated: {topic}

            Conversation:
            {formatted_history}

            Existing summary:
            {summary}

            Respond with an updated version of the summary in the described format. Make sure to preserve the specified formatting in the template "Lahn:\nPro:\nCon:\n\nYou:\nPro:\nCon:". No extra characters. The contents of your response should ba based purely on the given summary. 
            Summaries for 'Lahn' and 'User'should be based purely on what they said. If any party is yet to contribute to the conversation, leave their summary blank, as in the template."""

    response = debate_summary_llm.complete(prompt) #chat_engine.chat(prompt)
    # print('Summary model response: ', response)
    summary = str(response) #.choices[0].message.content

    # chat_history = [
    #     ChatMessage(role="user" if m["sender"] == "user" else "assistant", content=m["text"])
    #     for m in conversation
    #     ]

    # print('User message:', prompt)
    # response = chat_engine.chat(messages=chat_history)
    print('Summary:', summary)

    return jsonify({"summary": summary})



@app.route("/api/voice-chat", methods=["POST"])
def voice_chat():
    if "audio" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400

    audio_file = request.files["audio"]
    ext = audio_file.mimetype.split("/")[-1] 
    audio_path = 'data/temp.'+ext
    audio_file.save(audio_path)

    # audio_b64 = base64.b64encode(request.files["audio"].read()).decode()

    try:
        # run async function to get reply
        reply_text, reply_wav = asyncio.run(azure_speech_response_func(audio_path))
        # save reply to disk
        out_path = os.path.join("data", "reply.wav")
        with open(out_path, "wb") as f:
            f.write(reply_wav)
        return jsonify({
            "reply_text": reply_text,
            "reply_audio_url": "https://lahn-server.eastus.cloudapp.azure.com:5001/api/reply-audio"
        })
    except Exception as e:
        print("❌ Voice chat error:", e)
        return jsonify({"error": "Voice chat failed"}), 500
    finally:
        os.remove(audio_path)



@app.route("/api/reply-audio")
def reply_audio():
    # Serve the latest reply audio file
    audio_path = os.path.join("data", "reply.wav")
    if not os.path.exists(audio_path):
        return "", 404
    # Create response with CORS headers
    response = make_response(send_file(audio_path, mimetype="audio/wav"))
    response.headers["Access-Control-Allow-Origin"] = "*"  # or specify frontend origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response



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
    app.run(debug=True, use_reloader=False)
