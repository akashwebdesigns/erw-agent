import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

SYSTEM_PROMPT = """
You are an AI router that decides which tool should handle the user request.

TOOLS AVAILABLE:

1. create_incident
Use when user wants to log an incident, troubleshoot ERW errors, or posting errors.

2. ask_rule
Use when user asks about insurance rules, policies, cancellation periods, coverage requirements.

Return ONLY JSON:

{
  "tool": "create_incident"
}

OR

{
  "tool": "ask_rule"
}
"""


def detect_tool(user_query):

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT + "\n\nUser query:\n" + user_query
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

    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    # remove markdown
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except:
        return {"tool": "create_incident"}  # fallback