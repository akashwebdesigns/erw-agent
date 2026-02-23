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

def search_incidents_by_erw(erw_code: str, exclude_sys_id: str, limit: int = 20):
    """
    Fetch historical incidents containing the same ERW code
    Excludes the current incident.
    Prefers resolved/closed incidents.
    """

    query = (
        f"short_descriptionLIKE{erw_code}"
        f"^sys_id!={exclude_sys_id}"
        f"^stateIN6,7"  # 6 = Resolved, 7 = Closed (default SN states)
    )

    url = f"{SERVICENOW_INSTANCE}/api/now/table/{INCIDENT_TABLE}"

    params = {
        "sysparm_query": query,
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,number,short_description,state,u_temporary_workaround,close_notes"
    }

    response = requests.get(
        url,
        auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    return response.json()["result"]

    
def create_incident(short_description: str, description: str):

    url = f"{SERVICENOW_INSTANCE}/api/now/table/{INCIDENT_TABLE}"

    payload = {
        "short_description": short_description,
        "description": description,
        "caller_id": "a8f98bb0eb32010045e1a5115206fe3a"
    }

    print("CREATE INCIDENT PAYLOAD:", payload)

    response = requests.post(
        url,
        auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
        headers=HEADERS,
        json=payload,
        timeout=90
    )

    # response.raise_for_status()
    if not response.ok:
        print("SERVICE NOW ERROR:")
        print(response.status_code)
        print(response.text)
        response.raise_for_status()

    return response.json()["result"]



