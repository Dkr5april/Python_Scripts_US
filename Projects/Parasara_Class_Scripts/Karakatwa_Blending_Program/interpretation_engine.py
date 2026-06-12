import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- SETTINGS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge_base")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Selection Lists
RASIS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

def get_selection(options, prompt):
    print(f"\nSelect {prompt} (Enter numbers separated by commas):")
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
    choice = input(">> ")
    return ", ".join([options[int(c.strip()) - 1] for c in choice.split(',') if c.strip().isdigit()])

def sync_knowledge():
    if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"\n[!] ERROR: Folder '{KNOWLEDGE_DIR}' not found. Please create it.")
        return

    db = Chroma(persist_directory=DB_DIR, embedding_function=EMBEDDING_MODEL)
    
    if len(db.get()['ids']) == 0:
        print("\n--- Initializing Library (Syncing knowledge)... ---")
        documents = []
        for filename in os.listdir(KNOWLEDGE_DIR):
            if filename.lower().endswith(('.txt', '.pdf')):
                print(f"Reading: {filename}")
                path = os.path.join(KNOWLEDGE_DIR, filename)
                try:
                    loader = TextLoader(path, encoding='utf-8') if filename.endswith('.txt') else PyPDFLoader(path)
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Could not read {filename}: {e}")
        
        if documents:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.split_documents(documents)
            Chroma.from_documents(docs, EMBEDDING_MODEL, persist_directory=DB_DIR)
            print("--- Sync complete. Engine ready! ---")

def get_interpretation():
    sync_knowledge()
    print("\n" + "="*40 + "\n      VEDIC ASTROLOGY ENGINE      \n" + "="*40)
    
    rasi = get_selection(RASIS, "Rasi")
    bhava = input("Enter Bhava (1-12): ")
    planets = get_selection(PLANETS, "Planets")
    event = input("\nEnter the life event/topic: ")
    
    query = f"Topic: {event}. Rasi: {rasi}. House: {bhava}. Planets: {planets}."
    
    db = Chroma(persist_directory=DB_DIR, embedding_function=EMBEDDING_MODEL)
    results = db.similarity_search(query, k=3)
    
    print(f"\n--- Analysis for {event} ---")
    for i, doc in enumerate(results):
        print(f"\n[Perspective {i+1}]:\n{doc.page_content.strip()}")
    print("\n" + "="*40)

if __name__ == "__main__":
    while True:
        get_interpretation()
        if input("\nRun another query? (y/n): ").lower() != 'y':
            break