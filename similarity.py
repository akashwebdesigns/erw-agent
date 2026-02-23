from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def rank_by_similarity(new_text: str, historical_incidents: list, parsed_context: dict):
    if not historical_incidents:
        return []

    # SAFE handling of None values
    texts = [new_text or ""] + [
        h.get("short_description") or ""
        for h in historical_incidents
    ]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    scored_results = []

    for i, h in enumerate(historical_incidents):
        semantic_score = float(similarities[i])

        short_desc_hist = h.get("short_description") or ""

        state_boost = 1 if parsed_context.get("state") and parsed_context["state"] in short_desc_hist else 0
        line_boost = 1 if parsed_context.get("line") and parsed_context["line"] in short_desc_hist else 0
        company_boost = 1 if parsed_context.get("company") and parsed_context["company"] in short_desc_hist else 0

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
