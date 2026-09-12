import os
from dotenv import load_dotenv
from groq import Groq

from core.rag import (
    load_knowledge_base,
    create_documents,
    create_vector_index,
    search_knowledge_base,
)

# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found. Please add it to your .env file."
    )

# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(api_key=api_key)

# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an AI Industrial Fault Detection, Diagnostic and
Maintenance Response Agent.

Your job is to help technicians investigate industrial
machine incidents using the provided Knowledge Base.

You are a DECISION-SUPPORT system.

You must NOT claim that a diagnosis is guaranteed.

You must:
1. Analyze the reported symptoms.
2. Use the provided Knowledge Base as the primary source.
3. Identify the most likely possible causes.
4. Explain the evidence behind each possible cause.
5. Recommend safe diagnostic checks.
6. Recommend safe troubleshooting actions.
7. Assess the severity of the incident.
8. Clearly identify when the machine should be stopped.
9. Recommend escalation when qualified maintenance personnel
   are required.
10. Never instruct the user to bypass guards, interlocks,
    alarms, or safety systems.
11. Never tell a user to approach dangerous moving machinery.
12. Electrical, high-energy, hazardous-fluid, severe
    vibration, fire, smoke, or dangerous overheating
    situations require appropriate safety procedures and
    qualified personnel.

IMPORTANT:
Separate observed symptoms from possible causes.

If the provided Knowledge Base does not contain enough
information, say so instead of inventing technical facts.

Return your response using this structure:

INCIDENT SUMMARY

SEVERITY

OBSERVED SYMPTOMS

MOST LIKELY CAUSES

WHY THESE CAUSES ARE POSSIBLE

RECOMMENDED DIAGNOSTIC CHECKS

SAFE TROUBLESHOOTING STEPS

MACHINE STOP RECOMMENDATION

SAFETY WARNING

ESCALATION

CONFIDENCE & LIMITATIONS
"""

# ============================================================
# INITIALIZE RAG
# ============================================================

print("Loading Industrial Maintenance Knowledge Base...")

df = load_knowledge_base()
documents = create_documents(df)
model, index = create_vector_index(documents)

print("Knowledge Base and RAG ready.")

# ============================================================
# AI DIAGNOSTIC FUNCTION
# ============================================================

def diagnose_incident(
    machine,
    problem,
    additional_information=""
):

    query = f"""
Machine: {machine}

Reported Problem:
{problem}

Additional Information:
{additional_information}
"""

    # --------------------------------------------------------
    # Retrieve relevant Knowledge Base information
    # --------------------------------------------------------

    results = search_knowledge_base(
        query,
        documents,
        model,
        index,
        top_k=3
    )

    retrieved_context = "\n\n".join(
        [
            f"KNOWLEDGE BASE RESULT {i + 1}:\n{result['document']}"
            for i, result in enumerate(results)
        ]
    )

    # --------------------------------------------------------
    # Send retrieved information to Groq
    # --------------------------------------------------------

    user_prompt = f"""
Analyze the following industrial maintenance incident.

MACHINE:
{machine}

PROBLEM:
{problem}

ADDITIONAL INFORMATION:
{additional_information}

RELEVANT KNOWLEDGE BASE INFORMATION:
{retrieved_context}

Use the Knowledge Base information above to produce a
careful diagnostic response.

Do not invent information that is not supported by the
Knowledge Base or the incident information.
"""

    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME", "openai/gpt-oss-20b"),
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2,
        max_tokens=1500
    )

    return response.choices[0].message.content

# ============================================================
# TEST THE AGENT
# ============================================================

if __name__ == "__main__":

    print("\n======================================")
    print("AI INDUSTRIAL DIAGNOSTIC AGENT")
    print("======================================")

    machine = "Industrial Motor"

    problem = """
The motor is overheating and there is excessive vibration.
The machine has been running continuously.
"""

    print("\nAnalyzing incident...\n")

    result = diagnose_incident(
        machine=machine,
        problem=problem
    )

    print(result)
