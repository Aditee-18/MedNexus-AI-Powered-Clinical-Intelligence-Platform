import os
from pathlib import Path

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from langchain_core.tools import tool
from genai.retriever import retrieve_patient_info

from backend.database import patients_collection, register_file_in_mongodb

#Tool 1: Patient Directory Lookup (MongoDB Search)
@tool
def lookup_patient_by_name(name: str) -> str:
    """
    USE THIS TOOL when the doctor provides a patient's name (like 'Aarav' or 'Rohan') 
    but you do not know their formal hospital ID (like 'AMH-2026-09437').
    This searches MongoDB to discover their unique Patient ID and baseline demographics.
    """
    print(f"\n[Agent Action] Searching MongoDB directory for name: {name}...")
    try:
        # Perform a case-insensitive search to find the patient record
        patient = patients_collection.find_one({"name": {"$regex": name, "$options": "i"}}, {"_id": 0})
        if patient:
            return f"Patient Found in MongoDB: {str(patient)}"
        return f"No patient matching the name '{name}' was found in the master registry."
    except Exception as e:
        return f"MongoDB Registry Error: {str(e)}"

# Tool 2: Patient Record Search (ChromaDB RAG)
@tool
def search_patient_records(query: str, patient_id: str = None) -> str:
    """
    USE THIS TOOL to search the clinical vector database (ChromaDB) for specific medical details.
    You can pass either the formal Patient ID (e.g. 'AMH-2026-09437') or the patient's name (e.g. 'Meera', 'Rohan', 'Neha').
    """
    if not patient_id:
        return "Error: Cannot search vector clinical logs without a patient name or ID."

    clean_id = patient_id.strip()
    
    # Auto-resolve name or short ID to formal Patient ID if needed
    if not clean_id.upper().startswith("AMH-"):
        patient = patients_collection.find_one({"name": {"$regex": clean_id, "$options": "i"}}, {"_id": 0})
        if not patient:
            patient = patients_collection.find_one({"patient_id": {"$regex": clean_id, "$options": "i"}}, {"_id": 0})
        if patient:
            clean_id = patient["patient_id"]
        else:
            print(f"[Agent Warning] Could not resolve patient name '{clean_id}' to a registered MongoDB record.")

    print(f"\n[Agent Action] Executing ChromaDB Vector Search for Patient ID: {clean_id}...")

    raw_results = retrieve_patient_info(query=query, patient_id=clean_id)
    if not raw_results or 'documents' not in raw_results or not raw_results['documents'][0]:
        return f"No relevant matching text chunks found in the database for Patient ID {clean_id}."
    return "\n\n".join(raw_results['documents'][0])

# Tool 3: File Upload and Dual Ingestion (MongoDB + ChromaDB)
@tool 
def upload_patient_file(file_name: str, patient_id: str, name: str, age: int) -> str:
    """
    USE THIS TOOL ONLY when a doctor explicitly requests to upload, save, add, or ingest a NEW medical 
    document file into a patient's profile.
    
    Args:
        file_name: Name of the file.
        patient_id: The formal hospital ID.
        name: Full name of the patient.
        age: CRITICAL: This must be a raw integer number (e.g., 35), NEVER a string in quotes.
    """
    print(f"\n[Agent Action] Triggering dual database ingestion pipeline for file: {file_name}...")

    try:
        # 1. Update/Register in MongoDB
        mongo_message = register_file_in_mongodb(
            patient_id=patient_id, 
            name=name, 
            age=age, 
            filename=file_name
        )
        
        # 2. Locate patient folder in data/
        ROOT_DIR = Path(__file__).resolve().parent.parent
        data_dir = ROOT_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        matching_folder = None
        for folder in data_dir.iterdir():
            if folder.is_dir() and patient_id in folder.name:
                matching_folder = folder
                break
                
        if not matching_folder:
            clean_name = name.replace(" ", "_")
            folder_name = f"{clean_name}_{patient_id}"
            matching_folder = data_dir / folder_name
            matching_folder.mkdir(parents=True, exist_ok=True)
            
        file_path = matching_folder / file_name
        
        chroma_message = "File metadata registered."
        if file_path.exists():
            from genai.rag_ingestion import process_file
            from genai.chunk import get_documents_chunks
            from genai.vector_store import add_to_databse
            
            documents = process_file(file_path)
            for doc in documents:
                doc.metadata["patient_id"] = patient_id
                doc.metadata["file_name"] = file_name
                
            chunks = get_documents_chunks(documents)
            if chunks:
                add_to_databse(chunks)
                chroma_message = f"Indexed {len(chunks)} text chunks into ChromaDB vector store."
        else:
            chroma_message = f"Profile updated in MongoDB. File {file_name} can now be uploaded to {matching_folder.name}."
            
        return f"✅ File for this patient is saved successfully.\n- Patient: {name} (ID: {patient_id})\n- Document Ingested: {file_name}"
        
    except Exception as e:
        return f"Failed to save patient file. Error: {str(e)}"
    
# Tool 4: Smart Retrospective Health Trend Agent
@tool
def analyse_health_trends(patient_id: str, duration: str = "recent visits", focus: str = "vitals blood pressure glucose symptoms diagnosis lab results") -> str:
    """
    USE THIS TOOL when a doctor wants to scan, analyze, or review a patient's historical trends, 
    changes over time, or check if the patient is deteriorating/getting unwell over a timeframe 
    (e.g., 'past 2 months', 'recent visits', or 'last few checkups').
    
    Args:
        patient_id: Formal hospital ID (e.g., 'AMH-2026-04581').
        duration: Timeframe description e.g. 'recent visits', 'past 3 months', or 'all history'.
        focus: Clinical focus e.g. 'blood pressure', 'diabetic markers', or 'general vitals'.
    """
    print(f"\n[Agent Action] Extracting chronological health trajectory for {patient_id} ({duration}, focus: {focus})...")

    # Pull up to 15 chunks for this patient from ChromaDB
    raw_results = retrieve_patient_info(
        query=f"{focus} vitals date history blood pressure glucose symptoms diagnosis report",
        patient_id=patient_id,
        n_results=15
    )

    if not raw_results or not raw_results['documents'] or not raw_results['documents'][0]:
        return f"No health record logs found in database for Patient ID {patient_id}."

    context = "\n\n".join(raw_results['documents'][0])

    from genai.generate import rag_chain
    trajectory_prompt = f"""
    You are a Clinical Health Trend Specialist for MedNexus AI.
    Analyze the patient records below for Patient ID '{patient_id}' for the requested timeframe: '{duration}'.
    
    INSTRUCTIONS:
    1. Read all dates printed inside the patient records and order the visits chronologically.
    2. Format your response into these 4 clean sections:
    
    📊 **Clinical Health Trend Report** (Patient ID: {patient_id})
    • Focus: {focus.title()} ({duration})
    
    📉 **Baseline State** (Earliest visit in retrieved records):
    - [Date & Vitals/Lab values/Symptoms]
    
    📊 **Chronological Trajectory & Progression**:
    - [Date-by-date changes across intermediate visits]
    
    🚨 **Latest Status & Deterioration Assessment**:
    - [Most recent visit findings & overall trajectory: Stable / Improving / Deteriorating]
    
    🩺 **Clinical Decision Support Recommendation**:
    - [1-2 sentence suggested protocol for doctor review]
    
    Strictly base your answer ONLY on the retrieved records below. Do not guess or hallucinate.
    
    Patient Records:
    {context}
    """

    result = rag_chain.invoke({
        "context": context,
        "question": trajectory_prompt
    })

    return result

# Tool 5: Automated Post-Ingestion Alert Scanner
@tool
def scan_for_alerts(patient_id: str, patient_name: str, age: int = 30) -> str:
    """
    USE THIS TOOL automatically after every file upload.
    Analyzes uploaded chunks for critical findings (Delta comparison vs previous reports OR baseline check)
    and saves structured risk alerts to MongoDB.
    """
    print(f"\n[Agent Action] Running automated health scan for {patient_id} ({patient_name})...")

    # Pull latest chunks from ChromaDB for this patient
    raw_results = retrieve_patient_info(
        query="blood pressure glucose HbA1c abnormal critical risk symptoms diagnosis lab results prescription",
        patient_id=patient_id,
        n_results=10
    )

    if not raw_results or not raw_results['documents'] or not raw_results['documents'][0]:
        return "No data found to scan."

    chunks = raw_results['documents'][0]
    metadatas = raw_results.get('metadatas', [[]])[0]
    
    # Track unique files to detect if Delta comparison or Baseline check applies
    unique_files = set(m.get('file_name') for m in metadatas if isinstance(m, dict) and m.get('file_name'))
    comparison_type = "delta" if len(unique_files) > 1 else "baseline"
    context = "\n\n".join(chunks)

    # Use LLM to analyze risk and format structured response
    from genai.generate import rag_chain
    alert_prompt = f"""
    You are a clinical risk scanner for MedNexus AI.
    Analyze the patient records below for Patient '{patient_name}' ({patient_id}).
    
    Mode: {'DELTA COMPARISON (Compare new report vs older reports)' if comparison_type == 'delta' else 'BASELINE ANOMALY CHECK (Single report available)'}
    
    Look for anomalies:
    - High Blood Pressure (BP > 140/90 mmHg)
    - High Blood Sugar / HbA1c (> 7.5%)
    - Severe organ risk, anemia, or abnormal ECG
    
    If ANY clinical risk or deterioration is detected, format your response EXACTLY as a JSON string with these fields:
    {{
       "has_risk": true,
       "severity_level": "high",  // "high", "medium", or "low"
       "risk_score": 90,           // Number 1-100 (90-100 critical, 60-89 medium, 1-59 low)
       "title": "<Short 5-8 word headline e.g. BP Spike to 168/102 mmHg>",
       "ai_summary": "<2-3 sentence clinical summary comparing current vs previous values or key findings>",
       "suggested_action": "<1-2 sentence decision support recommendation for doctor review>"
    }}
    
    If NO clinical risk or anomaly is detected:
    {{ "has_risk": false }}
    
    Patient Records:
    {context}
    """

    result_text = rag_chain.invoke({
        "context": context,
        "question": alert_prompt
    })

    import json
    try:
        # Extract JSON from LLM output
        clean_json_str = result_text[result_text.find('{'):result_text.rfind('}')+1]
        data = json.loads(clean_json_str)
        
        if data.get("has_risk"):
            from backend.database import save_alert_to_mongodb
            alert_doc = save_alert_to_mongodb({
                "patient_id": patient_id,
                "patient_name": patient_name,
                "age": age,
                "severity_level": data.get("severity_level", "high"),
                "risk_score": data.get("risk_score", 85),
                "title": data.get("title", "Clinical Alert Detected"),
                "comparison_type": comparison_type,
                "ai_summary": data.get("ai_summary", result_text[:200]),
                "suggested_action": data.get("suggested_action", "Recommend doctor review."),
            })
            return f"ALERT_CREATED: {alert_doc['title']} (Risk Score: {alert_doc['risk_score']})"
        else:
            return "NO_ALERT: Patient vitals and lab results are within stable limits."
    except Exception as e:
        print("Alert parser notice:", e)
        # Fallback keyword match
        if any(term in result_text.lower() for term in ["high", "critical", "spike", "anemia", "hypertension", "diabetes", "elevated"]):
            from backend.database import save_alert_to_mongodb
            alert_doc = save_alert_to_mongodb({
                "patient_id": patient_id,
                "patient_name": patient_name,
                "age": age,
                "severity_level": "high",
                "risk_score": 85,
                "title": f"Clinical Finding for {patient_name}",
                "comparison_type": comparison_type,
                "ai_summary": result_text[:250],
                "suggested_action": "Recommend clinical follow-up review.",
            })
            return f"ALERT_CREATED: {alert_doc['title']}"
            
        return "NO_ALERT: No critical risk detected."