from incident_parser import parse_short_description

from servicenow import get_incident, search_incidents_by_erw
from fastapi import FastAPI, HTTPException




app = FastAPI(title="ERW Auto-Triage Agent")

@app.post("/triage")
def triage(payload: dict):
    sys_id = payload.get("sys_id")
    number = payload.get("number")

    if not sys_id:
        raise HTTPException(status_code=400, detail="sys_id missing")

    # Fetch current incident
    incident = get_incident(sys_id)

    short_desc = incident.get("short_description")
    description = incident.get("description")
    temp_wa = incident.get("u_temporary_workaround")
    state = incident.get("state")

    # Parse structured fields
    parsed = parse_short_description(short_desc)
    erw_code = parsed.get("erw_code")

    # Search historical incidents using ERW anchor
    historical = []
    if erw_code:
        historical = search_incidents_by_erw(erw_code, sys_id)

    print("\n========== INCIDENT RECEIVED ==========")
    print("Incident Number :", number)
    print("Short Description :", short_desc)
    print("Description :", description)
    print("Temporary Workaround :", temp_wa)
    print("State :", state)
    print("Parsed Fields :", parsed)
    print("Found Historical Incidents :", len(historical))

    for h in historical:
        print(" -", h["number"], "|", h["short_description"])

    print("=======================================\n")

    return {
        "status": "success",
        "incident_number": number,
        "parsed": parsed,
        "historical_count": len(historical)
    }

