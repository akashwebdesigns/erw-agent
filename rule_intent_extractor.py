# import os
# import json
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY not found.")

# GEMINI_URL = (
#     "https://generativelanguage.googleapis.com/v1beta/models/"
#     "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
# )

# SYSTEM_PROMPT = """
# You are a policy rule extraction AI.

# Extract structured information from user question.

# Required:
# - state (2 letter uppercase, e.g., TX, FL)
# - line (Auto, Homeowners, etc.)
# - company (numeric string)
# - question (the actual rule question being asked)

# Rules:
# - Convert full state names to 2-letter code.
# - If field not present, return null.
# - Return ONLY valid JSON.
# """


# def extract_rule_fields(user_text: str):

#     payload = {
#         "contents": [
#             {
#                 "parts": [
#                     {"text": SYSTEM_PROMPT + "\nUser message:\n" + user_text}
#                 ]
#             }
#         ]
#     }

#     headers = {"Content-Type": "application/json"}

#     response = requests.post(
#         GEMINI_URL,
#         headers=headers,
#         json=payload,
#         timeout=30
#     )

#     response.raise_for_status()

#     raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]

#     try:
#         return json.loads(raw)
#     except Exception:
#         print("AI returned invalid JSON:", raw)
#         return {}

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found.")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

SYSTEM_PROMPT = """
You are a policy rule extraction AI.

Extract structured information from the user question.

Return ONLY valid JSON.

Required fields:
- state (2 letter uppercase, e.g., TX, FL)
- line (Auto, Homeowners, etc.)
- company (numeric string)
- question (the actual rule question being asked)

Rules:
- Convert full state names to 2-letter code.
- If field not present, return null.
- Do NOT include markdown.
"""


def clean_json_response(raw_text: str):
    """
    Removes markdown wrapping like ```json ... ```
    and safely parses JSON.
    """

    raw_text = raw_text.strip()

    # Remove ```json wrapper
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "")
        raw_text = raw_text.replace("```", "")
        raw_text = raw_text.strip()

    return json.loads(raw_text)


def extract_rule_fields(user_text: str):

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\nUser message:\n" + user_text}
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        GEMINI_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    try:
        parsed = clean_json_response(raw)
        print("PARSED RULE JSON:", parsed)
        return parsed
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        print("RAW RESPONSE:", raw)
        return {}