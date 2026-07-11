# database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["mednexus_db"]
patients_collection = db["patients"]

def register_file_in_mongodb(patient_id: str, name: str, age: int, filename: str):
    existing_patient = patients_collection.find_one({"patient_id": patient_id})
    if existing_patient:
        patients_collection.update_one(
            {"patient_id": patient_id},
            {"$addToSet": {"uploaded_files": filename}}
        )
        return f"Updated metadata for {name}."
    else:
        new_profile = {
            "patient_id": patient_id,
            "name": name,
            "age": age,
            "uploaded_files": [filename],
            "status": "Active"
        }
        patients_collection.insert_one(new_profile)
        return f"Created profile for {name}."