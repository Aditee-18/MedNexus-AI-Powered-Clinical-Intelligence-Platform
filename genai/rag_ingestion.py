import os
import pandas as pd
from pathlib import Path
import easyocr

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


# Lazy loader for EasyOCR to prevent backend startup delays
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        print("[Lazy Load] Initializing EasyOCR PyTorch Model...")
        _ocr_reader = easyocr.Reader(['en'])
    return _ocr_reader

#PDF loader
def load_pdf(file_path):
    loader =PyPDFLoader(str(file_path))
    documents=loader.load()
    return documents

#txt loader
def load_txt(file_path):
    with open(file_path,"r",encoding="utf-8") as file:
        text=file.read()

    return[
        Document(
            page_content=text,
            metadata={"source":str(file_path)}
        )
    ]

#csv loader
def load_csv(file_path):
    df=pd.read_csv(file_path)
    text=df.to_string(index=False)

    return[
        Document(
            page_content=text,
            metadata={"source":str(file_path)}
        )
    ]

#image ocr loader
def load_img(file_path):
    reader = get_ocr_reader()
    result = reader.readtext(str(file_path), detail=0)
    text = " ".join(result)

    return[
        Document(
            page_content=text,
            metadata={"source":str(file_path)}
        )
    ]

#file processor
def process_file(file_path):
    extension=file_path.suffix.lower()

    if extension==".pdf":
        return load_pdf(file_path)
    elif extension==".txt":
        return load_txt(file_path)
    elif extension==".csv":
        return load_csv(file_path)
    elif extension in [".jpg",".jpeg",".png"]:
        return load_img(file_path)
    else: 
        print(f"Unsupported file type: {file_path}")
        return[]
    
#reading patient files

ROOT_DIR = Path(__file__).resolve().parent.parent  # always E:\MedNexusAI

def process_all_patients(data_dir="data"):
    Data_path = ROOT_DIR / data_dir  # always E:\MedNexusAI\data
    all_documents = []

    if not Data_path.exists():
        print(f"Warning: The directory {Data_path} does not exist")
        return all_documents

    for patient_folder in Data_path.iterdir():
        if patient_folder.is_dir():
            folder_name = patient_folder.name  # "Aarav_Mehta_AMH-2026-09437"

            # Extract just the patient ID from folder name
            parts = folder_name.rsplit("_AMH-", 1)
            if len(parts) == 2:
                patient_id = "AMH-" + parts[1]  # "AMH-2026-09437"
            else:
                patient_id = folder_name  # fallback

            print(f"\nProcessing patient: {patient_id}")

            for file_path in patient_folder.iterdir():
                if file_path.is_file():
                    print(f"  Reading file: {file_path.name}")
                    documents = process_file(file_path)

                    for doc in documents:
                        doc.metadata["patient_id"] = patient_id
                        doc.metadata["file_name"] = file_path.name
                        all_documents.append(doc)

    print(f"\nIngestion Done. Loaded {len(all_documents)} documents")
    return all_documents

#ouput
# print(f"\nTotal documents loaded: {len(all_documents)}")

# print("\nExample document:\n")

# print(all_documents[0].page_content[:500])

# print("\nMetadata:\n")

# print(all_documents[0].metadata)

