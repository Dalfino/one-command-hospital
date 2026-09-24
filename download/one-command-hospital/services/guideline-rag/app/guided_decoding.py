"""Guided (constrained) decoding for the answer contract.

ADOPT item from docs/tech_radar.md ("Structured-output / constrained
decoding"): until now the cite-or-refuse contract was enforced by PROMPT
alone. vLLM can enforce it at the DECODING level via `guided_json` — the
model is mechanically unable to emit anything except the answer schema,
which removes the "citation-less answer" and "free-text refusal drift"
failure classes instead of hoping the prompt prevents them.

Transport contract (deliberately fail-open to the legacy path):
  - vLLM's OpenAI-compatible server accepts a `guided_json` request field
    carrying a JSON schema. Newer versions group it under
    `structured_outputs`; GUIDED_JSON_FIELD switches the wire name without
    code changes (default stays the widely-supported `guided_json`).
  - A server that ignores the field answers free text -> parse_guided()
    returns None -> the legacy text contract (NOT_COVERED literal +
    [CORPUS_ID §N] markers) runs unchanged. Degrades, never breaks.
  - A server that TRIES to honor the field but emits unparseable JSON is
    treated as a generator malfunction and refused (fail closed) — see
    main.py's post-parse handling.

The schema is mirrored at deploy/vllm/guided_answer_schema.json for ops
visibility; a unit test asserts the two copies never drift.
"""
import json
import os

# Wire name vLLM uses for schema-guided decoding on /chat/completions.
GUIDED_JSON_FIELD_DEFAULT = "guided_json"

ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["covered", "answer", "citations"],
    "properties": {
        "covered": {
            "type": "boolean",
            "description": "false = the excerpts do not answer the question",
        },
        "answer": {
            "type": "string",
            "description": "Guideline answer; every claim cited inline as [CORPUS_ID §N]. "
                           "When covered=false this is exactly NOT_COVERED.",
        },
        "citations": {
            "type": "array",
            "description": "Every citation used in `answer`, as structured pairs.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["corpus_id", "section"],
                "properties": {
                    "corpus_id": {"type": "string", "pattern": "^[A-Z][A-Z0-9-]+$"},
                    "section": {"type": "integer", "minimum": 0},
                },
            },
        },
    },
}


def guided_enabled() -> bool:
    """GUIDED_DECODING=0/false/no/off disables the constraint (legacy mode)."""
    return os.environ.get("GUIDED_DECODING", "1").strip().lower() not in (
        "0", "false", "no", "off")


def guided_field() -> str:
    """Wire field name for the schema (vLLM: guided_json | structured_outputs)."""
    return os.environ.get("GUIDED_JSON_FIELD", GUIDED_JSON_FIELD_DEFAULT)


def guided_request_fields() -> dict:
    """Extra /chat/completions body fields that turn on guided decoding.
    Empty dict = legacy mode (constraint off) — callers just merge it in."""
    if not guided_enabled():
        return {}
    return {guided_field(): ANSWER_SCHEMA}


def parse_guided(content: str):
    """Parse a guided-JSON answer, strictly mirroring ANSWER_SCHEMA.

    Returns {"covered": bool, "answer": str, "citations": [{corpus_id, section}]}
    or None when `content` is not a valid guided answer (free-text/legacy).
    Strictness is the point: a constrained server should NEVER produce
    something this rejects, so a reject on a guided run is a real anomaly
    (handled fail-closed by the caller), while plain free text from a
    legacy server lands here constantly and must return None quietly.
    """
    if not isinstance(content, str):
        return None
    try:
        obj = json.loads(content)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    if set(obj) - {"covered", "answer", "citations"}:
        return None
    covered, answer, citations = obj.get("covered"), obj.get("answer"), obj.get("citations")
    if not isinstance(covered, bool) or not isinstance(answer, str):
        return None
    if not isinstance(citations, list):
        return None
    norm = []
    for c in citations:
        if not isinstance(c, dict) or set(c) - {"corpus_id", "section"}:
            return None
        cid, sec = c.get("corpus_id"), c.get("section")
        if not isinstance(cid, str) or not cid:
            return None
        # bool is an int subclass in Python — exclude it explicitly
        if isinstance(sec, bool) or not isinstance(sec, int) or sec < 0:
            return None
        norm.append({"corpus_id": cid, "section": sec})
    return {"covered": covered, "answer": answer, "citations": norm}
