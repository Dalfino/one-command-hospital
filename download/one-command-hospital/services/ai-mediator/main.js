/**
 * AI Mediator — the reusable plug between a hospital and any AI.
 *
 * Improvement #4: ONE contract every future model can ride on:
 *   clinical event / question → deid-gate → AI service → verifier
 *   → FHIR resource writeback (with provenance) → surfaced in the EHR.
 *
 * v0 exposes POST /process. Phase 1 registers it as an OpenHIM mediator
 * (POST {openhim-core}/mediators) and adds Medplum Bot JWT auth.
 */
import express from "express";
import { randomUUID } from "node:crypto";

const app = express();
app.use(express.json({ limit: "1mb" }));

const DEID_URL = process.env.DEID_URL || "http://deid-gate:8000/deid";
const RAG_URL = process.env.RAG_URL || "http://guideline-rag:8000/answer";
const VERIFY_URL = process.env.VERIFY_URL || "http://verifier:8000/verify";
const MEDPLUM_FHIR_URL = process.env.MEDPLUM_FHIR_URL || "http://medplum:8080/fhir";

async function postJson(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

app.get("/health", (_req, res) => res.json({ ok: true, service: "ai-mediator" }));

app.post("/process", async (req, res) => {
  const started = Date.now();
  const { question, contextText = "", patientId = null, userId = "unknown" } = req.body || {};
  if (!question) return res.status(400).json({ error: "question required" });

  try {
    // 1. De-ID any note context BEFORE it may reach the LLM path.
    let scrubbedContext = "";
    if (contextText) {
      const deid = await postJson(DEID_URL, { text: contextText });
      scrubbedContext = deid.anonymized;
    }

    // 2. Ask the guideline RAG service (citations forced inside).
    const rag = await postJson(RAG_URL, { question });

    // 3. Verify grounding (Phase 1: medspaCy ConText replaces heuristics).
    let verification = { grounded: true, notes: ["verifier skipped in v0 path"] };
    if (!rag.refusal && rag.citations?.length) {
      try {
        verification = await postJson(VERIFY_URL, {
          answer: rag.answer,
          sources: rag.citations.map((c) => ({
            corpus_id: c.corpus_id, section: c.section, text: c.title,
          })),
        });
      } catch { /* verifier down → mark for review, never silently pass */ 
        verification = { grounded: false, notes: ["verifier unreachable"] };
      }
    }

    // 4. Write back as a FHIR Communication with full provenance.
    const communication = {
      resourceType: "Communication",
      id: randomUUID(),
      status: "completed",
      category: [{ coding: [{ system: "http://one-command-hospital.local/ai", code: "guideline-answer" }] }],
      subject: patientId ? { reference: `Patient/${patientId}` } : undefined,
      sender: { display: "Guideline Copilot (advisory)" },
      sent: new Date().toISOString(),
      payload: [{
        contentString: JSON.stringify({
          question,
          answer: rag.answer,
          refusal: rag.refusal,
          citations: rag.citations,           // corpus id + edition + section
          grounding: verification.grounded,
          verifier_notes: verification.notes,
          model: rag.model,
          latency_ms: rag.latency_ms,
          human_action: "pending_review",     // audit: closed by clinician sign-off
          requested_by: userId,
        }, null, 2),
      }],
    };

    let fhir = { written: false };
    try {
      const r = await fetch(`${MEDPLUM_FHIR_URL}/Communication`, {
        method: "POST",
        headers: { "Content-Type": "application/fhir+json" },
        body: JSON.stringify(communication),
      });
      fhir = { written: r.ok, status: r.status };
    } catch { /* Medplum down → still return the answer to the clinician */ }

    res.json({ communication, fhir, total_latency_ms: Date.now() - started });
  } catch (e) {
    res.status(502).json({ error: String(e.message), stage: "pipeline" });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`ai-mediator on :${port}`));
