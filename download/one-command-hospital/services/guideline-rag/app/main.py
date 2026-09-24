"""Guideline RAG — the librarian robot (v0.3).

Improvement #1 (citation-forced RAG + hard refusal) and #2 (edition stamping),
Phase 1: hybrid retrieval (BM25 + optional SBERT), title-boosted chunks.
v0.3 hardening: TTL answer cache, ambiguity margin gate, /metrics, rate limit.

Rules the generator lives by:
  - Answer ONLY from the provided excerpts.
  - Every factual sentence must cite its source as [CORPUS_ID §N].
  - If the excerpts don't cover the question: reply exactly `NOT_COVERED`.
  - If retrieval is not confident enough (below THRESHOLD, or top-2 within
    MARGIN of each other): refuse — a wrong guess is worse than a refusal.
If the LLM is unreachable, fall back to extractive answering (top section
verbatim) so retrieval can still be evaluated without a GPU.

NOTE for callers: de-id the QUESTION as well as any note context before this
service if the question may contain patient identifiers — the mediator does
this upstream; direct callers must not bypass that gate.
"""
import hashlib
import os
import re
import time
import pathlib
from collections import OrderedDict
from typing import List, Optional

import requests
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

from .retrieval import HybridRetriever
from .hardening import Counter, Gauge, Histogram, install, json_log, request_id_of

ROOT = pathlib.Path(__file__).resolve().parents[1]   # container: /app  (repo override via GUIDELINES_DIR)
GUIDELINES = pathlib.Path(
    os.environ.get("GUIDELINES_DIR", ROOT / "guidelines")
)
# Path contract:
#   - in-container: /app/app/main.py → parents[1]=/app → /app/guidelines (compose mount) ✓
#   - repo/CI runs: set GUIDELINES_DIR=<repo>/guidelines (see tests/conftest.py)
THRESHOLD = float(os.environ.get("RETRIEVAL_THRESHOLD", "0.18"))
MARGIN = float(os.environ.get("RETRIEVAL_MARGIN", "0.02"))
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://llm:8000/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "BioMistral/BioMistral-7B")
CACHE_TTL_S = float(os.environ.get("CACHE_TTL_S", "300"))
CACHE_MAX = int(os.environ.get("CACHE_MAX", "1024"))

app = FastAPI(title="guideline-rag", version="0.3.0")

REFUSALS = Counter("rag_refusals_total", "Refusals returned, by reason.")
CACHE_HITS = Counter("rag_cache_hits_total", "Answers served from the TTL cache.")
TOP_SCORE = Gauge("rag_top_score_last", "Retrieval score of the last query's top hit.")
RETRIEVAL_GAP = Gauge("rag_margin_last", "Score gap between top-1 and top-2 of the last query.")
install(app, "guideline-rag", extra=[REFUSALS, CACHE_HITS, TOP_SCORE, RETRIEVAL_GAP])

manifest: dict = {}
retriever: HybridRetriever | None = None
_cache: OrderedDict = OrderedDict()  # key -> (expires_at, answer_dict)


def _cache_get(key):
    hit = _cache.get(key)
    if not hit:
        return None
    expires, value = hit
    if expires < time.time():
        _cache.pop(key, None)
        return None
    _cache.move_to_end(key)
    return value


def _cache_put(key, value):
    _cache[key] = (time.time() + CACHE_TTL_S, value)
    _cache.move_to_end(key)
    while len(_cache) > CACHE_MAX:
        _cache.popitem(last=False)


def _load_corpus():
    entries = yaml.safe_load((GUIDELINES / "manifest.yaml").read_text())["corpus"]
    man, sections = {}, []
    for e in entries:
        man[e["id"]] = e
        text = (GUIDELINES / e["file"]).read_text()
        parts = re.split(r"^(##\s+\d+\..+)$", text, flags=re.M)
        for i in range(1, len(parts), 2):
            header = parts[i].strip()
            m = re.match(r"##\s+(\d+)\.\s*(.+)", header)
            num, title = m.group(1), m.group(2)
            body = parts[i + 1] if i + 1 < len(parts) else ""
            # Title boost: corpus title + section header travel with the chunk,
            # so doc-level vocabulary helps retrieval, not just section text.
            chunk = f"[{e['title']} — §{num} {title}] (edition {e['edition']})\n{header}\n{body}"
            sections.append({
                "corpus_id": e["id"],
                "section": num,
                "edition": e["edition"],
                "text": chunk,
            })
    return man, sections


@app.on_event("startup")
def startup():
    global manifest, retriever
    manifest, sections = _load_corpus()
    retriever = HybridRetriever(sections)


class Question(BaseModel):
    question: str


CITE_RE = re.compile(r"\[([A-Z][A-Z0-9-]+)\s*§(\d+)\]")


def extract_citations(raw: str, manifest: dict, section_text: dict | None = None) -> List["Citation"]:
    """Pull [CORPUS_ID §N] markers out of generator output, dedupe, and drop
    anything not in the manifest — a citation the corpus can't back is not a
    citation. Pure function so the eval/tests can exercise it without HTTP.

    section_text: optional {(corpus_id, str(section)) -> chunk text} map. When
    given, each citation carries the quoted section text downstream — the
    verifier needs it for lexical grounding (a title alone cannot ground an
    answer)."""
    section_text = section_text or {}
    cites, seen = [], set()
    for cid, sec in CITE_RE.findall(raw):
        if (cid, sec) in seen or cid not in manifest:
            continue
        seen.add((cid, sec))
        e = manifest[cid]
        cites.append(Citation(corpus_id=cid, section=sec,
                              edition=e["edition"], title=e["title"],
                              text=section_text.get((cid, str(sec)), "")))
    return cites


class Citation(BaseModel):
    corpus_id: str
    section: str
    edition: str
    title: str
    text: str = ""  # quoted section text — grounding evidence for the verifier


class Answer(BaseModel):
    answer: str
    citations: List[Citation]
    refusal: bool
    refusal_reason: Optional[str] = None
    latency_ms: int
    model: str
    retrieval: Optional[dict] = None


def build_prompt(question: str, hits: list) -> str:
    ctx = "\n\n".join(
        f'--- [{h["corpus_id"]} §{h["section"]}] (edition {h["edition"]}) ---\n{h["text"]}'
        for h in hits
    )
    return (
        "You are a hospital guideline assistant. Use ONLY the excerpts below.\n"
        "Cite every claim inline as [CORPUS_ID §N]. If the excerpts do not answer "
        "the question, reply with exactly: NOT_COVERED\n\n"
        f"EXCERPTS:\n{ctx}\n\nQUESTION: {question}\nANSWER:"
    )


def call_llm(prompt: str) -> str:
    r = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        json={"model": LLM_MODEL, "temperature": 0.1, "max_tokens": 500,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _refusal(reason: str, latency_ms: int, retrieval_meta: dict) -> Answer:
    REFUSALS.inc({"reason": reason})
    return Answer(answer="NOT_COVERED", citations=[], refusal=True,
                  refusal_reason=reason, latency_ms=latency_ms, model=LLM_MODEL,
                  retrieval=retrieval_meta)


@app.post("/answer", response_model=Answer)
def answer(q: Question):
    t0 = time.time()
    SECTIONS = retriever.sections

    key = hashlib.sha256(
        f"{q.question.strip().lower()}|{retriever.engine}|{THRESHOLD}|{MARGIN}".encode()
    ).hexdigest()
    cached = _cache_get(key)
    if cached is not None:
        CACHE_HITS.inc({"route": "/answer"})
        return Answer(**{**cached, "latency_ms": int((time.time() - t0) * 1000)})

    results = retriever.search(q.question, k=3)
    top_score = results[0]["score"] if results else 0.0
    gap = (results[0]["score"] - results[1]["score"]) if len(results) >= 2 else 1.0
    TOP_SCORE.set({"route": "/answer"}, round(top_score, 4))
    RETRIEVAL_GAP.set({"route": "/answer"}, round(gap, 4))

    retrieval_meta = {"engine": retriever.engine,
                      "top": [{"corpus_id": SECTIONS[r["index"]]["corpus_id"],
                               "section": SECTIONS[r["index"]]["section"],
                               "score": round(r["score"], 3)}
                              for r in results]}

    # Gate 1 — confidence: nothing scored above the floor → refuse, don't guess.
    hits = [{**SECTIONS[r["index"]], "score": r["score"]}
            for r in results if r["score"] >= THRESHOLD]
    if not hits:
        json_log("guideline-rag", "refusal", request_id=request_id_of(),
                 reason="below-threshold",
                 question_sha=hashlib.sha256(q.question.encode()).hexdigest()[:12])
        return _refusal("no guideline section met retrieval confidence",
                        int((time.time() - t0) * 1000), retrieval_meta)

    # Gate 2 — ambiguity: top-2 nearly tied → refuse (MARGIN=0 disables).
    if MARGIN > 0 and len(results) >= 2 and gap < MARGIN:
        json_log("guideline-rag", "refusal", request_id=request_id_of(),
                 reason="ambiguity-margin",
                 question_sha=hashlib.sha256(q.question.encode()).hexdigest()[:12])
        return _refusal("top sections too close to disambiguate safely",
                        int((time.time() - t0) * 1000), retrieval_meta)

    prompt = build_prompt(q.question, hits)
    llm_used = True
    try:
        raw = call_llm(prompt)
    except Exception:
        # Extractive fallback (mock-LLM mode): the pipeline degrades honestly
        # instead of dying. The citation header is PREPENDED so downstream
        # grounding keeps working — an answer with no citation is ungrounded
        # by definition (the mediator flags those).
        llm_used = False
        h = hits[0]
        raw = f'[{h["corpus_id"]} §{h["section"]}] ' + h["text"].split("\n", 1)[-1].strip()[:800]

    if "NOT_COVERED" in raw.upper():
        return _refusal("generator judged the corpus does not cover this",
                        int((time.time() - t0) * 1000), retrieval_meta)

    # Improvement #2: stamp every citation with the manifest edition + title.
    # Text map built from the RETRIEVED sections only (never the whole corpus).
    sec_text = {(s["corpus_id"], str(s["section"])): s["text"] for s in hits}
    cites = extract_citations(raw, manifest, sec_text)

    result = Answer(answer=raw, citations=cites, refusal=False,
                    latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL,
                    retrieval=retrieval_meta)
    _cache_put(key, result.model_dump())
    json_log("guideline-rag", "answer", request_id=request_id_of(),
             question_sha=hashlib.sha256(q.question.encode()).hexdigest()[:12],
             refusal=False, citations=len(cites), llm=llm_used,
             latency_ms=result.latency_ms)
    return result


@app.get("/health")
def health():
    return {"ok": bool(retriever and retriever.sections),
            "sections": len(retriever.sections) if retriever else 0,
            "retrieval_engine": retriever.engine if retriever else "unloaded",
            "cache_entries": len(_cache),
            "gates": {"threshold": THRESHOLD, "margin": MARGIN},
            "corpus": {k: v["edition"] for k, v in manifest.items()}}
