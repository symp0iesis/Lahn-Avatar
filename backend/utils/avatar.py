import os
import subprocess
import datetime, requests
from rich.console import Console
from docx import Document
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import hashlib
import re
from dotenv import load_dotenv

from youtube_transcript_api import YouTubeTranscriptApi
from llama_index.core.schema import Document as LlamaDocument

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.settings import Settings
from llama_index.readers.web import SimpleWebPageReader

from llama_index.llms.azure_openai import AzureOpenAI
# from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike
from llama_index.callbacks import CallbackManager, LLMLogger

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .gwdg_llm import GWDGChatLLM, GWDGEmbedding, HrzOpenAI


load_dotenv()


# === CONFIG ===
DRIVE_FOLDER_ID = "1vT4UTYHeFxS5Vy2u_OfQyQ6cQ-cP5Ywd"
API_KEY = os.getenv("GWDG_API_KEY") 
API_BASE = os.getenv("GWDG_API_BASE")

AZURE_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_KEY = os.getenv("AZURE_CHAT_KEY")
AZURE_BASE = os.getenv("AZURE_API_BASE")

# base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = "./data" #os.path.join(base_dir, "/data")

# print('Base dir: ', base_dir, 'Data dir: ', DATA_DIR)
LOG_DIR = "./chat_logs" #os.path.join(base_dir, "/chat_logs")
STORAGE_DIR = "./lahn_index"#os.path.join(base_dir, "/lahn_index")


def download_drive_folder(folder_id, output_dir="./data"):
    print('Running download_drive_folder function...')
    os.makedirs(output_dir, exist_ok=True)
    cmd = f"gdown --folder https://drive.google.com/drive/folders/{folder_id} -O {output_dir}"
    subprocess.run(cmd, shell=True)


def fetch_system_prompt_from_gdoc():
    print(' Updating system prompt...')
    url = "https://docs.google.com/document/d/1NYOOy8KkaLDBwvHvEVg1hVDY5yvHeLACUpCEkJVM8Kw/export?format=txt"
    response = requests.get(url)
    response.raise_for_status()
    prompt = response.text.strip()
    prompt = prompt[:prompt.find('General Internal Impressions')]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'system_prompt.txt')
    with open(file_path, 'w') as f:
        f.write(prompt)
    print(' Done.')


def convert_docx_to_txt_and_cleanup(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.docx') or '.' not in file:
                try:
                    doc = Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    txt_filename = os.path.splitext(file)[0] + '.txt'
                    txt_path = os.path.join(root, txt_filename)
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    os.remove(file_path)
                    print(f"✅ Converted and deleted: {file_path}")
                except Exception as e:
                    print(f"❌ Failed to convert {file_path}: {e}")


def fetch_youtube_transcript(url, languages=["de"]):
    print(f"🔗 Fetching: {url}")
    try:
        parsed = urlparse(url)

        # Handle standard and short YouTube URL formats
        if "youtube.com" in parsed.netloc:
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif "youtu.be" in parsed.netloc:
            video_id = parsed.path.lstrip("/")
        else:
            raise ValueError("Unrecognized YouTube URL format.")

        if not video_id or len(video_id) != 11:
            raise ValueError("Invalid YouTube video ID.")

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        full_text = " ".join([entry["text"] for entry in transcript])
        return LlamaDocument(text=full_text, metadata={"source": url})

    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None


def sanitize_filename(url):
    domain = urlparse(url).netloc
    hashed = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{domain.replace('.', '_')}_{hashed}.txt"


def select_model():
    print("Choose a model:")
    print("1. Mistral")
    print("2. SauerKrautLM (Llama finetuned on German data)")
    choice = input("Enter 1 or 2: ")
    return "llama-3.1-sauerkrautlm-70b-instruct" if choice == "2" else "mistral-large-instruct"


class DebugOpenAILike(OpenAILike):
    def chat(self, messages, **kwargs):
        print("\n=== PAYLOAD TO .chat() ===")
        print("Messages:")
        for m in messages:
            print(m)
        print("Other kwargs:")
        for k, v in kwargs.items():
            print(f"{k}: {v}")
        print("==========================\n")
        return super().chat(messages, **kwargs)


callback_manager = CallbackManager([LLMLogger()])


def get_llm(model_name=None, system_prompt=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'system_prompt.txt')
    if system_prompt == None:
        system_prompt = open(file_path, 'r').read()

    if model_name != None:

        llm = DebugOpenAILike(
            model=model_name,           # your custom model
            api_base=API_BASE,                # HRZ endpoint
            api_key=API_KEY,
            is_chat_model=True,               # it uses the chat/completions endpoint
            is_function_calling_model=True,   # enable function/tool calling
            context_window=8192,              # set your real context size
            system_prompt=system_prompt,      
        )
        # Instantiate your LLM using the subclass:
        # return HrzOpenAI(
        #     model=model_name,
        #     system_prompt=system_prompt,
        #     temperature=0.7,
        #     api_key=API_KEY,
        #     api_base=API_BASE,
        #     api_type="open_ai",
        #     api_version="",
        #     deployment_id=model_name,
        # )

        # return OpenAI(
        #     model=model_name,        # your HRZ model name
        #     temperature=0.7,
        #     system_prompt=system_prompt,

        #     # point at your custom endpoint:
        #     api_key=API_KEY,             # e.g. 'sk-…'
        #     api_base=API_BASE,           # "https://llm.hrz.uni-giessen.de/api/"
        #     api_type="open_ai",          # use the “open_ai” protocol
        #     api_version=None,            # leave None unless your server needs a version
        # )


        # GWDGChatLLM(
        #     model=model_name,
        #     api_base=API_BASE,
        #     api_key=API_KEY,
        #     temperature=0.7,
        #     system_prompt=system_prompt
        # )

    else:
        llm = AzureOpenAI(
            model="gpt-4o",
            engine="gpt-4o",
            deployment_name="gpt-4o",
            api_version=AZURE_VERSION,  
            api_key= AZURE_KEY, 
            azure_endpoint= AZURE_BASE,
            system_prompt=system_prompt,
            callback_manager=callback_manager
        )

    print('LLM details: ', llm.model_dump())

    Settings.llm = llm

    return llm, system_prompt


def create_session_log():
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return open(os.path.join(LOG_DIR, f"session_{timestamp}.txt"), "w")

def build_index():

    print('Refreshing from Google Drive...')
    download_drive_folder(DRIVE_FOLDER_ID, DATA_DIR)
    convert_docx_to_txt_and_cleanup(DATA_DIR)

    print('Creating Vector store from data sources...')
    documents = SimpleDirectoryReader(DATA_DIR, recursive=True).load_data()

    links_path = Path(DATA_DIR) / "General_News/Online News (Links).txt"
    if links_path.exists():
        with open(links_path, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        web_reader = SimpleWebPageReader()
        for url in urls:
            try:
                print(f"🔗 Fetching: {url}")
                if "youtube.com" in url or "youtu.be" in url:
                    doc = fetch_youtube_transcript(url)
                else:
                    docs = web_reader.load_data([url])
                    full_text = "\n\n".join(doc.text for doc in docs)
                    doc = LlamaDocument(text=full_text, metadata={"source": url})

                if doc:
                    filename = sanitize_filename(url)
                    filepath = Path(DATA_DIR) / "General_News/scraped_texts" / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(doc.text)
                    print(f"✅ Saved to {filepath}")
            except Exception as e:
                print(f"❌ Failed to fetch {url}: {e}")

    scraped_documents = SimpleDirectoryReader(str(Path(DATA_DIR) / "General_News/scraped_texts")).load_data()
    documents += scraped_documents

    experiences_folder_is_empty = not os.listdir(str(Path(DATA_DIR) / "uploaded_experiences/text"))
    if not experiences_folder_is_empty:
        user_experiences = SimpleDirectoryReader(str(Path(DATA_DIR) / "uploaded_experiences/text")).load_data()
        documents += user_experiences

    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    print('Done')

    return index



def build_or_load_index(llm, refresh=False):
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    # GWDGEmbedding(
    #     api_key=API_KEY,
    #     api_base=API_BASE,
    #     model="e5-mistral-7b-instruct"
    # )

    index_ready = (
        os.path.exists(STORAGE_DIR)
        and os.path.exists(os.path.join(STORAGE_DIR, "docstore.json"))
        and os.path.exists(os.path.join(STORAGE_DIR, "index_store.json"))
    )

    if index_ready and not refresh:
        print('Loading index from storage...')
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        return load_index_from_storage(storage_context)

    #Index needs to be built and loaded
    index = build_index()
    
    return index


def main():
    console = Console()
    console.print("[bold cyan]Lahn River AI Avatar[/bold cyan]\n")

    refresh = input("Refresh Knowledge Base and System Prompt from Google Drive? (y/n): ").strip().lower() == "y"

    if refresh:
        fetch_system_prompt_from_gdoc()

    model_name = select_model()
    llm = get_llm(model_name)

    console.print("\U0001F4DA Preparing vector index...")
    index = build_or_load_index(llm, refresh=refresh)

    memory = ChatMemoryBuffer.from_defaults(token_limit=2000)
    chat_engine = index.as_chat_engine(chat_mode="context", memory=memory)

    console.print("✅ Ready to chat!\n")
    console.print(f"[bold green]Lahn River (Model: {model_name})[/bold green]")
    console.print("Type 'exit' to quit.\n")

    log_file = create_session_log()

    while True:
        user_input = input("[You]: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response = chat_engine.chat(user_input)
        console.print(f"[Lahn River]: {response.response}")
        log_file.write(f"You: {user_input}\nLahn River: {response.response}\n\n")

    log_file.close()
    console.print("\U0001F4C1 Chat session saved.")


if __name__ == "__main__":
    main()
