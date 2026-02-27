import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are an insurance policy expert.

Answer ONLY based on the provided policy excerpts.

If answer is not found, say:
"Information not found in provided policy rules."

Do NOT hallucinate.
"""


def generate_answer(question, chunks):

    context = "\n\n".join(chunks)

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text":
                            SYSTEM_PROMPT +
                            "\n\nPolicy Excerpts:\n" +
                            context +
                            "\n\nQuestion:\n" +
                            question
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

    return response.json()["candidates"][0]["content"]["parts"][0]["text"]
