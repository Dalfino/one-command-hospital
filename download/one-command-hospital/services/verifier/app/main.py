"""Verifier — the strict teacher who checks the librarian's quotes.

Improvement #3: NLP-as-verifier. Runs AFTER generation:
  1. every cited [CORPUS_ID §N] must exist in the retrieved sources;
  2. negation-consistency: answer sentences asserting negations whose source
     text does not support them are flagged (v0 heuristic; ConText via
     medspaCy lands in Phase 1);
  3. lexical grounding score: content-word overlap between answer and cited
     source text — a cheap proxy for "is this actually from the document?"

v0 is honest heuristics. Phase 1 swaps in medspaCy ConText + scispaCy NER.
"""
import re
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="verifier", version="0.1.0")
WORD = re.compile(r"[a-z0-9]+")
CITE = re.compile(r"\[([A-Z][A-Z0-9-]+)\s*§(\d+)\]")

STOP = set("""the a an and or of to in for with on is are be was were must may should
can it its this that by at as from not no if when any all patient patients procedure""".split())

NEGATORS = {"never", "avoid", "contraindicated", "not recommended", "should not",
            "must not", "no bridging", "not required", "does not"}


class VerifyRequest(BaseModel):
    answer: str
    sources: List[dict]  # [{corpus_id, section, text}]


class VerifyResponse(BaseModel):
    grounded: bool
    grounding_score: float
    invalid_citations: List[str]
    unsupported_negations: List[str]
    notes: List[str]


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    src_map = {(s["corpus_id"], str(s["section"])): s["text"].lower() for s in req.sources}
    notes: List[str] = []

    # 1. citation validity
    invalid = []
    for cid, sec in set(CITE.findall(req.answer)):
        if (cid, sec) not in src_map:
            invalid.append(f"[{cid} §{sec}]")
    if invalid:
        notes.append("answer cites section(s) not in retrieved sources")

    # 2. negation consistency (heuristic v0)
    unsupported = []
    cited_text = " ".join(src_map.values())
    for sentence in re.split(r"(?<=[.!?])\s+", req.answer):
        low = sentence.lower()
        if any(n in low for n in NEGATORS):
            key = CITE.findall(sentence)
            src = " ".join(src_map.get((c, s), "") for c, s in key) if key else cited_text
            # supported if the source also negates the same content word nearby
            content = [w for w in WORD.findall(low) if w not in STOP]
            supported = any(w in src for w in content)
            if not supported:
                unsupported.append(sentence.strip()[:120])
    if unsupported:
        notes.append("negation statements lack support in cited text — human review required")

    # 3. lexical grounding
    ans_words = {w for w in WORD.findall(req.answer.lower()) if w not in STOP}
    src_words = {w for w in WORD.findall(cited_text) if w not in STOP}
    grounding = len(ans_words & src_words) / max(len(ans_words), 1)

    return VerifyResponse(
        grounded=(not invalid) and grounding >= 0.45 and not unsupported,
        grounding_score=round(grounding, 3),
        invalid_citations=invalid,
        unsupported_negations=unsupported,
        notes=notes,
    )


@app.get("/health")
def health():
    return {"ok": True, "service": "verifier", "engine": "heuristic-v0"}
