#!/usr/bin/env python3
"""Confidence calibration + selective abstention analysis (M20).

Answers the two questions the roadmap called "refusal is a guess, not a
control":
  1. CALIBRATION — does higher confidence actually mean higher correctness?
     (10-bin reliability table + ECE, computed on eval-run scores.)
  2. SELECTIVE ABSTENTION — if the system abstains below confidence T, what
     accuracy does the REMAINING answered population have at what coverage?
     (risk-coverage curve; recommended T = highest coverage with risk <=
     TARGET_RISK, default 10%.)

Input: eval/scores.jsonl — one {"confidence": float, "correct": 0|1} per
graded answer, written by run_eval.py in full mode (confidence = normalized
top retrieval score of the live response). Zero heavy deps.
"""
import json
import pathlib
import sys

BINS = 10
TARGET_RISK = float(__import__("os").environ.get("TARGET_RISK", "0.10"))


def load_scores(path: pathlib.Path) -> list:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            if isinstance(r.get("confidence"), (int, float)) and \
               isinstance(r.get("correct"), (int, float)):
                rows.append({"confidence": float(r["confidence"]),
                             "correct": bool(int(r["correct"]))})
        except json.JSONDecodeError:
            continue
    return rows


def ece(rows: list, bins: int = BINS) -> tuple:
    """(expected_calibration_error, reliability_table).
    reliability_table: [{bin, lo, hi, n, accuracy, confidence}] sorted."""
    if not rows:
        return None, []
    width = 1.0 / bins
    table, ece_sum, total = [], 0.0, len(rows)
    for b in range(bins):
        lo, hi = b * width, (b + 1) * width
        in_bin = [r for r in rows
                  if (lo <= r["confidence"] < hi)
                  or (b == bins - 1 and r["confidence"] == 1.0)]  # 1.0 excluded by < hi otherwise
        entry = {"bin": b, "lo": round(lo, 2), "hi": round(hi, 2), "n": len(in_bin),
                 "accuracy": None, "confidence": None}
        if in_bin:
            acc = sum(r["correct"] for r in in_bin) / len(in_bin)
            conf = sum(r["confidence"] for r in in_bin) / len(in_bin)
            entry.update(accuracy=round(acc, 3), confidence=round(conf, 3))
            ece_sum += (len(in_bin) / total) * abs(acc - conf)
        table.append(entry)
    return round(ece_sum, 4), table


def risk_coverage(rows: list) -> list:
    """Sorted high→low confidence; risk at each coverage prefix."""
    ordered = sorted(rows, key=lambda r: -r["confidence"])
    curve, errors, n = [], 0, len(ordered)
    for i, r in enumerate(ordered, 1):
        errors += 0 if r["correct"] else 1
        curve.append({"coverage": round(i / n, 4), "risk": round(errors / i, 4)})
    return curve


def recommend_threshold(rows: list, target_risk: float = TARGET_RISK) -> dict:
    """Highest-confidence threshold whose ANSWERED population keeps risk
    <= target_risk. Returns {threshold, coverage, risk} or the no-win note."""
    ordered = sorted(rows, key=lambda r: -r["confidence"])
    best = None
    errors, n = 0, len(ordered)
    for i, r in enumerate(ordered, 1):
        errors += 0 if r["correct"] else 1
        risk = errors / i
        if risk <= target_risk:
            best = {"threshold": round(r["confidence"], 4),
                    "coverage": round(i / n, 4), "risk": round(risk, 4)}
    if best is None:
        return {"threshold": None,
                "note": f"no prefix achieves risk <= {target_risk} — do not tune abstention on this set"}
    return best


def analyze(path: pathlib.Path) -> dict:
    rows = load_scores(path)
    e, table = ece(rows)
    out = {
        "n": len(rows),
        "accuracy": round(sum(r["correct"] for r in rows) / len(rows), 4) if rows else None,
        "ece": e,
        "reliability": table,
        "risk_coverage": risk_coverage(rows),
        "recommended_threshold": recommend_threshold(rows),
        "target_risk": TARGET_RISK,
        "caveat": "mock-mode scores (extractive/retrieval confidence); refit on GPU generations before clinical use",
    }
    return out


if __name__ == "__main__":
    scores = pathlib.Path(__file__).parent / "scores.jsonl"
    result = analyze(scores)
    out = pathlib.Path(__file__).parent / "calibration.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"n={result['n']} accuracy={result['accuracy']} ECE={result['ece']}")
    print(f"recommended abstention threshold: {result['recommended_threshold']}")
    print(f"→ {out}")
    if not result.get("n"):
        print("scores.jsonl missing/empty — run run_eval.py with RAG_URL first", file=sys.stderr)
        sys.exit(1)
