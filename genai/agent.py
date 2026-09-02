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

llm=ChatGroq(groq_api_key=key, model="openai/gpt-oss-120b", temperature=0)

memorysaver=MemorySaver()

tool_belt=[search_patient_records,upload_patient_file,analyse_health_trends,lookup_patient_by_name]

agent_prompt="""You are MedNexus AI, an advanced, proactive clinical assistant.
Your goal is to assist clinicians by intelligently executing tasks using the tools provided to you.

CONVERSATION MEMORY & PATIENT CONTEXT RESOLUTION (CRITICAL):
- ALWAYS inspect recent conversation messages in memory before asking the user.
- If the clinician uses pronouns or implicit references like 'this patient', 'he', 'she', 'her', 'his', 'the patient', or 'summarize this report', automatically extract the patient name or hospital ID mentioned in recent previous messages (e.g., Neha Verma or Rohan Sharma) and pass that patient name/ID to the tool.
- NEVER ask the doctor to re-enter a patient name or hospital ID if it was already discussed, searched, or retrieved earlier in the current conversation thread!

CRITICAL ROUTING RULES:
- If the clinician asks to analyze health trends, check progress over time, review timeline trajectory, or evaluate if a patient is deteriorating/getting unwell over a timeframe (e.g., 'check health trends for past few months' or 'is patient getting worse'), use 'analyse_health_trends'.
- If the clinician asks to view, read, analyze, summarize, or check existing medical data/diagnoses/reports, use 'search_patient_records'.
- If the clinician explicitly asks to add, save, upload, or ingest a new file into the system, use 'upload_patient_file'.
- Always discover the formal Patient ID using 'lookup_patient_by_name' first if only a patient name is provided.

ANTI-LOOPING RULES (CRITICAL):
- DO NOT call the same tool more than twice.
- If a database search returns empty or fails, DO NOT keep retrying. Immediately stop and inform the user that the specific data is missing.
- Once you successfully retrieve the required data, immediately output your final clinical answer and stop tool usage.

CRITICAL FORMATTING RULES:
- When presenting patient medical summaries or report findings, default to clean, structured BULLET POINTS with bold section headings (e.g. 📋 **Primary Diagnosis**, 🔬 **Key Laboratory Results**, 💊 **Prescribed Treatment**, 💡 **Clinical Advice & Follow-up**). Bullet points are preferred for rapid clinician reading.
- Use Markdown tables ONLY for multi-date numerical lab/vital trends (e.g. Blood Pressure or Glucose over time) OR when the clinician explicitly requests a table (e.g., 'show this in a table').
- When using tools that require numeric inputs like age, you must pass them strictly as integers.
- Do not guess or hallucinate medical data. 
- Be professional, direct, and concise.
"""

mednexus_agent = create_react_agent(
    model=llm, 
    tools=tool_belt, 
    prompt=agent_prompt
)

def run_mednexus_agent(session_id: str, user_query: str) -> str:
    """Core execution handler with Option 3 State-Based Active Patient Context Management."""
    try:
        from backend.database import (
            get_chat_session_history, patients_collection,
            get_session_active_patient, update_session_active_patient
        )
        
        clean_query = user_query.strip()

        # Step 1: Dynamically scan query against MongoDB registry to detect patient mentions
        all_patients = list(patients_collection.find({}, {"_id": 0, "patient_id": 1, "name": 1}))
        for p in all_patients:
            p_name = p.get("name", "")
            p_id = p.get("patient_id", "")
            first_name = p_name.split()[0] if p_name else ""
            
            # If prompt mentions full name, first name, or formal Patient ID -> update active session state in MongoDB
            if (p_name and p_name.lower() in clean_query.lower()) or \
               (first_name and len(first_name) > 2 and first_name.lower() in clean_query.lower()) or \
               (p_id and p_id.lower() in clean_query.lower()):
                update_session_active_patient(session_id, p_id, p_name)
                break

        # Step 2: Retrieve current active patient session context from MongoDB
        active_patient = get_session_active_patient(session_id)

        # Step 3: Format user prompt with deterministic Active Patient Context
        final_user_prompt = clean_query
        if active_patient:
            final_user_prompt = f"[ACTIVE CONSULTATION PATIENT: {active_patient['name']} (ID: {active_patient['patient_id']})] {clean_query}"

        # Step 4: Build past conversation messages (last 6 turns, avoiding duplicates)
        past_msgs = get_chat_session_history(session_id)
        formatted_messages = []
        history_msgs = [m for m in past_msgs if m.get("content") != user_query]
        for m in history_msgs[-6:]:
            formatted_messages.append({"role": m["role"], "content": m["content"]})
        
        formatted_messages.append({"role": "user", "content": final_user_prompt})

        # Step 5: Invoke Agentic reasoning loop
        execution_result = mednexus_agent.invoke({
            "messages": formatted_messages
        }, config={
            "configurable": {"thread_id": session_id}, 
            "recursion_limit": 25
        })

        ai_response = execution_result["messages"][-1].content

        # Step 6: Post-execution check if tool output revealed patient details
        if not active_patient:
            for p in all_patients:
                if p.get("name") and p.get("name").lower() in ai_response.lower():
                    update_session_active_patient(session_id, p["patient_id"], p["name"])
                    break

        return ai_response

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