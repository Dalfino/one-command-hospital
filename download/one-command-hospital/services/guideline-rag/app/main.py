"""Guideline RAG — the librarian robot.

Improvement #1 (citation-forced RAG + hard refusal) and #2 (edition stamping).

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

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUIDELINES = ROOT / "guidelines"
THRESHOLD = float(os.environ.get("RETRIEVAL_THRESHOLD", "0.18"))
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://llm:8000/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "BioMistral/BioMistral-7B")

app = FastAPI(title="guideline-rag", version="0.1.0")
WORD = re.compile(r"[a-z0-9]+")

# corpus_id → {manifest fields}, and the flat section index
manifest: dict = {}
sections: list = []


@app.on_event("startup")
def load_corpus():
    global sections, manifest
    entries = yaml.safe_load((GUIDELINES / "manifest.yaml").read_text())["corpus"]
    manifest = {e["id"]: e for e in entries}
    sections = []
    for e in entries:
        text = (GUIDELINES / e["file"]).read_text()
        parts = re.split(r"^(##\s+\d+\..+)$", text, flags=re.M)
        for i in range(1, len(parts), 2):
            num = re.match(r"##\s+(\d+)\.", parts[i]).group(1)
            sections.append({
                "corpus_id": e["id"],
                "section": num,
                "edition": e["edition"],
                "text": parts[i].strip() + "\n" + (parts[i + 1] if i + 1 < len(parts) else ""),
            })
    from rank_bm25 import BM25Okapi
    app.state.bm25 = BM25Okapi([WORD.findall(s["text"].lower()) for s in sections])


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
    scores = app.state.bm25.get_scores(WORD.findall(q.question.lower()))
    top_idx = sorted(range(len(scores)), key=lambda i: -scores[i])[:3]
    hits = [sections[i] for i in top_idx if scores[i] >= THRESHOLD]

    if not hits:
        return Answer(answer="NOT_COVERED", citations=[], refusal=True,
                      refusal_reason="no guideline section met retrieval confidence",
                      latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL)

    prompt = build_prompt(q.question, hits)
    try:
        raw = call_llm(prompt)
    except Exception:
        # Extractive fallback so the pipeline degrades honestly instead of dying.
        raw = hits[0]["text"].split("\n", 1)[-1].strip()[:800]

    if "NOT_COVERED" in raw.upper():
        return Answer(answer="NOT_COVERED", citations=[], refusal=True,
                      refusal_reason="generator judged the corpus does not cover this",
                      latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL)

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
                  latency_ms=int((time.time() - t0) * 1000), model=LLM_MODEL)


@app.get("/health")
def health():
    return {"ok": bool(sections), "sections": len(sections),
            "corpus": {k: v["edition"] for k, v in manifest.items()}}
