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
    patient_id: str = Form(""),
    name: str = Form(""),
    age: int = Form(30),
    file: UploadFile = File(...)
):
    try:
        clean_patient_id = patient_id.strip()
        clean_name = name.strip()

        root_dir = Path(__file__).resolve().parent.parent
        temp_dir = root_dir / "scratch" / "temp_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / file.filename

        # Save temporary file to disk for OCR/PDF text extraction
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Parse Document Text FIRST (PyPDF / CSV / EasyOCR)
        documents = process_file(temp_file_path)
        extracted_text = " ".join([doc.page_content for doc in documents])

        import re

        # Extract Patient ID directly from report text if missing
        if not clean_patient_id:
            id_match = re.search(r'(?:Patient\s*ID|ID|Hospital\s*ID)[:\s]*([A-Z]{3}-\d{4}-\d{4,6}|\d{4,6})', extracted_text, re.IGNORECASE)
            if id_match:
                clean_patient_id = id_match.group(1).strip()

        # Extract Patient Name directly from report text if missing
        if not clean_name:
            name_match = re.search(r'(?:Patient\s*Name|Name)[:\s]*([A-Za-z\s]+?)(?=\s+(?:Age|ID|Gender|Sample|Referring|Report|Date|\d|\n|$))', extracted_text, re.IGNORECASE)
            if name_match:
                clean_name = name_match.group(1).strip()

        # Check filename if ID/Name are still missing
        filename_clean = file.filename.replace("_", " ").replace("-", " ")
        if not clean_patient_id or not clean_name:
            patients = get_all_patients()
            for p in patients:
                p_name = p.get("name", "")
                p_id = p.get("patient_id", "")
                first_name = p_name.split()[0] if p_name else ""
                if (p_name and p_name.lower() in filename_clean.lower()) or \
                   (first_name and len(first_name) > 2 and first_name.lower() in filename_clean.lower()) or \
                   (p_id and p_id.lower() in filename_clean.lower()):
                    if not clean_patient_id: clean_patient_id = p_id
                    if not clean_name: clean_name = p_name
                    break

        # Fallback for new unnamed files (NO HARDCODED 09437 DEFAULT!)
        if not clean_patient_id:
            parts = file.filename.split(".")[0].split("_")
            if len(parts) >= 2 and parts[0].isalpha():
                if not clean_name: clean_name = f"{parts[0]} {parts[1]}"
                clean_patient_id = f"AMH-2026-0{abs(hash(clean_name)) % 9000 + 1000}"
            else:
                import random
                clean_patient_id = f"AMH-2026-{random.randint(10000, 99999)}"
                if not clean_name: clean_name = "New Patient"

        print(f"Processing upload for resolved Patient ID: {clean_patient_id}, Name: {clean_name}, Age: {age}")
        
        # 2. Update/Create MongoDB Patient Profile
        mongo_res = register_file_in_mongodb(
            patient_id=clean_patient_id, 
            name=clean_name, 
            age=age, 
            filename=file.filename
        )
        
        formal_id = mongo_res["formal_patient_id"]
        formal_name = mongo_res["formal_name"]
        mongo_msg = mongo_res["status"]
        
        # 3. Find or Create Standardized Patient Folder in data/
        data_dir = root_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        matching_folder = None
        for folder in data_dir.iterdir():
            if folder.is_dir() and formal_id in folder.name:
                matching_folder = folder
                break
                
        if not matching_folder:
            folder_clean_name = formal_name.replace(" ", "_")
            folder_name = f"{folder_clean_name}_{formal_id}"
            matching_folder = data_dir / folder_name
            matching_folder.mkdir(parents=True, exist_ok=True)
            
        file_path = matching_folder / file.filename
        
        # Move temp file to permanent data location
        shutil.move(str(temp_file_path), str(file_path))
        
        # 4. Attach Metadata & Chunk Documents
        for doc in documents:
            doc.metadata["patient_id"] = formal_id
            doc.metadata["file_name"] = file.filename
            
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