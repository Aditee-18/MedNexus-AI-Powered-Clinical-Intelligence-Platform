import os
import sys
import pydantic.v1

# Ensure project root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Step 0: Backward compatibility layer for LangChain & Ragas imports across versions
sys.modules['langchain_core.pydantic_v1'] = pydantic.v1
sys.modules['langchain.pydantic_v1'] = pydantic.v1

import langchain_community.chat_models
setattr(langchain_community.chat_models, 'ChatVertexAI', type('ChatVertexAI', (), {}))

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (GROQ_API_KEY, etc.)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from genai.retriever import retrieve_patient_info
from genai.generate import generate_medical_response

# -----------------------------------------------------------------------------
# 1. EVALUATION TEST CASES
# -----------------------------------------------------------------------------
# Define realistic test questions, target patient IDs, and ground truth answers.
# - "ground_truth": The reference fact from actual patient clinical records.
test_cases = [
    {
        "question": "What is the clinical status or report details of Aarav Mehta?",
        "patient_id": "AMH-2026-09437",
        "ground_truth": "Aarav Mehta is a pediatric patient with blood and hemoglobin lab records."
    },
    {
        "question": "What is the diagnosis and medical notes for Rohan Sharma?",
        "patient_id": "AMH-2026-04581",
        "ground_truth": "Rohan Sharma has blood pressure history, doctor notes, and prescription details."
    },
    {
        "question": "What health conditions or reports are recorded for Neha Verma?",
        "patient_id": "AMH-2026-05294",
        "ground_truth": "Neha Verma has a diabetes report, diet instructions, and glucose history."
    },
]

def run_evaluation():
    print("====================================================")
    print("      MEDNEXUS AI - RAGAS EVALUATION PIPELINE       ")
    print("====================================================\n")

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    # -----------------------------------------------------------------------------
    # 2. DATA GENERATION FOR EVALUATION
    # -----------------------------------------------------------------------------
    # Loop over test queries, run ChromaDB vector retrieval and Groq LLM generation.
    for idx, case in enumerate(test_cases, 1):
        query = case["question"]
        patient_id = case["patient_id"]

        print(f"[{idx}/{len(test_cases)}] Processing Question: '{query}'")

        # Step 2a: Retrieve context chunks from ChromaDB for the given patient_id
        raw_results = retrieve_patient_info(query=query, patient_id=patient_id, n_results=3)
        
        retrieved_chunks = []
        if raw_results and 'documents' in raw_results and raw_results['documents'] and raw_results['documents'][0]:
            retrieved_chunks = raw_results['documents'][0]

        # Step 2b: Generate answer using MedNexus Groq RAG chain
        answer = generate_medical_response(query=query, retrieved_chunks=raw_results)

        questions.append(query)
        answers.append(answer)
        contexts.append(retrieved_chunks if retrieved_chunks else ["No context retrieved."])
        ground_truths.append(case["ground_truth"])

        print(f"   -> Retrieved Chunks: {len(retrieved_chunks)}")
        print(f"   -> Generated Answer: {answer}\n")

    # -----------------------------------------------------------------------------
    # 3. BUILD HUGGINGFACE DATASET FOR RAGAS
    # -----------------------------------------------------------------------------
    data = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    # -----------------------------------------------------------------------------
    # 4. CONFIGURE RAGAS EVALUATORS (Groq LLM + Local HuggingFace Embeddings)
    # -----------------------------------------------------------------------------
    # We explicitly wrap Groq Chat model and local SentenceTransformer embeddings
    # so RAGAS does NOT depend on OpenAI API keys.
    evaluator_llm = LangchainLLMWrapper(
        ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    )
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    )

    # -----------------------------------------------------------------------------
    # 5. EXECUTE METRICS EVALUATION
    # -----------------------------------------------------------------------------
    # Metrics evaluated:
    # - faithfulness: Measures hallucination (is every claim supported by retrieved context?)
    # - answer_relevancy: Measures how directly the answer addresses the question
    # - context_recall: Measures if ground truth information was successfully retrieved
    print("Running RAGAs Evaluation metrics calculation (Faithfulness, Answer Relevancy, Context Recall)...")
    
    results = evaluate(
        dataset=data,
        metrics=[faithfulness, answer_relevancy, context_recall],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings
    )

    print("\n====================================================")
    print("               EVALUATION RESULTS                   ")
    print("====================================================")
    print(results)
    
    # Export results summary
    df = results.to_pandas()
    print("\nDetailed Metric Scores per Test Query:")
    print(df[["question", "faithfulness", "answer_relevancy", "context_recall"]])

if __name__ == "__main__":
    run_evaluation()