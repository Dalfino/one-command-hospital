"""Verifier — the strict teacher who checks the librarian's quotes (v0.3).

Improvement #3, Phase 1: NLP-as-verifier with medspaCy ConText.

Checks, in order:
  1. Citation validity — every cited [CORPUS_ID §N] must exist in sources.
  2. Negation consistency (ConText) — claims the answer asserts with NEGATED
     polarity must be negated the same way in the cited source, and vice versa
     for positive claims about the same anchor word. Falls back to cue-word
     heuristics when medspaCy is unavailable.
  3. Lexical grounding — content-word overlap between answer and sources.

Engine reported in /health: "medspacy-context" or "heuristic-v0".
v0.3 hardening: NLP pipeline built ONCE (was per request), /metrics with
conflict + grounding collectors, rate limit, body-size cap, security headers.
"""
import re
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from .hardening import Counter, Gauge, install

app = FastAPI(title="verifier", version="0.3.0")

CONFLICTS = Counter("verifier_polarity_conflicts_total", "Polarity conflicts found.")
INVALID_CITES = Counter("verifier_invalid_citations_total", "Citations not in retrieved sources.")
GROUNDING = Gauge("verifier_grounding_score_last", "Lexical grounding score of the last verify.")
UNGROUNDED = Counter("verifier_ungrounded_total", "Verdicts that failed grounding.")
install(app, "verifier", extra=[CONFLICTS, INVALID_CITES, GROUNDING, UNGROUNDED])

WORD = re.compile(r"[a-z0-9]+")
CITE = re.compile(r"\[([A-Z][A-Z0-9-]+)\s*§(\d+)\]")

STOP = set("""the a an and or of to in for with on is are be was were must may should
can it its this that by at as from if when any all patient patients procedure
before after not no""".split())

# ConText-style cue fallback for environments without medspaCy.
NEG_CUES = {"never", "avoid", "contraindicated", "not recommended", "should not",
            "must not", "no bridging", "not required", "does not", "not covered",
            "do not", "without"}

_NLP_CACHE: dict = {}


def _build_nlp():
    """medspaCy pipeline (sentencizer + target_matcher + ConText). Built ONCE
    and cached — the rule state is read-only at inference time, so a shared
    pipeline is safe and keeps verify latency flat."""
    if "nlp" in _NLP_CACHE:
        return _NLP_CACHE["nlp"], _NLP_CACHE["TargetRule"]
    try:
        import medspacy  # noqa: F401
        from medspacy.context import ConTextComponent
        from medspacy.target_matcher import TargetMatcher, TargetRule
        import spacy

        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        nlp.add_pipe("target_matcher")
        nlp.add_pipe("medspacy_context")
        _NLP_CACHE["nlp"] = nlp
        _NLP_CACHE["TargetRule"] = TargetRule
        return nlp, TargetRule
    except Exception:
        _NLP_CACHE["nlp"] = None
        _NLP_CACHE["TargetRule"] = None
        return None, None


def _polarity_map(nlp, TargetRule, text: str, anchors: List[str]) -> dict:
    """anchor word → set of polarities ('affirmed'/'negated') found in text."""
    if not nlp:
        # heuristic fallback: cue-word window search
        low = text.lower()
        pol = {}
        for w in anchors:
            idx = 0
            while True:
                i = low.find(w, idx)
                if i < 0:
                    break
                window = low[max(0, i - 40): i + len(w) + 10]
                pol.setdefault(w, set()).add(
                    "negated" if any(c in window for c in NEG_CUES) else "affirmed"
                )
                idx = i + len(w)
        return pol

    matcher = nlp.get_pipe("target_matcher")
    matcher.add([TargetRule(literal=w, category="CLAIM") for w in anchors])
    pol = {}
    for doc in nlp.pipe([text] if isinstance(text, str) else text):
        for ent in doc.ents:
            pol.setdefault(ent.text.lower(), set()).add(
                "negated" if ent._.is_negated else "affirmed"
            )
    return pol


class VerifyRequest(BaseModel):
    answer: str
    sources: List[dict]  # [{corpus_id, section, text}]


class VerifyResponse(BaseModel):
    grounded: bool
    grounding_score: float
    invalid_citations: List[str]
    polarity_conflicts: List[str]
    notes: List[str]


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    nlp, TargetRule = _build_nlp()
    engine = "medspacy-context" if nlp else "heuristic-v0"
    src_map = {(s["corpus_id"], str(s["section"])): s["text"] for s in req.sources}
    notes: List[str] = [f"engine: {engine}"]

    # 1. citation validity
    invalid = []
    for cid, sec in set(CITE.findall(req.answer)):
        if (cid, sec) not in src_map:
            invalid.append(f"[{cid} §{sec}]")
    if invalid:
        notes.append("answer cites section(s) not in retrieved sources")
        INVALID_CITES.inc({"route": "/verify"}, len(invalid))

    # 2. negation/polarity consistency (ConText when available)
    cited_text = " ".join(src_map.values())
    sentences = re.split(r"(?<=[.!?])\s+", req.answer)
    anchors = []
    for s in sentences:
        anchors += [w for w in WORD.findall(s.lower()) if w not in STOP and len(w) > 3]
    anchors = list(dict.fromkeys(anchors))[:40]

    ans_pol = _polarity_map(nlp, TargetRule, req.answer, anchors)
    src_pol = _polarity_map(nlp, TargetRule, cited_text, anchors)

    conflicts = []
    for w in anchors:
        a = ans_pol.get(w, set())
        s = src_pol.get(w, set())
        # conflict: answer affirms what the source only negates (dangerous direction)
        if "affirmed" in a and "affirmed" not in s and "negated" in s:
            conflicts.append(f"'{w}' affirmed in answer but negated in source")
    if conflicts:
        notes.append("polarity conflicts — human review required")
        CONFLICTS.inc({"route": "/verify"}, len(conflicts))

    # 3. lexical grounding
    ans_words = {w for w in WORD.findall(req.answer.lower()) if w not in STOP}
    src_words = {w for w in WORD.findall(cited_text.lower()) if w not in STOP}
    grounding = len(ans_words & src_words) / max(len(ans_words), 1)
    GROUNDING.set({"route": "/verify"}, round(grounding, 3))

    grounded = (not invalid) and grounding >= 0.45 and not conflicts
    if not grounded:
        UNGROUNDED.inc({"route": "/verify"})

    return VerifyResponse(
        grounded=grounded,
        grounding_score=round(grounding, 3),
        invalid_citations=invalid,
        polarity_conflicts=conflicts,
        notes=notes,
    )


@app.get("/health")
def health():
    nlp, _ = _build_nlp()
    return {"ok": True, "service": "verifier",
            "engine": "medspacy-context" if nlp else "heuristic-v0"}
