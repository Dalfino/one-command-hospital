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
from .injection_guard import scan as injection_scan
from .guided_decoding import guided_enabled, guided_request_fields, parse_guided
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
INJECTION_BLOCKS = Counter("rag_injection_blocks_total", "Prompt-injection patterns blocked, by surface.")
install(app, "guideline-rag", extra=[REFUSALS, CACHE_HITS, TOP_SCORE, RETRIEVAL_GAP, INJECTION_BLOCKS])

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


def citations_for_answer(raw: str, guided_obj: dict | None, hits: list,
                         manifest: dict) -> List["Citation"]:
    """Provenance merge for a produced (non-refusal) answer — v0.6.3 GPU-pilot
    finding: 7B generators answer well but rarely emit inline [CORPUS_ID §N]
    markers and usually leave the guided `citations` array empty; marker-only
    extraction yielded 0 citations across 195 live GPU answers while retrieval
    itself hit 95-98%.

    Citations are PROVENANCE — what the generator was actually conditioned on —
    so the merge is: answer-text markers ∪ generator-claimed pairs ∪ retrieved
    sections, filtered to sections retrieval actually supplied (a citation the
    corpus cannot back is not a citation), stamped with manifest edition/title
    and the quoted text for the verifier's grounding check. The verifier stays
    the independent per-claim grounding judge downstream. Pure function for
    eval/tests."""
    sec_text = {(s["corpus_id"], str(s["section"])): s["text"] for s in hits}
    keys = {(c.corpus_id, c.section) for c in extract_citations(raw, manifest, sec_text)}
    for c in (guided_obj or {}).get("citations", []) or []:
        if isinstance(c, dict):
            keys.add((str(c.get("corpus_id", "")), str(c.get("section", ""))))
    keys |= set(sec_text.keys())
    cites = []
    for cid, sec in sorted(keys):
        if cid not in manifest or (cid, sec) not in sec_text:
            continue
        e = manifest[cid]
        cites.append(Citation(corpus_id=cid, section=sec,
                              edition=e["edition"], title=e["title"],
                              text=sec_text[(cid, sec)]))
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


def build_prompt(question: str, hits: list, guided: bool | None = None) -> str:
    ctx = "\n\n".join(
        f'--- [{h["corpus_id"]} §{h["section"]}] (edition {h["edition"]}) ---\n{h["text"]}'
        for h in hits
    )
    if guided is None:
        guided = guided_enabled()
    if guided:
        # Matches the guided_json schema (guided_decoding.ANSWER_SCHEMA): the
        # server constrains decoding to this object; the prompt mirrors it so
        # intent and constraint agree.
        return (
            "You are a hospital guideline assistant. Use ONLY the excerpts below.\n"
            'Respond with a JSON object with keys "covered" (boolean), "answer" '
            '(string), "citations" (array of {"corpus_id", "section"}).\n'
            "In `answer`, cite every claim inline as [CORPUS_ID §N]. If the excerpts "
            'do not answer the question, set covered=false and answer exactly: '
            "NOT_COVERED\n\n"
            f"EXCERPTS:\n{ctx}\n\nQUESTION: {question}\nANSWER (JSON):"
        )
    return (
        "You are a hospital guideline assistant. Use ONLY the excerpts below.\n"
        "Cite every claim inline as [CORPUS_ID §N]. If the excerpts do not answer "
        "the question, reply with exactly: NOT_COVERED\n\n"
        f"EXCERPTS:\n{ctx}\n\nQUESTION: {question}\nANSWER:"
    )


def call_llm(prompt: str, guided: bool | None = None) -> str:
    body = {"model": LLM_MODEL, "temperature": 0.1, "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}]}
    if guided is None:
        guided = guided_enabled()
    if guided:
        # Decoding-level contract (ADOPT, tech_radar): the model cannot emit
        # anything but the answer schema. Servers that ignore the field simply
        # answer free text and the legacy parser path takes over downstream.
        body.update(guided_request_fields())
    r = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        json=body,
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _refusal(reason: str, latency_ms: int, retrieval_meta: dict) -> Answer:
    REFUSALS.inc({"reason": reason})
    return Answer(answer="NOT_COVERED", citations=[], refusal=True,
                  refusal_reason=reason, latency_ms=latency_ms, model=LLM_MODEL,
                  retrieval=retrieval_meta)


def retrieval_meta_placeholder() -> dict:
    # Injection refusals fire before retrieval meta is assembled; keep the
    # contract (retrieval is Optional) honest instead of null-ing loudly.
    return None


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

    # Gate 0 — injection screen on the QUESTION itself (M19). Refuse-and-log:
    # a question carrying generator instructions never reaches the prompt.
    q_findings = injection_scan(q.question)
    if q_findings:
        INJECTION_BLOCKS.inc({"route": "/answer", "surface": "question"}, len(q_findings))
        json_log("guideline-rag", "injection_blocked", request_id=request_id_of(),
                 surface="question", patterns=[f["pattern_id"] for f in q_findings],
                 question_sha=hashlib.sha256(q.question.encode()).hexdigest()[:12])
        return _refusal("prompt-injection pattern detected in question",
                        int((time.time() - t0) * 1000), retrieval_meta_placeholder())

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
    raw_hits = [{**SECTIONS[r["index"]], "score": r["score"]}
                for r in results if r["score"] >= THRESHOLD]

    # Gate 1b — injection screen on the CORPUS chunks (M19). A poisoned
    # guideline chunk must not reach the generator prompt; it is dropped and
    # counted. If EVERY hit is poisoned there is nothing safe to answer from.
    hits, anomalies = [], 0
    for h in raw_hits:
        if injection_scan(h["text"]):
            anomalies += 1
            continue
        hits.append(h)
    if anomalies:
        INJECTION_BLOCKS.inc({"route": "/answer", "surface": "corpus"}, anomalies)
        json_log("guideline-rag", "injection_blocked", request_id=request_id_of(),
                 surface="corpus", dropped=anomalies)
        retrieval_meta["corpus_anomalies"] = anomalies
    if raw_hits and not hits:
        return _refusal("every retrieved section failed the integrity screen",
                        int((time.time() - t0) * 1000), retrieval_meta)
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

    guided = guided_enabled()
    prompt = build_prompt(q.question, hits, guided=guided)
    llm_used = True
    try:
        raw = call_llm(prompt, guided=guided)
    except Exception as e:
        # Extractive fallback (mock-LLM mode): the pipeline degrades honestly
        # instead of dying. The citation header is PREPENDED so downstream
        # grounding keeps working — an answer with no citation is ungrounded
        # by definition (the mediator flags those).
        # v0.6.3: log WHY (silent fallbacks masked generator mis-wiring for a
        # full pilot run — 4ms "answers" were 400s/refusals at the wire).
        json_log("guideline-rag", "llm_call_failed", level="warning",
                 error=repr(e)[:300], base_url=LLM_BASE_URL,
                 model=LLM_MODEL, guided=guided)
        llm_used = False
        h = hits[0]
        raw = f'[{h["corpus_id"]} §{h["section"]}] ' + h["text"].split("\n", 1)[-1].strip()[:800]

    # Guided-decoding path: when the server honored guided_json the content is
    # a strict JSON object. covered=false is the generator's mechanical refusal
    # (no room for free-text refusal drift). parse_guided() returning None on a
    # JSON-looking payload means a constrained server malfunctioned -> fail
    # closed rather than forward malformed output. Free text (legacy servers,
    # extractive fallback) passes straight through to the legacy contract.
    guided_used = False
    guided_obj = parse_guided(raw)
    if guided_obj is not None:
        guided_used = True
        if not guided_obj["covered"]:
            return _refusal("generator judged the corpus does not cover this",
                            int((time.time() - t0) * 1000), retrieval_meta)
        raw = guided_obj["answer"]
    elif raw.lstrip().startswith("{"):
        return _refusal("generator produced unparseable structured output",
                        int((time.time() - t0) * 1000), retrieval_meta)

    if "NOT_COVERED" in raw.upper():
        return _refusal("generator judged the corpus does not cover this",
                        int((time.time() - t0) * 1000), retrieval_meta)

    # Improvement #2: stamp every citation with the manifest edition + title.
    # v0.6.3: provenance merge (markers ∪ generator claims ∪ retrieved sections)
    # instead of marker-only extraction — see citations_for_answer().
    cites = citations_for_answer(raw, guided_obj, hits, manifest)

    result = Answer(answer=raw, citations=cites, refusal=False,
                    latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL,
                    retrieval=retrieval_meta)
    _cache_put(key, result.model_dump())
    json_log("guideline-rag", "answer", request_id=request_id_of(),
             question_sha=hashlib.sha256(q.question.encode()).hexdigest()[:12],
             refusal=False, citations=len(cites), llm=llm_used, guided=guided_used,
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
