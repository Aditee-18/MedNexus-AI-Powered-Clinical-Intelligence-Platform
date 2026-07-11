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

