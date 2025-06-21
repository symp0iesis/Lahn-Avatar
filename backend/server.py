from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, io, asyncio
from datetime import datetime

from llama_index.core.chat_engine.types import ChatMode
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
# from llama_index.core import Settings
from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.agent import ReActAgent
from llama_index.core.agent.workflow import FunctionAgent
# from llama_index.core.agent.runner.base import AgentRunner

from llama_index.core.agent import FunctionCallingAgent



from utils.avatar import get_llm, build_index, build_or_load_index, fetch_system_prompt_from_gdoc
from utils.utils import whisper_processor, whisper_model, transcribe_audio, azure_speech_response_func, format_history_as_string, LahnSensorsTool, NoMemory

import os

# === Initialize Flask ===
app = Flask(__name__)
CORS(app, supports_credentials=True)

UPLOAD_DIR = "data/uploaded_experiences"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Load LLM once at startup ===
llm_choice = "gemma-3-27b-it" #"hrz-chat-small" #"gemma-3-27b-it" #"mistral-large-instruct" #"hrz-chat-small"

llm, system_prompt = get_llm(llm_choice)

print('LLM metadata model name: ', llm.metadata.model_name)

# agent=True


from langchain.agents import Tool as LangChainTool

def llamaindex_tool_to_langchain(tool):
    return LangChainTool(
        name=tool.metadata.name,
        description=tool.metadata.description,
        func=lambda q: str(tool.query_engine.query(q)),
        return_direct=False,
    )


import openai

original_create = openai.resources.chat.completions.Completions.create

def patched_create(*args, **kwargs):
    print("\n🔍 Payload to LLM:\n", kwargs)
    return original_create(*args, **kwargs)

openai.resources.chat.completions.Completions.create = patched_create

def prepare_chat_engine(agent=True, refresh=False):
    global llm
    if refresh==True:
        index = build_index()
    else:
        index = build_or_load_index()


    no_memory = NoMemory()
    # memory = ChatMemoryBuffer.from_defaults(token_limit=2000)

    if agent==True:
        print('Agent == True')

        index_query_engine = index.as_query_engine(llm=llm,similarity_top_k=10)

        # Wrap that query engine in a QueryEngineTool:
        index_tool = QueryEngineTool.from_defaults(
            query_engine=index_query_engine,
            name="general_index",  
            description=(
                "Use this tool to obtain general context about the river from the indexed documents (news, study texts, etc.). "
                "It will retrieve and summarize relevant snippets from the RAG data sources. This grounds your responses in reliable context about the Lahn river."
                "If the user's message is not related to sensor readings from the user, use this tool to generate your response."
                "Even when their message involves sensor readings, use this tool to obtain historical context on the river, which is relevant to providing a Lahn-specific interpretation of those readings."
            ),
        )


        api_tool = QueryEngineTool.from_defaults(
            query_engine=LahnSensorsTool(llm),
            name=LahnSensorsTool.name,
            description=LahnSensorsTool.description,
        )

        # chat_engine = OpenAIAgent.from_tools(
        #     tools=[index_tool, api_tool], #], #
        #     llm=llm,
        #     # service_context=service_context,
        #     memory=no_memory,
        #     verbose=True,         # optionally see function‐call traces
        #     fallback_to_llm=False  # if the agent doesn’t think a tool is needed, just call LLM
        # )



        langchain_index_tool = llamaindex_tool_to_langchain(index_tool)
        langchain_api_tool = llamaindex_tool_to_langchain(api_tool)

        tools = [langchain_index_tool, langchain_api_tool]

        from langchain.chat_models import ChatOpenAI
        API_KEY = os.getenv("GWDG_API_KEY")

        from langchain.prompts.chat import (
            ChatPromptTemplate,
            SystemMessagePromptTemplate,
            HumanMessagePromptTemplate,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        llm = ChatOpenAI(
            model="gemma-3-27b-it",  # whatever you're using
            openai_api_base="https://llm.hrz.uni-giessen.de/api/",
            openai_api_key=API_KEY,
            temperature=0.5,
        )

        from langchain.agents import create_openai_functions_agent, AgentExecutor
        from langchain.chains import LLMChain

        # llm_chain = LLMChain(llm=llm, prompt=prompt)

        agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
        chat_engine = AgentExecutor(agent=agent, tools=tools, verbose=True)

        # from langchain.agents import initialize_agent, AgentType


        # chat_engine = initialize_agent(
        #     tools=tools,
        #     llm=llm,
        #     agent=AgentType.OPENAI_FUNCTIONS,
        #     verbose=True,
        #     memory=None,
        # )



        # chat_engine = FunctionCallingAgent.from_tools(
        #     tools=[index_tool, api_tool],
        #     llm=llm,
        #     verbose=True,
        #     memory=no_memory,
        #     system_prompt=system_prompt
        # )

        # chat_engine = AgentRunner.from_llm(
        #     tools=[index_tool, api_tool],    # <-- here’s where you pass your full list
        #     llm=llm,
        #     max_iterations=3,
        #     verbose=True,
        # )

        # chat_engine = index.as_chat_engine(
        #     chat_mode="best",      
        #     memory=no_memory,
        #     similarity_top_k=11,
        #     # toolkits=[index_tool, api_tool],
        #     # fallback_to_llm=True,
        #     verbose=True     
        # )

        # chat_engine = ReActAgent.from_tools(
        #     tools=[index_tool, api_tool], #], #
        #     llm=llm,
        #     # service_context=service_context,
        #     memory=no_memory,
        #     # max_iterations=3,
        #     # verbose=True,         # optionally see function‐call traces
        #     fallback_to_llm=True  # if the agent doesn’t think a tool is needed, just call LLM
        # )


    else:
        print('Agent == False')
        chat_engine = index.as_chat_engine(chat_mode="context", memory=no_memory, verbose=True) #, memory=memory)



    # tools = chat_engine.agent_worker._get_tools(None)
    # or, more semantically, pass in the agent’s state:
    # tools = chat_engine.agent_worker._get_tools(chat_engine.agent_worker.state)

    # print("Registered tools:")
    # for t in tools:
    #     print("Tool name:       ", t.metadata.name)
    #     print("Tool description:", t.metadata.description)
    #     print("—" * 40)

    

    return chat_engine


chat_engine = prepare_chat_engine()

debate_summary_llm, _ = get_llm("mistral-large-instruct", system_prompt= '')
print('LLM initialized.')




@app.route("/api/refresh-prompt", methods=["POST"])
def refresh_prompt():
    global system_prompt, chat_engine
    print('Refresh prompt request received.')
    fetch_system_prompt_from_gdoc()
    llm, system_prompt = get_llm(llm_choice)
    chat_engine = prepare_chat_engine()
    return 'Done.'



@app.route("/api/refresh-embeddings", methods=["POST"])
def refresh_embeddings():
    global chat_engine
    print('Refresh embeddings request received.')
    chat_engine = prepare_chat_engine(refresh=True)
    
    # index = build_index()
    # memory = ChatMemoryBuffer.from_defaults(token_limit=2000) #Do I need to define this afresh here?
    # chat_engine = index.as_chat_engine(chat_mode="context", memory=memory)
    return 'Done'



@app.route("/api/chat", methods=["POST"])
def chat():
    print('Chat request received.')
    data = request.get_json()
    prompt = data.get("prompt", "")
    conversation = data.get("history", "")

    if prompt == "__INIT__":
        prompt = "Hallo"
        chat_history=[]

    elif len(conversation) == 0:
        pass

    elif not prompt: #Needed?
        return jsonify({"reply": "Please say something."}), 400


    # print('User message:', prompt)
    # response = chat_engine.chat(messages=chat_history)

    else:
        # if agent==True:
        # chat_history = format_history_as_string(conversation)
        # else:
        #     # system = [ ChatMessage(role="system", content=system_prompt) ]
        #     # chat_history = system + 

        chat_history = [
            ChatMessage(role="user" if m["sender"] == "user" else "assistant", content=m["text"])
            for m in conversation
            ]
        
        # prompt = chat_history


    print('User message:', prompt)
    # response = chat_engine.chat(prompt)
    response = chat_engine.invoke({'input':prompt, 'chat_history': chat_history})
    print('Avatar response:', response["output"])

    return jsonify({"reply": response["output"]})



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
