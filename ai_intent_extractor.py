import os
import json
import requests
import re

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
- description (exact issue text from user)

Optional:
- txn_type (endorsement, renewal, new business, termination, etc.)

STRICT RULES:
- If a field is not explicitly mentioned by the user, return null.
- DO NOT invent or generate placeholder values.
- DO NOT summarize.
- Description must come directly from user text.
- Return ONLY valid JSON.
"""



def safe_json_extract(text: str) -> dict:
    """
    Cleans Gemini output and extracts valid JSON.
    Handles ```json ... ``` blocks.
    """

    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text)
        text = text.strip()

    # Try direct JSON load
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try extracting JSON object manually
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    print("AI returned invalid JSON:", text)
    return {}


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

    extracted = safe_json_extract(raw_text)

    # Always return structured dictionary safely
    return {
        "state": extracted.get("state"),
        "line": extracted.get("line"),
        "company": extracted.get("company"),
        "erw_code": extracted.get("erw_code"),
        "description": extracted.get("description"),
        "txn_type": extracted.get("txn_type")
    }
