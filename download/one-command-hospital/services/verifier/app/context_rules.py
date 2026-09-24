"""Context rules — ConText-class conflict detection, dependency-light (M21).

Companion to medspaCy ConText in the verifier. ConText already covers
NEGATION; this module adds the two conflict classes that matter clinically
and that the verifier previously ignored:

  - HISTORICAL: "history of DVT", "anticoagulated in 2023", "prior bleed"
  - FAMILY:     "family history of PE", "mother had warfarin reaction"

The dangerous direction is asymmetric, exactly like negation:
  the ANSWER asserts a CURRENT PATIENT fact while the cited source only
  supports the HISTORICAL or FAMILY sense. E.g. answer "Continue warfarin"
  citing a section whose only support is "family history of warfarin
  sensitivity".

Deliberately NOT a conflict class: HYPOTHETICAL/CONDITIONAL. Guidelines are
written as conditionals ("If the patient has AF, anticoagulate") and answers
legitimately affirm guideline conditionals. Flagging those would flood
review with false positives.

Pure functions + regex only, so the unit tier can exercise the rules without
importing presidio/medspaCy. The verifier mirrors these semantics in its
ConText path (ent._.is_historical / is_family).
"""
import re

WORD = re.compile(r"[a-z0-9]+")

# Sentences that speak about the PAST rather than the present patient state.
HISTORICAL_CUES = re.compile(
    r"\b(history of|history of present|past medical|previously|prior to|"
    r"prior (?:episode|therapy|treatment|dose|bleed|event)|"
    r"\b(?:19|20)\d{2}\b|"          # explicit years only ("in 2023") — never bare numbers
    r"\bago\b|remote|resolved|no longer|used to take|formally)\b",
    re.I)

# Sentences about RELATIVES, not the patient.
FAMILY_CUES = re.compile(
    r"\b(family history|familial|mother|father|maternal|paternal|"
    r"brother|sister|sibling|grandmother|grandfather|grandparent|"
    r"(?:first|second)-degree relative|runs? in the family)\b",
    re.I)

# Cue words that mark an assertion as NEGATED (mirror of verifier NEG_CUES).
NEG_CUES = ("never", "avoid", "contraindicated", "not recommended", "should not",
            "must not", "no bridging", "not required", "does not", "not covered",
            "do not", "without")


def _sentences(text: str):
    return [s for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def sentence_context(sentence: str) -> set:
    """One sentence → context labels: {negated, historical, family} ∩ found."""
    labels = set()
    if any(c in sentence.lower() for c in NEG_CUES):
        labels.add("negated")
    if HISTORICAL_CUES.search(sentence):
        labels.add("historical")
    if FAMILY_CUES.search(sentence):
        labels.add("family")
    return labels


def anchor_contexts(text: str, anchors) -> dict:
    """anchor word → set of labels across every sentence mentioning it."""
    out = {}
    for s in _sentences(text):
        labels = sentence_context(s)
        if not labels:
            continue
        low = s.lower()
        for a in anchors:
            if re.search(rf"\b{re.escape(a)}\b", low):
                out.setdefault(a, set()).update(labels)
    return out


def context_conflicts(answer: str, source_text: str, anchors) -> list:
    """Return human-readable conflict strings for the DANGEROUS direction:
    the answer affirms an anchor as a current patient fact while the source
    only ever mentions it as historical or family (never affirmed-current).

    anchors: iterable of candidate content words (already stopword-filtered).
    """
    conflicts = []
    src_ctx = anchor_contexts(source_text, anchors)
    if not src_ctx:
        return conflicts
    for s in _sentences(answer):
        low = s.lower()
        if "negated" in sentence_context(s):
            continue  # a negated answer sentence is the safe direction
        for a in anchors:
            if not re.search(rf"\b{re.escape(a)}\b", low):
                continue
            labels = src_ctx.get(a, set())
            if not labels:
                continue  # source mentions it affirmingly in-context → fine
            # source ONLY historical or ONLY family for this anchor
            if labels <= {"historical"} or labels <= {"family"} or labels <= {"historical", "family"}:
                sense = "+".join(sorted(labels))
                conflicts.append(f"'{a}' asserted as current fact but source support is {sense}-only")
    return conflicts
