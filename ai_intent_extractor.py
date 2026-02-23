import os
import json
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are an insurance incident extraction AI.

Extract structured fields from user message.

Required fields:
- state (2 letter uppercase, e.g., TX, KY)
- line (numeric string)
- company (numeric string)
- erw_code (format ABCD-12)
- description (short problem description)

Optional:
- txn_type (endorsement, renewal, new business, termination, etc.)

Rules:
- Convert full state names to 2-letter code.
- If field not present, return null.
- Return ONLY valid JSON.
"""


def extract_incident_fields(user_text: str) -> dict:

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT + "\nUser message:\n" + user_text
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        GEMINI_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    try:
        return json.loads(raw_text)
    except Exception:
        print("AI returned invalid JSON:", raw_text)
        return {}
