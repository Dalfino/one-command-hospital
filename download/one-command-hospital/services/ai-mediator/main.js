/**
 * AI Mediator — the reusable plug between a hospital and any AI.
 *
 * Improvement #4: ONE contract every future model can ride on:
 *   clinical event / question → deid-gate → AI service → verifier
 *   → FHIR resource writeback (with provenance) → surfaced in the EHR.
 *
 * v0.1: Medplum Bot JWT auth (client_credentials + JWT assertion) and the
 * /signoff endpoint that closes the human_action audit loop.
 * Phase 1 remaining: OpenHIM mediator registration (POST {core}/mediators).
 */
import express from "express";
import { randomUUID } from "node:crypto";
import { authMode, fhirHeaders } from "./medplum-auth.js";

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

app.get("/health", (_req, res) =>
  res.json({ ok: true, service: "ai-mediator", auth: authMode() })
);

app.post("/process", async (req, res) => {
  const started = Date.now();
  const { question, contextText = "", patientId = null, userId = "unknown" } = req.body || {};
  if (!question) return res.status(400).json({ error: "question required" });

  try {
    // 1. De-ID any note context BEFORE it may reach the LLM path.
    let scrubbedContext = "";
    let deidMeta = null;
    if (contextText) {
      const deid = await postJson(DEID_URL, { text: contextText });
      scrubbedContext = deid.anonymized;
      deidMeta = { findings: deid.finding_count };
    }

    // 2. Ask the guideline RAG service (citations forced inside).
    const rag = await postJson(RAG_URL, { question });

    // 3. Verify grounding (Phase 1: medspaCy ConText replaces heuristics).
    let verification = { grounded: true, notes: ["verifier skipped (refusal path)"] };
    if (!rag.refusal && rag.citations?.length) {
      try {
        verification = await postJson(VERIFY_URL, {
          answer: rag.answer,
          sources: rag.citations.map((c) => ({
            corpus_id: c.corpus_id,
            section: c.section,
            text: c.title,
          })),
        });
      } catch {
        // verifier down → mark for review, never silently pass
        verification = { grounded: false, notes: ["verifier unreachable"] };
      }
    }

    // 4. Write back as a FHIR Communication with full provenance.
    const communication = {
      resourceType: "Communication",
      id: randomUUID(),
      status: "completed",
      category: [
        {
          coding: [
            { system: "http://one-command-hospital.local/ai", code: "guideline-answer" },
          ],
        },
      ],
      subject: patientId ? { reference: `Patient/${patientId}` } : undefined,
      sender: { display: "Guideline Copilot (advisory)" },
      sent: new Date().toISOString(),
      payload: [
        {
          contentString: JSON.stringify(
            {
              question,
              scrubbed_context: scrubbedContext || undefined,
              deid: deidMeta,
              answer: rag.answer,
              refusal: rag.refusal,
              citations: rag.citations, // corpus id + edition + section
              grounding: verification.grounded,
              verifier_notes: verification.notes,
              model: rag.model,
              latency_ms: rag.latency_ms,
              auth_mode: authMode(),
              human_action: "pending_review", // closed by clinician sign-off
              requested_by: userId,
            },
            null,
            2
          ),
        },
      ],
    };

    let fhir = { written: false };
    try {
      const r = await fetch(`${MEDPLUM_FHIR_URL}/Communication`, {
        method: "POST",
        headers: await fhirHeaders(),
        body: JSON.stringify(communication),
      });
      if (authMode() === "unauthenticated-v0") fhir.warning = "sandbox: unauthenticated writeback";
      fhir = { ...fhir, written: r.ok, status: r.status };
    } catch {
      /* Medplum down → still return the answer to the clinician */
    }

    res.json({ communication, fhir, total_latency_ms: Date.now() - started });
  } catch (e) {
    res.status(502).json({ error: String(e.message), stage: "pipeline" });
  }
});

/**
 * POST /signoff — closes the audit loop.
 * Body: { communicationId, action: "signed_off"|"escalated", by }
 * Reads the Communication from Medplum, updates human_action, writes it back.
 */
app.post("/signoff", async (req, res) => {
  const { communicationId, action, by = "clinician" } = req.body || {};
  if (!communicationId || !["signed_off", "escalated"].includes(action)) {
    return res.status(400).json({ error: "communicationId and valid action required" });
  }
  try {
    const getUrl = `${MEDPLUM_FHIR_URL}/Communication/${communicationId}`;
    const g = await fetch(getUrl, { headers: await fhirHeaders({ Accept: "application/fhir+json" }) });
    if (!g.ok) return res.status(404).json({ error: `Communication ${communicationId} not found` });
    const resource = await g.json();

    const payload = JSON.parse(resource.payload?.[0]?.contentString || "{}");
    payload.human_action = action;
    payload.actioned_by = by;
    payload.actioned_at = new Date().toISOString();
    resource.payload[0].contentString = JSON.stringify(payload, null, 2);

    const p = await fetch(getUrl, {
      method: "PUT",
      headers: await fhirHeaders(),
      body: JSON.stringify(resource),
    });
    res.json({ ok: p.ok, status: p.status, human_action: action });
  } catch (e) {
    res.status(502).json({ error: String(e.message) });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`ai-mediator on :${port} (auth: ${authMode()})`));
