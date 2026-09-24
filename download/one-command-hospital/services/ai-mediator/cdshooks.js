/**
 * cdshooks.js — CDS Hooks `patient-view` facade logic (v0.6.1, zero deps).
 *
 * ADOPT item (docs/tech_radar.md): CDS Hooks is how real EHRs (Epic, Cerner,
 * Medplum-based charts) surface decision support natively — the copilot
 * appears inside the patient's chart view instead of a separate portal tab.
 * This module holds the PURE logic; the HTTP wiring lives in main.js:
 *
 *   POST /cds-services/guideline-copilot-patient-view
 *     validate → prefetch|FHIR context → ≤3 questions
 *     → runPipeline (deid → RAG → verify → FHIR writeback → audit → review)
 *     → CDS cards
 *
 * Design invariants (each mirrored by tests/node/cdshooks.test.mjs):
 *  - cards are built ONLY from scrubbed pipeline answers (corpus-derived);
 *    the FHIR context / prefetch payload is transient input and is never
 *    echoed into cards, logs, or audit records
 *  - a refusal produces NO card (we do not fabricate advice); when that
 *    leaves the response empty, exactly one deterministic no-coverage card
 *    is returned so the clinician is never left with a silent chart
 *  - an ungrounded answer renders as a WARNING card flagged for clinician
 *    review — never as verified advice
 *  - questions derived from chart data ride the same injection guard as
 *    typed questions (Gate 0 in guideline-rag scans every question)
 */

export const SERVICE_ID = "guideline-copilot-patient-view";
export const HOOK = "patient-view";
const SUMMARY_MAX = 140; // CDS Hooks card.summary is limited to 140 chars
const DEFAULT_MAX_QUESTIONS = 3;

/** GET /cds-services discovery document. */
export function discovery() {
  return {
    cdsServices: [
      {
        hook: HOOK,
        title: "Guideline Copilot — chart view",
        description:
          "Cite-or-refuse guideline guidance for the patient's active problems " +
          "and medications. Answers are grounded in the hospital guideline " +
          "corpus, verified for citation support, de-identified before any AI " +
          "processing, and audited end-to-end.",
        id: SERVICE_ID,
        prefetch: {
          patient: "Patient/{{context.patientId}}",
          conditions:
            "Condition?patient={{context.patientId}}&clinical-status=active",
          medications:
            "MedicationRequest?patient={{context.patientId}}&status=active",
        },
      },
    ],
  };
}

/** Validate a CDS Hooks request body. Returns
 *  {ok:true, patientId, userId, prefetch, fhirServer} or {ok:false, error}. */
export function validateHookRequest(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return { ok: false, error: "request body must be a JSON object" };
  }
  if (body.hook !== HOOK) {
    return {
      ok: false,
      error: `unsupported hook '${String(body.hook)}' — this service implements '${HOOK}' only`,
    };
  }
  const ctx = body.context && typeof body.context === "object" ? body.context : {};
  if (!ctx.patientId || typeof ctx.patientId !== "string") {
    return { ok: false, error: "context.patientId is required for patient-view" };
  }
  return {
    ok: true,
    patientId: ctx.patientId,
    userId: typeof ctx.userId === "string" && ctx.userId ? ctx.userId : "unknown",
    prefetch: body.prefetch && typeof body.prefetch === "object" ? body.prefetch : null,
    fhirServer: typeof body.fhirServer === "string" ? body.fhirServer : null,
  };
}

/** A prefetch value / FHIR search result may be a single resource or a
 *  searchset Bundle — normalize to an array of resources. */
function unwrap(resource) {
  if (!resource || typeof resource !== "object") return [];
  if (resource.resourceType === "Bundle" && Array.isArray(resource.entry)) {
    return resource.entry.map((e) => e && e.resource).filter(Boolean);
  }
  return [resource];
}

/** Normalize a prefetch map into {conditions, medications} resource arrays.
 *  (The Patient resource itself is deliberately NOT returned — nothing in
 *  the card path should ever see demographics.) */
export function normalizePrefetch(prefetch) {
  const p = prefetch && typeof prefetch === "object" ? prefetch : {};
  return {
    conditions: unwrap(p.conditions),
    medications: unwrap(p.medications),
  };
}

function codeText(codeField) {
  if (!codeField || typeof codeField !== "object") return "";
  if (typeof codeField.text === "string" && codeField.text.trim()) {
    return codeField.text.trim();
  }
  const codings = Array.isArray(codeField.coding) ? codeField.coding : [];
  for (const c of codings) {
    if (c && typeof c.display === "string" && c.display.trim()) return c.display.trim();
  }
  return "";
}

/** Status concepts carry FHIR tokens (coding[].code), not display names —
 *  e.g. clinicalStatus {coding:[{code:"active"}]}. Read code first, text as
 *  a fallback for sloppy producers. */
function statusToken(concept) {
  if (!concept || typeof concept !== "object") return "";
  const codings = Array.isArray(concept.coding) ? concept.coding : [];
  for (const c of codings) {
    if (c && typeof c.code === "string" && c.code.trim()) return c.code.trim().toLowerCase();
  }
  if (typeof concept.text === "string" && concept.text.trim()) {
    return concept.text.trim().toLowerCase();
  }
  return "";
}

function conditionActive(cond) {
  const verif = statusToken(cond.verificationStatus);
  if (verif === "refuted" || verif === "entered-in-error") return false;
  const status = statusToken(cond.clinicalStatus);
  return status !== "resolved" && status !== "inactive" && status !== "entered-in-error";
}

/** FHIR context → bounded, deduplicated question list.
 *
 *  The question is deliberately the BARE clinical term as it appears in the
 *  chart. Live probing during v0.6.1 showed templated phrasing ("What do the
 *  guidelines recommend for managing X?") injects corpus-frequent vocabulary
 *  (guidelines / recommend / manage) that degrades BM25 specificity: a
 *  templated GARBAGE term scored above the retrieval threshold where the bare
 *  term correctly refused. The copilot's job is retrieval + citation; the
 *  phrasing adds no information and costs discriminating power.
 *
 *  Injection-bearing chart text cannot bypass Gate 0: every question still
 *  runs the de-id + injection screen inside the pipeline. */
export function questionsFromContext(context, maxQ = DEFAULT_MAX_QUESTIONS) {
  const ctx = context && typeof context === "object" ? context : {};
  const questions = [];
  const seen = new Set();
  const push = (q) => {
    const key = q.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      questions.push(q);
    }
  };
  // Each side may arrive as a plain resource array (normalizePrefetch) or as
  // a raw FHIR searchset Bundle (fetchFhirContext) — unwrap handles both.
  for (const c of (ctx.conditions || []).flatMap(unwrap)) {
    if (!c || c.resourceType !== "Condition" || !conditionActive(c)) continue;
    const t = codeText(c.code);
    if (t) push(t.toLowerCase());
  }
  for (const m of (ctx.medications || []).flatMap(unwrap)) {
    if (!m || m.resourceType !== "MedicationRequest") continue;
    if (m.status && m.status !== "active") continue;
    const t = codeText(m.medicationCodeableConcept);
    if (t) push(t.toLowerCase());
  }
  return questions.slice(0, maxQ);
}

function firstSentence(s) {
  // Chart-facing summary hygiene: extractive/mock answers open with the
  // citation marker and the corpus section header ("## 1. Scope") — drop
  // markers and heading lines so the summary reads like a sentence.
  const cleaned = String(s || "")
    .replace(/\[[A-Z][A-Z0-9-]+\s*§\s*\d+\]/g, " ")
    .split("\n")
    .filter((line) => {
      const t = line.trim();
      if (!t || t.startsWith("#")) return false;
      if (/^\d+[.)]\s/.test(t)) return false; // numbered heading fragments
      return true;
    })
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  const m = cleaned.match(/^(.+?[.!?])(\s|$)/);
  return (m ? m[1] : cleaned.slice(0, 200)).trim();
}

function truncate(s, n) {
  return s.length <= n ? s : s.slice(0, n - 1).trimEnd() + "…";
}

const SOURCE = { label: "Guideline Copilot (advisory)" };

/** Pipeline result → CDS card, or null when the item must stay silent
 *  (refusals). `r` = {rag:{refusal, answer, citations}, verification:{grounded}}. */
export function cardFromResult(r) {
  if (!r || !r.rag || r.rag.refusal) return null;
  const rag = r.rag;
  const grounded = !!(r.verification && r.verification.grounded);
  const cites = (rag.citations || [])
    .map((c) => `${c.corpus_id} §${c.section} (ed. ${c.edition})`);
  const summary = truncate(
    (grounded ? "" : "[needs review] ") + firstSentence(rag.answer),
    SUMMARY_MAX
  );
  const detail = [
    grounded
      ? "Grounding verified against the cited guideline sections."
      : "WARNING: grounding verification FAILED — treat as unverified; a clinician must review this answer.",
    "",
    rag.answer,
    "",
    cites.length ? "Sources:\n- " + cites.join("\n- ") : "Sources: none (ungrounded)",
  ].join("\n");
  return {
    summary,
    indicator: grounded ? "info" : "warning",
    detail,
    source: { ...SOURCE },
    // Ungrounded cards deep-link to the review worklist so the flag has a
    // workflow attached, not just a label.
    ...(grounded ? {} : { link: { label: "Review queue", url: "/review", type: "relative" } }),
  };
}

/** Deterministic no-coverage card — emitted only when NO question produced
 *  an answer, so the clinician gets an explicit "nothing to say" instead of
 *  an empty response. */
export function coverageCard() {
  return {
    summary: "No guideline coverage found for this patient's active problems or medications.",
    indicator: "info",
    detail:
      "The guideline corpus does not cover the patient's current active problems/medications, " +
      "or retrieval confidence was below the safety threshold. Nothing is suggested. " +
      "Ask a specific clinical question via the copilot for a full cited attempt.",
    source: { ...SOURCE },
  };
}

/** All pipeline results → {cards, stats}. Refusals and pipeline errors are
 *  silent; the coverage card backstops an all-empty result set. */
export function cardsFromResults(results) {
  const list = Array.isArray(results) ? results : [];
  const cards = [];
  let answered = 0, refused = 0, errors = 0;
  for (const r of list) {
    if (r && r.pipeline_error) {
      errors += 1;
      continue;
    }
    const card = cardFromResult(r);
    if (card) {
      cards.push(card);
      answered += 1;
    } else {
      refused += 1;
    }
  }
  let coverage_only = false;
  if (!cards.length) {
    cards.push(coverageCard());
    coverage_only = true;
  }
  return {
    cards: cards.slice(0, DEFAULT_MAX_QUESTIONS + 2),
    stats: { asked: list.length, answered, refused, errors, coverage_only },
  };
}
