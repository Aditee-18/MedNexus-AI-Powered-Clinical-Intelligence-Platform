import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
key=os.getenv("GROQ_API_KEY")

llm=ChatGroq(groq_api_key=key,model_name="llama-3.3-70b-versatile",temperature=1,max_tokens=1024)

prompt_template=PromptTemplate.from_template(
    """You are MedNexus AI, a highly intelligent clinical assistant. 
    Use the following pieces of retrieved patient medical records to answer the doctor's question.
    If you cannot find the answer in the provided context, state clearly that the information is missing.
    Do not invent or guess any medical data.

    Context (Patient Records):
    {context}

    Doctor's Question: {question}

    Provide a clear, professional, and concise answer:"""
)

rag_chain=prompt_template|llm|StrOutputParser()

def generate_medical_response(query,retrieved_chunks):
    if not retrieved_chunks or 'documents' not in retrieved_chunks or not retrieved_chunks['documents'][0]:
        return "No relevant patient records found in the database."
    
    formatted_context="\n\n".join(retrieved_chunks['documents'][0])

    print("\nThinking...")
    response=rag_chain.invoke({
        "context":formatted_context,
        "question":query
    })

    return response