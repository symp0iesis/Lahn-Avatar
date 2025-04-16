import os
import subprocess
import datetime
from rich.console import Console

# Updated imports for latest LlamaIndex
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.settings import Settings

from gwdg_llm import GWDGChatLLM #GWDGLLM


# === CONFIG ===
DRIVE_FOLDER_ID = "1vT4UTYHeFxS5Vy2u_OfQyQ6cQ-cP5Ywd"
API_KEY = "sk-db54dbb552054e77ada3334b9736cfb3"
API_BASE = "https://llm.hrz.uni-giessen.de/api"
DATA_DIR = "./data"
LOG_DIR = "./chat_logs"
STORAGE_DIR = "./lahn_index"


# === DOWNLOAD DOCS ===
def download_drive_folder(folder_id, output_dir="./data"):
    os.makedirs(output_dir, exist_ok=True)
    cmd = f"gdown --folder https://drive.google.com/drive/folders/{folder_id} -O {output_dir}"
    subprocess.run(cmd, shell=True)

# === LLM SETUP ===
def select_model():
    print("Choose a model:")
    print("1. Mistral")
    print("2. SauerKrautLM (Llama finetuned on German data)")
    choice = input("Enter 1 or 2: ")
    if choice == "2":
        return "llama-3.1-sauerkrautlm-70b-instruct" 
    return "mistral-large-instruct"

def get_llm(model_name: str):

    # llm = GWDGLLM(model="llama-3.1-8b-instruct", api_key=API_KEY, base_url=API_BASE)

    llm = GWDGChatLLM(
        model=model_name,
        api_base=API_BASE,
        api_key=API_KEY,
        temperature=0.7
    )

    return llm

# === LOGGING SETUP ===
def create_session_log():
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return open(os.path.join(LOG_DIR, f"session_{timestamp}.txt"), "w")

# === INDEX BUILDER / LOADER ===
def build_or_load_index(llm, refresh=False):
    Settings.llm = llm
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    index_ready = (
        os.path.exists(STORAGE_DIR)
        and os.path.exists(os.path.join(STORAGE_DIR, "docstore.json"))
        and os.path.exists(os.path.join(STORAGE_DIR, "index_store.json"))
    )

    if index_ready and not refresh:
        print('Loading index from storage...')
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        return load_index_from_storage(storage_context)
    else:
        if refresh:
            print('Refreshing from Google Drive...')
            download_drive_folder(DRIVE_FOLDER_ID, DATA_DIR)

        print('Creating Vector store from data sources...')
        documents = SimpleDirectoryReader(DATA_DIR, recursive=True).load_data()

        index = VectorStoreIndex.from_documents(
            documents
        )
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        return index


# === MAIN ===
def main():
    console = Console()
    console.print("[bold cyan]Lahn River AI Avatar[/bold cyan]\n")

    refresh = input("Refresh knowledge base from Google Drive? (y/n): ").strip().lower() == "y"

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
    console.print("📁 Chat session saved.")

if __name__ == "__main__":
    main()
