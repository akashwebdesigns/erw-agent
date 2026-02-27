import os
import fitz
import faiss
import pickle
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env as soon as config is imported
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_RULE_PATH = "rules_repository"
INDEX_PATH = "rag/index.faiss"
META_PATH = "rag/metadata.pkl"

client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(api_version="v1beta"))

def embed_text(text):
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
    )
    return np.array(result.embeddings[0].values, dtype="float32")


def chunk_text(text, chunk_size=800, overlap=150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def extract_pdf_text(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def build_index():

    all_embeddings = []
    metadata = []

    for root, dirs, files in os.walk(BASE_RULE_PATH):
        for file in files:
            if file.endswith(".pdf"):

                file_path = os.path.join(root, file)

                parts = root.split(os.sep)
                state = parts[-2] if len(parts) >= 2 else ""
                line = parts[-1]

                company = file.replace("company_", "").replace(".pdf", "")

                text = extract_pdf_text(file_path)
                chunks = chunk_text(text)

                for chunk in chunks:
                    embedding = embed_text(chunk)
                    all_embeddings.append(embedding)
                    metadata.append({
                        "state": state,
                        "line": line,
                        "company": company,
                        "text": chunk
                    })

    dimension = len(all_embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(all_embeddings))

    os.makedirs("rag", exist_ok=True)

    faiss.write_index(index, INDEX_PATH)

    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print("RAG index built successfully.")


if __name__ == "__main__":
    build_index()