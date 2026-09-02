from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_documents_chunks(all_documents):
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n","\n"," ",""]
    )
    chunks=text_splitter.split_documents(all_documents)
    return chunks

# import chromadb
# from pathlib import Path
# ROOT_DIR = Path(__file__).resolve().parent.parent
# CHROMA_DB_PATH = str(ROOT_DIR / "genai" / "chroma_db")

# client=chromadb.PersistentClient(path=CHROMA_DB_PATH)
# collection=client.get_collection(name="patient_records")

# print(collection.count())
# print(collection.peek(5))

# # Fetch everything including the vector embeddings
# data = collection.get(include=["documents", "metadatas", "embeddings"])

# print(data["ids"])         # List of IDs
# print(data["documents"])   # List of original raw texts
# print(data["embeddings"])  # List of high-dimensional vectors


