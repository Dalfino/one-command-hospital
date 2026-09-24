#!/usr/bin/env python3
"""Feedback → eval-set seeding (M22 companion).

Reads the mediator's feedback ledger (AUDIT_DIR/feedback.jsonl, written by
POST /review/queue/resolve) and drafts eval entries from clinician
corrections. A correction becomes a graded eval item only when the clinician
tagged the answer `inaccurate` or `unsafe` AND the correction cites the
correct section as [CORPUS-ID §N] — the same citation contract the corpus
uses. Output is a DRAFT yaml: the steward reviews it before it joins
qa_full.yaml (governance rule: eval items are human-approved, never
auto-promoted).

Usage: python3 tools/feedback_to_eval.py /path/to/feedback.jsonl > draft.yaml
"""
import json
import pathlib
import re
import sys

CITE = re.compile(r"\[([A-Z][A-Z0-9-]+)\s*§(\d+)\]")


def draft_entries(feedback_path: pathlib.Path) -> list:
    entries, skipped = [], 0
    for line in feedback_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if rec.get("decision") not in ("inaccurate", "unsafe"):
            skipped += 1
            continue
        correction = str(rec.get("correction", ""))
        m = CITE.search(correction)
        if not m:
            skipped += 1
            continue
        cid, sec = m.group(1), m.group(2)
        # The correction text minus the citation marker becomes the answer key
        # note; the QUESTION itself is recovered by the steward from the audit
        # ledger via qid (audit seq) — we emit the placeholder for them.
        entries.append({
            "id": f"fb-{rec.get('qid', 'unknown')}",
            "question": "TODO-STEWARD: recover question from audit seq " + str(rec.get("qid")),
            "expected_corpus": cid,
            "expected_section": sec,
            "source": {"decision": rec.get("decision"), "by": rec.get("by"),
                       "ts": rec.get("ts"), "correction": correction},
        })
    return entries, skipped


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = pathlib.Path(sys.argv[1])
    if not path.exists():
        print(f"feedback ledger not found: {path}", file=sys.stderr)
        return 1
    entries, skipped = draft_entries(path)
    print("# DRAFT eval items from clinician feedback — steward review required.")
    print("# Do NOT merge into qa_full.yaml without governance sign-off.")
    print("questions:")
    for e in entries:
        print(f"  - id: {e['id']}")
        print(f'    question: "{e["question"]}"')
        print(f"    expected_corpus: {e['expected_corpus']}")
        print(f'    expected_section: "{e["expected_section"]}"')
        src = e["source"]
        print(f"    # {src['decision']} by {src['by']} at {src['ts']}")
        print(f"    # correction: {src['correction'][:200]}")
    if not entries:
        print("# (no eligible corrections)")
    print(f"# {len(entries)} drafted, {skipped} skipped", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
