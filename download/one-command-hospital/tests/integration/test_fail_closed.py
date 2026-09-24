"""Integration tier — fail-closed behavior under component failure.

Clinical rule: ANY component down must degrade to "flag for human review",
NEVER to "silently unverified but presented as trustworthy". This tier kills
the verifier mid-flight and asserts the answer comes back FLAGGED, and that
the audit trail still verifies.

Works against both stack flavors:
  docker      → docker compose stop/start verifier
  native      → SIGSTOP/SIGCONT on the verifier PID (tools/native_stack.sh
                writes /tmp/och-native-stack/*.pid). A SIGSTOPed process
                refuses TCP accepts, which is exactly the "unreachable"
                condition the mediator must survive.
"""
import json
import os
import signal
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.integration

from conftest import MEDIATOR, COMPOSE_FILE, RUN_DIR


def _post(url, body, timeout=120):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())


def _compose(*args):
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        capture_output=True, text=True, timeout=120)


def _pid_file(name="verifier"):
    p = RUN_DIR / f"{name}.pid"
    return p if p.exists() else None


def _stop_verifier():
    """Returns (stop_fn, heal_fn). Prefers docker; falls back to SIGSTOP."""
    pid_file = _pid_file()
    if pid_file is None:
        out = _compose("stop", "verifier")
        assert out.returncode == 0, out.stderr
        return
    pid = int(pid_file.read_text().strip())
    os.kill(pid, signal.SIGSTOP)

    def heal():
        os.kill(pid, signal.SIGCONT)
        # give uvicorn a beat to accept again before the next test
        for _ in range(20):
            try:
                urllib.request.urlopen("http://localhost:8212/health", timeout=2)
                return
            except Exception:
                time.sleep(0.5)

    return heal


def test_verifier_down_flags_answer_for_review(stack_ready):
    # 1. Baseline: pipeline healthy → grounded answer.
    status, resp = _post(f"{MEDIATOR}/process",
                         {"question": "How do I bridge warfarin?", "userId": "failtest"})
    assert status == 200

    # 2. Kill the verifier.
    heal = _stop_verifier()
    try:
        # 3. Same question with the verifier gone.
        status, resp = _post(f"{MEDIATOR}/process",
                             {"question": "What INR triggers bridging?", "userId": "failtest"})
        assert status == 200, "clinician must still get an answer (flagged, not dropped)"
        payload = json.loads(resp["communication"]["payload"][0]["contentString"])
        assert payload["grounding"] is False, "unverifiable answer must be flagged"
        assert any("unreachable" in n.lower() for n in payload["verifier_notes"])
        assert payload["human_action"] == "pending_review"
    finally:
        # 4. Heal the stack for subsequent tests.
        if heal:
            heal()
        else:
            _compose("start", "verifier")


def test_audit_chain_still_verifies_after_failures(stack_ready):
    status, resp = _post(f"{MEDIATOR}/process",
                         {"question": "First insulin order questions?", "userId": "failtest"})
    assert status == 200
    req = urllib.request.Request(f"{MEDIATOR}/audit/verify")
    with urllib.request.urlopen(req, timeout=30) as r:
        audit = json.loads(r.read())
    assert audit["ok"] is True
    assert audit["records"] >= 1
