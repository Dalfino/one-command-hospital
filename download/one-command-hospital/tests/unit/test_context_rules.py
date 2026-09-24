"""Unit tier — M21 context rules (historical/family sense conflicts).

The dangerous direction only: answer asserts a CURRENT patient fact, cited
source only supports historical or family sense. Guideline conditionals must
NOT be flagged (they are the corpus's normal voice).
"""
import os, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "verifier" / "app"))

from context_rules import sentence_context, anchor_contexts, context_conflicts  # noqa: E402


def test_sentence_labels():
    assert "historical" in sentence_context("Patient had a DVT in 2023, resolved.")
    assert "family" in sentence_context("Family history of PE in her mother.")
    assert "negated" in sentence_context("Bridging is not recommended in this setting.")
    assert sentence_context("Give apixaban 5 mg twice daily.") == set()


def test_historical_conflict_fires():
    answer = "Continue warfarin therapy for this patient."
    source = "The patient has a history of warfarin therapy, completed in 2023."
    anchors = ["warfarin", "therapy"]
    conflicts = context_conflicts(answer, source, anchors)
    assert conflicts and "warfarin" in conflicts[0]


def test_family_conflict_fires():
    answer = "Start heparin given the patient's reaction risk."
    source = "Family history of heparin reaction reported by the mother."
    conflicts = context_conflicts(answer, source, ["heparin", "reaction"])
    assert conflicts


def test_current_support_is_not_a_conflict():
    answer = "Continue warfarin therapy for this patient."
    source = "This patient takes warfarin 5 mg daily. INR is monitored."
    assert not context_conflicts(answer, source, ["warfarin", "therapy", "inr"])


def test_guideline_conditionals_not_flagged():
    # The corpus's normal voice is conditional; answers legitimately affirm it.
    answer = "Anticoagulate patients with atrial fibrillation before cardioversion."
    source = "If the patient has atrial fibrillation lasting over 48 hours, anticoagulate for 3 weeks before cardioversion."
    assert not context_conflicts(answer, source, ["fibrillation", "anticoagulate", "cardioversion"])


def test_negated_answer_is_safe_direction():
    answer = "Bridging is not recommended for this patient."
    source = "History of bridging therapy in 2019 without complication."
    assert not context_conflicts(answer, source, ["bridging"])


def test_anchor_contexts_distinguishes_senses():
    text = "Mother had PE. Patient has PE now."
    ctx = anchor_contexts(text, ["pe"])
    assert "family" in ctx["pe"] and "historical" not in ctx["pe"]
