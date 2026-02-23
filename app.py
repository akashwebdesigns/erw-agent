from incident_parser import parse_short_description
from similarity import rank_by_similarity
from servicenow import get_incident, search_incidents_by_erw, create_incident
from fastapi import FastAPI, HTTPException
from ai_workaround_judge import evaluate_workaround
from ai_intent_extractor import extract_incident_fields





app = FastAPI(title="ERW Auto-Triage Agent")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# @app.post("/triage")
# def triage(payload: dict):
#     try:
#         sys_id = payload.get("sys_id")
#         number = payload.get("number")

#         if not sys_id:
#             raise HTTPException(status_code=400, detail="sys_id missing")

#         # Fetch current incident
#         incident = get_incident(sys_id)

#         short_desc = incident.get("short_description")
#         description = incident.get("description")
#         temp_wa = incident.get("u_temporary_workaround")
#         state = incident.get("state")

#         # Parse structured fields
#         parsed = parse_short_description(short_desc)
#         erw_code = parsed.get("erw_code")

#         # Search historical incidents using ERW anchor
#         historical = []
#         if erw_code:
#             historical = search_incidents_by_erw(erw_code, sys_id)
        
#         print("DEBUG 1 - After fetching incident")

#         # Rank by semantic similarity (safe for None)
#         ranked = []
#         if historical:
#             print("DEBUG 1 - After fetching incident")
#             ranked = rank_by_similarity(short_desc or "", historical, parsed)

#         print("\n========== INCIDENT RECEIVED ==========")
#         print("Incident Number :", number)
#         print("Short Description :", short_desc)
#         print("Description :", description)
#         print("Temporary Workaround :", temp_wa)
#         print("State :", state)
#         print("Parsed Fields :", parsed)
#         print("Found Historical Incidents :", len(historical))

#         if ranked:
#             print("\nSimilarity Ranking:")
#             for r in ranked:
#                 print(
#                     f" - {r['incident']['number']} | "
#                     f"Semantic: {r['semantic_score']} | "
#                     f"Final: {r['final_score']} | "
#                     f"{r['incident']['short_description']}"
#                 )
#         else:
#             print("No historical incidents to rank.")

#         print("=======================================\n")

#         return {
#             "status": "success",
#             "incident_number": number,
#             "parsed": parsed,
#             "historical_count": len(historical),
#             "top_match": ranked[0]["incident"]["number"] if ranked else None
#         }

#     except Exception as e:
#         print("FULL ERROR TRACE:")
#         traceback.print_exc()
#         return {"error": str(e)}


# @app.post("/chat-create-incident")
# def chat_create_incident(data: dict):
#     state = data.get("state")
#     line = data.get("line")
#     company = data.get("company")
#     txn_type = data.get("txn_type")
#     erw_code = data.get("erw_code")
#     description = data.get("description")

#     short_description = f"{state} {line} {company} "
#     if txn_type:
#         short_description += f"{txn_type} "
#     short_description += f"{erw_code} {description}"

#     # Create incident
#     created = create_incident(short_description, description)

#     sys_id = created["sys_id"]

#     # Run triage internally
#     incident = get_incident(sys_id)
#     parsed = parse_short_description(short_description)
#     historical = search_incidents_by_erw(parsed["erw_code"], sys_id)
#     ranked = rank_by_similarity(short_description, historical, parsed)

#     return {
#         "created_incident": created["number"],
#         "suggestions": [
#             {
#                 "incident_number": r["incident"]["number"],
#                 "confidence": r["final_score"],
#                 "workaround": r["incident"].get("u_temporary_workaround")
#             }
#             for r in ranked[:3]
#         ]
#     }



@app.post("/chat-create-incident")
def chat_create_incident(data: dict):

    state = data.get("state")
    line = data.get("line")
    company = data.get("company")
    txn_type = data.get("txn_type")
    erw_code = data.get("erw_code")
    description = data.get("description")

    # ===============================
    # BUILD SHORT DESCRIPTION
    # ===============================
    short_description = f"{state} {line} {company} "
    if txn_type:
        short_description += f"{txn_type} "
    short_description += f"{erw_code} {description}"

    # ===============================
    # CREATE INCIDENT
    # ===============================
    created = create_incident(short_description, description)
    sys_id = created["sys_id"]

    # ===============================
    # RUN TRIAGE
    # ===============================
    incident = get_incident(sys_id)

    parsed = parse_short_description(short_description)

    historical = search_incidents_by_erw(
        parsed["erw_code"],
        sys_id
    )

    ranked = rank_by_similarity(
        short_description,
        historical,
        parsed
    )

    # ===============================
    # AI WORKAROUND EVALUATION
    # ===============================
    final_suggestions = []

    for r in ranked:

        inc = r["incident"]

        temp_wa = inc.get("u_temporary_workaround", "")
        work_notes = inc.get("close_notes", "")
        inc_state = inc.get("state", "")

        # Skip empty workaround directly
        if not temp_wa:
            continue

        try:
            ai_result = evaluate_workaround(
                temp_wa,
                work_notes,
                inc_state
            )

            print("AI RESULT:", ai_result)

            # VERY SIMPLE FILTER FOR NOW
            if "SUCCESS" in ai_result.upper():

                final_suggestions.append({
                    "incident_number": inc["number"],
                    "confidence": r["final_score"],
                    "workaround": temp_wa
                })

        except Exception as e:
            print("AI evaluation failed:", str(e))

    # ===============================
    # RETURN RESPONSE
    # ===============================
    return {
        "created_incident": created["number"],
        "suggestions": final_suggestions[:3]
    }


@app.post("/test-extract")
def test_extract(data: dict):
    return extract_incident_fields(data.get("query"))



