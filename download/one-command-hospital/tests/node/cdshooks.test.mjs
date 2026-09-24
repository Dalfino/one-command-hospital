/**
 * Unit tier — CDS Hooks patient-view facade logic (v0.6.1 ADOPT item).
 * Pure functions only: no HTTP, no services. The HTTP wiring in main.js is
 * covered by the integration tier (tests/integration/test_cds_hooks.py).
 */
import { test } from "node:test";
import assert from "node:assert/strict";

const cds = await import("../../services/ai-mediator/cdshooks.js");

const groundedResult = {
  rag: {
    refusal: false,
    answer:
      "[ANTICOAG-BRIDGE §2] Stop warfarin five days before surgery and bridge with LMWH.",
    citations: [{ corpus_id: "ANTICOAG-BRIDGE", section: "2", edition: "2024" }],
  },
  verification: { grounded: true, notes: [] },
};

const ungroundedResult = {
  rag: {
    refusal: false,
    answer: "Some answer without verification support.",
    citations: [],
  },
  verification: { grounded: false, notes: ["answer carried no citations — flagged for review"] },
};

const refusedResult = {
  rag: { refusal: true, answer: "NOT_COVERED", citations: [] },
  verification: { grounded: true, notes: ["verifier skipped (refusal)"] },
};

test("discovery exposes exactly the patient-view service", () => {
  const d = cds.discovery();
  assert.equal(d.cdsServices.length, 1);
  const s = d.cdsServices[0];
  assert.equal(s.hook, "patient-view");
  assert.equal(s.id, cds.SERVICE_ID);
  assert.ok(s.prefetch.patient.includes("{{context.patientId}}"));
});

test("validateHookRequest accepts a well-formed hook", () => {
  const v = cds.validateHookRequest({
    hook: "patient-view",
    context: { userId: "Practitioner/dr-1", patientId: " Patient/123 " },
  });
  assert.ok(v.ok);
  assert.equal(v.patientId, " Patient/123 "); // caller owns trimming; spec-verbatim
  assert.equal(v.userId, "Practitioner/dr-1");
});

test("validateHookRequest rejects wrong hook / missing patientId / garbage body", () => {
  assert.ok(!cds.validateHookRequest({ hook: "order-sign", context: { patientId: "1" } }).ok);
  assert.ok(!cds.validateHookRequest({ hook: "patient-view", context: {} }).ok);
  assert.ok(!cds.validateHookRequest({ hook: "patient-view", context: { patientId: 42 } }).ok);
  assert.ok(!cds.validateHookRequest(null).ok);
  assert.ok(!cds.validateHookRequest("hello").ok);
  assert.ok(!cds.validateHookRequest([1]).ok);
});

test("validateHookRequest defaults userId to unknown (never crashes)", () => {
  const v = cds.validateHookRequest({ hook: "patient-view", context: { patientId: "p1" } });
  assert.ok(v.ok);
  assert.equal(v.userId, "unknown");
});

test("questionsFromContext: active conditions + meds become questions, capped", () => {
  const ctx = {
    conditions: [
      { resourceType: "Condition", clinicalStatus: { coding: [{ code: "active" }] },
        code: { text: "Atrial Fibrillation" } },
      { resourceType: "Condition", clinicalStatus: { coding: [{ code: "resolved" }] },
        code: { text: "Historic Appendicitis" } },
      { resourceType: "Condition", verificationStatus: { coding: [{ code: "refuted" }] },
        code: { text: "Ruled-out Sepsis" } },
    ],
    medications: [
      { resourceType: "MedicationRequest", status: "active",
        medicationCodeableConcept: { text: "Warfarin" } },
      { resourceType: "MedicationRequest", status: "completed",
        medicationCodeableConcept: { text: "Old Drug" } },
    ],
  };
  const qs = cds.questionsFromContext(ctx);
  assert.deepEqual(qs, ["atrial fibrillation", "warfarin"]); // bare terms — see cdshooks.js rationale
});

test("questionsFromContext: dedupe, cap 3, tolerate bundles and garbage", () => {
  const dup = cds.questionsFromContext({
    conditions: [
      { resourceType: "Condition", code: { text: "Sepsis" } },
      { resourceType: "Condition", code: { text: "sepsis" } }, // dedupe (case-insensitive)
    ],
    medications: [],
  });
  assert.equal(dup.length, 1);

  const four = cds.questionsFromContext({
    conditions: ["A", "B", "C", "D"].map((t) => ({
      resourceType: "Condition", code: { text: t },
    })),
    medications: [],
  });
  assert.equal(four.length, 3); // DEFAULT_MAX_QUESTIONS

  assert.deepEqual(cds.questionsFromContext(null), []);
  const bundled = cds.questionsFromContext({
    conditions: [{ resourceType: "Bundle", entry: [
      { resource: { resourceType: "Condition", code: { text: "Bundle Condition" } } },
    ] }],
    medications: [],
  });
  assert.equal(bundled.length, 1, "searchset Bundle input must unwrap");
});

test("normalizePrefetch unwraps Bundles and drops the patient resource", () => {
  const n = cds.normalizePrefetch({
    patient: { resourceType: "Patient", id: "1", name: [{ family: "Smith" }] },
    conditions: { resourceType: "Bundle", entry: [
      { resource: { resourceType: "Condition", id: "c1" } },
    ] },
    medications: { resourceType: "MedicationRequest", id: "m1" },
  });
  assert.equal(n.conditions.length, 1);
  assert.equal(n.medications.length, 1);
  assert.equal(n.patient, undefined, "patient demographics must not travel onward");
});

test("cardFromResult: grounded answer → info card with citations in detail", () => {
  const card = cds.cardFromResult(groundedResult);
  assert.equal(card.indicator, "info");
  assert.ok(card.summary.length <= 140, "CDS Hooks summary limit");
  assert.ok(card.detail.includes("[ANTICOAG-BRIDGE §2]"));
  assert.ok(card.detail.includes("ANTICOAG-BRIDGE §2 (ed. 2024)"));
  assert.equal(card.source.label, "Guideline Copilot (advisory)");
  assert.equal(card.link, undefined);
});

test("cardFromResult: ungrounded answer → warning card flagged for review", () => {
  const card = cds.cardFromResult(ungroundedResult);
  assert.equal(card.indicator, "warning");
  assert.ok(card.summary.startsWith("[needs review]"));
  assert.ok(card.detail.includes("WARNING"));
  assert.equal(card.link.url, "/review");
});

test("cardFromResult: refusal → NO card (never fabricate advice)", () => {
  assert.equal(cds.cardFromResult(refusedResult), null);
  assert.equal(cds.cardFromResult(null), null);
  assert.equal(cds.cardFromResult({}), null);
});

test("cardFromResult: long answers truncate the summary to 140 chars", () => {
  const card = cds.cardFromResult({
    rag: { refusal: false,
           answer: "X".repeat(300) + " [ANTICOAG-BRIDGE §1] more",
           citations: [] },
    verification: { grounded: true },
  });
  assert.ok(card.summary.length <= 140);
  assert.ok(card.summary.endsWith("…"));
});

test("cardsFromResults: mixed results, silence on refusals, stats accurate", () => {
  const { cards, stats } = cds.cardsFromResults([
    groundedResult, refusedResult, ungroundedResult,
  ]);
  assert.equal(cards.length, 2);
  assert.equal(cards[0].indicator, "info");
  assert.equal(cards[1].indicator, "warning");
  assert.deepEqual(stats, { asked: 3, answered: 2, refused: 1, errors: 0, coverage_only: false });
});

test("cardsFromResults: all refused → exactly one coverage card", () => {
  const { cards, stats } = cds.cardsFromResults([refusedResult, refusedResult]);
  assert.equal(cards.length, 1);
  assert.ok(cards[0].summary.startsWith("No guideline coverage"));
  assert.equal(cards[0].indicator, "info");
  assert.equal(stats.coverage_only, true);
});

test("cardsFromResults: pipeline errors are silent but counted", () => {
  const { cards, stats } = cds.cardsFromResults([
    { question: "q", pipeline_error: "boom" },
  ]);
  assert.equal(cards.length, 1);
  assert.equal(stats.errors, 1);
  assert.equal(stats.coverage_only, true);
});
