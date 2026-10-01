from __future__ import annotations

import re
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def _clean_text(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"\b(?:tk|vr|c)\d+\b", " ", s)
    s = re.sub(r"\b\d{4,}\b", " ", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def low_csat_themes(df: pd.DataFrame, agent_id: str, top_n: int = 6) -> dict:
    """Local, zero-API NLP summary for one agent's low-CSAT tickets.

    Uses recorded categories plus TF-IDF phrases. It deliberately avoids pretending that
    a local keyword extractor has human-level causal understanding.
    """
    subset = df[(df["agent_id"] == agent_id) & (df["csat_score"].notna()) & (df["csat_score"] <= 2)].copy()
    if subset.empty:
        return {"tickets": 0, "categories": [], "phrases": []}

    cat_counts = subset["category"].value_counts().head(top_n)
    categories = [
        {"category": idx, "tickets": int(val), "share": float(val / len(subset))}
        for idx, val in cat_counts.items()
    ]

    docs = (
        subset["customer_message"].fillna("").map(_clean_text)
        + " "
        + subset["agent_notes"].fillna("").map(_clean_text)
    )
    docs = docs[docs.str.len() >= 8]
    phrases: list[str] = []
    if len(docs) >= 3:
        try:
            vec = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.85,
                max_features=500,
            )
            x = vec.fit_transform(docs)
            scores = x.mean(axis=0).A1
            terms = vec.get_feature_names_out()
            ranked = scores.argsort()[::-1]
            phrases = [terms[i] for i in ranked[:top_n] if scores[i] > 0]
        except ValueError:
            phrases = []

    return {
        "tickets": int(len(subset)),
        "categories": categories,
        "phrases": phrases,
    }
