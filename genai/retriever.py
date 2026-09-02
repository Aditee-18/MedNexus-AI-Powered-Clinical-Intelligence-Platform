import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

# Resolve project root and ChromaDB path absolutely
ROOT_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = str(ROOT_DIR / "genai" / "chroma_db")

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

chroma_client=chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection=chroma_client.get_collection(name="patient_records")

def retrieve_patient_info(query,patient_id=None,n_results=5):
    model = get_embedding_model()
    query_embedding=model.encode([query]).tolist()

    w={"patient_id":patient_id} if patient_id else None
    result = collection.query(
    query_embeddings=query_embedding,
    n_results=n_results,
    where=w
)

    return result

#without llm
# if __name__ == "__main__":
#     print("\n--- Testing RAG Retrieval ---")
     
    
#     test_query = "Does Meera show infection signs?"
    
#     raw_results = retrieve_patient_info(query=test_query, patient_id=None, n_results=3)
    
#     if raw_results and 'documents' in raw_results and raw_results['documents']:
        
        
#         for i, chunk_text in enumerate(raw_results['documents'][0], 1):
#             print(f"--- Chunk {i} ---")
#             print(chunk_text.strip())
#             print("-" * 20)
#     else:
#         print("No matching data found.")

#llm connected
# from generate import generate_medical_response
# if __name__=="__main__":
#     query="Who is our youngest patient"
    
#     print("Searching database...")
#     raw_results=retrieve_patient_info(query=query)

#     print("Generating AI response...")
#     final_answer=generate_medical_response(query=query,retrieved_chunks=raw_results)

#     print("MedNexus says...")
#     print(final_answer)