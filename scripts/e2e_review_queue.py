#!/usr/bin/env python3
"""End-to-end M22 validation: ungrounded answer -> review queue -> resolve
-> feedback ledger -> eval-seeding draft. Runs against the live stack."""
import json
import pathlib
import subprocess
import sys
import urllib.request

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1] / "download" / "one-command-hospital"

MEDIATOR = "http://localhost:8103"


def post(path, body):
    req = urllib.request.Request(
        MEDIATOR + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(MEDIATOR + path, timeout=10) as r:
        return json.loads(r.read())


qs = yaml.safe_load((REPO / "eval" / "qa_seed.yaml").read_text())["questions"]
target = next(q for q in qs if q["id"] == "a02")
print(f"question (a02): {target['question'][:70]}...")

resp = post("/process", {"question": target["question"], "userId": "dr-e2e"})
inner = json.loads(resp["communication"]["payload"][0]["contentString"])
print(f"grounded={inner['grounding']} audit_seq={resp['audit_seq']}")

queue = get("/review/queue")
open_ids = [i["qid"] for i in queue["open"]]
print(f"queue: {queue['counts']}; open items from live traffic: {open_ids}")
assert queue["counts"]["open"] >= 1, "expected live traffic to have produced review items"
qid = open_ids[0]

res = post("/review/queue/resolve", {
    "qid": qid, "decision": "inaccurate", "by": "dr-e2e",
    "correction": "Per [ANTICOAG-BRIDGE §3], interrupt warfarin 5 days before; low-risk needs no bridging."})
print(f"resolved: {res}")

queue2 = get("/review/queue")
print(f"queue after resolve: {queue2['counts']}")

fb = (pathlib.Path("/tmp/och-native-stack/audit-prod") / "feedback.jsonl")
if not fb.exists():
    # native stack layout check
    for p in pathlib.Path("/tmp/och-native-stack").rglob("feedback.jsonl"):
        fb = p
        break
draft = subprocess.run(
    [sys.executable, str(REPO / "tools" / "feedback_to_eval.py"), str(fb)],
    capture_output=True, text=True)
print("--- feedback_to_eval draft (head) ---")
print("\n".join(draft.stdout.splitlines()[:12]))
print(f"... exit={draft.returncode}")
