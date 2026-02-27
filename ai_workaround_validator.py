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
You are an insurance resolution validation AI.

Given:
- Incident short description
- Workaround steps
- Close notes

Determine whether the workaround successfully resolved the issue.

Return ONLY valid JSON:

{
  "result": "SUCCESS" or "FAILURE",
  "confidence": 0.0 to 1.0
}

Rules:
- If close notes mention policy posted, issue resolved, success → SUCCESS
- If notes mention failed, error persisted, reopened → FAILURE
- If unclear → FAILURE
- Do NOT explain.
"""


def safe_json(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return {"result": "FAILURE", "confidence": 0.0}


def validate_workaround(short_desc, workaround, close_notes):

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT +
                                f"\nShort Description: {short_desc}\n"
                                f"Workaround: {workaround}\n"
                                f"Close Notes: {close_notes}"
                    }
                ]
            }
        ]
    }

    response = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    return safe_json(raw_text)
