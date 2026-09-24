#!/usr/bin/env python3
"""Claim-level faithfulness scoring (M23).

The verifier checks lexical grounding globally; this module decomposes an
answer into ATOMIC CLAIMS and checks each claim against the cited section
text, so "the answer is mostly grounded" becomes "3 of 4 claims are
supported, and the unsupported one invented a number".

Checks per claim, cheapest first:
  1. NUMBER integrity — every dose/percentage/unit in the claim must appear
     verbatim in the cited text. Fabricated numbers are the highest-risk
     hallucination class in clinical text.
  2. CONTENT-WORD overlap — >= 0.5 of the claim's non-stopwords must appear
     in the cited text.
  3. POLARITY flip — a negation cue in the claim that is absent from the
     cited text (or vice versa) marks the claim unsupported.

Dependency-light (pure stdlib) so it runs in eval, in unit tests, and — if
wanted later — inside the verifier container. Upgrade path: replace the
overlap+number checks with an NLI entailment model on the GPU stack
(bio-NLI / DeBERTa); the claim decomposition contract stays identical.
"""
import hashlib
import re

WORD = re.compile(r"[a-z0-9]+")
NUMBER = re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|ml|units?|%|g\b|iu\b|mmol\b)?", re.I)
CITE = re.compile(r"\[[A-Z][A-Z0-9-]*\s*§\d+\]")  # * allows single-char ids in fixtures

STOP = set("""the a an and or of to in for with on is are be was were must may should
can it its this that by at as from if when any all patient patients
before after not no than then there their they""".split())

NEG_CUES = ("never", "avoid", "contraindicated", "not recommended", "should not",
            "must not", "does not", "do not", "without", "no bridging",
            "not required", "not indicated", "is not", "are not", "cannot")


def decompose_claims(answer: str) -> list:
    """Split the answer into claim candidates: real sentences minus citation
    fragments and boilerplate. Order preserved (position matters for triage)."""
    claims = []
    for s in re.split(r"(?<=[.!?])\s+", answer or ""):
        s = s.strip()
        if len(WORD.findall(s)) < 4:      # citation-only fragments, headers
            continue
        claims.append(s)
    return claims


def _sentences(text: str) -> list:
    return [s for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def _content_words(s: str) -> set:
    return {w for w in WORD.findall(s.lower()) if w not in STOP and len(w) > 2}


def _best_sentence(claim: str, cited_text: str) -> str:
    """The cited sentence sharing the most content words with the claim.
    Polarity is only meaningful against the sentence that actually talks
    about the claim's subject — a negation in a DIFFERENT cited sentence
    must not poison an affirmative claim (and vice versa)."""
    cw = _content_words(claim)
    best, best_overlap = "", -1
    for s in _sentences(cited_text):
        overlap = len(cw & _content_words(s))
        if overlap > best_overlap:
            best, best_overlap = s, overlap
    return best if best_overlap > 0 else cited_text


def _supported(claim: str, cited_text: str) -> tuple:
    """(bool, reason) for one claim against one block of cited text."""
    # Citation markers ([X §3]) are metadata, not claims — strip BEFORE number
    # checks or every cited section number reads as a fabricated dose.
    bare = CITE.sub(" ", claim)
    low_claim, low_cited = bare.lower(), (cited_text or "").lower()

    # 1. numbers must be verbatim somewhere in the cited text (recall-oriented)
    for num in NUMBER.findall(bare):
        n = num.strip()
        if n and n not in low_cited:
            return False, f"number '{n}' absent from cited text"

    words = [w for w in WORD.findall(low_claim) if w not in STOP and len(w) > 2]
    if not words:
        return True, "no content words to check"
    overlap = sum(1 for w in set(words) if w in low_cited) / len(set(words))
    if overlap < 0.5:
        return False, f"content overlap {overlap:.2f} < 0.5"

    # 2. polarity flip, checked against the BEST-MATCHING cited sentence
    scope = _best_sentence(bare, cited_text).lower()
    claim_neg = any(c in low_claim for c in NEG_CUES)
    cited_neg = any(c in scope for c in NEG_CUES)
    if claim_neg != cited_neg:
        return False, "polarity mismatch between claim and cited text"

    return True, f"overlap {overlap:.2f}"


def faithfulness(answer: str, cited_texts: list) -> dict:
    """Score the whole answer. cited_texts: list of cited section texts
    (the answer is checked against the UNION of its citations — a claim is
    supported if ANY cited section backs it).

    Returns {score: float|None, claims: [{claim_sha, supported, reason}]}.
    score is None when there is nothing to check against (no citations) —
    callers must treat that as unverifiable, not as perfect."""
    claims = decompose_claims(answer)
    if not claims:
        return {"score": None, "claims": []}
    union = "\n".join(cited_texts or []).strip()
    if not union:
        return {"score": None,
                "claims": [{"claim_sha": _sha(c), "supported": None,
                            "reason": "no citations to check against"} for c in claims]}
    checked = []
    for c in claims:
        ok, reason = _supported(c, union)
        checked.append({"claim_sha": _sha(c), "supported": ok, "reason": reason})
    score = sum(1 for c in checked if c["supported"]) / len(checked)
    return {"score": round(score, 3), "claims": checked}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]
