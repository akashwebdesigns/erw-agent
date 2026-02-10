from fastapi import FastAPI, HTTPException
from servicenow import get_incident



app = FastAPI(title="ERW Auto-Triage Agent")

@app.post("/triage")
def triage(payload: dict):
    sys_id = payload.get("sys_id")
    number = payload.get("number")

    if not sys_id:
        raise HTTPException(status_code=400, detail="sys_id missing")

    incident = get_incident(sys_id)

    print("\n========== INCIDENT RECEIVED ==========")
    print("Incident Number :", number)
    print("Short Description :", incident.get("short_description"))
    print("Description :", incident.get("description"))
    print("Temporary Workaround :", incident.get("u_temporary_workaround"))
    print("State :", incident.get("state"))
    print("======================================\n")

    return {
        "status": "success",
        "incident_number": number
    }
