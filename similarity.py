from sentence_transformers import SentenceTransformer, util

# Load model once (global)
model = SentenceTransformer("all-MiniLM-L6-v2")

def rank_by_similarity(new_text: str, historical_incidents: list):
    """
    Rank historical incidents by semantic similarity.
    """

    if not historical_incidents:
        return []

    historical_texts = [
        h["short_description"] for h in historical_incidents
    ]

    # Generate embeddings
    new_embedding = model.encode(new_text, convert_to_tensor=True)
    historical_embeddings = model.encode(historical_texts, convert_to_tensor=True)

    # Compute cosine similarity
    similarities = util.cos_sim(new_embedding, historical_embeddings)[0]

    # Attach scores
    scored_results = []
    for i, h in enumerate(historical_incidents):
        scored_results.append({
            "incident": h,
            "score": float(similarities[i])
        })

    # Sort by highest similarity
    scored_results.sort(key=lambda x: x["score"], reverse=True)

    return scored_results
