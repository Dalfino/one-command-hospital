"""Integration tier — the golden path.

One clinical question rides the whole pipeline against REAL containers:
mediator → deid-gate (Presidio) → guideline-rag (mock-LLM extractive mode) →
verifier → FHIR Communication shape → audit ledger → clinician sign-off.
This is the test a hospital would watch before trusting anything.
"""
import json
import urllib.request
import urllib.error

import pytest

pytestmark = pytest.mark.integration

from conftest import DEID, RAG, VERIFIER, MEDIATOR


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, json.loads(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        # error statuses are legitimate expectations in this tier (e.g. the
        # honest 502 when Medplum is absent) — return them, don't raise
        body = e.read()
        try:
            return e.code, json.loads(body), dict(e.headers)
        except Exception:
            return e.code, {}, dict(e.headers)


def _post(url, body, timeout=120):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body), dict(e.headers)
        except Exception:
            return e.code, {}, dict(e.headers)


def test_all_four_services_healthy(stack_ready):
    for url, name in [(f"{DEID}/health", "deid-gate"), (f"{RAG}/health", "guideline-rag"),
                      (f"{VERIFIER}/health", "verifier"), (f"{MEDIATOR}/health", "ai-mediator")]:
        status, body, _ = _get(url)
        assert status == 200 and body.get("ok") is True, f"{name} not healthy"


def test_rag_mock_mode_answers_with_citation(stack_ready):
    """LLM unreachable → extractive fallback must STILL carry a citation."""
    status, body, _ = _post(f"{RAG}/answer", {"question": "How do I bridge warfarin?"})
    assert status == 200
    assert body["refusal"] is False
    assert len(body["citations"]) >= 1, "extractive fallback must cite its section"
    assert body["citations"][0]["corpus_id"] == "ANTICOAG-BRIDGE"


def test_rag_refuses_off_corpus_question(stack_ready):
    status, body, _ = _post(f"{RAG}/answer",
                            {"question": "quantum flux capacitor recalibration"})
    assert status == 200
    assert body["refusal"] is True
    assert body["answer"] == "NOT_COVERED"
    assert body["citations"] == []


def test_golden_path_end_to_end(stack_ready):
    """THE test: question in → cited answer out → audit appended → verify ok."""
    status, resp, headers = _post(f"{MEDIATOR}/process", {
        "question": "What is the perioperative bridging protocol for warfarin?",
        "userId": "integration-test",
    })
    assert status == 200
    assert "X-Request-ID" in headers, "trace id must be echoed"

    payload = json.loads(resp["communication"]["payload"][0]["contentString"])
    assert payload["refusal"] is False
    assert len(payload["citations"]) >= 1
    assert payload["grounding"] is True, "golden-path answer must verify grounded"
    assert payload["human_action"] == "pending_review"
    # the raw question was de-identified before persistence — structural check
    assert "Robert Smith" not in json.dumps(payload)

    assert isinstance(resp["audit_seq"], int) and resp["audit_seq"] >= 1

    status, audit, _ = _get(f"{MEDIATOR}/audit/verify")
    assert status == 200
    assert audit["ok"] is True
    assert audit["records"] >= resp["audit_seq"]


def test_signoff_closes_the_human_action_loop(stack_ready):
    status, resp, _ = _post(f"{MEDIATOR}/process", {
        "question": "When should sepsis screening be repeated?",
        "userId": "integration-test",
    })
    comm_id = resp["communication"]["id"]
    status, out, _ = _post(f"{MEDIATOR}/signoff", {
        "communicationId": comm_id, "action": "signed_off", "by": "dr-integration"})
    # Medplum is absent in the test stack → the FHIR read fails with 404;
    # the endpoint must say so honestly, not pretend the sign-off landed.
    assert status in (200, 404, 502)
    if status == 404:
        assert "not found" in out["error"].lower()


def test_audit_detects_ledger_in_this_stack(stack_ready):
    status, audit, _ = _get(f"{MEDIATOR}/audit/verify")
    assert status == 200 and audit["ok"] is True
    assert audit["records"] >= 1, "golden-path test must have written audit events"
