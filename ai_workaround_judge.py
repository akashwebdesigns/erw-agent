import google.generativeai as genai
from config import *

validate_config()

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def evaluate_workaround(temp_wa, work_notes, state):

    prompt = f"""
You are an insurance policy troubleshooting AI.

Determine if this workaround actually solved the issue.

Temporary Workaround:
{temp_wa}

Work Notes:
{work_notes}

Incident State:
{state}

Rules:
- SUCCESS if issue resolved or policy posted.
- FAILURE if same error returned or workaround failed.
- UNKNOWN if unclear.

Return ONLY JSON:

{{
"result":"SUCCESS|FAILURE|UNKNOWN",
"confidence":0.0-1.0,
"reason":"short reason"
}}
"""

    response = model.generate_content(prompt)

    return response.text
