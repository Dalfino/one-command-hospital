"""Hybrid retrieval for the guideline corpus.

BM25 always runs; an optional sentence-transformer backend (all-MiniLM-L6-v2)
adds a semantic channel. Combined score = alpha * norm(BM25) + (1-alpha) * cosine.
Set VECTOR_BACKEND=sbert to enable; HYBRID_ALPHA to tune (0 = pure vector).
Env-driven, graceful degradation: if the model can't load, BM25-only is used
and the /health endpoint reports the active engine honestly.
"""
import os
import re

from rank_bm25 import BM25Okapi

WORD = re.compile(r"[a-z0-9]+")


def _minmax(scores):
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [0.0] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


class HybridRetriever:
    def __init__(self, sections):
        self.sections = sections
        self.alpha = float(os.environ.get("HYBRID_ALPHA", "0.5"))
        backend = os.environ.get("VECTOR_BACKEND", "bm25").lower()
        self.model = None
        self.emb = None
        self.bm25 = BM25Okapi([WORD.findall(s["text"].lower()) for s in sections])
        if backend == "sbert":
            try:
                from sentence_transformers import SentenceTransformer

                name = os.environ.get("SBERT_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                self.model = SentenceTransformer(name)
                self.emb = self.model.encode(
                    [s["text"] for s in sections], normalize_embeddings=True
                )
            except Exception as e:  # never crash the service over an optional model
                print(f"[retrieval] sbert unavailable ({e.__class__.__name__}); BM25-only")

    @property
    def engine(self) -> str:
        return f"hybrid-bm25+sbert(alpha={self.alpha})" if self.model else "bm25"

    def search(self, query: str, k: int = 3):
        q = WORD.findall(query.lower())
        bm = _minmax(self.bm25.get_scores(q))
        if self.model is not None:
            import numpy as np

            qv = self.model.encode([query], normalize_embeddings=True)[0]
            cos = self.emb @ qv
            combined = [self.alpha * bm[i] + (1 - self.alpha) * float(cos[i]) for i in range(len(bm))]
        else:
            combined = bm
        order = sorted(range(len(combined)), key=lambda i: -combined[i])[:k]
        return [{"index": i, "score": combined[i]} for i in order]
