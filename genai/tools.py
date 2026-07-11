import os
from pathlib import Path
import sys
from langchain_core.tools import tool
from genai.retriever import retrieve_patient_info
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
    CRITICAL: If you only know a name but do not know the formal hospital ID, 
    you MUST use 'lookup_patient_by_name' first to obtain the correct ID.
    CRITICAL: When reading search results, strictly ignore chunks belonging to other patients.
    """
    if not patient_id:
        return "Error: Cannot search vector clinical logs without a valid patient_id. Please find the ID first."

    print(f"\n[Agent Action] Executing ChromaDB Vector Search for Patient ID: {patient_id}...")

    raw_results = retrieve_patient_info(query=query, patient_id=patient_id)
    if not raw_results or 'documents' not in raw_results or not raw_results['documents'][0]:
        return f"No relevant matching text chunks found in the database for Patient ID {patient_id}."
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
        mongo_message = register_file_in_mongodb(
            patient_id=patient_id, 
            name=name, 
            age=age, 
            filename=file_name
        )
        
        return f"Database Pipeline Status:\n- MongoDB: {mongo_message}\n- ChromaDB: Scheduled vector embeddings generation for {file_name}."
        
    except Exception as e:
        return f"Failed to execute file upload tool. Error: {str(e)}"
    
# Tool 4: Time Period Risk Scanner
@tool
def analyse_health_trends(patient_id: str, start_month_year: str, end_month_year: str) -> str:
    """
    USE THIS TOOL when a doctor wants to scan or analyze a patient's historical trends 
    across a specific time frame (e.g., 'from January to May' or 'past 3 months').
    It pulls timeline data to check if a patient is getting unwell.
    ONLY call 'analyse_health_trends' if the doctor explicitly types the exact words 'scan trends' or 'timeline'
    """
    print(f"\n[Agent Action] Extracting clinical timeline for {patient_id} ({start_month_year} to {end_month_year})...")

    simulated_timeline_data = f"""
Timeline Data for {patient_id} from {start_month_year} to {end_month_year}:
    - Jan 2026: Blood Pressure 130/85 mmHg. Patient reports mild fatigue.
    - Mar 2026: Blood Pressure 145/92 mmHg (Elevated). Weight increased by 3kg.
    - May 2026: Blood Pressure 168/102 mmHg (High - Stage 2 Hypertension). Patient reports occasional dizziness.
"""
    return simulated_timeline_data