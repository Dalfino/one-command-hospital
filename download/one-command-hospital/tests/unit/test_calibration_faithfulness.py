"""Unit tier — M20 calibration math + M23 faithfulness scorer.

Synthetic data with known answers: ECE/risk-coverage/threshold must match
hand-computed values; faithfulness must catch fabricated numbers, polarity
flips, and unsupported claims while passing faithful ones.
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "eval"))

from calibrate import ece, risk_coverage, recommend_threshold, analyze  # noqa: E402
from faithfulness import decompose_claims, faithfulness  # noqa: E402

# ── calibration math ─────────────────────────────────────────────────────

def _rows(pairs):
    return [{"confidence": c, "correct": bool(k)} for c, k in pairs]


def test_ece_perfect_calibration():
    # each bin: accuracy exactly == confidence → ECE 0
    # bin b: conf=(2b+1)/20, correct rows=(2b+1) of 20 → acc == conf exactly
    rows = []
    for b in range(10):
        conf = round((2 * b + 1) / 20, 3)
        rows += _rows([(conf, 1)] * (2 * b + 1) + [(conf, 0)] * (19 - 2 * b))
    e, table = ece(rows)
    assert e is not None and e < 1e-6
    assert len(table) == 10 and all(t["n"] == 20 for t in table)


def test_ece_worst_case():
    rows = _rows([(0.9, 0)] * 10 + [(0.1, 1)] * 10)
    e, _ = ece(rows)
    assert e > 0.7  # |0.9-0| and |0.1-1| averaged = 0.9


def test_risk_coverage_monotone_coverage():
    rows = _rows([(0.9, 1), (0.8, 1), (0.7, 0), (0.6, 0)])
    curve = risk_coverage(rows)
    covs = [p["coverage"] for p in curve]
    assert covs == sorted(covs) and covs[-1] == 1.0
    assert curve[0]["risk"] == 0.0 and curve[-1]["risk"] == 0.5


def test_threshold_picks_max_coverage_under_target():
    rows = _rows([(0.95, 1), (0.9, 1), (0.5, 0), (0.4, 0)])
    rec = recommend_threshold(rows, target_risk=0.34)
    # coverage 0.5 → risk 0.0 (both high-conf correct); 0.75 → 1/3 ≤ 0.34? 0.333 ≤ 0.34 ✓
    assert rec["threshold"] == 0.5 and rec["coverage"] == 0.75
    rec2 = recommend_threshold(rows, target_risk=0.0)
    assert rec2["coverage"] == 0.5  # only the all-correct prefix qualifies


def test_threshold_honest_no_win():
    rows = _rows([(0.9, 0)] * 4)
    rec = recommend_threshold(rows, target_risk=0.10)
    assert rec["threshold"] is None and "do not tune" in rec["note"]


def test_analyze_on_real_scores_file(tmp_path):
    f = tmp_path / "scores.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in
                           [{"confidence": 0.9, "correct": 1},
                            {"confidence": 0.3, "correct": 0}]))
    out = analyze(f)
    assert out["n"] == 2 and out["accuracy"] == 0.5 and out["ece"] is not None


# ── faithfulness scorer ──────────────────────────────────────────────────

CITED = ("Warfarin should be interrupted 5 days before elective surgery. "
         "Bridging with LMWH is not required for low-risk patients. "
         "Reserve heparin for high-risk mechanical valves.")


def test_decompose_drops_fragments():
    claims = decompose_claims("[ANTICOAG-BRIDGE §3] Continue warfarin per protocol. [ANTICOAG-BRIDGE §4] ok")
    assert len(claims) == 1 and "Continue" in claims[0]


def test_faithful_answer_scores_1():
    answer = ("[ANTICOAG-BRIDGE §3] Warfarin is interrupted 5 days before elective surgery. "
              "[ANTICOAG-BRIDGE §4] LMWH bridging is not required for low-risk patients.")
    out = faithfulness(answer, [CITED])
    assert out["score"] == 1.0, out


def test_fabricated_number_is_unsupported():
    answer = "[X §1] Warfarin is interrupted 3 days before elective surgery."
    out = faithfulness(answer, [CITED])
    assert out["score"] == 0.0 and "number" in out["claims"][0]["reason"]


def test_polarity_flip_is_unsupported():
    answer = "[X §1] Bridging with LMWH is required for low-risk patients."
    out = faithfulness(answer, [CITED])
    assert out["score"] == 0.0 and "polarity" in out["claims"][0]["reason"]


def test_unsupported_claim_detected():
    answer = "[X §1] Schedule the patient for monthly INR checks at the anticoagulation clinic."
    out = faithfulness(answer, [CITED])
    assert out["score"] == 0.0 and "overlap" in out["claims"][0]["reason"]


def test_no_citations_is_none_not_perfect():
    out = faithfulness("Some answer with no citations.", [])
    assert out["score"] is None
