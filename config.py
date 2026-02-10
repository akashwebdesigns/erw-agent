import os
from dotenv import load_dotenv

# Load .env as soon as config is imported
load_dotenv()

SERVICENOW_INSTANCE = os.getenv("SN_INSTANCE")
SERVICENOW_USERNAME = os.getenv("SN_USERNAME")
SERVICENOW_PASSWORD = os.getenv("SN_PASSWORD")

INCIDENT_TABLE = "incident"
TEMP_WA_FIELD = "u_temporary_workaround"

def validate_config():
    missing = []
    if not SERVICENOW_INSTANCE:
        missing.append("SN_INSTANCE")
    if not SERVICENOW_USERNAME:
        missing.append("SN_USERNAME")
    if not SERVICENOW_PASSWORD:
        missing.append("SN_PASSWORD")

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
