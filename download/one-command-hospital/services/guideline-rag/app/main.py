"""Guideline RAG — the librarian robot (v0.2).

Improvement #1 (citation-forced RAG + hard refusal) and #2 (edition stamping),
Phase 1: hybrid retrieval (BM25 + optional SBERT) and title-boosted chunks.

Rules the generator lives by:
  - Answer ONLY from the provided excerpts.
  - Every factual sentence must cite its source as [CORPUS_ID §N].
  - If the excerpts don't cover the question: reply exactly `NOT_COVERED`.
If the LLM is unreachable, fall back to extractive answering (top section
verbatim) so retrieval can still be evaluated without a GPU.
"""
import os
import re
import time
import pathlib
from typing import List, Optional

import requests
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

from .retrieval import HybridRetriever

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUIDELINES = ROOT / "guidelines"
THRESHOLD = float(os.environ.get("RETRIEVAL_THRESHOLD", "0.18"))
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://llm:8000/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "BioMistral/BioMistral-7B")

app = FastAPI(title="guideline-rag", version="0.2.0")

manifest: dict = {}
retriever: HybridRetriever | None = None


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


class Citation(BaseModel):
    corpus_id: str
    section: str
    edition: str
    title: str


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


@app.post("/answer", response_model=Answer)
def answer(q: Question):
    t0 = time.time()
    SECTIONS = retriever.sections
    results = retriever.search(q.question, k=3)
    hits = [{**SECTIONS[r["index"]], "score": r["score"]}
            for r in results if r["score"] >= THRESHOLD]

    retrieval_meta = {"engine": retriever.engine,
                      "top": [{"corpus_id": SECTIONS[r["index"]]["corpus_id"],
                               "section": SECTIONS[r["index"]]["section"],
                               "score": round(r["score"], 3)}
                              for r in results]}

    if not hits:
        return Answer(answer="NOT_COVERED", citations=[], refusal=True,
                      refusal_reason="no guideline section met retrieval confidence",
                      latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL,
                      retrieval=retrieval_meta)

    prompt = build_prompt(q.question, hits)
    try:
        raw = call_llm(prompt)
    except Exception:
        # Extractive fallback so the pipeline degrades honestly instead of dying.
        raw = hits[0]["text"].split("\n", 1)[-1].strip()[:800]

    if "NOT_COVERED" in raw.upper():
        return Answer(answer="NOT_COVERED", citations=[], refusal=True,
                      refusal_reason="generator judged the corpus does not cover this",
                      latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL,
                      retrieval=retrieval_meta)

    # Improvement #2: stamp every citation with the manifest edition + title.
    cites, seen = [], set()
    for cid, sec in re.findall(r"\[([A-Z][A-Z0-9-]+)\s*§(\d+)\]", raw):
        key = (cid, sec)
        if key in seen or cid not in manifest:
            continue
        seen.add(key)
        e = manifest[cid]
        cites.append(Citation(corpus_id=cid, section=sec, edition=e["edition"], title=e["title"]))

    return Answer(answer=raw, citations=cites, refusal=False,
                  latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL,
                  retrieval=retrieval_meta)


@app.get("/health")
def health():
    return {"ok": bool(retriever and retriever.sections),
            "sections": len(retriever.sections) if retriever else 0,
            "retrieval_engine": retriever.engine if retriever else "unloaded",
            "corpus": {k: v["edition"] for k, v in manifest.items()}}
