#!/usr/bin/env python3
"""Guideline Copilot eval harness.

Two modes:
  1. Retrieval-only (default, no GPU needed): scores BM25 section retrieval.
  2. Full mode (RAG_URL set, e.g. http://localhost:8101): also checks citation
     validity and refusal behavior of the live service.

Scores every question in qa_seed.yaml, then writes eval/report.md.
"""
import os
import re
import sys
import json
import time
import pathlib
import urllib.request

import yaml

try:
    from faithfulness import faithfulness as faithfulness_score  # M23
except ImportError:  # direct-script execution from eval/ cwd
    faithfulness_score = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDELINES = ROOT / "guidelines"
# Usage: run_eval.py [questions.yaml]   (default: qa_seed.yaml; CI also runs qa_full.yaml)
_qfile = sys.argv[1] if len(sys.argv) > 1 else "qa_seed.yaml"
QUESTIONS = yaml.safe_load((pathlib.Path(__file__).parent / _qfile).read_text())["questions"]

try:
    from rank_bm25 import BM25Okapi
    HAVE_BM25 = True
except ImportError:  # graceful fallback: tiny TF scorer
    HAVE_BM25 = False

WORD = re.compile(r"[a-z0-9]+")
SECTION = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.M)


def load_corpus():
    manifest = yaml.safe_load((GUIDELINES / "manifest.yaml").read_text())["corpus"]
    sections = []
    for entry in manifest:
        text = (GUIDELINES / entry["file"]).read_text()
        # split into numbered sections on "## N. Title"
        parts = re.split(r"^(##\s+\d+\..+)$", text, flags=re.M)
        for i in range(1, len(parts), 2):
            block = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            m = re.match(r"##\s+(\d+)\.\s*(.+)", block)
            num, sec_title = m.group(1), m.group(2)
            # Title-boost, synced with services/guideline-rag/app/main.py
            chunk = (f"[{entry['title']} — §{num} {sec_title}] "
                     f"(edition {entry['edition']})\n{block}\n{body}")
            sections.append({
                "corpus_id": entry["id"],
                "section": num,
                "text": chunk,
            })
    return sections


def tokenize(s):
    return WORD.findall(s.lower())


def retrieval_scores(sections):
    if HAVE_BM25:
        bm25 = BM25Okapi([tokenize(s["text"]) for s in sections])
        return lambda q: bm25.get_scores(tokenize(q))
    # fallback: crude term overlap
    dts = [set(tokenize(s["text"])) for s in sections]
    return lambda q: [len(dts[i] & set(tokenize(q))) for i in range(len(sections))]


def call_rag(url, question):
    # Accept either the service root (http://host:8101) or the full endpoint
    # (http://host:8101/answer) — a bare host used to 404 every request.
    if not url.rstrip("/").endswith("/answer"):
        url = url.rstrip("/") + "/answer"
    req = urllib.request.Request(
        url,
        data=json.dumps({"question": question}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    sections = load_corpus()
    scorer = retrieval_scores(sections)
    rag_url = os.environ.get("RAG_URL")
    top_k = int(os.environ.get("TOP_K", "3"))
    score_rows = []  # M20: {confidence, correct} per graded item
    faith_scores = []  # M23: per-answer claim-level faithfulness

    rows, hits, ref_ok, cite_ok, n_ref, n_ans = [], 0, 0, 0, 0, 0
    for q in QUESTIONS:
        scores = scorer(q["question"])
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        top_refs = [(sections[i]["corpus_id"], sections[i]["section"]) for i in top]

        row = {"id": q["id"], "question": q["question"][:70] + "..."}
        if q.get("refusal"):
            n_ref += 1
            row["expected"] = "NOT_COVERED"
            row["retrieval_hit"] = "trap"  # graded on answer behavior in full mode
        else:
            n_ans += 1
            expected_hit = (q["expected_corpus"], q["expected_section"]) in top_refs
            row["expected"] = f'{q["expected_corpus"]} §{q["expected_section"]}'
            row["retrieval_hit"] = "PASS" if expected_hit else "FAIL"
            hits += expected_hit
        row["top"] = " | ".join(f"{c}§{s}" for c, s in top_refs)

        if rag_url:
            try:
                t0 = time.time()
                resp = call_rag(rag_url, q["question"])
                row["latency_ms"] = int((time.time() - t0) * 1000)
                refused = bool(resp.get("refusal"))
                cites = resp.get("citations", [])
                # M20 confidence signal: normalized top retrieval score.
                rmeta = resp.get("retrieval") or {}
                tops = rmeta.get("top") or []
                confidence = float(tops[0]["score"]) if tops else 0.0
                if q.get("refusal"):
                    ref_ok += refused
                    row["answer"] = "PASS" if refused else "FAIL"
                    score_rows.append({"confidence": round(confidence, 4),
                                       "correct": int(bool(refused))})
                else:
                    ok_refusal = not refused
                    valid_cites = any(c.get("corpus_id") == q["expected_corpus"]
                                      and str(c.get("section")) == q["expected_section"]
                                      for c in cites)
                    cite_ok += (ok_refusal and valid_cites)
                    row["answer"] = "PASS" if (ok_refusal and valid_cites) else "FAIL"
                    row["cites"] = "; ".join(f'{c.get("corpus_id")}§{c.get("section")}' for c in cites) or "-"
                    score_rows.append({"confidence": round(confidence, 4),
                                       "correct": int(bool(ok_refusal and valid_cites))})
                    # M23: claim-level faithfulness against the cited sections
                    if faithfulness_score and not refused:
                        f = faithfulness_score(resp.get("answer", ""),
                                               [c.get("text", "") for c in cites])
                        if f["score"] is not None:
                            faith_scores.append(f["score"])
                            row["faith"] = f["score"]
            except Exception as e:  # service down → don't crash the harness
                row["answer"] = f"ERR ({e.__class__.__name__})"
        rows.append(row)

    # M20: persist per-item confidence/correctness for calibrate.py
    if score_rows:
        (pathlib.Path(__file__).parent / "scores.jsonl").write_text(
            "\n".join(json.dumps(r) for r in score_rows) + "\n")

    lines = [
        "# Eval report",
        f"- generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- mode: {'full (RAG_URL)' if rag_url else 'retrieval-only'} | bm25: {HAVE_BM25}",
        f"- answerable: {n_ans} | retrieval hits: {hits} ({100.0 * hits / max(n_ans, 1):.0f}%)",
    ]
    if rag_url:
        lines.append(f"- refusal cases: {n_ref} | correct refusals: {ref_ok}")
        lines.append(f"- grounded answers (valid citation): {cite_ok}/{n_ans}")
    if faith_scores:
        lines.append(f"- claim faithfulness: mean {sum(faith_scores)/len(faith_scores):.2f} "
                     f"over {len(faith_scores)} answers (M23; mock-mode extractive generator)")
    if rag_url and score_rows:
        lines.append("- calibration: run `python3 calibrate.py` for ECE + risk-coverage + abstention threshold")
    lines += ["", "| id | expected | hit | answer | faith | top retrieved |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f'| {r["id"]} | {r["expected"]} | {r["retrieval_hit"]} | {r.get("answer", "-")} | {r.get("faith", "-")} | {r["top"]} |')
    (pathlib.Path(__file__).parent / _report_name()).write_text("\n".join(lines))
    print("\n".join(lines[:6]))
    print(f"→ full report: {pathlib.Path(__file__).parent / _report_name()}")
    if n_ans and hits < 0.8 * n_ans:
        sys.exit(2)  # CI gate: retrieval below 80% fails the build


def _report_name():
    if len(sys.argv) <= 1 or sys.argv[1].endswith("qa_seed.yaml"):
        return "report.md"
    if sys.argv[1].endswith("qa_injection.yaml"):
        return "report_injection.md"
    return "report_full.md"


if __name__ == "__main__":
    main()
