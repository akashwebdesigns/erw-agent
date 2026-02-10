import requests
from config import *

validate_config()

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_incident(sys_id: str) -> dict:
    url = f"{SERVICENOW_INSTANCE}/api/now/table/{INCIDENT_TABLE}/{sys_id}"
    response = requests.get(
        url,
        auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()
    return response.json()["result"]
