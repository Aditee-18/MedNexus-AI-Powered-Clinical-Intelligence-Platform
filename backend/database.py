# database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGO_DB")
client = MongoClient(mongo_uri)
db = client["mednexus_db"]
patients_collection = db["patients"]
alerts_collection = db["alerts"]
users_collection = db["users"]
chat_sessions_collection = db["chat_sessions"]

# Create 10-day TTL index on acknowledgedAt field (auto-deletes 10 days after acknowledgment)
try:
    alerts_collection.create_index("acknowledgedAt", expireAfterSeconds=864000)
except Exception as e:
    print("TTL index notice:", e)

def register_file_in_mongodb(patient_id: str, name: str, age: int, filename: str):
    """
    Searches MongoDB for patient using full or partial Patient ID (e.g. '09437' or 'AMH-2026-09437').
    If found, updates existing patient files. If not found, registers a new formal profile.
    """
    clean_id = patient_id.strip()
    
    # Perform regex search to match partial or full Patient ID
    existing_patient = patients_collection.find_one(
        {"patient_id": {"$regex": clean_id, "$options": "i"}}
    )
    
    if existing_patient:
        formal_id = existing_patient["patient_id"]
        formal_name = existing_patient.get("name", name)
        patients_collection.update_one(
            {"patient_id": formal_id},
            {"$addToSet": {"uploaded_files": filename}}
        )
        return {
            "status": f"Updated metadata for {formal_name} ({formal_id}).",
            "formal_patient_id": formal_id,
            "formal_name": formal_name,
            "is_new": False
        }
    else:
        # Standardize ID if just numbers/short code were passed
        if clean_id.upper().startswith("AMH-"):
            formal_id = clean_id.upper()
        else:
            formal_id = f"AMH-2026-{clean_id}"

        new_profile = {
            "patient_id": formal_id,
            "name": name if name else f"Patient {clean_id}",
            "age": age,
            "uploaded_files": [filename],
            "status": "Active"
        }
        patients_collection.insert_one(new_profile)
        return {
            "status": f"Created new patient profile for {new_profile['name']} ({formal_id}).",
            "formal_patient_id": formal_id,
            "formal_name": new_profile['name'],
            "is_new": True
        }

def get_all_patients():
    """Returns list of all patient profiles for UI selection."""
    patients = list(patients_collection.find({}, {"_id": 0}))
    return patients

def save_alert_to_mongodb(alert_data: dict):
    """Saves or updates structured risk alert in MongoDB."""
    import uuid
    from datetime import datetime
    
    alert_id = alert_data.get("alert_id") or f"alt_{uuid.uuid4().hex[:8]}"
    alert_doc = {
        "alert_id": alert_id,
        "patient_id": alert_data.get("patient_id"),
        "patient_name": alert_data.get("patient_name"),
        "age": alert_data.get("age", 30),
        "severity_level": alert_data.get("severity_level", "high"),  # "high", "medium", "low"
        "risk_score": alert_data.get("risk_score", 85),  # 1-100 for sorting
        "title": alert_data.get("title", "Clinical Delta Alert Detected"),
        "comparison_type": alert_data.get("comparison_type", "delta"),
        "ai_summary": alert_data.get("ai_summary", "Critical findings detected in recent report."),
        "suggested_action": alert_data.get("suggested_action", "Recommend clinical review."),
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "acknowledgedAt": None
    }
    
    # Overwrite active alert for same patient or insert new
    alerts_collection.update_one(
        {"patient_id": alert_doc["patient_id"], "status": "active"},
        {"$set": alert_doc},
        upsert=True
    )
    return alert_doc

def get_all_alerts():
    """Returns all alerts sorted by risk_score descending (High -> Low)."""
    alerts = list(alerts_collection.find({}, {"_id": 0}).sort("risk_score", -1))
    return alerts

def acknowledge_alert(alert_id: str):
    """Marks alert as acknowledged and sets acknowledgedAt timestamp for 10-day TTL auto-deletion."""
    from datetime import datetime
    now = datetime.utcnow()
    res = alerts_collection.update_one(
        {"alert_id": alert_id},
        {"$set": {"status": "acknowledged", "acknowledgedAt": now}}
    )
    return res.modified_count > 0

# --- USER AUTHENTICATION HELPERS ---
def create_user_account(name: str, email: str, password_hash: str, hospital_id: str = "MED-2026", specialty: str = "General Medicine"):
    """Registers a new clinician in MongoDB users collection."""
    import uuid
    from datetime import datetime
    
    user_doc = {
        "user_id": f"usr_{uuid.uuid4().hex[:8]}",
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "hospital_id": hospital_id.strip() if hospital_id else "MED-2026",
        "specialty": specialty.strip() if specialty else "General Medicine",
        "created_at": datetime.utcnow().isoformat()
    }
    users_collection.insert_one(user_doc)
    user_doc.pop("_id", None)
    return user_doc

def find_user_by_email(email: str):
    """Fetches user document by email."""
    user = users_collection.find_one({"email": email.strip().lower()}, {"_id": 0})
    return user

# --- PERSISTENT CHAT HISTORY HELPERS ---
def save_chat_message(session_id: str, user_id: str, role: str, content: str):
    """Appends message to session thread in chat_sessions collection."""
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    
    chat_sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$setOnInsert": {
                "session_id": session_id,
                "user_id": user_id,
                "title": content[:35] + ("..." if len(content) > 35 else ""),
                "created_at": now
            },
            "$set": {"updated_at": now},
            "$push": {"messages": {"role": role, "content": content, "timestamp": now}}
        },
        upsert=True
    )

def get_user_chat_sessions(user_id: str):
    """Returns list of recent chat session metadata for sidebar."""
    sessions = list(
        chat_sessions_collection.find(
            {"user_id": user_id},
            {"_id": 0, "session_id": 1, "title": 1, "updated_at": 1}
        ).sort("updated_at", -1)
    )
    return sessions

def get_chat_session_history(session_id: str):
    """Returns all messages for a specific session_id."""
    session = chat_sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
    if session and "messages" in session:
        return session["messages"]
    return []

# --- OPTION 3: STATE-BASED ACTIVE PATIENT CONTEXT MANAGER ---
def update_session_active_patient(session_id: str, patient_id: str, patient_name: str):
    """Updates the active patient context for a consultation session in MongoDB."""
    from datetime import datetime
    chat_sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "active_patient_id": patient_id,
                "active_patient_name": patient_name,
                "updated_at": datetime.utcnow().isoformat()
            }
        },
        upsert=True
    )

def get_session_active_patient(session_id: str):
    """Retrieves the current active patient context for a consultation session."""
    session = chat_sessions_collection.find_one({"session_id": session_id}, {"_id": 0, "active_patient_id": 1, "active_patient_name": 1})
    if session and session.get("active_patient_id"):
        return {
            "patient_id": session.get("active_patient_id"),
            "name": session.get("active_patient_name")
        }
    return None