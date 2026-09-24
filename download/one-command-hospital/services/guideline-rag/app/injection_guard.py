"""Injection guard — prompt-injection pattern screening (M19).

Two attack surfaces in a hospital RAG pipeline:
  1. The QUESTION — a clinician prompt is de-identified but not sanitized;
     a hostile or pasted-in payload can carry generator instructions.
  2. The CORPUS — guidelines are versioned documents updated by humans; a
     poisoned or corrupted chunk could smuggle instructions into the prompt.

scan() is a pure, dependency-light pattern matcher tuned for LOW false
positives on clinical language: every pattern needs an explicit
instruction-verb + target collocation ("ignore all instructions"), never a
single common word. Designed to refuse-and-log, not to silently strip.
"""
import re

# (pattern_id, compiled regex). Anchored on instruction collocations, not
# single words — "discharge instructions" must never trip this.
_PATTERNS = [
    ("ignore-instructions",
     re.compile(r"\bignore\s+(all|any|the\s+above|all\s+previous|previous|prior|earlier)\s+(instructions|prompts?|rules?|directions?)\b", re.I)),
    ("disregard-instructions",
     re.compile(r"\bdisregard\s+(all|any|the|your|previous|all\s+previous)\s+(instructions|prompts?|rules?|guidance)\b", re.I)),
    ("system-prompt-probe",
     re.compile(r"\b(system\s+prompt|initial\s+prompt|your\s+original\s+instructions?|hidden\s+instructions?)\b", re.I)),
    ("reveal-prompt",
     re.compile(r"\b(reveal|show|print|repeat|output|display|dump)\s+(me\s+)?(your\s+)?(system\s+prompt|instructions|prompt|rules)\b", re.I)),
    ("role-hijack",
     re.compile(r"\b(you\s+are\s+now|act\s+as\s+if|pretend\s+to\s+be|from\s+now\s+on\s+you\s+are|enter\s+developer\s+mode|enable\s+DAN\s+mode|do\s+anything\s+now)\b", re.I)),
    ("override-behavior",
     re.compile(r"\b(override|bypass|disable)\s+(your\s+)?(safety|filters?|guardrails?|restrictions?|rules)\b", re.I)),
    ("exfil-instruction",
     re.compile(r"\b(send|post|email|upload|exfiltrate)\s+(this|(?:the\s+)?patient\s+data|the\s+data|the\s+text)\s+(to|out|somewhere)\b", re.I)),
    ("embedded-protocol",
     re.compile(r"\b(end\s+of\s+system\s+prompt|new\s+system\s+instructions?|assistant:\s*(sure|ok|of course))\b", re.I)),
    ("invisible-exfil",
     re.compile(r"(!\[[^\]]*\]\(https?://|data:image/|<img\s|javascript:)", re.I)),
]

MAX_FINDINGS = 8


def scan(text: str) -> list:
    """Return [{pattern_id, match_sha}] for every injection pattern hit.
    Bounded output; never returns the raw matched text (logs stay PHI-safe)."""
    if not text:
        return []
    import hashlib
    findings = []
    for pid, rx in _PATTERNS:
        m = rx.search(text)
        if m:
            findings.append({
                "pattern_id": pid,
                "match_sha": hashlib.sha256(m.group(0).encode()).hexdigest()[:12],
            })
            if len(findings) >= MAX_FINDINGS:
                break
    return findings


def is_suspicious(text: str) -> bool:
    return bool(scan(text))
