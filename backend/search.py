"""
Semantic search over the Q&A knowledge base.
Loads the JSON, embeds all questions once on startup, then answers
similarity queries using cosine distance.
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"   # small, fast, good quality

_model: SentenceTransformer | None = None
_records: list[dict] = []
_embeddings: np.ndarray | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def load_knowledge_base(path: str) -> None:
    """Load and embed the Q&A JSON. Call once at startup."""
    global _records, _embeddings

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Only index entries that have at least one answer
    _records = []
    for entry in raw:
        answers = entry.get("answers", [])
        if not answers:
            continue
        # Collect all answer texts
        answer_texts = [a.get("text", "").strip() for a in answers if a.get("text")]
        if not answer_texts:
            continue
        _records.append({
            "number": entry.get("number"),
            "title": entry.get("title", ""),
            "question": entry.get("text", "").strip(),
            "answers": answer_texts,
            "subcategory": entry.get("subcategory", ""),
            "category": entry.get("category", ""),
        })

    # Embed: combine title + question for richer signal
    texts = [f"{r['title']} {r['question']}" for r in _records]
    model = _get_model()
    _embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    print(f"Knowledge base loaded: {len(_records)} records indexed.")


def search(query: str, top_k: int = 3) -> list[dict]:
    """Return the top-k most similar records for a query."""
    if _embeddings is None or len(_records) == 0:
        return []

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True)[0]
    scores = _embeddings @ q_emb          # cosine similarity (embeddings are normalised)
    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_idx:
        rec = _records[idx].copy()
        rec["score"] = float(scores[idx])
        results.append(rec)
    return results
