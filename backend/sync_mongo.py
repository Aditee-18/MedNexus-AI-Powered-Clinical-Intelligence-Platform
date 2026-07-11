from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import register_file_in_mongodb

def sync_existing_files_to_mongo():
    data_path = Path("data")
    
    print("Syncing existing files to MongoDB...")
    
    for patient_folder in data_path.iterdir():
        if patient_folder.is_dir():
            folder_name = patient_folder.name  # e.g. "Aarav_Mehta_AMH-2026-09437"
            
            # Split on the last occurrence of AMH to separate name from ID
            parts = folder_name.rsplit("_AMH-", 1)
            
            if len(parts) == 2:
                patient_name = parts[0].replace("_", " ")  # "Aarav Mehta"
                patient_id = "AMH-" + parts[1]             # "AMH-2026-09437"
            else:
                # Fallback if folder name format is unexpected
                print(f"  Skipping unexpected folder format: {folder_name}")
                continue
            
            for file_path in patient_folder.iterdir():
                if file_path.is_file():
                    register_file_in_mongodb(
                        patient_id=patient_id,
                        name=patient_name,
                        age=0,
                        filename=file_path.name
                    )
            print(f"  Synced: {patient_name} ({patient_id})")

if __name__ == "__main__":
    sync_existing_files_to_mongo()