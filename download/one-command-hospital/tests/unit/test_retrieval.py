"""Unit tier — hybrid retrieval math.

The retrieval gate is the FIRST safety net (refuse before you answer), so its
scoring math is contract-tested: BM25 ranking, min-max normalisation edges,
the k limit, and the alpha-blended hybrid channel with a fake vector model.
"""
import numpy as np
import pytest

from retrieval import HybridRetriever, _minmax

SECTIONS = [
    {"corpus_id": "ANTICOAG-BRIDGE", "section": "4",
     "text": "[Anticoagulation Bridging — §4 Perioperative management] "
             "warfarin heparin bridging INR withhold dose perioperative"},
    {"corpus_id": "GLYCEMIC-CTRL", "section": "2",
     "text": "[Inpatient Glycemic Control — §2 Insulin dosing] "
             "insulin basal bolus correction glucose sliding scale units"},
    {"corpus_id": "SEPSIS-SCREEN", "section": "1",
     "text": "[Sepsis Screening — §1 Screening criteria] "
             "sepsis lactate qSOFA screening criteria suspicion infection"},
]


@pytest.fixture()
def retriever(monkeypatch):
    monkeypatch.setenv("VECTOR_BACKEND", "bm25")
    return HybridRetriever(SECTIONS)


def test_bm25_ranks_relevant_section_first(retriever):
    out = retriever.search("how do I bridge warfarin before surgery?", k=3)
    assert out[0]["index"] == 0


def test_scores_are_sorted_descending(retriever):
    out = retriever.search("insulin dosing", k=3)
    scores = [r["score"] for r in out]
    assert scores == sorted(scores, reverse=True)


def test_k_limits_result_count(retriever):
    assert len(retriever.search("sepsis", k=1)) == 1
    assert len(retriever.search("sepsis", k=3)) == 3


def test_engine_reports_bm25_honestly(retriever):
    assert retriever.engine == "bm25"


def test_minmax_flat_scores_do_not_divide_by_zero():
    assert _minmax([3.0, 3.0, 3.0]) == [0.0, 0.0, 0.0]


def test_minmax_spans_to_unit_interval():
    out = _minmax([2.0, 4.0])
    assert out == [0.0, 1.0]


class _FakeModel:
    """Vector channel with controllable disagreement: corpus docs get fixed
    basis vectors by their marker word; any query string gets QUERY_VEC (set
    per test). alpha semantics are then pinned exactly."""

    QUERY_VEC = np.array([0.0, 1.0, 0.0])

    def encode(self, texts, normalize_embeddings=False):
        basis = {"warfarin": [1.0, 0.0, 0.0],      # doc 0's direction
                 "insulin": [0.0, 1.0, 0.0],       # doc 1's direction
                 "sepsis": [0.0, 0.0, 1.0]}        # doc 2's direction
        out = []
        for t in texts:
            for marker, vec in basis.items():
                if marker in t:
                    out.append(np.array(vec))
                    break
            else:
                out.append(self.QUERY_VEC)
        return np.array(out)


def _with_vector_channel(monkeypatch, alpha):
    monkeypatch.setenv("VECTOR_BACKEND", "bm25")   # avoid attempting real sbert
    r = HybridRetriever(SECTIONS)
    r.alpha = alpha
    r.model = _FakeModel()
    r.emb = r.model.encode([s["text"] for s in SECTIONS], normalize_embeddings=True)
    return r


def test_alpha_zero_means_vector_channel_wins(monkeypatch):
    r = _with_vector_channel(monkeypatch, alpha=0.0)
    # Query hits no corpus word → BM25 flat (all 0.0); vector points at doc 1.
    out = r.search("completely unrelated query words", k=3)
    assert out[0]["index"] == 1


def test_alpha_one_means_bm25_wins(monkeypatch):
    r = _with_vector_channel(monkeypatch, alpha=1.0)
    # BM25 clearly favors doc 0; the vector channel favors doc 1 — ignored at α=1.
    out = r.search("warfarin bridging", k=3)
    assert out[0]["index"] == 0


def test_hybrid_blend_is_a_weighted_sum(monkeypatch):
    r = _with_vector_channel(monkeypatch, alpha=0.5)
    # BM25 flat (0.0 everywhere) → blended score = 0.5 * cosine exactly:
    # doc 1 cosine 1.0 → 0.5; docs 0/2 cosine 0.0 → 0.0.
    out = r.search("completely unrelated query words", k=3)
    by_idx = {o["index"]: o["score"] for o in out}
    assert by_idx[1] == pytest.approx(0.5, abs=1e-6)
    assert by_idx[0] == pytest.approx(0.0, abs=1e-6)
    assert by_idx[2] == pytest.approx(0.0, abs=1e-6)
