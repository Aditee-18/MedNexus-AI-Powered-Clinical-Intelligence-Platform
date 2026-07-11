from pathlib import Path
from rag_ingestion import process_all_patients
from chunk import get_documents_chunks
from vector_store import add_to_databse

def run_pipeline():
    print("Starting MedNexus AI Pipeline...")

    all_documents=process_all_patients(Path("data"))

    chunks=get_documents_chunks(all_documents)

    add_to_databse(chunks)

    print("Pipeline complete!")

if __name__=="__main__":
    run_pipeline()