# from sentence_transformers import SentenceTransformer, util

# # Load model once (global)
# model = SentenceTransformer("all-MiniLM-L6-v2")

# def rank_by_similarity(new_text: str, historical_incidents: list):
#     """
#     Rank historical incidents by semantic similarity.
#     """

#     if not historical_incidents:
#         return []

#     historical_texts = [
#         h["short_description"] for h in historical_incidents
#     ]

#     # Generate embeddings
#     new_embedding = model.encode(new_text, convert_to_tensor=True)
#     historical_embeddings = model.encode(historical_texts, convert_to_tensor=True)

#     # Compute cosine similarity
#     similarities = util.cos_sim(new_embedding, historical_embeddings)[0]

#     # Attach scores
#     scored_results = []
#     for i, h in enumerate(historical_incidents):
#         scored_results.append({
#             "incident": h,
#             "score": float(similarities[i])
#         })

#     # Sort by highest similarity
#     scored_results.sort(key=lambda x: x["score"], reverse=True)

#     return scored_results


from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")


def rank_by_similarity(new_text: str, historical_incidents: list, parsed_context: dict):
    if not historical_incidents:
        return []

    historical_texts = [
        h["short_description"] for h in historical_incidents
    ]

    new_embedding = model.encode(new_text, convert_to_tensor=True)
    historical_embeddings = model.encode(historical_texts, convert_to_tensor=True)

    similarities = util.cos_sim(new_embedding, historical_embeddings)[0]

    scored_results = []

    for i, h in enumerate(historical_incidents):
        semantic_score = float(similarities[i])

        # Context boosting
        state_boost = 1 if parsed_context["state"] and parsed_context["state"] in h["short_description"] else 0
        line_boost = 1 if parsed_context["line"] and parsed_context["line"] in h["short_description"] else 0
        company_boost = 1 if parsed_context["company"] and parsed_context["company"] in h["short_description"] else 0

        final_score = (
            0.7 * semantic_score
            + 0.1 * state_boost
            + 0.1 * line_boost
            + 0.1 * company_boost
        )

        scored_results.append({
            "incident": h,
            "semantic_score": round(semantic_score, 4),
            "final_score": round(final_score, 4)
        })

    scored_results.sort(key=lambda x: x["final_score"], reverse=True)

    return scored_results
