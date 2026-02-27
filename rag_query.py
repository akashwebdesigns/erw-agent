import numpy as np
import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "embedding-001:embedContent?key=" + GEMINI_API_KEY
)


def embed_query(text):

    payload = {
        "content": {
            "parts": [{"text": text}]
        }
    }

    response = requests.post(
        EMBED_URL,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return np.array(
        response.json()["embedding"]["values"],
        dtype="float32"
    )


def search(index, metadata, query, state, line, company, top_k=5):

    query_vector = embed_query(query)

    D, I = index.search(np.array([query_vector]), top_k * 3)

    results = []

    for idx in I[0]:
        record = metadata[idx]

        if (
            record["state"].upper() == state.upper()
            and record["line"].lower() == line.lower()
            and record["company"] == company
        ):
            results.append(record["text"])

        if len(results) == top_k:
            break

    return results
