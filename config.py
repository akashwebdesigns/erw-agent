import os
from dotenv import load_dotenv

# Load .env as soon as config is imported
load_dotenv()

SERVICENOW_INSTANCE = os.getenv("SN_INSTANCE")
SERVICENOW_USERNAME = os.getenv("SN_USERNAME")
SERVICENOW_PASSWORD = os.getenv("SN_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
