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


def _load_json_files(path: str) -> list[dict]:
    """Load one JSON file or all JSON files in a directory."""
    if os.path.isdir(path):
        entries = []
        files = sorted(f for f in os.listdir(path) if f.endswith(".json"))
        if not files:
            raise FileNotFoundError(f"No .json files found in directory: {path}")
        for fname in files:
            fpath = os.path.join(path, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries.extend(data if isinstance(data, list) else [data])
            print(f"  Loaded {fname} ({len(data)} entries)")
        return entries
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]


def load_knowledge_base(path: str) -> None:
    """Load and embed Q&A records from a file or directory. Call once at startup."""
    global _records, _embeddings

    print(f"Loading knowledge base from: {path}")
    raw = _load_json_files(path)

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


def search(
    query: str,
    top_k: int = 3,
    category: str | None = None,
    subcategory: str | None = None,
) -> list[dict]:
    """Return the top-k most similar records for a query.

    If category/subcategory are provided, search is restricted to matching
    records. Falls back to global search if no records match the filter.
    """
    if _embeddings is None or len(_records) == 0:
        return []

    # Build index mask for category filter
    def matches_filter(rec):
        if category and rec["category"].lower() != category.lower():
            return False
        if subcategory and rec["subcategory"].lower() != subcategory.lower():
            return False
        return True

    indices = [i for i, r in enumerate(_records) if matches_filter(r)]

    # If a filter was requested but nothing matched, signal the caller
    if (category or subcategory) and not indices:
        return [], False   # (results, category_found)

    if not indices:
        indices = list(range(len(_records)))

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True)[0]

    # Score only the filtered subset
    subset_scores = _embeddings[indices] @ q_emb
    top_local = np.argsort(subset_scores)[::-1][:top_k]

    results = []
    for local_idx in top_local:
        global_idx = indices[local_idx]
        rec = _records[global_idx].copy()
        rec["score"] = float(subset_scores[local_idx])
        results.append(rec)
    return results, True   # (results, category_found)
