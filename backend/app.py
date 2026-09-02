import os
import sys
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from genai.rag_ingestion import process_file
from genai.chunk import get_documents_chunks
from genai.vector_store import add_to_databse
from genai.agent import run_mednexus_agent
from backend.database import (
    register_file_in_mongodb, get_all_patients, get_all_alerts, acknowledge_alert,
    create_user_account, find_user_by_email, save_chat_message,
    get_user_chat_sessions, get_chat_session_history
)
from backend.auth import hash_password, verify_password, generate_session_token

app = FastAPI(title="MedNexus AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str = "usr_default"
    user_query: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    hospital_id: str = "MED-2026"
    specialty: str = "General Medicine"

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
def read_root():
    return {"message": "Mednexus API is running"}

# --- AUTH ENDPOINTS ---
@app.post("/api/auth/signup")
def signup_clinician(req: SignupRequest):
    try:
        existing = find_user_by_email(req.email)
        if existing:
            raise HTTPException(status_code=400, detail="Account with this email already exists.")
            
        pwd_hash = hash_password(req.password)
        user_doc = create_user_account(
            name=req.name,
            email=req.email,
            password_hash=pwd_hash,
            hospital_id=req.hospital_id,
            specialty=req.specialty
        )
        token = generate_session_token(user_doc["user_id"])
        return {
            "status": "success",
            "token": token,
            "user": {
                "user_id": user_doc["user_id"],
                "name": user_doc["name"],
                "email": user_doc["email"],
                "hospital_id": user_doc["hospital_id"],
                "specialty": user_doc["specialty"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
def login_clinician(req: LoginRequest):
    try:
        user = find_user_by_email(req.email)
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
        token = generate_session_token(user["user_id"])
        return {
            "status": "success",
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "hospital_id": user.get("hospital_id", "MED-2026"),
                "specialty": user.get("specialty", "General Medicine")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PATIENT & ALERT ENDPOINTS ---
@app.get("/api/patients")
def fetch_patients():
    try:
        patients = get_all_patients()
        return {"status": "success", "patients": patients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
def fetch_alerts():
    try:
        alerts = get_all_alerts()
        return {"status": "success", "alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts/{alert_id}/acknowledge")
def mark_alert_acknowledged(alert_id: str):
    try:
        success = acknowledge_alert(alert_id)
        return {"status": "success" if success else "failed", "acknowledged": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PERSISTENT CHAT ENDPOINTS ---
@app.get("/api/chat/sessions")
def fetch_chat_sessions(user_id: str = "usr_default"):
    try:
        sessions = get_user_chat_sessions(user_id)
        return {"status": "success", "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}")
def fetch_chat_history(session_id: str):
    try:
        messages = get_chat_session_history(session_id)
        return {"status": "success", "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    try:
        print(f"Received message from {request.user_id} in {request.session_id}: {request.user_query}")
        
        # Save user message to persistent MongoDB session
        save_chat_message(
            session_id=request.session_id,
            user_id=request.user_id,
            role="user",
            content=request.user_query
        )

        # Run Agentic Reasoning Loop
        ai_response = run_mednexus_agent(
            session_id=request.session_id,
            user_query=request.user_query
        )

        # Save AI response to persistent MongoDB session
        save_chat_message(
            session_id=request.session_id,
            user_id=request.user_id,
            role="ai",
            content=ai_response
        )

        return {"status": "success", "response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_patient_file(
    patient_id: str = Form(...),
    name: str = Form(""),
    age: int = Form(30),
    file: UploadFile = File(...)
):
    try:
        print(f"Processing upload for input Patient ID: {patient_id}, Name: {name}, Age: {age}")
        
        # 1. Update/Create MongoDB Patient Profile
        mongo_res = register_file_in_mongodb(
            patient_id=patient_id, 
            name=name, 
            age=age, 
            filename=file.filename
        )
        
        formal_id = mongo_res["formal_patient_id"]
        formal_name = mongo_res["formal_name"]
        mongo_msg = mongo_res["status"]
        
        # 2. Find or Create Standardized Patient Folder in data/
        root_dir = Path(__file__).resolve().parent.parent
        data_dir = root_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        matching_folder = None
        for folder in data_dir.iterdir():
            if folder.is_dir() and formal_id in folder.name:
                matching_folder = folder
                break
                
        if not matching_folder:
            clean_name = formal_name.replace(" ", "_")
            folder_name = f"{clean_name}_{formal_id}"
            matching_folder = data_dir / folder_name
            matching_folder.mkdir(parents=True, exist_ok=True)
            
        file_path = matching_folder / file.filename
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Document Parsing (PDF, CSV, TXT, OCR Images)
        documents = process_file(file_path)
        
        for doc in documents:
            doc.metadata["patient_id"] = formal_id
            doc.metadata["file_name"] = file.filename
            
        # 4. Text Chunking
        chunks = get_documents_chunks(documents)
        
        # 5. ChromaDB Vector Store Ingestion
        if chunks:
            add_to_databse(chunks)
            
        # 6. Post-Ingestion Automated Alert Scanner
        scan_msg = "Scan skipped."
        try:
            from genai.tools import scan_for_alerts
            scan_msg = scan_for_alerts.invoke({"patient_id": formal_id, "patient_name": formal_name, "age": age})
        except Exception as scan_err:
            print("Post-ingestion alert scan error:", scan_err)
            scan_msg = f"Scan notice: {scan_err}"
        
        return {
            "status": "success",
            "patient_id": formal_id,
            "patient_name": formal_name,
            "filename": file.filename,
            "mongodb_status": mongo_msg,
            "chromadb_status": f"Successfully processed {len(chunks)} text chunks into vector store.",
            "alert_status": scan_msg
        }
    except Exception as e:
        print(f"Error in upload_patient_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))