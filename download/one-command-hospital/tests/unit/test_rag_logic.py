"""Unit tier — guideline-rag pure logic.

Covers the answer-cache (TTL + LRU), citation extraction (dedupe, manifest
filtering, edition stamping), prompt construction, and the refusal shape.
Loads the real corpus via startup() so assertions run against the actual
manifest the service ships with.
"""
import time

import pytest

from app import main as rag


@pytest.fixture(scope="module", autouse=True)
def load_corpus():
    rag.startup()          # sets rag.manifest + rag.retriever from ./guidelines


# ── answer cache ──────────────────────────────────────────────────────────

def test_cache_roundtrip():
    rag._cache_put("k1", {"answer": "a"})
    assert rag._cache_get("k1") == {"answer": "a"}


def test_cache_miss_returns_none():
    assert rag._cache_get("no-such-key") is None


def test_cache_ttl_expiry(monkeypatch):
    monkeypatch.setattr(rag, "CACHE_TTL_S", 0.05)
    rag._cache_put("ttl", {"v": 1})
    time.sleep(0.07)
    assert rag._cache_get("ttl") is None


def test_cache_lru_eviction(monkeypatch):
    monkeypatch.setattr(rag, "CACHE_MAX", 2)
    rag._cache_put("e1", {"v": 1})
    rag._cache_put("e2", {"v": 2})
    rag._cache_get("e1")              # touch e1 → e2 becomes LRU
    rag._cache_put("e3", {"v": 3})    # evicts e2
    assert rag._cache_get("e1") is not None
    assert rag._cache_get("e2") is None
    assert rag._cache_get("e3") is not None


# ── citation extraction (the citation-forcing contract) ───────────────────

def test_extract_citations_dedupes_and_filters_unknown():
    raw = ("Use LMWH [ANTICOAG-BRIDGE §3]. Repeat [ANTICOAG-BRIDGE §3]. "
           "Also see [FAKE-CORPUS §9].")
    cites = rag.extract_citations(raw, rag.manifest)
    ids = [(c.corpus_id, c.section) for c in cites]
    assert ids == [("ANTICOAG-BRIDGE", "3")]      # dup dropped, unknown dropped


def test_extract_citations_stamp_manifest_edition_and_title():
    raw = "Answer with [ANTICOAG-BRIDGE §4] per protocol."
    c = rag.extract_citations(raw, rag.manifest)[0]
    entry = rag.manifest["ANTICOAG-BRIDGE"]
    assert c.edition == entry["edition"]
    assert c.title == entry["title"]


def test_extract_citations_empty_when_no_markers():
    assert rag.extract_citations("no citations here at all", rag.manifest) == []


# ── prompt construction ───────────────────────────────────────────────────

def test_build_prompt_contains_rules_excerpts_and_question():
    hits = [{"corpus_id": "X", "section": "1", "edition": "v1", "text": "body text"}]
    p = rag.build_prompt("what dose?", hits)
    assert "ONLY the excerpts" in p
    assert "NOT_COVERED" in p
    assert "[X §1] (edition v1)" in p
    assert "body text" in p
    assert "what dose?" in p


# ── refusal shape (the hard-refusal contract) ─────────────────────────────

def test_refusal_returns_exact_marker_and_reason():
    a = rag._refusal("test-reason", 5, {"engine": "bm25"})
    assert a.answer == "NOT_COVERED"
    assert a.refusal is True
    assert a.refusal_reason == "test-reason"
    assert a.citations == []


def test_manifest_has_editions_for_every_corpus():
    assert rag.manifest, "corpus must not be empty"
    for cid, e in rag.manifest.items():
        assert e.get("edition"), f"{cid} missing edition stamp"
        assert e.get("title"), f"{cid} missing title"
