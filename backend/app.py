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
from backend.database import register_file_in_mongodb

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
    user_query: str

@app.get("/")
def read_root():
    return {"message": "Mednexus API is running"}

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    try:
        print(f"Received message from {request.session_id}: {request.user_query}")
        ai_response = run_mednexus_agent(
            session_id=request.session_id,
            user_query=request.user_query
        )
        return {"status": "success", "response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_patient_file(
    patient_id: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    file: UploadFile = File(...)
):
    try:
        print(f"Processing upload for Patient ID: {patient_id}, Name: {name}")
        
        mongo_msg = register_file_in_mongodb(
            patient_id=patient_id, 
            name=name, 
            age=age, 
            filename=file.filename
        )
        
        # Resolve path to the absolute data folder in project root
        root_dir = Path(__file__).resolve().parent.parent
        patient_folder = root_dir / "data" / patient_id
        patient_folder.mkdir(parents=True, exist_ok=True)
        
        file_path = patient_folder / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        documents = process_file(file_path)
        
        for doc in documents:
            doc.metadata["patient_id"] = patient_id
            doc.metadata["file_name"] = file.filename
            
        chunks = get_documents_chunks(documents)
        
        add_to_databse(chunks)
        
        return {
            "status": "success",
            "mongodb_status": mongo_msg,
            "chromadb_status": f"Successfully processed {len(chunks)} chunks into vector store."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))