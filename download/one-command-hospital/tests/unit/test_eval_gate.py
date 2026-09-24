"""Unit tier — the eval CI gate itself.

The 80% retrieval floor only protects patients if the gate actually fails
the build. This module proves both directions: the shipped seed set passes,
and a deliberately impossible question set fails with the gate exit code.
"""
import pathlib
import subprocess
import sys

EVAL_DIR = pathlib.Path(__file__).resolve().parents[2] / "eval"

IMPOSSIBLE_YAML = """\
questions:
  - id: gate-fail-a
    question: zzz quantum flux capacitor recalibration protocol
    expected_corpus: NOPE-NOP
    expected_section: "99"
  - id: gate-fail-b
    question: warp coil insulation maintenance schedule
    expected_corpus: NOPE-NOP
    expected_section: "98"
"""


def test_seed_eval_passes_the_gate():
    r = subprocess.run([sys.executable, "run_eval.py", "qa_seed.yaml"],
                       cwd=EVAL_DIR, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"seed eval must pass ≥80% gate:\n{r.stdout[-800:]}"


def test_gate_fails_when_retrieval_collapses(tmp_path):
    qfile = tmp_path / "qa_gate_probe.yaml"
    qfile.write_text(IMPOSSIBLE_YAML)
    r = subprocess.run([sys.executable, "run_eval.py", str(qfile)],
                       cwd=EVAL_DIR, capture_output=True, text=True, timeout=300)
    assert r.returncode == 2, "impossible questions must trip the CI gate (exit 2)"
