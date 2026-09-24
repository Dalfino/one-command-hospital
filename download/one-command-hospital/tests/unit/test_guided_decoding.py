"""Unit tier — guided (constrained) decoding (v0.6.1 ADOPT item).

Covers: schema/file mirror integrity, wire-field selection, strict guided-JSON
parsing (the fail-open-to-legacy contract), and the guided prompt variant.
"""
import json
import pathlib

from app import guided_decoding as gd
from app import main as rag

REPO = pathlib.Path(__file__).resolve().parents[2]


def test_deploy_schema_mirror_never_drifts():
    """deploy/vllm/guided_answer_schema.json is an ops mirror of the Python
    constant — the unit tier enforces the sync."""
    on_disk = json.loads(
        (REPO / "deploy" / "vllm" / "guided_answer_schema.json").read_text())
    assert on_disk == gd.ANSWER_SCHEMA


def test_guided_enabled_default_and_disable():
    assert gd.guided_enabled() is True  # default on
    import os
    old = os.environ.get("GUIDED_DECODING")
    try:
        for v in ("0", "false", "no", "off"):
            os.environ["GUIDED_DECODING"] = v
            assert gd.guided_enabled() is False, v
        os.environ["GUIDED_DECODING"] = "1"
        assert gd.guided_enabled() is True
    finally:
        if old is None:
            os.environ.pop("GUIDED_DECODING", None)
        else:
            os.environ["GUIDED_DECODING"] = old


def test_request_fields_use_configured_wire_name():
    import os
    old = os.environ.get("GUIDED_JSON_FIELD")
    try:
        os.environ.pop("GUIDED_JSON_FIELD", None)
        assert gd.guided_request_fields() == {"guided_json": gd.ANSWER_SCHEMA}
        os.environ["GUIDED_JSON_FIELD"] = "structured_outputs"
        assert list(gd.guided_request_fields()) == ["structured_outputs"]
    finally:
        if old is None:
            os.environ.pop("GUIDED_JSON_FIELD", None)
        else:
            os.environ["GUIDED_JSON_FIELD"] = old


def test_request_fields_empty_when_disabled(monkeypatch):
    monkeypatch.setenv("GUIDED_DECODING", "0")
    assert gd.guided_request_fields() == {}


def test_parse_guided_accepts_valid_schema_output():
    out = gd.parse_guided(json.dumps({
        "covered": True,
        "answer": "Bridging is required [ANTICOAG-BRIDGE §2].",
        "citations": [{"corpus_id": "ANTICOAG-BRIDGE", "section": 2}],
    }))
    assert out is not None
    assert out["covered"] is True
    assert out["citations"][0]["corpus_id"] == "ANTICOAG-BRIDGE"


def test_parse_guided_rejects_legacy_free_text():
    """A server that ignored guided_json answers free text → None → legacy
    contract. This is the fail-open path the whole design rests on."""
    assert gd.parse_guided("NOT_COVERED") is None
    assert gd.parse_guided("[ANTICOAG-BRIDGE §1] Bridging dose is ...") is None
    assert gd.parse_guided("") is None
    assert gd.parse_guided(None) is None
    assert gd.parse_guided(["not", "an", "object"]) is None


def test_parse_guided_rejects_malformed_structured_output():
    bad = [
        '{"covered": "yes"}',                      # wrong type
        '{"covered": true}',                       # missing fields
        '{"covered": true, "answer": "", "citations": {}}',  # citations not array
        '{"covered": true, "answer": "", "citations": [{"corpus_id": "X"}]}',  # missing section
        '{"covered": true, "answer": "", "citations": [{"corpus_id": "X", "section": true}]}',  # bool is not an int here
        '{"covered": true, "answer": "", "citations": [{"corpus_id": "X", "section": -1}]}',   # negative
        '{"covered": true, "answer": "", "citations": [], "extra": 1}',   # unknown key
        'not json at all {',                       # unparseable
        '[1,2,3]',                                 # JSON but not an object
    ]
    for b in bad:
        assert gd.parse_guided(b) is None, b


def test_guided_prompt_mentions_schema_and_markers():
    hits = [{"corpus_id": "X", "section": "1", "edition": "2024", "text": "body"}]
    g = rag.build_prompt("q?", hits, guided=True)
    assert '"covered"' in g and "[CORPUS_ID" in g and "EXCERPTS:" in g
    legacy = rag.build_prompt("q?", hits, guided=False)
    assert "JSON" not in legacy
    assert "NOT_COVERED" in g and "NOT_COVERED" in legacy


def test_guided_answer_with_covered_false_is_refusal_shape():
    """Integration of parse + decision shape: covered=false must read as the
    generator's refusal (mirrors the branch in main.answer)."""
    raw = json.dumps({"covered": False, "answer": "NOT_COVERED", "citations": []})
    obj = gd.parse_guided(raw)
    assert obj is not None and obj["covered"] is False
