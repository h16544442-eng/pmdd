import json
import os
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Attempt to initialize Firebase Admin
try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import firestore
    
    # Initialize only if not already initialized
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-adminsdk.json")
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        if cred_json:
            import json as init_json
            cred_dict = init_json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            USE_FIREBASE = True
        elif os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            USE_FIREBASE = True
        else:
            USE_FIREBASE = False
            db = None
    else:
        USE_FIREBASE = True
        db = firestore.client()
except ImportError:
    USE_FIREBASE = False
    db = None

MEMORY_FILE = "data/episodic_memory.json"
COLLECTION_NAME = "episodic_memory"

def save_to_memory(corpus_name: str, analysis_data: Any):
    """
    Saves an analysis session to episodic memory.
    Supports Firebase Firestore for Vercel, with local fallback.
    """
    timestamp = time.time()
    
    if USE_FIREBASE and db is not None:
        try:
            doc_ref = db.collection(COLLECTION_NAME).document()
            doc_ref.set({
                "corpus_name": corpus_name,
                "timestamp": timestamp,
                "data": analysis_data
            })
            return
        except Exception as e:
            print(f"Firebase save error: {e}")
            # Fallback to local
            
    # Local fallback
    if not os.path.exists("data"):
        os.makedirs("data")
        
    memory = {}
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            try:
                memory = json.load(f)
            except json.JSONDecodeError:
                memory = {}
                
    if corpus_name not in memory:
        memory[corpus_name] = []
        
    memory[corpus_name].append({
        "timestamp": timestamp,
        "data": analysis_data
    })
    
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2)

def get_from_memory(corpus_name: str) -> Any:
    """
    Retrieves previous analysis data for a specific corpus.
    """
    if USE_FIREBASE and db is not None:
        try:
            docs = db.collection(COLLECTION_NAME).where("corpus_name", "==", corpus_name).stream()
            results = [doc.to_dict() for doc in docs]
            return results if results else None
        except Exception as e:
            print(f"Firebase read error: {e}")
            
    # Local fallback
    if not os.path.exists(MEMORY_FILE):
        return None
        
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        memory = json.load(f)
        
    return memory.get(corpus_name)

def get_all_experiences() -> str:
    """
    Summarizes all previous analytical experiences for the Agent's Brain.
    Pulls from Firebase if available, otherwise local file.
    """
    summary = "Previous Experiences Summary:\n"
    
    if USE_FIREBASE and db is not None:
        try:
            docs = db.collection(COLLECTION_NAME).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20).stream()
            has_data = False
            for doc in docs:
                data = doc.to_dict()
                summary += f"- Lesson from {data.get('corpus_name', 'Unknown')}: {data.get('data', {}).get('lesson', 'No specific lesson recorded.')}\n"
                has_data = True
            
            if not has_data:
                return "No previous analysis data available."
            return summary
        except Exception as e:
            print(f"Firebase read error: {e}")
            
    # Local fallback
    if not os.path.exists(MEMORY_FILE):
        return "No previous analysis data available."
        
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        memory = json.load(f)
        
    for name, history in memory.items():
        if isinstance(history, list):
            for entry in history:
                lesson = entry.get('data', {}).get('lesson', '')
                if lesson:
                    summary += f"- Lesson from {name}: {lesson}\n"
        elif isinstance(history, dict):
            lesson = history.get('data', {}).get('lesson', '')
            if lesson:
                summary += f"- Lesson from {name}: {lesson}\n"
    
    return summary
