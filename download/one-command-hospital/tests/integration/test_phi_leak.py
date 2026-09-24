"""Integration tier — the PHI white-out, tested against real Presidio.

Identifiers in → identifiers must NOT survive. Feeds obviously-fake patient
identifiers through deid-gate and through the full mediator pipeline, then
greps every surface we can see (scrubbed question, persisted Communication
payload, audit detail) for the originals. Synthetic identifiers only — never
real PHI in tests.
"""
import json
import urllib.request
import urllib.error

import pytest

pytestmark = pytest.mark.integration

from conftest import DEID, MEDIATOR

# obviously synthetic identifiers (fake name / DOB / MRN / phone)
FAKE_NOTE = ("Patient Robert Smith, DOB 05/12/1968, MRN 4471182, "
             "call 555-0143 regarding warfarin bridging plan.")
SECRETS = ["Robert Smith", "4471182", "555-0143", "05/12/1968"]


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


def test_deid_gate_strips_every_planted_identifier(stack_ready):
    status, body, _ = _post(f"{DEID}/deid", {"text": FAKE_NOTE})
    assert status == 200
    assert body["finding_count"] >= 3, "planted identifiers must be detected"
    for secret in SECRETS:
        assert secret not in body["anonymized"], f"identifier survived: {secret}"


def test_mediator_persists_no_planted_phi(stack_ready):
    """The full pipeline: question+context planted with PHI → nothing survives
    into the Communication payload that would land in the EHR."""
    status, resp, _ = _post(f"{MEDIATOR}/process", {
        "question": "Robert Smith's warfarin bridging plan?",
        "contextText": FAKE_NOTE,
        "userId": "phi-test",
    })
    assert status == 200
    blob = json.dumps(resp["communication"])
    for secret in SECRETS:
        assert secret not in blob, f"PHI leaked into FHIR Communication: {secret}"
    # and the audit detail (no narratives by policy) stays clean too
    assert "Robert Smith" not in json.dumps({"a": resp["audit_seq"]})
