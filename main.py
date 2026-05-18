from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
import os
import shutil
import uuid
import json
from dotenv import load_dotenv

# Import our agents
from agents.agent1_preprocessor import run_agent1
from agents.agent2_pragmatic import run_agent2
from agents.agent3_semantic import run_agent3
from agents.agent4_statistics import run_agent4
from agents.agent5_orchestrator import run_agent5

load_dotenv()

app = FastAPI(title="PMDD Professional API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for analysis status and context
analysis_sessions = {}

def is_valid_key(key: str | None) -> bool:
    return bool(key and key.strip() and key != "your_api_key_here")

def preview_key(key: str | None) -> str | None:
    return f"{key[:7]}...{key[-4:]}" if key and len(key) > 12 else None

def get_api_key_for_session(session: dict) -> str:
    key = session.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not key or key == "your_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not active. Enter and activate an API key before running agents.",
        )
    return key

def get_session_or_404(session_id: str):
    session = analysis_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

def agent_error(message: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail=message)

@app.get("/config/api-key-status")
async def get_api_key_status():
    key = os.getenv("OPENAI_API_KEY")
    return {
        "is_configured": is_valid_key(key),
        "key_preview": preview_key(key)
    }

@app.post("/session/create")
async def create_session():
    session_id = str(uuid.uuid4())
    analysis_sessions[session_id] = {
        "corpus_name": "",
        "file_path": "",
        "a1_result": None,
        "a2_result": None,
        "a3_result": None,
        "a4_result": None,
        "report": None,
        "pdf_url": None,
        "api_key": None,
        "api_key_active": False,
        "api_key_preview": None,
        "logs": ["Session initialized."]
    }
    return {"session_id": session_id}

@app.post("/session/{session_id}/api-key")
async def activate_session_api_key(session_id: str, api_key: str = Form(...)):
    session = get_session_or_404(session_id)
    api_key = api_key.strip()
    if not is_valid_key(api_key):
        agent_error("Enter a valid OpenAI API key.", status_code=400)

    try:
        OpenAI(api_key=api_key).models.list()
    except Exception as e:
        session["api_key_active"] = False
        session["api_key_preview"] = None
        session["logs"].append("OpenAI API key activation failed.")
        agent_error(f"API key is not active: {str(e)}", status_code=401)

    session["api_key"] = api_key
    session["api_key_active"] = True
    session["api_key_preview"] = preview_key(api_key)
    session["logs"].append("OpenAI API key is active for this session.")
    return {
        "active": True,
        "key_preview": session["api_key_preview"],
        "message": "API key is active."
    }

@app.post("/session/{session_id}/upload")
async def upload_file_to_session(session_id: str, file: UploadFile = File(...)):
    session = get_session_or_404(session_id)
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{session_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    session["file_path"] = file_path
    session["logs"].append(f"File uploaded: {file.filename}")
    return {"status": "success", "file_path": file_path}

@app.post("/agent/1/{session_id}")
async def start_agent1(session_id: str):
    session = get_session_or_404(session_id)
    api_key = get_api_key_for_session(session)
    if not session or not session["file_path"]:
        agent_error("No file uploaded for this session")
    
    session["logs"].append(">>> Agent 1: Starting Preprocessing...")
    result = run_agent1(session["file_path"], api_key=api_key)
    print(f"DEBUG Agent 1 Result: {result}")
    
    if "error" in result:
        session["logs"].append(f"Agent 1 Error: {result['error']}")
        agent_error(result["error"], status_code=502)

    session["a1_result"] = result
    
    # Handle both old and new result formats for log message
    count = result.get('total_segments', len(result.get('segments', [])))
    session["logs"].append(f"Agent 1 Complete. Found {count} segments.")
    return result

@app.post("/agent/2/{session_id}")
async def start_agent2(session_id: str, limit: int = 5):
    session = get_session_or_404(session_id)
    api_key = get_api_key_for_session(session)
    if not session or not session.get("a1_result") or "segments" not in session["a1_result"]:
        agent_error("Agent 1 must be run successfully first")
    
    session["logs"].append(f">>> Agent 2: Starting Pragmatic Analysis (Limit: {limit})...")
    
    try:
        result = run_agent2(session["a1_result"]["segments"], limit=limit, api_key=api_key)
        if "error" in result:
            session["logs"].append(f"Agent 2 Error: {result['error']}")
            agent_error(result["error"], status_code=502)
            
        session["a2_result"] = result
        session["logs"].append("Agent 2 Complete.")
        return result
    except Exception as e:
        session["logs"].append(f"Agent 2 System Error: {str(e)}")
        agent_error(str(e), status_code=502)

@app.post("/agent/3/{session_id}")
async def start_agent3(session_id: str, limit: int = 5):
    session = get_session_or_404(session_id)
    api_key = get_api_key_for_session(session)
    if not session or not session.get("a2_result"):
        agent_error("Agent 2 must be run successfully first")
    
    session["logs"].append(f">>> Agent 3: Starting Semantic Detection (Limit: {limit})...")
    
    try:
        result = run_agent3(session["a2_result"], limit=limit, api_key=api_key)
        if "error" in result:
            session["logs"].append(f"Agent 3 Error: {result['error']}")
            agent_error(result["error"], status_code=502)
            
        session["a3_result"] = result
        count = len(result.get('segments', []))
        session["logs"].append(f"Agent 3 Complete. Processed {count} segments.")
        return result
    except Exception as e:
        session["logs"].append(f"Agent 3 System Error: {str(e)}")
        agent_error(str(e), status_code=502)

@app.post("/agent/4/{session_id}")
async def start_agent4(session_id: str):
    session = get_session_or_404(session_id)
    api_key = get_api_key_for_session(session)
    if not session or not session.get("a1_result") or "segments" not in session["a1_result"]:
        agent_error("Agent 1 must be run successfully first")
    
    session["logs"].append(">>> Agent 4: Starting Statistical Analysis...")
    
    try:
        result = run_agent4(session["a1_result"]["segments"], api_key=api_key)
        if "error" in result:
            session["logs"].append(f"Agent 4 Error: {result['error']}")
            agent_error(result["error"], status_code=502)
            
        session["a4_result"] = result
        session["logs"].append(f"Agent 4 Complete. Analyzed {result.get('tokens_processed', 0)} tokens.")
        return result
    except Exception as e:
        session["logs"].append(f"Agent 4 System Error: {str(e)}")
        agent_error(str(e), status_code=502)

@app.post("/agent/5/{session_id}")
async def start_agent5_orchestrator(session_id: str, corpus_name: str = "Analysis"):
    session = get_session_or_404(session_id)
    api_key = get_api_key_for_session(session)
    if not all([session["a1_result"], session["a2_result"], session["a3_result"], session["a4_result"]]):
        agent_error("All preceding agents must be run first")
    
    session["logs"].append(">>> Agent 5: Orchestrating Final Report...")
    report_text, pdf_path, synthesis_data = run_agent5(
        corpus_name, 
        session["a1_result"], 
        session["a2_result"], 
        session["a3_result"], 
        session["a4_result"],
        api_key=api_key
    )
    if not pdf_path and report_text.startswith("Synthesis failed:"):
        session["logs"].append(report_text)
        agent_error(report_text, status_code=502)
    session["report"] = report_text
    session["pdf_url"] = pdf_path
    session["logs"].append("Agent 5 Complete. Report synthesized.")
    return {"report": report_text, "pdf_url": pdf_path}

@app.get("/session/check-key")
async def check_key():
    key = os.getenv("OPENAI_API_KEY")
    return {"configured": is_valid_key(key)}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    return analysis_sessions.get(session_id, {"error": "Not found"})

@app.get("/download/{filename:path}")
async def download_file(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=10001)
