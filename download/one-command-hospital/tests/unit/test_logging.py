"""Unit tier — structured logging + trace ids.

The logging policy is a compliance surface: no raw clinical narrative may
ever reach stdout. These tests pin the JSON shape and the redaction rule.
"""
import json

import hardening
from hardening import json_log, request_id_of, text_sha


def _captured(capsys):
    out = capsys.readouterr().out.strip()
    assert out, "expected a log line"
    return json.loads(out.splitlines()[-1])


def test_json_log_shape(capsys):
    json_log("svc", "event_x", request_id="rid-1", status=200, ms=12.3)
    rec = _captured(capsys)
    assert rec["service"] == "svc"
    assert rec["event"] == "event_x"
    assert rec["request_id"] == "rid-1"
    assert rec["level"] == "info"
    assert rec["status"] == 200
    assert "ts" in rec


def test_json_log_redacts_raw_question_text(capsys):
    json_log("svc", "answer", question="Robert Smith warfarin dose",
             question_sha="abc123", refusal=False)
    rec = _captured(capsys)
    assert rec["question"] == "<redacted len=26>"
    assert "Robert Smith" not in json.dumps(rec)
    assert rec["question_sha"] == "abc123"


def test_json_log_redaction_is_case_insensitive(capsys):
    json_log("svc", "ev", Text="sensitive note body", meta=1)
    rec = _captured(capsys)
    assert rec["Text"] == "<redacted len=19>"
    assert "sensitive" not in json.dumps(rec)
    assert rec["meta"] == 1


def test_text_sha_is_short_stable_and_irreversible():
    h1 = text_sha("same text")
    h2 = text_sha("same text")
    h3 = text_sha("other text")
    assert h1 == h2 and h1 != h3
    assert len(h1) == 12
    assert "same" not in h1


def test_request_id_contextvar_roundtrip():
    token = hardening._request_id.set("trace-xyz")
    try:
        assert request_id_of() == "trace-xyz"
    finally:
        hardening._request_id.reset(token)
    assert request_id_of() is None
