import os
import sys
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from genai.tools import search_patient_records, upload_patient_file, analyse_health_trends,lookup_patient_by_name
load_dotenv()
key=os.getenv("GROQ_API_KEY")

llm=ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

memorysaver=MemorySaver()

tool_belt=[search_patient_records,upload_patient_file,analyse_health_trends,lookup_patient_by_name]

agent_prompt="""You are MedNexus AI, an advanced, proactive clinical assistant.
Your goal is to assist clinicians by intelligently executing tasks using the tools provided to you.

CRITICAL ROUTING RULES:
- If the clinician asks to view, read, analyze, summarize, or check existing medical data/diagnoses/reports, use your record searching capabilities.
- If the clinician explicitly asks to add, save, upload, or ingest a new file into the system, use your file upload capability.
- Always discover the formal Patient ID using the directory lookup before searching clinical logs.

ANTI-LOOPING RULES (CRITICAL):
- DO NOT call the same tool more than twice.
- If a database search returns empty or fails, DO NOT keep retrying. Immediately stop and inform the user that the specific data is missing.
- Once you successfully retrieve the required data, immediately output your final clinical answer and stop tool usage.

CRITICAL FORMATTING RULES:
- When using tools that require numeric inputs like age, you must pass them strictly as integers.
- Do not guess or hallucinate medical data. 
- Be professional, direct, and concise.
"""

mednexus_agent = create_react_agent(
    model=llm, 
    tools=tool_belt, 
    prompt=agent_prompt
)

def run_mednexus_agent(session_id: str,user_query: str)->str:
    """Core execution handler for incoming backend API questions."""

    try:
        execution_result=mednexus_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        },config={
            "configurable": {"thread_id": session_id}, 
            "recursion_limit": 25
        })

        return execution_result["messages"][-1].content
    except Exception as e:
        return f"Agent Core Error: {str(e)}"
    
if __name__ == "__main__":
    print("\n=============================================")
    print("      MEDNEXUS AGENT TEST WORKSPACE          ")
    print("=============================================\n")
    
    # Scenario A: General Medical Inquiry (Should use NO tools)
    # print("\n>>> Scenario 1: General Medical Inquiry")
    # print(run_mednexus_agent("What is the typical clinical protocol for managing stage 2 hypertension?"))
    
    # Scenario B: Specific Patient Query (Should trigger RAG Search tool)
    # print("\n>>> Scenario 2: Target Patient Search")
    # print(run_mednexus_agent("What is diagnosis of Rohan and what medicines has doctor prescribed him?"))
    
    # Scenario C: File Modification Request (Should trigger Ingestion tool)
    print("\n>>> Scenario 3: Autonomous Database File Upload")
    print(run_mednexus_agent("doc123","Please upload the file 'lab_report_delta.pdf' into patient profile AMH-9011."))
    
    # Scenario D: Time-Period Trend Scanning (Should trigger Trend Analyzer tool)
    print("\n>>> Scenario 4: Historical Timeline Scan & Risk Alert")
    print(run_mednexus_agent("doc123","Run a scan on Rohan's records from January to May and let me know if he is becoming unwell."))