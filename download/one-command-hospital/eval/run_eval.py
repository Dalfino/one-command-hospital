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

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDELINES = ROOT / "guidelines"
QUESTIONS = yaml.safe_load((pathlib.Path(__file__).parent / "qa_seed.yaml").read_text())["questions"]

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
        header = text.split("## ")[0]
        # split into numbered sections on "## N. Title"
        parts = re.split(r"^(##\s+\d+\..+)$", text, flags=re.M)
        for i in range(1, len(parts), 2):
            block = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            num = re.match(r"##\s+(\d+)\.", block).group(1)
            sections.append({
                "corpus_id": entry["id"],
                "section": num,
                "text": block + "\n" + body,
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
                if q.get("refusal"):
                    ref_ok += refused
                    row["answer"] = "PASS" if refused else "FAIL"
                else:
                    ok_refusal = not refused
                    valid_cites = any(c.get("corpus_id") == q["expected_corpus"]
                                      and str(c.get("section")) == q["expected_section"]
                                      for c in cites)
                    cite_ok += (ok_refusal and valid_cites)
                    row["answer"] = "PASS" if (ok_refusal and valid_cites) else "FAIL"
                    row["cites"] = "; ".join(f'{c.get("corpus_id")}§{c.get("section")}' for c in cites) or "-"
            except Exception as e:  # service down → don't crash the harness
                row["answer"] = f"ERR ({e.__class__.__name__})"
        rows.append(row)

    lines = [
        "# Eval report",
        f"- generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- mode: {'full (RAG_URL)' if rag_url else 'retrieval-only'} | bm25: {HAVE_BM25}",
        f"- answerable: {n_ans} | retrieval hits: {hits} ({100.0 * hits / max(n_ans, 1):.0f}%)",
    ]
    if rag_url:
        lines.append(f"- refusal cases: {n_ref} | correct refusals: {ref_ok}")
        lines.append(f"- grounded answers (valid citation): {cite_ok}/{n_ans}")
    lines += ["", "| id | expected | hit | answer | top retrieved |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f'| {r["id"]} | {r["expected"]} | {r["retrieval_hit"]} | {r.get("answer", "-")} | {r["top"]} |')
    (pathlib.Path(__file__).parent / "report.md").write_text("\n".join(lines))
    print("\n".join(lines[:6]))
    print(f"→ full report: {pathlib.Path(__file__).parent / 'report.md'}")
    if n_ans and hits < 0.8 * n_ans:
        sys.exit(2)  # CI gate: retrieval below 80% fails the build


if __name__ == "__main__":
    main()
