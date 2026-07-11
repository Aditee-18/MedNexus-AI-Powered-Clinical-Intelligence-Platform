import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# Resolve project root and ChromaDB path absolutely
ROOT_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = str(ROOT_DIR / "genai" / "chroma_db")

embedding_model=SentenceTransformer('all-MiniLM-L6-v2')
chroma_client=chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection=chroma_client.get_or_create_collection(name="patient_records")

def add_to_databse(chunks):
    documents=[chunk.page_content for chunk in chunks]
    metadatas=[chunk.metadata for chunk in chunks]

    #unique id for every chunk
    ids=[str(uuid.uuid4()) for _ in chunks]
    print("Generating embeddings...")
    embeddings=embedding_model.encode(documents).tolist()
    print("Storing in chromadb...")
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Successfully added {len(chunks)} to the database.")
