from incident_parser import parse_short_description
from similarity import rank_by_similarity
from servicenow import get_incident, search_incidents_by_erw, create_incident
from fastapi import FastAPI, HTTPException
from ai_workaround_judge import evaluate_workaround
from ai_intent_extractor import extract_incident_fields
from ai_workaround_validator import validate_workaround
from rule_intent_extractor import extract_rule_fields
import numpy as np
import requests
import os
from dotenv import load_dotenv

app = FastAPI(title="ERW Auto-Triage Agent")
from rag_builder import embed_text

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found.")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)



from rag_loader import load_rag
from rag_query import search
from rag_answer import generate_answer

index, metadata = load_rag()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



REQUIRED_FIELDS = ["state", "line", "company", "erw_code", "description"]


@app.post("/chat-create-incident")
def chat_create_incident(data: dict):

    user_query = data.get("query")
    collected_data = data.get("collected_data", {})

    # ==============================
    # STEP 1 — Extract using AI
    # ==============================
    extracted = extract_incident_fields(user_query)

    if extracted is None:
        extracted = {}

    # Merge previous + new
    extracted = {**collected_data, **extracted}

    # ======================================================
    # FIX #2 — PREVENT HALLUCINATED GENERIC DESCRIPTIONS
    # ======================================================
    if extracted.get("description"):
        desc = extracted["description"].strip().lower()

        generic_phrases = [
            "new incident",
            "incident",
            "create incident",
            "incident creation",
            "log incident"
        ]

        if desc in generic_phrases:
            extracted["description"] = None

    print("CURRENT EXTRACTED DATA:", extracted)

    # ==============================
    # STEP 2 — Check Missing Fields
    # ==============================
    missing = [
        field for field in REQUIRED_FIELDS
        if not extracted.get(field)
    ]

    if missing:
        return {
            "status": "incomplete",
            "missing_fields": missing,
            "collected_data": extracted
        }

    # ==============================
    # STEP 3 — Create Incident
    # ==============================
    state = extracted["state"]
    line = extracted["line"]
    company = extracted["company"]
    txn_type = extracted.get("txn_type")
    erw_code = extracted["erw_code"]
    description = extracted["description"]

    short_description = f"{state} {line} {company} "
    if txn_type:
        short_description += f"{txn_type} "
    short_description += f"{erw_code} {description}"

    created = create_incident(short_description, description)
    sys_id = created["sys_id"]

    # ==============================
    # STEP 4 — Similarity Retrieval
    # ==============================
    parsed = parse_short_description(short_description)
    historical = search_incidents_by_erw(parsed["erw_code"], sys_id)

    ranked = rank_by_similarity(short_description, historical, parsed)

    # ==============================
    # STEP 5 — AI VALIDATION + CONFIDENCE FUSION
    # ==============================
    validated_results = []

    for r in ranked:

        incident_hist = r["incident"]

        workaround = incident_hist.get("u_temporary_workaround")
        close_notes = incident_hist.get("close_notes") or ""

        # ❌ Skip if no workaround present
        if not workaround:
            continue

        # 🤖 Ask Gemini if workaround worked
        ai_result = validate_workaround(
            incident_hist.get("short_description"),
            workaround,
            close_notes
        )

        if ai_result.get("result") != "SUCCESS":
            continue

        ai_confidence = ai_result.get("confidence", 0.0)

        # 🧠 AI Confidence Fusion
        final_confidence = (
            0.5 * r["semantic_score"] +
            0.3 * ai_confidence +
            0.2 * r["structured_boost"]
        )

        # Apply threshold
        if final_confidence < 0.6:
            continue

        validated_results.append({
            "incident_number": incident_hist["number"],
            "confidence": round(final_confidence, 2),
            "workaround": workaround
        })

    # Sort by confidence
    validated_results.sort(
        key=lambda x: x["confidence"],
        reverse=True
    )

    return {
        "status": "created",
        "created_incident": created["number"],
        "suggestions": validated_results[:3]
    }




@app.post("/ask-rule")
def ask_rule(data: dict):

    try:
        user_query = data.get("query")

        if not user_query:
            return {"error": "Query required."}

        # =====================================
        # STEP 1 — Extract structured fields
        # =====================================
        extracted = extract_rule_fields(user_query)

        print("RULE EXTRACTED:", extracted)

        if not isinstance(extracted, dict):
            extracted = {}

        state = extracted.get("state")
        line = extracted.get("line")
        company = extracted.get("company")
        question = extracted.get("question")

        # =====================================
        # STEP 2 — Validate Required Fields
        # =====================================
        missing = []

        if not state:
            missing.append("state")
        if not line:
            missing.append("line")
        if not company:
            missing.append("company")

        if missing:
            return {
                "status": "incomplete",
                "missing_fields": missing,
                "extracted": extracted
            }

        # =====================================
        # STEP 3 — Build Semantic Search Query
        # =====================================
        search_query = f"{state} {line} {company} {question}"

        embedding = embed_text(search_query)

        if embedding is None or len(embedding) == 0:
            return {"error": "Embedding generation failed."}

        embedding_array = np.array(embedding).astype("float32").reshape(1, -1)

        # =====================================
        # STEP 4 — FAISS Search
        # =====================================
        D, I = index.search(embedding_array, 5)

        retrieved_chunks = []

        for idx in I[0]:
            if 0 <= idx < len(metadata):
                chunk_data = metadata[idx]

                # If metadata is dict, extract text
                if isinstance(chunk_data, dict):
                    retrieved_chunks.append(chunk_data.get("text", ""))
                else:
                    retrieved_chunks.append(chunk_data)

        # Remove empty chunks
        retrieved_chunks = [c for c in retrieved_chunks if c]

        if not retrieved_chunks:
            return {
                "status": "success",
                "state": state,
                "line": line,
                "company": company,
                "answer": "Not found in rules."
            }

        context = "\n\n".join(retrieved_chunks)

        # =====================================
        # STEP 5 — Ask Gemini With Context
        # =====================================
        final_prompt = f"""
You are an insurance rule assistant.

Answer strictly and ONLY based on the provided context.
If the answer is not present in the context, reply exactly:
"Not found in rules."

Context:
{context}

Question:
{question}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": final_prompt}
                    ]
                }
            ]
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            GEMINI_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        raw_answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        answer = raw_answer.strip()

        return {
            "status": "success",
            "state": state,
            "line": line,
            "company": company,
            "answer": answer
        }

    except Exception as e:
        print("ASK RULE ERROR:", str(e))
        return {"error": str(e)}


